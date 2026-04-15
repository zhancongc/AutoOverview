"""
LLM Function Calling 驱动的文献检索 Agent

让 LLM 自行决定检索策略、生成检索词、评估结果质量，
通过 Function Calling 调用本地 SemanticScholarService 包装方法，
本地方法控制全局速率限制。
"""

import os
import json
import asyncio
from typing import List, Dict, Optional, Set
from openai import AsyncOpenAI
from .semantic_scholar_search import SemanticScholarService

import logging
logger = logging.getLogger(__name__)


class PaperSearchAgent:
    """LLM 驱动的文献检索 Agent"""

    def __init__(self, ss_service: SemanticScholarService):
        self.ss_service = ss_service
        self.search_years = 10  # 默认值，由 search() 方法覆盖
        self.llm_client = AsyncOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        )
        self.model = "deepseek-chat"
        # 收集到的论文（去重）
        self.collected_papers: Dict[str, Dict] = {}  # paperId -> paper
        # 搜索统计
        self.search_count = 0

    async def search(
        self,
        topic: str,
        search_years: int = 10,
        target_count: int = 50
    ) -> List[Dict]:
        """
        主入口：LLM 驱动检索，返回去重后的论文列表。

        Args:
            topic: 用户的研究主题（中文或英文）
            search_years: 搜索近 N 年的文献
            target_count: 目标收集论文数量

        Returns:
            去重后的论文列表
        """
        logger.debug(f"\n[PaperSearchAgent] 开始检索: {topic}")
        logger.debug(f"  目标: {target_count} 篇, 年限: {search_years} 年")

        self.search_years = search_years

        system_prompt = self._build_system_prompt(search_years, target_count)
        user_message = self._build_user_message(topic, target_count)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        tools = self._get_tools_definition(search_years)
        max_iterations = 4  # 限制迭代次数，防止超时
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=4096
            )

            assistant_message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason
            logger.debug(f"  [迭代 {iteration}] finish_reason={finish_reason}, tool_calls={len(assistant_message.tool_calls or [])}, collected={len(self.collected_papers)}")

            if assistant_message.tool_calls:
                messages.append(assistant_message)

                # 并发执行所有工具调用（大幅减少等待时间）
                async def _exec_tool(tool_call):
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    result = await self._handle_tool_call(function_name, function_args)
                    return {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    }

                tool_responses = await asyncio.gather(*[
                    _exec_tool(tc) for tc in assistant_message.tool_calls
                ])

                messages.extend(tool_responses)
                logger.debug(f"  [迭代 {iteration}] 已收集 {len(self.collected_papers)} 篇去重论文, 共调用 {self.search_count} 次搜索")

                # 如果已经收集足够多的论文，在下一轮提示 LLM 结束
                if len(self.collected_papers) >= target_count * 1.5:
                    messages.append({
                        "role": "user",
                        "content": f"已收集 {len(self.collected_papers)} 篇论文，超过目标 {target_count} 篇。请总结检索结果并结束。"
                    })
            else:
                # LLM 没有调用工具，认为检索完成
                logger.debug(f"[PaperSearchAgent] 检索完成: {len(self.collected_papers)} 篇论文, {self.search_count} 次搜索调用, {iteration} 轮对话")
                break

        # 转换为列表
        all_papers = list(self.collected_papers.values())

        # 兜底：如果 LLM 没找到任何论文，用主题直接做一次关键词搜索
        if len(all_papers) == 0:
            logger.warning(f"[PaperSearchAgent] 搜索结果为空（{self.search_count} 次搜索），执行兜底搜索")
            try:
                # 用中文主题直接搜
                fallback_papers = await self.ss_service.search_papers(
                    query=topic,
                    years_ago=search_years,
                    limit=target_count,
                    sort="citationCount:desc"
                )
                for paper in fallback_papers:
                    paper_id = paper.get("id") or paper.get("paperId")
                    if paper_id and paper_id not in self.collected_papers:
                        self.collected_papers[paper_id] = paper
                all_papers = list(self.collected_papers.values())
                logger.info(f"[PaperSearchAgent] 中文兜底搜索找到 {len(all_papers)} 篇论文")

                # 如果中文也没结果，用翻译后的英文关键词再搜
                if len(all_papers) == 0:
                    # 尝试用 DeepSeek 翻译并提取英文关键词
                    translate_response = await self.llm_client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "你是一个学术翻译助手。将用户给定的中文学术主题翻译为英文，提取3-5个最适合在Semantic Scholar搜索的英文关键词组合（用AND连接）。只返回搜索查询，不要其他内容。"},
                            {"role": "user", "content": f"翻译以下学术主题为英文搜索词：{topic}"}
                        ],
                        temperature=0.1,
                        max_tokens=200
                    )
                    en_query = translate_response.choices[0].message.content.strip()
                    logger.info(f"[PaperSearchAgent] 英文兜底搜索词: {en_query}")

                    en_papers = await self.ss_service.search_papers(
                        query=en_query,
                        years_ago=search_years,
                        limit=target_count,
                        sort="citationCount:desc"
                    )
                    for paper in en_papers:
                        paper_id = paper.get("id") or paper.get("paperId")
                        if paper_id and paper_id not in self.collected_papers:
                            self.collected_papers[paper_id] = paper
                    all_papers = list(self.collected_papers.values())
                    logger.info(f"[PaperSearchAgent] 英文兜底搜索找到 {len(all_papers)} 篇论文")
            except Exception as e:
                logger.error(f"[PaperSearchAgent] 兜底搜索失败: {e}")

        # 按引用量排序
        all_papers.sort(key=lambda p: p.get("cited_by_count", 0), reverse=True)

        logger.debug(f"[PaperSearchAgent] 最终: {len(all_papers)} 篇去重论文")
        return all_papers

    # ==================== Prompt 构建 ====================

    def _build_system_prompt(self, search_years: int, target_count: int) -> str:
        return f"""你是一位学术文献检索专家。你的任务是根据用户给定的研究主题，通过工具调用 Semantic Scholar API 检索相关文献。

## 关键约束：必须一次性批量调用所有工具
- **你只有 2 轮工具调用机会**，必须在第一轮就把所有搜索全部发出
- **禁止逐个调用工具**。你必须在一次回复中同时调用所有需要的工具（5-10 个）
- 第一轮：同时发起所有精确标题搜索 + 关键词搜索
- 第二轮（如需要）：根据第一轮结果补充搜索

## 检索策略

### 1. 锚定核心论文（精确标题搜索）
识别该领域最核心的 3-5 篇论文，使用 `search_by_exact_title` 搜索。

### 2. 关键词搜索（覆盖各子方向）
为每个子方向生成 **英文** 检索词，使用 `search_papers` 搜索。
检索词要求：
- 精准：使用该领域的标准术语
- 具体：优先使用具体方法名（如 "micro-expression recognition" 而非 "facial expression"）
- 组合：使用 AND/OR 缩小范围

好的检索词: "micro-expression recognition AND deep learning", "micro-expression spotting AND video sequence"
差的检索词: "facial expression analysis", "machine learning"

## 工具说明

1. **search_papers(query, limit, sort)**: 关键词搜索
   - query: 英文检索词，支持 AND/OR/NOT 布尔运算
   - limit: 返回数量（建议 20-50）
   - sort: "citationCount:desc" 按引用排序，"publicationDate:desc" 按时间排序

2. **search_by_exact_title(title)**: 精确标题搜索
   - title: 论文的完整英文标题（用于锚定已知的核心论文，不限年份）

## 时间范围
关键词搜索近 {search_years} 年的文献。精确标题搜索不受年份限制。

## 输出要求
检索完成后，简要总结检索结果。"""

    def _build_user_message(self, topic: str, target_count: int) -> str:
        return f"""请为以下研究主题检索相关学术文献：

**研究主题**: {topic}

**目标数量**: 约 {target_count} 篇高质量相关文献

请一次性批量调用所有工具完成检索。"""

    # ==================== Tools 定义 ====================

    def _get_tools_definition(self, search_years: int) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_papers",
                    "description": "在 Semantic Scholar 中按关键词搜索论文。支持布尔查询（AND/OR/NOT）。返回标题、年份、引用量等基本信息。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "英文检索词，支持 AND/OR/NOT。例如: 'vision-language model AND contrastive learning'"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回数量，默认30，最大100",
                                "default": 30
                            },
                            "sort": {
                                "type": "string",
                                "description": "排序方式: 'citationCount:desc' 按引用排序, 'publicationDate:desc' 按时间排序",
                                "default": "citationCount:desc"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_by_exact_title",
                    "description": "根据论文完整标题精确搜索，用于锚定已知的核心/经典论文。返回该论文的详细信息。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "论文的完整英文标题"
                            }
                        },
                        "required": ["title"]
                    }
                }
            }
        ]

    # ==================== Tool 执行 ====================

    async def _handle_tool_call(
        self, function_name: str, function_args: Dict
    ) -> Dict:
        """处理 LLM 的 tool call，返回结果"""

        if function_name == "search_papers":
            return await self._tool_search_papers(function_args)
        elif function_name == "search_by_exact_title":
            return await self._tool_search_by_exact_title(function_args)
        else:
            return {"error": f"未知工具: {function_name}"}

    async def _tool_search_papers(self, args: Dict) -> Dict:
        """执行 search_papers 工具调用"""
        query = args.get("query", "")
        limit = min(args.get("limit", 30), 100)
        sort = args.get("sort", "citationCount:desc")

        logger.debug(f"  [搜索] query='%s', limit=%s, sort=%s", query, limit, sort)

        try:
            papers = await self.ss_service.search_papers(
                query=query,
                years_ago=self.search_years,
                limit=limit,
                sort=sort
            )

            self.search_count += 1

            # 去重收集
            new_count = 0
            results_summary = []
            for paper in papers:
                paper_id = paper.get("id") or paper.get("paperId")
                if paper_id and paper_id not in self.collected_papers:
                    self.collected_papers[paper_id] = paper
                    new_count += 1

                results_summary.append({
                    "title": paper.get("title", "")[:80],
                    "year": paper.get("year"),
                    "citations": paper.get("cited_by_count", 0)
                })

            return {
                "total_returned": len(papers),
                "new_papers": new_count,
                "total_collected": len(self.collected_papers),
                "papers_preview": results_summary[:15]
            }

        except Exception as e:
            logger.debug(f"  [搜索错误] %s", e)
            return {"error": str(e), "total_returned": 0, "new_papers": 0}

    async def _tool_search_by_exact_title(self, args: Dict) -> Dict:
        """执行精确标题搜索"""
        title = args.get("title", "")

        logger.debug(f"  [精确搜索] title='%s...'", title[:60])

        try:
            paper = await self.ss_service.search_by_exact_title(title)
            self.search_count += 1

            if paper:
                paper_id = paper.get("id") or paper.get("paperId")
                if paper_id and paper_id not in self.collected_papers:
                    self.collected_papers[paper_id] = paper
                    authors = paper.get("authors", [])
                    # authors 可能是字符串列表
                    author_names = authors[:3] if authors and isinstance(authors[0], str) else [a.get("name", "") for a in authors[:3]]
                    return {
                        "found": True,
                        "title": paper.get("title", ""),
                        "year": paper.get("year"),
                        "citations": paper.get("cited_by_count", 0),
                        "authors": author_names,
                        "total_collected": len(self.collected_papers)
                    }
                else:
                    return {
                        "found": True,
                        "already_collected": True,
                        "title": paper.get("title", ""),
                        "total_collected": len(self.collected_papers)
                    }
            else:
                return {"found": False, "title": title}

        except Exception as e:
            logger.debug("  [精确搜索错误] %s", e)
            return {"error": str(e), "found": False}
