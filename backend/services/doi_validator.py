"""
文献验证服务 — 从文本中提取参考文献，逐条验证是否真实存在

解析：用 LLM 提取结构化参考文献
验证：英文 → OpenAlex，中文 → Crossref + Baidu Scholar
"""
import asyncio
import json
import logging
import re
from typing import Dict, List, Optional

from services.baidu_scholar_client import baidu_scholar_client
from services.openalex_search import get_openalex_service

logger = logging.getLogger(__name__)

# 检测中文字符
_CHINESE_RE = re.compile(r'[一-鿿]')
# 参考文献区域分隔符
_REF_SECTION_PATTERNS = [
    re.compile(r'^\s*(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY)\s*$', re.MULTILINE),
    re.compile(r'^\s*参考文献\s*$', re.MULTILINE),
]

MAX_REF_LENGTH = 30000  # 参考文献区域最大字符数（约 100-120 条引用）


def _is_chinese(text: str) -> bool:
    return bool(_CHINESE_RE.search(text))


def _extract_ref_section(text: str) -> str:
    """提取参考文献区域文本"""
    for pattern in _REF_SECTION_PATTERNS:
        m = pattern.search(text)
        if m:
            return text[m.end():]
    return text


async def _crossref_search_title(title: str) -> Optional[Dict]:
    """用 Crossref API 搜索标题（支持中文），返回最匹配的结果或 None"""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://api.crossref.org/works", params={
                "query.title": title,
                "rows": 5,
                "select": "title,DOI,author",
            })
            resp.raise_for_status()
            items = resp.json().get("message", {}).get("items", [])
            if not items:
                return None

            # 中文标题：关键词重叠匹配
            title_keywords = set(re.findall(r'[一-鿿]{2,}', title))
            for item in items:
                item_title = (item.get("title") or [""])[0]
                if not item_title:
                    continue
                item_keywords = set(re.findall(r'[一-鿿]{2,}', item_title))
                if not title_keywords or not item_keywords:
                    continue
                overlap = len(title_keywords & item_keywords) / len(title_keywords)
                if overlap >= 0.5:
                    return {
                        "title": item_title,
                        "doi": item.get("DOI", ""),
                        "source": "crossref",
                    }
            return None
    except Exception as e:
        logger.debug(f"[Crossref] search error: {e}")
        return None


async def _llm_parse_references(text: str) -> List[Dict]:
    """用 LLM 从文本中解析出结构化参考文献列表"""
    ref_text = _extract_ref_section(text)

    # 截断过长文本，节省 LLM 调用花费
    if len(ref_text) > MAX_REF_LENGTH:
        ref_text = ref_text[:MAX_REF_LENGTH]

    # 文本太短直接返回
    if len(ref_text.strip()) < 20:
        return []

    from authkit.llm.client import LLMClient
    client = LLMClient()

    prompt = f"""You are a reference parser. Extract ALL references from the text below.

For each reference, output a JSON array where each item has:
- "raw": the original reference text (preserve exactly)
- "title": the paper/chapter title only (no authors, no journal, no year)
- "first_author": the first author's last name (or full name for Chinese)
- "language": "zh" if the title contains Chinese characters, otherwise "en"

Rules:
- Extract the TITLE only, not the journal name, year, or volume info
- If the reference has a DOI, include it in a "doi" field
- Return ONLY the JSON array, no other text

Text:
```
{ref_text}
```"""

    response = await client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=4096,
    )

    # 解析 JSON
    content = response.strip()
    # 去掉可能的 markdown 代码块标记
    content = re.sub(r'^```(?:json)?\s*', '', content)
    content = re.sub(r'\s*```$', '', content)

    try:
        refs = json.loads(content)
    except json.JSONDecodeError:
        # 尝试找到 JSON 数组
        m = re.search(r'\[.*\]', content, re.DOTALL)
        if m:
            refs = json.loads(m.group())
        else:
            logger.error(f"[DOIValidator] LLM 返回无效 JSON: {content[:200]}")
            return []

    if not isinstance(refs, list):
        return []

    # 标准化字段
    for r in refs:
        r.setdefault("title", "")
        r.setdefault("first_author", "")
        r.setdefault("language", "zh" if _is_chinese(r.get("title", "")) else "en")
        r.setdefault("raw", "")

    return refs


async def validate_reference(ref: Dict) -> Dict:
    """验证单条参考文献"""
    title = ref.get("title", "")
    author = ref.get("first_author", "")
    lang = ref.get("language", "en")

    if not title or len(title) < 3:
        return {
            **ref,
            "verified": False,
            "status": "skipped",
            "message": "无法提取标题",
        }

    try:
        # 英文文献：OpenAlex
        if lang == "en":
            result = await get_openalex_service().search_by_exact_title(title)
            if result:
                return {
                    **ref,
                    "verified": True,
                    "status": "verified",
                    "match_title": result.get("title", ""),
                    "doi": result.get("doi", ""),
                    "source": "openalex",
                }

        # 中文文献：Crossref → Baidu Scholar
        if lang == "zh":
            result = await _crossref_search_title(title)
            if result:
                return {
                    **ref,
                    "verified": True,
                    "status": "verified",
                    "match_title": result["title"],
                    "doi": result.get("doi", ""),
                    "source": "crossref",
                }

            result_bs = await baidu_scholar_client.search_by_title(title, author)
            if result_bs and result_bs.get("found"):
                return {
                    **ref,
                    "verified": True,
                    "status": "verified",
                    "match_title": result_bs["title"],
                    "source": "baidu_scholar",
                    "url": result_bs.get("url", ""),
                }

        return {
            **ref,
            "verified": False,
            "status": "not_found",
            "message": "未找到匹配文献",
        }
    except Exception as e:
        logger.error(f"[DOIValidator] Error validating '{title}': {e}")
        return {
            **ref,
            "verified": False,
            "status": "error",
            "message": str(e),
        }


async def validate_all(text: str) -> Dict:
    """
    验证文本中的所有参考文献。

    Returns:
        {
            "total": int,
            "verified": int,
            "suspicious": int,
            "errors": int,
            "references": [{raw, title, verified, status, ...}]
        }
    """
    refs = await _llm_parse_references(text)
    if not refs:
        return {
            "total": 0,
            "verified": 0,
            "suspicious": 0,
            "errors": 0,
            "references": [],
        }

    # 并发验证，限制并发数
    semaphore = asyncio.Semaphore(5)

    async def _validate_with_semaphore(ref):
        async with semaphore:
            return await validate_reference(ref)

    results = await asyncio.gather(*[_validate_with_semaphore(r) for r in refs])

    verified = sum(1 for r in results if r.get("verified"))
    suspicious = sum(1 for r in results if r.get("status") == "not_found")
    errors = sum(1 for r in results if r.get("status") == "error")

    return {
        "total": len(results),
        "verified": verified,
        "suspicious": suspicious,
        "errors": errors,
        "references": results,
    }
