"""
测试研究方向配置功能

验证：
1. 获取研究方向列表
2. 根据ID获取研究方向详情
3. 根据文本匹配研究方向
4. 缩写词扩展功能
"""
import sys
sys.path.append('/Users/zhancc/Github/AutoOverview/backend')

from config.research_directions import (
    get_all_directions,
    get_direction_by_id,
    get_direction_abbreviations,
    get_direction_keywords,
    match_direction_by_text,
    expand_abbreviation_by_direction,
)


def test_get_all_directions():
    """测试获取所有研究方向"""
    print("=" * 80)
    print("测试1: 获取所有研究方向")
    print("=" * 80)

    directions = get_all_directions()

    print(f"\n共有 {len(directions)} 个研究方向:\n")

    for direction in directions:
        print(f"【{direction['name']}】")
        print(f"  ID: {direction['id']}")
        print(f"  英文名: {direction['name_en']}")
        print(f"  描述: {direction['description']}")
        print(f"  关键词数量: {len(direction['keywords'])}")
        print(f"  缩写词数量: {len(direction['abbreviations'])}")
        print(f"  子方向数量: {len(direction['sub_directions'])}")
        print()


def test_get_direction_by_id():
    """测试根据ID获取研究方向"""
    print("=" * 80)
    print("测试2: 根据ID获取研究方向")
    print("=" * 80)

    # 测试计算机科学
    print("\n【计算机科学】")
    computer = get_direction_by_id("computer")
    if computer:
        print(f"  名称: {computer['name']}")
        print(f"  英文名: {computer['name_en']}")
        print(f"  部分关键词: {computer['keywords'][:5]}")
        print(f"  部分缩写: {list(computer['abbreviations'].keys())[:5]}")

    # 测试材料科学
    print("\n【材料科学】")
    materials = get_direction_by_id("materials")
    if materials:
        print(f"  名称: {materials['name']}")
        print(f"  英文名: {materials['name_en']}")
        print(f"  部分关键词: {materials['keywords'][:5]}")
        print(f"  部分缩写: {list(materials['abbreviations'].keys())[:5]}")

    # 测试管理学
    print("\n【管理学】")
    management = get_direction_by_id("management")
    if management:
        print(f"  名称: {management['name']}")
        print(f"  英文名: {management['name_en']}")
        print(f"  部分关键词: {management['keywords'][:5]}")
        print(f"  部分缩写: {list(management['abbreviations'].keys())[:5]}")


def test_match_direction_by_text():
    """测试根据文本匹配研究方向"""
    print("\n" + "=" * 80)
    print("测试3: 根据文本匹配研究方向")
    print("=" * 80)

    test_cases = [
        {
            "text": "机器学习算法优化",
            "expected": "computer"
        },
        {
            "text": "纳米材料合成",
            "expected": "materials"
        },
        {
            "text": "供应链管理优化",
            "expected": "management"
        },
        {
            "text": "深度学习在材料科学中的应用",
            "expected": "materials"  # 优先匹配材料科学
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        expected = test_case["expected"]

        result = match_direction_by_text(text)
        status = "✅" if result == expected else "❌"

        print(f"\n{i}. {text}")
        print(f"   预期: {expected}")
        print(f"   实际: {result}")
        print(f"   {status}")


def test_expand_abbreviation():
    """测试缩写词扩展"""
    print("\n" + "=" * 80)
    print("测试4: 根据研究方向扩展缩写词")
    print("=" * 80)

    test_cases = [
        {
            "abbr": "ML",
            "direction": "computer",
            "expected": "Machine Learning"
        },
        {
            "abbr": "XRD",
            "direction": "materials",
            "expected": "X-ray Diffraction"
        },
        {
            "abbr": "KPI",
            "direction": "management",
            "expected": "Key Performance Indicator"
        },
        {
            "abbr": "CAS",
            "direction": "computer",
            "expected": "Computer Algebra System"
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        abbr = test_case["abbr"]
        direction = test_case["direction"]
        expected = test_case["expected"]

        result = expand_abbreviation_by_direction(abbr, direction)
        status = "✅" if result == expected else "❌"

        print(f"\n{i}. {abbr} (研究方向: {direction})")
        print(f"   预期: {expected}")
        print(f"   实际: {result}")
        print(f"   {status}")


def test_api_usage():
    """测试 API 使用示例"""
    print("\n" + "=" * 80)
    print("测试5: API 使用示例")
    print("=" * 80)

    print("\n【获取研究方向列表】")
    print("GET /api/research-directions")
    print()
    print("响应示例:")
    import json
    directions = get_all_directions()
    # 只显示每个方向的部分信息
    simplified = [
        {
            "id": d["id"],
            "name": d["name"],
            "name_en": d["name_en"],
            "description": d["description"][:50] + "..."
        }
        for d in directions
    ]
    print(json.dumps({"success": True, "data": simplified}, indent=2, ensure_ascii=False))

    print("\n\n【创建综述任务（指定研究方向）】")
    print("POST /api/smart-generate")
    print()
    print("请求示例:")
    print(json.dumps({
        "topic": "ML算法优化研究",
        "research_direction_id": "computer",  # 指定计算机科学
        "target_count": 50,
        "recent_years_ratio": 0.5,
        "english_ratio": 0.3
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # 运行所有测试
    test_get_all_directions()
    test_get_direction_by_id()
    test_match_direction_by_text()
    test_expand_abbreviation()
    test_api_usage()

    print("\n" + "=" * 80)
    print("所有测试完成")
    print("=" * 80)
