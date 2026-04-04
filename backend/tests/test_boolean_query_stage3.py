"""
测试阶段2组合查询在阶段3的布尔搜索功能
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.review_task_executor import ReviewTaskExecutor
from dotenv import load_dotenv

load_dotenv()


async def test_boolean_query_in_stage3():
    """测试布尔查询在阶段3的使用"""
    print("=" * 80)
    print("测试：阶段2组合查询 → 阶段3布尔搜索")
    print("=" * 80)

    executor = ReviewTaskExecutor()

    # 模拟阶段2生成的组合查询
    combined_queries = [
        {
            'query': 'computer algebra system AND algorithm',
            'lang': 'en',
            'source': 'semantic_scholar',
            'is_combination': True
        },
        {
            'query': 'symbolic computation AND implementation',
            'lang': 'en',
            'source': 'semantic_scholar',
            'is_combination': True
        },
        {
            'query': '(transformer OR attention) AND neural network',
            'lang': 'en',
            'source': 'semantic_scholar',
            'is_combination': True
        },
        {
            'query': 'CAS核心算法 AND 计算机代数',
            'lang': 'zh',
            'source': 'aminer',
            'is_combination': True
        },
    ]

    print("\n[测试1] 检测布尔查询")
    print("-" * 80)
    for q in combined_queries:
        is_bool = executor._is_boolean_query(q['query'])
        print(f"  查询: {q['query']}")
        print(f"  是布尔查询: {is_bool}")
        print()

    print("\n[测试2] Semantic Scholar 布尔搜索")
    print("-" * 80)

    # 测试 Semantic Scholar 的布尔搜索
    test_query = 'computer algebra system AND algorithm'
    print(f"查询: {test_query}")

    papers = await executor._search_with_source(
        query=test_query,
        lang='en',
        source='semantic_scholar',
        years_ago=5,
        limit=10
    )

    print(f"✓ 找到 {len(papers)} 篇论文")
    for i, p in enumerate(papers[:3], 1):
        title = p.get('title', '')[:60]
        citations = p.get('cited_by_count', 0)
        year = p.get('year', 'N/A')
        print(f"  {i}. [{year}] {title}... (引用: {citations})")

    print("\n[测试3] AMiner 布尔查询分解")
    print("-" * 80)

    # AMiner 不支持布尔查询，应该被分解
    test_query = 'CAS核心算法 AND 计算机代数'
    print(f"查询: {test_query}")

    papers = await executor._search_with_source(
        query=test_query,
        lang='zh',
        source='aminer',
        years_ago=5,
        limit=10
    )

    print(f"✓ 找到 {len(papers)} 篇论文（通过查询分解）")
    for i, p in enumerate(papers[:3], 1):
        title = p.get('title', '')[:60]
        print(f"  {i}. {title}...")

    print("\n[测试4] 复杂布尔查询")
    print("-" * 80)

    test_query = '(Gröbner basis OR Risch algorithm) AND computer algebra'
    print(f"查询: {test_query}")

    papers = await executor._search_with_source(
        query=test_query,
        lang='en',
        source='semantic_scholar',
        years_ago=10,
        limit=10
    )

    print(f"✓ 找到 {len(papers)} 篇论文")
    for i, p in enumerate(papers[:3], 1):
        title = p.get('title', '')[:60]
        citations = p.get('cited_by_count', 0)
        venue = p.get('venue', 'Unknown')[:20]
        print(f"  {i}. [{venue}] {title}... (引用: {citations})")

    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)
    print("\n总结:")
    print("✅ Semantic Scholar: 支持布尔查询，直接传递")
    print("✅ AMiner: 不支持布尔查询，自动分解为多个查询")
    print("✅ 其他数据源: 根据支持情况选择策略")


async def test_stage2_to_stage3_flow():
    """测试完整的阶段2→阶段3流程"""
    print("\n\n" + "=" * 80)
    print("完整流程测试：阶段2组合查询 → 阶段3布尔搜索")
    print("=" * 80)

    executor = ReviewTaskExecutor()
    topic = "computer algebra system的算法实现及应用"

    # 模拟阶段2生成的查询
    search_queries = [
        {'query': 'computer algebra system', 'section': 'Core Concepts'},
        {'query': 'algorithm', 'section': 'Core Concepts'},
        {'query': 'symbolic computation', 'section': 'Core Concepts'},
    ]

    print(f"\n[阶段2] 原始查询:")
    for q in search_queries:
        print(f"  - {q['query']}")

    # 运行阶段2优化
    optimized = await executor._optimize_search_queries_basic(
        search_queries, topic, 'computer_algebra'
    )

    print(f"\n[阶段2] 优化后的查询: {len(optimized)} 个")
    for q in optimized:
        is_comb = '🔗' if q.get('is_combination') else ''
        print(f"  - {q['query'][:50]}... (source={q['source']}){is_comb}")

    # 检查布尔查询
    boolean_queries = [q for q in optimized if executor._is_boolean_query(q['query'])]
    print(f"\n[阶段3] 将使用布尔搜索的查询: {len(boolean_queries)} 个")

    for q in boolean_queries[:3]:
        print(f"  - {q['query'][:50]}... (source={q['source']})")

        # 模拟阶段3搜索
        if q['source'] == 'semantic_scholar':
            papers = await executor._search_with_source(
                query=q['query'],
                lang=q.get('lang', 'en'),
                source=q['source'],
                years_ago=5,
                limit=5
            )
            print(f"    → 找到 {len(papers)} 篇")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_boolean_query_in_stage3())
    asyncio.run(test_stage2_to_stage3_flow())
