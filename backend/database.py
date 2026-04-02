"""
数据库管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    """数据库管理类"""

    def __init__(self):
        # 数据库类型选择
        self.db_type = os.getenv("DB_TYPE", "postgresql").lower()  # postgresql 或 mysql

        if self.db_type == "postgresql":
            # PostgreSQL 配置
            self.db_user = os.getenv("DB_USER", "postgres")
            self.db_password = os.getenv("DB_PASSWORD", "security")
            self.db_host = os.getenv("DB_HOST", "localhost")
            self.db_port = os.getenv("DB_PORT", "5432")
            self.db_name = os.getenv("DB_NAME", "paper")

            self.database_url = (
                f"postgresql://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
            # PostgreSQL 连接池配置
            self.pool_size = 10
            self.max_overflow = 20
        else:
            # MySQL 配置（原有逻辑）
            self.db_user = os.getenv("DB_USER", "root")
            self.db_password = os.getenv("DB_PASSWORD", "security")
            self.db_host = os.getenv("DB_HOST", "localhost")
            self.db_port = os.getenv("DB_PORT", "3306")
            self.db_name = os.getenv("DB_NAME", "paper")

            self.database_url = (
                f"mysql+pymysql://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
                f"?charset=utf8mb4"
            )
            # MySQL 连接池配置
            self.pool_size = 5
            self.max_overflow = 10

        self.engine = None
        self.SessionLocal = None

        print(f"[Database] 数据库类型: {self.db_type.upper()}")
        print(f"[Database] 连接地址: {self.db_host}:{self.db_port}/{self.db_name}")

    def connect(self):
        """创建数据库连接"""
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        return self.engine

    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话"""
        if self.SessionLocal is None:
            self.connect()
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def create_tables(self):
        """创建所有表"""
        from models import Base
        if self.engine is None:
            self.connect()
        Base.metadata.create_all(bind=self.engine)


# 全局数据库实例
db = Database()


def get_db():
    """依赖注入：获取数据库会话"""
    yield from db.get_session()
