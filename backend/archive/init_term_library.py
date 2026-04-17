"""
学术术语库初始化脚本

用于：
1. 创建数据库表
2. 导入默认术语数据
3. 验证术语库功能
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from services.academic_term_service import AcademicTermService


def initialize_term_library():
    """初始化术语库"""
    print("=" * 80)
    print("学术术语库初始化")
    print("=" * 80)

    # 1. 连接数据库
    print("\n[步骤 1/3] 连接数据库...")
    db.connect()
    print("[步骤 1/3] ✓ 数据库连接成功")

    # 2. 创建表
    print("\n[步骤 2/3] 创建数据库表...")
    from models import Base
    Base.metadata.create_all(db.engine)
    print("[步骤 2/3] ✓ 数据库表创建完成")

    # 3. 导入默认术语
    print("\n[步骤 3/3] 导入默认术语...")
    term_service = AcademicTermService()
    result = term_service.initialize_default_terms()
    print(f"[步骤 3/3] ✓ 术语导入完成")
    print(f"  - 成功: {result['success']} 条")
    print(f"  - 跳过: {result['skipped']} 条")
    print(f"  - 错误: {result['errors']} 条")
    print(f"  - 总计: {result['total']} 条")

    # 4. 显示统计信息
    print("\n" + "=" * 80)
    print("术语库统计")
    print("=" * 80)

    session_gen = term_service.get_session()
    session = next(session_gen)

    try:
        from services.academic_term_dao import AcademicTermDAO
        dao = AcademicTermDAO(session)
        stats = dao.get_statistics()

        print(f"总术语数: {stats['total']}")
        print(f"分类统计:")
        for category, count in stats.get('categories', {}).items():
            print(f"  - {category}: {count} 条")
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass

    print("\n" + "=" * 80)
    print("初始化完成！")
    print("=" * 80)


def test_term_library():
    """测试术语库功能"""
    print("\n" + "=" * 80)
    print("测试术语库功能")
    print("=" * 80)

    term_service = AcademicTermService()

    # 测试关键词提取
    test_topic = "基于双向长短期记忆网络和卷积神经网络的DNA 6mA甲基化位点预测"
    print(f"\n测试主题: {test_topic}")

    keywords = term_service.search_keywords_from_topic(test_topic)
    print(f"提取的关键词: {keywords}")

    # 测试搜索建议
    print("\n测试术语搜索建议:")
    suggestions = term_service.get_term_suggestions("lstm", limit=5)
    for i, sug in enumerate(suggestions, 1):
        print(f"  {i}. {sug['chinese']} -> {sug['english']}")


if __name__ == "__main__":
    # 初始化术语库
    initialize_term_library()

    # 测试功能
    test_response = input("\n是否测试术语库功能？(y/n): ").strip().lower()
    if test_response == 'y':
        test_term_library()
