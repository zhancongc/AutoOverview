"""
测试深度对比分析功能
演示如何在文献矩阵中追问"这种分歧可能源于..."
"""
import asyncio
from services.deep_comparison import (
    DeepComparisonAnalyzer,
    DeepComparisonFormatter,
    generate_deep_comparison,
    infer_divergence_reasons
)


# 模拟论文数据（包含冲突观点）
MOCK_PAPERS = [
    {
        "id": "1",
        "title": "Media Coverage Reduces Earnings Management in Chinese Listed Firms",
        "abstract": "Using a sample of 5,000 Chinese listed firms from 2010-2020, we find that higher media coverage significantly reduces earnings management. The negative correlation is robust after controlling for firm size and governance characteristics.",
        "year": 2021,
        "authors": ["Zhang", "Wang"],
        "is_english": True
    },
    {
        "id": "2",
        "title": "Media Pressure May Increase Earnings Management under Performance Pressure",
        "abstract": "Based on a survey of 200 US firms, we find that intense media pressure can force managers to meet earnings targets through accrual earnings management. When firms face high performance pressure, media coverage acts as a double-edged sword.",
        "year": 2019,
        "authors": ["Smith", "Johnson"],
        "is_english": True
    },
    {
        "id": "3",
        "title": "Corporate Governance Moderates the Media-Earnings Management Relationship",
        "abstract": "Using panel data from emerging markets, we show that the monitoring effect of media is stronger in firms with weak internal governance. Well-governed firms already have low earnings management, so media adds less value.",
        "year": 2022,
        "authors": ["Chen", "Lee"],
        "is_english": True
    },
    {
        "id": "4",
        "title": "媒体关注与上市公司盈余管理：基于沪深A股的实证研究",
        "abstract": "本文以2008-2018年沪深A股上市公司为样本，发现媒体关注度与盈余管理程度呈显著负相关。媒体报道每增加10%，盈余管理程度降低约15%。",
        "year": 2020,
        "authors": ["李明", "王强"],
        "is_english": False
    },
]


async def test_divergence_inference():
    """测试分歧原因推断"""
    print("=" * 80)
    print("测试1: 分歧原因推断")
    print("=" * 80)

    analyzer = DeepComparisonAnalyzer()

    # 对比中美研究
    paper_cn = MOCK_PAPERS[3]  # 中文论文
    paper_us = MOCK_PAPERS[1]  # 英文论文（压力效应）

    print(f"\n对比论文:")
    print(f"  论文A: {paper_cn['title'][:50]}... ({paper_cn['year']})")
    print(f"  论文B: {paper_us['title'][:50]}... ({paper_us['year']})")

    reasons = analyzer.infer_divergence_reasons(paper_cn, paper_us, "媒体关注与盈余管理")

    print(f"\n推断的分歧原因:")
    for i, reason in enumerate(reasons, 1):
        print(f"  {i}. {reason}")


async def test_reasoning_formatting():
    """测试带原因追问的格式化"""
    print("\n" + "=" * 80)
    print("测试2: 带原因追问的对比陈述")
    print("=" * 80)

    analyzer = DeepComparisonAnalyzer()

    # 支持压力效应的论文
    supporting_papers = [MOCK_PAPERS[1]]  # Smith: 压力效应
    opposing_papers = [MOCK_PAPERS[0], MOCK_PAPERS[3]]  # Zhang/李明: 监督效应

    statement = "关于媒体关注的效应，现有研究存在不同发现"

    formatted = analyzer.format_comparison_with_reasons(
        statement,
        supporting_papers,
        opposing_papers,
        "媒体关注与盈余管理"
    )

    print(f"\n格式化后的对比陈述:")
    print(f"  {formatted}")


async def test_deep_comparison_generation():
    """测试深度对比分析生成"""
    print("\n" + "=" * 80)
    print("测试3: 深度对比分析生成")
    print("=" * 80)

    analyzer = DeepComparisonAnalyzer()

    topic = "媒体关注与盈余管理"

    # 生成深度对比
    deep_comparison = await analyzer.generate_deep_comparison(
        MOCK_PAPERS,
        topic,
        section="监督效应"
    )

    print(f"\n生成的深度对比分析:")
    print("-" * 80)
    print(deep_comparison)
    print("-" * 80)


async def test_comparison_table():
    """测试对比表格生成"""
    print("\n" + "=" * 80)
    print("测试4: 文献对比矩阵表格")
    print("=" * 80)

    formatter = DeepComparisonFormatter()

    comparison_table = formatter.format_comparison_table(
        MOCK_PAPERS,
        "媒体关注与盈余管理"
    )

    print(f"\n生成的对比表格:")
    print("-" * 80)
    print(comparison_table)
    print("-" * 80)


async def test_section_generation():
    """测试带深度对比的章节生成"""
    print("\n" + "=" * 80)
    print("测试5: 带深度对比的章节")
    print("=" * 80)

    formatter = DeepComparisonFormatter()

    section_content = await formatter.generate_section_with_deep_comparison(
        section_title="媒体监督效应：观点对比与原因分析",
        papers=MOCK_PAPERS,
        topic="媒体关注与盈余管理"
    )

    print(f"\n生成的章节内容:")
    print("-" * 80)
    print(section_content)
    print("-" * 80)


async def test_enhance_existing_review():
    """测试增强现有综述"""
    print("\n" + "=" * 80)
    print("测试6: 增强现有综述")
    print("=" * 80)

    analyzer = DeepComparisonAnalyzer()

    # 原始综述（有对比但无原因分析）
    original_review = """## 媒体监督效应

关于媒体关注对盈余管理的影响，Zhang等[1]和李明等[4]的研究发现显著负相关，表明媒体具有监督作用。然而，Smith等[2]则发现媒体压力可能诱发盈余管理。Chen等[3]的研究进一步指出公司治理水平是重要的调节变量。

现有研究在该领域存在明显分歧。
"""

    print("原始综述:")
    print("-" * 80)
    print(original_review)
    print("-" * 80)

    # 增强深度对比
    enhanced_review, report = await analyzer.enhance_review_with_deep_comparison(
        original_review,
        MOCK_PAPERS,
        "媒体关注与盈余管理"
    )

    print("\n增强后的综述:")
    print("-" * 80)
    print(enhanced_review)
    print("-" * 80)

    print(f"\n增强报告:")
    print(f"  原始长度: {report['original_length']} 字符")
    print(f"  增强长度: {report['enhanced_length']} 字符")
    print(f"  追加原因分析: {'是' if report['added_reasoning'] else '否'}")


async def test_practical_examples():
    """演示实际使用场景"""
    print("\n" + "=" * 80)
    print("演示: 实际使用场景")
    print("=" * 80)

    print("\n场景：在综述中增加深度对比分析\n")

    # 普通对比（无原因分析）
    print("❌ 普通对比（缺乏深度）:")
    print("""
    关于媒体关注的效应，现有研究存在分歧。Zhang等[1]发现显著负相关；
    Smith等[2]则发现压力效应；Chen等[3]指出治理水平的调节作用。
    """)

    # 深度对比（有原因分析）
    print("\n✅ 深度对比（追问原因）:")
    print("""
    关于媒体关注的效应，现有研究存在分歧。Zhang等[1]发现显著负相关；
    Smith等[2]则发现压力效应；Chen等[3]指出治理水平的调节作用。

    > **这种分歧可能源于：**
    > - **研究对象差异**：Zhang等[1]和李明等[4]基于中国市场，而Smith等[2]研究美国企业
    > - **样本情境差异**：Smith等[2]聚焦于业绩压力情境，而其他研究涵盖一般情境
    > - **理论视角差异**：Zhang等[1]强调监督理论，而Smith等[2]关注压力应对理论
    """)

    print("\n💡 深度对比的优势:")
    print("  - 展示批判性思维")
    print("  - 帮助读者理解分歧来源")
    print("  - 指明未来研究方向")
    print("  - 提高综述的学术价值")


async def test_llm_deep_comparison():
    """测试LLM深度对比分析"""
    print("\n" + "=" * 80)
    print("测试7: LLM深度对比分析")
    print("=" * 80)

    import os
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("\n⚠️  DEEPSEEK_API_KEY 未配置，跳过LLM测试\n")
        return

    analyzer = DeepComparisonAnalyzer()

    llm_comparison = await analyzer.generate_deep_comparison(
        MOCK_PAPERS,
        "媒体关注与盈余管理",
        "监督效应"
    )

    print("\nLLM生成的深度对比分析:")
    print("-" * 80)
    print(llm_comparison)
    print("-" * 80)


async def main():
    """运行所有测试"""
    await test_divergence_inference()
    await test_reasoning_formatting()
    await test_deep_comparison_generation()
    await test_comparison_table()
    await test_section_generation()
    await test_enhance_existing_review()
    await test_practical_examples()
    await test_llm_deep_comparison()

    print("\n" + "=" * 80)
    print("✅ 所有测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
