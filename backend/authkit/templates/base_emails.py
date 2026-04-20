"""
通用邮件模板系统
支持自定义品牌信息
"""
from jinja2 import Template
from typing import Optional
import os


class EmailTemplateConfig:
    """邮件模板配置"""

    def __init__(self):
        # 从环境变量读取配置
        self.app_name = os.getenv("AUTH_EMAIL_APP_NAME", "Danmo Scholar")
        self.app_url = os.getenv("AUTH_EMAIL_APP_URL", "#")
        self.app_url_en = os.getenv("AUTH_EMAIL_APP_URL_EN", "#")
        self.logo_emoji = os.getenv("AUTH_EMAIL_LOGO_EMOJI", "📚")
        self.contact_email = os.getenv("AUTH_EMAIL_CONTACT_EMAIL", "service@danmo.tech")
        self.contact_email_en = os.getenv("AUTH_EMAIL_CONTACT_EMAIL_EN", "service@danmo.tech")
        self.primary_color = os.getenv("AUTH_EMAIL_PRIMARY_COLOR", "#C0392B")
        self.secondary_color = os.getenv("AUTH_EMAIL_SECONDARY_COLOR", "#8E1A1A")

    @property
    def gradient(self):
        return f"linear-gradient(135deg, {self.primary_color} 0%, {self.secondary_color} 100%)"


# 全局配置实例
email_config = EmailTemplateConfig()


# 通用验证码邮件模板
VERIFICATION_CODE_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #FFFBF5; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .header { background: #FFFBF5; padding: 40px 30px; text-align: center; border-radius: 12px 12px 0 0; border: 2px solid #e8ecef; border-bottom: none; }
        .header h1 { margin: 10px 0 0 0; font-size: 24px; font-weight: 600; color: #1A1A1A !important; }
        .logo { font-size: 32px; margin-bottom: 10px; }
        .content { background: white; padding: 40px 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); color: #333; border: 2px solid #e8ecef; border-top: none; }
        .greeting { font-size: 16px; margin-bottom: 20px; }
        .code-box { background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%); border: 2px dashed {{ primary_color }}; padding: 25px; text-align: center; margin: 25px 0; border-radius: 8px; }
        .code { font-size: 36px; font-weight: 700; color: {{ primary_color }} !important; letter-spacing: 8px; font-family: 'Courier New', monospace; }
        .expire-notice { color: #666; font-size: 14px; text-align: center; }
        .warning { background: #fff3cd; color: #856404; padding: 15px; border-radius: 6px; font-size: 14px; margin-top: 20px; border-left: 4px solid #ffc107; }
        .code-preview { font-size: 24px; color: {{ primary_color }} !important; letter-spacing: 4px; font-family: 'Courier New', monospace; }
        .footer { text-align: center; margin-top: 30px; color: #999; font-size: 12px; }
        .footer a { color: {{ primary_color }}; text-decoration: none; }
        @media (prefers-color-scheme: dark) {
            body { background: #1a1a1a; }
            .header { background: #1a1a1a; border-color: #333; }
            .header h1 { color: #ffffff !important; }
            .content { background: #2a2a2a; color: #e0e0e0; border-color: #333; }
            .code-box { background: #1a1a1a !important; }
            .code { color: #ffffff !important; }
            .code-preview { color: #ffffff !important; }
            .expire-notice { color: #aaa; }
            .warning { background: #5c4a18; color: #ffecb5; border-left-color: #ffc107; }
            .footer { color: #777; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">{{ logo_emoji }}</div>
            <h1>{{ app_name }}</h1>
        </div>
        <div class="content">
            {% if language == 'en' %}
            <p class="greeting">Hello!</p>
            <p>Your verification code is: <strong class="code-preview">{{ code }}</strong> (valid for {{ expire_minutes }} minutes)</p>
            <p>You are verifying your identity for <strong>{{ purpose }}</strong>.</p>
            {% else %}
            <p class="greeting">您好！</p>
            <p>您的验证码是: <strong class="code-preview">{{ code }}</strong>（有效期 {{ expire_minutes }} 分钟）</p>
            <p>您正在进行 <strong>{{ purpose }}</strong> 操作。</p>
            {% endif %}
            <div class="code-box">
                <div class="code">{{ code }}</div>
            </div>
            {% if language == 'en' %}
            <p class="expire-notice">
                This code expires in <strong>{{ expire_minutes }}</strong> minutes. Please verify promptly.
            </p>
            <div class="warning">
                ⚠️ If you did not request this code, please ignore this email. Your account is safe.
            </div>
            {% else %}
            <p class="expire-notice">
                验证码有效期为 <strong>{{ expire_minutes }}</strong> 分钟，请尽快完成验证。
            </p>
            <div class="warning">
                ⚠️ 如果这不是您的操作，请忽略此邮件，您的账号安全不会受到影响。
            </div>
            {% endif %}
            <div class="footer">
                {% if language == 'en' %}
                <p>This email was sent automatically by <a href="{{ app_url }}">{{ app_name }}</a>. Please do not reply.</p>
                <p>Questions? Contact us at {{ contact_email }}</p>
                {% else %}
                <p>此邮件由 <a href="{{ app_url }}">{{ app_name }}</a> 自动发送，请勿直接回复</p>
                <p>如有疑问，请联系我们：{{ contact_email }}</p>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
""")


# 通用欢迎邮件模板
WELCOME_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #FFFBF5; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .header { background: #FFFBF5; padding: 40px 30px; text-align: center; border-radius: 12px 12px 0 0; border: 2px solid #e8ecef; border-bottom: none; }
        .header h1 { margin: 10px 0 0 0; font-size: 24px; font-weight: 600; color: #1A1A1A !important; }
        .logo { font-size: 32px; margin-bottom: 10px; }
        .content { background: white; padding: 40px 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); color: #333; border: 2px solid #e8ecef; border-top: none; }
        .welcome-text { font-size: 16px; margin-bottom: 20px; }
        .cta-button { display: inline-block; padding: 15px 40px; background: {{ gradient }}; color: #ffffff !important; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; color: #999; font-size: 12px; }
        .footer a { color: {{ primary_color }}; text-decoration: none; }
        @media (prefers-color-scheme: dark) {
            body { background: #1a1a1a; }
            .header { background: #1a1a1a; border-color: #333; }
            .header h1 { color: #ffffff !important; }
            .content { background: #2a2a2a; color: #e0e0e0; border-color: #333; }
            .footer { color: #777; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎉</div>
            <h1>欢迎注册 {{ app_name }}！</h1>
        </div>
        <div class="content">
            <p class="welcome-text">
                {% if language == 'en' %}
                {% if nickname %}
                Dear <strong>{{ nickname }}</strong>,
                {% else %}
                Hello!
                {% endif %}
                {% else %}
                {% if nickname %}
                亲爱的 <strong>{{ nickname }}</strong>，
                {% else %}
                您好！
                {% endif %}
                {% endif %}
            </p>
            {% if language == 'en' %}
            <p>Thank you for signing up! Your account has been created successfully.</p>
            <p>You can now start using our services.</p>

            <div style="text-align: center;">
                <a href="{{ app_url }}" class="cta-button">Get Started</a>
            </div>

            <p style="color: #666; font-size: 14px; margin-top: 25px;">
                If you have any questions, feel free to contact us.
            </p>
            {% else %}
            <p>感谢您注册！您的账号已成功创建。</p>
            <p>现在您可以开始使用我们的服务了。</p>

            <div style="text-align: center;">
                <a href="{{ app_url }}" class="cta-button">开始使用</a>
            </div>

            <p style="color: #666; font-size: 14px; margin-top: 25px;">
                如有任何问题，欢迎随时联系我们。
            </p>
            {% endif %}

            <div class="footer">
                {% if language == 'en' %}
                <p>This email was sent automatically by <a href="{{ app_url }}">{{ app_name }}</a>. Please do not reply.</p>
                <p>Contact us: {{ contact_email }}</p>
                {% else %}
                <p>此邮件由 <a href="{{ app_url }}">{{ app_name }}</a> 自动发送，请勿直接回复</p>
                <p>联系我们：{{ contact_email }}</p>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
""")


def _get_contact_email(language: str = "zh") -> str:
    """根据语言返回联系邮箱"""
    if language == "en":
        return email_config.contact_email_en
    return email_config.contact_email


def _get_app_url(language: str = "zh") -> str:
    """根据语言返回站点链接"""
    if language == "en":
        return email_config.app_url_en or email_config.app_url
    return email_config.app_url


def get_verification_code_email(code: str, purpose: str = "登录", expire_minutes: int = 10, language: str = "zh") -> str:
    """获取验证码邮件 HTML"""
    return VERIFICATION_CODE_TEMPLATE.render(
        code=code,
        purpose=purpose,
        expire_minutes=expire_minutes,
        language=language,
        contact_email=_get_contact_email(language),
        app_name=email_config.app_name,
        app_url=_get_app_url(language),
        logo_emoji=email_config.logo_emoji,
        primary_color=email_config.primary_color,
    )


def get_welcome_email(nickname: Optional[str] = None, language: str = "zh") -> str:
    """获取欢迎邮件 HTML"""
    return WELCOME_TEMPLATE.render(
        nickname=nickname or ("User" if language == "en" else "用户"),
        language=language,
        contact_email=_get_contact_email(language),
        app_name=email_config.app_name,
        app_url=_get_app_url(language),
        logo_emoji=email_config.logo_emoji,
        primary_color=email_config.primary_color,
        gradient=email_config.gradient,
    )
