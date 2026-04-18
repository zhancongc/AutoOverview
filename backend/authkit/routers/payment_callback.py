"""
支付同步跳转处理
处理支付宝的同步跳转（用户支付完成后的浏览器跳转）和开发环境模拟支付
"""
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..models.payment import Subscription, PaymentLog, PLAN_DURATION, PLAN_CREDITS
from ..services.payment_config import get_payment_service, get_payment_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payment", tags=["支付回调"])

# 数据库依赖
_default_get_db = None


def get_db():
    global _default_get_db
    if _default_get_db is not None:
        yield from _default_get_db()
        return
    raise NotImplementedError("请在主应用中实现 set_get_db_cb() 函数")


def set_get_db(get_db_func):
    global _default_get_db
    _default_get_db = get_db_func


def _activate_subscription(subscription: Subscription, trade_no: str, db: Session):
    """更新订阅状态并增加额度"""
    if subscription.status == "paid":
        logger.info(f"订单 {subscription.order_no} 已是 paid 状态，跳过")
        return True

    subscription.status = "paid"
    subscription.payment_method = "alipay"
    subscription.payment_time = datetime.now()
    subscription.trade_no = trade_no

    # 增加综述额度（中文站使用 credits_cn）
    from ..models.payment import PLAN_CREDITS, Plan
    from ..models import User
    user = db.query(User).filter(User.id == subscription.user_id).first()
    if user:
        plan_record = db.query(Plan).filter_by(type=subscription.plan_type, is_active=True).first()
        if plan_record:
            credits_to_add = plan_record.credits_cn if plan_record.credits_cn is not None else plan_record.credits
        else:
            credits_to_add = PLAN_CREDITS.get(subscription.plan_type, 1)
        current_credits = user.get_meta("review_credits", 0)
        user.set_meta("review_credits", current_credits + credits_to_add)
        user.set_meta("has_purchased", True)
        # 增加搜索次数（中文站）
        SEARCH_BONUS_CN = {"single": 100, "semester": 300, "yearly": 900}
        bonus = SEARCH_BONUS_CN.get(subscription.plan_type, 0)
        if bonus > 0:
            user.set_meta("search_bonus", user.get_meta("search_bonus", 0) + bonus)
        logger.info(f"✅ 用户 {user.id} 获得 {credits_to_add} 篇付费额度，当前付费 {current_credits + credits_to_add}")

    db.commit()
    return True


@router.get("/return")
async def payment_return(request: Request, db: Session = Depends(get_db)):
    """处理支付宝同步跳转"""
    try:
        params = dict(request.query_params)
        logger.info(f"收到支付跳转: order={params.get('out_trade_no')}, trade_no={params.get('trade_no')}")

        config = get_payment_config()
        out_trade_no = params.get("out_trade_no")
        trade_no = params.get("trade_no", "")

        # 开发环境模拟支付检测
        is_dev_mock = params.get("success") == "true" and trade_no.startswith("DEV")

        if is_dev_mock or config.get("is_dev"):
            logger.info(f"[开发环境] 处理模拟支付: {out_trade_no}")

            subscription = db.query(Subscription).filter(
                Subscription.order_no == out_trade_no
            ).first()

            if subscription:
                _activate_subscription(subscription, trade_no or "DEV_MOCK", db)
                frontend_url = f"{config['frontend_url']}/?payment=success&order={out_trade_no}"
                return RedirectResponse(url=frontend_url, status_code=302)
            else:
                raise HTTPException(status_code=404, detail="订单不存在")

        # 生产环境
        if not out_trade_no:
            raise HTTPException(status_code=400, detail="缺少订单号")

        subscription = db.query(Subscription).filter(
            Subscription.order_no == out_trade_no
        ).first()

        if not subscription:
            raise HTTPException(status_code=404, detail="订单不存在")

        if subscription.status == "pending":
            trade_status = params.get("trade_status")
            if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
                _activate_subscription(subscription, trade_no, db)
            else:
                # 主动查询
                try:
                    alipay = get_payment_service()
                    result = alipay.query_order(out_trade_no)
                    if result and result.get("trade_status") in ("TRADE_SUCCESS", "TRADE_FINISHED"):
                        _activate_subscription(subscription, result.get("trade_no", trade_no), db)
                except Exception as e:
                    logger.error(f"查询支付宝订单失败: {str(e)}")

        db.refresh(subscription)
        if subscription.status == "paid":
            frontend_url = f"{config['frontend_url']}/?payment=success&order={out_trade_no}"
        else:
            frontend_url = f"{config['frontend_url']}/?payment=pending&order={out_trade_no}"

        return RedirectResponse(url=frontend_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理支付跳转失败: {str(e)}")
        config = get_payment_config()
        return RedirectResponse(url=f"{config['frontend_url']}/?payment=error", status_code=302)
