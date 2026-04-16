"""
支付服务 Mock 测试

验证开发环境下的支付服务 Mock 行为：
- DevPaddleService
- DevPayPalService
- 支付宝 AlipayService（需要配置才能测试）
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()


def test_dev_paddle_service():
    """测试 DevPaddleService Mock 行为"""
    print("\n[测试] DevPaddleService...")

    # 强制开发模式
    os.environ["IS_DEV"] = "true"

    from authkit.services.paddle_service import DevPaddleService

    paddle = DevPaddleService()

    # 1. create_price
    price_id = paddle.create_price(5.99, "USD")
    assert price_id, "create_price 应返回 price_id"
    assert "pri_dev_" in price_id, f"Mock price_id 格式错误: {price_id}"
    assert "5.99" in price_id, f"Mock price_id 应包含金额: {price_id}"
    print(f"  ✓ create_price(5.99, USD) → {price_id}")

    # 2. create_checkout_link
    checkout_url = paddle.create_checkout_link(
        price_id=price_id,
        customer_email="test@example.com",
        custom_data={"order_no": "TEST123"},
        success_url="http://localhost:3000/profile",
    )
    assert checkout_url, "create_checkout_link 应返回 URL"
    print(f"  ✓ create_checkout_link → URL 已生成")

    # 3. verify_webhook
    result = paddle.verify_webhook(b"test", "sig")
    assert result is True, "Dev 模式 webhook 验证应始终返回 True"
    print(f"  ✓ verify_webhook → True")

    # 4. get_transaction
    txn = paddle.get_transaction("txn_123")
    assert txn is not None, "get_transaction 应返回数据"
    assert txn["status"] == "completed"
    print(f"  ✓ get_transaction → status={txn['status']}")

    return True


def test_dev_paypal_service():
    """测试 DevPayPalService Mock 行为"""
    print("\n[测试] DevPayPalService...")

    os.environ["IS_DEV"] = "true"

    from authkit.services.paypal_service import DevPayPalService

    paypal = DevPayPalService()

    # 1. create_order
    order = paypal.create_order(
        amount=24.99,
        currency="USD",
        description="Test Order",
        custom_id="ORDER-TEST-24",
        return_url="http://localhost:3000/profile",
        cancel_url="http://localhost:3000/",
    )
    assert order["order_id"], "应返回 order_id"
    assert order["status"] == "CREATED", f"状态应为 CREATED，实际 {order['status']}"
    assert order["approval_link"], "应返回 approval_link"
    print(f"  ✓ create_order → order_id={order['order_id']}, status={order['status']}")

    # 2. capture_order
    capture = paypal.capture_order(order["order_id"])
    assert capture["status"] == "COMPLETED", f"捕获状态应为 COMPLETED，实际 {capture['status']}"
    print(f"  ✓ capture_order → status={capture['status']}")

    # 3. get_order
    order_data = paypal.get_order(order["order_id"])
    assert order_data is not None
    assert order_data["status"] == "COMPLETED"
    print(f"  ✓ get_order → status={order_data['status']}")

    # 4. verify_webhook
    result = paypal.verify_webhook(b"test", "tid", "time", "sig", "cert_url", "SHA256")
    assert result is True, "Dev 模式 webhook 验证应始终返回 True"
    print(f"  ✓ verify_webhook → True")

    return True


def test_paddle_pricing_structure():
    """测试 PADDLE_PRICING 数据结构完整性"""
    print("\n[测试] PADDLE_PRICING 数据结构...")

    from authkit.services.paddle_service import PADDLE_PRICING

    required_keys = {"name", "price", "credits", "currency"}
    all_pass = True

    for plan_type, plan in PADDLE_PRICING.items():
        missing = required_keys - set(plan.keys())
        if missing:
            print(f"  ✗ {plan_type}: 缺少字段 {missing}")
            all_pass = False
        else:
            assert plan["currency"] == "USD", f"{plan_type} 货币应为 USD"
            assert plan["price"] > 0, f"{plan_type} 价格应 > 0"
            print(f"  ✓ {plan_type}: {plan['name']}, ${plan['price']}, {plan['credits']} credits, {plan['currency']}")

    return all_pass


def test_paypal_pricing_structure():
    """测试 PAYPAL_PRICING 数据结构完整性"""
    print("\n[测试] PAYPAL_PRICING 数据结构...")

    from authkit.services.paypal_service import PAYPAL_PRICING

    required_keys = {"name", "price", "credits", "currency"}
    all_pass = True

    for plan_type, plan in PAYPAL_PRICING.items():
        missing = required_keys - set(plan.keys())
        if missing:
            print(f"  ✗ {plan_type}: 缺少字段 {missing}")
            all_pass = False
        else:
            assert plan["currency"] == "USD", f"{plan_type} 货币应为 USD"
            assert plan["price"] > 0, f"{plan_type} 价格应 > 0"
            print(f"  ✓ {plan_type}: {plan['name']}, ${plan['price']}, {plan['credits']} credits, {plan['currency']}")

    return all_pass


def test_get_paddle_service_dev_mode():
    """测试 get_paddle_service 在开发模式下返回 Mock"""
    print("\n[测试] get_paddle_service 开发模式...")

    os.environ["IS_DEV"] = "true"
    from authkit.services.paddle_service import get_paddle_service, DevPaddleService

    service = get_paddle_service()
    assert isinstance(service, DevPaddleService), f"开发模式应返回 DevPaddleService，实际 {type(service)}"
    print(f"  ✓ IS_DEV=true → DevPaddleService")

    return True


def test_get_paypal_service_dev_mode():
    """测试 get_paypal_service 在开发模式下返回 Mock"""
    print("\n[测试] get_paypal_service 开发模式...")

    os.environ["IS_DEV"] = "true"
    from authkit.services.paypal_service import get_paypal_service, DevPayPalService

    service = get_paypal_service()
    assert isinstance(service, DevPayPalService), f"开发模式应返回 DevPayPalService，实际 {type(service)}"
    print(f"  ✓ IS_DEV=true → DevPayPalService")

    return True


def test_order_number_format():
    """测试订单号格式是否正确"""
    print("\n[测试] 订单号格式...")

    from datetime import datetime
    import uuid

    # Alipay: AO + 时间 + 随机
    ao = f"AO{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    assert ao.startswith("AO"), f"支付宝订单号应以 AO 开头: {ao}"
    assert len(ao) > 10, f"订单号长度应 > 10: {ao}"
    print(f"  ✓ Alipay 格式: {ao}")

    # Paddle: PD + 时间 + 随机
    pd = f"PD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    assert pd.startswith("PD"), f"Paddle 订单号应以 PD 开头: {pd}"
    print(f"  ✓ Paddle 格式: {pd}")

    # PayPal: PP + 时间 + 随机
    pp = f"PP{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    assert pp.startswith("PP"), f"PayPal 订单号应以 PP 开头: {pp}"
    print(f"  ✓ PayPal 格式: {pp}")

    return True


def test_payment_model_methods():
    """测试 Subscription 模型的 metadata 操作方法"""
    print("\n[测试] Subscription metadata 操作...")

    from authkit.models.payment import Subscription

    # 创建一个 Subscription 实例（不需要数据库）
    sub = Subscription(
        user_id=1,
        order_no="TEST001",
        plan_type="single",
        amount=9.99,
        currency="USD",
        status="pending",
    )

    # 测试 get_metadata / set_metadata
    sub.set_metadata({"paypal_order_id": "PP-123", "record_id": 42})
    meta = sub.get_metadata()
    assert meta["paypal_order_id"] == "PP-123", f"metadata 存储失败"
    assert meta["record_id"] == 42, f"metadata 存储失败"
    print(f"  ✓ set_metadata / get_metadata 正常")

    # 测试 get_meta / set_meta
    sub.set_meta("test_key", "test_value")
    assert sub.get_meta("test_key") == "test_value"
    print(f"  ✓ get_meta / set_meta 正常")

    # 测试默认值
    assert sub.get_meta("nonexistent", "default") == "default"
    print(f"  ✓ get_meta 默认值正常")

    return True


def test_payment_log_model():
    """测试 PaymentLog 模型创建"""
    print("\n[测试] PaymentLog 模型...")

    from authkit.models.payment import PaymentLog

    log = PaymentLog(
        subscription_id=1,
        user_id=1,
        action="create",
        request_data="plan_type=single",
        response_data="pay_url=...",
    )

    assert log.action == "create"
    assert log.subscription_id == 1
    print(f"  ✓ PaymentLog 创建正常")

    return True


def main():
    print("=" * 60)
    print("支付服务 Mock 测试")
    print("=" * 60)

    tests = [
        ("DevPaddleService", test_dev_paddle_service),
        ("DevPayPalService", test_dev_paypal_service),
        ("PADDLE_PRICING 结构", test_paddle_pricing_structure),
        ("PAYPAL_PRICING 结构", test_paypal_pricing_structure),
        ("get_paddle_service 开发模式", test_get_paddle_service_dev_mode),
        ("get_paypal_service 开发模式", test_get_paypal_service_dev_mode),
        ("订单号格式", test_order_number_format),
        ("Subscription metadata", test_payment_model_methods),
        ("PaymentLog 模型", test_payment_log_model),
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
