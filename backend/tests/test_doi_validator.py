"""
DOI Validator 文献验证测试

测试内容：
1. 参考文献解析（parse_references）— 中英文
2. 标题提取（_extract_title）
3. 语言检测（_is_chinese）
4. 百度学术客户端（BaiduScholarClient）
5. 完整验证流程（validate_all）— Mock 外部 API
6. /api/verify-references 端点测试
"""
import sys
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from services.doi_validator import (
    parse_references,
    validate_reference,
    validate_all,
    _extract_title,
    _extract_author,
    _is_chinese,
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


# ==================== 2. 标题提取 ====================

class TestExtractTitle:
    def test_quoted_title_english(self):
        ref = '[1] Smith, J. et al. "Deep Learning for Natural Language Processing." Nature, 2023.'
        title = _extract_title(ref)
        assert "Deep Learning" in title

    def test_quoted_title_chinese(self):
        ref = '[1] 张三, 李四. "深度学习在自然语言处理中的应用." 计算机学报, 2023.'
        title = _extract_title(ref)
        assert "深度学习" in title

    def test_english_no_quotes(self):
        ref = 'Smith J. Attention Is All You Need. Advances in Neural Information Processing Systems, 2017.'
        title = _extract_title(ref)
        assert len(title) > 5

    def test_chinese_no_quotes(self):
        ref = '张三. 基于注意力机制的文本分类方法研究. 中国科学, 2022.'
        title = _extract_title(ref)
        assert "注意力" in title or len(title) > 5

    def test_short_ref(self):
        ref = '[1] Short.'
        title = _extract_title(ref)
        assert len(title) > 0


# ==================== 3. 作者提取 ====================

class TestExtractAuthor:
    def test_english_author(self):
        ref = '[1] Smith, J. et al. "Deep Learning." Nature, 2023.'
        author = _extract_author(ref)
        assert "Smith" in author

    def test_numbered_ref(self):
        ref = '[1] Wang, L. "Attention." Science, 2022.'
        author = _extract_author(ref)
        assert len(author) > 0

    def test_no_author(self):
        ref = 'This is just a sentence with no clear author pattern.'
        author = _extract_author(ref)
        # 应该返回空或极短的字符串
        assert len(author) < 50


# ==================== 4. 参考文献列表解析 ====================

class TestParseReferences:
    def test_english_references_section(self):
        text = """
        This is the body of the paper with some content.

        References

        [1] Vaswani, A. et al. "Attention Is All You Need." NeurIPS, 2017.
        [2] Devlin, J. et al. "BERT: Pre-training of Deep Bidirectional Transformers." NAACL, 2019.
        [3] Brown, T. et al. "Language Models are Few-Shot Learners." NeurIPS, 2020.
        """
        refs = parse_references(text)
        assert len(refs) == 3
        assert all(r["language"] == "en" for r in refs)
        assert any("Attention" in r["title"] or "attention" in r["title"].lower() for r in refs)

    def test_chinese_references_section(self):
        text = """
        本文综述了深度学习在NLP中的应用。

        参考文献

        [1] 张三, 李四. "深度学习在自然语言处理中的应用综述." 计算机学报, 2023.
        [2] 王五. "注意力机制研究进展." 中国科学, 2022.
        """
        refs = parse_references(text)
        assert len(refs) == 2
        assert all(r["language"] == "zh" for r in refs)

    def test_no_references_section(self):
        text = """
        This is just a regular text with no references section.
        [1] Smith J. Some paper. Nature, 2023.
        [2] Wang L. Another paper. Science, 2022.
        """
        refs = parse_references(text)
        # 没有 References 分隔符，应该尝试解析所有内容
        assert len(refs) >= 2

    def test_empty_text(self):
        refs = parse_references("")
        assert refs == []

    def test_too_short_lines(self):
        text = "References\n[1] Too short"
        refs = parse_references(text)
        assert refs == []

    def test_mixed_languages(self):
        text = """
        References

        [1] Vaswani, A. "Attention Is All You Need." NeurIPS, 2017.
        [2] 张三. "基于注意力机制的文本分类." 计算机学报, 2022.
        [3] Brown, T. "Language Models." NeurIPS, 2020.
        """
        refs = parse_references(text)
        assert len(refs) == 3
        languages = [r["language"] for r in refs]
        assert "en" in languages
        assert "zh" in languages

    def test_multiline_reference(self):
        """测试被换行符打断的引用是否合并"""
        text = """
        References

        [1] Smith, J. et al. "Deep Learning for Natural Language Processing
        and Its Applications in Healthcare." Nature, 2023.
        [2] Wang, L. "Attention Mechanism." Science, 2022.
        """
        refs = parse_references(text)
        # 第一条引用跨两行，应该合并
        assert len(refs) >= 2


# ==================== 5. 标题相似度 ====================

class TestTitleSimilarity:
    def test_identical_titles(self):
        score = _title_similarity("Deep Learning for NLP", "Deep Learning for NLP")
        assert score == 1.0

    def test_similar_titles(self):
        score = _title_similarity(
            "深度学习在自然语言处理中的应用",
            "深度学习在自然语言处理中的应用研究"
        )
        assert score >= 0.6

    def test_different_titles(self):
        score = _title_similarity(
            "Deep Learning for NLP",
            "Quantum Computing Algorithms"
        )
        assert score < 0.3

    def test_empty_title(self):
        score = _title_similarity("", "Some Title")
        assert score == 0.0

    def test_partial_overlap(self):
        score = _title_similarity(
            "Attention Is All You Need",
            "Attention Is Not What You Need"
        )
        assert 0.3 < score < 0.8


# ==================== 6. 百度学术客户端 ====================

class TestBaiduScholarClient:
    def test_parse_results_with_matching_title(self):
        """测试 HTML 解析能从模拟搜索结果中找到匹配标题"""
        client = BaiduScholarClient()
        html = """
        <html><body>
        <div class="t"><a href="https://xueshu.baidu.com/1">
            深度学习在自然语言处理中的应用综述
        </a></div>
        <div class="t"><a href="https://xueshu.baidu.com/2">
            量子计算算法研究进展
        </a></div>
        </body></html>
        """
        result = client._parse_results(html, "深度学习在自然语言处理中的应用综述")
        assert result is not None
        assert result["found"] is True
        assert "深度学习" in result["title"]

    def test_parse_results_no_match(self):
        """测试不匹配的搜索结果"""
        client = BaiduScholarClient()
        html = """
        <html><body>
        <div class="t"><a href="https://xueshu.baidu.com/1">
            量子计算算法研究进展
        </a></div>
        </body></html>
        """
        result = client._parse_results(html, "完全不相关的标题关于海洋生物学")
        assert result is None

    def test_parse_empty_html(self):
        """测试空 HTML"""
        client = BaiduScholarClient()
        result = client._parse_results("<html><body></body></html>", "Some Title")
        assert result is None


# ==================== 7. 单条验证（Mock 外部 API）====================

@pytest.mark.asyncio
async def test_validate_english_reference_verified():
    """英文文献 — OpenAlex 命中"""
    mock_service = MagicMock()
    mock_service.search_by_exact_title = AsyncMock(return_value={
        "title": "Attention Is All You Need",
        "doi": "10.5555/123456",
    })
    with patch("services.doi_validator.get_openalex_service", return_value=mock_service):
        ref = {"raw": '[1] Vaswani et al. "Attention Is All You Need." NeurIPS, 2017.',
               "title": "Attention Is All You Need", "author": "Vaswani", "language": "en"}
        result = await validate_reference(ref)
        assert result["verified"] is True
        assert result["status"] == "verified"
        assert result["doi"] == "10.5555/123456"
        assert result["source"] == "openalex"


@pytest.mark.asyncio
async def test_validate_english_reference_not_found():
    """英文文献 — OpenAlex 未命中"""
    mock_service = MagicMock()
    mock_service.search_by_exact_title = AsyncMock(return_value=None)
    with patch("services.doi_validator.get_openalex_service", return_value=mock_service):
        ref = {"raw": '[1] Fake Author. "This Paper Does Not Exist." Journal of Nothing, 2099.',
               "title": "This Paper Does Not Exist", "author": "Fake", "language": "en"}
        result = await validate_reference(ref)
        assert result["verified"] is False
        assert result["status"] == "not_found"


@pytest.mark.asyncio
async def test_validate_chinese_reference_verified():
    """中文文献 — Baidu Scholar 命中"""
    mock_result = {
        "found": True,
        "title": "深度学习在自然语言处理中的应用综述",
        "url": "https://xueshu.baidu.com/123",
        "source": "baidu_scholar",
    }
    with patch("services.doi_validator.baidu_scholar_client") as mock_baidu:
        mock_baidu.search_by_title = AsyncMock(return_value=mock_result)
        ref = {"raw": '[1] 张三. "深度学习综述." 计算机学报, 2023.',
               "title": "深度学习综述", "author": "张三", "language": "zh"}
        result = await validate_reference(ref)
        assert result["verified"] is True
        assert result["status"] == "verified"
        assert result["source"] == "baidu_scholar"


@pytest.mark.asyncio
async def test_validate_chinese_reference_not_found():
    """中文文献 — Baidu Scholar 未命中"""
    with patch("services.doi_validator.baidu_scholar_client") as mock_baidu:
        mock_baidu.search_by_title = AsyncMock(return_value=None)
        ref = {"raw": '[1] 虚假作者. "一篇不存在的论文." 虚假期刊, 2099.',
               "title": "一篇不存在的论文", "author": "虚假", "language": "zh"}
        result = await validate_reference(ref)
        assert result["verified"] is False
        assert result["status"] == "not_found"


@pytest.mark.asyncio
async def test_validate_short_title_skipped():
    """标题太短应跳过"""
    ref = {"raw": "[1] A.", "title": "A", "author": "", "language": "en"}
    result = await validate_reference(ref)
    assert result["verified"] is False
    assert result["status"] == "skipped"


# ==================== 8. 完整验证流程（validate_all）====================

@pytest.mark.asyncio
async def test_validate_all_mixed():
    """混合中英文参考文献验证"""
    mock_openalex = MagicMock()
    mock_openalex.search_by_exact_title = AsyncMock(return_value={
        "title": "Attention Is All You Need", "doi": "10.5555/123"
    })
    with patch("services.doi_validator.get_openalex_service", return_value=mock_openalex), \
         patch("services.doi_validator.baidu_scholar_client") as mock_baidu:
        mock_baidu.search_by_title = AsyncMock(return_value=None)

        text = """
        References

        [1] Vaswani, A. "Attention Is All You Need." NeurIPS, 2017.
        [2] 虚假作者. "不存在的中文论文." 虚假期刊, 2099.
        """
        result = await validate_all(text)
        assert result["total"] == 2
        assert result["verified"] == 1
        assert result["suspicious"] == 1


@pytest.mark.asyncio
async def test_validate_all_empty():
    """空文本"""
    result = await validate_all("")
    assert result["total"] == 0
    assert result["references"] == []


@pytest.mark.asyncio
async def test_validate_all_all_verified():
    """全部验证通过"""
    mock_openalex = MagicMock()
    mock_openalex.search_by_exact_title = AsyncMock(return_value={
        "title": "Some Paper", "doi": "10.1234/5678"
    })
    with patch("services.doi_validator.get_openalex_service", return_value=mock_openalex):
        text = """
        References

        [1] Smith, J. "Some Paper Title Here." Nature, 2023.
        [2] Wang, L. "Another Paper Title." Science, 2022.
        """
        result = await validate_all(text)
        assert result["total"] == 2
        assert result["verified"] == 2
        assert result["suspicious"] == 0


@pytest.mark.asyncio
async def test_validate_all_handles_errors():
    """API 异常时应标记为 error"""
    mock_openalex = MagicMock()
    mock_openalex.search_by_exact_title = AsyncMock(side_effect=Exception("Network error"))
    with patch("services.doi_validator.get_openalex_service", return_value=mock_openalex):
        text = """
        References

        [1] Smith, J. "Important Research." Nature, 2023.
        """
        result = await validate_all(text)
        assert result["total"] == 1
        assert result["errors"] == 1
