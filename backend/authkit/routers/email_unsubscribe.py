"""
邮件退订 API
"""
import hashlib
import os
import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["email"])

UNSUBSCRIBE_SECRET = os.getenv("UNSUBSCRIBE_SECRET", "danmo-scholar-unsubscribe")


def generate_unsubscribe_token(email: str) -> str:
    """生成退订 token（邮箱 + 密钥的 HMAC）"""
    import hmac
    return hmac.new(
        UNSUBSCRIBE_SECRET.encode(),
        email.lower().encode(),
        hashlib.sha256,
    ).hexdigest()[:16]


def generate_unsubscribe_url(email: str) -> str:
    """生成退订链接"""
    backend_url = os.getenv("BACKEND_URL", "https://scholar.danmo.tech")
    token = generate_unsubscribe_token(email)
    return f"{backend_url}/api/email/unsubscribe?email={email}&token={token}"


def verify_unsubscribe_token(email: str, token: str) -> bool:
    return generate_unsubscribe_token(email) == token


@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe(email: str, token: str, request: Request):
    """退订接口 — 用户点击链接后调用"""
    if not verify_unsubscribe_token(email, token):
        return HTMLResponse("<h3>Invalid unsubscribe link.</h3>", status_code=400)

    _get_db = request.app.state.auth_get_db if hasattr(request.app.state, "auth_get_db") else None
    if not _get_db:
        from authkit.database import get_db as _get_db_func
        _get_db = _get_db_func

    db = next(_get_db())
    try:
        result = db.execute(text("""
            UPDATE email_contacts SET unsubscribed = true
            WHERE email = :email AND (unsubscribed IS NULL OR unsubscribed = false)
            RETURNING name
        """), {"email": email.lower()})
        row = result.fetchone()
        db.commit()

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
        db.close()
