"""
积分变动记录表
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func

from . import Base


class CreditLog(Base):
    __tablename__ = "credit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    change = Column(Integer, nullable=False, comment="变动量（正数增加，负数扣减）")
    balance_before = Column(Integer, nullable=False, comment="变动前余额")
    balance_after = Column(Integer, nullable=False, comment="变动后余额")
    reason = Column(String(100), nullable=False, comment="变动原因：register/payment/consume/refund/adjust")
    detail = Column(Text, comment="详细说明（订单号、任务ID等）")
    operator = Column(String(100), default="system", comment="操作者（system/admin/email）")
    created_at = Column(DateTime, default=func.now())
