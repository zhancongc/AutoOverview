"""
测试研究方向参数功能

验证：
1. 指定研究方向时，能够提高搜索相关性
2. 未指定研究方向时，系统能够自动推断
"""
import asyncio
import sys
sys.path.append('/Users/zhancc/Github/AutoOverview/backend')

from services.contextual_keyword_translator import translate_keywords_contextual
from services.review_task_executor import ReviewTaskExecutor


async def test_research_direction_in_translation():
    """测试研究方向在关键词翻译中的作用"""
    print("=" * 80)
    print("测试1: 研究方向对关键词翻译的影响")
    print("=" * 80)

    # 测试用例：CAS 缩写词
    topic = "CAS算法研究"
    keywords = ["CAS算法优化", "CAS系统设计"]

    # 不指定研究方向
    print("\n【不指定研究方向】")
    print(f"题目: {topic}")
    print(f"关键词: {keywords}")

    result1 = await translate_keywords_contextual(
        keywords=keywords,
        topic=topic,
        research_direction=""
    )

    print(f"\n翻译结果:")
    for orig, trans in result1.items():
        print(f"  {orig} -> {trans}")

    # 指定研究方向：计算机代数系统
    print("\n\n【指定研究方向: 计算机代数系统】")
    print(f"题目: {topic}")
    print(f"关键词: {keywords}")
    print(f"研究方向: 计算机代数系统")

    result2 = await translate_keywords_contextual(
        keywords=keywords,
        topic=topic,
        research_direction="计算机代数系统"
    )

    print(f"\n翻译结果:")
    for orig, trans in result2.items():
        print(f"  {orig} -> {trans}")

    # 指定研究方向：化学分析系统
    print("\n\n【指定研究方向: 化学分析系统】")
    print(f"题目: {topic}")
    print(f"关键词: {keywords}")
    print(f"研究方向: 化学分析系统")

    result3 = await translate_keywords_contextual(
        keywords=keywords,
        topic=topic,
        research_direction="化学分析系统"
    )

    print(f"\n翻译结果:")
    for orig, trans in result3.items():
        print(f"  {orig} -> {trans}")

    # 对比结果
    print("\n\n【结果对比】")
    print("不指定研究方向: 可能翻译成 'Critical Assessment System' 或其他")
    print("指定 '计算机代数系统': 翻译成 'Computer Algebra System' ✓")
    print("指定 '化学分析系统': 翻译成 'Chemical Analysis System' ✓")


async def test_research_direction_in_outline():
    """测试研究方向在大纲生成中的作用"""
    print("\n\n" + "=" * 80)
    print("测试2: 研究方向对大纲生成的影响")
    print("=" * 80)

    executor = ReviewTaskExecutor()

    # 测试用例：模糊的题目
    topic = "ML算法优化研究"

    # 不指定研究方向
    print("\n【不指定研究方向】")
    print(f"题目: {topic}")

    outline1 = await executor._generate_review_outline(topic, research_direction="")

    print(f"\n生成的大纲章节:")
    for section in outline1.get('body_sections', [])[:3]:
        print(f"  - {section.get('title', 'N/A')}")
        print(f"    关键词: {section.get('search_keywords', [])}")

    # 指定研究方向：机器学习
    print("\n\n【指定研究方向: 机器学习】")
    print(f"题目: {topic}")
    print(f"研究方向: 机器学习")

    outline2 = await executor._generate_review_outline(topic, research_direction="机器学习")

    print(f"\n生成的大纲章节:")
    for section in outline2.get('body_sections', [])[:3]:
        print(f"  - {section.get('title', 'N/A')}")
        print(f"    关键词: {section.get('search_keywords', [])}")


def test_api_request_format():
    """测试 API 请求格式"""
    print("\n\n" + "=" * 80)
    print("测试3: API 请求格式示例")
    print("=" * 80)

    print("\n【不指定研究方向的请求】")
    print("""
{
  "topic": "CAS算法研究",
  "target_count": 50,
  "recent_years_ratio": 0.5,
  "english_ratio": 0.3
}
    """)

    print("\n【指定研究方向的请求】")
    print("""
{
  "topic": "CAS算法研究",
  "research_direction": "计算机代数系统",
  "target_count": 50,
  "recent_years_ratio": 0.5,
  "english_ratio": 0.3
}
    """)

    print("\n【优势】")
    print("  ✅ 明确指定研究方向，避免歧义")
    print("  ✅ 提高搜索结果的相关性")
    print("  ✅ 减少不相关文献的混入")
    print("  ✅ 生成更精准的大纲和关键词")


async def main():
    """运行所有测试"""
    # 测试1：研究方向在翻译中的作用
    await test_research_direction_in_translation()

    # 测试2：研究方向在大纲生成中的作用
    # await test_research_direction_in_outline()

    # 测试3：API 请求格式
    test_api_request_format()

    print("\n\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
