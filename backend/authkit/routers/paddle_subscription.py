"""
Paddle Subscription API Router
Handles Paddle payment integration for international markets
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..models.payment import Plan, Subscription, PaymentLog
from ..models.schemas import UserResponse
from ..services.paddle_service import get_paddle_service, PADDLE_PRICING
from ..core.security import decode_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/paddle", tags=["Paddle Payment"])

security = HTTPBearer()

# Database dependency
_default_get_db = None


def get_db():
    global _default_get_db
    if _default_get_db is not None:
        yield from _default_get_db()
        return
    raise NotImplementedError("Please implement set_get_db_paddle() function")


def set_get_db(get_db_func):
    global _default_get_db
    _default_get_db = get_db_func


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> UserResponse:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    from ..models import User
    user = db.query(User).filter(User.id == int(payload.get("sub", 0))).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return UserResponse.from_user(user)


class PaddleSubscriptionCreate(BaseModel):
    plan_type: str


class PaddleUnlockCreate(BaseModel):
    record_id: int


class PaddlePaymentResponse(BaseModel):
    order_no: str
    checkout_url: str
    amount: float
    currency: str


@router.get("/plans")
def get_paddle_plans(db: Session = Depends(get_db)):
    """Get Paddle pricing plans from database"""
    from ..models.payment import get_plans_from_db
    plans = get_plans_from_db(db)
    return {"plans": plans}


@router.post("/create", response_model=PaddlePaymentResponse)
def create_paddle_subscription(
    data: PaddleSubscriptionCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create Paddle checkout session"""
    user_id = current_user.id

    # Get plan details from database, fallback to hardcoded
    plan_record = db.query(Plan).filter_by(type=data.plan_type, is_active=True).first()
    if plan_record:
        plan = {
            "name": plan_record.name_en or plan_record.name,
            "price": plan_record.price_usd or plan_record.price,
            "credits": plan_record.credits,
            "currency": "USD",
        }
    else:
        plan = PADDLE_PRICING.get(data.plan_type)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan type")

    # Generate order number
    order_no = f"PD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

    # Create subscription record
    subscription = Subscription(
        user_id=user_id,
        order_no=order_no,
        plan_type=data.plan_type,
        amount=plan["price"],
        currency="USD",
        status="pending",
        payment_method="paddle",
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    # Log creation
    log = PaymentLog(
        subscription_id=subscription.id,
        user_id=user_id,
        action="paddle_create",
        request_data=f"plan_type={data.plan_type}, amount={plan['price']} USD",
    )
    db.add(log)
    db.commit()

    try:
        import os

        paddle = get_paddle_service()

        # Create price
        price_id = paddle.create_price(plan["price"], plan["currency"])

        # Create checkout link
        success_url = os.getenv("EN_FRONTEND_URL") or os.getenv("FRONTEND_URL", "http://localhost:3006")
        checkout_url = paddle.create_checkout_link(
            price_id=price_id,
            customer_email=current_user.email,
            custom_data={
                "order_no": order_no,
                "user_id": str(user_id),
                "plan_type": data.plan_type,
            },
            success_url=f"{success_url}/profile?payment=success",
        )

        # Log success
        log = PaymentLog(
            subscription_id=subscription.id,
            user_id=user_id,
            action="paddle_create_success",
            response_data=f"checkout_url={checkout_url[:100]}...",
        )
        db.add(log)
        db.commit()

        return PaddlePaymentResponse(
            order_no=order_no,
            checkout_url=checkout_url,
            amount=plan["price"],
            currency=plan["currency"],
        )

    except Exception as e:
        logger.error(f"Failed to create Paddle checkout: {e}")
        log = PaymentLog(
            subscription_id=subscription.id,
            user_id=user_id,
            action="paddle_create_failed",
            response_data=str(e),
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to create payment session")


@router.post("/webhook")
async def paddle_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Paddle webhook notifications
    """
    import os

    paddle = get_paddle_service()
    payload = await request.body()
    signature = request.headers.get("Paddle-Signature", "")

    # Verify webhook signature
    if not paddle.verify_webhook(payload, signature):
        logger.warning("[Paddle] Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        import json
        data = json.loads(payload)
        event_type = data.get("event_type")
        event_data = data.get("data", {})

        logger.info(f"[Paddle] Webhook received: {event_type}")

        # Handle payment.success event
        if event_type == "payment.success":
            custom_data = event_data.get("custom_data", {})
            order_no = custom_data.get("order_no")

            if not order_no:
                logger.warning("[Paddle] Webhook missing order_no")
                raise HTTPException(status_code=400, detail="Missing order_no")

            # Find and activate subscription
            subscription = db.query(Subscription).filter(
                Subscription.order_no == order_no
            ).first()

            if not subscription:
                logger.warning(f"[Paddle] Subscription not found: {order_no}")
                raise HTTPException(status_code=404, detail="Subscription not found")

            if subscription.status != "paid":
                subscription.status = "paid"
                subscription.payment_method = "paddle"
                subscription.payment_time = datetime.now()
                subscription.trade_no = event_data.get("transaction_id", "")

                # Handle unlock vs subscription plans
                if subscription.plan_type == "unlock":
                    # Unlock specific review record
                    record_id = subscription.get_meta("record_id")
                    if record_id:
                        from models import ReviewRecord
                        record = db.query(ReviewRecord).filter(
                            ReviewRecord.id == int(record_id),
                            ReviewRecord.user_id == subscription.user_id
                        ).first()
                        if record:
                            record.is_paid = True
                            logger.info(f"[Paddle] Unlocked record {record_id} for user {subscription.user_id}")
                        else:
                            logger.warning(f"[Paddle] Record {record_id} not found for unlock")
                else:
                    # Add credits to user for subscription plans
                    from ..models import User
                    user = db.query(User).filter(User.id == subscription.user_id).first()
                    if user:
                        # 从数据库读取 credits
                        plan_rec = db.query(Plan).filter_by(type=subscription.plan_type, is_active=True).first()
                        if plan_rec:
                            credits_to_add = plan_rec.credits
                        else:
                            plan = PADDLE_PRICING.get(subscription.plan_type, {})
                            credits_to_add = plan.get("credits", 1)
                        current_credits = user.get_meta("review_credits", 0)
                        user.set_meta("review_credits", current_credits + credits_to_add)
                        user.set_meta("has_purchased", True)
                        logger.info(f"[Paddle] Added {credits_to_add} credits to user {user.id}")

                db.commit()

                # 发送订单通知邮件
                from ..services.email_service import send_payment_notification
                user_email = user.email if user else ""
                user_nickname = user.get_meta("nickname", "") if user else ""
                send_payment_notification(sub, user_email, user_nickname)

                logger.info(f"[Paddle] Activated subscription {order_no}")

        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Paddle] Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.get("/query/{order_no}")
def query_paddle_subscription(
    order_no: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Query Paddle subscription status"""
    subscription = db.query(Subscription).filter(
        Subscription.order_no == order_no,
        Subscription.user_id == current_user.id,
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return {
        "status": subscription.status,
        "payment_time": subscription.payment_time.isoformat() if subscription.payment_time else None,
        "amount": subscription.amount,
        "currency": "USD",
    }


@router.post("/unlock", response_model=PaddlePaymentResponse)
def create_paddle_unlock(
    data: PaddleUnlockCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create Paddle unlock session for single review export"""
    user_id = current_user.id
    record_id = data.record_id

    # Verify record exists and belongs to user
    from models import ReviewRecord
    record = db.query(ReviewRecord).filter(
        ReviewRecord.id == record_id,
        ReviewRecord.user_id == user_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Review record not found")

    if record.is_paid:
        return PaddlePaymentResponse(
            order_no="",
            checkout_url="",
            amount=0,
            currency="USD",
        )

    # Get unlock plan details from database
    plan_record = db.query(Plan).filter_by(type="unlock", is_active=True).first()
    if plan_record:
        plan = {"price": plan_record.price_usd or plan_record.price, "currency": "USD"}
    else:
        plan = PADDLE_PRICING.get("unlock")
    if not plan:
        raise HTTPException(status_code=500, detail="Unlock plan not configured")

    # Generate order number
    order_no = f"PD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

    # Create subscription record for unlock
    subscription = Subscription(
        user_id=user_id,
        order_no=order_no,
        plan_type="unlock",
        amount=plan["price"],
        currency="USD",
        status="pending",
        payment_method="paddle",
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    # Store record_id in subscription metadata for webhook processing
    subscription.set_meta("record_id", record_id)
    db.commit()

    # Log creation
    log = PaymentLog(
        subscription_id=subscription.id,
        user_id=user_id,
        action="paddle_unlock_create",
        request_data=f"record_id={record_id}, amount={plan['price']} USD",
    )
    db.add(log)
    db.commit()

    try:
        import os

        paddle = get_paddle_service()

        # Create price
        price_id = paddle.create_price(plan["price"], plan["currency"])

        # Create checkout link
        success_url = os.getenv("EN_FRONTEND_URL") or os.getenv("FRONTEND_URL", "http://localhost:3006")
        checkout_url = paddle.create_checkout_link(
            price_id=price_id,
            customer_email=current_user.email,
            custom_data={
                "order_no": order_no,
                "user_id": str(user_id),
                "plan_type": "unlock",
                "record_id": str(record_id),
            },
            success_url=f"{success_url}/profile?payment=success",
        )

        # Log success
        log = PaymentLog(
            subscription_id=subscription.id,
            user_id=user_id,
            action="paddle_unlock_create_success",
            response_data=f"checkout_url={checkout_url[:100]}...",
        )
        db.add(log)
        db.commit()

        return PaddlePaymentResponse(
            order_no=order_no,
            checkout_url=checkout_url,
            amount=plan["price"],
            currency=plan["currency"],
        )

    except Exception as e:
        logger.error(f"Failed to create Paddle unlock checkout: {e}")
        log = PaymentLog(
            subscription_id=subscription.id,
            user_id=user_id,
            action="paddle_unlock_create_failed",
            response_data=str(e),
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to create unlock session")
