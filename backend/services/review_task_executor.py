"""
综述生成任务执行器
将同步的生成逻辑包装成异步任务
"""
import logging
import os
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from services.task_manager import TaskManager, TaskStatus, task_manager
from services.paper_filter import PaperFilterService
from services.smart_review_generator_final import SmartReviewGeneratorFinal
from services.openalex_search import get_openalex_service
from services.semantic_scholar_search import get_semantic_scholar_service
from services.paper_search_agent import PaperSearchAgent
from services.citation_validator_v2 import CitationValidatorV2
from services.review_record_service import ReviewRecordService
from services.stage_recorder import stage_recorder
from services.progress_messages import get_progress, get_progress_message


class ReviewTaskExecutor:
    """综述生成任务执行器"""

    def __init__(self):
        self.filter_service = PaperFilterService()
        self.record_service = ReviewRecordService()

    async def execute_task(self, task_id: str, db_session: Session):
        """
        执行综述生成任务（3步流程）

        步骤1: PaperSearchAgent 搜索文献
        步骤2: SmartReviewGeneratorFinal 生成综述
        步骤3: CitationValidatorV2 引用校验修复

        Args:
            task_id: 任务ID
            db_session: 数据库会话
        """
        task = task_manager.get_task(task_id)
        if not task:
            logger.debug(f"[TaskExecutor] 任务不存在: {task_id}")
            return

        # 尝试获取执行槽位（并发控制，支持排队提示和超时）
        acquired = await task_manager.acquire_slot(task_id, timeout=1800)  # 30分钟超时
        if not acquired:
            logger.debug(f"[TaskExecutor] 任务 {task_id} 排队超时")
            task_manager.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error="系统繁忙，排队超时（超过30分钟），请稍后重试"
            )
            return

        params = task.params
        topic = task.topic

        # 创建任务记录
        task_user_id = getattr(task, 'user_id', None)
        stage_recorder.create_task(task_id, topic, params, user_id=task_user_id)
        task_manager.update_task_status(task_id, TaskStatus.PROCESSING)

        try:
            # 创建数据库记录
            record = self.record_service.create_record(
                db_session=db_session,
                topic=topic,
                target_count=params.get('target_count', 50),
                recent_years_ratio=params.get('recent_years_ratio', 0.5),
                english_ratio=params.get('english_ratio', 0.3),
                is_paid=getattr(task, 'is_paid', False),
                user_id=task_user_id
            )

            # =====================================================
            # 步骤1: PaperSearchAgent 搜索文献
            # =====================================================
            logger.debug("\n" + "=" * 80)
            logger.debug(f"[步骤1] 搜索文献: {topic}")
            logger.debug("=" * 80)

            language = params.get('language', 'zh')
            task_manager.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress=get_progress("searching", language)
            )


            # 使用 OpenAlex 检索（精度与 SS 同级，无需 API Key，速率更高）
            # 方法论描述中使用 "Danmo Scholar" 作为对外展示的数据源名称
            search_service = get_openalex_service()
            search_agent = PaperSearchAgent(ss_service=search_service)
            all_papers = await search_agent.search(
                topic=topic,
                search_years=params.get('search_years', 10),
                target_count=params.get('target_count', 50)
            )

            # Fallback: OA 结果不足时切到 Semantic Scholar
            if len(all_papers) < 20:
                logger.warning(f"[步骤1] OA 仅 {len(all_papers)} 篇，fallback 到 SS")
                ss_service = get_semantic_scholar_service()
                ss_agent = PaperSearchAgent(ss_service=ss_service)
                ss_papers = await ss_agent.search(
                    topic=topic,
                    search_years=params.get('search_years', 10),
                    target_count=params.get('target_count', 50)
                )
                # 合并去重
                seen_ids = {p.get("id") or p.get("paperId") for p in all_papers}
                for p in ss_papers:
                    pid = p.get("id") or p.get("paperId")
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        all_papers.append(p)
                logger.info(f"[步骤1] SS fallback 补充后共 {len(all_papers)} 篇")

            logger.debug(f"[步骤1] 搜索完成: 共 {len(all_papers)} 篇文献")

            if not all_papers:
                raise Exception(f'未找到关于「{topic}」的相关文献')

            MIN_PAPERS_THRESHOLD = 20
            if len(all_papers) < MIN_PAPERS_THRESHOLD:
                raise Exception(f'搜索到的文献数量不足，只有 {len(all_papers)} 篇，至少需要 {MIN_PAPERS_THRESHOLD} 篇')

            # 记录步骤1完成
            stage_recorder.record_paper_search(
                task_id=task_id,
                outline={'topic': topic},
                search_queries_count=1,
                papers_count=len(all_papers),
                papers_summary=self.filter_service.get_statistics(all_papers),
                papers_sample=all_papers[:20]
            )
            stage_recorder.update_task_status(task_id, status="processing", current_stage="文献搜索完成")

            # 通知前端：文献搜索完成，附带文献列表
            papers_preview = []
            for p in all_papers[:30]:
                papers_preview.append({
                    "id": p.get("id", ""),
                    "title": p.get("title", ""),
                    "authors": p.get("authors", []),
                    "year": p.get("year"),
                    "cited_by_count": p.get("cited_by_count", 0),
                    "abstract": (p.get("abstract") or "")[:300],
                    "doi": p.get("doi"),
                    "is_english": p.get("is_english", True),
                })
            task_manager.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress={
                    "step": "papers_found",
                    "message": get_progress_message("papers_found", language, papers_count=len(all_papers)),
                    "papers": papers_preview,
                    "papers_count": len(all_papers),
                }
            )

            # =====================================================
            # 步骤2: SmartReviewGeneratorFinal 生成综述
            # =====================================================
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise Exception("DEEPSEEK_API_KEY not configured")

            logger.debug("\n" + "=" * 80)
            logger.debug(f"[步骤2] 生成综述（最终版）")
            logger.debug(f"[步骤2] 候选文献: {len(all_papers)} 篇")
            logger.debug("=" * 80)

            task_manager.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress=get_progress("generating", language)
            )

            final_generator = SmartReviewGeneratorFinal(
                deepseek_api_key=api_key,
                deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            )

            # 构建搜索参数，用于生成文献检索方法论说明
            search_params = {
                "search_years": params.get('search_years', 10),
                "target_count": params.get('target_count', 50),
                "recent_years_ratio": params.get('recent_years_ratio', 0.5),
                "english_ratio": params.get('english_ratio', 0.3),
                "search_platform": "Semantic Scholar",
                "sort_by": "被引量降序"
            }

            result = await final_generator.generate_review_from_papers(
                topic=topic,
                papers=all_papers,
                model=params.get('review_model', 'deepseek-reasoner'),
                search_params=search_params,
                language=params.get('language', 'zh')
            )

            review = result["review"]
            cited_papers = result["cited_papers"]
            final_validation = result.get("validation", {"valid": True, "issues": []})

            # =====================================================
            # 步骤3: CitationValidatorV2 引用校验修复
            # =====================================================
            logger.debug("\n[步骤3] 使用 CitationValidatorV2 进行额外引用校验...")
            validator_v2 = CitationValidatorV2()
            validation_result = validator_v2.validate_and_fix(review, cited_papers)

            if not validation_result.valid:
                logger.debug(f"[步骤3] 发现问题: {validation_result.issues}")
                if validation_result.fixed_content:
                    logger.debug("[步骤3] 使用修复后的综述内容")
                    review = validation_result.fixed_content
                if validation_result.fixed_references:
                    logger.debug(f"[步骤3] 使用修复后的参考文献 ({len(validation_result.fixed_references)} 篇)")
                    cited_papers = validation_result.fixed_references
                final_validation = {
                    "valid": validation_result.valid,
                    "issues": validation_result.issues
                }
            else:
                logger.debug("[步骤3] ✓ 引用规范校验通过")
                # 使用 v2 改进版格式化参考文献（处理 arXiv ID、Unicode 等）
                improved_refs = validator_v2.format_references_ieee_improved(cited_papers)
                if "## References" in review:
                    review = review[:review.index("## References")] + "## References\n\n" + improved_refs
                    logger.debug("[步骤3] 使用改进版 IEEE 格式化参考文献")
            # 统计信息
            stats = self.filter_service.get_statistics(cited_papers)

            # 标记文献是否被引用
            cited_paper_ids = {p.get('id') for p in cited_papers}
            for paper in all_papers:
                if 'relevance_score' not in paper:
                    paper['relevance_score'] = 0
                paper['cited'] = paper.get('id') in cited_paper_ids

            # 记录步骤2完成
            stage_recorder.update_task_status(task_id, status="processing", current_stage="生成综述")

            papers_summary = []
            for p in cited_papers:
                url = p.get('url') or ''
                papers_summary.append({
                    'id': p.get('id'),
                    'title': p.get('title', '')[:200],
                    'authors': p.get('authors', [])[:5],
                    'year': p.get('year'),
                    'venue': (p.get('journal', '') or p.get('venue', ''))[:100],
                    'cited_by_count': p.get('cited_by_count', 0),
                    'url': url[:500] if url else ''
                })

            candidate_pool_summary = []
            for p in all_papers:
                url = p.get('url') or ''
                candidate_pool_summary.append({
                    'id': p.get('id'),
                    'title': p.get('title', '')[:200],
                    'authors': p.get('authors', [])[:5],
                    'year': p.get('year'),
                    'venue': (p.get('journal', '') or p.get('venue', ''))[:100],
                    'cited_by_count': p.get('cited_by_count', 0),
                    'url': url[:500] if url else ''
                })

            stage_recorder.record_review_generation(
                task_id=task_id,
                papers_count=len(all_papers),
                review_length=len(review),
                citation_count=review.count('['),
                cited_papers_count=len(cited_papers),
                validation_result=final_validation,
                review=review,
                papers_summary=papers_summary,
                candidate_pool_summary=candidate_pool_summary
            )

            # 保存数据库记录
            record = self.record_service.update_success(
                db_session=db_session,
                record=record,
                review=review,
                papers=cited_papers,
                statistics=stats
            )

            # 保存对比矩阵为独立任务记录（便于 Profile 页面展示）
            comparison_matrix = result.get("comparison_matrix")
            if comparison_matrix:
                import uuid as _uuid
                from models import ReviewTask as _RT
                matrix_task_id = str(_uuid.uuid4())[:8]
                matrix_task = _RT(
                    id=matrix_task_id,
                    topic=topic,
                    user_id=task_user_id,
                    status="completed",
                    params={
                        "type": "comparison_matrix_only",
                        "comparison_matrix": comparison_matrix,
                        "statistics": stats,
                        "papers": papers_summary,
                        "source_task_id": task_id,
                    }
                )
                db_session.add(matrix_task)
                db_session.commit()
                logger.debug(f"对比矩阵已保存为独立任务: {matrix_task_id}")

            # 任务完成
            task_manager.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                result={
                    "id": record.id,
                    "topic": topic,
                    "review": review,
                    "papers": cited_papers,
                    "candidate_pool": all_papers,
                    "statistics": stats,
                    "cited_papers_count": len(cited_papers),
                    "validation": final_validation,
                    "created_at": record.created_at.isoformat()
                }
            )

            stage_recorder.update_task_status(
                task_id,
                status="completed",
                current_stage="完成",
                completed_at=datetime.now(),
                review_record_id=record.id
            )

        except Exception as e:
            logger.error("综述生成任务失败: task_id=%s, error=%s", task_id, e, exc_info=True)

            if task_id in task_manager._running_tasks:
                task_manager.release_slot(task_id)

            # 映射常见错误到友好提示
            error_msg = "生成失败，请稍后重试"
            error_str = str(e)
            if "未找到关于" in error_str:
                error_msg = error_str
            elif "搜索到的文献数量不足" in error_str:
                error_msg = error_str
            elif "DEEPSEEK_API_KEY" in error_str:
                error_msg = "服务配置异常，请联系客服"
            elif "积分" in error_str or "credit" in error_str.lower():
                error_msg = error_str
            task_manager.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=error_msg
            )

            stage_recorder.update_task_status(
                task_id,
                status="failed",
                current_stage="失败",
                error_message=error_msg,
                completed_at=datetime.now()
            )

            try:
                if 'record' in locals():
                    self.record_service.update_failure(
                        db_session=db_session,
                        record=record,
                        error_message=str(e)
                    )
            except Exception as e:
                logger.error("任务失败后更新状态异常: task_id=%s, error=%s", task_id, e)

            # 退还用户额度
            task_user_id = getattr(task, 'user_id', None)
            if task_user_id:
                try:
                    from main import refund_credit
                    from authkit.database import SessionLocal as AuthSessionLocal
                    if AuthSessionLocal:
                        auth_db = AuthSessionLocal()
                        try:
                            credit_cost = params.get('credit_cost', 2)
                            refund_credit(task_user_id, auth_db, cost=credit_cost)
                            logger.info("已退还用户 %s 的 %s 个 credit", task_user_id, credit_cost)
                        finally:
                            auth_db.close()
                except Exception as refund_err:
                    logger.error("额度退还失败: user_id=%s, error=%s", task_user_id, refund_err)

    async def search_papers_only(
        self,
        topic: str,
        params: dict,
        user_id: Optional[int] = None,
    ) -> dict:
        """
        只查找文献，不生成综述（使用 PaperSearchAgent）
        搜索结果持久化到数据库：论文入 PaperMetadata 总库，搜索任务入 ReviewTask + PaperSearchStage。

        Args:
            topic: 论文主题
            params: 参数配置
            user_id: 用户ID（可选，登录用户的搜索任务会关联）

        Returns:
            {
                'task_id': 搜索任务ID（可用于后续生成综述）,
                'all_papers': 所有搜索到的文献,
                'statistics': 统计信息,
            }
        """
        import uuid
        from services.paper_metadata_dao import PaperMetadataDAO
        from database import db as database

        # 1. 执行搜索（使用 OpenAlex，速率更高）
        from services.openalex_search import get_openalex_service
        search_service = get_openalex_service()
        search_agent = PaperSearchAgent(ss_service=search_service)
        all_papers = await search_agent.search(
            topic=topic,
            search_years=params.get('search_years', 10),
            target_count=params.get('target_count', 50)
        )

        # Fallback: OA 结果不足时切到 Semantic Scholar
        if len(all_papers) < 20:
            logger.warning(f"[search_papers_only] OA 仅 {len(all_papers)} 篇，fallback 到 SS")
            from services.semantic_scholar_search import get_semantic_scholar_service as _get_ss
            ss_service = _get_ss()
            ss_agent = PaperSearchAgent(ss_service=ss_service)
            ss_papers = await ss_agent.search(
                topic=topic,
                search_years=params.get('search_years', 10),
                target_count=params.get('target_count', 50)
            )
            seen_ids = {p.get("id") or p.get("paperId") for p in all_papers}
            for p in ss_papers:
                pid = p.get("id") or p.get("paperId")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    all_papers.append(p)
            logger.info(f"[search_papers_only] SS fallback 补充后共 {len(all_papers)} 篇")

        stats = self.filter_service.get_statistics(all_papers)
        logger.debug(f"[search_papers_only] 搜索完成: {len(all_papers)} 篇文献")

        # 2. 创建 ReviewTask 记录（标记为 search_only）
        task_id = str(uuid.uuid4())[:8]
        task_params = {**params, 'type': 'search_only'}
        stage_recorder.create_task(task_id, topic, task_params, user_id=user_id)
        stage_recorder.update_task_status(task_id, status="completed", current_stage="文献搜索完成")

        # 3. 将论文存入 PaperMetadata 总库
        if database.engine is None:
            database.connect()
        with next(database.get_session()) as session:
            paper_dao = PaperMetadataDAO(session)
            try:
                saved_count = paper_dao.save_papers(all_papers, source="openalex")
                logger.debug(f"[search_papers_only] 论文入总库: 新增 {saved_count} 篇")
            except Exception as e:
                logger.error(f"[search_papers_only] 论文入库失败（不影响返回）: {e}")

        # 4. 记录搜索阶段（存全部论文样本，便于后续复用）
        stage_recorder.record_paper_search(
            task_id=task_id,
            outline={'topic': topic},
            search_queries_count=1,
            papers_count=len(all_papers),
            papers_summary=stats,
            papers_sample=all_papers,  # 存全部论文，便于后续生成综述时复用
            save_all_papers=True
        )

        return {
            'task_id': task_id,
            'all_papers': all_papers,
            'statistics': stats,
        }

    async def execute_task_with_papers(self, task_id: str, db_session: Session, papers: list):
        """
        使用已有论文列表执行综述生成（跳过搜索阶段）

        Args:
            task_id: 任务ID
            db_session: 数据库会话
            papers: 已有的论文列表
        """
        task = task_manager.get_task(task_id)
        if not task:
            logger.debug(f"[TaskExecutor] 任务不存在: {task_id}")
            return

        acquired = await task_manager.acquire_slot(task_id, timeout=1800)
        if not acquired:
            task_manager.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error="系统繁忙，排队超时，请稍后重试"
            )
            return

        params = task.params
        topic = task.topic

        task_manager.update_task_status(task_id, TaskStatus.PROCESSING)

        try:
            # 创建数据库记录
            record = self.record_service.create_record(
                db_session=db_session,
                topic=topic,
                target_count=params.get('target_count', 50),
                recent_years_ratio=params.get('recent_years_ratio', 0.5),
                english_ratio=params.get('english_ratio', 0.3),
                is_paid=getattr(task, 'is_paid', False),
                user_id=getattr(task, 'user_id', None)
            )

            # 记录搜索阶段（使用已有论文）
            all_papers = papers
            stats = self.filter_service.get_statistics(all_papers)

            stage_recorder.record_paper_search(
                task_id=task_id,
                outline={'topic': topic, 'source': 'reused'},
                search_queries_count=0,
                papers_count=len(all_papers),
                papers_summary=stats,
                papers_sample=all_papers[:20]
            )
            stage_recorder.update_task_status(task_id, status="processing", current_stage="复用已有文献")

            # 阶段2: 生成综述（直接使用已有论文）
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise Exception("DEEPSEEK_API_KEY not configured")

            logger.debug(f"[execute_task_with_papers] 使用已有 {len(all_papers)} 篇文献生成综述")

            language = params.get('language', 'zh')
            task_manager.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress=get_progress("generating", language)
            )

            final_generator = SmartReviewGeneratorFinal(
                deepseek_api_key=api_key,
                deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            )

            search_params = {
                "search_years": params.get('search_years', 10),
                "target_count": params.get('target_count', 50),
                "recent_years_ratio": params.get('recent_years_ratio', 0.5),
                "english_ratio": params.get('english_ratio', 0.3),
                "search_platform": "Semantic Scholar",
                "sort_by": "被引量降序"
            }

            result = await final_generator.generate_review_from_papers(
                topic=topic,
                papers=all_papers,
                model=params.get('review_model', 'deepseek-reasoner'),
                search_params=search_params,
                language=params.get('language', 'zh')
            )

            review = result["review"]
            cited_papers = result["cited_papers"]
            final_validation = result.get("validation", {"valid": True, "issues": []})

            # 阶段3: 引用校验
            validator_v2 = CitationValidatorV2()
            validation_result = validator_v2.validate_and_fix(review, cited_papers)

            if not validation_result.valid:
                if validation_result.fixed_content:
                    review = validation_result.fixed_content
                if validation_result.fixed_references:
                    cited_papers = validation_result.fixed_references
                final_validation = {
                    "valid": validation_result.valid,
                    "issues": validation_result.issues
                }
            else:
                improved_refs = validator_v2.format_references_ieee_improved(cited_papers)
                if "## References" in review:
                    review = review[:review.index("## References")] + "## References\n\n" + improved_refs

            cited_stats = self.filter_service.get_statistics(cited_papers)

            # 标记文献是否被引用
            cited_paper_ids = {p.get('id') for p in cited_papers}
            for paper in all_papers:
                if 'relevance_score' not in paper:
                    paper['relevance_score'] = 0.5
                paper['is_cited'] = paper.get('id') in cited_paper_ids

            # 保存最终结果
            record = self.record_service.update_success(
                db_session=db_session,
                record=record,
                review=review,
                papers=cited_papers,
                statistics=cited_stats
            )

            stage_recorder.record_review_generation(
                task_id=task_id,
                papers_count=len(all_papers),
                review_length=len(review),
                citation_count=review.count('['),
                cited_papers_count=len(cited_papers),
                validation_result=final_validation,
                review=review
            )

            stage_recorder.update_task_status(
                task_id,
                status="completed",
                completed_at=datetime.now(),
                review_record_id=record.id
            )

            task_manager.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                result={
                    "review": review,
                    "papers": cited_papers,
                    "statistics": cited_stats,
                    "record_id": record.id,
                    "task_id": task_id
                }
            )

            logger.debug(f"[execute_task_with_papers] 综述生成完成: record_id={record.id}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"[execute_task_with_papers] 任务执行失败: {e}")

            if task_id in task_manager._running_tasks:
                task_manager.release_slot(task_id)

            # 映射常见错误到友好提示
            error_msg = "生成失败，请稍后重试"
            error_str = str(e)
            if "未找到关于" in error_str:
                error_msg = error_str
            elif "搜索到的文献数量不足" in error_str:
                error_msg = error_str
            elif "DEEPSEEK_API_KEY" in error_str:
                error_msg = "服务配置异常，请联系客服"
            elif "积分" in error_str or "credit" in error_str.lower():
                error_msg = error_str

            stage_recorder.update_task_status(
                task_id,
                status="failed",
                current_stage="失败",
                error_message=error_msg,
                completed_at=datetime.now()
            )
            task_manager.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=error_msg
            )

            try:
                if 'record' in locals():
                    self.record_service.update_failure(
                        db_session=db_session,
                        record=record,
                        error_message=str(e)
                    )
            except Exception as update_err:
                logger.error("任务失败后更新状态异常: task_id=%s, error=%s", task_id, update_err)

            # 退还额度
            task_user_id = getattr(task, 'user_id', None)
            if task_user_id:
                try:
                    from main import refund_credit
                    from authkit.database import SessionLocal as AuthSessionLocal
                    if AuthSessionLocal:
                        auth_db = AuthSessionLocal()
                        try:
                            credit_cost = params.get('credit_cost', 2)
                            refund_credit(task_user_id, auth_db, cost=credit_cost)
                            logger.info("已退还用户 %s 的 %s 个 credit", task_user_id, credit_cost)
                        finally:
                            auth_db.close()
                except Exception as refund_err:
                    logger.error("额度退还失败: user_id=%s, error=%s", task_user_id, refund_err)

    async def execute_comparison_matrix_only(
        self,
        task_id: str,
        db_session: Session,
        reuse_task_id: str = "",
        language: str = "zh"
    ):
        """
        仅执行对比矩阵生成（不生成完整综述）

        Args:
            task_id: 任务ID
            db_session: 数据库会话
            reuse_task_id: 复用已有搜索任务的ID（可选）
            language: 生成语言（zh 或 en）
        """
        import time
        from models import PaperSearchStage

        task = task_manager.get_task(task_id)
        if not task:
            logger.debug(f"[TaskExecutor] 任务不存在: {task_id}")
            return

        topic = task.topic

        task_manager.update_task_status(
            task_id,
            TaskStatus.PROCESSING,
            progress=get_progress("preparing", language)
        )

        try:
            start_time = time.time()

            # 步骤1: 获取论文数据（要么复用，要么重新搜索）
            all_papers = []
            if reuse_task_id:
                # 从 PaperSearchStage 加载已有论文
                stage = db_session.query(PaperSearchStage).filter_by(
                    task_id=reuse_task_id
                ).order_by(PaperSearchStage.id.desc()).first()

                if not stage or not stage.papers_sample:
                    raise Exception(f"未找到搜索任务 {reuse_task_id} 的文献数据")

                all_papers = stage.papers_sample
                logger.debug(f"[execute_comparison_matrix_only] 复用已有论文: {len(all_papers)} 篇")
            else:
                # 重新搜索论文
                logger.debug(f"[execute_comparison_matrix_only] 开始搜索论文: {topic}")
                task_manager.update_task_status(
                    task_id,
                    TaskStatus.PROCESSING,
                    progress=get_progress("searching", language)
                )

                from services.openalex_search import get_openalex_service
                search_service = get_openalex_service()
                search_agent = PaperSearchAgent(ss_service=search_service)
                all_papers = await search_agent.search(
                    topic=topic,
                    search_years=10,
                    target_count=50
                )

                # Fallback: OA 结果不足时切到 Semantic Scholar
                if len(all_papers) < 20:
                    logger.warning(f"[execute_comparison_matrix_only] OA 仅 {len(all_papers)} 篇，fallback 到 SS")
                    from services.semantic_scholar_search import get_semantic_scholar_service as _get_ss
                    ss_svc = _get_ss()
                    ss_ag = PaperSearchAgent(ss_service=ss_svc)
                    ss_pp = await ss_ag.search(topic=topic, search_years=10, target_count=50)
                    seen_ids = {p.get("id") or p.get("paperId") for p in all_papers}
                    for p in ss_pp:
                        pid = p.get("id") or p.get("paperId")
                        if pid and pid not in seen_ids:
                            seen_ids.add(pid)
                            all_papers.append(p)
                    logger.info(f"[execute_comparison_matrix_only] SS fallback 补充后共 {len(all_papers)} 篇")

                logger.debug(f"[execute_comparison_matrix_only] 搜索完成: {len(all_papers)} 篇文献")

            if not all_papers:
                raise Exception(f'未找到关于「{topic}」的相关文献')

            # 步骤2: 生成对比矩阵
            logger.debug(f"[execute_comparison_matrix_only] 开始生成对比矩阵")
            task_manager.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress={
                    "step": "generating_matrix",
                    "message": get_progress("generating_matrix", language),
                    "papers": all_papers[:30]
                }
            )

            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise Exception("DEEPSEEK_API_KEY not configured")

            from services.smart_review_generator_final import SmartReviewGeneratorFinal

            final_generator = SmartReviewGeneratorFinal(
                deepseek_api_key=api_key,
                deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            )

            result = await final_generator.generate_comparison_matrix_only(
                topic=topic,
                papers=all_papers,
                language=language
            )

            comparison_matrix = result["comparison_matrix"]
            papers_used = result.get("papers_used", len(all_papers))
            total_time = time.time() - start_time

            statistics = {
                "papers_used": papers_used,
                "total_time_seconds": round(total_time, 2),
                "generated_at": datetime.now().isoformat()
            }

            # 更新任务状态（完成）
            task_manager.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                result={
                    "topic": topic,
                    "comparison_matrix": comparison_matrix,
                    "statistics": statistics,
                    "papers": all_papers
                }
            )

            # 同时更新数据库中的任务 params，以便后续查询
            from models import ReviewTask
            from sqlalchemy.orm.attributes import flag_modified
            review_task = db_session.query(ReviewTask).filter_by(id=task_id).first()
            if review_task:
                review_task.status = "completed"
                review_task.completed_at = datetime.now()
                # 将结果存储在 params 中，作为临时方案
                # 创建新的 params 字典以确保 SQLAlchemy 检测到变更
                params = dict(review_task.params or {})
                params["comparison_matrix"] = comparison_matrix
                params["statistics"] = statistics
                params["papers"] = all_papers
                review_task.params = params
                # 显式标记 params 字段为已修改
                flag_modified(review_task, "params")
                db_session.commit()

            stage_recorder.update_task_status(
                task_id,
                status="completed",
                current_stage="完成",
                completed_at=datetime.now()
            )

            logger.debug(f"[execute_comparison_matrix_only] 对比矩阵生成完成")

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error("对比矩阵生成任务失败: task_id=%s, error=%s", task_id, e, exc_info=True)

            if task_id in task_manager._running_tasks:
                task_manager.release_slot(task_id)

            # 映射常见错误到友好提示
            error_msg = "生成失败，请稍后重试"
            error_str = str(e)
            if "未找到关于" in error_str:
                error_msg = error_str
            elif "DEEPSEEK_API_KEY" in error_str:
                error_msg = "服务配置异常，请联系客服"
            elif "积分" in error_str or "credit" in error_str.lower():
                error_msg = error_str

            task_manager.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=error_msg
            )

            stage_recorder.update_task_status(
                task_id,
                status="failed",
                current_stage="失败",
                error_message=error_msg,
                completed_at=datetime.now()
            )

            # 退还 credit（对比矩阵需要 1 credit）
            task_user_id = getattr(task, 'user_id', None)
            if task_user_id:
                try:
                    from main import refund_credit
                    from authkit.database import SessionLocal as AuthSessionLocal
                    if AuthSessionLocal:
                        auth_db = AuthSessionLocal()
                        try:
                            refund_credit(task_user_id, auth_db, cost=1)
                            logger.info("已退还用户 %s 的 1 个 credit（对比矩阵失败）", task_user_id)
                        finally:
                            auth_db.close()
                except Exception as refund_err:
                    logger.error("额度退还失败: user_id=%s, error=%s", task_user_id, refund_err)
