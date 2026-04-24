"""
authkit 模块化功能测试 — Redis / Database / LLM
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# Redis 模块测试
# ============================================================

class TestRedisConfig:
    """Redis 配置测试"""

    def test_default_config_reads_env(self):
        from authkit.redis.config import RedisConfig

        cfg = RedisConfig()
        # 默认从 AUTH_REDIS_* 环境变量读取，没有则 localhost
        assert cfg.host is not None
        assert cfg.port == 6379 or cfg.port == int(os.getenv("AUTH_REDIS_PORT", "6379"))
        assert cfg.decode_responses is True
        assert cfg.max_connections == 20

    def test_explicit_config(self):
        from authkit.redis.config import RedisConfig

        cfg = RedisConfig(host="10.0.0.1", port=6380, db=2, password="secret")
        assert cfg.host == "10.0.0.1"
        assert cfg.port == 6380
        assert cfg.db == 2
        assert cfg.password == "secret"

    def test_frozen(self):
        from authkit.redis.config import RedisConfig

        cfg = RedisConfig(host="localhost")
        with pytest.raises(AttributeError):
            cfg.host = "other"


class TestRedisClient:
    """Redis 客户端管理测试"""

    def test_init_redis_returns_client(self):
        from authkit.redis import init_redis

        client = init_redis()
        # 如果 Redis 可用则返回客户端，否则 None
        assert client is None or hasattr(client, "ping")

    def test_get_redis_returns_same_instance(self):
        from authkit.redis import init_redis, get_redis

        init_redis()
        a = get_redis()
        b = get_redis()
        assert a is b  # 单例

    def test_client_basic_operations(self):
        """测试基本 Redis 读写（需要 Redis 可用）"""
        from authkit.redis import get_redis

        client = get_redis()
        if client is None:
            pytest.skip("Redis 不可用")

        key = "authkit:test:hello"
        client.set(key, "world", ex=10)
        assert client.get(key) == "world"
        client.delete(key)
        assert client.get(key) is None


class TestRedisPatterns:
    """Redis 工具类测试"""

    def test_cache_set_get_delete(self):
        from authkit.redis import get_redis, RedisCache

        client = get_redis()
        if client is None:
            pytest.skip("Redis 不可用")

        cache = RedisCache(client, prefix="test_cache", default_ttl=30)
        assert cache.set("k1", "v1") is True
        assert cache.get("k1") == "v1"
        assert cache.exists("k1") is True
        assert cache.delete("k1") is True
        assert cache.get("k1") is None

    def test_cache_ttl_expiry(self):
        from authkit.redis import get_redis, RedisCache

        client = get_redis()
        if client is None:
            pytest.skip("Redis 不可用")

        cache = RedisCache(client, prefix="test_ttl", default_ttl=1)
        cache.set("short", "gone")
        assert cache.get("short") == "gone"
        import time
        time.sleep(2)
        assert cache.get("short") is None

    def test_rate_limiter_allows_then_blocks(self):
        from authkit.redis import get_redis, RedisRateLimiter

        client = get_redis()
        if client is None:
            pytest.skip("Redis 不可用")

        limiter = RedisRateLimiter(client, prefix="test_rate")
        key = "test_user_123"

        # 前 3 次应该允许
        for _ in range(3):
            allowed, remaining = limiter.is_allowed(key, max_requests=3, window_seconds=60)
            assert allowed is True

        # 第 4 次应该被拒绝
        allowed, remaining = limiter.is_allowed(key, max_requests=3, window_seconds=60)
        assert allowed is False
        assert remaining == 0


class TestCacheServiceIntegration:
    """CacheService 集成测试"""

    def test_verification_code_flow(self):
        from authkit.services.cache_service import CacheService
        from authkit.redis import get_redis

        client = get_redis()
        if client is None:
            pytest.skip("Redis 不可用")

        svc = CacheService(redis_client=client)

        email = "test@example.com"
        code = "123456"

        # 保存验证码
        assert svc.save_verification_code(email, code) is True

        # 获取验证码
        assert svc.get_verification_code(email) == code

        # 验证成功
        assert svc.verify_code(email, code) is True

        # 验证后应被删除
        assert svc.get_verification_code(email) is None

        # 再次验证应失败
        assert svc.verify_code(email, code) is False

    def test_code_sent_rate_limit(self):
        from authkit.services.cache_service import CacheService
        from authkit.redis import get_redis

        client = get_redis()
        if client is None:
            pytest.skip("Redis 不可用")

        svc = CacheService(redis_client=client)
        email = "rate@example.com"

        # 清理
        svc.delete(f"verification_code_sent:login:{email}")

        # 首次未发送
        assert svc.check_code_sent_recently(email) is False

        # 标记已发送
        assert svc.mark_code_sent(email) is True

        # 检测到已发送
        assert svc.check_code_sent_recently(email) is True

        # 清理
        svc.delete(f"verification_code_sent:login:{email}")


# ============================================================
# Database 模块测试
# ============================================================

class TestDatabaseConfig:
    """Database 配置测试"""

    def test_config_from_env(self):
        from authkit.database import DatabaseConfig

        cfg = DatabaseConfig()
        assert "://" in cfg.url  # 应该包含数据库协议
        assert cfg.pool_size == 10
        assert cfg.max_overflow == 20
        assert cfg.pool_pre_ping is True

    def test_config_explicit_url(self):
        from authkit.database import DatabaseConfig

        cfg = DatabaseConfig(url="sqlite:///test.db")
        assert cfg.url == "sqlite:///test.db"

    def test_frozen(self):
        from authkit.database import DatabaseConfig

        cfg = DatabaseConfig(url="sqlite:///test.db")
        with pytest.raises(AttributeError):
            cfg.url = "other"


class TestDatabase:
    """Database 类测试"""

    def test_create_database_from_env(self):
        from authkit.database import Database, create_database

        db = create_database()
        assert db.engine is not None
        assert db.SessionLocal is not None

    def test_get_session_yields_session(self):
        from sqlalchemy import text
        from authkit.database import create_database

        db = create_database()
        for session in db.get_session():
            assert session is not None
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1

    def test_create_tables(self):
        from authkit.database import create_database

        db = create_database()
        # 不应报错（幂等）
        db.create_tables()


class TestDatabaseShim:
    """backend/database.py 薄封装层测试"""

    def test_shim_imports(self):
        from database import db, get_db

        assert db is not None
        assert db.engine is not None

    def test_shim_get_db(self):
        from sqlalchemy import text
        from database import get_db

        for session in get_db():
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1


class TestLegacyDatabaseAPI:
    """旧 API 兼容性测试"""

    def test_init_and_get_db(self):
        from sqlalchemy import text
        from authkit.database import init_database, get_db

        db_url = os.getenv("AUTH_DATABASE_URL", "postgresql://postgres:security@localhost/paper")
        if not db_url or db_url == "postgresql://postgres:security@localhost/paper":
            # 尝试用主数据库 URL
            db_url = os.getenv("DB_TYPE", "postgresql").lower()
            user = os.getenv("DB_USER", "postgres")
            password = os.getenv("DB_PASSWORD", "security")
            host = os.getenv("DB_HOST", "localhost")
            port = os.getenv("DB_PORT", "5432")
            name = os.getenv("DB_NAME", "paper")
            db_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"

        init_database(db_url)
        for session in get_db():
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1


# ============================================================
# LLM 模块测试
# ============================================================

class TestLLMConfig:
    """LLM 配置测试"""

    def test_default_config_reads_env(self):
        from authkit.llm.config import LLMConfig

        cfg = LLMConfig()
        assert cfg.api_key == os.getenv("DEEPSEEK_API_KEY", "")
        assert cfg.base_url == os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        assert cfg.model == os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        assert cfg.timeout == 120.0
        assert cfg.max_retries == 3

    def test_explicit_config(self):
        from authkit.llm.config import LLMConfig

        cfg = LLMConfig(api_key="sk-test", base_url="https://api.test.com", model="gpt-4")
        assert cfg.api_key == "sk-test"
        assert cfg.base_url == "https://api.test.com"
        assert cfg.model == "gpt-4"

    def test_frozen(self):
        from authkit.llm.config import LLMConfig

        cfg = LLMConfig(api_key="sk-test")
        with pytest.raises(AttributeError):
            cfg.api_key = "other"


class TestLLMClient:
    """LLM 客户端测试"""

    def test_create_client(self):
        from authkit.llm import create_llm_client

        client = create_llm_client()
        assert client is not None
        assert client.config.api_key != ""

    def test_get_raw_client(self):
        from authkit.llm import get_llm_client

        llm = get_llm_client()
        raw = llm.get_raw_client()
        from openai import AsyncOpenAI

        assert isinstance(raw, AsyncOpenAI)

    def test_singleton(self):
        from authkit.llm import get_llm_client

        a = get_llm_client()
        b = get_llm_client()
        assert a is b

    @pytest.mark.asyncio
    async def test_chat_real_call(self):
        """实际调用 DeepSeek API（需要 API Key）"""
        from authkit.llm import get_llm_client

        llm = get_llm_client()
        if not llm.config.api_key:
            pytest.skip("DEEPSEEK_API_KEY 未配置")

        result = await llm.chat(
            messages=[{"role": "user", "content": "请回复 OK"}],
            max_tokens=10,
        )
        assert "OK" in result or "ok" in result.lower()


class TestLLMMigration:
    """验证迁移后的 service 能正确获取 LLM 客户端"""

    def test_smart_review_generator_gets_client(self):
        from services.smart_review_generator_final import SmartReviewGeneratorFinal

        gen = SmartReviewGeneratorFinal(deepseek_api_key="test-key")
        from openai import AsyncOpenAI

        assert isinstance(gen.llm_client, AsyncOpenAI)

    def test_paper_search_agent_gets_client(self):
        from services.paper_search_agent import PaperSearchAgent

        agent = PaperSearchAgent("test topic")
        from openai import AsyncOpenAI

        assert isinstance(agent.llm_client, AsyncOpenAI)

    def test_hybrid_classifier_gets_client(self):
        from services.hybrid_classifier import HybridTopicClassifier

        clf = HybridTopicClassifier()
        from openai import AsyncOpenAI

        assert isinstance(clf.client, AsyncOpenAI)

    def test_deep_comparison_gets_client(self):
        from services.deep_comparison import DeepComparisonAnalyzer

        analyzer = DeepComparisonAnalyzer()
        from openai import AsyncOpenAI

        assert isinstance(analyzer.client, AsyncOpenAI)


# ============================================================
# 跨模块集成测试
# ============================================================

class TestCrossModuleIntegration:
    """验证三个模块可以同时正常工作"""

    def test_all_modules_importable(self):
        from authkit.redis import get_redis, RedisConfig
        from authkit.database import Database, DatabaseConfig, create_database
        from authkit.llm import get_llm_client, LLMConfig
        from authkit.oauth import OAuthConfig, create_oauth_router

        # 只验证 import 不报错
        assert RedisConfig is not None
        assert DatabaseConfig is not None
        assert LLMConfig is not None
        assert OAuthConfig is not None

    def test_task_manager_uses_shared_redis(self):
        """验证 TaskManager 使用共享 Redis（不再是独立连接）"""
        from services.task_manager import TaskManager
        from authkit.redis import get_redis

        tm = TaskManager()
        shared_redis = get_redis()

        if shared_redis:
            assert tm._persistence.redis_client is shared_redis

    def test_database_shim_uses_authkit(self):
        """验证 database.py shim 委托给 authkit"""
        from database import db as shim_db
        from authkit.database import Database

        assert isinstance(shim_db, Database)
