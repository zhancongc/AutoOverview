"""
DOI Validator 文献验证测试

测试内容：
1. 参考文献区域提取（_extract_ref_section）
2. LLM 解析 Mock（_llm_parse_references）
3. 语言检测（_is_chinese）
4. 百度学术客户端（BaiduScholarClient）
5. 单条验证 Mock
6. 完整验证流程（validate_all）
7. /api/verify-references 端点
"""
import sys
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from services.doi_validator import (
    _extract_ref_section,
    _is_chinese,
    validate_reference,
    validate_all,
    MAX_REF_LENGTH,
)
from services.baidu_scholar_client import _title_similarity, BaiduScholarClient


# ==================== 1. 语言检测 ====================

class TestLanguageDetection:
    def test_chinese_text(self):
        assert _is_chinese("张三等. 深度学习综述. 计算机学报, 2023.") is True

    def test_english_text(self):
        assert _is_chinese("Smith J. Deep Learning for NLP. Nature, 2023.") is False

    def test_mixed_text(self):
        assert _is_chinese("基于Transformer的NLP模型综述") is True

    def test_empty_text(self):
        assert _is_chinese("") is False


# ==================== 2. 参考文献区域提取 ====================

class TestExtractRefSection:
    def test_english_references(self):
        text = "Body text here.\n\nReferences\n\n[1] Smith. Deep Learning. Nature, 2023."
        section = _extract_ref_section(text)
        assert "Smith" in section
        assert "Body text" not in section

    def test_chinese_references(self):
        text = "正文内容。\n\n参考文献\n\n[1] 张三. 深度学习综述. 计算机学报, 2023."
        section = _extract_ref_section(text)
        assert "张三" in section
        assert "正文内容" not in section

    def test_no_section_returns_all(self):
        text = "[1] Smith. Deep Learning. Nature, 2023."
        section = _extract_ref_section(text)
        assert section == text


# ==================== 3. LLM 解析 Mock ====================

@pytest.mark.asyncio
async def test_llm_parse_references_success():
    """LLM 返回有效 JSON"""
    mock_response = json.dumps([
        {"raw": "[1] Vaswani A. Attention Is All You Need. NeurIPS, 2017.",
         "title": "Attention Is All You Need", "first_author": "Vaswani", "language": "en"},
        {"raw": "[2] 张三. 深度学习综述. 计算机学报, 2023.",
         "title": "深度学习综述", "first_author": "张三", "language": "zh"},
    ])

    mock_client = MagicMock()
    mock_client.chat = AsyncMock(return_value=mock_response)

    with patch("authkit.llm.client.LLMClient", return_value=mock_client):
        from services.doi_validator import _llm_parse_references
        refs = await _llm_parse_references("References\n\n[1] Vaswani A. Attention Is All You Need. NeurIPS, 2017.\n[2] 张三. 深度学习综述. 计算机学报, 2023.")

        assert len(refs) == 2
        assert refs[0]["title"] == "Attention Is All You Need"
        assert refs[1]["language"] == "zh"


@pytest.mark.asyncio
async def test_llm_parse_references_with_markdown():
    """LLM 返回带 markdown 代码块的 JSON"""
    mock_response = '```json\n[{"raw": "[1] Test.", "title": "Test Paper", "first_author": "Smith", "language": "en"}]\n```'

    mock_client = MagicMock()
    mock_client.chat = AsyncMock(return_value=mock_response)

    with patch("authkit.llm.client.LLMClient", return_value=mock_client):
        from services.doi_validator import _llm_parse_references
        refs = await _llm_parse_references("References\n\n[1] Smith J. Test Paper Title. Nature, 2023.")

        assert len(refs) == 1
        assert refs[0]["title"] == "Test Paper"


@pytest.mark.asyncio
async def test_llm_parse_references_empty():
    """空文本"""
    from services.doi_validator import _llm_parse_references
    refs = await _llm_parse_references("No references here.")
    assert refs == []


# ==================== 4. 标题相似度 ====================

class TestTitleSimilarity:
    def test_identical_titles(self):
        score = _title_similarity("Deep Learning for NLP", "Deep Learning for NLP")
        assert score == 1.0

    def test_similar_chinese_titles(self):
        score = _title_similarity(
            "深度学习在自然语言处理中的应用",
            "深度学习在自然语言处理中的应用研究"
        )
        assert score >= 0.6

    def test_different_titles(self):
        score = _title_similarity("Deep Learning for NLP", "Quantum Computing Algorithms")
        assert score < 0.3

    def test_empty_title(self):
        score = _title_similarity("", "Some Title")
        assert score == 0.0


# ==================== 5. 百度学术客户端 ====================

class TestBaiduScholarClient:
    def test_parse_results_with_matching_title(self):
        client = BaiduScholarClient()
        html = '<div class="t"><a href="/1">深度学习在自然语言处理中的应用综述</a></div>'
        result = client._parse_results(html, "深度学习在自然语言处理中的应用综述")
        assert result is not None
        assert result["found"] is True

    def test_parse_results_no_match(self):
        client = BaiduScholarClient()
        html = '<div class="t"><a href="/1">量子计算算法研究进展</a></div>'
        result = client._parse_results(html, "完全不相关的标题关于海洋生物学")
        assert result is None

    def test_parse_empty_html(self):
        client = BaiduScholarClient()
        result = client._parse_results("<html><body></body></html>", "Some Title")
        assert result is None


# ==================== 6. 单条验证（Mock 外部 API）====================

@pytest.mark.asyncio
async def test_validate_english_reference_verified():
    """英文文献 — OpenAlex 命中"""
    mock_service = MagicMock()
    mock_service.search_by_exact_title = AsyncMock(return_value={
        "title": "Attention Is All You Need", "doi": "10.5555/123456",
    })
    with patch("services.doi_validator.get_openalex_service", return_value=mock_service):
        ref = {"raw": '[1] Vaswani et al. "Attention Is All You Need." NeurIPS, 2017.',
               "title": "Attention Is All You Need", "first_author": "Vaswani", "language": "en"}
        result = await validate_reference(ref)
        assert result["verified"] is True
        assert result["status"] == "verified"
        assert result["doi"] == "10.5555/123456"


@pytest.mark.asyncio
async def test_validate_english_reference_not_found():
    """英文文献 — OpenAlex 未命中"""
    mock_service = MagicMock()
    mock_service.search_by_exact_title = AsyncMock(return_value=None)
    with patch("services.doi_validator.get_openalex_service", return_value=mock_service):
        ref = {"raw": '[1] Fake. "This Paper Does Not Exist." Journal of Nothing, 2099.',
               "title": "This Paper Does Not Exist", "first_author": "Fake", "language": "en"}
        result = await validate_reference(ref)
        assert result["verified"] is False
        assert result["status"] == "not_found"


@pytest.mark.asyncio
async def test_validate_chinese_reference_verified():
    """中文文献 — OpenAlex 命中（现在中文也先查 OpenAlex）"""
    mock_service = MagicMock()
    mock_service.search_by_exact_title = AsyncMock(return_value={
        "title": "深度学习在自然语言处理中的应用综述",
        "doi": "10.1234/cn",
    })
    with patch("services.doi_validator.get_openalex_service", return_value=mock_service):
        ref = {"raw": '[1] 张三. "深度学习综述." 计算机学报, 2023.',
               "title": "深度学习综述", "first_author": "张三", "language": "zh"}
        result = await validate_reference(ref)
        assert result["verified"] is True
        assert result["source"] == "openalex"


@pytest.mark.asyncio
async def test_validate_chinese_reference_fallback_baidu():
    """中文文献 — OpenAlex 未命中，Baidu Scholar 命中"""
    mock_service = MagicMock()
    mock_service.search_by_exact_title = AsyncMock(return_value=None)
    with patch("services.doi_validator.get_openalex_service", return_value=mock_service), \
         patch("services.doi_validator.baidu_scholar_client") as mock_baidu:
        mock_baidu.search_by_title = AsyncMock(return_value={
            "found": True, "title": "深度学习综述",
            "url": "https://xueshu.baidu.com/123", "source": "baidu_scholar",
        })
        ref = {"raw": '[1] 张三. "深度学习综述." 计算机学报, 2023.',
               "title": "深度学习综述", "first_author": "张三", "language": "zh"}
        result = await validate_reference(ref)
        assert result["verified"] is True
        assert result["source"] == "baidu_scholar"


@pytest.mark.asyncio
async def test_validate_chinese_reference_not_found():
    """中文文献 — OpenAlex 和 Baidu Scholar 都未命中"""
    mock_service = MagicMock()
    mock_service.search_by_exact_title = AsyncMock(return_value=None)
    with patch("services.doi_validator.get_openalex_service", return_value=mock_service), \
         patch("services.doi_validator.baidu_scholar_client") as mock_baidu:
        mock_baidu.search_by_title = AsyncMock(return_value=None)
        ref = {"raw": '[1] 虚假作者. "不存在的论文." 虚假期刊, 2099.',
               "title": "不存在的论文", "first_author": "虚假", "language": "zh"}
        result = await validate_reference(ref)
        assert result["verified"] is False
        assert result["status"] == "not_found"


@pytest.mark.asyncio
async def test_validate_short_title_skipped():
    ref = {"raw": "[1] A.", "title": "A", "first_author": "", "language": "en"}
    result = await validate_reference(ref)
    assert result["verified"] is False
    assert result["status"] == "skipped"


# ==================== 7. 完整验证流程 ====================

@pytest.mark.asyncio
async def test_validate_all_mixed():
    """混合中英文参考文献验证"""
    mock_llm_response = json.dumps([
        {"raw": "[1] Vaswani A. Attention Is All You Need. NeurIPS, 2017.",
         "title": "Attention Is All You Need", "first_author": "Vaswani", "language": "en"},
        {"raw": "[2] 虚假作者. 不存在的中文论文. 虚假期刊, 2099.",
         "title": "不存在的中文论文", "first_author": "虚假", "language": "zh"},
    ])

    mock_openalex = MagicMock()
    # 英文命中，中文未命中（触发 Baidu Scholar fallback）
    call_count = [0]
    async def _mock_search(title):
        call_count[0] += 1
        if call_count[0] == 1:
            return {"title": "Attention Is All You Need", "doi": "10.5555/123"}
        return None
    mock_openalex.search_by_exact_title = AsyncMock(side_effect=_mock_search)

    mock_client = MagicMock()
    mock_client.chat = AsyncMock(return_value=mock_llm_response)

    with patch("authkit.llm.client.LLMClient", return_value=mock_client), \
         patch("services.doi_validator.get_openalex_service", return_value=mock_openalex), \
         patch("services.doi_validator.baidu_scholar_client") as mock_baidu:

        mock_baidu.search_by_title = AsyncMock(return_value=None)

        result = await validate_all("References\n\n[1] Vaswani A. Attention Is All You Need.\n[2] 虚假作者. 不存在的中文论文.")
        assert result["total"] == 2
        assert result["verified"] == 1
        assert result["suspicious"] == 1


@pytest.mark.asyncio
async def test_validate_all_empty():
    result = await validate_all("")
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_validate_all_handles_errors():
    """API 异常时应标记为 error"""
    mock_llm_response = json.dumps([
        {"raw": "[1] Smith. Important Research. Nature, 2023.",
         "title": "Important Research", "first_author": "Smith", "language": "en"},
    ])

    mock_openalex = MagicMock()
    mock_openalex.search_by_exact_title = AsyncMock(side_effect=Exception("Network error"))

    mock_client = MagicMock()
    mock_client.chat = AsyncMock(return_value=mock_llm_response)

    with patch("authkit.llm.client.LLMClient", return_value=mock_client), \
         patch("services.doi_validator.get_openalex_service", return_value=mock_openalex):

        result = await validate_all("References\n\n[1] Smith. Important Research.")
        assert result["total"] == 1
        assert result["errors"] == 1


# ==================== 8. 长度限制 ====================

def test_max_ref_length():
    assert MAX_REF_LENGTH == 30000


import json
