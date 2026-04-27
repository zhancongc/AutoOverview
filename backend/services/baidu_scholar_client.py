"""
百度学术搜索客户端 — 用标题+作者搜索验证中文文献是否存在
"""
import asyncio
import logging
import random
import re
import urllib.parse
from typing import Optional, Dict

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


def _title_similarity(a: str, b: str) -> float:
    """基于词重叠的标题相似度"""
    if not a or not b:
        return 0.0
    # 移除标点，按字符 bigram 比较（适合中文）
    a_clean = re.sub(r'[^\w]', '', a.lower())
    b_clean = re.sub(r'[^\w]', '', b.lower())
    if a_clean == b_clean:
        return 1.0
    if not a_clean or not b_clean:
        return 0.0
    # bigram similarity (Dice coefficient)
    a_bigrams = set(a_clean[i:i+2] for i in range(len(a_clean) - 1))
    b_bigrams = set(b_clean[i:i+2] for i in range(len(b_clean) - 1))
    if not a_bigrams or not b_bigrams:
        return 0.0
    return 2 * len(a_bigrams & b_bigrams) / (len(a_bigrams) + len(b_bigrams))


class BaiduScholarClient:
    """百度学术搜索"""

    BASE_URL = "https://xueshu.baidu.com/s"

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers={"Accept-Language": "zh-CN,zh;q=0.9"},
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def search_by_title(
        self,
        title: str,
        author: str = "",
        max_retries: int = 2,
    ) -> Optional[Dict]:
        """
        搜索百度学术，验证文献是否存在。

        Returns:
            {"found": True, "title": "...", "url": "...", "source": "baidu_scholar"}
            or None if not found
        """
        query = title
        if author:
            query = f"{title} {author}"

        params = {"wd": query, "ie": "utf-8"}

        for attempt in range(max_retries + 1):
            try:
                client = await self._get_client()
                headers = {
                    "User-Agent": random.choice(USER_AGENTS),
                    "Referer": "https://xueshu.baidu.com/",
                }
                resp = await client.get(self.BASE_URL, params=params, headers=headers)

                if resp.status_code == 429 or resp.status_code == 403:
                    logger.warning(f"[BaiduScholar] Rate limited (attempt {attempt+1})")
                    await asyncio.sleep(2 ** attempt)
                    continue

                resp.raise_for_status()
                result = self._parse_results(resp.text, title)
                if result:
                    return result

                # 没有匹配，再试一次不加作者
                if author and attempt == 0:
                    params["wd"] = title
                    continue

                return None

            except Exception as e:
                logger.warning(f"[BaiduScholar] Search error (attempt {attempt+1}): {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
                continue

        return None

    def _parse_results(self, html: str, target_title: str) -> Optional[Dict]:
        """解析搜索结果页，查找匹配的标题"""
        soup = BeautifulSoup(html, "html.parser")

        # 百度学术结果页标题在 .t 或 .sc_content 的 <a> 标签中
        titles = []
        for link in soup.select(".t a, .sc_content h3 a, .c_font a, .result-op a"):
            text = link.get_text(strip=True)
            if text:
                titles.append({"title": text, "url": link.get("href", "")})

        # 如果结构选择器没命中，fallback: 找所有含 target 关键词的链接
        if not titles:
            for link in soup.find_all("a"):
                text = link.get_text(strip=True)
                if text and len(text) > 10:
                    titles.append({"title": text, "url": link.get("href", "")})

        # 找最佳匹配
        best_match = None
        best_score = 0.0
        for t in titles:
            score = _title_similarity(target_title, t["title"])
            if score > best_score:
                best_score = score
                best_match = t

        if best_match and best_score >= 0.6:
            return {
                "found": True,
                "title": best_match["title"],
                "url": best_match.get("url", ""),
                "source": "baidu_scholar",
            }

        return None


# Singleton
baidu_scholar_client = BaiduScholarClient()
