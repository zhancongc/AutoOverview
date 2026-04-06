"""
用户数据模型（通用版本，可复用）
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """用户模型（通用版本）"""
    __tablename__ = "users"

    # 基础字段
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    email = Column(String(255), unique=True, index=True, nullable=False, comment="邮箱")
    hashed_password = Column(String(255), comment="加密后的密码")

    # 用户信息
    nickname = Column(String(100), comment="昵称")
    avatar_url = Column(String(500), comment="头像URL")
    gender = Column(Integer, default=0, comment="性别：0-未知，1-男，2-女")
    country = Column(String(50), comment="国家")
    province = Column(String(50), comment="省份")
    city = Column(String(50), comment="城市")
    language = Column(String(20), default="zh_CN", comment="语言")
    phone_number = Column(String(20), comment="手机号")

    # 账号状态
    is_active = Column(Boolean, default=True, comment="是否活跃")
    is_verified = Column(Boolean, default=False, comment="邮箱是否验证")
    is_superuser = Column(Boolean, default=False, comment="是否超级管理员")
    is_staff = Column(Boolean, default=False, comment="是否员工")

    # 扩展字段（JSON 格式，用于存储业务特定数据）
    meta_data = Column(Text, comment="扩展元数据（JSON格式）")

    # 时间字段
    last_login_at = Column(DateTime(timezone=True), comment="最后登录时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

    def get_metadata(self) -> dict:
        """获取元数据"""
        import json
        if self.meta_data:
            try:
                return json.loads(self.meta_data)
            except:
                return {}
        return {}

    def set_metadata(self, data: dict):
        """设置元数据"""
        import json
        self.meta_data = json.dumps(data)

    def get_meta(self, key: str, default=None):
        """获取元数据中的单个值"""
        return self.get_metadata().get(key, default)

    def set_meta(self, key: str, value):
        """设置元数据中的单个值"""
        data = self.get_metadata()
        data[key] = value
        self.set_metadata(data)
