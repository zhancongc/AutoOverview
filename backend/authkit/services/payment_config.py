"""
支付配置和 Alipay 服务初始化
"""
import os
import logging
import base64

logger = logging.getLogger(__name__)


def _fix_base64_padding(s: str) -> str:
    """修复 base64 字符串的 padding"""
    return s + '=' * ((4 - len(s) % 4) % 4)


def _read_private_key_from_secrets(base_dir: str) -> str | None:
    """从 secrets.txt 读取私钥并格式化为 PKCS#1 格式"""
    secrets_path = os.path.join(base_dir, "secrets.txt")
    if not os.path.exists(secrets_path):
        logger.warning(f"secrets.txt 不存在: {secrets_path}")
        return None
    try:
        with open(secrets_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        logger.info(f"从 secrets.txt 读取到内容，长度: {len(content)}")

        # 如果已经是完整的 PEM 格式，直接返回
        if "-----BEGIN" in content:
            logger.info("私钥已经是 PEM 格式")
            return content

        # 否则，添加 PKCS#8 格式标记（支付宝生成的通常是 PKCS#8）
        # 先清理内容
        content = content.replace("\n", "").replace("\r", "").replace(" ", "").strip()

        # 尝试修复 base64 padding
        try:
            content = _fix_base64_padding(content)
            # 测试解码
            base64.b64decode(content)
            logger.info("Base64 padding 修复成功")
        except Exception as e:
            logger.warning(f"Base64 padding 修复可能有问题: {e}，继续尝试")

        # 格式化为 PKCS#8 PEM
        # 每 64 个字符换行
        lines = []
        for i in range(0, len(content), 64):
            lines.append(content[i:i+64])
        content_with_newlines = "\n".join(lines)

        pem_content = f"-----BEGIN PRIVATE KEY-----\n{content_with_newlines}\n-----END PRIVATE KEY-----"

        logger.info(f"成功格式化私钥为 PKCS#8 PEM 格式")
        return pem_content
    except Exception as e:
        logger.error(f"读取 secrets.txt 失败: {e}", exc_info=True)
        return None


def _resolve_cert_path(env_value: str | None, default_name: str, base_dir: str) -> str | None:
    """解析证书路径：环境变量优先，相对路径基于 base_dir 解析"""
    if env_value is None:
        return os.path.join(base_dir, default_name)
    if os.path.isabs(env_value):
        return env_value
    return os.path.join(base_dir, env_value)


def get_payment_config():
    """获取支付配置"""
    # 默认证书路径在 backend 目录下
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # 优先从环境变量读私钥，没有则尝试从 secrets.txt 读取
    app_private_key = os.getenv("ALIPAY_APP_PRIVATE_KEY", "")
    if not app_private_key or app_private_key == "your-alipay-app-private-key":
        app_private_key = _read_private_key_from_secrets(base_dir) or ""
        if app_private_key:
            logger.info("使用 secrets.txt 中的私钥")
        else:
            logger.error("无法获取应用私钥")

    return {
        "alipay_app_id": os.getenv("ALIPAY_APP_ID", ""),
        "alipay_app_private_key": app_private_key,
        "alipay_public_key": os.getenv("ALIPAY_PUBLIC_KEY", ""),
        "alipay_server_url": os.getenv("ALIPAY_SERVER_URL", "https://openapi.alipay.com/gateway.do"),
        # 证书路径配置：环境变量优先，相对路径基于 backend 目录解析
        "alipay_app_cert_path": _resolve_cert_path(
            os.getenv("ALIPAY_APP_CERT_PATH"), "appCertPublicKey_2021006144609789.crt", base_dir
        ),
        "alipay_alipay_cert_path": _resolve_cert_path(
            os.getenv("ALIPAY_ALIPAY_CERT_PATH"), "alipayCertPublicKey_RSA2.crt", base_dir
        ),
        "alipay_root_cert_path": _resolve_cert_path(
            os.getenv("ALIPAY_ROOT_CERT_PATH"), "alipayRootCert.crt", base_dir
        ),
        "is_dev": os.getenv("IS_DEV", "true").lower() == "true",
        "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:3006"),
        "backend_url": os.getenv("BACKEND_URL", "http://localhost:8006"),
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

        # 检查证书文件是否存在
        app_cert = config["alipay_app_cert_path"]
        alipay_cert = config["alipay_alipay_cert_path"]
        root_cert = config["alipay_root_cert_path"]

        use_cert_mode = all([
            app_cert and os.path.exists(app_cert),
            alipay_cert and os.path.exists(alipay_cert),
            root_cert and os.path.exists(root_cert),
        ])

        if use_cert_mode:
            logger.info("[Payment] 生产模式 - 证书模式")
            return AlipayService(
                app_id=config["alipay_app_id"],
                app_private_key=config["alipay_app_private_key"],  # 证书模式也需要私钥来签名
                alipay_public_key=config["alipay_public_key"],
                app_cert_path=app_cert,
                alipay_cert_path=alipay_cert,
                alipay_root_cert_path=root_cert,
                server_url=config["alipay_server_url"],
            )
        else:
            logger.info("[Payment] 生产模式 - 公钥模式")
            return AlipayService(
                app_id=config["alipay_app_id"],
                app_private_key=config["alipay_app_private_key"],
                alipay_public_key=config["alipay_public_key"],
                server_url=config["alipay_server_url"],
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
