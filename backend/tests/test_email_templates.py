"""
推广邮件 A/B 测试模板测试

测试内容：
1. 4 个模板都能正确渲染
2. 个性化变量替换（first_name, research_topic 等）
3. 随机模板选择
4. 指定模板选择
5. 模板内容完整性（HTML + Text + Subject）
6. 退订链接
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from authkit.templates.promo_email import render_promo_email, TEMPLATES


# ==================== 1. 基础渲染 ====================

class TestBasicRendering:
    def test_render_template_a(self):
        subject, html, text, variant = render_promo_email(
            name="John Smith",
            first_name="John",
            research_topic="brain-computer interfaces",
            university="University of Leeds",
            unsubscribe_url="https://example.com/unsub?token=abc",
            template_variant="a",
        )
        assert variant == "a"
        assert "John" in subject
        assert "John" in html
        assert "John" in text
        assert "brain-computer interfaces" in html
        assert "brain-computer interfaces" in text
        assert "email_a" in html
        assert "email_a" in text
        assert "https://example.com/unsub?token=abc" in text

    def test_render_template_b(self):
        subject, html, text, variant = render_promo_email(
            name="Alice Wang",
            first_name="Alice",
            template_variant="b",
        )
        assert variant == "b"
        assert "Alice" in html
        assert "email_b" in html
        assert "email_b" in text

    def test_render_template_c(self):
        subject, html, text, variant = render_promo_email(
            name="Bob Lee",
            first_name="Bob",
            template_variant="c",
        )
        assert variant == "c"
        assert "Bob" in html
        assert "fake citations" in subject.lower()
        assert "email_c" in html

    def test_render_template_d(self):
        subject, html, text, variant = render_promo_email(
            name="Carol Zhang",
            first_name="Carol",
            template_variant="d",
        )
        assert variant == "d"
        assert "Carol" in html
        assert "email_d" in html


# ==================== 2. 个性化变量 ====================

class TestPersonalization:
    def test_first_name_from_name(self):
        """不传 first_name 时自动从 name 提取"""
        _, html, _, _ = render_promo_email(
            name="John Smith",
            template_variant="a",
        )
        assert "John" in html

    def test_default_research_topic(self):
        """不传 research_topic 时使用默认值"""
        _, html, _, _ = render_promo_email(
            name="Test",
            template_variant="a",
        )
        assert "your research topic" in html

    def test_unsubscribe_url_in_all_templates(self):
        """所有模板都包含退订链接"""
        for v in ["a", "b", "c", "d"]:
            _, html, text, _ = render_promo_email(
                name="Test",
                unsubscribe_url="https://unsub.example.com/test",
                template_variant=v,
            )
            assert "https://unsub.example.com/test" in text, f"Template {v} missing unsub URL in text"
            assert "https://unsub.example.com/test" in html, f"Template {v} missing unsub URL in html"

    def test_empty_name_uses_default(self):
        """空 name 使用 Researcher"""
        _, html, text, _ = render_promo_email(
            name="",
            first_name="",
            template_variant="a",
        )
        assert "Researcher" in html


# ==================== 3. 模板选择逻辑 ====================

class TestTemplateSelection:
    def test_random_selection_without_variant(self):
        """不指定 variant 时随机选择"""
        variants_seen = set()
        for _ in range(50):
            _, _, _, v = render_promo_email(name="Test")
            variants_seen.add(v)
        # 跑 50 次应该至少覆盖 2 个不同模板（概率极高）
        assert len(variants_seen) >= 2, f"50次随机只选到 {variants_seen}"

    def test_forced_variant_a(self):
        _, _, _, v = render_promo_email(name="Test", template_variant="a")
        assert v == "a"

    def test_forced_variant_b(self):
        _, _, _, v = render_promo_email(name="Test", template_variant="b")
        assert v == "b"

    def test_forced_variant_c(self):
        _, _, _, v = render_promo_email(name="Test", template_variant="c")
        assert v == "c"

    def test_forced_variant_d(self):
        _, _, _, v = render_promo_email(name="Test", template_variant="d")
        assert v == "d"

    def test_invalid_variant_falls_back_to_a(self):
        _, _, _, v = render_promo_email(name="Test", template_variant="x")
        assert v == "a"


# ==================== 4. 模板内容完整性 ====================

class TestTemplateIntegrity:
    def test_all_templates_registered(self):
        """4 个模板都已注册"""
        assert set(TEMPLATES.keys()) == {"a", "b", "c", "d"}

    def test_all_templates_have_subject_text_html(self):
        """每个模板都有 subject, text, html"""
        for key, tmpl in TEMPLATES.items():
            assert "subject" in tmpl, f"Template {key} missing subject"
            assert "text" in tmpl, f"Template {key} missing text"
            assert "html" in tmpl, f"Template {key} missing html"

    def test_html_structure(self):
        """HTML 包含基本结构"""
        for v in ["a", "b", "c", "d"]:
            _, html, _, _ = render_promo_email(name="Test", template_variant=v)
            assert "<!DOCTYPE html>" in html, f"Template {v} missing DOCTYPE"
            assert "Danmo Scholar" in html, f"Template {v} missing brand name"
            assert "en-scholar.danmo.tech" in html, f"Template {v} missing URL"

    def test_text_is_plain(self):
        """纯文本版本不包含 HTML 标签"""
        for v in ["a", "b", "c", "d"]:
            _, _, text, _ = render_promo_email(name="Test", template_variant=v)
            assert "<" not in text or "<" in "Unsubscribe:", f"Template {v} text contains HTML"
            assert "Danmo Scholar" in text, f"Template {v} text missing brand name"

    def test_all_cta_links_use_ref_param(self):
        """所有 CTA 链接带 ref 参数用于追踪"""
        for v in ["a", "b", "c", "d"]:
            _, html, text, _ = render_promo_email(name="Test", template_variant=v)
            ref = f"ref=email_{v}"
            assert ref in html, f"Template {v} HTML missing ref param"
            assert ref in text, f"Template {v} text missing ref param"


# ==================== 5. 各模板独特内容 ====================

class TestTemplateUniqueContent:
    def test_template_a_has_free_sample_hook(self):
        _, html, text, _ = render_promo_email(
            name="Test", template_variant="a",
            research_topic="machine learning",
        )
        assert "free sample" in html.lower() or "free sample" in text.lower()
        assert "machine learning" in html

    def test_template_b_is_short(self):
        _, html, text, _ = render_promo_email(name="Test", template_variant="b")
        # 模板 B 短小精悍，文本应较短
        assert len(text) < len(TEMPLATES["a"]["text"].render(
            name="Test", first_name="Test", university="",
            research_topic="test", unsubscribe_url=""
        ))

    def test_template_c_has_checkmarks(self):
        _, html, _, _ = render_promo_email(name="Test", template_variant="c")
        assert "✅" in html or "100%" in html

    def test_template_d_has_question(self):
        _, html, text, _ = render_promo_email(name="Test", template_variant="d")
        assert "?" in text  # 问题驱动
        assert "10" in html or "10" in text  # "under 10 minutes"


# ==================== 6. 返回值格式 ====================

class TestReturnValue:
    def test_returns_tuple_of_four(self):
        result = render_promo_email(name="Test", template_variant="a")
        assert isinstance(result, tuple)
        assert len(result) == 4

    def test_subject_is_string(self):
        subject, _, _, _ = render_promo_email(name="Test", template_variant="a")
        assert isinstance(subject, str)
        assert len(subject) > 0

    def test_html_is_string(self):
        _, html, _, _ = render_promo_email(name="Test", template_variant="a")
        assert isinstance(html, str)
        assert len(html) > 100

    def test_text_is_string(self):
        _, _, text, _ = render_promo_email(name="Test", template_variant="a")
        assert isinstance(text, str)
        assert len(text) > 50

    def test_variant_is_single_char(self):
        _, _, _, v = render_promo_email(name="Test", template_variant="b")
        assert v in ("a", "b", "c", "d")
        assert len(v) == 1
