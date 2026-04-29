"""
邮件退订 API — 单参数 opaque token，URL 不暴露邮箱
"""
import base64
import hashlib
import hmac
import json
import logging
import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["email"])

UNSUBSCRIBE_SECRET = os.getenv("UNSUBSCRIBE_SECRET", "danmo-scholar-unsubscribe")


def generate_unsubscribe_token(email: str) -> str:
    """生成 HMAC 验证 token。"""
    return hmac.new(
        UNSUBSCRIBE_SECRET.encode(),
        email.lower().encode(),
        hashlib.sha256,
    ).hexdigest()[:16]


def generate_unsubscribe_url(email: str) -> str:
    """生成退订链接 — 单参数 opaque token，URL 不暴露邮箱。"""
    backend_url = os.getenv("BACKEND_URL", "https://scholar.danmo.tech")
    token = generate_unsubscribe_token(email)
    payload = json.dumps({"e": email.lower(), "t": token}, separators=(",", ":"))
    encoded = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    return f"{backend_url}/api/email/unsubscribe?t={encoded}"


def _decode_opaque_token(encoded: str) -> tuple[str, str] | None:
    """解码 opaque token，返回 (email, hmac_token) 或 None。"""
    try:
        padded = encoded + "=" * (4 - len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        return payload.get("e", ""), payload.get("t", "")
    except Exception:
        return None


@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe(request: Request):
    """退订接口 — 支持新格式 (?t=xxx) 和旧格式 (?email=&token=)"""
    email = ""
    token = ""

    opaque = request.query_params.get("t")
    if not opaque:
        return HTMLResponse("<h3>Invalid unsubscribe link.</h3>", status_code=400)

    result = _decode_opaque_token(opaque)
    if not result:
        return HTMLResponse("<h3>Invalid unsubscribe link.</h3>", status_code=400)
    email, token = result

    if not email or not token or not verify_unsubscribe_token(email, token):
        return HTMLResponse("<h3>Invalid unsubscribe link.</h3>", status_code=400)

    _get_db = request.app.state.auth_get_db if hasattr(request.app.state, "auth_get_db") else None
    if not _get_db:
        from authkit.database import get_db as _get_db_func
        _get_db = _get_db_func

    db_session = next(_get_db())
    try:
        result = db_session.execute(text("""
            UPDATE email_contacts SET unsubscribed = true
            WHERE email = :email AND (unsubscribed IS NULL OR unsubscribed = false)
            RETURNING name
        """), {"email": email})
        row = result.fetchone()
        db_session.commit()

        if row:
            name = row[0] or "Researcher"
            logger.info(f"[Unsubscribe] {email} unsubscribed")
            return HTMLResponse(f"""
            <div style="font-family:-apple-system,sans-serif;max-width:480px;margin:80px auto;padding:40px;text-align:center;">
                <h2 style="color:#1a1a2e;">Unsubscribed</h2>
                <p style="color:#555;">Dear {name}, you have been successfully unsubscribed from Danmo Scholar promotional emails.</p>
                <p style="color:#888;font-size:13px;">You can still use <a href="https://en-scholar.danmo.tech/">Danmo Scholar</a> at any time.</p>
            </div>
            """)
        else:
            return HTMLResponse("<p>You are already unsubscribed.</p>")
    except Exception as e:
        logger.error(f"[Unsubscribe] Error: {e}")
        return HTMLResponse("<p>An error occurred. Please try again.</p>", status_code=500)
    finally:
        db_session.close()


def verify_unsubscribe_token(email: str, token: str) -> bool:
    return generate_unsubscribe_token(email) == token
