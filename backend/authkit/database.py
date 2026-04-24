"""
数据库管理 — 统一的数据库连接池与会话管理

用法:
    from authkit.database import Database, DatabaseConfig, create_database

    # 方式一：显式配置
    db = Database(DatabaseConfig(url="postgresql://user:pass@host/db"))
    db.connect()

    # 方式二：从环境变量自动创建（DB_TYPE, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME）
    db = create_database()

    # 获取会话（兼容依赖注入）
    for session in db.get_session():
        ...

    # 向后兼容（旧 API）
    init_database(url)   # 初始化全局实例
    for session in get_db():
        ...
"""
import os
import logging
from dataclasses import dataclass
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatabaseConfig:
    url: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_pre_ping: bool = True
    pool_recycle: int = 3600
    echo: bool = False

    def __post_init__(self):
        if not self.url:
            object.__setattr__(self, 'url', self._build_url_from_env())

    @staticmethod
    def _build_url_from_env() -> str:
        db_type = os.getenv("DB_TYPE", "postgresql").lower()
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "security")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME", "paper")

        if db_type == "mysql":
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"


class Database:
    """数据库管理类（连接池 + 会话）"""

    def __init__(self, config: DatabaseConfig = None):
        self._config = config or DatabaseConfig()
        self.engine = None
        self.SessionLocal = None

    def connect(self):
        """创建连接池和会话工厂"""
        url = self._config.url
        connect_args = {"check_same_thread": False} if "sqlite" in url else {}

        self.engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=self._config.pool_size,
            max_overflow=self._config.max_overflow,
            pool_pre_ping=self._config.pool_pre_ping,
            pool_recycle=self._config.pool_recycle,
            echo=self._config.echo,
            connect_args=connect_args,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        logger.info(f"[Database] 连接池已创建: {url.split('@')[-1] if '@' in url else url}")
        return self.engine

    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话（生成器）"""
        if self.SessionLocal is None:
            self.connect()
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def create_tables(self, base=None):
        """创建所有表"""
        if self.engine is None:
            self.connect()
        if base is None:
            from .models import Base
            base = Base
        base.metadata.create_all(bind=self.engine)


def create_database(config: DatabaseConfig = None) -> Database:
    """工厂函数：创建并连接数据库。config 为空时从环境变量读取。"""
    db = Database(config)
    db.connect()
    return db


# ==================== 向后兼容 API ====================

_engine = None
_SessionLocal = None
SessionLocal = _SessionLocal  # 旧代码 import 用


def init_database(database_url: str):
    """初始化数据库（旧 API，保持兼容）"""
    global _engine, _SessionLocal, SessionLocal
    from .models import Base

    connect_args = {"check_same_thread": False} if "sqlite" in database_url else {}
    _engine = create_engine(database_url, connect_args=connect_args)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    SessionLocal = _SessionLocal
    Base.metadata.create_all(bind=_engine)


def get_db():
    """获取数据库会话（旧 API，保持兼容）"""
    if _SessionLocal is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
