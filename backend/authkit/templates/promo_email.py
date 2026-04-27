"""
推广邮件 HTML 模板 — 4 个 A/B 测试变体

模板 A: 高度个性化 + 免费样例钩子（预期回复率最高）
模板 B: 短小精悍 + 直接价值
模板 C: 痛点 + 信任背书（精炼版）
模板 D: 好奇心 + 问题驱动

基于 Jinja2 渲染，支持个性化变量：
- name: 收件人姓名
- first_name: 名
- university: 大学名称
- research_topic: 研究方向/论文标题
- unsubscribe_url: 退订链接
"""
import random
from jinja2 import Template

# ==================== 模板 A ====================

SUBJECT_A = Template("{{ first_name }}, Leeds PhD文献综述快速方案（真实DOI验证）")

TEXT_A = Template("""\
Dear {{ first_name }},

I came across your recent work on {{ research_topic }} at the University of Leeds — really impressive stuff.

As someone who builds tools for researchers, I know how painful it is when ChatGPT gives fake citations or broken DOIs that could hurt your thesis.

That's why we built Danmo Scholar: it pulls real papers and automatically verifies every single DOI (Crossref + Baidu Scholar) before generating a full structured literature review + comparison matrix.

Would you like me to generate one free sample review based on your current research topic? Just reply "yes" or paste your topic and I'll send it over (no login required).

No strings attached.

Best,
Jade Zhan
Founder, Danmo Scholar
https://en-scholar.danmo.tech/?ref=email_a

---
Unsubscribe: {{ unsubscribe_url }}
""")

HTML_A = Template("""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f5f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:32px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);">

<!-- Header -->
<tr><td style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);padding:24px 40px;">
  <span style="font-size:22px;color:#ffffff;font-weight:700;">Danmo Scholar</span>
</td></tr>

<!-- Body -->
<tr><td style="padding:32px 40px;">
  <p style="margin:0 0 16px;font-size:15px;color:#1a1a2e;">Dear {{ first_name }},</p>

  <p style="margin:0 0 16px;font-size:15px;color:#555;line-height:1.6;">
    I came across your recent work on <strong>{{ research_topic }}</strong> at the University of Leeds — really impressive stuff.
  </p>

  <p style="margin:0 0 16px;font-size:15px;color:#555;line-height:1.6;">
    As someone who builds tools for researchers, I know how painful it is when ChatGPT gives <strong style="color:#dc2626;">fake citations or broken DOIs</strong> that could hurt your thesis.
  </p>

  <p style="margin:0 0 16px;font-size:15px;color:#555;line-height:1.6;">
    That's why we built <a href="https://en-scholar.danmo.tech/?ref=email_a" style="color:#2563eb;text-decoration:none;font-weight:600;">Danmo Scholar</a>: it pulls real papers and automatically verifies every single DOI (Crossref + Baidu Scholar) before generating a full structured literature review + comparison matrix.
  </p>

  <table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">
    <tr><td align="center" style="background:#f0f5ff;border-radius:8px;padding:20px;">
      <p style="margin:0 0 12px;font-size:15px;color:#1a1a2e;font-weight:600;">Want a free sample review on your topic?</p>
      <p style="margin:0;font-size:14px;color:#555;">Just reply <strong>"yes"</strong> or paste your research topic — no login required.</p>
    </td></tr>
  </table>

  <p style="margin:0;font-size:14px;color:#888;">No strings attached.</p>
</td></tr>

<!-- Footer -->
<tr><td style="padding:24px 40px;background-color:#f8f9fa;border-top:1px solid #e5e7eb;">
  <p style="margin:0 0 4px;font-size:14px;color:#1a1a2e;font-weight:600;">Best,<br>Jade Zhan</p>
  <p style="margin:0 0 4px;font-size:13px;color:#888;">Founder, Danmo Scholar</p>
  <p style="margin:0 0 12px;font-size:13px;"><a href="https://en-scholar.danmo.tech/?ref=email_a" style="color:#2563eb;text-decoration:none;">https://en-scholar.danmo.tech/</a></p>
  <p style="margin:0;font-size:11px;color:#aaa;">
    Unsubscribe: <a href="{{ unsubscribe_url }}" style="color:#aaa;text-decoration:underline;">Click here</a>
  </p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>
""")

# ==================== 模板 B ====================

SUBJECT_B = Template("Leeds PhD：10分钟出带真实DOI验证的文献矩阵")

TEXT_B = Template("""\
Hi {{ first_name }},

Quick one for your lit review at Leeds:

Danmo Scholar generates complete literature reviews + side-by-side comparison matrices with 100% verified DOIs (no more fake citations).

Pay only for what you use — no monthly subscription.

Want a free sample on your topic?
Reply with your research question and I'll send it.

Cheers,
Jade Zhan
Danmo Scholar
https://en-scholar.danmo.tech/?ref=email_b

---
Unsubscribe: {{ unsubscribe_url }}
""")

HTML_B = Template("""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f5f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:32px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);">

<tr><td style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);padding:24px 40px;">
  <span style="font-size:22px;color:#ffffff;font-weight:700;">Danmo Scholar</span>
</td></tr>

<tr><td style="padding:32px 40px;">
  <p style="margin:0 0 16px;font-size:15px;color:#1a1a2e;">Hi {{ first_name }},</p>

  <p style="margin:0 0 16px;font-size:15px;color:#555;line-height:1.6;">
    Quick one for your lit review at Leeds:
  </p>

  <p style="margin:0 0 16px;font-size:15px;color:#555;line-height:1.6;">
    <a href="https://en-scholar.danmo.tech/?ref=email_b" style="color:#2563eb;text-decoration:none;font-weight:600;">Danmo Scholar</a> generates complete literature reviews + side-by-side comparison matrices with <strong>100% verified DOIs</strong> (no more fake citations).
  </p>

  <p style="margin:0 0 24px;font-size:15px;color:#555;">Pay only for what you use — no monthly subscription.</p>

  <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 16px;">
    <tr><td align="center">
      <a href="https://en-scholar.danmo.tech/?ref=email_b" style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#ffffff;font-size:16px;font-weight:600;text-decoration:none;border-radius:8px;">Get Your Free Sample →</a>
    </td></tr>
  </table>

  <p style="margin:0;font-size:14px;color:#888;">Reply with your research question and I'll send it.</p>
</td></tr>

<tr><td style="padding:24px 40px;background-color:#f8f9fa;border-top:1px solid #e5e7eb;">
  <p style="margin:0 0 4px;font-size:14px;color:#1a1a2e;">Cheers,<br>Jade Zhan</p>
  <p style="margin:0 0 12px;font-size:13px;"><a href="https://en-scholar.danmo.tech/?ref=email_b" style="color:#2563eb;text-decoration:none;">en-scholar.danmo.tech</a></p>
  <p style="margin:0;font-size:11px;color:#aaa;">
    Unsubscribe: <a href="{{ unsubscribe_url }}" style="color:#aaa;text-decoration:underline;">Click here</a>
  </p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>
""")

# ==================== 模板 C ====================

SUBJECT_C = Template("Avoid fake citations in your PhD lit review (Leeds)")

TEXT_C = Template("""\
Dear {{ first_name }},

I know writing literature reviews while juggling experiments and analysis is exhausting — especially when generic AI tools keep producing invalid DOIs.

We built Danmo Scholar specifically for researchers like you at Leeds:
- 100% real citations with full DOI verification (Crossref + more)
- One-click review + literature comparison matrix
- Pay-as-you-go (only pay for what you actually use)

Would you like to try it free on your topic?

Best regards,
Jade Zhan
https://en-scholar.danmo.tech/?ref=email_c

---
Unsubscribe: {{ unsubscribe_url }}
""")

HTML_C = Template("""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f5f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:32px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);">

<tr><td style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);padding:24px 40px;">
  <span style="font-size:22px;color:#ffffff;font-weight:700;">Danmo Scholar</span>
</td></tr>

<tr><td style="padding:32px 40px;">
  <p style="margin:0 0 16px;font-size:15px;color:#1a1a2e;">Dear {{ first_name }},</p>

  <p style="margin:0 0 20px;font-size:15px;color:#555;line-height:1.6;">
    I know writing literature reviews while juggling experiments and analysis is exhausting — especially when generic AI tools keep producing <strong style="color:#dc2626;">invalid DOIs</strong>.
  </p>

  <p style="margin:0 0 12px;font-size:15px;color:#1a1a2e;font-weight:600;">We built Danmo Scholar specifically for researchers like you at Leeds:</p>

  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:8px;">
    <tr>
      <td width="28" valign="top" style="font-size:16px;">✅</td>
      <td style="font-size:15px;color:#555;line-height:1.6;">
        <strong style="color:#1a1a2e;">100% real citations with full DOI verification</strong> (Crossref + more)
      </td>
    </tr>
  </table>
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:8px;">
    <tr>
      <td width="28" valign="top" style="font-size:16px;">✅</td>
      <td style="font-size:15px;color:#555;line-height:1.6;">
        <strong style="color:#1a1a2e;">One-click review + literature comparison matrix</strong>
      </td>
    </tr>
  </table>
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
    <tr>
      <td width="28" valign="top" style="font-size:16px;">✅</td>
      <td style="font-size:15px;color:#555;line-height:1.6;">
        <strong style="color:#1a1a2e;">Pay-as-you-go</strong> (only pay for what you actually use)
      </td>
    </tr>
  </table>

  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;">
    <tr><td align="center">
      <a href="https://en-scholar.danmo.tech/?ref=email_c" style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#ffffff;font-size:16px;font-weight:600;text-decoration:none;border-radius:8px;">Try Free on Your Topic →</a>
    </td></tr>
  </table>
</td></tr>

<tr><td style="padding:24px 40px;background-color:#f8f9fa;border-top:1px solid #e5e7eb;">
  <p style="margin:0 0 4px;font-size:14px;color:#1a1a2e;">Best regards,<br>Jade Zhan</p>
  <p style="margin:0 0 12px;font-size:13px;"><a href="https://en-scholar.danmo.tech/?ref=email_c" style="color:#2563eb;text-decoration:none;">en-scholar.danmo.tech</a></p>
  <p style="margin:0;font-size:11px;color:#aaa;">
    Unsubscribe: <a href="{{ unsubscribe_url }}" style="color:#aaa;text-decoration:underline;">Click here</a>
  </p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>
""")

# ==================== 模板 D ====================

SUBJECT_D = Template("{{ first_name }}，你的文献综述还在手动做矩阵吗？")

TEXT_D = Template("""\
Hi {{ first_name }},

Quick question: How much time are you currently spending building literature comparison tables for your PhD?

We've helped several researchers cut that down to under 10 minutes with automatically verified citations.

Curious if this would be useful for your work at Leeds?
Reply with your main research topic and I'll generate a free sample for you.

Best,
Jade Zhan
Danmo Scholar
https://en-scholar.danmo.tech/?ref=email_d

---
Unsubscribe: {{ unsubscribe_url }}
""")

HTML_D = Template("""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f5f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:32px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);">

<tr><td style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);padding:24px 40px;">
  <span style="font-size:22px;color:#ffffff;font-weight:700;">Danmo Scholar</span>
</td></tr>

<tr><td style="padding:32px 40px;">
  <p style="margin:0 0 16px;font-size:15px;color:#1a1a2e;">Hi {{ first_name }},</p>

  <p style="margin:0 0 16px;font-size:15px;color:#555;line-height:1.6;">
    Quick question: How much time are you currently spending building literature comparison tables for your PhD?
  </p>

  <p style="margin:0 0 16px;font-size:15px;color:#555;line-height:1.6;">
    We've helped several researchers cut that down to <strong style="color:#2563eb;">under 10 minutes</strong> with automatically verified citations.
  </p>

  <table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">
    <tr><td align="center" style="background:#f0f5ff;border-radius:8px;padding:20px;">
      <p style="margin:0 0 8px;font-size:15px;color:#1a1a2e;">Curious if this would be useful for your work at Leeds?</p>
      <p style="margin:0;font-size:14px;color:#555;">Reply with your main research topic and I'll generate a <strong>free sample</strong> for you.</p>
    </td></tr>
  </table>

  <p style="margin:0;font-size:14px;color:#888;">Or try it yourself: <a href="https://en-scholar.danmo.tech/?ref=email_d" style="color:#2563eb;text-decoration:none;">en-scholar.danmo.tech</a></p>
</td></tr>

<tr><td style="padding:24px 40px;background-color:#f8f9fa;border-top:1px solid #e5e7eb;">
  <p style="margin:0 0 4px;font-size:14px;color:#1a1a2e;">Best,<br>Jade Zhan</p>
  <p style="margin:0 0 12px;font-size:13px;"><a href="https://en-scholar.danmo.tech/?ref=email_d" style="color:#2563eb;text-decoration:none;">Danmo Scholar</a></p>
  <p style="margin:0;font-size:11px;color:#aaa;">
    Unsubscribe: <a href="{{ unsubscribe_url }}" style="color:#aaa;text-decoration:underline;">Click here</a>
  </p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>
""")

# ==================== 注册表 ====================

TEMPLATES = {
    "a": {"subject": SUBJECT_A, "text": TEXT_A, "html": HTML_A},
    "b": {"subject": SUBJECT_B, "text": TEXT_B, "html": HTML_B},
    "c": {"subject": SUBJECT_C, "text": TEXT_C, "html": HTML_C},
    "d": {"subject": SUBJECT_D, "text": TEXT_D, "html": HTML_D},
}


def render_promo_email(
    name: str,
    university: str = "",
    unsubscribe_url: str = "",
    first_name: str = "",
    research_topic: str = "",
    template_variant: str = "",
) -> tuple[str, str, str, str]:
    """
    渲染推广邮件。随机选择模板（除非指定 variant）。

    Returns:
        (subject, html_content, text_content, variant)
    """
    variant = template_variant.lower() if template_variant else random.choice(list(TEMPLATES.keys()))
    if variant not in TEMPLATES:
        variant = "a"
    tmpl = TEMPLATES[variant]

    if not first_name:
        first_name = name.split()[0] if name else "Researcher"
    if not research_topic:
        research_topic = "your research topic"

    ctx = dict(
        name=name or "Researcher",
        first_name=first_name,
        university=university,
        research_topic=research_topic,
        unsubscribe_url=unsubscribe_url,
    )

    subject = tmpl["subject"]
    if isinstance(subject, Template):
        subject = subject.render(**ctx)

    html = tmpl["html"].render(**ctx)
    text = tmpl["text"].render(**ctx)

    return subject, html, text, variant
