"""
测试 AMiner Token 是否能正常搜索文献
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_aminer():
    """测试 AMiner 搜索功能"""
    # 检查 Token 配置
    aminer_token = os.getenv('AMINER_API_TOKEN')
    if not aminer_token:
        print("❌ AMINER_API_TOKEN 未配置")
        return
    
    print(f"✅ AMINER_API_TOKEN 已配置: {aminer_token[:20]}...")
    
    # 导入服务
    try:
        from services.aminer_search import AMinerSearchService
        service = AMinerSearchService(api_token=aminer_token)
        
        # 测试搜索
        print("\n" + "="*60)
        print("测试 1: 搜索 '深度学习' 相关论文")
        print("="*60)
        
        papers = await service.search_papers(
            keywords=["深度学习", "DNA"],
            year_start=2020,
            year_end=2025,
            max_results=5
        )
        
        print(f"\n找到 {len(papers)} 篇论文:")
        for i, paper in enumerate(papers, 1):
            title = paper.get('title', 'N/A')
            authors = paper.get('authors', {})
            author_list = authors.get('authors', []) if isinstance(authors, dict) else []
            author_names = ', '.join([a.get('name', 'N/A') for a in author_list[:3]])
            year = paper.get('year', 'N/A')
            venue = paper.get('venue', {}).get('name', 'N/A') if isinstance(paper.get('venue'), dict) else paper.get('venue', 'N/A')
            citations = paper.get('citations', 0)
            
            print(f"\n{i}. {title}")
            print(f"   作者: {author_names}")
            print(f"   年份: {year}")
            print(f"   期刊: {venue}")
            print(f"   引用: {citations}")
        
        # 测试英文搜索
        print("\n" + "="*60)
        print("测试 2: 搜索 'deep learning' 英文论文")
        print("="*60)
        
        papers_en = await service.search_papers(
            keywords=["deep learning"],
            year_start=2020,
            year_end=2025,
            max_results=3
        )
        
        print(f"\n找到 {len(papers_en)} 篇英文论文:")
        for i, paper in enumerate(papers_en, 1):
            title = paper.get('title', 'N/A')
            year = paper.get('year', 'N/A')
            citations = paper.get('citations', 0)
            print(f"{i}. [{year}] {title} (引用: {citations})")
        
        # 测试 ScholarFlux 集成
        print("\n" + "="*60)
        print("测试 3: 通过 ScholarFlux 搜索")
        print("="*60)
        
        from services.scholarflux_wrapper import ScholarFlux
        flux = ScholarFlux()
        
        papers_flux = await flux.search(
            query="深度学习",
            years_ago=5,
            limit=5
        )
        
        print(f"\nScholarFlux 找到 {len(papers_flux)} 篇论文:")
        for i, paper in enumerate(papers_flux[:5], 1):
            title = paper.get('title', 'N/A')[:60]
            source = paper.get('source', 'N/A')
            print(f"{i}. {title}... (来源: {source})")
        
        print("\n" + "="*60)
        print("✅ AMiner Token 测试成功！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ AMiner Token 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_aminer())
