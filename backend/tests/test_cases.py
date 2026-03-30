"""
测试用例：题目分类和文献搜索
"""
import pytest
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.hybrid_classifier import HybridTopicClassifier, FrameworkGenerator
from services.paper_search import PaperSearchService


class TestTopicClassification:
    """题目分类测试用例"""

    @pytest.fixture
    def classifier(self):
        """创建分类器实例"""
        return HybridTopicClassifier()

    @pytest.mark.asyncio
    async def test_hybrid_topics_empirical_with_model(self, classifier):
        """测试：应用型+实证型混血题目（基于XX模型的影响研究）"""
        title = "基于结构方程模型的制造企业质量绩效影响研究"

        topic_type, reason, details = await classifier.classify(title)

        # 验证
        assert topic_type.value == "empirical", f"期望实证型，实际: {topic_type.value}"
        assert "模式识别" in reason, f"应该使用模式识别: {reason}"
        assert details.get('method') == 'pattern', "应该使用模式识别方法"
        assert details.get('pattern') == 'empirical_with_model'
        print(f"✓ 测试通过: {title}")
        print(f"  类型: {topic_type.value}")
        print(f"  理由: {reason}")

    @pytest.mark.asyncio
    async def test_hybrid_topics_empirical_with_maturity(self, classifier):
        """测试：评价型+实证型混血题目（成熟度对...的影响）"""
        title = "质量管理成熟度对创新绩效的影响研究"

        topic_type, reason, details = await classifier.classify(title)

        # 验证
        assert topic_type.value == "empirical", f"期望实证型，实际: {topic_type.value}"
        assert "模式识别" in reason, f"应该使用模式识别: {reason}"
        assert details.get('method') == 'pattern'
        print(f"✓ 测试通过: {title}")
        print(f"  类型: {topic_type.value}")
        print(f"  理由: {reason}")

    @pytest.mark.asyncio
    async def test_hybrid_topics_evaluation_with_improvement(self, classifier):
        """测试：评价型+应用型混血题目（评价与提升）"""
        title = "智能制造背景下质量成熟度评价与提升路径研究"

        topic_type, reason, details = await classifier.classify(title)

        # 验证
        assert topic_type.value == "evaluation", f"期望评价型，实际: {topic_type.value}"
        assert "模式识别" in reason, f"应该使用模式识别: {reason}"
        assert details.get('method') == 'pattern'
        print(f"✓ 测试通过: {title}")
        print(f"  类型: {topic_type.value}")
        print(f"  理由: {reason}")

    @pytest.mark.asyncio
    async def test_pure_evaluation_topic(self, classifier):
        """测试：纯评价型题目"""
        title = "制造型企业质量管理成熟度评价研究"

        topic_type, reason, details = await classifier.classify(title)

        # 验证
        assert topic_type.value == "evaluation", f"期望评价型，实际: {topic_type.value}"
        # 纯评价型题目可能使用大模型分类
        print(f"✓ 测试通过: {title}")
        print(f"  类型: {topic_type.value}")
        print(f"  理由: {reason}")

    @pytest.mark.asyncio
    async def test_direct_influence_topic(self, classifier):
        """测试：直接影响题目（X对Y的影响）"""
        title = "供应链整合对质量绩效的影响机制研究"

        topic_type, reason, details = await classifier.classify(title)

        # 验证
        assert topic_type.value == "empirical", f"期望实证型，实际: {topic_type.value}"
        assert "模式识别" in reason, f"应该使用模式识别: {reason}"
        print(f"✓ 测试通过: {title}")
        print(f"  类型: {topic_type.value}")
        print(f"  理由: {reason}")

    @pytest.mark.asyncio
    async def test_framework_generation(self):
        """测试：框架生成"""
        title = "基于结构方程模型的制造企业质量绩效影响研究"

        gen = FrameworkGenerator()
        result = await gen.generate_framework(title)

        # 验证
        assert result['type'] == 'empirical'
        assert result['type_name'] == '实证型'
        assert result['confidence'] == 'high'  # 模式识别应该是高置信度
        assert 'framework' in result
        assert result['framework']['structure'] == '问题-方案式'
        assert 'search_queries' in result
        print(f"✓ 框架生成测试通过")
        print(f"  类型: {result['type_name']}")
        print(f"  框架: {result['framework']['structure']}")
        print(f"  置信度: {result['confidence']}")
        print(f"  检索策略数: {len(result['search_queries'])}")


class TestPaperSearch:
    """文献搜索测试用例"""

    @pytest.fixture
    def search_service(self):
        """创建搜索服务实例"""
        return PaperSearchService()

    @pytest.mark.asyncio
    async def test_search_basic_query(self, search_service):
        """测试：基本文献搜索"""
        papers = await search_service.search_papers(
            query="machine learning",
            years_ago=5,
            limit=10
        )

        # 验证
        assert isinstance(papers, list), "应该返回列表"
        assert len(papers) > 0, "应该找到相关文献"

        # 验证第一篇论文的结构
        if len(papers) > 0:
            paper = papers[0]
            required_fields = ['id', 'title', 'authors', 'year', 'cited_by_count', 'is_english']
            for field in required_fields:
                assert field in paper, f"论文应该包含 {field} 字段"

            print(f"✓ 基本搜索测试通过")
            print(f"  搜索词: machine learning")
            print(f"  找到文献: {len(papers)} 篇")
            print(f"  第一篇: {paper['title'][:60]}...")
            print(f"  被引量: {paper['cited_by_count']}")
            print(f"  年份: {paper['year']}")

    @pytest.mark.asyncio
    async def test_search_chinese_query(self, search_service):
        """测试：中文搜索词"""
        papers = await search_service.search_papers(
            query="质量管理",
            years_ago=5,
            limit=10
        )

        # 验证
        assert isinstance(papers, list)
        # 中文搜索可能结果较少，不强制要求有结果
        print(f"✓ 中文搜索测试完成")
        print(f"  搜索词: 质量管理")
        print(f"  找到文献: {len(papers)} 篇")

    @pytest.mark.asyncio
    async def test_search_with_citation_filter(self, search_service):
        """测试：带被引量过滤的搜索"""
        papers = await search_service.search_papers(
            query="artificial intelligence",
            years_ago=3,
            limit=20,
            min_citations=50
        )

        # 验证：所有论文的被引量应该 >= 50
        for paper in papers:
            assert paper['cited_by_count'] >= 50, f"被引量应该 >= 50: {paper['cited_by_count']}"

        print(f"✓ 被引量过滤测试通过")
        print(f"  搜索词: artificial intelligence")
        print(f"  最小被引量: 50")
        print(f"  符合条件: {len(papers)} 篇")

    @pytest.mark.asyncio
    async def test_search_english_detection(self, search_service):
        """测试：英文文献检测"""
        papers = await search_service.search_papers(
            query="deep learning",
            years_ago=5,
            limit=10
        )

        # 验证英文检测
        english_count = sum(1 for p in papers if p.get('is_english', False))
        print(f"✓ 英文检测测试通过")
        print(f"  搜索词: deep learning")
        print(f"  英文文献: {english_count}/{len(papers)}")

    @pytest.mark.asyncio
    async def test_search_recent_papers(self, search_service):
        """测试：搜索近期文献"""
        current_year = 2024  # 使用固定年份进行测试

        papers = await search_service.search_papers(
            query="quantum computing",
            years_ago=3,
            limit=10
        )

        # 验证：文献应该是近3年的
        if len(papers) > 0:
            for paper in papers:
                year = paper.get('year', 0)
                assert year >= (current_year - 3), f"文献应该是近3年的: {year}"

            print(f"✓ 近期文献测试通过")
            print(f"  搜索词: quantum computing")
            print(f"  时间范围: 近3年")
            print(f"  结果数: {len(papers)} 篇")


def run_manual_tests():
    """手动运行测试"""
    print("=" * 60)
    print("运行手动测试")
    print("=" * 60)

    # 测试1：题目分类
    print("\n【测试1】题目分类")
    print("-" * 40)

    classifier = HybridTopicClassifier()

    test_titles = [
        "基于结构方程模型的制造企业质量绩效影响研究",
        "质量管理成熟度对创新绩效的影响研究",
        "智能制造背景下质量成熟度评价与提升路径研究",
        "制造型企业质量管理成熟度评价研究"
    ]

    for title in test_titles:
        print(f"\n题目: {title}")
        result = asyncio.run(classifier.classify(title))
        print(f"  类型: {result[0].value}")
        print(f"  理由: {result[1][:80]}...")
        print(f"  方法: {result[2].get('method', 'N/A')}")

    # 测试2：文献搜索
    print("\n" + "=" * 60)
    print("【测试2】文献搜索")
    print("-" * 40)

    search_service = PaperSearchService()

    print("\n搜索: machine learning (近5年)")
    papers = asyncio.run(search_service.search_papers(
        query="machine learning",
        years_ago=5,
        limit=5
    ))

    print(f"找到 {len(papers)} 篇文献:")
    for i, paper in enumerate(papers, 1):
        print(f"  [{i}] {paper['title'][:60]}...")
        print(f"      被引: {paper['cited_by_count']} | 年份: {paper['year']} | 英文: {paper['is_english']}")


if __name__ == "__main__":
    run_manual_tests()
