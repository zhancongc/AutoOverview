"""
API 端点集成测试

测试三个核心 API 端点：
1. POST /api/search-papers-only  — 文献搜索
2. POST /api/generate-comparison-matrix — 文献对比矩阵生成
3. POST /api/smart-generate — 文献综述生成

使用 FastAPI TestClient，需要数据库连接。
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """创建 TestClient（触发 lifespan 以初始化数据库依赖）"""
    from main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers():
    """获取认证头（需要测试用户 token）"""
    token = os.getenv("TEST_AUTH_TOKEN", "")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# ==================== 文献搜索 API ====================

class TestSearchPapers:
    """POST /api/search-papers-only"""

    def test_search_without_auth_returns_401(self, client):
        """未登录应返回 401"""
        resp = client.post("/api/search-papers-only", json={
            "topic": "deep learning in image recognition",
            "target_count": 10,
            "search_years": 5,
        })
        assert resp.status_code == 401

    def test_search_with_auth(self, client, auth_headers):
        """登录用户正常发起搜索"""
        if not auth_headers:
            pytest.skip("TEST_AUTH_TOKEN not set")

        resp = client.post("/api/search-papers-only", json={
            "topic": "deep learning in image recognition",
            "target_count": 10,
            "search_years": 5,
        }, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data or "success" in data

    def test_search_missing_topic(self, client, auth_headers):
        """缺少 topic 参数应返回 422"""
        resp = client.post("/api/search-papers-only", json={
            "target_count": 10,
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_search_invalid_target_count(self, client, auth_headers):
        """target_count 超出范围应返回 422"""
        resp = client.post("/api/search-papers-only", json={
            "topic": "test topic",
            "target_count": 5,  # min is 10
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_search_daily_limit_endpoint(self, client, auth_headers):
        """GET /api/search/daily-limit 应返回限制信息"""
        if not auth_headers:
            pytest.skip("TEST_AUTH_TOKEN not set")

        resp = client.get("/api/search/daily-limit", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "limit" in data or "remaining" in data


# ==================== 文献对比矩阵生成 API ====================

class TestGenerateComparisonMatrix:
    """POST /api/generate-comparison-matrix"""

    def test_generate_without_auth(self, client):
        """未登录提交应返回失败消息"""
        resp = client.post("/api/generate-comparison-matrix", json={
            "topic": "deep learning in medical imaging",
            "language": "zh",
        })
        data = resp.json()
        assert data.get("success") is False

    def test_generate_with_auth(self, client, auth_headers):
        """登录用户提交对比矩阵任务"""
        if not auth_headers:
            pytest.skip("TEST_AUTH_TOKEN not set")

        resp = client.post("/api/generate-comparison-matrix", json={
            "topic": "deep learning in medical imaging",
            "language": "zh",
        }, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data or "success" in data

    def test_generate_missing_topic(self, client, auth_headers):
        """缺少 topic 应返回 422"""
        resp = client.post("/api/generate-comparison-matrix", json={
            "language": "zh",
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_get_comparison_matrix_not_found(self, client):
        """查询不存在的 task_id"""
        resp = client.get("/api/comparison-matrix/nonexistent-task-id")
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("success") is False or data.get("status") in ("failed", "not_found")


# ==================== 文献综述生成 API ====================

class TestSmartGenerate:
    """POST /api/smart-generate"""

    def test_generate_with_defaults(self, client, auth_headers):
        """使用默认参数提交综述生成"""
        if not auth_headers:
            pytest.skip("TEST_AUTH_TOKEN not set")

        resp = client.post("/api/smart-generate", json={
            "topic": "transformer models in NLP",
        }, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data or "success" in data

    def test_generate_with_language_en(self, client, auth_headers):
        """指定英文生成"""
        if not auth_headers:
            pytest.skip("TEST_AUTH_TOKEN not set")

        resp = client.post("/api/smart-generate", json={
            "topic": "transformer models in NLP",
            "language": "en",
        }, headers=auth_headers)

        assert resp.status_code == 200

    def test_generate_missing_topic(self, client, auth_headers):
        """缺少 topic 应返回 422"""
        resp = client.post("/api/smart-generate", json={
            "language": "zh",
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_generate_invalid_search_years(self, client, auth_headers):
        """search_years 超出范围应返回 422"""
        resp = client.post("/api/smart-generate", json={
            "topic": "test",
            "search_years": 1,  # min is 5
        }, headers=auth_headers)
        assert resp.status_code == 422


# ==================== 公共接口 ====================

class TestPublicEndpoints:
    """无需认证的公共接口"""

    def test_health_check(self, client):
        """GET / 健康检查"""
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_get_plans(self, client):
        """GET /api/subscription/plans 获取套餐列表"""
        resp = client.get("/api/subscription/plans")
        assert resp.status_code == 200
        data = resp.json()
        assert "plans" in data
        plans = data["plans"]
        assert len(plans) >= 3

        plan_types = {p["type"] for p in plans}
        assert "single" in plan_types
        assert "semester" in plan_types
        assert "yearly" in plan_types

    def test_plans_have_credits_cn(self, client):
        """套餐应包含 credits_cn 字段"""
        resp = client.get("/api/subscription/plans")
        data = resp.json()
        for plan in data["plans"]:
            assert "credits_cn" in plan
            assert isinstance(plan["credits_cn"], int)

    def test_plans_features_format(self, client):
        """套餐 features 应为列表"""
        resp = client.get("/api/subscription/plans")
        data = resp.json()
        for plan in data["plans"]:
            assert isinstance(plan["features"], list)
            assert isinstance(plan["features_en"], list)

    def test_plan_type_matches_frontend(self, client):
        """前端使用的 planType 应与后端套餐 type 一致（single/semester/yearly）"""
        resp = client.get("/api/subscription/plans")
        data = resp.json()
        plan_types = {p["type"] for p in data["plans"]}

        # 前端传的 planType 值
        frontend_plan_types = {"single", "semester", "yearly"}
        for pt in frontend_plan_types:
            assert pt in plan_types, f"前端 planType '{pt}' 在后端套餐中不存在"

    def test_plans_have_nonzero_price(self, client):
        """所有非 unlock 套餐价格应大于 0，防止 0 元支付"""
        resp = client.get("/api/subscription/plans")
        data = resp.json()
        for plan in data["plans"]:
            if plan["type"] == "unlock":
                continue
            assert plan["price"] > 0, f"{plan['type']}: price={plan['price']} 不应 <= 0"
            assert plan["price_usd"] > 0, f"{plan['type']}: price_usd={plan['price_usd']} 不应 <= 0"
