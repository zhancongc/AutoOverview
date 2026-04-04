"""
测试统计数据提取功能
演示如何从论文中提取OR值、P值等具体数据
"""
import asyncio
from services.statistics_extractor import (
    StatisticsExtractor,
    StatisticsEnhancedCitation,
    EnhancedReviewGenerator,
    extract_statistics_from_papers,
    format_statistics_for_citation
)


# 模拟论文数据（包含真实的统计信息）
MOCK_PAPERS = [
    {
        "id": "1",
        "title": "Media Coverage and Earnings Management: Evidence from Chinese Listed Firms",
        "abstract": "Using a sample of 2,500 firm-year observations, we find that high media coverage is associated with a 35% reduction in earnings management (OR=0.65, 95%CI:0.55-0.75, p<0.001). The effect remains significant after controlling for firm size and governance characteristics.",
        "year": 2020
    },
    {
        "id": "2",
        "title": "QFD Implementation and Product Quality: A Meta-Analysis",
        "abstract": "Our meta-analysis of 45 studies (N=12,500) reveals that QFD implementation significantly improves product quality (Cohen's d=0.68, 95%CI:0.52-0.84, p<0.001). The average quality defect rate decreased from 5.2% to 2.8% following QFD adoption.",
        "year": 2021
    },
    {
        "id": "3",
        "title": "Social Media and Mental Health: A Longitudinal Study",
        "abstract": "In a study of 1,000 adolescents over 3 years, we found that daily social media use >3 hours was associated with increased risk of depression (RR=1.8, 95%CI:1.4-2.3, p=0.002). The incidence of depressive symptoms was 25.5% in high-use group vs 14.2% in low-use group.",
        "year": 2022
    },
    {
        "id": "4",
        "title": "Titanium Dioxide Photocatalytic Degradation of Dyes",
        "abstract": "The TiO2 microspheres showed excellent photocatalytic activity with 95.2% methylene blue degradation within 60 min. The degradation rate constant was 0.045 min^-1 (SD=0.005, n=5), significantly higher than conventional TiO2 nanoparticles (p<0.01).",
        "year": 2023
    },
    {
        "id": "5",
        "title": "Risk Management and Project Success: An Empirical Study",
        "abstract": "Analysis of 200 software projects revealed that formal risk management practices increase project success rate by 42% (from 35% to 71%, p<0.001). The odds ratio for project success with risk management was OR=2.45 (95%CI:1.85-3.24). Each additional risk management process maturity level increased success probability by 15.5% (β=0.155, p=0.003).",
        "year": 2021
    },
]


async def test_statistics_extraction():
    """测试统计数据提取"""
    print("=" * 80)
    print("测试1: 统计数据提取")
    print("=" * 80)

    extractor = StatisticsExtractor()

    for paper in MOCK_PAPERS[:3]:
        print(f"\n论文: {paper['title'][:60]}...")

        # 规则提取
        stats = extractor.extract_statistics_from_text(paper['abstract'])
        print(f"  提取的统计数据:")
        for key, value in stats.items():
            if key not in ['paper_id', 'paper_title']:
                print(f"    {key}: {value}")

        # 格式化为引用
        formatted = extractor.format_statistics_for_citation(stats, "compact")
        print(f"  引用格式: {formatted}")


async def test_llm_extraction():
    """测试LLM增强提取"""
    print("\n" + "=" * 80)
    print("测试2: LLM增强提取")
    print("=" * 80)

    import os
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("\n⚠️  DEEPSEEK_API_KEY 未配置，跳过LLM测试\n")
        return

    extractor = StatisticsExtractor()

    paper = MOCK_PAPERS[0]  # 使用第一篇论文

    print(f"\n论文: {paper['title'][:60]}...")

    stats = await extractor.extract_statistics_with_llm(paper)

    print(f"  LLM提取的统计数据:")
    for key, value in stats.items():
        if key not in ['paper_id', 'paper_title'] and value:
            print(f"    {key}: {value}")


async def test_enhanced_citation():
    """测试增强引用生成"""
    print("\n" + "=" * 80)
    print("测试3: 增强引用生成")
    print("=" * 80)

    citation_gen = StatisticsEnhancedCitation()

    for i, paper in enumerate(MOCK_PAPERS, 1):
        print(f"\n论文{i}: {paper['title'][:50]}...")

        # 先提取统计数据
        extractor = StatisticsExtractor()
        stats = extractor.extract_statistics_from_text(paper['abstract'])
        paper['statistics'] = stats

        # 生成增强引用
        citation = await citation_gen.generate_enhanced_citation(paper, i, style="compact", use_llm=False)
        print(f"  增强引用: {citation}")

        # 生成带上下文的引用
        example_finding = "研究发现"
        full_citation = citation_gen.format_citation_with_context(
            paper, example_finding, i, include_statistics=True
        )
        print(f"  完整引用: {full_citation}")


async def test_batch_extraction():
    """测试批量提取"""
    print("\n" + "=" * 80)
    print("测试4: 批量提取")
    print("=" * 80)

    papers_with_stats = await extract_statistics_from_papers(MOCK_PAPERS, use_llm=False)

    print(f"\n批量提取完成，共 {len(papers_with_stats)} 篇论文")

    # 统计提取结果
    stats_count = {}
    for paper in papers_with_stats:
        stats = paper.get("statistics", {})
        for key in stats.keys():
            if key not in ['paper_id', 'paper_title']:
                stats_count[key] = stats_count.get(key, 0) + 1

    print(f"\n提取统计:")
    for key, count in sorted(stats_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {key}: {count} 篇")

    # 展示前3篇的统计数据
    print(f"\n前3篇论文的统计数据:")
    for i, paper in enumerate(papers_with_stats[:3], 1):
        print(f"\n{i}. {paper['title'][:50]}...")
        stats = paper.get("statistics", {})
        formatted = format_statistics_for_citation(stats, "compact")
        print(f"   {formatted if formatted else '(无统计数据)'}")


async def test_review_generation():
    """测试带统计数据的综述生成"""
    print("\n" + "=" * 80)
    print("测试5: 带统计数据的综述生成")
    print("=" * 80)

    import os
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("\n⚠️  DEEPSEEK_API_KEY 未配置，跳过LLM生成测试\n")
        return

    generator = EnhancedReviewGenerator()

    topic = "媒体关注与盈余管理"
    papers = MOCK_PAPERS[:3]  # 使用前3篇论文

    review, papers_with_stats = await generator.generate_review_with_statistics(
        topic=topic,
        papers=papers,
        model="deepseek-chat"
    )

    print(f"\n生成的综述（{len(review)} 字符）:")
    print("-" * 80)
    print(review)
    print("-" * 80)


async def test_citation_formats():
    """测试不同引用格式"""
    print("\n" + "=" * 80)
    print("测试6: 不同引用格式")
    print("=" * 80)

    extractor = StatisticsExtractor()

    # 示例统计数据
    example_stats = {
        "or": 1.5,
        "or_ci_lower": 1.2,
        "or_ci_upper": 1.8,
        "p": 0.03,
        "n": 500
    }

    print(f"\n示例统计数据: OR=1.5, 95%CI:1.2-1.8, p=0.03, n=500\n")

    styles = ["compact", "detailed", "apa"]

    for style in styles:
        formatted = extractor.format_statistics_for_citation(example_stats, style)
        print(f"{style.upper()}: [1]{formatted}")


async def demo_practical_usage():
    """演示实际使用场景"""
    print("\n" + "=" * 80)
    print("演示: 实际使用场景")
    print("=" * 80)

    print("\n场景：在综述中引用具体数据\n")

    citation_gen = StatisticsEnhancedCitation()
    extractor = StatisticsExtractor()

    # 示例：风险管理论文
    risk_paper = MOCK_PAPERS[4]

    # 提取统计数据
    stats = extractor.extract_statistics_from_text(risk_paper['abstract'])
    risk_paper['statistics'] = stats

    print(f"论文: {risk_paper['title']}")
    print(f"摘要: {risk_paper['abstract'][:100]}...")

    # 展示如何在综述中引用
    print(f"\n在综述中的引用方式:\n")

    # 方式1：简单引用（无数据）
    print(f"❌ 普通引用: 研究发现正式的风险管理实践能提高项目成功率[5]")

    # 方式2：带统计数据的引用
    citation = await citation_gen.generate_enhanced_citation(risk_paper, 5, style="compact", use_llm=False)
    print(f"✅ 增强引用: 研究发现正式的风险管理实践能提高项目成功率{citation}")

    # 方式3：带完整上下文的引用
    full_citation = citation_gen.format_citation_with_context(
        risk_paper,
        "正式的风险管理实践使项目成功率从35%提升至71%",
        5,
        include_statistics=True
    )
    print(f"✅ 完整引用: {full_citation}")

    print(f"\n效果对比:")
    print(f"  - 普通引用：泛泛而谈，缺乏说服力")
    print(f"  - 增强引用：具体数据，一目了然")


async def main():
    """运行所有测试"""
    await test_statistics_extraction()
    await test_llm_extraction()
    await test_enhanced_citation()
    await test_batch_extraction()
    await test_review_generation()
    await test_citation_formats()
    await demo_practical_usage()

    print("\n" + "=" * 80)
    print("✅ 所有测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
