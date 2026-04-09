"""
Semantic Scholar 文献检索服务
免费API，对中文文献有一定支持
全局单例：所有并发任务共享同一个实例和速率限制
"""
import httpx
import asyncio
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class SemanticScholarService:
    """
    Semantic Scholar API 客户端（全局单例）

    所有并发任务共享同一个实例，确保速率限制（1 次/秒）在全局生效。
    通过 get_semantic_scholar_service() 获取实例，不要直接构造。
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    _instance = None
    _initialized = False

    def __new__(cls, api_key: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, api_key: str = None):
        if self._initialized:
            # 单例已初始化，只更新 api_key（如果提供了更好的）
            if api_key and not self.api_key:
                self.api_key = api_key
                self.request_delay = 1.0
            return

        self.client = httpx.AsyncClient(timeout=30.0)
        self.api_key = api_key
        # 速率限制：有API Key时每秒1次，无API Key时每10秒1次
        self.request_delay = 1.0 if api_key else 10.0
        self.last_request_time = None
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 5
        self.backoff_factor = 2
        # 异步锁：确保并发请求排队等待速率限制
        self._lock = asyncio.Lock()

        self._initialized = True

    async def close(self):
        """关闭 HTTP 客户端（仅在进程退出时调用）"""
        # 单例模式下不关闭，保持连接复用
        pass

    async def shutdown(self):
        """真正关闭（仅进程退出时调用）"""
        if self.client:
            await self.client.aclose()

    async def search_papers(
        self,
        query: str,
        years_ago: int = 5,
        limit: int = 100,
        min_citations: int = 0,
        venue: str = None,
        fields: str = None,
        year_start: int = None,
        year_end: int = None,
        sort: str = None,
        open_access_pdf: bool = False
    ) -> List[Dict]:
        """
        搜索论文（支持高级搜索）

        Args:
            query: 搜索关键词（支持布尔查询：AND, OR, NOT）
            years_ago: 近N年（当 year_start/year_end 未设置时使用）
            limit: 返回数量（默认100，最大100）
            min_citations: 最小被引量
            venue: 期刊/会议名称过滤
            fields: 自定义返回字段（逗号分隔）
            year_start: 起始年份（如 2021）
            year_end: 结束年份（如 2024）
            sort: 排序方式（citationCount:desc, citationCount:asc, publicationDate:desc, publicationDate:asc）
            open_access_pdf: 是否只返回有开放获取PDF的论文

        Returns:
            论文列表

        高级查询示例:
            # 按年份范围搜索并按引用量排序
            search_papers("large language model", year_start="2021", year_end="2024", sort="citationCount:desc")

            # 搜索特定期刊
            search_papers("attention mechanism", venue="Nature")

            # 布尔查询
            search_papers("(transformer OR attention) AND (vision OR language)")

            # 只获取开放获取论文
            search_papers("machine learning", open_access_pdf=True)
        """
        # 计算年份范围
        current_year = datetime.now().year
        if year_start is None:
            year_start = current_year - years_ago
        if year_end is None:
            year_end = current_year

        # 默认返回字段
        default_fields = "paperId,title,authors,year,citationCount,externalIds,publicationDate,journal,abstract,venue,publicationVenue"
        if fields:
            default_fields = fields

        # 构建查询参数
        params = {
            "query": query,
            "fields": default_fields,
            "limit": min(limit, 100),  # Semantic Scholar 默认最大100
        }

        # 年份过滤
        if year_start and year_end:
            params["year"] = f"{year_start}-{year_end}"
        elif year_start:
            params["minYear"] = year_start
        elif year_end:
            params["maxYear"] = year_end

        # 期刊/会议过滤
        if venue:
            params["venue"] = venue

        # 排序
        if sort:
            params["sort"] = sort

        # 开放获取过滤
        if open_access_pdf:
            params["openAccessPdf"] = ""

        # 如果有 API key，添加到请求头
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        print(f"[Semantic Scholar] 搜索参数: query=\"{query[:50]}...\", year={year_start}-{year_end}, limit={limit}")
        if sort:
            print(f"[Semantic Scholar] 排序: {sort}")
        if venue:
            print(f"[Semantic Scholar] 期刊: {venue}")

        # 重试机制（带全局速率限制）
        for attempt in range(self.max_retries):
            try:
                # 全局速率限制：通过异步锁确保并发请求排队
                async with self._lock:
                    if self.last_request_time:
                        elapsed = datetime.now().timestamp() - self.last_request_time
                        if elapsed < self.request_delay:
                            wait_time = self.request_delay - elapsed
                            await asyncio.sleep(wait_time)

                    self.last_request_time = datetime.now().timestamp()
                response = await self.client.get(
                    f"{self.BASE_URL}/paper/search",
                    params=params,
                    headers=headers
                )

                # 检查是否是429错误（速率限制）
                if response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        # 计算退避时间
                        backoff_delay = self.retry_delay * (self.backoff_factor ** attempt)
                        print(f"[Semantic Scholar] 遇到429限流，{backoff_delay}秒后重试 (尝试 {attempt + 1}/{self.max_retries})")
                        await asyncio.sleep(backoff_delay)
                        continue
                    else:
                        print(f"[Semantic Scholar] 达到最大重试次数，放弃请求")
                        return []

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

                    # 获取期刊/会议信息（更全面的提取）
                    venue_name = ""

                    # 尝试从 journal 字段获取
                    journal = item.get("journal", {})
                    if journal:
                        venue_name = journal.get("name", "")

                    # 如果没有期刊信息，尝试从 venue 字段获取
                    if not venue_name:
                        venue = item.get("venue", "")
                        if venue:
                            venue_name = venue

                    # 如果仍然没有，尝试从 publicationVenueId 推断
                    if not venue_name:
                        venue_id = item.get("publicationVenueId", "")
                        if venue_id:
                            venue_name = venue_id

                    # 从 DOI 解析出版社信息（作为补充）
                    if not venue_name and doi:
                        if "10.1145/" in doi:
                            venue_name = "ACM"
                        elif "10.1109/" in doi:
                            venue_name = "IEEE"
                        elif "10.48550/arXiv" in doi:
                            venue_name = "arXiv"
                        elif "10.1038/" in doi:
                            venue_name = "Nature"
                        elif "10.1126/" in doi:
                            venue_name = "Science"

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
                        "venue": venue_name,  # 添加 venue 字段
                        "journal": venue_name,  # 添加 journal 字段
                        "venue_name": venue_name,  # 添加 venue_name 字段（用于数据库存储）
                        "primary_location": {
                            "source": {
                                "display_name": venue_name
                            } if venue_name else {}
                        },
                        "concepts": [],  # Semantic Scholar 没有直接的 concepts 字段
                        "source": "semantic_scholar"  # 标记数据来源
                    })

                print(f"[Semantic Scholar] 成功获取 {len(papers)} 篇论文")
                return papers

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # 429错误在上面已经处理
                    continue
                else:
                    print(f"[Semantic Scholar] HTTP错误: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                    else:
                        return []
            except Exception as e:
                print(f"[Semantic Scholar] 请求失败: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    return []

        return []

    def _is_english(self, text: str) -> bool:
        """简单判断文本是否为英文"""
        if not text:
            return False
        # 计算非ASCII字符比例
        non_ascii = sum(1 for c in text if ord(c) > 127)
        return non_ascii / len(text) < 0.3

    async def search_by_exact_title(self, title: str) -> Optional[Dict]:
        """
        精确标题搜索，用于锚定已知的核心论文。

        使用 Semantic Scholar 的 paper/search 端点，
        以标题作为查询词，取第一条结果。

        Args:
            title: 论文的完整英文标题

        Returns:
            匹配到的论文（Dict）或 None
        """
        try:
            papers = await self.search_papers(
                query=f'title:"{title}"',
                limit=3
            )

            if not papers:
                # 回退：用标题直接搜索
                papers = await self.search_papers(
                    query=title,
                    limit=5
                )

            if papers:
                # 找标题最匹配的
                best = None
                best_score = 0
                title_lower = title.lower().strip()
                for p in papers:
                    p_title = (p.get("title") or "").lower().strip()
                    # 简单相似度：交集词占比
                    words_a = set(title_lower.split())
                    words_b = set(p_title.split())
                    if not words_a:
                        continue
                    overlap = len(words_a & words_b) / len(words_a)
                    if overlap > best_score:
                        best_score = overlap
                        best = p

                # 相似度阈值：至少 70% 的词匹配
                if best and best_score >= 0.7:
                    return best

            return None

        except Exception as e:
            print(f"[SemanticScholar] 精确标题搜索失败: {e}")
            return None

    async def search_by_venue(
        self,
        query: str,
        venue: str,
        years_ago: int = 5,
        limit: int = 100,
        min_citations: int = 0,
        sort: str = "citationCount:desc"
    ) -> List[Dict]:
        """
        在特定期刊/会议中搜索论文

        Args:
            query: 搜索关键词
            venue: 期刊/会议名称（如 "Nature", "NeurIPS", "ICML"）
            years_ago: 近N年
            limit: 返回数量
            min_citations: 最小被引量
            sort: 排序方式

        Returns:
            论文列表
        """
        return await self.search_papers(
            query=query,
            venue=venue,
            years_ago=years_ago,
            limit=limit,
            min_citations=min_citations,
            sort=sort
        )

    async def search_recent_highly_cited(
        self,
        query: str,
        year_start: int = None,
        year_end: int = None,
        min_citations: int = 10,
        limit: int = 50
    ) -> List[Dict]:
        """
        搜索近期高被引论文

        Args:
            query: 搜索关键词
            year_start: 起始年份（默认为3年前）
            year_end: 结束年份（默认为当前年份）
            min_citations: 最小被引量（默认10）
            limit: 返回数量

        Returns:
            论文列表（按引用量降序）
        """
        current_year = datetime.now().year
        if year_start is None:
            year_start = current_year - 3
        if year_end is None:
            year_end = current_year

        return await self.search_papers(
            query=query,
            year_start=year_start,
            year_end=year_end,
            min_citations=min_citations,
            limit=limit,
            sort="citationCount:desc"
        )

    async def search_top_venues(
        self,
        query: str,
        venues: List[str],
        years_ago: int = 5,
        limit_per_venue: int = 20
    ) -> List[Dict]:
        """
        在多个顶级期刊/会议中搜索论文

        Args:
            query: 搜索关键词
            venues: 期刊/会议列表（如 ["Nature", "Science", "Cell"]）
            years_ago: 近N年
            limit_per_venue: 每个期刊返回的论文数量

        Returns:
            论文列表
        """
        all_papers = []
        seen_ids = set()

        for venue in venues:
            papers = await self.search_by_venue(
                query=query,
                venue=venue,
                years_ago=years_ago,
                limit=limit_per_venue
            )

            # 去重
            for paper in papers:
                paper_id = paper.get("id")
                if paper_id and paper_id not in seen_ids:
                    seen_ids.add(paper_id)
                    all_papers.append(paper)

        # 按引用量排序
        all_papers.sort(key=lambda p: p.get("cited_by_count", 0), reverse=True)
        return all_papers


# ==================== 全局单例获取 ====================

def get_semantic_scholar_service() -> SemanticScholarService:
    """获取全局单例实例"""
    return SemanticScholarService(api_key=os.getenv("SEMANTIC_SCHOLAR_API_KEY"))


# ==================== 高级搜索示例 ====================

async def example_advanced_search():
    """Semantic Scholar 高级搜索示例"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    service = SemanticScholarService(api_key=api_key)

    try:
        print("=" * 80)
        print("Semantic Scholar 高级搜索示例")
        print("=" * 80)

        # 示例1: 搜索2021-2024年的LLM论文，按引用量排序
        print("\n[示例1] 搜索2021-2024年的LLM高被引论文")
        papers = await service.search_papers(
            query="large language model",
            year_start=2021,
            year_end=2024,
            limit=20,
            sort="citationCount:desc"
        )
        print(f"找到 {len(papers)} 篇论文")
        for i, p in enumerate(papers[:5], 1):
            print(f"  {i}. [{p.get('year')}] {p.get('title')[:60]}... (引用: {p.get('cited_by_count')})")

        # 示例2: 在特定期刊中搜索
        print("\n[示例2] 在 Nature 中搜索 transformer 论文")
        papers = await service.search_by_venue(
            query="transformer architecture",
            venue="Nature",
            years_ago=5,
            limit=10
        )
        print(f"找到 {len(papers)} 篇论文")
        for i, p in enumerate(papers[:3], 1):
            print(f"  {i}. {p.get('title')[:60]}...")

        # 示例3: 布尔查询
        print("\n[示例3] 布尔查询: (transformer OR attention) AND vision")
        papers = await service.search_papers(
            query="(transformer OR attention) AND vision",
            years_ago=3,
            limit=10,
            sort="citationCount:desc"
        )
        print(f"找到 {len(papers)} 篇论文")
        for i, p in enumerate(papers[:3], 1):
            print(f"  {i}. {p.get('title')[:60]}...")

        # 示例4: 搜索顶级期刊
        print("\n[示例4] 在顶级期刊中搜索 symbolic computation")
        top_venues = [
            "Journal of Symbolic Computation",
            "Journal of the ACM",
            "SIAM Journal on Computing"
        ]
        papers = await service.search_top_venues(
            query="symbolic computation OR computer algebra",
            venues=top_venues,
            years_ago=10,
            limit_per_venue=10
        )
        print(f"找到 {len(papers)} 篇论文")
        for i, p in enumerate(papers[:5], 1):
            venue = p.get('venue', 'Unknown')
            print(f"  {i}. [{venue}] {p.get('title')[:60]}...")

        print("\n" + "=" * 80)

    finally:
        await service.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_advanced_search())
