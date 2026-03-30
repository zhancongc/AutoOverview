"""
FastAPI 主应用
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from datetime import datetime

from database import db, get_db
from models import ReviewRecord
from services.paper_search import PaperSearchService
from services.paper_filter import PaperFilterService
from services.review_generator import ReviewGeneratorService
from services.topic_analyzer import ThreeCirclesReviewGenerator
from services.hybrid_classifier import FrameworkGenerator
from services.docx_generator import DocxGenerator

load_dotenv()

app = FastAPI(title="论文综述生成器 API")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求模型
class TopicRequest(BaseModel):
    topic: str = Field(..., description="论文题目", min_length=1)


class GenerateRequest(BaseModel):
    topic: str = Field(..., description="论文主题", min_length=1)
    target_count: int = Field(50, description="目标文献数量", ge=10, le=100)
    recent_years_ratio: float = Field(0.5, description="近5年占比", ge=0.1, le=1.0)
    english_ratio: float = Field(0.3, description="英文文献占比", ge=0.1, le=1.0)


class GenerateResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None


# 全局服务实例
search_service = PaperSearchService()
filter_service = PaperFilterService()
three_circles_generator = ThreeCirclesReviewGenerator()


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库连接"""
    db.connect()


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "service": "论文综述生成器 API"}


@app.get("/api/search")
async def search_papers(
    query: str,
    limit: int = 100,
    years_ago: int = 5
):
    """搜索论文接口"""
    try:
        papers = await search_service.search_papers(
            query=query,
            years_ago=years_ago,
            limit=limit
        )
        return {
            "success": True,
            "count": len(papers),
            "papers": papers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_review(
    request: GenerateRequest,
    db_session: Session = Depends(get_db)
):
    """生成文献综述接口"""
    record = ReviewRecord(
        topic=request.topic,
        review="",
        papers=[],
        statistics={},
        target_count=request.target_count,
        recent_years_ratio=request.recent_years_ratio,
        english_ratio=request.english_ratio,
        status="processing"
    )
    db_session.add(record)
    db_session.commit()

    try:
        # 1. 搜索文献
        papers = await search_service.search_papers(
            query=request.topic,
            years_ago=10,
            limit=200
        )

        if not papers:
            record.status = "failed"
            record.error_message = f'未找到关于「{request.topic}」的相关文献'
            db_session.commit()
            return GenerateResponse(
                success=False,
                message=record.error_message
            )

        # 2. 筛选文献
        filtered_papers = filter_service.filter_and_sort(
            papers=papers,
            target_count=request.target_count,
            recent_years_ratio=request.recent_years_ratio,
            english_ratio=request.english_ratio
        )

        # 3. 获取统计信息
        stats = filter_service.get_statistics(filtered_papers)

        # 4. 生成综述
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not configured")

        generator = ReviewGeneratorService(api_key=api_key)
        review = await generator.generate_review(
            topic=request.topic,
            papers=filtered_papers
        )

        # 5. 保存记录
        record.review = review
        record.papers = filtered_papers
        record.statistics = stats
        record.status = "success"
        db_session.commit()

        return GenerateResponse(
            success=True,
            message="文献综述生成成功",
            data={
                "id": record.id,
                "topic": request.topic,
                "review": review,
                "papers": filtered_papers,
                "statistics": stats,
                "created_at": record.created_at.isoformat()
            }
        )

    except Exception as e:
        record.status = "failed"
        record.error_message = str(e)
        db_session.commit()
        return GenerateResponse(
            success=False,
            message=f"生成失败: {str(e)}"
        )


@app.post("/api/smart-generate")
async def smart_generate_review(
    request: GenerateRequest,
    db_session: Session = Depends(get_db)
):
    """
    智能生成文献综述（基于智能分析结果进行聚焦搜索）
    """
    record = ReviewRecord(
        topic=request.topic,
        review="",
        papers=[],
        statistics={},
        target_count=request.target_count,
        recent_years_ratio=request.recent_years_ratio,
        english_ratio=request.english_ratio,
        status="processing"
    )
    db_session.add(record)
    db_session.commit()

    try:
        # 1. 智能分析题目，获取搜索策略
        from services.hybrid_classifier import FrameworkGenerator
        gen = FrameworkGenerator()
        framework = await gen.generate_framework(request.topic)

        # 2. 根据分析结果生成搜索关键词
        all_papers = []
        search_queries = []

        if framework.get('search_queries'):
            # 使用智能分析生成的搜索查询
            search_queries = framework.get('search_queries', [])
            print(f"[SmartGenerate] 使用智能分析生成的搜索查询: {len(search_queries)} 个")

            # 并发搜索
            for query_info in search_queries[:5]:  # 最多搜索 5 个查询
                query = query_info.get('query', request.topic)
                papers = await search_service.search_papers(
                    query=query,
                    years_ago=10,
                    limit=50  # 每个查询最多 50 篇
                )
                print(f"[SmartGenerate] 查询 '{query}' 找到 {len(papers)} 篇")
                all_papers.extend(papers)

        # 如果搜索到的文献太少，使用主题进行补充搜索
        if len(all_papers) < 20:
            print(f"[SmartGenerate] 文献数量不足，使用主题补充搜索")
            additional_papers = await search_service.search_papers(
                query=request.topic,
                years_ago=10,
                limit=100
            )
            all_papers.extend(additional_papers)

        # 去重
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            paper_id = paper.get("id")
            if paper_id not in seen_ids:
                seen_ids.add(paper_id)
                unique_papers.append(paper)

        all_papers = unique_papers
        print(f"[SmartGenerate] 去重后共 {len(all_papers)} 篇文献")

        if not all_papers:
            record.status = "failed"
            record.error_message = f'未找到关于「{request.topic}」的相关文献'
            db_session.commit()
            return GenerateResponse(
                success=False,
                message=record.error_message
            )

        # 3. 提取主题关键词用于相关性评分
        topic_keywords = []
        key_elements = framework.get('key_elements', {})
        for key, value in key_elements.items():
            if value and isinstance(value, str):
                topic_keywords.extend(value.split())
                if value == key_elements.get('methodology'):
                    # 处理缩写
                    for kw in ['QFD', 'FMEA', 'DMAIC', 'AHP']:
                        if kw in value:
                            topic_keywords.append(kw)

        # 4. 筛选文献（使用关键词进行相关性评分）
        filtered_papers = filter_service.filter_and_sort(
            papers=all_papers,
           ars=target_count,
            recent_years_ratio=request.recent_years_ratio,
            english_ratio=request.english_ratio,
            topic_keywords=topic_keywords
        )

        # 5. 获取统计信息
        stats = filter_service.get_statistics(filtered_papers)

        # 6. 生成综述
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not configured")

        generator = ReviewGeneratorService(api_key=api_key)
        review = await generator.generate_review(
            topic=request.topic,
            papers=filtered_papers
        )

        # 7. 保存记录
        record.review = review
        record.papers = filtered_papers
        record.statistics = stats
        record.status = "success"
        db_session.commit()

        return GenerateResponse(
            success=True,
            message="文献综述生成成功",
            data={
                "id": record.id,
                "topic": request.topic,
                "review": review,
                "papers": filtered_papers,
                "statistics": stats,
                "analysis": framework,
                "created_at": record.created_at.isoformat()
            }
        )

    except Exception as e:
        record.status = "failed"
        record.error_message = str(e)
        db_session.commit()
        return GenerateResponse(
            success=False,
            message=f"生成失败: {str(e)}"
        )


@app.get("/api/records")
async def get_records(
    skip: int = 0,
    limit: int = 20,
    db_session: Session = Depends(get_db)
):
    """获取生成记录列表"""
    records = db_session.query(ReviewRecord).order_by(
        ReviewRecord.created_at.desc()
    ).offset(skip).limit(limit).all()

    return {
        "success": True,
        "count": len(records),
        "records": [r.to_dict() for r in records]
    }


@app.get("/api/records/{record_id}")
async def get_record(
    record_id: int,
    db_session: Session = Depends(get_db)
):
    """获取单条记录详情"""
    record = db_session.query(ReviewRecord).filter(
        ReviewRecord.id == record_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    return {
        "success": True,
        "record": record.to_dict()
    }


@app.delete("/api/records/{record_id}")
async def delete_record(
    record_id: int,
    db_session: Session = Depends(get_db)
):
    """删除记录"""
    record = db_session.query(ReviewRecord).filter(
        ReviewRecord.id == record_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    db_session.delete(record)
    db_session.commit()

    return {"success": True, "message": "删除成功"}


@app.post("/api/records/{record_id}/export")
async def export_record_docx(
    record_id: int,
    db_session: Session = Depends(get_db)
):
    """
    导出文献记录为 Word 文档

    返回 .docx 文件的二进制数据
    """
    record = db_session.query(ReviewRecord).filter(
        ReviewRecord.id == record_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    try:
        generator = DocxGenerator()
        docx_bytes = generator.generate_review_docx(
            topic=record.topic,
            review=record.review,
            papers=record.papers,
            statistics=record.statistics
        )

        from fastapi.responses import Response

        # 生成安全的文件名
        safe_topic = record.topic.replace('/', '-').replace('\\', '-').replace(':', '-')
        filename = f"{safe_topic}.docx"

        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@app.post("/api/export")
async def export_review_docx(
    topic: str,
    review: str,
    papers: List[Dict],
    statistics: Optional[Dict] = None
):
    """
    导出文献综述为 Word 文档

    接收直接传入的数据并返回 .docx 文件
    """
    try:
        generator = DocxGenerator()
        docx_bytes = generator.generate_review_docx(
            topic=topic,
            review=review,
            papers=papers,
            statistics=statistics
        )

        from fastapi.responses import Response

        # 生成安全的文件名
        safe_topic = topic.replace('/', '-').replace('\\', '-').replace(':', '-')
        filename = f"{safe_topic}.docx"

        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    return {
        "status": "ok",
        "deepseek_configured": bool(api_key)
    }


# ==================== 三圈文献分析接口 ====================

@app.post("/api/classify-topic")
async def classify_topic(request: TopicRequest):
    """
    题目分类接口（使用大模型）

    自动识别题目类型（应用型/评价型/理论型/实证型）
    并生成对应的综述框架
    """
    import sys
    import time

    print(f"[API] 收到分类请求: {request.topic}")
    start = time.time()

    try:
        from services.hybrid_classifier import FrameworkGenerator

        gen = FrameworkGenerator()
        result = await gen.generate_framework(request.topic)

        elapsed = time.time() - start
        print(f"[API] 大模型分类成功，耗时 {elapsed:.2f}秒，类型: {result['type']}")

        return {
            "success": True,
            "message": "题目分类完成",
            "data": result
        }
    except Exception as e:
        elapsed = time.time() - start
        print(f"[DEBUG] 大模型分类错误 (耗时{elapsed:.2f}秒): {e}")
        import traceback
        traceback.print_exc()
        # 出错时使用规则引擎回退
        from services.topic_classifier import FrameworkGenerator as FallbackGenerator
        fallback = FallbackGenerator()
        result = fallback.generate_framework(request.topic)
        result['classification_reason'] += f'（大模型错误，使用规则引擎）'
        return {
            "success": True,
            "message": "题目分类完成（使用规则引擎）",
            "data": result
        }


@app.post("/api/smart-analyze")
async def smart_analyze(request: TopicRequest):
    """
    智能分析接口（使用大模型）

    根据题目类型自动选择合适的分析方法
    - 应用型：三圈交集分析
    - 评价型：金字塔式分析
    - 其他：通用分析
    """
    try:
        from services.hybrid_classifier import FrameworkGenerator
        gen = FrameworkGenerator()
        framework = await gen.generate_framework(request.topic)

        # 根据类型选择分析方法
        if framework['type'] == 'application':
            # 应用型使用三圈分析
            circles_result = await three_circles_generator.generate(request.topic)

            # 清理 papers 数据，只保留摘要信息
            circles = []
            for circle in circles_result.get('circles', []):
                circles.append({
                    'circle': circle['circle'],
                    'name': circle['name'],
                    'query': circle['query'],
                    'description': circle['description'],
                    'count': circle['count']
                })

            result = {
                'analysis': framework,  # 使用正确的分类数据结构
                'circles': circles,
                'review_framework': framework.get('framework'),
                'framework_type': 'three-circles'
            }
        elif framework['type'] == 'evaluation':
            # 评价型使用金字塔式分析
            result = {
                'analysis': framework,
                'circles': [],
                'review_framework': framework.get('framework'),
                'framework_type': 'pyramid'
            }
        else:
            # 其他类型使用框架分析
            result = {
                'analysis': framework,
                'circles': [],
                'review_framework': framework.get('framework'),
                'framework_type': framework.get('type', 'general')
            }

        return {
            "success": True,
            "message": "智能分析完成",
            "data": result
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 三圈文献分析接口（保留原有功能） ====================

@app.post("/api/analyze-three-circles")
async def analyze_three_circles(request: TopicRequest):
    """
    三圈文献分析接口

    分析论文题目，构建"研究对象+优化目标+方法论"三圈文献体系
    """
    try:
        result = await three_circles_generator.generate(request.topic)

        return {
            "success": True,
            "message": "三圈分析完成",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-three-circles")
async def generate_three_circles_review(
    request: GenerateRequest,
    db_session: Session = Depends(get_db)
):
    """
    基于三圈分析生成综述接口
    """
    try:
        # 三圈分析
        analysis_result = await three_circles_generator.generate(request.topic)

        # 合并三个圈的文献
        all_papers = []
        for circle in analysis_result['circles']:
            all_papers.extend(circle['papers'])

        if not all_papers:
            return GenerateResponse(
                success=False,
                message="未找到足够的文献"
            )

        # 筛选文献
        filtered_papers = filter_service.filter_and_sort(
            papers=all_papers,
            target_count=request.target_count,
            recent_years_ratio=request.recent_years_ratio,
            english_ratio=request.english_ratio
        )

        # 获取统计信息
        stats = filter_service.get_statistics(filtered_papers)

        # 生成综述（使用三圈框架）
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not configured")

        generator = ReviewGeneratorService(api_key=api_key)

        # 构建带三圈框架的综述提示
        framework = analysis_result['review_framework']
        review = await generator.generate_review(
            topic=request.topic,
            papers=filtered_papers
        )

        # 保存记录
        record = ReviewRecord(
            topic=request.topic,
            review=review,
            papers=filtered_papers,
            statistics=stats,
            target_count=request.target_count,
            recent_years_ratio=request.recent_years_ratio,
            english_ratio=request.english_ratio,
            status="success"
        )
        db_session.add(record)
        db_session.commit()

        return GenerateResponse(
            success=True,
            message="三圈文献综述生成成功",
            data={
                "id": record.id,
                "topic": request.topic,
                "review": review,
                "papers": filtered_papers,
                "statistics": stats,
                "analysis": analysis_result['analysis'],
                "framework": framework,
                "circles": [
                    {
                        "circle": c['circle'],
                        "name": c['name'],
                        "count": c['count']
                    }
                    for c in analysis_result['circles']
                ],
                "gap_analysis": analysis_result['gap_analysis'],
                "created_at": record.created_at.isoformat()
            }
        )

    except Exception as e:
        return GenerateResponse(
            success=False,
            message=f"生成失败: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
