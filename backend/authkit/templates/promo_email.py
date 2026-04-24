"""
推广邮件 HTML 模板

基于 Jinja2 渲染，支持个性化变量：
- name: 收件人姓名
- university: 大学名称（从邮箱域名自动推断，可选）
"""
from jinja2 import Template

_SUBJECT = "Avoid Fake Citations & Build Your Literature Matrix in Minutes"

_HTML_TEMPLATE = Template("""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f5f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:32px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);">

<!-- Header -->
<tr><td style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);padding:32px 40px;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td><span style="font-size:24px;color:#ffffff;font-weight:700;letter-spacing:0.5px;">Danmo Scholar</span></td>
      <td align="right"><span style="font-size:13px;color:rgba(255,255,255,0.7);">Your Academic Writing Assistant</span></td>
    </tr>
  </table>
</td></tr>

<!-- Body -->
<tr><td style="padding:40px;">
  <p style="margin:0 0 6px;font-size:16px;color:#1a1a2e;">Dear {{ name }},</p>
  <p style="margin:0 0 20px;font-size:15px;color:#555;line-height:1.6;">I hope this email finds you well.</p>

  <p style="margin:0 0 20px;font-size:15px;color:#555;line-height:1.6;">
    {% if university %}As a researcher at {{ university }}, I know how draining writing literature reviews can be{% else %}If you've ever spent days writing a literature review, you know how draining it can be{% endif %} — especially when you're juggling research projects, data analysis, and strict academic standards.
  </p>

  <p style="margin:0 0 20px;font-size:15px;color:#555;line-height:1.6;">
    ChatGPT and other generic AI tools often produce <strong style="color:#dc2626;">fake citations or invalid DOIs</strong>, which can put your academic work at risk. That's why we built <a href="https://en-scholar.danmo.tech/" style="color:#2563eb;text-decoration:none;font-weight:600;">Danmo Scholar</a> — a tool specifically designed for researchers, to make literature review writing faster, more reliable, and stress-free.
  </p>

  <p style="margin:0 0 12px;font-size:15px;color:#1a1a2e;font-weight:600;">Here's how Danmo Scholar can support your research:</p>

  <!-- Feature 1 -->
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
    <tr>
      <td width="28" valign="top" style="font-size:16px;">✅</td>
      <td style="font-size:15px;color:#555;line-height:1.6;">
        <strong style="color:#1a1a2e;">100% Real Citations with DOI Verification</strong><br>
        No more fake references or invalid DOIs — every citation is sourced from authoritative academic databases and fully verifiable.
      </td>
    </tr>
  </table>

  <!-- Feature 2 -->
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
    <tr>
      <td width="28" valign="top" style="font-size:16px;">✅</td>
      <td style="font-size:15px;color:#555;line-height:1.6;">
        <strong style="color:#1a1a2e;">One-Click Literature Review &amp; Matrix</strong><br>
        Skip hours of sorting papers and building comparison tables — our tool auto-generates a structured review AND a literature matrix (methods, findings, and conclusions side-by-side), aligned with academic standards in your field.
      </td>
    </tr>
  </table>

  <!-- Feature 3 -->
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
    <tr>
      <td width="28" valign="top" style="font-size:16px;">✅</td>
      <td style="font-size:15px;color:#555;line-height:1.6;">
        <strong style="color:#1a1a2e;">Pay-as-You-Go, No Monthly Subscription</strong><br>
        You only pay for what you use — no hidden fees, no mandatory monthly charges.
      </td>
    </tr>
  </table>

  <p style="margin:0 0 24px;font-size:15px;color:#555;line-height:1.6;">
    Whether you're working on a literature review for your PhD thesis, master's dissertation, or research project, Danmo Scholar helps you focus on your research, not the tedious parts of writing.
  </p>

  <!-- CTA -->
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:20px;">
    <tr><td align="center">
      <a href="https://en-scholar.danmo.tech/" style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#ffffff;font-size:16px;font-weight:600;text-decoration:none;border-radius:8px;">Try Danmo Scholar Now →</a>
    </td></tr>
  </table>

  <p style="margin:0 0 4px;font-size:15px;color:#555;line-height:1.6;">
    If you have any questions, feel free to reply to this email. We're here to help.
  </p>
</td></tr>

<!-- Footer -->
<tr><td style="padding:24px 40px;background-color:#f8f9fa;border-top:1px solid #e5e7eb;">
  <p style="margin:0 0 4px;font-size:14px;color:#1a1a2e;font-weight:600;">Best regards,<br>Danmo Tech Team</p>
  <p style="margin:0 0 4px;font-size:13px;color:#888;">Danmo Scholar | Your Trusted Academic Writing Assistant</p>
  <p style="margin:0 0 12px;font-size:13px;"><a href="https://en-scholar.danmo.tech/" style="color:#2563eb;text-decoration:none;">https://en-scholar.danmo.tech/</a></p>
  <p style="margin:0;font-size:11px;color:#aaa;line-height:1.5;">
    Unsubscribe: <a href="{{ unsubscribe_url }}" style="color:#aaa;text-decoration:underline;">Click here to unsubscribe</a> from promotional emails.
  </p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>
""")

_TEXT_TEMPLATE = Template("""\
Dear {{ name }},

I hope this email finds you well.

{% if university %}As a researcher at {{ university }}, I know how draining writing literature reviews can be{% else %}If you've ever spent days writing a literature review, you know how draining it can be{% endif %} — especially when you're juggling research projects, data analysis, and strict academic standards.

ChatGPT and other generic AI tools often produce fake citations or invalid DOIs, which can put your academic work at risk. That's why we built Danmo Scholar (https://en-scholar.danmo.tech/) — a tool specifically designed for researchers, to make literature review writing faster, more reliable, and stress-free.

Here's how Danmo Scholar can support your research:
- 100% Real Citations with DOI Verification: Every citation is sourced from authoritative databases and fully verifiable.
- One-Click Literature Review & Matrix: Auto-generate a structured review AND a literature matrix.
- Pay-as-You-Go, No Monthly Subscription: You only pay for what you use.

Whether you're working on a literature review for your PhD thesis, master's dissertation, or research project, Danmo Scholar helps you focus on your research, not the tedious parts of writing.

Try it now: https://en-scholar.danmo.tech/

If you have any questions, feel free to reply to this email.

Best regards,
Danmo Tech Team
Danmo Scholar | Your Trusted Academic Writing Assistant
https://en-scholar.danmo.tech/

---
Unsubscribe: {{ unsubscribe_url }}
""")


def render_promo_email(
    name: str,
    university: str = "",
    unsubscribe_url: str = "",
) -> tuple[str, str, str]:
    """
    渲染推广邮件。

    Returns:
        (subject, html_content, text_content)
    """
    ctx = dict(
        name=name,
        university=university,
        unsubscribe_url=unsubscribe_url,
    )
    return _SUBJECT, _HTML_TEMPLATE.render(**ctx), _TEXT_TEMPLATE.render(**ctx)
