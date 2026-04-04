"""
测试综述生成器 v2.0 - 多步骤生成
"""
import asyncio
import os
from dotenv import load_dotenv
from services.review_generator_v2 import ReviewGeneratorServiceV2
from services.paper_metadata_dao import PaperMetadataDAO
from database import db


# 加载环境变量
load_dotenv()


async def test_v2_generator():
    """测试 v2.0 生成器"""
    print("=" * 80)
    print("测试综述生成器 v2.0")
    print("=" * 80)

    # 获取 API 配置
    api_key = os.getenv('DEEPSEEK_API_KEY')
    base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    aminer_token = os.getenv('AMINER_API_TOKEN')

    if not api_key:
        print("❌ DEEPSEEK_API_KEY 未配置")
        return

    print(f"✓ API Key: {api_key[:10]}...")
    print(f"✓ Base URL: {base_url}")
    print(f"✓ AMiner Token: {'已配置' if aminer_token else '未配置'}")

    # 从数据库获取一些测试论文
    print(f"\n获取测试论文...")
    session_gen = db.get_session()
    session = next(session_gen)

    try:
        dao = PaperMetadataDAO(session)
        papers = dao.get_recent_papers(limit=30)
        print(f"✓ 获取到 {len(papers)} 篇论文")

        if not papers:
            print("❌ 数据库中没有论文")
            return

        # 显示前3篇论文
        print(f"\n前3篇论文:")
        for i, paper in enumerate(papers[:3], 1):
            print(f"  {i}. {paper.title[:50]}...")

    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass

    # 测试主题
    topic = "机器学习在图像识别中的应用研究"

    # 场景特异性指导（可选）
    specificity_guidance = {
        'core_scene': '图像识别系统',
        'research_field': '计算机视觉',
        'main_technology': '深度学习、卷积神经网络',
        'scene_specificity': '需要处理复杂背景、遮挡、光照变化等挑战',
        'review_requirement': '重点关注方法对比和性能分析',
        'lack_research_statement': '如果某方面文献较少，请明确指出并提出研究建议'
    }

    print(f"\n测试主题: {topic}")
    print("=" * 80)

    # 创建生成器
    generator = ReviewGeneratorServiceV2(
        api_key=api_key,
        base_url=base_url,
        aminer_token=aminer_token
    )

    try:
        # 只测试第1步：生成大纲
        print(f"\n[测试] 第1步：生成大纲")
        print("-" * 80)

        outline = await generator._step1_generate_outline(
            topic=topic,
            papers=papers,
            specificity_guidance=specificity_guidance,
            model="deepseek-chat"
        )

        print(f"\n✓ 大纲生成成功!")
        print(f"\n【引言部分】")
        intro = outline.get('introduction', {})
        print(f"  重点: {intro.get('focus', '')}")
        print(f"  推荐文献: {intro.get('key_papers', [])[:5]}...")

        print(f"\n【主体部分】({len(outline.get('sections', []))}个主题)")
        for i, section in enumerate(outline.get('sections', []), 1):
            print(f"  {i}. {section.get('title', '')}")
            print(f"     重点: {section.get('focus', '')}")
            print(f"     推荐文献: {section.get('key_papers', [])[:5]}...")
            if section.get('comparison_points'):
                print(f"     对比要点: {section.get('comparison_points', [])}")

        print(f"\n【结论部分】")
        conclusion = outline.get('conclusion', {})
        print(f"  重点: {conclusion.get('focus', '')}")
        print(f"  推荐文献: {conclusion.get('key_papers', [])[:5]}...")

        # 如果大纲生成成功，可以选择测试第2步
        print(f"\n" + "=" * 80)
        user_input = input("是否继续测试第2步（生成内容）？(y/n): ")

        if user_input.lower() == 'y':
            print(f"\n[测试] 第2步：逐节生成内容")
            print("-" * 80)

            content = await generator._step2_generate_sections(
                topic=topic,
                papers=papers,
                outline=outline,
                specificity_guidance=specificity_guidance,
                model="deepseek-chat"
            )

            print(f"\n✓ 内容生成成功!")
            print(f"\n【内容预览】(前1500字符)")
            print("-" * 80)
            print(content[:1500] + "...")
            print("-" * 80)

            print(f"\n完整内容长度: {len(content)} 字符")

            # 统计引用
            import re
            citations = re.findall(r'\[(\d+)\]', content)
            unique_citations = len(set(citations))
            print(f"引用数量: {len(citations)} 次，覆盖 {unique_citations} 篇文献")

            # 如果第2步成功，可以选择测试完整流程
            print(f"\n" + "=" * 80)
            user_input2 = input("是否继续测试完整流程（步骤3-4）？(y/n): ")

            if user_input2.lower() == 'y':
                print(f"\n[测试] 完整流程")
                print("-" * 80)

                final_review, cited_papers = await generator.generate_review(
                    topic=topic,
                    papers=papers,
                    model="deepseek-chat",
                    specificity_guidance=specificity_guidance
                )

                print(f"\n✓ 完整综述生成成功!")
                print(f"\n【最终综述】")
                print("=" * 80)
                print(final_review[:2000] + "...")
                print("=" * 80)
                print(f"\n总长度: {len(final_review)} 字符")
                print(f"引用文献: {len(cited_papers)} 篇")

                # 保存到文件
                output_file = "/tmp/test_review_v2.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(final_review)
                print(f"\n✓ 综述已保存到: {output_file}")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await generator.close()

    print(f"\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_v2_generator())
