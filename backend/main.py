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
from urllib.parse import quote

from database import db, get_db
from models import ReviewRecord
from services.scholarflux_wrapper import ScholarFlux
from services.paper_filter import PaperFilterService
from services.review_generator import ReviewGeneratorService
from services.topic_analyzer import ThreeCirclesReviewGenerator
from services.hybrid_classifier import FrameworkGenerator
from services.docx_generator import DocxGenerator
from services.reference_validator import ReferenceValidator
from services.review_record_service import ReviewRecordService

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

class ExportRequest(BaseModel):
    record_id: int

# 全局服务实例
search_service = ScholarFlux()
filter_service = PaperFilterService()
three_circles_generator = ThreeCirclesReviewGenerator()
record_service = ReviewRecordService()

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

@app.get("/api/records")
async def get_records(
    skip: int = 0,
    limit: int = 20,
    db_session: Session = Depends(get_db)
):
    """获取生成记录列表"""
    records = record_service.list_records(db_session, skip, limit)

    return {
        "success": True,
        "count": len(records),
        "records": [record_service.record_to_dict(r) for r in records]
    }

@app.get("/api/records/{record_id}")
async def get_record(
    record_id: int,
    db_session: Session = Depends(get_db)
):
    """获取单条记录详情"""
    record = record_service.get_record(db_session, record_id)

    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    return {
        "success": True,
        "record": record_service.record_to_dict(record)
    }

@app.delete("/api/records/{record_id}")
async def delete_record(
    record_id: int,
    db_session: Session = Depends(get_db)
):
    """删除记录"""
    deleted = record_service.delete_record(db_session, record_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="记录不存在")

    return {"success": True, "message": "删除成功"}

@app.post("/api/records/export")
async def export_review_docx(
    request: ExportRequest,
    db_session: Session = Depends(get_db)
):
    """
    导出文献综述为 Word 文档

    接收 record_id，从数据库获取数据并返回 .docx 文件
    """
    record = record_service.get_record(db_session, request.record_id)

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

        # 生成文件名：文献综述-论文标题-yymmdd-HHMMSS.docx
        from datetime import datetime
        now = datetime.now()
        timestamp = now.strftime("%y%m%d-%H%M%S")

        # 清理主题中的特殊字符
        safe_topic = record.topic.replace('/', '-').replace('\\', '-').replace(':', '-')
        safe_topic = safe_topic.replace('（', '-').replace('）', '-')
        safe_topic = safe_topic.replace('<', '-').replace('>', '-').replace('|', '-')
        safe_topic = safe_topic.replace('"', '-').replace('*', '-').replace('?', '-')
        # 限制主题长度，避免文件名过长
        safe_topic = safe_topic[:50]

        filename = f"文献综述-{safe_topic}-{timestamp}.docx"

        # 使用 URL 编码处理中文文件名
        encoded_filename = quote(filename, safe='')
        content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"

        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": content_disposition
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

    # ==================== 题目分类接口 ====================

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

# ==================== 智能分析接口 ====================

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
        framework = await gen.generate_framework(request.topic, enable_llm_validation=True)

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

# ==================== 智能生成综述接口 ====================

@app.post("/api/smart-generate")
async def smart_generate_review(
    request: GenerateRequest,
    db_session: Session = Depends(get_db)
):
    """
    智能生成文献综述（生成后验证被引用文献质量，不达标则扩大候选池重试）
    """
    # 创建记录
    record = record_service.create_record(
        db_session=db_session,
        topic=request.topic,
        target_count=request.target_count,
        recent_years_ratio=request.recent_years_ratio,
        english_ratio=request.english_ratio
    )

    validator = ReferenceValidator()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        record = record_service.update_failure(
            db_session=db_session,
            record=record,
            error_message="DEEPSEEK_API_KEY not configured"
        )
        return GenerateResponse(
            success=False,
            message="API配置错误"
        )

    try:
        # 1. 智能分析题目
        from services.hybrid_classifier import FrameworkGenerator
        gen = FrameworkGenerator()
        framework = await gen.generate_framework(request.topic, enable_llm_validation=True)

        # 2. 初始文献搜索
        all_papers = []
        search_queries_results = []

        search_queries = framework.get('search_queries', [])
        if search_queries:
            print(f"[SmartGenerate] 使用智能分析生成的搜索查询: {len(search_queries)} 个")

            for query_info in search_queries[:5]:
                query = query_info.get('query', request.topic)
                section = query_info.get('section', '通用')
                papers = await search_service.search_papers(
                    query=query,
                    years_ago=10,
                    limit=100  # 增加到100篇
                )
                print(f"[SmartGenerate] 查询 '{query}' 找到 {len(papers)} 篇")

                search_queries_results.append({
                    'query': query,
                    'section': section,
                    'papers': papers,
                    'citedCount': 0
                })
                all_papers.extend(papers)

        # 补充搜索（确保至少有150篇文献）
        if len(all_papers) < 150:
            print(f"[SmartGenerate] 文献数量不足（{len(all_papers)}篇），使用主题补充搜索")
            additional_papers = await search_service.search_papers(
                query=request.topic,
                years_ago=10,
                limit=200  # 增加补充搜索的数量
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
            record = record_service.update_failure(
                db_session=db_session,
                record=record,
                error_message=f'未找到关于「{request.topic}」的相关文献'
            )
            return GenerateResponse(
                success=False,
                message=record.error_message
            )

        # 3. 提取主题关键词
        topic_keywords = gen.extract_relevance_keywords(framework)

        # 4. 筛选文献（作为候选池）
        search_count = max(request.target_count * 2, 100)
        filtered_papers = filter_service.filter_and_sort(
            papers=all_papers,
            target_count=search_count,
            recent_years_ratio=request.recent_years_ratio,
            english_ratio=request.english_ratio,
            topic_keywords=topic_keywords
        )
        print(f"[SmartGenerate] 筛选后候选池: {len(filtered_papers)} 篇")

        # 5-7. 生成综述并验证被引用文献（带重试循环）
        generator = ReviewGeneratorService(api_key=api_key)
        review = None
        cited_papers = None
        validation_passed = False
        retry_count = 0
        max_retries = 1
        candidate_pool = filtered_papers

        while retry_count <= max_retries:
            print(f"[SmartGenerate] 第 {retry_count + 1} 次生成综述，候选池: {len(candidate_pool)} 篇")

            # 5. 生成综述
            review, cited_papers = await generator.generate_review(
                topic=request.topic,
                papers=candidate_pool
            )

            # 6. 验证被引用文献质量
            content, _ = validator._split_review_and_references(review)
            cited_indices = validator._extract_cited_indices(content)

            # 验证引用数量
            count_validation = validator.validate_citation_count(
                cited_indices=cited_indices,
                papers=cited_papers,
                min_count=request.target_count
            )

            # 验证近5年占比
            recent_validation = validator.validate_recent_ratio(
                papers=cited_papers,
                min_ratio=request.recent_years_ratio
            )

            # 验证英文占比
            english_validation = validator.validate_english_ratio(
                papers=cited_papers,
                min_ratio=request.english_ratio
            )

            # 检查是否全部通过
            all_passed = (
                count_validation["passed"] and
                recent_validation["passed"] and
                english_validation["passed"]
            )

            print(f"[SmartGenerate] 引用数量: {count_validation['actual']}/{count_validation['required']}, "
                  f"近5年: {recent_validation['actual']}%/{recent_validation['required']}%, "
                  f"英文: {english_validation['actual']}%/{english_validation['required']}%")

            if all_passed:
                validation_passed = True
                print(f"[SmartGenerate] 被引用文献验证通过")
                break
            else:
                if retry_count < max_retries:
                    print(f"[SmartGenerate] 被引用文献验证未通过，扩大候选池重试...")
                    # 扩大候选池
                    additional_papers = await search_service.search_papers(
                        query=request.topic,
                        years_ago=15,  # 扩大年份范围
                        limit=150
                    )
                    # 去重并添加到候选池
                    for paper in additional_papers:
                        paper_id = paper.get("id")
                        if paper_id not in seen_ids:
                            seen_ids.add(paper_id)
                            all_papers.append(paper)

                    # 重新筛选更大的候选池
                    search_count = max(request.target_count * 3, 150)
                    candidate_pool = filter_service.filter_and_sort(
                        papers=all_papers,
                        target_count=search_count,
                        recent_years_ratio=request.recent_years_ratio,
                        english_ratio=request.english_ratio,
                        topic_keywords=topic_keywords
                    )
                    print(f"[SmartGenerate] 扩大后候选池: {len(candidate_pool)} 篇")
                else:
                    print(f"[SmartGenerate] 达到最大重试次数，标记未通过")

                retry_count += 1

        # 7. 验证并修正引用顺序（无论是否通过都要检查）
        content, _ = validator._split_review_and_references(review)
        cited_indices = validator._extract_cited_indices(content)

        if cited_indices:
            order_validation = validator.validate_citation_order(content, cited_indices)
            if not order_validation["passed"]:
                print(f"[SmartGenerate] 引用顺序有问题，尝试修正: {order_validation['message']}")
                renumbered_content, renumbered_papers = generator._renumber_citations_by_appearance(
                    content, cited_papers, cited_indices
                )
                references = generator._format_references(renumbered_papers)
                review = f"{renumbered_content}\n\n## 参考文献\n\n{references}"
                cited_papers = renumbered_papers
                print(f"[SmartGenerate] 引用顺序已修正")

        # 8. 计算统计信息（基于最终被引用文献）
        stats = filter_service.get_statistics(cited_papers)

        # 计算每个搜索查询的被引用论文数量
        cited_paper_ids = {p.get('id') for p in cited_papers}
        for query_result in search_queries_results:
            cited_count = sum(1 for p in query_result['papers'] if p.get('id') in cited_paper_ids)
            query_result['citedCount'] = cited_count
            for paper in query_result['papers']:
                paper['cited'] = paper.get('id') in cited_paper_ids

        # 9. 最终完整验证
        final_validation = validator.validate_review(
            review=review,
            papers=cited_papers
        )

        # 10. 保存记录
        record = record_service.update_success(
            db_session=db_session,
            record=record,
            review=review,
            papers=cited_papers,
            statistics=stats
        )

        return GenerateResponse(
            success=True,
            message="文献综述生成成功" if validation_passed else "文献综述生成完成（部分指标未达标）",
            data={
                "id": record.id,
                "topic": request.topic,
                "review": review,
                "papers": candidate_pool,  # 返回最终使用的候选池
                "statistics": stats,
                "analysis": framework,
                "search_queries_results": search_queries_results,
                "cited_papers_count": len(cited_papers),
                "validation_passed": validation_passed,
                "validation": final_validation,
                "created_at": record.created_at.isoformat()
            }
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        record = record_service.update_failure(
            db_session=db_session,
            record=record,
            error_message=str(e)
        )
        return GenerateResponse(
            success=False,
            message=f"生成失败: {str(e)}"
        )

# ==================== 参考文献验证接口 ====================

class ValidateRequest(BaseModel):
    review: str = Field(..., description="综述内容")
    papers: List[Dict] = Field(..., description="参考文献列表")

@app.post("/api/validate-review")
async def validate_review(request: ValidateRequest):
    """
    验证参考文献质量

    检查：
    1. 引用数量是否>=50篇
    2. 近5年文献占比是否>=50%
    3. 英文文献占比是否>=30%
    4. 引用顺序是否正确（连续编号）
    """
    try:
        validator = ReferenceValidator()
        result = validator.validate_review(
            review=request.review,
            papers=request.papers
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
