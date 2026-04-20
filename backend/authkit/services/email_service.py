"""
邮件服务 - 使用通用模板系统
"""
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from ..core.config import config
from ..templates.base_emails import (
    get_verification_code_email,
    get_welcome_email,
)

logger = logging.getLogger(__name__)

PAYMENT_NOTIFY_EMAIL = os.getenv("PAYMENT_NOTIFY_EMAIL", "")


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
            logger.error("发送邮件失败: to=%s, error=%s", to_email, e, exc_info=True)
            return False

    def send_verification_code(
        self,
        to_email: str,
        code: str,
        purpose: str = "login",
        language: str = "zh"
    ) -> bool:
        """
        发送验证码邮件（使用通用模板）

        Args:
            to_email: 收件人邮箱
            code: 验证码
            purpose: 用途（登录/注册/重置密码）
            language: 语言（zh/en）

        Returns:
            bool: 是否发送成功
        """
        if language == "en":
            purpose_map = {
                "login": "Sign In",
                "register": "Sign Up",
                "reset_password": "Reset Password"
            }
            purpose_text = purpose_map.get(purpose, purpose)
            subject = f"Verification Code - {purpose_text}"
            text_content = f"""
Your verification code is: {code}

This code expires in {config.VERIFICATION_CODE_EXPIRE_MINUTES} minutes.

If you did not request this code, please ignore this email.
"""
        else:
            purpose_map = {
                "login": "登录",
                "register": "注册",
                "reset_password": "重置密码"
            }
            purpose_text = purpose_map.get(purpose, purpose)
            subject = f"验证码 - {purpose_text}"
            text_content = f"""
您的验证码是：{code}

验证码有效期为 {config.VERIFICATION_CODE_EXPIRE_MINUTES} 分钟。

如果这不是您的操作，请忽略此邮件。
"""

        # 使用通用模板
        html_content = get_verification_code_email(
            code=code,
            purpose=purpose_text,
            expire_minutes=config.VERIFICATION_CODE_EXPIRE_MINUTES,
            language=language
        )

        return self.send_email(to_email, subject, html_content, text_content)

    def send_welcome_email(self, to_email: str, nickname: Optional[str] = None, language: str = "zh") -> bool:
        """
        发送欢迎邮件（使用通用模板）

        Args:
            to_email: 收件人邮箱
            nickname: 昵称
            language: 语言 (zh/en)

        Returns:
            bool: 是否发送成功
        """
        if language == "en":
            subject = "Welcome to Danmo Scholar!"
            text_content = f"""
{'Dear ' + (nickname or 'User') + ',' if nickname else 'Hello!'}

Thank you for signing up! Your account has been created successfully.

You can now start using our services.

If you have any questions, feel free to contact us.
"""
        else:
            subject = "欢迎注册！"
            text_content = f"""
{'亲爱的 ' + (nickname or '用户') + '，' if nickname else '您好！'}

欢迎注册！您的账号已成功创建。

现在您可以开始使用我们的服务了。

如有任何问题，欢迎随时联系我们。
"""

        # 使用通用模板
        html_content = get_welcome_email(nickname=nickname, language=language)

        return self.send_email(to_email, subject, html_content, text_content)


def send_payment_notification(subscription=None, user_email: str = "", user_nickname: str = "",
                             refund_credits: int = 0, refund_user_id: int = 0):
    """支付成功或退款时发送通知邮件给管理员"""
    if not PAYMENT_NOTIFY_EMAIL:
        return

    try:
        if refund_credits > 0:
            subject = f"[额度退还] 用户 {refund_user_id} 退还 {refund_credits} 积分"
            html = f"""
            <div style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #e74c3c;">🔙 额度退还</h2>
                <table style="border-collapse: collapse; width: 100%; font-size: 14px;">
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666; width: 120px;">退还积分</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{refund_credits}</strong></td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">用户ID</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{refund_user_id}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">用户邮箱</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{user_email or 'N/A'}</td></tr>
                    <tr><td style="padding: 8px; color: #666;">用户昵称</td><td style="padding: 8px;">{user_nickname or 'N/A'}</td></tr>
                </table>
            </div>
            """
            email_service.send_email(PAYMENT_NOTIFY_EMAIL, subject, html)
            logger.info(f"[Notify] Refund notification sent: user {refund_user_id}, {refund_credits} credits")
        elif subscription:
            currency = getattr(subscription, 'currency', 'CNY') or 'CNY'
            currency_label = "USD" if currency == "USD" else "CNY"
            currency_symbol = "$" if currency == "USD" else "¥"

            subject = f"[{currency_label} 订单] {subscription.order_no} - {currency_symbol}{subscription.amount}"

            plan_names = {
                "single": "体验包 / Starter",
                "semester": "标准包 / Semester Pro",
                "yearly": "进阶包 / Annual Premium",
                "unlock": "单次解锁 / Unlock",
            }
            plan_name = plan_names.get(subscription.plan_type, subscription.plan_type)
            payment_time = subscription.payment_time.strftime("%Y-%m-%d %H:%M:%S") if subscription.payment_time else "N/A"

            html = f"""
            <div style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">💰 收到新订单</h2>
                <table style="border-collapse: collapse; width: 100%; font-size: 14px;">
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666; width: 120px;">订单号</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{subscription.order_no}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">套餐</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{plan_name}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">金额</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{currency_symbol}{subscription.amount} {currency_label}</strong></td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">支付方式</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{subscription.payment_method or 'N/A'}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">支付时间</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{payment_time}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">用户邮箱</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{user_email or 'N/A'}</td></tr>
                    <tr><td style="padding: 8px; color: #666;">用户昵称</td><td style="padding: 8px;">{user_nickname or 'N/A'}</td></tr>
                </table>
            </div>
            """
            email_service.send_email(PAYMENT_NOTIFY_EMAIL, subject, html)
            logger.info(f"[Notify] Payment notification sent: {subscription.order_no}")
    except Exception as e:
        logger.error(f"[Notify] Failed to send notification: {e}")


# 全局邮件服务实例
email_service = EmailService()
