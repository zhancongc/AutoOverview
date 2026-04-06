"""
数据库初始化工具
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# 创建数据库引擎（需要在主应用中配置）
engine = None
SessionLocal = None


def init_database(database_url: str):
    """
    初始化数据库

    Args:
        database_url: 数据库连接字符串，例如：
            - SQLite: sqlite:///./auth.db
            - PostgreSQL: postgresql://user:password@localhost/dbname
            - MySQL: mysql://user:password@localhost/dbname
    """
    global engine, SessionLocal

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # 创建表
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    if SessionLocal is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
