"""
Semantic Scholar 文献检索服务
免费API，对中文文献有一定支持
"""
import httpx
from typing import List, Dict
from datetime import datetime, timedelta


class SemanticScholarService:
    """Semantic Scholar API 客户端"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        # Semantic Scholar API key is optional but increases rate limits
        self.api_key = None
        # 速率限制：免费API每分钟5次请求
        self.request_delay = 12  # 秒，保守起见设置12秒间隔
        self.last_request_time = None

    async def search_papers(
        self,
        query: str,
        years_ago: int = 5,
        limit: int = 100,
        min_citations: int = 0
    ) -> List[Dict]:
        """
        搜索论文

        Args:
            query: 搜索关键词
            years_ago: 近N年
            limit: 返回数量
            min_citations: 最小被引量

        Returns:
            论文列表
        """
        # 速率限制：等待足够时间再发送请求
        import asyncio
        if self.last_request_time:
            elapsed = datetime.now().timestamp() - self.last_request_time
            if elapsed < self.request_delay:
                wait_time = self.request_delay - elapsed
                await asyncio.sleep(wait_time)

        # 计算截止年份
        current_year = datetime.now().year
        start_year = current_year - years_ago

        # Semantic Scholar 使用年份范围过滤
        year_range = f"{start_year}-{current_year}"

        params = {
            "query": query,
            "fields": "paperId,title,authors,year,citationCount,externalIds,publicationDate,journal,abstract",
            "limit": min(limit, 100),  # Semantic Scholar 默认最大100
            "year": year_range
        }

        # 如果有 API key，添加到请求头
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        try:
            self.last_request_time = datetime.now().timestamp()
            response = await self.client.get(
                f"{self.BASE_URL}/paper/search",
                params=params,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            papers = []
            for item in data.get("data", []):
                # 过滤被引量
                citation_count = item.get("citationCount", 0)
                if citation_count < min_citations:
                    continue

                # 提取作者信息
                authors = []
                for author in item.get("authors", [])[:10]:  # 最多10个作者
                    name = author.get("name", "")
                    if name:
                        authors.append(name)

                # 判断语言（简单判断：标题含非ASCII字符可能是中文）
                title = item.get("title", "")
                is_english = self._is_english(title)

                # 获取 DOI
                doi = None
                external_ids = item.get("externalIds", {})
                if external_ids and "DOI" in external_ids:
                    doi = external_ids["DOI"]

                # 获取期刊信息
                journal = item.get("journal", {})
                journal_name = journal.get("name", "") if journal else ""

                papers.append({
                    "id": item.get("paperId", ""),
                    "title": title,
                    "authors": authors,
                    "year": item.get("year"),
                    "cited_by_count": citation_count,
                    "is_english": is_english,
                    "abstract": item.get("abstract", ""),
                    "type": "article",
                    "doi": doi,
                    "primary_location": {
                        "source": {
                            "display_name": journal_name
                        } if journal_name else {}
                    },
                    "concepts": [],  # Semantic Scholar 没有直接的 concepts 字段
                    "source": "semantic_scholar"  # 标记数据来源
                })

            return papers

        except httpx.HTTPError as e:
            print(f"Semantic Scholar API error: {e}")
            return []

    def _is_english(self, text: str) -> bool:
        """简单判断文本是否为英文"""
        if not text:
            return False
        # 计算非ASCII字符比例
        non_ascii = sum(1 for c in text if ord(c) > 127)
        return non_ascii / len(text) < 0.3

    async def close(self):
        await self.client.aclose()
