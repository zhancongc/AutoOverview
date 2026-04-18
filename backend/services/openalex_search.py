"""
OpenAlex 文献检索服务
API 免费且无需 key，携带 mailto header 可获得更高速率限制（10+ req/s）。
返回与 SemanticScholarService 相同的 paper 数据格式，实现无缝替换。
"""
import httpx
import asyncio
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenAlexService:
    """
    OpenAlex API 客户端（全局单例）

    与 SemanticScholarService 实现相同的接口方法，返回相同的 paper dict 格式。
    """

    BASE_URL = "https://api.openalex.org"

    _instance = None
    _initialized = False

    def __new__(cls, email: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, email: str = None):
        if self._initialized:
            if email and not self.email:
                self.email = email
            return

        headers = {"User-Agent": "AutoOverview/1.0"}
        if email:
            headers["mailto"] = email

        self.client = httpx.AsyncClient(timeout=30.0, headers=headers)
        self.email = email or ""
        self.max_retries = 3
        self.retry_delay = 2
        self._initialized = True

    async def close(self):
        pass

    async def shutdown(self):
        if self.client:
            await self.client.aclose()

    def _parse_work(self, item: Dict) -> Dict:
        """将 OpenAlex work 转换为标准 paper 格式（与 Semantic Scholar 一致）"""
        # 作者
        authors = []
        for authorship in item.get("authorships", [])[:10]:
            author = authorship.get("author", {})
            name = author.get("display_name", "")
            if name:
                authors.append(name)

        # 标题
        title = item.get("title", "") or ""
        is_english = self._is_english(title)

        # DOI（去掉 https://doi.org/ 前缀）
        doi = item.get("doi", "")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/"):]

        # 期刊/会议
        venue_name = ""
        primary_location = item.get("primary_location") or {}
        source = primary_location.get("source") or {}
        if source:
            venue_name = source.get("display_name", "")

        # 摘要（OpenAlex 用 inverted index 存储）
        abstract = self._decode_abstract(item.get("abstract_inverted_index"))

        # ID：用 OpenAlex ID 短格式（W1234...）
        openalex_id = item.get("id", "")
        if openalex_id.startswith("https://openalex.org/"):
            openalex_id = openalex_id.split("/")[-1]

        return {
            "id": openalex_id,
            "title": title,
            "authors": authors,
            "year": item.get("publication_year"),
            "cited_by_count": item.get("cited_by_count", 0),
            "is_english": is_english,
            "abstract": abstract,
            "type": item.get("type", "article"),
            "doi": doi,
            "venue": venue_name,
            "journal": venue_name,
            "venue_name": venue_name,
            "primary_location": {
                "source": {
                    "display_name": venue_name
                } if venue_name else {}
            },
            "concepts": [],
            "source": "openalex"
        }

    def _decode_abstract(self, inverted_index: Optional[Dict]) -> str:
        """将 OpenAlex inverted index 转换为普通文本"""
        if not inverted_index:
            return ""

        word_count = max(pos for positions in inverted_index.values() for pos in positions) + 1
        words = [""] * word_count
        for word, positions in inverted_index.items():
            for pos in positions:
                words[pos] = word
        return " ".join(words)

    def _is_english(self, text: str) -> bool:
        if not text:
            return False
        non_ascii = sum(1 for c in text if ord(c) > 127)
        return non_ascii / len(text) < 0.3

    def _build_date_filter(self, years_ago: int = None, year_start: int = None, year_end: int = None) -> str:
        """构建 OpenAlex 日期过滤条件"""
        current_year = datetime.now().year
        if year_start is None and years_ago:
            year_start = current_year - years_ago
        if year_end is None:
            year_end = current_year

        filters = []
        if year_start:
            filters.append(f"from_publication_date:{year_start}-01-01")
        if year_end:
            filters.append(f"to_publication_date:{year_end}-12-31")
        return ",".join(filters)

    def _build_sort(self, sort: str = None) -> str:
        """将 Semantic Scholar 排序格式转换为 OpenAlex 格式"""
        if not sort:
            return "cited_by_count:desc"
        # SS: "citationCount:desc" → OA: "cited_by_count:desc"
        # SS: "publicationDate:desc" → OA: "publication_date:desc"
        mapping = {
            "citationCount": "cited_by_count",
            "publicationDate": "publication_date",
        }
        parts = sort.split(":")
        if len(parts) == 2:
            field = mapping.get(parts[0], parts[0])
            return f"{field}:{parts[1]}"
        return sort

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
        搜索论文（接口与 SemanticScholarService 一致）

        OpenAlex 支持更高速率（10+ req/s），适合高频搜索场景。

        针对多词组合查询（含 AND/OR），使用 title.search + abstract.search
        代替全文 search 参数，显著提升精度。
        """
        filter_parts = []

        # 日期过滤
        date_filter = self._build_date_filter(years_ago=years_ago, year_start=year_start, year_end=year_end)
        if date_filter:
            filter_parts.append(date_filter)

        # 最小被引量
        if min_citations > 0:
            filter_parts.append(f"cited_by_count:>{min_citations}")

        # 期刊/会议过滤
        if venue:
            filter_parts.append(f"primary_location.source.display_name.search:{venue}")

        # 开放获取
        if open_access_pdf:
            filter_parts.append("is_oa:true")

        # 判断查询复杂度，选择最优搜索策略
        use_precise_search = self._should_use_precise_search(query)
        if use_precise_search:
            filter_parts.append(f"title.search:{query}")
            sort_param = "publication_date:desc"
            search_param = None
        else:
            sort_param = self._build_sort(sort)
            search_param = query

        params = {
            "per_page": min(limit, 200),
            "sort": sort_param,
        }
        if search_param:
            params["search"] = search_param
        if filter_parts:
            params["filter"] = ",".join(filter_parts)

        logger.debug(f"[OpenAlex] 搜索: query=\"{query[:80]}\", mode={'precise' if use_precise_search else 'broad'}, limit={limit}")

        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(
                    f"{self.BASE_URL}/works",
                    params=params
                )

                if response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        backoff = self.retry_delay * (2 ** attempt)
                        logger.debug(f"[OpenAlex] 429 限流，{backoff}s 后重试")
                        await asyncio.sleep(backoff)
                        continue
                    return []

                response.raise_for_status()
                data = response.json()

                papers = []
                for item in data.get("results", []):
                    paper = self._parse_work(item)
                    # 二次过滤被引量（OpenAlex filter 可能不完全精确）
                    if paper["cited_by_count"] < min_citations:
                        continue
                    papers.append(paper)

                # precise 模式结果不够时，补充一次 broad search
                if use_precise_search and len(papers) < limit // 2:
                    logger.debug(f"[OpenAlex] precise 模式仅 {len(papers)} 篇，补充 broad search")
                    broad_papers = await self._broad_search(
                        query, years_ago, limit, min_citations, venue,
                        year_start, year_end, sort, open_access_pdf
                    )
                    seen_ids = {p.get("id") for p in papers}
                    for p in broad_papers:
                        if p.get("id") not in seen_ids:
                            seen_ids.add(p.get("id"))
                            papers.append(p)

                logger.debug(f"[OpenAlex] 获取 {len(papers)} 篇论文")
                return papers

            except httpx.HTTPStatusError as e:
                logger.debug(f"[OpenAlex] HTTP 错误: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    return []
            except Exception as e:
                logger.debug(f"[OpenAlex] 请求失败: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    return []

        return []

    def _should_use_precise_search(self, query: str) -> bool:
        """
        判断是否应使用 title.search 精准模式。

        触发条件：查询包含 AND/OR 连接的多词组合（LLM 生成的组合查询词），
        或包含 3+ 个技术术语（niche 主题）。
        """
        has_boolean = " AND " in query or " OR " in query
        # 清理布尔运算符后计算有效词数
        clean = query.upper().replace(" AND ", " ").replace(" OR ", " ").replace(" NOT ", " ")
        words = [w for w in clean.split() if len(w) >= 3]
        return has_boolean or len(words) >= 4

    async def _broad_search(
        self, query, years_ago, limit, min_citations, venue,
        year_start, year_end, sort, open_access_pdf
    ) -> List[Dict]:
        """兜底的宽泛搜索（使用 search 参数）"""
        filter_parts = []
        date_filter = self._build_date_filter(years_ago=years_ago, year_start=year_start, year_end=year_end)
        if date_filter:
            filter_parts.append(date_filter)
        if min_citations > 0:
            filter_parts.append(f"cited_by_count:>{min_citations}")
        if venue:
            filter_parts.append(f"primary_location.source.display_name.search:{venue}")
        if open_access_pdf:
            filter_parts.append("is_oa:true")

        # broad search 时用 abstract.search 限制范围，比 search 更精准
        clean_query = query.upper().replace(" AND ", " ").replace(" OR ", " ").strip()
        filter_parts.append(f"abstract.search:{clean_query}")

        params = {
            "per_page": min(limit, 200),
            "sort": "publication_date:desc",
        }
        if filter_parts:
            params["filter"] = ",".join(filter_parts)

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/works",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            papers = []
            for item in data.get("results", []):
                paper = self._parse_work(item)
                if paper["cited_by_count"] < min_citations:
                    continue
                papers.append(paper)
            return papers
        except Exception as e:
            logger.debug(f"[OpenAlex] broad search 失败: {e}")
            return []

    async def search_by_exact_title(self, title: str) -> Optional[Dict]:
        """精确标题搜索"""
        try:
            # 用 title 过滤做精确匹配
            params = {
                "filter": f"title.search:{title}",
                "per_page": 5,
            }
            response = await self.client.get(
                f"{self.BASE_URL}/works",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            papers = [self._parse_work(item) for item in data.get("results", [])]
            if papers:
                # 找标题最匹配的
                title_lower = title.lower().strip()
                words_a = set(title_lower.split())
                best = None
                best_score = 0
                for p in papers:
                    p_title = (p.get("title") or "").lower().strip()
                    words_b = set(p_title.split())
                    if not words_a:
                        continue
                    overlap = len(words_a & words_b) / len(words_a)
                    if overlap > best_score:
                        best_score = overlap
                        best = p
                if best and best_score >= 0.7:
                    return best

            return None
        except Exception as e:
            logger.debug(f"[OpenAlex] 精确标题搜索失败: {e}")
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
        """在特定期刊/会议中搜索论文"""
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
        """搜索近期高被引论文"""
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
        """在多个顶级期刊/会议中搜索论文"""
        all_papers = []
        seen_ids = set()

        for venue in venues:
            papers = await self.search_by_venue(
                query=query,
                venue=venue,
                years_ago=years_ago,
                limit=limit_per_venue
            )
            for paper in papers:
                paper_id = paper.get("id")
                if paper_id and paper_id not in seen_ids:
                    seen_ids.add(paper_id)
                    all_papers.append(paper)

        all_papers.sort(key=lambda p: p.get("cited_by_count", 0), reverse=True)
        return all_papers


def get_openalex_service() -> OpenAlexService:
    """获取全局单例实例"""
    return OpenAlexService(email=os.getenv("OPENALEX_EMAIL", ""))
