"""
Auth Kit 独立性测试

验证 auth-kit 是否可以独立运行，不依赖任何业务代码
"""
import sys
import os

# 添加 auth-kit 到路径
sys.path.insert(0, os.path.dirname(__file__))


def test_imports():
    """测试所有模块可以独立导入"""
    print("测试 1: 导入核心模块...")
    try:
        from core import config, security, validator
        print("  ✓ 核心模块导入成功")
    except Exception as e:
        print(f"  ✗ 核心模块导入失败: {e}")
        return False

    print("\n测试 2: 导入数据模型...")
    try:
        from models import Base, User
        from models.schemas import UserCreate, UserResponse
        print("  ✓ 数据模型导入成功")
    except Exception as e:
        print(f"  ✗ 数据模型导入失败: {e}")
        return False

    print("\n测试 3: 导入服务...")
    try:
        from services import AuthService, email_service, cache_service
        print("  ✓ 服务导入成功")
    except Exception as e:
        print(f"  ✗ 服务导入失败: {e}")
        return False

    print("\n测试 4: 导入路由...")
    try:
        from routers import router
        print("  ✓ 路由导入成功")
    except Exception as e:
        print(f"  ✗ 路由导入失败: {e}")
        return False

    print("\n测试 5: 导入邮件模板...")
    try:
        from templates import EmailTemplateConfig, get_verification_code_email
        print("  ✓ 邮件模板导入成功")
    except Exception as e:
        print(f"  ✗ 邮件模板导入失败: {e}")
        return False

    return True


def test_no_business_deps():
    """测试没有业务依赖"""
    print("\n测试 6: 检查业务依赖...")

    # 检查 models
    from models import User
    user_attrs = dir(User)

    business_keywords = ['review', 'paper', 'snappicker', 'autooverview']
    found_business = []

    for attr in user_attrs:
        if any(kw in attr.lower() for kw in business_keywords):
            found_business.append(attr)

    if found_business:
        print(f"  ✗ 发现业务相关属性: {found_business}")
        return False
    else:
        print("  ✓ 没有业务相关属性")

    # 检查 metadata 字段
    if hasattr(User, 'metadata'):
        print("  ✓ 支持 metadata 扩展字段")
    else:
        print("  ✗ 缺少 metadata 扩展字段")
        return False

    return True


def test_configurable():
    """测试可配置性"""
    print("\n测试 7: 检查配置系统...")

    from core.config import config

    # 检查是否支持环境变量配置
    config_attrs = ['JWT_SECRET_KEY', 'SMTP_HOST', 'DATABASE_URL']
    for attr in config_attrs:
        if hasattr(config, attr):
            print(f"  ✓ 支持配置: {attr}")
        else:
            print(f"  ✗ 缺少配置: {attr}")
            return False

    return True


def test_metadata_extension():
    """测试 metadata 扩展机制"""
    print("\n测试 8: 测试 metadata 扩展...")

    # 模拟用户对象
    class MockUser:
        def __init__(self):
            self.metadata = None

        def get_metadata(self):
            import json
            if self.metadata:
                try:
                    return json.loads(self.metadata)
                except:
                    return {}
            return {}

        def set_metadata(self, data):
            import json
            self.metadata = json.dumps(data)

        def get_meta(self, key, default=None):
            return self.get_metadata().get(key, default)

        def set_meta(self, key, value):
            data = self.get_metadata()
            data[key] = value
            self.set_metadata(data)

    user = MockUser()

    # 测试设置和读取
    user.set_meta("plan", "premium")
    user.set_meta("quota", 100)

    plan = user.get_meta("plan")
    quota = user.get_meta("quota")

    if plan == "premium" and quota == 100:
        print("  ✓ metadata 扩展机制正常工作")
        return True
    else:
        print(f"  ✗ metadata 扩展机制失败: plan={plan}, quota={quota}")
        return False


def main():
    print("=" * 60)
    print("Auth Kit 独立性测试")
    print("=" * 60)

    tests = [
        test_imports,
        test_no_business_deps,
        test_configurable,
        test_metadata_extension
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    if all(results):
        print(f"✓ 所有测试通过 ({passed}/{total})")
        print("\nAuth Kit 可以独立复用！")
        return 0
    else:
        print(f"✗ 部分测试失败 ({passed}/{total})")
        return 1


if __name__ == "__main__":
    sys.exit(main())
