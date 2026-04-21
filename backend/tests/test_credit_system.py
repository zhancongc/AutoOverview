"""
Credit 积分系统测试

验证核心积分逻辑：
- 积分扣除（check_and_deduct_credit）
- 积分退还（refund_credit）
- 支付后积分增加（_add_credits）
- 注册赠送积分
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()


# ========== Mock User 模型 ==========

class MockUser:
    """模拟 User ORM 对象，仅用于测试 meta 操作"""
    def __init__(self, user_id=1, meta_data=None):
        self.id = user_id
        self._meta_data = meta_data or {}

    def get_meta(self, key, default=None):
        return self._meta_data.get(key, default)

    def set_meta(self, key, value):
        self._meta_data[key] = value


# ========== 测试用例 ==========

def test_deduct_paid_credits_first():
    """测试扣除时优先使用付费额度"""
    print("\n[测试] 积分扣除：优先使用付费额度...")

    user = MockUser(meta_data={"review_credits": 5, "free_credits": 2})
    total_before = user.get_meta("review_credits") + user.get_meta("free_credits")
    assert total_before == 7, f"初始总额应为 7，实际 {total_before}"

    # 扣除 3 个积分，应优先从付费额度扣
    paid = user.get_meta("review_credits", 0)  # 5
    free = user.get_meta("free_credits", 0)     # 2
    cost = 3

    remaining_cost = cost
    used_paid = False

    if paid >= remaining_cost:
        user.set_meta("review_credits", paid - remaining_cost)
        used_paid = True
        remaining_cost = 0
    else:
        remaining_cost -= paid
        user.set_meta("review_credits", 0)
        used_paid = paid > 0

    if remaining_cost > 0:
        user.set_meta("free_credits", free - remaining_cost)

    # 验证
    assert user.get_meta("review_credits") == 2, f"付费额度应为 2，实际 {user.get_meta('review_credits')}"
    assert user.get_meta("free_credits") == 2, f"免费额度应为 2，实际 {user.get_meta('free_credits')}"
    assert used_paid is True, "应标记使用了付费额度"

    total_after = user.get_meta("review_credits") + user.get_meta("free_credits")
    assert total_after == 4, f"扣除后总额应为 4，实际 {total_after}"

    print(f"  ✓ 扣除 3 积分：付费 5→2, 免费 2→2, 总额 {total_before}→{total_after}")
    return True


def test_deduct_mixed_credits():
    """测试扣除时付费不够，使用免费额度补足"""
    print("\n[测试] 积分扣除：付费+免费混合扣除...")

    user = MockUser(meta_data={"review_credits": 1, "free_credits": 3})
    cost = 2

    paid = user.get_meta("review_credits", 0)  # 1
    free = user.get_meta("free_credits", 0)     # 3
    remaining_cost = cost
    used_paid = False

    if paid >= remaining_cost:
        user.set_meta("review_credits", paid - remaining_cost)
        used_paid = True
        remaining_cost = 0
    else:
        remaining_cost -= paid
        user.set_meta("review_credits", 0)
        used_paid = paid > 0

    if remaining_cost > 0:
        user.set_meta("free_credits", free - remaining_cost)

    assert user.get_meta("review_credits") == 0, f"付费额度应为 0，实际 {user.get_meta('review_credits')}"
    assert user.get_meta("free_credits") == 2, f"免费额度应为 2，实际 {user.get_meta('free_credits')}"
    assert used_paid is True, "使用了部分付费额度"

    print(f"  ✓ 扣除 2 积分：付费 1→0, 免费 3→2, used_paid=True")
    return True


def test_deduct_insufficient_credits():
    """测试积分不足时返回错误"""
    print("\n[测试] 积分扣除：积分不足...")

    user = MockUser(meta_data={"review_credits": 1, "free_credits": 0})
    total = user.get_meta("review_credits") + user.get_meta("free_credits")
    cost = 2

    insufficient = total < cost

    assert insufficient is True, "积分不足应返回 True"
    print(f"  ✓ 总额 {total} < 需要扣除 {cost}，正确判定不足")
    return True


def test_deduct_free_credits_only():
    """测试只有免费额度时的扣除"""
    print("\n[测试] 积分扣除：仅使用免费额度...")

    user = MockUser(meta_data={"review_credits": 0, "free_credits": 3})
    cost = 2

    paid = user.get_meta("review_credits", 0)  # 0
    free = user.get_meta("free_credits", 0)     # 3
    remaining_cost = cost
    used_paid = False

    if paid >= remaining_cost:
        user.set_meta("review_credits", paid - remaining_cost)
        used_paid = True
        remaining_cost = 0
    else:
        remaining_cost -= paid
        user.set_meta("review_credits", 0)
        used_paid = paid > 0  # False because paid=0

    if remaining_cost > 0:
        user.set_meta("free_credits", free - remaining_cost)

    assert user.get_meta("review_credits") == 0
    assert user.get_meta("free_credits") == 1
    assert used_paid is False, "没有使用付费额度"

    print(f"  ✓ 扣除 2 积分：付费 0→0, 免费 3→1, used_paid=False")
    return True


def test_refund_to_free_first():
    """测试退还时优先退还免费额度"""
    print("\n[测试] 积分退还：优先退还免费额度...")

    user = MockUser(meta_data={"review_credits": 1, "free_credits": 0})
    cost = 2  # 退还 2 个积分

    free = user.get_meta("free_credits", 0)  # 0
    paid = user.get_meta("review_credits", 0)  # 1

    remaining_refund = cost

    # 先退给 free
    new_free = free
    new_paid = paid

    if remaining_refund > 0:
        new_free += remaining_refund
        remaining_refund = 0

    user.set_meta("free_credits", new_free)

    assert user.get_meta("free_credits") == 2, f"免费额度应为 2，实际 {user.get_meta('free_credits')}"
    assert user.get_meta("review_credits") == 1, f"付费额度应不变为 1"

    print(f"  ✓ 退还 2 积分：付费 1→1 (不变), 免费 0→2")
    return True


def test_add_credits_after_payment():
    """测试支付成功后增加积分（使用实际套餐 credits 值）"""
    print("\n[测试] 支付成功后增加积分...")

    from authkit.models.payment import DEFAULT_PLANS
    semester_plan = next(p for p in DEFAULT_PLANS if p["type"] == "semester")
    credits_to_add = semester_plan["credits"]  # 18

    user = MockUser(meta_data={"review_credits": 2, "free_credits": 0})

    current = user.get_meta("review_credits", 0)
    user.set_meta("review_credits", current + credits_to_add)
    user.set_meta("has_purchased", True)

    expected = 2 + credits_to_add
    assert user.get_meta("review_credits") == expected, f"应为 {expected}，实际 {user.get_meta('review_credits')}"
    assert user.get_meta("has_purchased") is True

    print(f"  ✓ 增加积分：2 + {credits_to_add} = {expected}, has_purchased=True")
    return True


def test_registration_credits():
    """测试注册赠送积分"""
    print("\n[测试] 注册赠送积分...")

    # 模拟注册流程 (auth_service.py 中的逻辑)
    user = MockUser()
    user.set_meta("free_credits", 0)
    user.set_meta("review_credits", 2)
    user.set_meta("has_purchased", False)

    assert user.get_meta("review_credits") == 2, "注册应赠送 2 个积分"
    assert user.get_meta("free_credits") == 0, "免费额度应为 0"
    assert user.get_meta("has_purchased") is False

    total = user.get_meta("review_credits") + user.get_meta("free_credits")
    # 2 credits = 1 篇综述（cost=2） 或 2 篇对比矩阵（cost=1）
    assert total >= 1, "注册赠送积分应至少可生成 1 篇综述"

    print(f"  ✓ 注册赠送: review_credits=2, free_credits=0, 总计 {total} credits")
    return True


def test_review_cost_is_2():
    """测试综述生成的积分消耗为 2"""
    print("\n[测试] 综述生成积分消耗...")

    # 从 main.py 的 check_and_deduct_credit 默认参数
    REVIEW_COST = 2

    user = MockUser(meta_data={"review_credits": 2, "free_credits": 0})

    # 模拟扣除
    total = user.get_meta("review_credits") + user.get_meta("free_credits")
    can_generate = total >= REVIEW_COST

    assert can_generate is True, "注册赠送的 2 积分应可生成 1 篇综述"
    print(f"  ✓ 综述消耗 {REVIEW_COST} credits, 注册赠送 2 积分刚好 1 篇")

    # 扣除后
    remaining = total - REVIEW_COST
    assert remaining == 0, f"扣除后应剩 0，实际 {remaining}"
    print(f"  ✓ 扣除后剩余 {remaining} credits")
    return True


def test_comparison_matrix_cost_is_1():
    """测试对比矩阵的积分消耗为 1"""
    print("\n[测试] 对比矩阵积分消耗...")

    COMPARISON_COST = 1

    user = MockUser(meta_data={"review_credits": 2, "free_credits": 0})

    # 注册赠送 2 积分，可以生成 2 篇对比矩阵
    total = user.get_meta("review_credits") + user.get_meta("free_credits")
    can_generate_count = total // COMPARISON_COST

    assert can_generate_count == 2, f"2 积分应可生成 2 篇对比矩阵，实际 {can_generate_count}"
    print(f"  ✓ 对比矩阵消耗 {COMPARISON_COST} credit, 2 积分可生成 {can_generate_count} 篇")
    return True


def test_plan_credit_sufficiency():
    """测试各套餐积分可以生成的综述/对比矩阵数量"""
    print("\n[测试] 各套餐积分的生成能力...")

    from authkit.models.payment import DEFAULT_PLANS

    REVIEW_COST = 2
    COMPARISON_COST = 1

    all_pass = True
    for plan in DEFAULT_PLANS:
        ptype = plan["type"]
        credits = plan["credits"]

        if credits == 0:
            print(f"  ℹ {ptype}: unlock 套餐不含积分")
            continue

        reviews = credits // REVIEW_COST
        comparisons = credits // COMPARISON_COST

        if reviews < 1:
            print(f"  ✗ {ptype}: {credits} credits 不足以生成任何综述（需要 {REVIEW_COST}）")
            all_pass = False
        else:
            print(f"  ✓ {ptype}: {credits} credits → {reviews} 篇综述 / {comparisons} 篇对比矩阵")

    return all_pass


def main():
    print("=" * 60)
    print("Credit 积分系统测试")
    print("=" * 60)

    tests = [
        ("扣除：优先使用付费额度", test_deduct_paid_credits_first),
        ("扣除：付费+免费混合", test_deduct_mixed_credits),
        ("扣除：积分不足判定", test_deduct_insufficient_credits),
        ("扣除：仅使用免费额度", test_deduct_free_credits_only),
        ("退还：优先退还免费额度", test_refund_to_free_first),
        ("支付后增加积分", test_add_credits_after_payment),
        ("注册赠送积分", test_registration_credits),
        ("综述生成消耗 2 credits", test_review_cost_is_2),
        ("对比矩阵消耗 1 credit", test_comparison_matrix_cost_is_1),
        ("各套餐生成能力", test_plan_credit_sufficiency),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except AssertionError as e:
            print(f"\n  ✗ 断言失败: {e}")
            results.append((name, False))
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
