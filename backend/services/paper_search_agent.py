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
        max_iterations = 15
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

            if assistant_message.tool_calls:
                messages.append(assistant_message)
                tool_responses = []

                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    result = await self._handle_tool_call(
                        function_name, function_args
                    )

                    tool_responses.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })

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

        # 按引用量排序
        all_papers.sort(key=lambda p: p.get("cited_by_count", 0), reverse=True)

        logger.debug(f"[PaperSearchAgent] 最终: {len(all_papers)} 篇去重论文")
        return all_papers

    # ==================== Prompt 构建 ====================

    def _build_system_prompt(self, search_years: int, target_count: int) -> str:
        return f"""你是一位学术文献检索专家。你的任务是根据用户给定的研究主题，制定检索策略，通过工具调用 Semantic Scholar API 检索相关文献。

## 你的目标
收集 {target_count} 篇左右的高质量、高相关性学术文献。

## 检索策略（必须遵循）

### 第一步：分析主题
分析用户的研究主题，识别出：
1. 该领域的 3-5 个核心子主题/关键技术方向
2. 该领域的核心模型、方法、数据集名称（如 CLIP、DALL-E、Transformer、ImageNet）
3. 该领域的代表性研究团队/作者

### 第二步：生成检索词
为每个子主题生成 **英文** 检索词（Semantic Scholar 英文效果远好于中文）。

检索词要求：
- 精准：使用该领域的标准术语，不要用泛化词
- 具体：优先使用具体模型名/方法名（如 "vision-language model" 而非 "multimodal learning"）
- 组合：使用 AND/OR 组合关键词，缩小范围

检索词示例：
- 好的: "vision-language model AND contrastive learning", "multimodal large language model", "image captioning transformer"
- 差的: "multimodal data processing", "machine learning model", "AI application"

### 第三步：锚定核心论文
识别该领域最核心、最具代表性的 3-5 篇论文（奠基性工作、里程碑论文），
使用 `search_by_exact_title` 精确搜索这些论文，确保不遗漏。

例如主题"多模态大模型"，核心论文包括：
- "Learning Transferable Visual Models From Natural Language Supervision" (CLIP)
- "Visual ChatGPT: Talking, Drawing and Editing with Large Foundation Models"
- "LLaVA: Visual Instruction Tuning"

### 第四步：评估与补充
每次检索后，评估结果：
- 如果某子主题的文献不足，换一组检索词补充
- 如果发现新的关键词/方向，追加检索
- 合理控制总调用次数

## 工具说明

你有两个工具可用：

1. **search_papers(query, limit, sort)**: 关键词搜索
   - query: 英文检索词，支持 AND/OR/NOT 布尔运算
   - limit: 返回数量（建议 20-50）
   - sort: "citationCount:desc" 按引用排序，"publicationDate:desc" 按时间排序
   - 返回: 论文列表（标题、年份、引用量、论文ID）

2. **search_by_exact_title(title)**: 精确标题搜索
   - title: 论文的完整英文标题
   - 用于锚定已知的核心论文
   - 返回: 单篇论文详情或空

## 时间范围
搜索近 {search_years} 年的文献。

## 输出要求
检索完成后，请简要总结：
- 按子主题分类的检索结果统计
- 检索策略是否有效
- 是否有重要方向被遗漏"""

    def _build_user_message(self, topic: str, target_count: int) -> str:
        return f"""请为以下研究主题检索相关学术文献：

**研究主题**: {topic}

**目标数量**: 约 {target_count} 篇高质量相关文献

请开始制定检索策略并执行检索。"""

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
