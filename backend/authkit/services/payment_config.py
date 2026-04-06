"""
支付配置和 Alipay 服务初始化
"""
import os
import logging

logger = logging.getLogger(__name__)


def get_payment_config():
    """获取支付配置"""
    return {
        "alipay_app_id": os.getenv("ALIPAY_APP_ID", ""),
        "alipay_app_private_key": os.getenv("ALIPAY_APP_PRIVATE_KEY", ""),
        "alipay_public_key": os.getenv("ALIPAY_PUBLIC_KEY", ""),
        "is_dev": os.getenv("IS_DEV", "true").lower() == "true",
        "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "backend_url": os.getenv("BACKEND_URL", "http://localhost:8000"),
    }


def init_alipay():
    """初始化支付宝服务（延迟导入，避免未安装 SDK 时影响其他功能）"""
    config = get_payment_config()
    is_dev = config["is_dev"]

    if is_dev:
        logger.info("[Payment] 开发模式 - 模拟支付")
        return DevAlipayService()
    else:
        from .alipay import AlipayService
        return AlipayService(
            app_id=config["alipay_app_id"],
            app_private_key=config["alipay_app_private_key"],
            alipay_public_key=config["alipay_public_key"],
        )


# 全局支付服务实例
_payment_service = None


def get_payment_service():
    """获取支付服务实例"""
    global _payment_service
    if _payment_service is None:
        _payment_service = init_alipay()
    return _payment_service


class DevAlipayService:
    """开发环境模拟支付服务"""

    def create_order(self, out_trade_no: str, total_amount: float, subject: str,
                     timeout_express: str = "15m", return_url: str = None,
                     notify_url: str = None) -> str:
        """模拟支付 - 返回包含模拟参数的回调 URL"""
        from urllib.parse import urlencode
        config = get_payment_config()
        final_return_url = return_url or f"{config['backend_url']}/api/payment/return"
        mock_params = {
            "out_trade_no": out_trade_no,
            "trade_no": f"DEV{out_trade_no[-10:]}",
            "total_amount": f"{total_amount:.2f}",
            "buyer_id": "2088102112345678",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "success": "true",
        }
        return f"{final_return_url}?{urlencode(mock_params)}"

    def query_order(self, out_trade_no: str):
        """模拟查询 - 返回成功"""
        return {"trade_status": "TRADE_SUCCESS", "trade_no": f"DEV{out_trade_no[-10:]}"}

    def cancel_order(self, out_trade_no: str) -> bool:
        return True


# 用于 DevAlipayService
from datetime import datetime
