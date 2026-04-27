"""
推广邮件联系人模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, UniqueConstraint, func

from . import Base


class EmailContact(Base):
    __tablename__ = "email_contacts"

    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    email = Column(String(500), nullable=False)
    position = Column(String(200))
    source_url = Column(Text)
    status = Column(String(20), default="pending")  # pending / sent / failed
    template_variant = Column(String(2))  # a / b / c / d — A/B 测试
    unsubscribed = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    error = Column(Text)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("email", name="uq_email_contacts_email"),
    )
