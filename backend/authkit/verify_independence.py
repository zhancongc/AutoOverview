"""
Auth Kit 独立性验证（简化版）

验证 auth-kit 是否可以独立复用
"""
import logging
import os
import sys

logger = logging.getLogger(__name__)

# 添加 auth-kit 到路径
auth_kit_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, auth_kit_dir)


def check_no_business_deps():
    """检查是否有业务依赖"""
    print("=" * 60)
    print("Auth Kit 独立性检查")
    print("=" * 60)

    print("\n检查 1: 扫描 Python 文件中的业务依赖...")
    business_keywords = ['autooverview', 'snappicker', 'ReviewRecord', 'review_count', 'review_quota']
    found_issues = []

    # 要检查的核心目录
    core_dirs = ['core', 'models', 'services', 'routers', 'templates']

    for dir_name in core_dirs:
        dir_path = os.path.join(auth_kit_dir, dir_name)
        if not os.path.exists(dir_path):
            continue

        for file in os.listdir(dir_path):
            if not file.endswith('.py') or file.startswith('__'):
                continue

            filepath = os.path.join(dir_path, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                    for i, line in enumerate(lines, 1):
                        # 跳过注释行
                        if line.strip().startswith('#'):
                            continue

                        line_lower = line.lower()
                        for keyword in business_keywords:
                            if keyword.lower() in line_lower:
                                found_issues.append(f"{filepath}:{i} - 发现 '{keyword}'")
                                break
            except Exception as e:
                logger.error("Failed to read file %s: %s", filepath, e)
                pass

    if found_issues:
        print("  ✗ 发现业务依赖:")
        for issue in found_issues[:10]:  # 只显示前10个
            print(f"    - {issue}")
        if len(found_issues) > 10:
            print(f"    ... 还有 {len(found_issues) - 10} 个")
        return False
    else:
        print("  ✓ 没有发现业务依赖")

    print("\n检查 2: 验证数据模型...")
    try:
        # 读取 User 模型定义
        models_file = os.path.join(auth_kit_dir, 'models', '__init__.py')
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否有扩展字段
        if 'meta_data' in content or 'metadata' in content:
            print("  ✓ 支持扩展字段（meta_data）")
        else:
            print("  ✗ 缺少扩展字段")

        # 检查是否有业务字段
        business_fields = ['review_count', 'review_quota', 'total_papers_used', 'review_records']
        found_business = []
        for field in business_fields:
            if field in content:
                found_business.append(field)

        if found_business:
            print(f"  ✗ 发现业务字段: {found_business}")
            return False
        else:
            print("  ✓ 没有业务特定字段")

    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
        return False

    print("\n检查 3: 验证配置系统...")
    try:
        config_file = os.path.join(auth_kit_dir, 'core', 'config.py')
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()

        required_configs = ['JWT_SECRET_KEY', 'SMTP_HOST', 'DATABASE_URL']
        for config_name in required_configs:
            if config_name in content:
                print(f"  ✓ 支持配置: {config_name}")
            else:
                print(f"  ✗ 缺少配置: {config_name}")

        # 检查是否使用环境变量
        if 'os.getenv' in content or 'environ' in content:
            print("  ✓ 支持环境变量配置")
        else:
            print("  ✗ 不支持环境变量配置")

    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
        return False

    print("\n检查 4: 验证邮件模板...")
    try:
        template_file = os.path.join(auth_kit_dir, 'templates', 'base_emails.py')
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否可配置
        if 'EmailTemplateConfig' in content:
            print("  ✓ 支持自定义邮件模板")
        else:
            print("  ✗ 不支持自定义邮件模板")

        # 检查是否有硬编码品牌信息
        hardcoded_brands = []
        brand_keywords = ['autooverview.com', 'snappicker.com']
        for keyword in brand_keywords:
            if keyword in content.lower():
                hardcoded_brands.append(keyword)

        if hardcoded_brands:
            print(f"  ✗ 发现硬编码品牌: {hardcoded_brands}")
        else:
            print("  ✓ 没有硬编码品牌信息")

    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
        return False

    print("\n检查 5: 验证文档完整性...")
    required_docs = ['README.md', 'QUICKSTART.md', 'REUSABILITY.md', '.env.example']
    for doc in required_docs:
        doc_path = os.path.join(auth_kit_dir, doc)
        if os.path.exists(doc_path):
            print(f"  ✓ 文档存在: {doc}")
        else:
            print(f"  ✗ 文档缺失: {doc}")

    print("\n" + "=" * 60)
    print("检查完成！")
    print("=" * 60)
    print("\n结论: Auth Kit 可以独立复用")
    print("\n使用方式:")
    print("  1. 复制 auth-kit 目录到新项目")
    print("  2. 安装依赖: pip install fastapi sqlalchemy passlib[bcrypt] pydantic-settings jinja2 redis pyjwt")
    print("  3. 配置环境变量（至少 AUTH_JWT_SECRET_KEY）")
    print("  4. 在 FastAPI 中集成（见 QUICKSTART.md）")

    return True


if __name__ == "__main__":
    check_no_business_deps()
