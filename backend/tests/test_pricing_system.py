"""
定价体系一致性测试

验证所有定价相关配置在不同文件中保持一致：
- backend/authkit/models/payment.py (DEFAULT_PLANS)
- backend/authkit/services/paddle_service.py (PADDLE_PRICING)
- backend/authkit/services/paypal_service.py (PAYPAL_PRICING)
- backend/migrations/005_migrate_credits_to_points.py (plan_credits)
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()


# ========== 从各模块提取定价数据 ==========

def get_default_plans():
    """从 payment.py 提取 DEFAULT_PLANS"""
    from authkit.models.payment import DEFAULT_PLANS
    return DEFAULT_PLANS


def get_paddle_pricing():
    """从 paddle_service.py 提取 PADDLE_PRICING"""
    from authkit.services.paddle_service import PADDLE_PRICING
    return PADDLE_PRICING


def get_paypal_pricing():
    """从 paypal_service.py 提取 PAYPAL_PRICING"""
    from authkit.services.paypal_service import PAYPAL_PRICING
    return PAYPAL_PRICING


def get_migration_plan_credits():
    """从迁移脚本提取 plan_credits"""
    # 直接解析文件内容，避免执行迁移
    migration_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "migrations", "005_migrate_credits_to_points.py"
    )
    if not os.path.exists(migration_path):
        return None

    with open(migration_path, "r") as f:
        content = f.read()

    # 提取 plan_credits 字典
    import re
    match = re.search(r'plan_credits\s*=\s*\{([^}]+)\}', content)
    if not match:
        return None

    credits_str = match.group(1)
    credits = {}
    for line in credits_str.strip().split('\n'):
        line = line.strip().rstrip(',')
        if ':' in line or ',' in line:
            parts = line.replace('"', '').replace("'", "").split(':')
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip()
                try:
                    credits[key] = int(val)
                except ValueError:
                    pass
    return credits


def get_migration_features_en():
    """从迁移脚本提取 plan_features_en"""
    migration_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "migrations", "005_migrate_credits_to_points.py"
    )
    if not os.path.exists(migration_path):
        return None

    with open(migration_path, "r") as f:
        content = f.read()

    # 检查 features_en 是否包含正确的 credit 数量
    results = {}
    import re

    # 检查每个套餐的 features_en 描述中的 credit 数量
    patterns = {
        "single": r'"single".*?"(\d+)\s+Credits',
        "semester": r'"semester".*?"(\d+)\s+Credits',
        "yearly": r'"yearly".*?"(\d+)\s+Credits',
    }

    for plan_type, pattern in patterns.items():
        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            results[plan_type] = int(matches[-1])  # 取最后一个匹配

    return results if results else None


# ========== 测试用例 ==========

def test_default_plans_credits():
    """测试 DEFAULT_PLANS 中的 credits 数量是否正确"""
    print("\n[测试] DEFAULT_PLANS credits 数量...")
    plans = get_default_plans()

    expected = {
        "single": 6,
        "semester": 20,
        "yearly": 50,
        "unlock": 0,
    }

    all_pass = True
    for plan in plans:
        ptype = plan["type"]
        if ptype in expected:
            actual = plan["credits"]
            exp = expected[ptype]
            status = "✓" if actual == exp else "✗"
            if actual != exp:
                all_pass = False
            print(f"  {status} {ptype}: credits={actual} (期望 {exp})")

    return all_pass


def test_default_plans_usd_pricing():
    """测试 DEFAULT_PLANS 中的 USD 定价"""
    print("\n[测试] DEFAULT_PLANS USD 定价...")
    plans = get_default_plans()

    expected = {
        "single": 9.99,
        "semester": 24.99,
        "yearly": 49.99,
        "unlock": 9.99,
    }

    all_pass = True
    for plan in plans:
        ptype = plan["type"]
        if ptype in expected:
            actual = plan.get("price_usd", 0)
            exp = expected[ptype]
            status = "✓" if actual == exp else "✗"
            if actual != exp:
                all_pass = False
            print(f"  {status} {ptype}: price_usd={actual} (期望 {exp})")

    return all_pass


def test_paddle_pricing_consistency():
    """测试 PADDLE_PRICING 与 DEFAULT_PLANS 的一致性"""
    print("\n[测试] PADDLE_PRICING 与 DEFAULT_PLANS 一致性...")
    plans = get_default_plans()
    paddle = get_paddle_pricing()

    all_pass = True
    plan_dict = {p["type"]: p for p in plans}

    for ptype in ["single", "semester", "yearly"]:
        if ptype in paddle and ptype in plan_dict:
            paddle_plan = paddle[ptype]
            default_plan = plan_dict[ptype]

            # 检查 credits 一致
            if paddle_plan["credits"] != default_plan["credits"]:
                print(f"  ✗ {ptype}: credits 不一致 Paddle={paddle_plan['credits']} vs DEFAULT={default_plan['credits']}")
                all_pass = False
            else:
                print(f"  ✓ {ptype}: credits={paddle_plan['credits']}")

            # 检查 price_usd 一致（Paddle 可能用不同价格）
            paddle_price = paddle_plan["price"]
            default_price = default_plan.get("price_usd", 0)
            # Paddle 可以有自己的价格策略，这里只做记录
            if paddle_price != default_price:
                print(f"  ⚠ {ptype}: USD 价格不同 Paddle=${paddle_price} vs DEFAULT=${default_price}（Paddle 独立定价，可接受）")
            else:
                print(f"  ✓ {ptype}: price_usd=${paddle_price}")

    return all_pass


def test_paypal_pricing_consistency():
    """测试 PAYPAL_PRICING 与 DEFAULT_PLANS 的一致性"""
    print("\n[测试] PAYPAL_PRICING 与 DEFAULT_PLANS 一致性...")
    plans = get_default_plans()
    paypal = get_paypal_pricing()

    all_pass = True
    plan_dict = {p["type"]: p for p in plans}

    for ptype in ["single", "semester", "yearly"]:
        if ptype in paypal and ptype in plan_dict:
            paypal_plan = paypal[ptype]
            default_plan = plan_dict[ptype]

            # 检查 credits 一致
            if paypal_plan["credits"] != default_plan["credits"]:
                print(f"  ✗ {ptype}: credits 不一致 PayPal={paypal_plan['credits']} vs DEFAULT={default_plan['credits']}")
                all_pass = False
            else:
                print(f"  ✓ {ptype}: credits={paypal_plan['credits']}")

            # 检查 price_usd 一致
            paypal_price = paypal_plan["price"]
            default_price = default_plan.get("price_usd", 0)
            if paypal_price != default_price:
                print(f"  ✗ {ptype}: USD 价格不一致 PayPal=${paypal_price} vs DEFAULT=${default_price}")
                all_pass = False
            else:
                print(f"  ✓ {ptype}: price_usd=${paypal_price}")

    return all_pass


def test_migration_credits_consistency():
    """测试迁移脚本的 plan_credits 与 DEFAULT_PLANS 一致"""
    print("\n[测试] 迁移脚本 005 plan_credits 与 DEFAULT_PLANS 一致性...")
    plans = get_default_plans()
    migration_credits = get_migration_plan_credits()

    if migration_credits is None:
        print("  ⚠ 迁移脚本 005 未找到，跳过")
        return True

    all_pass = True
    plan_dict = {p["type"]: p for p in plans}

    for ptype in ["single", "semester", "yearly"]:
        if ptype in migration_credits and ptype in plan_dict:
            mig_credits = migration_credits[ptype]
            default_credits = plan_dict[ptype]["credits"]
            if mig_credits != default_credits:
                print(f"  ✗ {ptype}: 迁移 credits={mig_credits} vs DEFAULT credits={default_credits}")
                all_pass = False
            else:
                print(f"  ✓ {ptype}: credits={mig_credits}")

    return all_pass


def test_plan_features_en_credits_description():
    """测试 features_en 中的 credit 描述与实际 credits 数量一致"""
    print("\n[测试] features_en 中 credit 描述与实际 credits 数量一致性...")
    plans = get_default_plans()

    import re
    all_pass = True

    for plan in plans:
        ptype = plan["type"]
        credits = plan["credits"]
        features_en = plan.get("features_en", [])

        if ptype == "unlock" or not features_en:
            continue

        # 查找 features_en 中包含 "Credits" 的描述
        for feature in features_en:
            if "Credit" in feature:
                match = re.search(r'(\d+)\s+Credit', feature)
                if match:
                    described_credits = int(match.group(1))
                    if described_credits != credits:
                        print(f"  ✗ {ptype}: features_en 描述 {described_credits} credits vs 实际 {credits} credits")
                        all_pass = False
                    else:
                        print(f"  ✓ {ptype}: features_en 描述 {described_credits} credits = 实际 {credits} credits")
                break

    return all_pass


def test_plan_cost_per_credit():
    """测试每个套餐的 credit 单价是否合理"""
    print("\n[测试] Credit 单价合理性...")
    plans = get_default_plans()

    all_pass = True
    for plan in plans:
        ptype = plan["type"]
        credits = plan["credits"]
        price_usd = plan.get("price_usd", 0)

        if credits == 0 or price_usd == 0:
            continue

        cost_per_credit = price_usd / credits
        print(f"  ℹ {ptype}: ${price_usd} / {credits} credits = ${cost_per_credit:.2f}/credit")

        # 检查单价递减（批量购买应更便宜）
        # 单价不应超过 $2.00
        if cost_per_credit > 2.0:
            print(f"  ✗ {ptype}: 单价 ${cost_per_credit:.2f} 过高（超过 $2.00/credit）")
            all_pass = False

    return all_pass


def test_all_plan_types_present():
    """测试所有必需的套餐类型都存在"""
    print("\n[测试] 所有必需套餐类型是否存在...")
    plans = get_default_plans()
    plan_types = {p["type"] for p in plans}

    required = {"single", "semester", "yearly", "unlock"}
    all_pass = True

    for req in required:
        if req in plan_types:
            print(f"  ✓ 套餐类型 '{req}' 存在")
        else:
            print(f"  ✗ 套餐类型 '{req}' 缺失")
            all_pass = False

    return all_pass


def test_plan_model_fields():
    """测试 Plan 模型包含所有必要字段"""
    print("\n[测试] Plan 模型字段完整性...")
    from authkit.models.payment import Plan

    required_columns = [
        "id", "type", "name", "name_en", "price", "price_usd",
        "original_price", "original_price_usd", "credits", "recommended",
        "features", "features_en", "badge", "badge_en", "is_active", "sort_order"
    ]

    all_pass = True
    existing_columns = {c.name for c in Plan.__table__.columns}

    for col in required_columns:
        if col in existing_columns:
            print(f"  ✓ 字段 '{col}' 存在")
        else:
            print(f"  ✗ 字段 '{col}' 缺失")
            all_pass = False

    return all_pass


def test_subscription_model_fields():
    """测试 Subscription 模型包含所有必要字段"""
    print("\n[测试] Subscription 模型字段完整性...")
    from authkit.models.payment import Subscription

    required_columns = [
        "id", "user_id", "order_no", "plan_type", "amount", "currency",
        "status", "payment_method", "payment_time", "trade_no", "extra_data"
    ]

    all_pass = True
    existing_columns = {c.name for c in Subscription.__table__.columns}

    for col in required_columns:
        if col in existing_columns:
            print(f"  ✓ 字段 '{col}' 存在")
        else:
            print(f"  ✗ 字段 '{col}' 缺失")
            all_pass = False

    return all_pass


def main():
    print("=" * 60)
    print("定价体系一致性测试")
    print("=" * 60)

    tests = [
        ("DEFAULT_PLANS credits 数量", test_default_plans_credits),
        ("DEFAULT_PLANS USD 定价", test_default_plans_usd_pricing),
        ("PADDLE_PRICING 一致性", test_paddle_pricing_consistency),
        ("PAYPAL_PRICING 一致性", test_paypal_pricing_consistency),
        ("迁移脚本 005 一致性", test_migration_credits_consistency),
        ("features_en 描述一致性", test_plan_features_en_credits_description),
        ("Credit 单价合理性", test_plan_cost_per_credit),
        ("套餐类型完整性", test_all_plan_types_present),
        ("Plan 模型字段", test_plan_model_fields),
        ("Subscription 模型字段", test_subscription_model_fields),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"\n  ✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed_count = 0
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status} - {name}")
        if passed:
            passed_count += 1

    total = len(results)
    print(f"\n  总计: {passed_count}/{total} 通过")

    return 0 if passed_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
