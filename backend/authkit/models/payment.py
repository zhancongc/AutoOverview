"""
支付相关数据模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional, List

# 使用独立的 Base，由 main.py 通过 engine 创建表
PaymentBase = declarative_base()


class Plan(PaymentBase):
    """套餐价格模型"""
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(32), unique=True, nullable=False, comment="套餐类型: single/semester/yearly/unlock")
    name = Column(String(50), nullable=False, comment="套餐名称（中文）")
    name_en = Column(String(100), nullable=True, comment="套餐名称（英文）")
    price = Column(Float, nullable=False, comment="CNY 价格")
    price_usd = Column(Float, nullable=True, comment="USD 价格")
    original_price = Column(Float, nullable=True, comment="CNY 原价（划线价）")
    original_price_usd = Column(Float, nullable=True, comment="USD 原价")
    credits = Column(Integer, nullable=False, comment="包含的 Credit 点数（英文站）")
    credits_cn = Column(Integer, nullable=True, comment="包含的积分点数（中文站）")
    recommended = Column(Boolean, default=False, comment="是否推荐")
    features = Column(Text, nullable=True, comment="中文特性（JSON格式）")
    features_en = Column(Text, nullable=True, comment="英文特性（JSON格式）")
    badge = Column(String(50), nullable=True, comment="中文角标")
    badge_en = Column(String(50), nullable=True, comment="英文角标")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="显示顺序")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "name_en": self.name_en or self.name,
            "price": self.price,
            "price_usd": self.price_usd or self.price,
            "original_price": self.original_price,
            "original_price_usd": self.original_price_usd,
            "credits": self.credits,
            "credits_cn": self.credits_cn if self.credits_cn is not None else self.credits,
            "recommended": self.recommended,
            "features": self._parse(self.features),
            "features_en": self._parse(self.features_en) or self._parse(self.features),
            "badge": self.badge,
            "badge_en": self.badge_en,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
        }

    @staticmethod
    def _parse(features_json):
        if not features_json:
            return []
        import json
        try:
            return json.loads(features_json)
        except:
            return []


class Subscription(PaymentBase):
    """订阅订单模型"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    order_no = Column(String(64), unique=True, nullable=False, index=True, comment="商户订单号")
    plan_type = Column(String(32), nullable=False, comment="套餐类型: single(体验包1篇)/semester(标准包3篇)/yearly(进阶包6篇)/unlock(单次解锁)")
    amount = Column(Float, nullable=False, comment="订单金额")
    currency = Column(String(10), default="CNY", comment="货币: CNY/USD")
    status = Column(String(20), default="pending", comment="订单状态: pending/paid/cancelled")
    payment_method = Column(String(20), nullable=True, comment="支付方式: alipay/paypal/paddle")
    payment_time = Column(DateTime(timezone=True), nullable=True, comment="支付时间")
    trade_no = Column(String(64), nullable=True, comment="支付宝交易号")
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="会员到期时间")
    record_id = Column(Integer, nullable=True, comment="关联的综述记录ID（unlock类型时使用）")
    extra_data = Column(Text, nullable=True, comment="额外数据（JSON格式）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "order_no": self.order_no,
            "plan_type": self.plan_type,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "payment_method": self.payment_method,
            "payment_time": self.payment_time.isoformat() if self.payment_time else None,
            "trade_no": self.trade_no,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_metadata(self) -> dict:
        import json
        if self.extra_data:
            try:
                return json.loads(self.extra_data)
            except Exception:
                return {}
        return {}

    def set_metadata(self, data: dict):
        import json
        self.extra_data = json.dumps(data)

    def get_meta(self, key: str, default=None):
        return self.get_metadata().get(key, default)

    def set_meta(self, key: str, value):
        data = self.get_metadata()
        data[key] = value
        self.set_metadata(data)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(self, "extra_data")


class PaymentLog(PaymentBase):
    """支付日志模型"""
    __tablename__ = "payment_logs"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, nullable=True, comment="订阅ID")
    user_id = Column(Integer, nullable=True, comment="用户ID")
    action = Column(String(50), nullable=False, comment="操作类型")
    request_data = Column(Text, nullable=True, comment="请求数据")
    response_data = Column(Text, nullable=True, comment="响应数据")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")


# ==================== Pydantic Schemas ====================

class SubscriptionCreate(BaseModel):
    """创建订阅请求"""
    plan_type: str  # single(体验包1篇)/semester(标准包3篇)/yearly(进阶包6篇)/unlock(单次解锁)


class PaymentCreateResponse(BaseModel):
    """创建支付响应"""
    order_no: str
    pay_url: str
    amount: float
    expires_in: int = 900  # 15分钟


class MembershipInfo(BaseModel):
    """会员信息"""
    membership_type: str = "free"  # free / premium
    expires_at: Optional[str] = None
    days_remaining: Optional[int] = None


# ==================== 套餐定义 ====================

# 默认套餐配置（用于初始化数据库）
DEFAULT_PLANS = [
    {
        "type": "single",
        "name": "体验包", "name_en": "Starter",
        "price": 9.9, "price_usd": 9.99,
        "original_price": 29.8, "original_price_usd": 14.99,
        "credits": 6,
        "credits_cn": 2,
        "recommended": False,
        "sort_order": 1,
        "badge": None, "badge_en": None,
        "features": [
            "2 个积分（1 篇综述 或 2 篇对比矩阵）",
            "在线查看 + Word 导出",
            "参考文献包含真实文献 DOI 链接",
            "支持导出 BibTeX、RIS、Word 格式",
            "约 ¥4.9/积分",
        ],
        "features_en": [
            "6 Credits (3 reviews or 6 comparison matrices)",
            "Online viewing + Word export",
            "DOI-verifiable citations",
            "Export BibTeX, XML, RIS formats",
            "~$1.67/Credit",
        ]
    },
    {
        "type": "semester",
        "name": "标准包", "name_en": "Semester Pro",
        "price": 19.8, "price_usd": 24.99,
        "original_price": 69.8, "original_price_usd": 39.99,
        "credits": 20,
        "credits_cn": 6,
        "recommended": True,
        "sort_order": 2,
        "badge": "热门", "badge_en": "Popular",
        "features": [
            "6 个积分（3 篇综述 或 6 篇对比矩阵）",
            "在线查看 + Word 导出",
            "参考文献包含真实文献 DOI 链接",
            "支持导出 BibTeX、RIS、Word 格式",
            "约 ¥3.3/积分",
        ],
        "features_en": [
            "20 Credits (10 reviews or 20 comparison matrices)",
            "Online viewing + Word export",
            "DOI-verifiable citations",
            "Export BibTeX, XML, RIS formats",
            "~$1.25/Credit",
        ]
    },
    {
        "type": "yearly",
        "name": "进阶包", "name_en": "Annual Premium",
        "price": 49.8, "price_usd": 49.99,
        "original_price": 109.8, "original_price_usd": 69.99,
        "credits": 50,
        "credits_cn": 18,
        "recommended": False,
        "sort_order": 3,
        "badge": "超值", "badge_en": "Best Value",
        "features": [
            "18 个积分（9 篇综述 或 18 篇对比矩阵）",
            "在线查看 + Word 导出",
            "参考文献包含真实文献 DOI 链接",
            "支持导出 BibTeX、RIS、Word 格式",
            "约 ¥2.8/积分",
        ],
        "features_en": [
            "50 Credits (25 reviews or 50 comparison matrices)",
            "Online viewing + Word export",
            "DOI-verifiable citations",
            "Export BibTeX, XML, RIS formats",
            "~$1.00/Credit",
        ]
    },
    {
        "type": "unlock",
        "name": "单次解锁", "name_en": "Unlock Single Export",
        "price": 9.9, "price_usd": 9.99,
        "original_price": None, "original_price_usd": None,
        "credits": 0,
        "credits_cn": 0,
        "recommended": False,
        "sort_order": 4,
        "badge": None, "badge_en": None,
        "features": [
            "解锁当前综述 Word 导出权限",
            "无水印 Word 文档",
        ],
        "features_en": [
            "Unlock Word export for this review",
            "Watermark-free Word document",
        ]
    },
]

# 保持向后兼容的常量（从数据库读取）
PLANS = DEFAULT_PLANS
PLAN_CREDITS = {p["type"]: p["credits"] for p in PLANS}
PLAN_DURATION = {p["type"]: 365 for p in PLANS}  # 额度不过期，保持兼容


def get_plans_from_db(session):
    """
    从数据库获取启用的套餐列表

    Args:
        session: 数据库会话

    Returns:
        套餐列表
    """
    plans = session.query(Plan).filter_by(is_active=True).order_by(Plan.sort_order).all()
    if plans:
        return [plan.to_dict() for plan in plans]
    # 如果数据库中没有套餐，返回默认配置
    return DEFAULT_PLANS


def init_plans_in_db(session):
    """
    初始化或更新套餐数据到数据库

    Args:
        session: 数据库会话
    """
    import json

    for plan_data in DEFAULT_PLANS:
        existing = session.query(Plan).filter_by(type=plan_data["type"]).first()
        if existing:
            # 已存在则更新
            existing.name = plan_data["name"]
            existing.name_en = plan_data.get("name_en")
            existing.price = plan_data["price"]
            existing.price_usd = plan_data.get("price_usd")
            existing.original_price = plan_data.get("original_price")
            existing.original_price_usd = plan_data.get("original_price_usd")
            existing.credits = plan_data["credits"]
            existing.credits_cn = plan_data.get("credits_cn")
            existing.recommended = plan_data["recommended"]
            existing.features = json.dumps(plan_data["features"])
            existing.features_en = json.dumps(plan_data["features_en"]) if plan_data.get("features_en") else None
            existing.badge = plan_data.get("badge")
            existing.badge_en = plan_data.get("badge_en")
            existing.sort_order = plan_data.get("sort_order", 0)
        else:
            # 不存在则创建
            plan = Plan(
                type=plan_data["type"],
                name=plan_data["name"],
                name_en=plan_data.get("name_en"),
                price=plan_data["price"],
                price_usd=plan_data.get("price_usd"),
                original_price=plan_data.get("original_price"),
                original_price_usd=plan_data.get("original_price_usd"),
                credits=plan_data["credits"],
                credits_cn=plan_data.get("credits_cn"),
                recommended=plan_data["recommended"],
                features=json.dumps(plan_data["features"]),
                features_en=json.dumps(plan_data["features_en"]) if plan_data.get("features_en") else None,
                badge=plan_data.get("badge"),
                badge_en=plan_data.get("badge_en"),
                sort_order=plan_data.get("sort_order", 0)
            )
            session.add(plan)
    session.commit()
    print("[Init] 已同步套餐数据到数据库")
