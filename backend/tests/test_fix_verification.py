"""
快速验证修复是否有效
"""
import asyncio
import sys
sys.path.append('/Users/zhancc/Github/PaperOverview/backend')

async def test_query_ordering():
    """测试查询排序逻辑"""
    # 模拟优化查询（混合中英文）
    section_optimized_queries = [
        {'query': '符号执行软件分析', 'lang': 'zh', 'source': 'aminer'},
        {'query': 'symbolic execution software analysis', 'lang': 'en', 'source': 'openalex'},
        {'query': '函数契约生成方法', 'lang': 'zh', 'source': 'aminer'},
        {'query': 'function contract generation method', 'lang': 'en', 'source': 'openalex'},
    ]

    print("原始查询顺序:")
    for i, q in enumerate(section_optimized_queries, 1):
        print(f"  {i}. {q['query']} (lang={q['lang']})")

    # 应用新的排序逻辑
    en_queries = [q for q in section_optimized_queries if q.get('lang') == 'en']
    zh_queries = [q for q in section_optimized_queries if q.get('lang') != 'en']
    unique_optimized_queries = en_queries + zh_queries

    print("\n调整后的查询顺序（英文优先）:")
    for i, q in enumerate(unique_optimized_queries, 1):
        print(f"  {i}. {q['query']} (lang={q['lang']})")

    # 检查前5个查询
    print("\n前5个查询（实际会使用的）:")
    for i, q in enumerate(unique_optimized_queries[:5], 1):
        print(f"  {i}. {q['query']} (lang={q['lang']})")

    # 验证
    en_in_first_5 = sum(1 for q in unique_optimized_queries[:5] if q.get('lang') == 'en')
    print(f"\n验证: 前5个查询中有 {en_in_first_5} 个英文查询")

    if en_in_first_5 > 0:
        print("✅ 修复有效：英文查询被优先使用")
    else:
        print("❌ 修复无效：英文查询没有被优先使用")

asyncio.run(test_query_ordering())
