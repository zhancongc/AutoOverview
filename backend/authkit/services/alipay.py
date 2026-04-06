"""
支付宝支付服务（生产环境）
使用 alipay-aop-sdk (alipay-sdk-python)
"""
import logging
import traceback
from typing import Optional

logger = logging.getLogger(__name__)


class AlipayService:
    """支付宝支付服务"""

    def __init__(
        self,
        app_id: str,
        app_private_key: str,
        alipay_public_key: str,
        server_url: str = "https://openapi.alipay.com/gateway.do",
        sign_type: str = "RSA2",
    ):
        from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
        from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient

        config = AlipayClientConfig()
        config.server_url = server_url
        config.app_id = app_id
        config.app_private_key = app_private_key
        config.alipay_public_key = alipay_public_key
        config.sign_type = sign_type

        self.client = DefaultAlipayClient(config)
        logger.info(f"支付宝客户端初始化成功，APP_ID: {app_id}")

    def create_order(
        self,
        out_trade_no: str,
        total_amount: float,
        subject: str,
        timeout_express: str = "15m",
        return_url: str = None,
        notify_url: str = None,
    ) -> Optional[str]:
        """创建电脑网站支付订单，返回支付链接"""
        from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
        from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest

        try:
            model = AlipayTradePagePayModel()
            model.out_trade_no = out_trade_no
            model.total_amount = f"{total_amount:.2f}"
            model.subject = subject
            model.product_code = "FAST_INSTANT_TRADE_PAY"
            model.qr_pay_mode = 1
            model.timeout_express = timeout_express

            request = AlipayTradePagePayRequest(biz_model=model)
            if return_url:
                request.return_url = return_url
            if notify_url:
                request.notify_url = notify_url

            pay_url = self.client.page_execute(request, "GET")
            logger.info(f"创建支付订单: {out_trade_no}, 金额: {total_amount}")
            return pay_url

        except Exception as e:
            logger.error(f"创建支付订单异常: {str(e)}")
            traceback.print_exc()
            return None

    def query_order(self, out_trade_no: str) -> Optional[dict]:
        """查询订单支付状态"""
        from alipay.aop.api.domain.AlipayTradeQueryModel import AlipayTradeQueryModel
        from alipay.aop.api.request.AlipayTradeQueryRequest import AlipayTradeQueryRequest
        from alipay.aop.api.response.AlipayTradeQueryResponse import AlipayTradeQueryResponse

        try:
            model = AlipayTradeQueryModel()
            model.out_trade_no = out_trade_no

            request = AlipayTradeQueryRequest(biz_model=model)
            response_content = self.client.execute(request)

            response = AlipayTradeQueryResponse()
            response.parse_response_content(response_content)

            if response.is_success():
                return {
                    "trade_status": response.trade_status,
                    "trade_no": response.trade_no,
                    "total_amount": response.total_amount,
                    "buyer_logon_id": response.buyer_logon_id,
                }
            else:
                logger.warning(f"查询订单失败: {response.sub_msg}")
                return None

        except Exception as e:
            logger.error(f"查询订单异常: {str(e)}")
            return None

    def cancel_order(self, out_trade_no: str) -> bool:
        """取消订单"""
        logger.warning(f"取消订单功能待实现: {out_trade_no}")
        return True
