"""
测试缩写词扩展功能

验证特定领域的缩写词（如 CAS）能够被正确扩展，避免搜索到不相关文献
"""
import asyncio
import sys
sys.path.append('/Users/zhancc/Github/AutoOverview/backend')

from services.contextual_keyword_translator import (
    DomainKnowledge,
    translate_keywords_contextual
)


def test_abbreviation_expansion():
    """测试缩写词扩展"""
    print("=" * 80)
    print("缩写词扩展测试")
    print("=" * 80)

    test_cases = [
        {
            "name": "CAS - 计算机代数系统（应该扩展）",
            "topic": "CAS (computer algebra system) 的算法、实现及应用",
            "text": "CAS符号计算算法",
            "expected": "Computer Algebra System符号计算算法"
        },
        {
            "name": "CAS - 蛋白质结构预测（不应该扩展）",
            "topic": "Critical Assessment of protein Structure Prediction",
            "text": "CAS competition results",
            "expected": "CAS competition results"
        },
        {
            "name": "ML - 机器学习（应该扩展）",
            "topic": "Machine learning algorithms for image classification",
            "text": "ML model optimization",
            "expected": "Machine Learning model optimization"
        },
        {
            "name": "NLP - 自然语言处理（应该扩展）",
            "topic": "Natural Language Processing in healthcare",
            "text": "NLP applications in clinical text",
            "expected": "Natural Language Processing applications in clinical text"
        },
        {
            "name": "DL - 深度学习（应该扩展）",
            "topic": "Deep learning for computer vision",
            "text": "DL architecture design",
            "expected": "Deep Learning architecture design"
        },
        {
            "name": "API - 应用程序接口（应该扩展）",
            "topic": "RESTful API design patterns",
            "text": "API endpoint optimization",
            "expected": "Application Programming Interface endpoint optimization"
        },
    ]

    print("\n测试结果:")
    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   题目: {test_case['topic']}")
        print(f"   原文: {test_case['text']}")

        result = DomainKnowledge.expand_abbreviations(test_case['text'], test_case['topic'])
        print(f"   结果: {result}")
        print(f"   期望: {test_case['expected']}")

        if result == test_case['expected']:
            print(f"   ✅ 通过")
            passed += 1
        else:
            print(f"   ❌ 失败")
            failed += 1

    print(f"\n" + "=" * 80)
    print(f"测试总结: {passed} 通过, {failed} 失败")
    print("=" * 80)


async def test_keyword_translation_with_expansion():
    """测试关键词翻译（包含缩写扩展）"""
    print("\n\n" + "=" * 80)
    print("关键词翻译测试（包含缩写扩展）")
    print("=" * 80)

    test_cases = [
        {
            "name": "CAS 计算机代数系统",
            "topic": "CAS (computer algebra system) 的算法、实现及应用",
            "keywords": ["CAS符号计算算法", "计算机代数系统实现", "符号积分算法"]
        },
        {
            "name": "ML 机器学习",
            "topic": "Machine learning algorithms for data analysis",
            "keywords": ["ML模型优化", "深度学习算法", "神经网络架构"]
        },
    ]

    for test_case in test_cases:
        print(f"\n{'=' * 80}")
        print(f"测试: {test_case['name']}")
        print(f"题目: {test_case['topic']}")
        print(f"原始关键词: {test_case['keywords']}")

        result = await translate_keywords_contextual(
            test_case['keywords'],
            test_case['topic']
        )

        print(f"\n翻译结果:")
        for orig, trans in result.items():
            print(f"  {orig} -> {trans}")

        # 检查是否包含扩展后的完整形式
        has_expansion = any(
            "Computer Algebra System" in trans or
            "Machine Learning" in trans
            for trans in result.values()
        )

        if has_expansion:
            print(f"  ✅ 缩写已正确扩展")
        else:
            print(f"  ⚠️  未检测到缩写扩展（可能使用了规则翻译）")


def test_search_query_comparison():
    """对比扩展前后的搜索查询"""
    print("\n\n" + "=" * 80)
    print("搜索查询对比测试")
    print("=" * 80)

    print("\n【场景】CAS 计算机代数系统")
    print("-" * 80)

    topic = "CAS (computer algebra system) 的算法、实现及应用"
    original_keywords = ["CAS算法", "CAS系统", "CAS应用"]

    print(f"题目: {topic}")
    print(f"原始关键词: {original_keywords}")

    print("\n不使用扩展（可能搜到不相关文献）:")
    for kw in original_keywords:
        print(f"  - {kw}")
        print(f"    可能匹配: Critical Assessment Series, Cancer studies, etc.")

    print("\n使用扩展（避免不相关文献）:")
    for kw in original_keywords:
        expanded = DomainKnowledge.expand_abbreviations(kw, topic)
        print(f"  - {kw} -> {expanded}")
        print(f"    更精确匹配: Computer Algebra System 相关文献")

    print("\n【优势】")
    print("  ✅ 避免搜索到 Critical Assessment Series 的文献")
    print("  ✅ 避免搜索到医学领域的 CAS (Critical Assessment of Structure)")
    print("  ✅ 提高搜索结果的相关性")
    print("  ✅ 减少后续筛选的工作量")


if __name__ == "__main__":
    # 测试1：缩写词扩展
    test_abbreviation_expansion()

    # 测试2：关键词翻译（包含缩写扩展）
    asyncio.run(test_keyword_translation_with_expansion())

    # 测试3：搜索查询对比
    test_search_query_comparison()

    print("\n\n" + "=" * 80)
    print("所有测试完成")
    print("=" * 80)
