"""
测试上下文关键词翻译和搜索结果验证

验证修复方案是否能够解决 CAS 题目的问题
"""
import asyncio
import sys
sys.path.append('/Users/zhancc/Github/PaperOverview/backend')

from services.contextual_keyword_translator import DomainKnowledge, translate_keywords_contextual


async def test_cas_case():
    """测试 CAS 题目"""
    print("=" * 80)
    print("测试用例: CAS (computer algebra system) 的算法、实现及应用")
    print("=" * 80)

    topic = "CAS (computer algebra system) 的算法、实现及应用"
    keywords = ["CAS符号计算算法", "计算机代数系统实现", "符号积分算法"]

    # 1. 测试领域识别
    domain = DomainKnowledge.identify_domain(topic)
    print(f"\n[测试1] 领域识别")
    print(f"  题目: {topic}")
    print(f"  识别领域: {domain}")
    print(f"  预期: computer_algebra")
    print(f"  结果: {'✅ 正确' if domain == 'computer_algebra' else '❌ 错误'}")

    # 2. 测试关键词翻译
    print(f"\n[测试2] 关键词翻译")
    translations = await translate_keywords_contextual(keywords, topic)

    print(f"  原始关键词:")
    for kw in keywords:
        print(f"    - {kw}")

    print(f"\n  翻译结果:")
    for orig, trans in translations.items():
        print(f"    {orig} -> {trans}")

    # 检查翻译是否包含被排除的术语
    domain_info = DomainKnowledge.DOMAINS.get(domain, {})
    exclude_terms = domain_info.get("exclude_terms", [])

    has_excluded = False
    for translated in translations.values():
        for exclude in exclude_terms:
            if exclude in translated.lower():
                print(f"\n  ⚠️  警告: 翻译结果包含排除术语 '{exclude}'")
                has_excluded = True

    if not has_excluded:
        print(f"\n  ✅ 翻译结果不包含排除术语")

    # 3. 模拟搜索结果验证
    print(f"\n[测试3] 搜索结果验证")

    # 模拟两组搜索结果
    wrong_papers = [
        {"title": "SymQEMU: Compilation-based symbolic execution for binaries"},
        {"title": "Accelerating array constraints in symbolic execution"},
        {"title": "Park: accelerating smart contract vulnerability detection via parallel-fork symbolic execution"},
    ]

    correct_papers = [
        {"title": "Symbolic integration algorithms in Computer Algebra Systems"},
        {"title": "Mathematica: A system for doing mathematics by computer"},
        {"title": "Equation solving in Maple: A Computer Algebra System approach"},
    ]

    from services.review_task_executor import ReviewTaskExecutor
    executor = ReviewTaskExecutor()

    print(f"  错误的搜索结果（符号执行相关）:")
    wrong_score = executor._validate_search_relevance(topic, wrong_papers)
    print(f"    相关性得分: {wrong_score:.1%}")
    print(f"    判断: {'❌ 不相关' if wrong_score < 0.3 else '✅ 相关'}")

    print(f"\n  正确的搜索结果（计算机代数系统相关）:")
    correct_score = executor._validate_search_relevance(topic, correct_papers)
    print(f"    相关性得分: {correct_score:.1%}")
    print(f"    判断: {'✅ 相关' if correct_score >= 0.3 else '❌ 不相关'}")

    # 总结
    print(f"\n" + "=" * 80)
    print(f"测试总结:")
    print(f"  1. 领域识别: {'✅ 通过' if domain == 'computer_algebra' else '❌ 失败'}")
    print(f"  2. 关键词翻译: {'✅ 通过' if not has_excluded else '❌ 失败'}")
    print(f"  3. 结果验证:")
    print(f"     - 错误结果被识别: {'✅ 是' if wrong_score < 0.3 else '❌ 否'}")
    print(f"     - 正确结果被接受: {'✅ 是' if correct_score >= 0.3 else '❌ 否'}")
    print(f"=" * 80)


async def test_symbolic_execution_case():
    """测试符号执行题目"""
    print("\n\n" + "=" * 80)
    print("测试用例: 符号执行技术在软件验证中的应用")
    print("=" * 80)

    topic = "符号执行技术在软件验证中的应用"
    keywords = ["符号执行算法", "路径探索策略", "约束求解优化"]

    # 1. 测试领域识别
    domain = DomainKnowledge.identify_domain(topic)
    print(f"\n[测试1] 领域识别")
    print(f"  题目: {topic}")
    print(f"  识别领域: {domain}")
    print(f"  预期: symbolic_execution")
    print(f"  结果: {'✅ 正确' if domain == 'symbolic_execution' else '❌ 错误'}")

    # 2. 测试关键词翻译
    print(f"\n[测试2] 关键词翻译")
    translations = await translate_keywords_contextual(keywords, topic)

    print(f"  原始关键词:")
    for kw in keywords:
        print(f"    - {kw}")

    print(f"\n  翻译结果:")
    for orig, trans in translations.items():
        print(f"    {orig} -> {trans}")


async def main():
    """运行所有测试"""
    await test_cas_case()
    await test_symbolic_execution_case()


if __name__ == "__main__":
    asyncio.run(main())
