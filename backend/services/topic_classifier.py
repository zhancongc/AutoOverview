"""
论文题目分类器（增强版）
根据关键词、核心动词、研究范式进行多层判定
"""
import re
from typing import Dict, List, Optional, Tuple
from enum import Enum


class TopicType(Enum):
    """题目类型枚举"""
    APPLICATION = "application"  # 应用型/解决方案型 - 三圈交集
    EVALUATION = "evaluation"    # 评价型/体系构建型 - 金字塔式
    THEORETICAL = "theoretical"  # 理论型/研究型 - 溯源式
    EMPIRICAL = "empirical"      # 实证型 - 问题-方案式
    GENERAL = "general"          # 通用型


class TopicClassifier:
    """论文题目分类器（增强版）"""

    # ==================== 第一眼：核心动词/名词 ====================

    # 应用型关键词（优先级最高）
    APPLICATION_KEYWORDS = {
        'primary': ['基于', '优化', '改进', '应用', '提升', '实施', '部署', '增强'],
        'methods': ['dmaic', '敏捷', 'devops', 'ci/cd', 'cicd', 'ahp', 'triz',
                   '六西格玛', '六sigma', '6sigma', 'scrum', 'kanban', '精益',
                   'design thinking', 'okr', '5w2h']
    }

    # 评价型关键词
    EVALUATION_KEYWORDS = {
        'primary': ['成熟度', '评价', '评估', '指标', '体系', '度量', '测评'],
        'secondary': ['评价模型', '评估体系', '质量评价', '绩效评估', '能力成熟度',
                     '评价体系', '评估框架', '评价指标', '综合评价']
    }

    # 理论型关键词
    THEORETICAL_KEYWORDS = {
        'primary': ['理论', '机理', '机制', '原理', '综述', '进展'],
        'secondary': ['本质', '内涵', '界定', '概念', '定义', '理论框架',
                     '研究综述', '理论构建', '概念界定', '研究现状']
    }

    # 实证型关键词
    EMPIRICAL_KEYWORDS = {
        'primary': ['影响', '效应', '关系', '相关', '作用'],
        'secondary': ['影响因素', '决定因素', '驱动因素', '因果', '实证', '验证',
                     '影响机制', '效应分析', '相关性研究', '关系研究', '中介', '调节']
    }

    # ==================== 第二眼：研究范式 ====================

    # 解决问题范式（应用型）
    PROBLEM_SOLVING_PATTERNS = [
        r'.+?的.+?(?:优化|改进|提升|增强)',
        r'利用.+?(?:优化|改进|解决).+?',
        r'.+?(?:问题|挑战|痛点).+?(?:解决|应对|处理)'
    ]

    # 构建工具范式（评价型）
    TOOL_BUILDING_PATTERNS = [
        r'.+?(?:成熟度|评价|评估).+?(?:模型|体系|框架|指标)',
        r'构建.+?(?:评价|评估).+?(?:体系|模型|框架)',
        r'.+?(?:评价|评估)体系.+(?:构建|设计|开发)'
    ]

    # 整合知识范式（理论型）
    KNOWLEDGE_INTEGRATION_PATTERNS = [
        r'.+?(?:理论|研究).+?(?:综述|回顾|梳理)',
        r'.+?(?:研究|理论).+?(?:现状|进展|前沿)',
        r'.+?(?:文献|理论).+?(?:综述|述评)'
    ]

    # 检验假设范式（实证型）
    HYPOTHESIS_TESTING_PATTERNS = [
        r'.+?对.+?(?:影响|效应|作用)',
        r'.+?与.+?(?:关系|相关|相关性)',
        r'.+?(?:影响|效应|作用).+?(?:机制|路径)',
        r'.+?(?:影响因素|决定因素|驱动因素)',
        r'.+?(?:中介|调节|干扰).+?(?:效应|作用)'
    ]

    # ==================== 混血题目判定规则 ====================

    # 实证型优先：如果核心是检验影响关系，即使有"基于XX方法"也按实证型处理
    EMPIRICAL_PRIORITY_PATTERNS = [
        (r'基于.+?(?:模型|方法).+?(?:影响|效应|关系)', '实证型：核心是检验影响关系，模型只是工具'),
        (r'.+?对.+?(?:影响|效应).+?(?:研究|分析)', '实证型：核心是影响关系研究'),
    ]

    # 评价型优先：如果核心是构建评价体系，即使有"提升路径"等应用元素也按评价型处理
    EVALUATION_PRIORITY_PATTERNS = [
        (r'.+?(?:成熟度|评价).+?(?:评价|提升路径)', '评价型：核心是构建评价体系'),
        (r'.+?评价.+(?:与|及).+?(?:提升|优化|改进)', '评价型：核心是评价，提升是延伸'),
    ]

    def __init__(self):
        pass

    def classify(self, title: str) -> Tuple[TopicType, str, Dict]:
        """
        分类题目（增强版）

        Args:
            title: 论文题目

        Returns:
            (题目类型, 置信度说明, 判定详情)
        """
        title_stripped = title.strip()
        title_lower = title_stripped.lower()

        # 记录判定过程
        decision_log = {
            'first_look': None,
            'second_look': None,
            'hybrid_check': None,
            'final_decision': None
        }

        # ==================== 第一步：混血题目优先判定 ====================
        hybrid_result = self._check_hybrid_topics(title_stripped, title_lower)
        if hybrid_result:
            decision_log['hybrid_check'] = hybrid_result
            decision_log['final_decision'] = hybrid_result[0]
            return (hybrid_result[0], hybrid_result[1], decision_log)

        # ==================== 第二步：第一眼看关键词 ====================
        first_look_result = self._first_look_classification(title_stripped, title_lower)
        decision_log['first_look'] = first_look_result

        # 如果第一眼有明确结果，直接返回
        if first_look_result[0] != TopicType.GENERAL:
            decision_log['final_decision'] = first_look_result[0]
            return first_look_result

        # ==================== 第三步：第二眼看研究范式 ====================
        second_look_result = self._second_look_classification(title_stripped, title_lower)
        decision_log['second_look'] = second_look_result
        decision_log['final_decision'] = second_look_result[0]

        return second_look_result

    def _check_hybrid_topics(self, title: str, title_lower: str) -> Optional[Tuple[TopicType, str]]:
        """检查混血题目，优先处理特定组合"""
        # 实证型优先：检验影响关系
        for pattern, reason in self.EMPIRICAL_PRIORITY_PATTERNS:
            if re.search(pattern, title):
                return (TopicType.EMPIRICAL, f'混血题目→{reason}')

        # 评价型优先：构建评价体系
        for pattern, reason in self.EVALUATION_PRIORITY_PATTERNS:
            if re.search(pattern, title):
                return (TopicType.EVALUATION, f'混血题目→{reason}')

        return None

    def _first_look_classification(self, title: str, title_lower: str) -> Tuple[TopicType, str]:
        """第一眼：看核心动词/名词关键词"""
        scores = {
            TopicType.APPLICATION: 0,
            TopicType.EVALUATION: 0,
            TopicType.THEORETICAL: 0,
            TopicType.EMPIRICAL: 0
        }

        # 检查应用型关键词
        for kw in self.APPLICATION_KEYWORDS['primary']:
            if kw in title:
                scores[TopicType.APPLICATION] += 3  # 高权重
        for kw in self.APPLICATION_KEYWORDS['methods']:
            if kw in title_lower:
                scores[TopicType.APPLICATION] += 2

        # 检查评价型关键词
        for kw in self.EVALUATION_KEYWORDS['primary']:
            if kw in title:
                scores[TopicType.EVALUATION] += 3  # 高权重
        for kw in self.EVALUATION_KEYWORDS['secondary']:
            if kw in title:
                scores[TopicType.EVALUATION] += 2

        # 检查理论型关键词
        for kw in self.THEORETICAL_KEYWORDS['primary']:
            if kw in title:
                scores[TopicType.THEORETICAL] += 3
        for kw in self.THEORETICAL_KEYWORDS['secondary']:
            if kw in title:
                scores[TopicType.THEORETICAL] += 2

        # 检查实证型关键词
        for kw in self.EMPIRICAL_KEYWORDS['primary']:
            if kw in title:
                scores[TopicType.EMPIRICAL] += 3
        for kw in self.EMPIRICAL_KEYWORDS['secondary']:
            if kw in title:
                scores[TopicType.EMPIRICAL] += 2

        # 找出最高分
        max_score = max(scores.values())
        if max_score == 0:
            return (TopicType.GENERAL, '未识别到关键词，进入第二眼判定')

        # 获取最高分的类型
        winner = [t for t, s in scores.items() if s == max_score][0]
        reason_map = {
            TopicType.APPLICATION: f'识别到应用型关键词（基于/优化/应用等），权重{max_score}',
            TopicType.EVALUATION: f'识别到评价型关键词（成熟度/评价/体系等），权重{max_score}',
            TopicType.THEORETICAL: f'识别到理论型关键词（理论/机理/综述等），权重{max_score}',
            TopicType.EMPIRICAL: f'识别到实证型关键词（影响/效应/关系等），权重{max_score}'
        }

        return (winner, reason_map[winner])

    def _second_look_classification(self, title: str, title_lower: str) -> Tuple[TopicType, str]:
        """第二眼：看研究范式"""
        # 检查解决问题范式（应用型）
        for pattern in self.PROBLEM_SOLVING_PATTERNS:
            if re.search(pattern, title):
                return (TopicType.APPLICATION, '第二眼：识别到「解决问题」范式（优化/改进/提升）')

        # 检查构建工具范式（评价型）
        for pattern in self.TOOL_BUILDING_PATTERNS:
            if re.search(pattern, title):
                return (TopicType.EVALUATION, '第二眼：识别到「构建工具」范式（评价模型/体系构建）')

        # 检查检验假设范式（实证型）
        for pattern in self.HYPOTHESIS_TESTING_PATTERNS:
            if re.search(pattern, title):
                return (TopicType.EMPIRICAL, '第二眼：识别到「检验假设」范式（影响/关系/效应）')

        # 检查整合知识范式（理论型）
        for pattern in self.KNOWLEDGE_INTEGRATION_PATTERNS:
            if re.search(pattern, title):
                return (TopicType.THEORETICAL, '第二眼：识别到「整合知识」范式（综述/现状/进展）')

        return (TopicType.GENERAL, '未识别到明确范式，使用通用框架')


class FrameworkGenerator:
    """综述框架生成器（增强版）"""

    def __init__(self):
        self.classifier = TopicClassifier()

    def generate_framework(self, title: str) -> Dict:
        """
        根据题目类型生成综述框架

        Args:
            title: 论文题目

        Returns:
            综述框架
        """
        topic_type, reason, decision_log = self.classifier.classify(title)

        framework = {
            'title': title,
            'type': topic_type.value,
            'type_name': self._get_type_name(topic_type),
            'classification_reason': reason,
            'decision_log': decision_log,
            'framework': None,
            'search_queries': []
        }

        # 根据类型生成框架
        if topic_type == TopicType.APPLICATION:
            framework['framework'] = self._application_framework(title)
            framework['search_queries'] = self._application_queries(title)
        elif topic_type == TopicType.EVALUATION:
            framework['framework'] = self._evaluation_framework(title)
            framework['search_queries'] = self._evaluation_queries(title)
        elif topic_type == TopicType.THEORETICAL:
            framework['framework'] = self._theoretical_framework(title)
            framework['search_queries'] = self._theoretical_queries(title)
        elif topic_type == TopicType.EMPIRICAL:
            framework['framework'] = self._empirical_framework(title)
            framework['search_queries'] = self._empirical_queries(title)
        else:
            framework['framework'] = self._general_framework(title)
            framework['search_queries'] = self._general_queries(title)

        return framework

    def _get_type_name(self, topic_type: TopicType) -> str:
        """获取类型名称"""
        names = {
            TopicType.APPLICATION: "应用型/解决方案型",
            TopicType.EVALUATION: "评价型/体系构建型",
            TopicType.THEORETICAL: "理论型/研究型",
            TopicType.EMPIRICAL: "实证型",
            TopicType.GENERAL: "通用型"
        }
        return names.get(topic_type, "未知类型")

    # ==================== 应用型框架（三圈交集） ====================

    def _application_framework(self, title: str) -> Dict:
        """应用型综述框架 - 三圈交集"""
        return {
            'structure': '三圈交集式',
            'description': '证明「工具+场景+目标」三者结合的必要性和可行性',
            'sections': [
                {
                    'title': '研究对象分析',
                    'description': '分析研究对象的重要性和特殊性',
                    'key_points': ['研究对象的发展现状', '研究对象的特征', '研究对象面临的挑战']
                },
                {
                    'title': '优化目标现状',
                    'description': '分析优化目标的现状与痛点',
                    'key_points': ['优化目标的理论基础', '当前实践中的问题', '改进需求']
                },
                {
                    'title': '方法论应用',
                    'description': '分析方法论的应用可行性',
                    'key_points': ['方法论的理论框架', '在相关领域的应用', '优势与局限']
                },
                {
                    'title': '研究缺口与机会',
                    'description': '识别三者结合的研究空白',
                    'key_points': ['现有研究的不足', '本研究的创新点', '预期贡献']
                }
            ]
        }

    def _application_queries(self, title: str) -> List[Dict]:
        """应用型检索查询"""
        return [
            {'query': f'{title} 应用', 'section': '研究对象'},
            {'query': f'{title} 优化 改进', 'section': '优化目标'},
            {'query': f'{title} 方法论', 'section': '方法论'}
        ]

    # ==================== 评价型框架（金字塔式） ====================

    def _evaluation_framework(self, title: str) -> Dict:
        """评价型综述框架 - 金字塔式"""
        object_match = re.search(r'(.+?)(?:成熟度|评价|评估|体系)', title)
        evaluation_object = object_match.group(1) if object_match else "研究对象"

        return {
            'structure': '金字塔式',
            'description': '从理论基础到实践应用，层层递进证明评价体系的科学性',
            'sections': [
                {
                    'title': '评价理论基础',
                    'description': f'确立{evaluation_object}评价的理论依据',
                    'key_points': [
                        f'{evaluation_object}的概念界定',
                        '评价理论的发展历程',
                        '成熟度模型的理论基础',
                        '评价体系的设计原则'
                    ]
                },
                {
                    'title': '评价维度与指标',
                    'description': '梳理现有研究的评价维度和指标体系',
                    'key_points': [
                        '主流评价维度梳理',
                        '关键评价指标总结',
                        '指标权重确定方法',
                        '维度间关系分析'
                    ]
                },
                {
                    'title': '评价方法与技术',
                    'description': '总结评价方法和技术手段',
                    'key_points': [
                        '定性评价方法',
                        '定量评价方法',
                        '综合评价方法',
                        '数据采集与处理技术'
                    ]
                },
                {
                    'title': '评价实践与应用',
                    'description': '分析评价体系的实践应用情况',
                    'key_points': [
                        '行业应用案例',
                        '评价效果分析',
                        '存在问题与改进',
                        '应用趋势与展望'
                    ]
                },
                {
                    'title': '研究缺口',
                    'description': '识别现有评价体系的不足',
                    'key_points': [
                        '理论基础的薄弱环节',
                        '维度覆盖的缺失',
                        '方法适用性的局限',
                        '本研究的改进方向'
                    ]
                }
            ]
        }

    def _evaluation_queries(self, title: str) -> List[Dict]:
        """评价型检索查询"""
        object_match = re.search(r'(.+?)(?:成熟度|评价|评估|体系)', title)
        evaluation_object = object_match.group(1) if object_match else "质量管理"

        return [
            {'query': f'{evaluation_object} 评价 理论', 'section': '评价理论基础'},
            {'query': f'{evaluation_object} 成熟度 模型', 'section': '评价理论基础'},
            {'query': f'{evaluation_object} 评价 指标 维度', 'section': '评价维度与指标'},
            {'query': f'{evaluation_object} 评价 方法', 'section': '评价方法与技术'},
            {'query': f'{evaluation_object} 评价 实践 案例', 'section': '评价实践与应用'}
        ]

    # ==================== 理论型框架（溯源式） ====================

    def _theoretical_framework(self, title: str) -> Dict:
        """理论型综述框架 - 溯源式"""
        return {
            'structure': '溯源式',
            'description': '从理论源头出发，梳理理论发展脉络',
            'sections': [
                {
                    'title': '理论起源',
                    'description': '追溯理论的起源和早期发展',
                    'key_points': ['理论起源背景', '奠基性研究', '核心概念界定']
                },
                {
                    'title': '理论发展',
                    'description': '梳理理论的发展历程',
                    'key_points': ['发展阶段划分', '重要理论突破', '代表性研究']
                },
                {
                    'title': '当前研究现状',
                    'description': '分析当前理论研究的重点',
                    'key_points': ['研究热点', '主要学派', '争议问题']
                },
                {
                    'title': '理论应用',
                    'description': '总结理论的实践应用',
                    'key_points': ['应用领域', '应用效果', '理论验证']
                },
                {
                    'title': '理论前沿与展望',
                    'description': '展望理论发展方向',
                    'key_points': ['前沿问题', '发展趋势', '未来方向']
                }
            ]
        }

    def _theoretical_queries(self, title: str) -> List[Dict]:
        """理论型检索查询"""
        return [
            {'query': f'{title} 理论 起源', 'section': '理论起源'},
            {'query': f'{title} 理论 发展', 'section': '理论发展'},
            {'query': f'{title} 研究现状', 'section': '当前研究现状'},
            {'query': f'{title} 理论 应用', 'section': '理论应用'}
        ]

    # ==================== 实证型框架（问题-方案式） ====================

    def _empirical_framework(self, title: str) -> Dict:
        """实证型综述框架 - 问题-方案式"""
        # 提取变量关系
        variables_match = re.search(r'(.+?)(?:对|与)(.+?)(?:影响|效应|关系)', title)
        if variables_match:
            iv = variables_match.group(1).strip()  # 自变量
            dv = variables_match.group(2).strip()  # 因变量
        else:
            iv = "自变量"
            dv = "因变量"

        return {
            'structure': '问题-方案式',
            'description': '围绕研究问题和假设，梳理相关实证研究',
            'sections': [
                {
                    'title': '研究背景与问题',
                    'description': '阐述研究背景和核心问题',
                    'key_points': [
                        f'{iv}的发展背景',
                        f'{dv}面临的挑战',
                        '研究问题提出'
                    ]
                },
                {
                    'title': f'{iv}的理论基础与测量',
                    'description': f'梳理{iv}的相关理论和测量方法',
                    'key_points': [
                        f'{iv}的概念界定',
                        f'{iv}的维度划分',
                        f'{iv}的测量方法',
                        f'{iv}的相关研究'
                    ]
                },
                {
                    'title': f'{dv}的理论基础与测量',
                    'description': f'梳理{dv}的相关理论和测量方法',
                    'key_points': [
                        f'{dv}的概念界定',
                        f'{dv}的维度划分',
                        f'{dv}的测量方法',
                        f'{dv}的相关研究'
                    ]
                },
                {
                    'title': f'{iv}对{dv}的影响机制',
                    'description': '总结实证研究的主要发现',
                    'key_points': [
                        '直接影响效应',
                        '中介机制',
                        '调节效应',
                        '研究结论对比'
                    ]
                },
                {
                    'title': '研究不足与展望',
                    'description': '指出研究不足和未来方向',
                    'key_points': [
                        '样本与方法的局限',
                        '情境因素的考虑',
                        '未来研究方向'
                    ]
                }
            ]
        }

    def _empirical_queries(self, title: str) -> List[Dict]:
        """实证型检索查询"""
        # 尝试提取变量
        variables_match = re.search(r'(.+?)(?:对|与)(.+?)(?:影响|效应|关系)', title)
        if variables_match:
            iv = variables_match.group(1).strip()
            dv = variables_match.group(2).strip()
        else:
            iv = dv = title

        return [
            {'query': f'{iv} 理论 测量', 'section': f'{iv}的理论基础与测量'},
            {'query': f'{dv} 理论 测量', 'section': f'{dv}的理论基础与测量'},
            {'query': f'{iv} {dv} 影响', 'section': '影响机制'},
            {'query': f'{iv} {dv} 实证', 'section': '影响机制'},
            {'query': f'{iv} {dv} 中介 调节', 'section': '影响机制'}
        ]

    # ==================== 通用型框架 ====================

    def _general_framework(self, title: str) -> Dict:
        """通用综述框架"""
        return {
            'structure': '通用结构',
            'description': '采用标准文献综述结构',
            'sections': [
                {
                    'title': '引言',
                    'description': '介绍研究背景和意义',
                    'key_points': ['研究背景', '研究意义', '综述目标']
                },
                {
                    'title': '研究现状',
                    'description': '梳理相关研究现状',
                    'key_points': ['国内研究', '国外研究', '对比分析']
                },
                {
                    'title': '主要问题与挑战',
                    'description': '总结主要问题和挑战',
                    'key_points': ['技术问题', '管理问题', '研究挑战']
                },
                {
                    'title': '发展趋势',
                    'description': '分析发展趋势',
                    'key_points': ['技术趋势', '应用趋势', '研究方向']
                }
            ]
        }

    def _general_queries(self, title: str) -> List[Dict]:
        """通用检索查询"""
        return [
            {'query': f'{title} 研究现状', 'section': '研究现状'},
            {'query': f'{title} 综述', 'section': '研究现状'},
            {'query': f'{title} 发展趋势', 'section': '发展趋势'}
        ]
