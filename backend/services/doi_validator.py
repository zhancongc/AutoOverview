"""
文献验证服务 — 从文本中提取参考文献，逐条验证是否真实存在

中文文献 → Baidu Scholar
英文文献 → OpenAlex
"""
import asyncio
import logging
import re
from typing import Dict, List, Optional

from services.baidu_scholar_client import baidu_scholar_client
from services.openalex_search import get_openalex_service

logger = logging.getLogger(__name__)

# 参考文献区域分隔符
REF_SECTION_PATTERNS = [
    re.compile(r'^\s*(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY)\s*$', re.MULTILINE),
    re.compile(r'^\s*参考文献\s*$', re.MULTILINE),
    re.compile(r'^\s*参\s*考\s*文\s*献\s*$', re.MULTILINE),
    re.compile(r'^\s*\[?参考文献\]?\s*$', re.MULTILINE),
]

# 检测中文字符
_CHINESE_RE = re.compile(r'[一-鿿]')

# 从单条引用中提取标题
# 1. 引号内的内容（中英文引号）
_QUOTED_TITLE_RE = re.compile(r'["“”]([^"“”]{5,})["“”]')
# 2. 英文: 从句首到第一个句号（排除开头的序号/作者）
_EN_TITLE_RE = re.compile(
    r'(?:^|\.\s)([A-Z][^.]*?\.(?:\s[A-Z][^.]*?\.)*)'
)
# 3. 中文: 到第一个句号
_CN_TITLE_RE = re.compile(r'[。．\.\s]([^\[【\(（\d].*?[。．])')

# 提取作者（参考文献开头部分）
_AUTHOR_PATTERNS = [
    re.compile(r'^\[?\d+\]?\s*([^,.，]+?)[,.，]\s*'),  # [1] Author,
    re.compile(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s*,|\s+and))'),  # English Author,
]


def _is_chinese(text: str) -> bool:
    return bool(_CHINESE_RE.search(text))


def _extract_title(ref: str) -> str:
    """从单条参考文献中提取标题"""
    # 尝试引号匹配
    m = _QUOTED_TITLE_RE.search(ref)
    if m:
        return m.group(1).strip()

    # 去掉开头序号 [1] 或 1.
    cleaned = re.sub(r'^\s*\[?\d+\]?\s*\.?\s*', '', ref).strip()

    if _is_chinese(cleaned):
        # 中文: 找第一个句号前最长的有意义的段
        parts = re.split(r'[。．;\；]', cleaned)
        if parts:
            # 取最可能是标题的部分（通常含书名号或较长）
            best = max(parts, key=lambda p: len(p.strip()))
            return best.strip()[:100]
    else:
        # 英文: 找句号之间的段，取最长的一段（排除短的作者名段）
        parts = re.split(r'\.\s+', cleaned)
        if len(parts) >= 2:
            # 跳过第一段（通常是作者），取最长段
            candidates = parts[1:]
            best = max(candidates, key=lambda p: len(p.strip()))
            return best.strip().rstrip('.')[:200]
        elif parts:
            return parts[0].strip()[:200]

    return cleaned[:200]


def _extract_author(ref: str) -> str:
    """尝试提取第一作者"""
    for pattern in _AUTHOR_PATTERNS:
        m = pattern.search(ref)
        if m:
            author = m.group(1).strip()
            if len(author) < 50 and not author.isdigit():
                return author
    return ""


def parse_references(text: str) -> List[Dict]:
    """
    从文本中提取参考文献列表。

    Returns:
        [{"raw": "完整引用", "title": "提取的标题", "author": "第一作者", "language": "zh/en"}]
    """
    # 找参考文献区域
    ref_text = text
    for pattern in REF_SECTION_PATTERNS:
        m = pattern.search(text)
        if m:
            ref_text = text[m.end():]
            break

    # 按行分割，过滤空行和太短的行
    lines = ref_text.split('\n')
    refs = []
    for line in lines:
        line = line.strip()
        if len(line) < 15:
            continue
        # 跳过明显的非引用行
        if re.match(r'^\s*(?:Chapter|CHAPTER|第[一二三四五六七八九十\d]+[章节])', line):
            continue
        if line.startswith('://') or line.startswith('http'):
            continue
        refs.append(line)

    if not refs:
        return []

    # 合并被换行符打断的引用（下一行不以序号开头的接到上一行）
    merged = []
    for line in refs:
        if merged and not re.match(r'^\s*\[?\d+\]', line) and not re.match(r'^\s*[A-Z][a-z]', line):
            merged[-1] += ' ' + line
        else:
            merged.append(line)

    # 解析每条引用
    results = []
    for raw in merged:
        title = _extract_title(raw)
        author = _extract_author(raw)
        lang = "zh" if _is_chinese(raw) else "en"
        results.append({
            "raw": raw,
            "title": title,
            "author": author,
            "language": lang,
        })

    return results


async def validate_reference(ref: Dict) -> Dict:
    """验证单条参考文献"""
    title = ref.get("title", "")
    author = ref.get("author", "")
    lang = ref.get("language", "en")

    if not title or len(title) < 3:
        return {
            **ref,
            "verified": False,
            "status": "skipped",
            "message": "无法提取标题",
        }

    try:
        if lang == "zh":
            result = await baidu_scholar_client.search_by_title(title, author)
            if result and result.get("found"):
                return {
                    **ref,
                    "verified": True,
                    "status": "verified",
                    "match_title": result["title"],
                    "source": "baidu_scholar",
                    "url": result.get("url", ""),
                }
            return {
                **ref,
                "verified": False,
                "status": "not_found",
                "message": "Baidu Scholar 未找到匹配文献",
            }
        else:
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
            return {
                **ref,
                "verified": False,
                "status": "not_found",
                "message": "OpenAlex 未找到匹配文献",
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
    refs = parse_references(text)
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
