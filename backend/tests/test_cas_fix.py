"""
端到端测试：验证 CAS 题目修复方案

测试完整的流程：
1. 领域识别
2. 上下文关键词翻译
3. 搜索结果验证
4. 标题相关性检查
"""
import asyncio
import sys
sys.path.append('/Users/zhancc/Github/PaperOverview/backend')

from services.contextual_keyword_translator import DomainKnowledge, translate_keywords_contextual
from services.title_relevance_checker import batch_check_titles
from services.review_task_executor import ReviewTaskExecutor


async def test_cas_end_to_end():
    """端到端测试 CAS 题目"""
    print("=" * 80)
    print("端到端测试: CAS (computer algebra system) 的算法、实现及应用")
    print("=" * 80)

    topic = "CAS (computer algebra system) 的算法、实现及应用"

    # 模拟搜索到的文献（混合了相关和不相关的）
    simulated_papers = [
        # 不相关的文献（符号执行相关）
        {"id": "1", "title": "SymQEMU: Compilation-based symbolic execution for binaries", "year": 2021, "cited_by_count": 68},
        {"id": "2", "title": "Accelerating array constraints in symbolic execution", "year": 2021, "cited_by_count": 45},
        {"id": "3", "title": "Park: accelerating smart contract vulnerability detection via parallel-fork symbolic execution", "year": 2022, "cited_by_count": 45},
        {"id": "4", "title": "KLEE: symbolic execution engine for LLVM", "year": 2018, "cited_by_count": 120},
        {"id": "5", "title": "Type and interval aware array constraint solving for symbolic execution", "year": 2021, "cited_by_count": 18},

        # 相关的文献（计算机代数系统相关）
        {"id": "6", "title": "Mathematica: A system for doing mathematics by computer", "year": 2020, "cited_by_count": 150},
        {"id": "7", "title": "Symbolic integration algorithms in Computer Algebra Systems", "year": 2019, "cited_by_count": 35},
        {"id": "8", "title": "Equation solving in Maple: A Computer Algebra System approach", "year": 2018, "cited_by_count": 42},
        {"id": "9", "title": "Polynomial factorization in SageMath", "year": 2021, "cited_by_count": 28},

        # 不相关的文献（生物信息学相关）
        {"id": "10", "title": "STRING v11: protein–protein association networks", "year": 2023, "cited_by_count": 89},
        {"id": "11", "title": "Deep learning for protein structure prediction", "year": 2022, "cited_by_count": 256},
    ]

    # 测试1：领域识别
    print("\n[测试1] 领域识别")
    domain = DomainKnowledge.identify_domain(topic)
    print(f"  识别领域: {domain}")
    print(f"  预期: computer_algebra")
    print(f"  结果: {'✅' if domain == 'computer_algebra' else '❌'}")

    # 测试2：上下文关键词翻译
    print("\n[测试2] 上下文关键词翻译")
    keywords = ["CAS符号计算算法", "计算机代数系统实现", "符号积分算法"]
    translations = await translate_keywords_contextual(keywords, topic)

    print(f"  翻译结果:")
    for orig, trans in translations.items():
        print(f"    {orig} -> {trans}")

    # 检查是否包含排除术语
    domain_info = DomainKnowledge.DOMAINS.get(domain, {})
    exclude_terms = domain_info.get("exclude_terms", [])

    has_excluded = any(exclude in trans for exclude in exclude_terms for trans in translations.values())
    print(f"  包含排除术语: {'❌ 是' if has_excluded else '✅ 否'}")

    # 测试3：搜索结果验证
    print("\n[测试3] 搜索结果验证")
    executor = ReviewTaskExecutor()
    relevance_score = executor._validate_search_relevance(topic, simulated_papers)
    print(f"  相关性得分: {relevance_score:.1%}")
    print(f"  判断: {'✅ 相关' if relevance_score >= 0.3 else '❌ 不相关'}")

    # 测试4：标题相关性检查
    print("\n[测试4] 标题相关性检查")
    relevant, irrelevant, uncertain = batch_check_titles(simulated_papers, topic, domain)

    print(f"  明显相关: {len(relevant)} 篇")
    for paper in relevant[:3]:
        print(f"    ✓ {paper['title'][:60]}")

    print(f"\n  明显不相关: {len(irrelevant)} 篇")
    for paper in irrelevant[:3]:
        print(f"    ✗ {paper['title'][:60]}")

    print(f"\n  需要LLM判断: {len(uncertain)} 篇")
    for paper in uncertain[:3]:
        print(f"    ? {paper['title'][:60]}")

    # 计算效率提升
    total_papers = len(simulated_papers)
    llm_papers_needed = len(uncertain)
    saved_papers = total_papers - llm_papers_needed
    efficiency = (saved_papers / total_papers) * 100 if total_papers > 0 else 0

    print(f"\n[效率提升]")
    print(f"  总文献数: {total_papers}")
    print(f"  需要LLM判断: {llm_papers_needed}")
    print(f"  通过标题过滤: {saved_papers}")
    print(f"  效率提升: {efficiency:.1f}%")
    print(f"  API调用节省: ~{saved_papers} 次")

    # 总结
    print(f"\n" + "=" * 80)
    print(f"测试总结:")
    print(f"  1. 领域识别: {'✅ 通过' if domain == 'computer_algebra' else '❌ 失败'}")
    print(f"  2. 关键词翻译: {'✅ 通过' if not has_excluded else '❌ 失败'}")
    print(f"  3. 搜索结果验证: {'✅ 通过' if relevance_score < 0.3 else '❌ 失败'}")
    print(f"  4. 标题相关性检查: {'✅ 通过' if len(irrelevant) > 0 else '❌ 失败'}")
    print(f"  5. 效率提升: {efficiency:.1f}%")
    print(f"=" * 80)

    # 预期行为
    print(f"\n[预期行为]")
    print(f"  - 系统会自动过滤掉 {len(irrelevant)} 篇不相关文献")
    print(f"  - 只对 {len(uncertain)} 篇不确定文献使用 LLM 判断")
    print(f"  - 节省 {saved_papers} 次 API 调用")
    print(f"  - 最终综述将只包含相关的文献")


if __name__ == "__main__":
    asyncio.run(test_cas_end_to_end())
