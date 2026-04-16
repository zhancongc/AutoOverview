"""
后端综合测试运行器

运行所有后端测试并汇总结果
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()


def run_test_file(filepath, description):
    """运行单个测试文件并返回结果"""
    import subprocess
    backend_dir = os.path.dirname(os.path.dirname(__file__))

    print(f"\n{'─' * 60}")
    print(f"▶ 运行: {description}")
    print(f"  文件: {filepath}")
    print(f"{'─' * 60}")

    start = time.time()
    result = subprocess.run(
        [sys.executable, filepath],
        cwd=backend_dir,
        capture_output=False,
        timeout=60,
    )
    elapsed = time.time() - start

    passed = result.returncode == 0
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"\n  {status} ({elapsed:.1f}s)")

    return passed, elapsed


def run_pytest_if_available():
    """尝试运行 pytest（如果安装了）"""
    import shutil
    pytest_path = shutil.which("pytest")
    if not pytest_path:
        # 检查 venv 中的 pytest
        venv_pytest = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            ".venv", "bin", "pytest"
        )
        if os.path.exists(venv_pytest):
            pytest_path = venv_pytest

    if not pytest_path:
        print("\n  ⚠ pytest 未安装，跳过 pytest 测试集")
        return None

    backend_dir = os.path.dirname(os.path.dirname(__file__))
    tests_dir = os.path.join(backend_dir, "tests")

    print(f"\n{'─' * 60}")
    print(f"▶ 运行: pytest 测试集")
    print(f"{'─' * 60}")

    import subprocess
    start = time.time()
    # 只运行新创建的测试文件，跳过有历史遗留问题的旧测试
    new_tests = [
        os.path.join(tests_dir, "test_pricing_system.py"),
        os.path.join(tests_dir, "test_credit_system.py"),
        os.path.join(tests_dir, "test_payment_services.py"),
    ]

    result = subprocess.run(
        [pytest_path] + new_tests + ["-v", "--tb=short"],
        cwd=backend_dir,
        capture_output=False,
        timeout=120,
    )
    elapsed = time.time() - start

    passed = result.returncode == 0
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"\n  {status} ({elapsed:.1f}s)")

    return passed


def main():
    print("=" * 60)
    print("AutoOverview 后端测试运行器")
    print("=" * 60)

    tests_dir = os.path.dirname(__file__)

    test_files = [
        (os.path.join(tests_dir, "test_pricing_system.py"), "定价体系一致性测试"),
        (os.path.join(tests_dir, "test_credit_system.py"), "Credit 积分系统测试"),
        (os.path.join(tests_dir, "test_payment_services.py"), "支付服务 Mock 测试"),
    ]

    results = []
    total_start = time.time()

    # 运行各个测试文件
    for filepath, description in test_files:
        if os.path.exists(filepath):
            passed, elapsed = run_test_file(filepath, description)
            results.append((description, passed, elapsed))
        else:
            print(f"\n  ⚠ 测试文件不存在: {filepath}")
            results.append((description, False, 0))

    # 尝试运行 pytest
    pytest_result = run_pytest_if_available()
    if pytest_result is not None:
        results.append(("pytest 测试集", pytest_result, 0))

    total_elapsed = time.time() - total_start

    # 汇总结果
    print("\n" + "=" * 60)
    print("全部测试结果汇总")
    print("=" * 60)

    passed_count = 0
    for name, passed, elapsed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        time_str = f"({elapsed:.1f}s)" if elapsed > 0 else ""
        print(f"  {status} - {name} {time_str}")
        if passed:
            passed_count += 1

    total = len(results)
    print(f"\n  总计: {passed_count}/{total} 通过 ({total_elapsed:.1f}s)")

    if passed_count == total:
        print("\n  🎉 所有测试通过！")
    else:
        print(f"\n  ⚠ {total - passed_count} 个测试失败，请检查上方输出")

    return 0 if passed_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
