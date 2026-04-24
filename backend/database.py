"""
数据库管理 — 薄封装层，委托给 authkit.database

保持向后兼容：`from database import db, get_db` 继续工作。
"""
from authkit.database import Database, DatabaseConfig, create_database

# 全局数据库实例（从环境变量自动创建）
db = create_database()


def get_db():
    """依赖注入：获取数据库会话"""
    yield from db.get_session()
