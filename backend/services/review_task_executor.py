"""
综述生成任务执行器
将同步的生成逻辑包装成异步任务
"""
import os
from typing import Dict
from sqlalchemy.orm import Session

from services.task_manager import TaskManager, TaskStatus, task_manager
from services.smart_paper_search import SmartPaperSearchService
from services.paper_filter import PaperFilterService
from services.review_generator import ReviewGeneratorService
from services.reference_validator import ReferenceValidator
from services.review_record_service import ReviewRecordService
from services.citation_order_checker import CitationOrderChecker
from services.scholarflux_wrapper import ScholarFlux
from database import get_db


class ReviewTaskExecutor:
    """综述生成任务执行器"""

    def __init__(self):
        self.scholarflux = ScholarFlux()
        self.search_service = SmartPaperSearchService(self.scholarflux, get_db)
        self.filter_service = PaperFilterService()
        self.record_service = ReviewRecordService()

    async def execute_task(self, task_id: str, db_session: Session):
        """
        执行综述生成任务

        Args:
            task_id: 任务ID
            db_session: 数据库会话
        """
        task = task_manager.get_task(task_id)
        if not task:
            print(f"[TaskExecutor] 任务不存在: {task_id}")
            return

        # 尝试获取执行槽位（并发控制）
        acquired = await task_manager.acquire_slot(task_id)
        if not acquired:
            # 无法获取槽位，等待当前任务完成后再重试
            print(f"[TaskExecutor] 无法获取执行槽位，任务 {task_id} 将等待")
            task_manager.update_task_status(
                task_id,
                TaskStatus.PENDING,
                progress={"step": "waiting", "message": "等待可用执行槽位..."}
            )
            return

        params = task.params
        topic = task.topic

        # 更新状态为处理中
        task_manager.update_task_status(task_id, TaskStatus.PROCESSING)

        try:
            # 创建数据库记录
            record = self.record_service.create_record(
                db_session=db_session,
                topic=topic,
                target_count=params.get('target_count', 50),
                recent_years_ratio=params.get('recent_years_ratio', 0.5),
                english_ratio=params.get('english_ratio', 0.3)
            )

            # 更新进度
            task_manager.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress={"step": "analyzing", "message": "正在分析题目..."}
            )

            # 1. 智能分析题目
            from services.hybrid_classifier import FrameworkGenerator
            gen = FrameworkGenerator()
            framework = await gen.generate_framework(topic, enable_llm_validation=True)

            # 提取场景特异性指导
            specificity_guidance = framework.get('specificity_guidance', {})

            # 2. 增强文献搜索（使用新的搜索方法）
            search_queries = framework.get('search_queries', [])

            # 使用LLM验证和修复搜索关键词
            if search_queries:
                try:
                    from services.hybrid_classifier import HybridTopicClassifier
                    classifier = HybridTopicClassifier()
                    print(f"[TaskExecutor] 原始搜索查询数量: {len(search_queries)}")
                    for i, q in enumerate(search_queries[:5]):
                        print(f"  [{i+1}] {q.get('query', '')[:50]}... (lang: {q.get('lang', 'N/A')})")

                    search_queries = await classifier.validate_and_fix_search_queries(
                        title=topic,
                        queries=search_queries
                    )

                    print(f"[TaskExecutor] 修复后搜索查询数量: {len(search_queries)}")
                    for i, q in enumerate(search_queries[:5]):
                        print(f"  [{i+1}] {q.get('query', '')[:50]}... (lang: {q.get('lang', 'N/A')})")
                except Exception as e:
                    print(f"[TaskExecutor] LLM关键词验证失败: {e}")
                    import traceback
                    traceback.print_exc()

            # 使用新的增强搜索方法
            all_papers, search_queries_results = await self._search_literature_with_requirements(
                topic=topic,
                search_queries=search_queries,
                params=params,
                framework=framework,
                task_id=task_id
            )

            if not all_papers:
                raise Exception(f'未找到关于「{topic}」的相关文献')

            # 3. 筛选文献（增强版）
            task_manager.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress={"step": "filtering", "message": "正在筛选文献..."}
            )

            topic_keywords = gen.extract_relevance_keywords(framework)

            # 获取配置参数
            target_count = params.get('target_count', 50)
            recent_years_ratio = params.get('recent_years_ratio', 0.5)
            english_ratio = params.get('english_ratio', 0.3)

            # 第1次筛选：使用标准要求
            search_count = max(target_count * 2, 100)
            filtered_papers = self.filter_service.filter_and_sort(
                papers=all_papers,
                target_count=search_count,
                recent_years_ratio=recent_years_ratio,
                english_ratio=english_ratio,
                topic_keywords=topic_keywords
            )

            # 检查是否满足要求
            filter_stats = self.filter_service.get_statistics(filtered_papers)
            print(f"[TaskExecutor] 第1次筛选结果: 总数={filter_stats['total']}, "
                  f"近5年比例={filter_stats['recent_ratio']:.2%}, "
                  f"英文比例={filter_stats['english_ratio']:.2%}")

            # 检查是否满足数量要求
            requirements_met = (
                filter_stats['total'] >= target_count and
                filter_stats['recent_ratio'] >= recent_years_ratio * 0.8 and  # 允许20%误差
                filter_stats['english_ratio'] >= english_ratio * 0.8
            )

            if not requirements_met:
                print(f"[TaskExecutor] 第1次筛选未达标，尝试放宽要求重新筛选")

                # 第2次筛选：放宽要求
                filtered_papers = self.filter_service.filter_and_sort(
                    papers=all_papers,
                    target_count=search_count,
                    recent_years_ratio=recent_years_ratio * 0.5,  # 放宽年份要求
                    english_ratio=english_ratio * 0.5,  # 放宽英文比例要求
                    topic_keywords=topic_keywords
                )

                filter_stats = self.filter_service.get_statistics(filtered_papers)
                print(f"[TaskExecutor] 第2次筛选结果: 总数={filter_stats['total']}, "
                      f"近5年比例={filter_stats['recent_ratio']:.2%}, "
                      f"英文比例={filter_stats['english_ratio']:.2%}")

            # 检查是否满足最低数量要求
            if filter_stats['total'] < target_count:
                print(f"[TaskExecutor] 筛选后文献数量不足（{filter_stats['total']}/{target_count}），尝试补充搜索")

                # === 调用LLM调整章节主题和关键词，进行补充搜索 ===
                try:
                    task_manager.update_task_status(
                        task_id,
                        TaskStatus.PROCESSING,
                        progress={"step": "adjusting", "message": "正在调整搜索策略..."}
                    )

                    # 调用LLM生成新的搜索关键词
                    new_search_keywords = await self._llm_adjust_search_strategy(
                        topic=topic,
                        framework=framework,
                        current_count=filter_stats['total'],
                        target_count=target_count
                    )

                    # 使用新的关键词进行补充搜索
                    for keyword in new_search_keywords[:5]:
                        task_manager.update_task_status(
                            task_id,
                            TaskStatus.PROCESSING,
                            progress={"step": "searching", "message": f"正在补充搜索: {keyword}..."}
                        )

                        additional_papers = await self.search_service.search(
                            query=keyword,
                            years_ago=params.get('search_years', 10) + 5,
                            limit=30,
                            use_all_sources=True
                        )

                        # 去重并添加到筛选结果
                        existing_ids = {p.get('id') for p in filtered_papers}
                        for paper in additional_papers:
                            if paper.get('id') not in existing_ids:
                                filtered_papers.append(paper)

                        # 检查是否已满足要求
                        if len(filtered_papers) >= target_count:
                            print(f"[TaskExecutor] 补充搜索后达标，停止搜索")
                            break

                except Exception as e:
                    print(f"[TaskExecutor] LLM调整搜索策略失败: {e}")
                    import traceback
                    traceback.print_exc()

            # 保底：如果仍然不足，使用所有文献
            if len(filtered_papers) < max(target_count, 10):
                print(f"[TaskExecutor] 筛选后文献仍然不足，使用所有可用文献")
                # 按相关性评分排序
                all_papers_with_score = []
                for paper in all_papers:
                    score = self._calculate_relevance_score(paper, topic_keywords)
                    all_papers_with_score.append({**paper, '_relevance_score': score})

                all_papers_with_score.sort(key=lambda x: x.get('_relevance_score', 0), reverse=True)
                filtered_papers = all_papers_with_score[:max(target_count * 2, 100)]

                # 转换 _relevance_score 为 relevance_score
                for paper in filtered_papers:
                    if '_relevance_score' in paper:
                        paper['relevance_score'] = paper.pop('_relevance_score')

            # 最终统计
            filter_stats = self.filter_service.get_statistics(filtered_papers)
            print(f"[TaskExecutor] 最终筛选结果: 总数={filter_stats['total']}, "
                  f"近5年比例={filter_stats['recent_ratio']:.2%}, "
                  f"英文比例={filter_stats['english_ratio']:.2%}")

            # 4. 生成综述
            task_manager.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress={"step": "preselecting", "message": "正在预选高相关文献..."}
            )

            api_key = os.getenv("DEEPSEEK_API_KEY")
            aminer_token = os.getenv("AMINER_API_TOKEN")

            if not api_key:
                raise Exception("DEEPSEEK_API_KEY not configured")

            # === 预选文献：从筛选后的文献池中智能预选60篇 ===
            # 要求（在范围内随机）：
            # 1. 从100篇文献池中
            # 2. 英文文献：30%～45%（约18～27篇）
            # 3. 近5年文献：50%～80%（约30～48篇）
            # 4. 总共输出60篇

            import random
            english_ratio = random.uniform(0.30, 0.45)  # 英文文献比例：30%～45%
            recent_ratio = random.uniform(0.50, 0.80)  # 近5年文献比例：50%～80%

            min_english = int(60 * english_ratio)
            min_recent_count = int(60 * recent_ratio)

            print(f"[预选] 本次随机目标: 英文比例={english_ratio:.2%} ({min_english}篇), "
                  f"近5年比例={recent_ratio:.2%} ({min_recent_count}篇)")

            preselected_papers = self._preselect_papers_with_requirements(
                papers=filtered_papers,
                target_count=60,
                min_english=min_english,
                min_recent_ratio=recent_ratio
            )

            print(f"[TaskExecutor] 预选文献: {len(filtered_papers)} → {len(preselected_papers)} 篇")

            # 验证预选结果
            preselect_stats = self.filter_service.get_statistics(preselected_papers)
            print(f"[TaskExecutor] 预选结果: 总数={preselect_stats['total']}, "
                  f"英文={preselect_stats['english']}, "
                  f"近5年={preselect_stats['recent_count']}, "
                  f"比例={preselect_stats['recent_ratio']:.2%}")

            task_manager.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress={"step": "generating", "message": f"正在生成综述 (候选文献: {len(preselected_papers)}篇)..."}
            )

            generator = ReviewGeneratorService(api_key=api_key, aminer_token=aminer_token)

            review, cited_papers = await generator.generate_review(
                topic=topic,
                papers=preselected_papers,
                specificity_guidance=specificity_guidance
            )

            # 5. 验证和修复（增强版）
            task_manager.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress={"step": "validating", "message": "正在验证和修复引用..."}
            )

            # 使用增强的验证方法
            content, cited_papers = await self._validate_and_fix_review(
                review=review,
                papers=preselected_papers,
                generator=generator,
                task_id=task_id
            )

            # 6. 计算统计信息
            stats = self.filter_service.get_statistics(cited_papers)

            cited_paper_ids = {p.get('id') for p in cited_papers}
            for query_result in search_queries_results:
                cited_count = sum(1 for p in query_result['papers'] if p.get('id') in cited_paper_ids)
                query_result['citedCount'] = cited_count
                for paper in query_result['papers']:
                    paper['cited'] = paper.get('id') in cited_paper_ids
                    if 'relevance_score' not in paper:
                        paper['relevance_score'] = 0

            for paper in filtered_papers:
                if 'relevance_score' not in paper:
                    paper['relevance_score'] = 0
                paper['cited'] = paper.get('id') in cited_paper_ids

            # 7. 最终验证
            final_validation = validator.validate_review(review=review, papers=cited_papers)

            # 8. 保存记录
            record = self.record_service.update_success(
                db_session=db_session,
                record=record,
                review=review,
                papers=cited_papers,
                statistics=stats
            )

            # 任务完成
            task_manager.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                result={
                    "id": record.id,
                    "topic": topic,
                    "review": review,
                    "papers": cited_papers,
                    "candidate_pool": filtered_papers,
                    "statistics": stats,
                    "analysis": framework,
                    "search_queries_results": search_queries_results,
                    "cited_papers_count": len(cited_papers),
                    "validation": final_validation,
                    "created_at": record.created_at.isoformat()
                }
            )

        except Exception as e:
            import traceback
            traceback.print_exc()

            # 确保槽位被释放（如果还没被释放）
            if task_id in task_manager._running_tasks:
                task_manager.release_slot(task_id)

            task_manager.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=str(e)
            )

            # 更新数据库记录为失败
            try:
                if 'record' in locals():
                    self.record_service.update_failure(
                        db_session=db_session,
                        record=record,
                        error_message=str(e)
                    )
            except:
                pass

    # ==================== 新增：阶段3增强文献搜索方法 ====================

    async def _search_literature_with_requirements(
        self,
        topic: str,
        search_queries: list,
        params: dict,
        framework: dict,
        task_id: str
    ) -> tuple:
        """
        增强的文献搜索方法，确保满足数量和质量要求

        要求：
        1. 文献不重复
        2. 总数>target_total（默认100，可配置）
        3. 中文文献>target_chinese（默认60，可配置）
        4. 英文文献>target_english（默认30，可配置）
        5. AMiner论文补充详情
        6. 保存到数据库
        7. 不达标时扩大范围搜索

        Args:
            topic: 论文主题
            search_queries: 搜索查询列表
            params: 参数配置
            framework: 框架信息
            task_id: 任务ID

        Returns:
            (文献列表, 搜索结果统计)
        """
        # 获取配置的目标数量
        target_total = params.get('target_total', 100)
        target_chinese = params.get('target_chinese', 60)
        target_english = params.get('target_english', 30)

        print(f"[TaskExecutor] 文献搜索目标: 总数>{target_total}, 中文>{target_chinese}, 英文>{target_english}")

        all_papers = []
        search_queries_results = []
        seen_ids = set()

        # 第1轮：使用原始搜索查询
        print(f"[TaskExecutor] 第1轮搜索: 使用{len(search_queries)}个搜索查询")
        for i, query_info in enumerate(search_queries[:params.get('max_search_queries', 8)]):
            query = query_info.get('query', topic)
            section = query_info.get('section', '通用')
            lang = query_info.get('lang', None)
            keywords = query_info.get('keywords', None)
            search_mode = query_info.get('search_mode', None)

            task_manager.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress={"step": "searching", "message": f"正在搜索文献 ({i+1}/{len(search_queries)})..."}
            )

            papers = await self.search_service.search(
                query=query,
                years_ago=params.get('search_years', 10),
                limit=50,
                lang=lang,
                keywords=keywords,
                search_mode=search_mode
            )

            # 去重
            new_papers = []
            for paper in papers:
                paper_id = paper.get("id")
                if paper_id not in seen_ids:
                    seen_ids.add(paper_id)
                    new_papers.append(paper)

            search_queries_results.append({
                'query': query,
                'section': section,
                'papers': new_papers,
                'citedCount': 0
            })
            all_papers.extend(new_papers)

        # 检查是否满足要求
        stats = self._calculate_paper_stats(all_papers)
        print(f"[TaskExecutor] 第1轮搜索结果: 总数={stats['total']}, 中文={stats['chinese']}, 英文={stats['english']}")

        # 第2轮：如果不满足要求，扩大范围搜索
        if (stats['total'] < target_total or
            stats['chinese'] < target_chinese or
            stats['english'] < target_english):

            print(f"[TaskExecutor] 第1轮未达标，开始第2轮扩大范围搜索")

            # 扩大搜索策略：
            # 1. 使用更宽泛的查询
            # 2. 增加年份范围
            # 3. 使用所有数据源

            # 从框架中提取核心关键词
            section_keywords = framework.get('section_keywords', {})

            # 为每个章节进行扩展搜索
            for section_title, keywords in section_keywords.items():
                if section_title in ['引言', '结论']:
                    continue  # 跳过引言和结论

                # 取前3个关键词进行搜索
                for keyword in keywords[:3]:
                    task_manager.update_task_status(
                        task_id,
                        TaskStatus.PROCESSING,
                        progress={"step": "searching", "message": f"正在扩大搜索: {keyword}..."}
                    )

                    # 扩大年份范围
                    papers = await self.search_service.search(
                        query=keyword,
                        years_ago=params.get('search_years', 10) + 5,  # 增加5年
                        limit=30,
                        use_all_sources=True
                    )

                    # 去重
                    new_papers = []
                    for paper in papers:
                        paper_id = paper.get("id")
                        if paper_id not in seen_ids:
                            seen_ids.add(paper_id)
                            new_papers.append(paper)

                    all_papers.extend(new_papers)

                    # 检查是否已满足要求
                    stats = self._calculate_paper_stats(all_papers)
                    if (stats['total'] >= target_total and
                        stats['chinese'] >= target_chinese and
                        stats['english'] >= target_english):
                        print(f"[TaskExecutor] 第2轮搜索已达标，停止搜索")
                        break

                # 再次检查
                stats = self._calculate_paper_stats(all_papers)
                if (stats['total'] >= target_total and
                    stats['chinese'] >= target_chinese and
                    stats['english'] >= target_english):
                    break

        # 第3轮：如果仍然不满足，使用主题进行宽泛搜索
        stats = self._calculate_paper_stats(all_papers)
        if (stats['total'] < target_total or
            stats['chinese'] < target_chinese or
            stats['english'] < target_english):

            print(f"[TaskExecutor] 第2轮未达标，开始第3轮宽泛搜索")

            task_manager.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                progress={"step": "searching", "message": "正在进行宽泛搜索..."}
            )

            # 提取主题关键词
            topic_keywords = self._extract_topic_keywords_from_framework(framework)

            for keyword in topic_keywords[:5]:
                papers = await self.search_service.search(
                    query=keyword,
                    years_ago=20,  # 扩大到20年
                    limit=50,
                    use_all_sources=True
                )

                # 去重
                new_papers = []
                for paper in papers:
                    paper_id = paper.get("id")
                    if paper_id not in seen_ids:
                        seen_ids.add(paper_id)
                        new_papers.append(paper)

                all_papers.extend(new_papers)

                stats = self._calculate_paper_stats(all_papers)
                if stats['total'] >= target_total:
                    break

        # 最终统计
        stats = self._calculate_paper_stats(all_papers)
        print(f"[TaskExecutor] 搜索完成: 总数={stats['total']}, 中文={stats['chinese']}, 英文={stats['english']}")

        # 检查是否满足最低要求
        if stats['total'] < 50:
            print(f"[TaskExecutor] 警告: 搜索文献总数不足50篇，当前{stats['total']}篇")

        # AMiner论文详情补充
        all_papers = await self._enrich_aminer_papers(all_papers)

        # 保存到数据库（由SmartPaperSearchService自动处理）

        return all_papers, search_queries_results

    def _calculate_paper_stats(self, papers: list) -> dict:
        """计算文献统计信息"""
        chinese_count = sum(1 for p in papers if not p.get('is_english', True))
        english_count = sum(1 for p in papers if p.get('is_english', False))

        return {
            'total': len(papers),
            'chinese': chinese_count,
            'english': english_count
        }

    def _extract_topic_keywords_from_framework(self, framework: dict) -> list:
        """从框架中提取主题关键词"""
        keywords = []

        # 从关键元素中提取
        key_elements = framework.get('key_elements', {})
        for key, value in key_elements.items():
            if value and isinstance(value, str):
                keywords.append(value)

        # 从搜索查询中提取
        search_queries = framework.get('search_queries', [])
        for query_info in search_queries:
            query = query_info.get('query', '')
            if query:
                keywords.append(query)

        # 去重
        return list(set(k for k in keywords if k))

    async def _enrich_aminer_papers(self, papers: list) -> list:
        """补充AMiner论文详情"""
        aminer_token = os.getenv("AMINER_API_TOKEN")
        if not aminer_token:
            return papers

        try:
            from services.aminer_paper_detail import enrich_papers
            enriched = await enrich_papers(papers, aminer_token)
            print(f"[TaskExecutor] AMiner详情补充完成: {len(papers)}篇")
            return enriched
        except Exception as e:
            print(f"[TaskExecutor] AMiner详情补充失败: {e}")
            return papers

    def _calculate_relevance_score(self, paper: dict, topic_keywords: list) -> float:
        """
        计算论文的相关性评分

        Args:
            paper: 论文信息
            topic_keywords: 主题关键词列表

        Returns:
            相关性评分（0-100）
        """
        score = 0.0

        # 基础分：被引量（0-30分）
        citations = paper.get("cited_by_count", 0)
        score += min(citations / 10, 30)

        # 关键词匹配度（0-50分）
        if topic_keywords:
            title_lower = paper.get("title", "").lower()
            abstract_lower = paper.get("abstract", "").lower()

            for kw in topic_keywords:
                if not kw:
                    continue
                kw_lower = kw.lower()
                if kw_lower in title_lower:
                    score += 15  # 标题匹配权重更高
                elif kw_lower in abstract_lower:
                    score += 5   # 摘要匹配权重较低

        # 新近论文加分（0-20分）
        from datetime import datetime
        current_year = datetime.now().year
        paper_year = paper.get("year")
        if paper_year:
            if paper_year >= current_year - 5:
                score += 20
            elif paper_year >= current_year - 10:
                score += 10

        return min(score, 100)

    async def _llm_adjust_search_strategy(
        self,
        topic: str,
        framework: dict,
        current_count: int,
        target_count: int
    ) -> list:
        """
        使用LLM调整搜索策略并生成新的搜索关键词

        Args:
            topic: 论文主题
            framework: 框架信息
            current_count: 当前文献数量
            target_count: 目标文献数量

        Returns:
            新的搜索关键词列表
        """
        from openai import AsyncOpenAI

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return []

        client = AsyncOpenAI(api_key=api_key, base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))

        # 获取当前章节信息
        sections = framework.get('framework', {}).get('sections', [])

        system_prompt = """你是学术文献搜索专家。当前文献搜索结果未达到预期数量，需要你调整搜索策略。

请分析以下信息，生成5-10个新的搜索关键词：

**分析要点**：
1. 识别当前搜索策略的不足
2. 找出可能被忽视的相关领域或术语
3. 生成更宽泛但相关的搜索关键词
4. 包含中英文术语
5. 考虑同义词、相关术语、缩写等

**输出格式**：
请直接输出搜索关键词列表，每行一个关键词。"""

        user_prompt = f"""**论文主题**：{topic}

**当前章节结构**：
{chr(10).join([f"- {s.get('title', '')}: {s.get('description', '')}" for s in sections[:3]])}

**当前状态**：
- 已搜索文献数量：{current_count}
- 目标文献数量：{target_count}
- 差距：{target_count - current_count}

**请生成5-10个新的搜索关键词**："""

        try:
            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            content = response.choices[0].message.content

            # 提取关键词
            keywords = []
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # 移除可能的序号和符号
                    keyword = line.lstrip('0123456789.-* ').strip()
                    if keyword:
                        keywords.append(keyword)

            print(f"[TaskExecutor] LLM生成的搜索关键词: {keywords[:5]}")
            return keywords

        except Exception as e:
            print(f"[TaskExecutor] LLM调整搜索策略失败: {e}")
            return []

    async def _validate_and_fix_review(
        self,
        review: str,
        papers: list,
        generator: 'ReviewGeneratorService',
        task_id: str
    ) -> tuple:
        """
        增强的综述验证和修复方法

        检查项：
        1. 正文引用是否严格在参考文献范围内
        2. 引用是否一一对应
        3. 文献格式是否为国标格式

        Args:
            review: 综述草稿
            papers: 文献列表
            generator: 综述生成器实例
            task_id: 任务ID

        Returns:
            (修复后的内容, 引用的文献列表)
        """
        from services.reference_validator import ReferenceValidator
        from services.citation_order_checker import CitationOrderChecker

        validator = ReferenceValidator()
        citation_checker = CitationOrderChecker()

        # 分离内容和参考文献
        content, references_section = validator._split_review_and_references(review)

        print(f"[验证] 开始验证和修复综述...")

        # === 检查1：正文引用是否严格在参考文献范围内 ===
        print(f"[验证] 检查1: 引用范围验证...")
        citation_check_result = citation_checker.check_order(content, papers_count=len(papers))

        if citation_check_result.get('exceeds_range', False):
            max_citation = citation_check_result.get('max_citation', 0)
            papers_count = citation_check_result.get('papers_count', 0)
            print(f"[验证] ✗ 检测到超出范围的引用（最大: {max_citation}，文献数: {papers_count}），正在修复...")
            content = citation_checker.remove_out_of_range_citations(content, len(papers))
        else:
            print(f"[验证] ✓ 引用范围检查通过")

        # === 检查2：引用是否一一对应并连续 ===
        print(f"[验证] 检查2: 引用顺序验证...")
        citations = citation_checker.extract_citations(content)

        if citations:
            # 提取引用编号
            cited_indices = [int(c) for c in citations]

            # 检查是否有重复或跳跃
            unique_sorted = sorted(set(cited_indices))
            if unique_sorted != list(range(1, len(unique_sorted) + 1)):
                print(f"[验证] ✗ 引用编号不连续，需要重新排序...")
                fixed_content, number_mapping = citation_checker.fix_citation_order(content, citations)

                # 根据新的引用顺序重新构建文献列表
                new_to_old = {}
                for item in number_mapping:
                    new_to_old[item['new']] = item['old']

                cited_papers = []
                for new_index in sorted(new_to_old.keys()):
                    old_index = new_to_old[new_index]
                    # 确保旧索引在有效范围内
                    if 1 <= old_index <= len(papers):
                        cited_papers.append(papers[old_index - 1])

                content = fixed_content
                print(f"[验证] ✓ 引用顺序已修复，共引用{len(cited_papers)}篇文献")
            else:
                # 只保留在有效范围内的引用编号
                valid_cited_indices = {i for i in cited_indices if 1 <= i <= len(papers)}
                cited_papers = [papers[i - 1] for i in sorted(valid_cited_indices)]
                print(f"[验证] ✓ 引用顺序检查通过，共引用{len(cited_papers)}篇文献")
        else:
            print(f"[验证] ⚠ 未检测到任何引用")
            cited_papers = []

        # === 检查3：每篇文献引用次数限制 ===
        print(f"[验证] 检查3: 引用次数验证...")
        content = self._limit_citation_count(content, max_count=2)
        print(f"[验证] ✓ 引用次数限制已应用")

        # === 检查4：文献格式验证（国标格式）===
        print(f"[验证] 检查4: 文献格式验证...")
        # _format_references 已使用国标格式，这里只需确保格式正确
        references = generator._format_references(cited_papers)

        # 验证格式
        format_errors = self._validate_reference_format(references)
        if format_errors:
            print(f"[验证] ✗ 发现{len(format_errors)}个格式错误，正在修复...")
            # 重新生成参考文献
            references = generator._format_references(cited_papers)
        else:
            print(f"[验证] ✓ 文献格式检查通过")

        # === 最终检查：确保没有超出范围的引用 ===
        print(f"[验证] 最终检查...")
        final_check = citation_checker.check_order(content, papers_count=len(cited_papers))
        if final_check.get('exceeds_range', False):
            print(f"[验证] ✗ 最终检查发现超出范围的引用，正在修复...")
            content = citation_checker.remove_out_of_range_citations(content, len(cited_papers))

        # 组合最终综述
        final_review = f"{content}\n\n## 参考文献\n\n{references}"

        print(f"[验证] ✓ 验证和修复完成")

        return final_review, cited_papers

    def _limit_citation_count(self, content: str, max_count: int = 2) -> str:
        """
        限制每篇文献的引用次数

        Args:
            content: 综述内容
            max_count: 最大引用次数

        Returns:
            修复后的内容
        """
        import re
        citation_pattern = re.compile(r'\[(\d+)\]')
        citations = []

        for match in citation_pattern.finditer(content):
            num = int(match.group(1))
            citations.append((match.start(), match.end(), num))

        citation_count = {}
        for _, _, num in citations:
            citation_count[num] = citation_count.get(num, 0) + 1

        to_remove = []
        for num, count in citation_count.items():
            if count > max_count:
                occurrences = [(start, end) for start, end, n in citations if n == num]
                for start, end in occurrences[max_count:]:
                    to_remove.append((start, end))

        if not to_remove:
            return content

        result = list(content)
        for start, end in sorted(to_remove, reverse=True):
            del result[start:end]

        return ''.join(result)

    def _validate_reference_format(self, references: str) -> list:
        """
        验证参考文献格式是否符合国标格式

        Args:
            references: 参考文献字符串

        Returns:
            格式错误列表
        """
        errors = []

        # 基本格式检查
        lines = references.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # 检查是否以 [数字] 开头
            if not line.startswith('['):
                errors.append(f"第{i}行: 未以引用编号开头")
                continue

            # 检查是否包含必要元素
            if '[J]' not in line and '[M]' not in line and '[C]' not in line:
                errors.append(f"第{i}行: 缺少文献类型标识")

        return errors

    def _preselect_papers_with_requirements(
        self,
        papers: list,
        target_count: int = 60,
        min_english: int = 30,
        min_recent_ratio: float = 0.5
    ) -> list:
        """
        智能预选文献，满足特定要求

        要求：
        1. 总数 = target_count
        2. 英文文献 >= min_english
        3. 近5年文献 >= target_count * min_recent_ratio

        Args:
            papers: 筛选后的文献池
            target_count: 目标数量（默认60）
            min_english: 最少英文文献数（默认30）
            min_recent_ratio: 近5年文献最少比例（默认0.5）

        Returns:
            预选后的文献列表
        """
        if len(papers) <= target_count:
            print(f"[预选] 文献池数量不足({len(papers)})，返回全部文献")
            return papers

        from datetime import datetime
        current_year = datetime.now().year
        recent_threshold = current_year - 5
        min_recent_count = int(target_count * min_recent_ratio)

        # 分类文献
        english_papers = []
        chinese_papers = []
        recent_papers = []
        old_papers = []

        for paper in papers:
            is_english = paper.get('is_english', False)
            year = paper.get('year')
            is_recent = year is not None and year >= recent_threshold

            if is_english:
                english_papers.append(paper)
            else:
                chinese_papers.append(paper)

            if is_recent:
                recent_papers.append(paper)
            else:
                old_papers.append(paper)

        print(f"[预选] 文献池分类: 英文={len(english_papers)}, 中文={len(chinese_papers)}, "
              f"近5年={len(recent_papers)}, 5年前={len(old_papers)}")

        # 按相关性评分排序各类文献
        english_papers.sort(key=lambda p: p.get('relevance_score', 0), reverse=True)
        chinese_papers.sort(key=lambda p: p.get('relevance_score', 0), reverse=True)
        recent_papers.sort(key=lambda p: p.get('relevance_score', 0), reverse=True)
        old_papers.sort(key=lambda p: p.get('relevance_score', 0), reverse=True)

        selected = set()
        result = []

        # === 策略1：优先满足英文文献要求 ===
        english_needed = min(min_english, len(english_papers))
        for paper in english_papers[:english_needed]:
            paper_id = paper.get('id')
            if paper_id not in selected:
                selected.add(paper_id)
                result.append(paper)

        print(f"[预选] 已选择英文文献: {len([p for p in result if p.get('is_english')])}/{min_english}")

        # === 策略2：优先满足近5年文献要求 ===
        recent_needed = min_recent_count
        for paper in recent_papers:
            if len(result) >= target_count:
                break
            paper_id = paper.get('id')
            if paper_id not in selected:
                selected.add(paper_id)
                result.append(paper)

        current_recent_count = sum(1 for p in result if p.get('year', 0) >= recent_threshold)
        print(f"[预选] 已选择近5年文献: {current_recent_count}/{min_recent_count}")

        # === 策略3：补充剩余文献到目标数量 ===
        if len(result) < target_count:
            # 从所有文献中按相关性排序补充
            all_remaining = []
            for paper in papers:
                paper_id = paper.get('id')
                if paper_id not in selected:
                    all_remaining.append(paper)

            all_remaining.sort(key=lambda p: p.get('relevance_score', 0), reverse=True)

            for paper in all_remaining:
                if len(result) >= target_count:
                    break
                paper_id = paper.get('id')
                if paper_id not in selected:
                    selected.add(paper_id)
                    result.append(paper)

        # === 最终验证和调整 ===
        final_stats = self.filter_service.get_statistics(result)
        print(f"[预选] 最终结果: 总数={len(result)}, 英文={final_stats['english_count']}, "
              f"近5年={final_stats['recent_count']} ({final_stats['recent_ratio']:.2%})")

        # 如果英文文献仍然不足，放宽要求
        if final_stats['english_count'] < min_english:
            print(f"[预选] 警告: 英文文献不足({final_stats['english_count']} < {min_english})")

        # 如果近5年文献仍然不足，放宽要求
        if final_stats['recent_count'] < min_recent_count:
            print(f"[预选] 警告: 近5年文献不足({final_stats['recent_count']} < {min_recent_count})")

        return result


