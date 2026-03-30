"""
测试用例：文献筛选与排序
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.paper_search import PaperSearchService
from services.paper_filter import PaperFilterService


class TestPaperFilter:
    """文献筛选与排序测试用例"""

    @pytest.fixture
    async def sample_papers(self):
        """创建测试用文献样本"""
        search_service = PaperSearchService()

        # 搜索一些论文作为测试数据
        papers = await search_service.search_papers(
            query="machine learning",
            years_ago=10,
            limit=100
        )

        return papers

    def test_filter_paper_count(self, sample_papers):
        """测试：筛选到指定数量的文献（50篇）"""
        filter_service = PaperFilterService()

        filtered = filter_service.filter_and_sort(
            papers=sample_papers,
            target_count=50,
            recent_years_ratio=0.5,
            english_ratio=0.3
        )

        # 验证
        assert len(filtered) == 50, f"应该筛选到50篇文献，实际: {len(filtered)}"
        print(f"✓ 筛选数量测试通过")
        print(f"  原始文献: {len(sample_papers)} 篇")
        print(f"  筛选后: {len(filtered)} 篇")

    def test_recent_years_ratio(self, sample_papers):
        """测试：近5年文献占比 ≥ 50%"""
        filter_service = PaperFilterService()

        filtered = filter_service.filter_and_sort(
            papers=sample_papers,
            target_count=50,
            recent_years_ratio=0.5,
            english_ratio=0.3
        )

        # 计算近5年文献数量
        current_year = 2024
        recent_threshold = current_year - 5
        recent_count = sum(1 for p in filtered if p.get('year', 0) >= recent_threshold)
        recent_ratio = recent_count / len(filtered) if filtered else 0

        # 验证
        assert recent_ratio >= 0.5, f"近5年文献占比应该 ≥ 50%，实际: {recent_ratio:.2%}"
        print(f"✓ 近5年占比测试通过")
        print(f"  近5年文献: {recent_count}/{len(filtered)} ({recent_ratio:.1%})")

    def test_english_ratio(self, sample_papers):
        """测试：英文文献占比 ≥ 30%"""
        filter_service = PaperFilterService()

        filtered = filter_service.filter_and_sort(
            papers=sample_papers,
            target_count=50,
            recent_years_ratio=0.5,
            english_ratio=0.3
        )

        # 计算英文文献数量
        english_count = sum(1 for p in filtered if p.get('is_english', False))
        english_ratio = english_count / len(filtered) if filtered else 0

        # 验证
        assert english_ratio >= 0.3, f"英文文献占比应该 ≥ 30%，实际: {english_ratio:.2%}"
        print(f"✓ 英文占比测试通过")
        print(f"  英文文献: {english_count}/{len(filtered)} ({english_ratio:.1%})")

    def test_sorted_by_citations(self, sample_papers):
        """测试：按被引量降序排序"""
        filter_service = PaperFilterService()

        filtered = filter_service.filter_and_sort(
            papers=sample_papers,
            target_count=50,
            recent_years_ratio=0.5,
            english_ratio=0.3
        )

        # 验证排序
        for i in range(len(filtered) - 1):
            current = filtered[i].get('cited_by_count', 0)
            next_paper = filtered[i + 1].get('cited_by_count', 0)
            assert current >= next_paper, f"文献应该按被引量降序排序: [{i}]{current} < [{i+1}]{next_paper}"

        print(f"✓ 排序测试通过")
        print(f"  最高被引: {filtered[0].get('cited_by_count', 0)}")
        print(f"  最低被引: {filtered[-1].get('cited_by_count', 0)}")

    def test_statistics_generation(self, sample_papers):
        """测试：统计信息生成"""
        filter_service = PaperFilterService()

        filtered = filter_service.filter_and_sort(
            papers=sample_papers,
            target_count=50,
            recent_years_ratio=0.5,
            english_ratio=0.3
        )

        stats = filter_service.get_statistics(filtered)

        # 验证统计信息
        assert 'total' in stats
        assert 'recent_count' in stats
        assert 'recent_ratio' in stats
        assert 'english_count' in stats
        assert 'english_ratio' in stats
        assert 'total_citations' in stats
        assert 'avg_citations' in stats

        print(f"✓ 统计信息测试通过")
        print(f"  总数: {stats['total']}")
        print(f"  近5年: {stats['recent_count']} ({stats['recent_ratio']:.1%})")
        print(f"  英文: {stats['english_count']} ({stats['english_ratio']:.1%})")
        print(f"  总被引: {stats['total_citations']}")
        print(f"  平均被引: {stats['avg_citations']:.1f}")

    def test_insufficient_papers(self):
        """测试：文献不足时的处理"""
        filter_service = PaperFilterService()

        # 创建少量文献（少于50篇）
        small_papers = [
            {
                'id': f'paper_{i}',
                'title': f'Paper {i}',
                'authors': ['Author'],
                'year': 2023,
                'cited_by_count': 100 - i,
                'is_english': True,
                'abstract': 'Abstract',
                'type': 'article',
                'doi': f'10.1234/{i}',
                'concepts': []
            }
            for i in range(10)  # 只有10篇
        ]

        filtered = filter_service.filter_and_sort(
            papers=small_papers,
            target_count=50,
            recent_years_ratio=0.5,
            english_ratio=0.3
        )

        # 验证：应该返回所有可用文献
        assert len(filtered) == 10, f"文献不足时应该返回所有可用文献"
        print(f"✓ 文献不足处理测试通过")
        print(f"  可用文献: 10 篇")
        print(f"  返回文献: {len(filtered)} 篇")

    def test_high_requirements(self):
        """测试：高要求筛选（严格的英文和近期要求）"""
        filter_service = PaperFilterService()

        # 创建混合文献样本
        current_year = 2024
        mixed_papers = [
            {
                'id': f'paper_{i}',
                'title': f'Paper {i}',
                'authors': ['Author'],
                'year': current_year - (i % 10),  # 0-9年前
                'cited_by_count': 100 - i,
                'is_english': i % 2 == 0,  # 50%英文
                'abstract': 'Abstract',
                'type': 'article',
                'doi': f'10.1234/{i}',
                'concepts': []
            }
            for i in range(100)
        ]

        # 高要求：80%近5年，80%英文
        filtered = filter_service.filter_and_sort(
            papers=mixed_papers,
            target_count=30,
            recent_years_ratio=0.8,
            english_ratio=0.8
        )

        # 计算实际比例
        recent_threshold = current_year - 5
        recent_count = sum(1 for p in filtered if p['year'] >= recent_threshold)
        english_count = sum(1 for p in filtered if p['is_english'])

        print(f"✓ 高要求筛选测试完成")
        print(f"  目标: 30篇")
        print(f"  实际: {len(filtered)} 篇")
        print(f"  近5年: {recent_count}/{len(filtered)} ({recent_count/len(filtered):.1%})")
        print(f"  英文: {english_count}/{len(filtered)} ({english_count/len(filtered):.1%})")
        print(f"  注: 文献不足时会放宽限制")


def run_manual_tests():
    """手动运行测试"""
    import asyncio

    print("=" * 60)
    print("文献筛选与排序测试")
    print("=" * 60)

    # 获取测试数据
    async def get_test_data():
        search_service = PaperSearchService()
        return await search_service.search_papers(
            query="machine learning",
            years_ago=10,
            limit=100
        )

    papers = asyncio.run(get_test_data())
    filter_service = PaperFilterService()

    print(f"\n原始文献: {len(papers)} 篇")

    # 执行筛选
    filtered = filter_service.filter_and_sort(
        papers=papers,
        target_count=50,
        recent_years_ratio=0.5,
        english_ratio=0.3
    )

    # 统计信息
    stats = filter_service.get_statistics(filtered)

    print(f"\n筛选结果:")
    print(f"  总数: {len(filtered)} 篇")
    print(f"  近5年: {stats['recent_count']} 篇 ({stats['recent_ratio']:.1%})")
    print(f"  英文: {stats['english_count']} 篇 ({stats['english_ratio']:.1%})")
    print(f"  总被引: {stats['total_citations']}")
    print(f"  平均被引: {stats['avg_citations']:.1f}")

    # 验证排序
    print(f"\n被引量排序验证:")
    print(f"  第1名: {filtered[0]['cited_by_count']} 次")
    print(f"  第10名: {filtered[9]['cited_by_count']} 次")
    print(f"  第50名: {filtered[-1]['cited_by_count']} 次")

    # 验证条件
    assert len(filtered) == 50, "✗ 筛选数量不正确"
    assert stats['recent_ratio'] >= 0.5, "✗ 近5年占比不足"
    assert stats['english_ratio'] >= 0.3, "✗ 英文占比不足"

    print(f"\n✓ 所有验证通过！")


if __name__ == "__main__":
    run_manual_tests()
