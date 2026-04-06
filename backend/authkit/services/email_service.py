"""
邮件服务 - 使用通用模板系统
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from ..core.config import config
from ..templates.base_emails import (
    get_verification_code_email,
    get_welcome_email,
    get_password_reset_email
)


class EmailService:
    """邮件服务"""

    def __init__(self):
        self.smtp_host = config.SMTP_HOST
        self.smtp_port = config.SMTP_PORT
        self.smtp_user = config.SMTP_USER
        self.smtp_password = config.SMTP_PASSWORD
        self.from_email = config.SMTP_FROM_EMAIL
        self.from_name = config.SMTP_FROM_NAME

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        发送邮件

        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML 内容
            text_content: 纯文本内容（可选）

        Returns:
            bool: 是否发送成功
        """
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            # 添加纯文本内容
            if text_content:
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))

            # 添加 HTML 内容
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # 连接 SMTP 服务器（支持 SSL 端口 465 和 STARTTLS 端口 587）
            if self.smtp_port == 465:
                # 使用 SSL 连接
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                # 使用 STARTTLS 连接
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

            return True

        except Exception as e:
            print(f"发送邮件失败: {e}")
            return False

    def send_verification_code(
        self,
        to_email: str,
        code: str,
        purpose: str = "login"
    ) -> bool:
        """
        发送验证码邮件（使用通用模板）

        Args:
            to_email: 收件人邮箱
            code: 验证码
            purpose: 用途（登录/注册/重置密码）

        Returns:
            bool: 是否发送成功
        """
        purpose_map = {
            "login": "登录",
            "register": "注册",
            "reset_password": "重置密码"
        }
        purpose_text = purpose_map.get(purpose, purpose)

        subject = f"验证码 - {purpose_text}"

        # 使用通用模板
        html_content = get_verification_code_email(
            code=code,
            purpose=purpose_text,
            expire_minutes=config.VERIFICATION_CODE_EXPIRE_MINUTES
        )

        # 纯文本内容
        text_content = f"""
您的验证码是：{code}

验证码有效期为 {config.VERIFICATION_CODE_EXPIRE_MINUTES} 分钟。

如果这不是您的操作，请忽略此邮件。
"""

        return self.send_email(to_email, subject, html_content, text_content)

    def send_welcome_email(self, to_email: str, nickname: Optional[str] = None) -> bool:
        """
        发送欢迎邮件（使用通用模板）

        Args:
            to_email: 收件人邮箱
            nickname: 昵称

        Returns:
            bool: 是否发送成功
        """
        subject = "欢迎注册！"

        # 使用通用模板
        html_content = get_welcome_email(nickname=nickname or "用户")

        # 纯文本内容
        text_content = f"""
{'亲爱的 ' + (nickname or '用户') + '，' if nickname else '您好！'}

欢迎注册！您的账号已成功创建。

现在您可以开始使用我们的服务了。

如有任何问题，欢迎随时联系我们。
"""

        return self.send_email(to_email, subject, html_content, text_content)

    def send_password_reset_email(self, to_email: str, code: str) -> bool:
        """
        发送密码重置邮件（使用通用模板）

        Args:
            to_email: 收件人邮箱
            code: 验证码

        Returns:
            bool: 是否发送成功
        """
        subject = "重置密码"

        # 使用通用模板
        html_content = get_password_reset_email(
            code=code,
            expire_minutes=config.VERIFICATION_CODE_EXPIRE_MINUTES
        )

        # 纯文本内容
        text_content = f"""
您好！

我们收到了您的密码重置请求，验证码如下：{code}

验证码有效期为 {config.VERIFICATION_CODE_EXPIRE_MINUTES} 分钟。

如果这不是您的操作，请忽略此邮件。
"""

        return self.send_email(to_email, subject, html_content, text_content)


# 全局邮件服务实例
email_service = EmailService()
