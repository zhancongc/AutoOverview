"""
论文题目解析与三圈文献体系构建
识别"方法论+应用场景+优化目标"结构
"""
import re
from typing import Dict, List, Tuple
from services.paper_search import PaperSearchService


class TopicAnalyzer:
    """论文题目分析器"""

    # 常见方法论关键词
    METHODOLOGY_KEYWORDS = {
        'DMAIC': ['dmaic', '六西格玛', '六sigma', '6sigma', '6 sigma'],
        '敏捷': ['敏捷开发', 'agile', 'scrum', 'kanban'],
        'DevOps': ['devops', '持续交付', 'ci/cd', 'cicd', '持续集成'],
        'AHP': ['ahp', '层次分析法', 'analytic hierarchy process'],
        '精益': ['精益', 'lean', '精益生产'],
        'TRIZ': ['triz', '发明问题解决理论'],
        'Design Thinking': ['设计思维', 'design thinking'],
        'OKR': ['okr', '目标与关键结果'],
        '5W2H': ['5w2h', '七问分析法'],
    }

    # 应用场景领域关键词
    DOMAIN_KEYWORDS = {
        '智能座舱': ['智能座舱', '智能驾驶舱', '车载系统', '车机系统', '智能网联'],
        '汽车软件': ['汽车软件', '车载软件', '汽车电子'],
        '嵌入式': ['嵌入式', 'embedded'],
        'Web应用': ['web应用', 'web开发', '网站', '网页'],
        '移动应用': ['移动应用', 'app', '手机应用', '移动端'],
        '企业软件': ['企业软件', 'erp', 'crm', '企业系统'],
        '云计算': ['云计算', '云平台', '云服务'],
        '大数据': ['大数据', '数据挖掘'],
        '人工智能': ['人工智能', 'ai', '机器学习', '深度学习'],
    }

    # 优化目标关键词
    OPTIMIZATION_KEYWORDS = {
        '持续交付': ['持续交付', 'continuous delivery', '持续部署', 'continuous deployment'],
        '质量管理': ['质量管理', '质量改进', '质量控制', 'quality management'],
        '流程优化': ['流程优化', 'process optimization', '流程改进', 'process improvement'],
        '效率提升': ['效率提升', '效率优化', '效能提升'],
        '成本控制': ['成本控制', '成本优化', '降本增效'],
        '用户体验': ['用户体验', 'ux', '用户满意度'],
        '安全性': ['安全性', '安全', 'security'],
        '可靠性': ['可靠性', 'reliability', '稳定性'],
    }

    def __init__(self):
        self.search_service = PaperSearchService()

    def analyze_topic(self, title: str) -> Dict[str, str]:
        """
        分析论文题目，提取三个圈的关键词

        Args:
            title: 论文题目

        Returns:
            包含三个圈关键词的字典
        """
        title_lower = title.lower()

        # 圈C：方法论
        methodology = self._extract_methodology(title, title_lower)

        # 圈A：应用场景
        domain = self._extract_domain(title, title_lower)

        # 圈B：优化目标
        optimization = self._extract_optimization(title, title_lower)

        return {
            'methodology': methodology,
            'domain': domain,
            'optimization': optimization,
            'title': title
        }

    def _extract_methodology(self, title: str, title_lower: str) -> str:
        """提取方法论关键词"""
        for method, keywords in self.METHODOLOGY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return method
        # 默认返回题目中的可能方法论
        return self._fallback_extract(title, ['研究', '方法', '模型', '框架'])

    def _extract_domain(self, title: str, title_lower: str) -> str:
        """提取应用场景关键词"""
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return domain
        # 尝试从"基于...的"模式中提取
        match = re.search(r'基于(.+?)的', title)
        if match:
            return match.group(1)
        return self._fallback_extract(title, ['系统', '平台', '软件'])

    def _extract_optimization(self, title: str, title_lower: str) -> str:
        """提取优化目标关键词"""
        for opt, keywords in self.OPTIMIZATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return opt
        # 从"优化"、"改进"、"研究"等词前的内容提取
        match = re.search(r'(.+?)(?:优化|改进|研究|提升)', title)
        if match:
            return match.group(1)
        return self._fallback_extract(title, ['优化', '改进', '提升'])

    def _fallback_extract(self, title: str, suffixes: List[str]) -> str:
        """备用提取方法"""
        for suffix in suffixes:
            if suffix in title:
                parts = title.split(suffix)
                if parts:
                    return parts[0].replace('基于', '').strip()
        return "通用"

    def generate_search_queries(self, analysis: Dict[str, str]) -> List[Dict]:
        """
        生成三个圈的检索查询

        Returns:
            包含三个圈查询信息的列表
        """
        methodology = analysis['methodology']
        domain = analysis['domain']
        optimization = analysis['optimization']

        return [
            {
                'circle': 'A',
                'name': f'{domain}研究现状',
                'query': f'{domain} 软件 工程',
                'description': f'证明{domain}的重要性和特殊性'
            },
            {
                'circle': 'B',
                'name': f'{optimization}现状与痛点',
                'query': f'{optimization} 软件 质量管理',
                'description': f'证明{optimization}的现状与痛点'
            },
            {
                'circle': 'C',
                'name': f'{methodology}方法应用',
                'query': f'{methodology} 软件 流程优化',
                'description': f'证明{methodology}的可行性及在软件领域的应用'
            }
        ]

    async def search_three_circles(self, title: str) -> Dict:
        """
        检索三个圈的文献

        Args:
            title: 论文题目

        Returns:
            包含三个圈文献和分析结果的字典
        """
        # 分析题目
        analysis = self.analyze_topic(title)

        # 生成查询
        queries = self.generate_search_queries(analysis)

        # 并行检索三个圈的文献
        results = []
        for query_info in queries:
            papers = await self.search_service.search_papers(
                query=query_info['query'],
                years_ago=10,
                limit=50
            )
            results.append({
                **query_info,
                'papers': papers,
                'count': len(papers)
            })

        # 分析研究缺口
        gap_analysis = self._analyze_gap(analysis, results)

        return {
            'analysis': analysis,
            'circles': results,
            'gap_analysis': gap_analysis
        }

    def _analyze_gap(self, analysis: Dict, circle_results: List[Dict]) -> Dict:
        """分析研究缺口"""
        methodology = analysis['methodology']
        domain = analysis['domain']
        optimization = analysis['optimization']

        # 统计交集文献数量
        all_papers = []
        for result in circle_results:
            all_papers.extend(result['papers'])

        # 检查是否存在三圈交集
        intersection_count = self._count_intersection(all_papers)

        gap = {
            'gap_description': f'现有研究缺乏将{methodology}系统性地应用于{domain}这一特定领域的{optimization}改进中。',
            'research_opportunity': f'本研究填补了将{methodology}方法论与{domain}的{optimization}相结合的研究空白。',
            'intersection_count': intersection_count,
            'suggestions': [
                f'探索{methodology}在{domain}场景下的适应性',
                f'建立针对{domain}的{optimization}评价指标',
                f'设计{methodology}与{optimization}工具的集成方案'
            ]
        }

        return gap

    def _count_intersection(self, papers: List[Dict]) -> int:
        """粗略估计交集文献数量（简化版）"""
        # 实际应用中可以用更复杂的算法
        return min(5, len(papers) // 10)


class ThreeCirclesReviewGenerator:
    """三圈文献综述生成器"""

    def __init__(self):
        self.analyzer = TopicAnalyzer()

    async def generate(self, title: str) -> Dict:
        """
        生成三圈文献综述

        Args:
            title: 论文题目

        Returns:
            包含分析和综述的字典
        """
        result = await self.analyzer.search_three_circles(title)

        # 构建综述框架
        review_framework = self._build_framework(result)

        result['review_framework'] = review_framework

        return result

    def _build_framework(self, result: Dict) -> Dict:
        """构建综述框架"""
        analysis = result['analysis']
        circles = result['circles']
        gap = result['gap_analysis']

        return {
            'introduction': {
                'title': '引言',
                'content': f'本文研究{analysis["title"]}，涉及{analysis["domain"]}、{analysis["optimization"]}和{analysis["methodology"]}三个领域。'
            },
            'sections': [
                {
                    'circle': 'A',
                    'title': f'{analysis["domain"]}研究现状',
                    'description': circles[0]['description'],
                    'paper_count': circles[0]['count'],
                    'key_points': [
                        f'{analysis["domain"]}的发展历程',
                        f'{analysis["domain"]}的技术特点',
                        f'{analysis["domain"]}面临的挑战'
                    ]
                },
                {
                    'circle': 'B',
                    'title': f'{analysis["optimization"]}现状与痛点',
                    'description': circles[1]['description'],
                    'paper_count': circles[1]['count'],
                    'key_points': [
                        f'{analysis["optimization"]}的理论基础',
                        f'{analysis["optimization"]}的实践方法',
                        f'当前存在的问题与挑战'
                    ]
                },
                {
                    'circle': 'C',
                    'title': f'{analysis["methodology"]}方法应用',
                    'description': circles[2]['description'],
                    'paper_count': circles[2]['count'],
                    'key_points': [
                        f'{analysis["methodology"]}的理论框架',
                        f'{analysis["methodology"]}在软件领域的应用',
                        f'{analysis["methodology"]}的优势与局限'
                    ]
                }
            ],
            'gap_analysis': {
                'title': '研究缺口分析',
                'gap': gap['gap_description'],
                'opportunity': gap['research_opportunity'],
                'suggestions': gap['suggestions']
            }
        }
