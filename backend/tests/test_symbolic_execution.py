"""
测试符号执行相关主题的文献生成

用于验证中文关键词翻译修复是否有效
"""
import asyncio
import sys
sys.path.append('/Users/zhancc/Github/PaperOverview/backend')

from services.review_task_executor import ReviewTaskExecutor

async def test_symbolic_execution():
    """测试符号执行主题"""
    executor = ReviewTaskExecutor()

    topic = "Array-Carrying Symbolic Execution for Function Contract Generation"
    params = {
        'target_count': 30,
        'recent_years_ratio': 0.5,
        'english_ratio': 0.5,
        'search_years': 10,
        'max_search_queries': 8,
    }

    print(f"测试主题: {topic}")
    print("=" * 80)

    try:
        # 只测试搜索文献，不生成综述
        result = await executor.search_papers_only(
            topic=topic,
            params=params
        )

        print("\n" + "=" * 80)
        print("搜索结果统计:")
        print(f"  总文献数: {len(result.get('all_papers', []))}")
        print(f"  筛选后文献数: {len(result.get('filtered_papers', []))}")

        # 检查前10篇文献的标题
        all_papers = result.get('all_papers', [])
        if all_papers:
            print(f"\n前10篇文献标题:")
            for i, paper in enumerate(all_papers[:10], 1):
                title = paper.get('title', 'N/A')
                print(f"  {i}. {title}")

                # 检查是否包含相关关键词
                relevant_keywords = ['symbolic', 'execution', 'contract', 'verification', 'program']
                is_relevant = any(kw in title.lower() for kw in relevant_keywords)
                if not is_relevant:
                    print(f"     ⚠️  不相关!")

        # 统计相关文献数量
        relevant_count = 0
        for paper in all_papers:
            title = paper.get('title', '').lower()
            if any(kw in title for kw in ['symbolic', 'execution', 'contract', 'verification']):
                relevant_count += 1

        print(f"\n相关性统计:")
        print(f"  相关文献: {relevant_count}/{len(all_papers)} ({relevant_count/len(all_papers)*100:.1f}%)")

        if relevant_count < len(all_papers) * 0.5:
            print(f"  ⚠️  警告: 相关文献比例低于50%，搜索可能有问题")
        else:
            print(f"  ✅ 相关文献比例正常")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_symbolic_execution())
