"""
用户调研邮件模板 — 流失用户反馈 + 加微信送积分

变量：
- topic: 用户生成过的综述主题
- wechat_id: 微信号
- qrcode_url: 微信二维码图片 URL
- unsubscribe_url: 退订链接
"""
from jinja2 import Template

SUBJECT = "关于你之前用过的澹墨学术，想请教一个简单的问题"

TEXT_TEMPLATE = Template("""\
同学你好，

我是澹墨学术（Danmo Scholar）的开发者 詹聪聪（微信号：{{ wechat_id }}）。

{% if topic %}
前段时间你用我们的工具生成了关于《{{ topic }}》的综述，但后来就没再继续用了。我特别想知道原因——这对我们改进产品非常重要。
{% else %}
前段时间你花时间用我们的工具生成了综述，但后来就没再继续用了。我特别想知道原因——这对我们改进产品非常重要。
{% endif %}

无论是：

- 生成的综述质量不行（比如逻辑乱、内容不相关）
- 文献不够新，或者DOI验证不方便
- 功能不能满足你的需求
- 价格不合适
- 或者就是单纯觉得"没必要用"……

任何原因，都请你直接告诉我。

如果你愿意花2分钟回复这封邮件（或者加我微信），我会往你的账户里充 4 个积分（价值 19.8 元），作为感谢。
积分可以用来再生成 2 篇综述，或者做 4 份文献对比矩阵。

加微信时请备注"Danmo反馈 + 你的注册邮箱"，我看到后会立刻把积分加上。

我的微信号：{{ wechat_id }}

我只是一个开发者，真心想做出对研究生真正有用的工具。

谢谢。

祝研究顺利，

詹聪聪
微信：{{ wechat_id }}

---
不想再收到此类邮件：{{ unsubscribe_url }}
""")

HTML_TEMPLATE = Template("""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f5f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,'PingFang SC','Microsoft YaHei',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:32px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);">

<!-- Header -->
<tr><td style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);padding:24px 40px;">
  <span style="font-size:22px;color:#ffffff;font-weight:700;">澹墨学术 Danmo Scholar</span>
</td></tr>

<!-- Body -->
<tr><td style="padding:32px 40px;">

  <p style="margin:0 0 16px;font-size:15px;color:#1a1a2e;">同学你好，</p>

  <p style="margin:0 0 16px;font-size:15px;color:#555;line-height:1.6;">
    我是<a href="https://scholar.danmo.tech" style="color:#2563eb;text-decoration:none;">澹墨学术（Danmo Scholar）</a>的开发者&nbsp;詹聪聪（微信号：{{ wechat_id }}）。
  </p>

  {% if topic %}
  <p style="margin:0 0 16px;font-size:15px;color:#555;line-height:1.6;">
    前段时间你用我们的工具生成了关于<strong>《{{ topic }}》</strong>的综述，但后来就没再继续用了。我特别想知道原因——这对我们改进产品非常重要。
  </p>
  {% else %}
  <p style="margin:0 0 16px;font-size:15px;color:#555;line-height:1.6;">
    前段时间你花时间用我们的工具生成了综述，但后来就没再继续用了。我特别想知道原因——这对我们改进产品非常重要。
  </p>
  {% endif %}

  <p style="margin:0 0 8px;font-size:15px;color:#555;line-height:1.6;">无论是：</p>

  <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 16px;">
    <tr><td style="font-size:14px;color:#555;line-height:2;">
      <span style="color:#999;">▸</span> 生成的综述质量不行（比如逻辑乱、内容不相关）<br>
      <span style="color:#999;">▸</span> 文献不够新，或者 DOI 验证不方便<br>
      <span style="color:#999;">▸</span> 功能不能满足你的需求<br>
      <span style="color:#999;">▸</span> 价格不合适<br>
      <span style="color:#999;">▸</span> 或者就是单纯觉得"没必要用"……
    </td></tr>
  </table>

  <p style="margin:0 0 20px;font-size:15px;color:#1a1a2e;line-height:1.6;font-weight:600;">
    任何原因，都请你直接告诉我。
  </p>

  <!-- 感谢积分卡片 -->
  <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
    <tr><td style="background:#f0f5ff;border-radius:8px;padding:20px;">
      <p style="margin:0 0 8px;font-size:15px;color:#1a1a2e;font-weight:600;">🎁 反馈感谢</p>
      <p style="margin:0 0 6px;font-size:14px;color:#555;line-height:1.6;">
        如果你愿意花 2 分钟回复这封邮件（或者加我微信），我会往你的账户里充
        <strong style="color:#2563eb;">4&nbsp;个积分</strong>（价值 ¥19.8），作为感谢。
      </p>
      <p style="margin:0;font-size:13px;color:#888;">
        积分可以用来再生成 2 篇综述，或者做 4 份文献对比矩阵。
      </p>
    </td></tr>
  </table>

  <!-- 微信二维码 -->
  <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 16px;">
    <tr><td align="center" style="background:#fafafa;border-radius:8px;padding:24px;">
      <p style="margin:0 0 12px;font-size:14px;color:#555;">
        加微信时请备注&nbsp;<strong>"Danmo反馈 + 你的注册邮箱"</strong>
      </p>
      {% if qrcode_url %}
      <img src="{{ qrcode_url }}" alt="微信二维码" width="160" height="160"
           style="border-radius:8px;border:1px solid #e5e7eb;display:block;">
      {% endif %}
      <p style="margin:8px 0 0;font-size:13px;color:#888;">微信号：{{ wechat_id }}</p>
    </td></tr>
  </table>

  <p style="margin:0;font-size:14px;color:#999;line-height:1.6;">
    我只是一个开发者，真心想做出对研究生真正有用的工具。
  </p>

</td></tr>

<!-- Footer -->
<tr><td style="padding:24px 40px;background-color:#f8f9fa;border-top:1px solid #e5e7eb;">
  <p style="margin:0 0 4px;font-size:14px;color:#1a1a2e;font-weight:600;">谢谢。祝研究顺利，</p>
  <p style="margin:0 0 4px;font-size:14px;color:#555;">詹聪聪</p>
  <p style="margin:0 0 12px;font-size:13px;color:#888;">微信：{{ wechat_id }}</p>
  <p style="margin:0;font-size:11px;color:#aaa;">
    不想再收到此类邮件？<a href="{{ unsubscribe_url }}" style="color:#aaa;text-decoration:underline;">点击退订</a>
  </p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>
""")


def render_survey_email(
    topic: str = "",
    wechat_id: str = "zhancongc",
    qrcode_url: str = "",
    unsubscribe_url: str = "",
) -> tuple[str, str, str]:
    """渲染调研邮件。返回 (subject, html_content, text_content)。"""
    ctx = dict(
        nickname="同学",
        topic=topic,
        wechat_id=wechat_id,
        qrcode_url=qrcode_url,
        unsubscribe_url=unsubscribe_url,
    )
    return SUBJECT, HTML_TEMPLATE.render(**ctx), TEXT_TEMPLATE.render(**ctx)
