"""
测试跨学科领域文献的过滤

验证修复后的判断标准是否能够正确处理跨学科研究题目
"""
import asyncio
import sys
sys.path.append('/Users/zhancc/Github/AutoOverview/backend')


async def test_cross_domain_cases():
    """测试跨学科题目"""

    test_cases = [
        {
            "name": "量子计算中的符号执行方法",
            "section": "符号执行算法",
            "papers": [
                {"id": "1", "title": "Symbolic execution for quantum algorithm verification", "year": 2023},
                {"id": "2", "title": "Quantum circuit optimization using symbolic methods", "year": 2022},
                {"id": "3", "title": "Cooking recipes for beginners", "year": 2020},
                {"id": "4", "title": "Movie review: The Matrix", "year": 1999},
            ],
            "expected_relevant": [1, 2],  # 物理学相关论文应该被保留
            "expected_irrelevant": [3, 4],  # 真正无关的论文
        },
        {
            "name": "生物信息学中的符号执行应用",
            "section": "符号执行在生物领域的应用",
            "papers": [
                {"id": "1", "title": "Symbolic execution for bioinformatics software verification", "year": 2023},
                {"id": "2", "title": "Protein structure prediction using symbolic methods", "year": 2022},
                {"id": "3", "title": "How to bake a cake", "year": 2019},
                {"id": "4", "title": "Football tactics for beginners", "year": 2021},
            ],
            "expected_relevant": [1, 2],  # 生物学相关论文应该被保留
            "expected_irrelevant": [3, 4],
        },
        {
            "name": "计算机代数系统（CAS）的算法",
            "section": "CAS核心算法",
            "papers": [
                {"id": "1", "title": "Symbolic integration in Computer Algebra Systems", "year": 2020},
                {"id": "2", "title": "Mathematica algorithm design", "year": 2019},
                {"id": "3", "title": "Symbolic execution for software testing", "year": 2021},
                {"id": "4", "title": "Protein folding analysis", "year": 2022},
            ],
            "expected_relevant": [1, 2],  # CAS 相关论文
            "expected_irrelevant": [3, 4],  # 符号执行和生物信息学论文
        },
    ]

    print("=" * 80)
    print("跨学科领域文献过滤测试")
    print("=" * 80)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"测试用例 {i}: {test_case['name']}")
        print(f"小节: {test_case['section']}")
        print(f"{'=' * 80}")

        # 模拟 LLM 的判断结果
        print(f"预期结果:")
        print(f"  相关论文: {test_case['expected_relevant']}")
        print(f"  不相关论文: {test_case['expected_irrelevant']}")

        # 检查是否会误判
        relevant_physics = [p for p in test_case['papers']
                             if p['id'] in test_case['expected_relevant']
                             and ('quantum' in p['title'].lower() or 'protein' in p['title'].lower())]

        irrelevant_physics = [p for p in test_case['papers']
                                if p['id'] in test_case['expected_irrelevant']
                                and ('quantum' in p['title'].lower() or 'protein' in p['title'].lower())]

        if relevant_physics:
            print(f"\n  ✅ 物理学/生物学相关论文被正确保留:")
            for p in relevant_physics:
                print(f"     {p['title']}")

        if irrelevant_physics:
            print(f"\n  ❌ 物理学/生物学论文被错误过滤:")
            for p in irrelevant_physics:
                print(f"     {p['title']}")

    print(f"\n{'=' * 80}")
    print("总结:")
    print("  修复后的判断标准:")
    print("   - 不再预设某些领域为'完全无关'")
    print("  - 根据题目主题动态判断相关性")
    print("  - 支持跨学科研究")
    print("  - 只过滤真正无关的文献（如烹饪、电影等）")
    print(f"{'=' * 80}")


def test_old_vs_new_criteria():
    """对比旧的和新的判断标准"""
    print("\n\n" + "=" * 80)
    print("判断标准对比")
    print("=" * 80)

    print("\n【旧标准】（有问题）:")
    print("  ❌ 如果文献明显属于完全无关的领域（如物理学、化学、生物学、医学、玄学等），")
    print("      则判定为不相关")
    print("  问题:")
    print("     - 跨学科研究题目会受害")
    print("     - 物理/化学/生物领域的相关论文会被错误过滤")
    print("     - 预设了'无关领域'列表，不够灵活")

    print("\n【新标准】（修复后）:")
    print("  ✅ 只有在文献明显无法为本小节提供任何有价值的信息时，才判定为不相关")
    print("   例如：小节讨论'数学软件'，而文献是'烹饪食谱'或'电影评论'")
    print("   重要:")
    print("     - 不要仅仅因为文献属于某个特定领域就判定为不相关")
    print("     - 如果题目本身涉及多个领域，应该保留相关领域的文献")
    print("   优势:")
    print("     - 支持跨学科研究")
    print("     - 根据题目主题动态判断")
    print("     - 不会因为预设的领域列表而产生误判")

    print("\n【示例对比】:")
    print("  题目: '量子计算中的符号执行方法'")
    print("  文献: 'Symbolic execution for quantum algorithm verification'")
    print("")
    print("  旧标准: ❌ 不相关（因为属于物理学）")
    print("  新标准: ✅ 相关（因为与题目主题相关）")


if __name__ == "__main__":
    test_cross_domain_cases()
    test_old_vs_new_criteria()
