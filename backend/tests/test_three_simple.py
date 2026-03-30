"""
手动测试：三圈文献分析
"""
import sys
import asyncio

sys.path.insert(0, '.')

from services.topic_analyzer import TopicAnalyzer, ThreeCirclesReviewGenerator


async def run_tests():
    print("=" * 60)
    print("三圈文献分析测试")
    print("=" * 60)

    analyzer = TopicAnalyzer()

    # 测试1: 题目解析
    print("\n【测试1】题目解析")
    print("-" * 40)

    title = "基于DMAIC的智能座舱软件持续交付流程优化研究"
    analysis = analyzer.analyze_topic(title)

    print(f"题目: {title}")
    print(f"  圈A（研究对象）: {analysis['domain']}")
    print(f"  圈B（优化目标）: {analysis['optimization']}")
    print(f"  圈C（方法论）: {analysis['methodology']}")

    # 测试2: 三圈检索
    print("\n【测试2】三圈文献检索")
    print("-" * 40)

    result = await analyzer.search_three_circles(
        title="基于人工智能的制造业优化研究"
    )

    for circle in result['circles']:
        print(f"圈{circle['circle']}: {circle['name']}")
        print(f"  检索到: {circle['count']} 篇")

    # 测试3: 研究缺口
    print("\n【测试3】研究缺口分析")
    print("-" * 40)

    gap = result['gap_analysis']
    print(f"缺口描述: {gap['gap_description'][:80]}...")
    print(f"研究机会: {gap['research_opportunity'][:80]}...")
    print(f"建议方向:")
    for i, suggestion in enumerate(gap['suggestions'], 1):
        print(f"  {i}. {suggestion}")

    # 测试4: 综述框架
    print("\n【测试4】综述框架")
    print("-" * 40)

    generator = ThreeCirclesReviewGenerator()
    framework_result = await generator.generate(
        title="基于区块链的供应链溯源研究"
    )
    framework = framework_result['review_framework']
    print(f"引言: {framework['introduction']}")
    for section in framework['sections']:
        print(f"- {section['title']}")

    print(f"\n✓ 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(run_tests())
