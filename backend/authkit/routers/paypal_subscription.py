"""
PayPal Subscription API Router
Handles PayPal payment integration for international markets
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..models.payment import Subscription, PaymentLog
from ..models.schemas import UserResponse
from ..services.paypal_service import get_paypal_service, PAYPAL_PRICING
from ..core.security import decode_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/paypal", tags=["PayPal Payment"])

security = HTTPBearer()

# Database dependency
_default_get_db = None


def get_db():
    global _default_get_db
    if _default_get_db is not None:
        yield from _default_get_db()
        return
    raise NotImplementedError("Please implement set_get_db() function")


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
    return UserResponse.from_orm(user)


class PayPalSubscriptionCreate(BaseModel):
    plan_type: str


class PayPalUnlockCreate(BaseModel):
    record_id: int


class PayPalCaptureRequest(BaseModel):
    order_id: str


class PayPalPaymentResponse(BaseModel):
    order_no: str
    paypal_order_id: str
    approval_link: str
    amount: float
    currency: str


@router.get("/plans")
def get_paypal_plans():
    """Get PayPal pricing plans"""
    return {"plans": PAYPAL_PRICING}


@router.get("/config")
def get_paypal_config():
    """Get PayPal client config for frontend SDK"""
    import os
    return {
        "client_id": os.getenv("PAYPAL_CLIENT_ID", ""),
        "sandbox": os.getenv("PAYPAL_SANDBOX", "true").lower() == "true",
    }


@router.post("/create", response_model=PayPalPaymentResponse)
def create_paypal_subscription(
    data: PayPalSubscriptionCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create PayPal checkout session"""
    user_id = current_user.id

    # Get plan details
    plan = PAYPAL_PRICING.get(data.plan_type)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan type")

    # Generate order number
    order_no = f"PP{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

    # Create subscription record
    subscription = Subscription(
        user_id=user_id,
        order_no=order_no,
        plan_type=data.plan_type,
        amount=plan["price"],
        status="pending",
        payment_method="paypal",
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    # Log creation
    log = PaymentLog(
        subscription_id=subscription.id,
        user_id=user_id,
        action="paypal_create",
        request_data=f"plan_type={data.plan_type}, amount={plan['price']} USD",
    )
    db.add(log)
    db.commit()

    try:
        import os

        paypal = get_paypal_service()
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3006")

        # Create PayPal order
        order_data = paypal.create_order(
            amount=plan["price"],
            currency=plan["currency"],
            description=f"AutoOverview {plan['name']}",
            custom_id=order_no,
            return_url=f"{frontend_url}/?payment_success=1&order_no={order_no}",
            cancel_url=f"{frontend_url}/?payment_cancelled=1",
        )

        # Store PayPal order ID in subscription metadata
        subscription.set_meta("paypal_order_id", order_data["order_id"])
        db.commit()

        # Log success
        log = PaymentLog(
            subscription_id=subscription.id,
            user_id=user_id,
            action="paypal_create_success",
            response_data=f"paypal_order_id={order_data['order_id']}",
        )
        db.add(log)
        db.commit()

        return PayPalPaymentResponse(
            order_no=order_no,
            paypal_order_id=order_data["order_id"],
            approval_link=order_data["approval_link"],
            amount=plan["price"],
            currency=plan["currency"],
        )

    except Exception as e:
        logger.error(f"Failed to create PayPal checkout: {e}")
        log = PaymentLog(
            subscription_id=subscription.id,
            user_id=user_id,
            action="paypal_create_failed",
            response_data=str(e),
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to create payment session")


@router.post("/capture")
def capture_paypal_order(
    data: PayPalCaptureRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Capture PayPal order after user approval"""
    paypal_order_id = data.order_id

    # Find subscription by PayPal order ID
    from ..models import User

    subscription = None
    all_subs = db.query(Subscription).all()
    for sub in all_subs:
        if sub.get_meta("paypal_order_id") == paypal_order_id:
            subscription = sub
            break

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if subscription.status == "paid":
        return {"status": "already_paid", "order_no": subscription.order_no}

    try:
        paypal = get_paypal_service()

        # Capture the order
        capture_data = paypal.capture_order(paypal_order_id)

        # Check if capture was successful
        status = capture_data.get("status", "")
        if status not in ("COMPLETED", "APPROVED"):
            # Try to get order status to verify
            order_data = paypal.get_order(paypal_order_id)
            if order_data and order_data.get("status") not in ("COMPLETED", "APPROVED"):
                raise HTTPException(status_code=400, detail="Payment not completed")

        # Update subscription
        subscription.status = "paid"
        subscription.payment_method = "paypal"
        subscription.payment_time = datetime.now()
        subscription.trade_no = paypal_order_id

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
                    logger.info(f"[PayPal] Unlocked record {record_id} for user {subscription.user_id}")
        else:
            # Add credits to user for subscription plans
            user = db.query(User).filter(User.id == subscription.user_id).first()
            if user:
                plan = PAYPAL_PRICING.get(subscription.plan_type, {})
                credits_to_add = plan.get("credits", 1)
                current_credits = user.get_meta("review_credits", 0)
                user.set_meta("review_credits", current_credits + credits_to_add)
                user.set_meta("has_purchased", True)
                logger.info(f"[PayPal] Added {credits_to_add} credits to user {user.id}")

        db.commit()

        # Log success
        log = PaymentLog(
            subscription_id=subscription.id,
            user_id=subscription.user_id,
            action="paypal_capture_success",
            response_data=f"status={status}",
        )
        db.add(log)
        db.commit()

        return {
            "status": "paid",
            "order_no": subscription.order_no,
            "payment_time": subscription.payment_time.isoformat() if subscription.payment_time else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to capture PayPal order: {e}")
        log = PaymentLog(
            subscription_id=subscription.id,
            user_id=subscription.user_id,
            action="paypal_capture_failed",
            response_data=str(e),
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to capture payment")


@router.post("/webhook")
async def paypal_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle PayPal webhook notifications
    """
    import os
    from ..models import User

    paypal = get_paypal_service()
    payload = await request.body()

    # Get webhook headers
    transmission_id = request.headers.get("Paypal-Transmission-Id", "")
    transmission_time = request.headers.get("Paypal-Transmission-Time", "")
    transmission_sig = request.headers.get("Paypal-Transmission-Sig", "")
    cert_url = request.headers.get("Paypal-Cert-Url", "")
    auth_algo = request.headers.get("Paypal-Auth-Algo", "")

    # Verify webhook signature
    if not paypal.verify_webhook(payload, transmission_id, transmission_time,
                                   transmission_sig, cert_url, auth_algo):
        logger.warning("[PayPal] Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        import json
        data = json.loads(payload)
        event_type = data.get("event_type")
        resource = data.get("resource", {})

        logger.info(f"[PayPal] Webhook received: {event_type}")

        # Handle payment capture completed event
        if event_type == "CHECKOUT.ORDER.COMPLETED":
            # Get the order ID from the resource
            paypal_order_id = resource.get("id", "")

            # Find subscription by PayPal order ID
            subscription = None
            all_subs = db.query(Subscription).all()
            for sub in all_subs:
                if sub.get_meta("paypal_order_id") == paypal_order_id:
                    subscription = sub
                    break

            if not subscription:
                logger.warning(f"[PayPal] Subscription not found for PayPal order: {paypal_order_id}")
                raise HTTPException(status_code=404, detail="Subscription not found")

            if subscription.status != "paid":
                subscription.status = "paid"
                subscription.payment_method = "paypal"
                subscription.payment_time = datetime.now()
                subscription.trade_no = paypal_order_id

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
                            logger.info(f"[PayPal] Unlocked record {record_id} for user {subscription.user_id}")
                else:
                    # Add credits to user for subscription plans
                    user = db.query(User).filter(User.id == subscription.user_id).first()
                    if user:
                        plan = PAYPAL_PRICING.get(subscription.plan_type, {})
                        credits_to_add = plan.get("credits", 1)
                        current_credits = user.get_meta("review_credits", 0)
                        user.set_meta("review_credits", current_credits + credits_to_add)
                        user.set_meta("has_purchased", True)
                        logger.info(f"[PayPal] Added {credits_to_add} credits to user {user.id}")

                db.commit()
                logger.info(f"[PayPal] Activated subscription {subscription.order_no} via webhook")

        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PayPal] Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.get("/query/{order_no}")
def query_paypal_subscription(
    order_no: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Query PayPal subscription status"""
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


@router.post("/unlock", response_model=PayPalPaymentResponse)
def create_paypal_unlock(
    data: PayPalUnlockCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create PayPal unlock session for single review export"""
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
        return PayPalPaymentResponse(
            order_no="",
            paypal_order_id="",
            approval_link="",
            amount=0,
            currency="USD",
        )

    # Get unlock plan details
    plan = PAYPAL_PRICING.get("unlock")
    if not plan:
        raise HTTPException(status_code=500, detail="Unlock plan not configured")

    # Generate order number
    order_no = f"PP{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

    # Create subscription record for unlock
    subscription = Subscription(
        user_id=user_id,
        order_no=order_no,
        plan_type="unlock",
        amount=plan["price"],
        status="pending",
        payment_method="paypal",
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
        action="paypal_unlock_create",
        request_data=f"record_id={record_id}, amount={plan['price']} USD",
    )
    db.add(log)
    db.commit()

    try:
        import os

        paypal = get_paypal_service()
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3006")

        # Create PayPal order
        order_data = paypal.create_order(
            amount=plan["price"],
            currency=plan["currency"],
            description=f"AutoOverview {plan['name']}",
            custom_id=order_no,
            return_url=f"{frontend_url}/?payment_success=1&order_no={order_no}",
            cancel_url=f"{frontend_url}/?payment_cancelled=1",
        )

        # Store PayPal order ID in subscription metadata
        subscription.set_meta("paypal_order_id", order_data["order_id"])
        db.commit()

        # Log success
        log = PaymentLog(
            subscription_id=subscription.id,
            user_id=user_id,
            action="paypal_unlock_create_success",
            response_data=f"paypal_order_id={order_data['order_id']}",
        )
        db.add(log)
        db.commit()

        return PayPalPaymentResponse(
            order_no=order_no,
            paypal_order_id=order_data["order_id"],
            approval_link=order_data["approval_link"],
            amount=plan["price"],
            currency=plan["currency"],
        )

    except Exception as e:
        logger.error(f"Failed to create PayPal unlock checkout: {e}")
        log = PaymentLog(
            subscription_id=subscription.id,
            user_id=user_id,
            action="paypal_unlock_create_failed",
            response_data=str(e),
        )
        db.add(log)
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to create unlock session")
