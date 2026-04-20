#!/usr/bin/env python3
"""
探索 OpenAlex 最新论文数据质量（v2: 使用 topic_id 精确过滤）
"""
import subprocess
import json
from datetime import datetime, timedelta
from urllib.parse import urlencode

BASE_URL = "https://api.openalex.org"

# 先手动查好 topic_id，避免每次都要查
# 通过 GET /topics?search=xxx 获取
FIELDS = [
    {"name": "大语言模型", "topic_search": "large language model", "topic_id": None},
    {"name": "AI Agent", "topic_search": "AI agent", "topic_id": None},
    {"name": "具身智能", "topic_search": "embodied intelligence", "topic_id": None},
    {"name": "mRNA 疫苗", "topic_search": "mRNA vaccine", "topic_id": None},
    {"name": "CRISPR 基因编辑", "topic_search": "CRISPR gene editing", "topic_id": None},
    {"name": "量子计算", "topic_search": "quantum computing", "topic_id": None},
]


def api_get(endpoint: str, params: dict = None):
    query = urlencode(params or {})
    url = f"{BASE_URL}/{endpoint}?{query}"
    r = subprocess.run(["curl", "-s", "--max-time", "15", url], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)


def find_topic_id(search: str):
    """搜索 topic，返回最佳匹配的 topic id 和名称"""
    data = api_get("topics", {"search": search, "per_page": 5})
    if not data or not data.get("results"):
        return None, None
    # 取第一个结果
    top = data["results"][0]
    topic_id = top.get("id", "").replace("https://openalex.org/", "")
    name = top.get("display_name", "")
    return topic_id, name


def get_works(params: dict):
    data = api_get("works", params)
    if not data:
        return []
    return data.get("results", [])


def parse_work(w: dict) -> dict:
    title = w.get("title", "")
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    pub_date = w.get("publication_date", "")
    cited = w.get("cited_by_count", 0)

    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    venue = src.get("display_name", "")

    authors = []
    for a in (w.get("authorships") or [])[:3]:
        name = (a.get("author") or {}).get("display_name", "")
        if name:
            authors.append(name)
    author_str = ", ".join(authors)
    if len((w.get("authorships") or [])) > 3:
        author_str += " et al."

    abstract_inv = w.get("abstract_inverted_index")
    abstract = ""
    if abstract_inv:
        words = {}
        for word, positions in abstract_inv.items():
            for pos in positions:
                words[pos] = word
        abstract = " ".join(words[k] for k in sorted(words.keys()))

    topics = [t.get("display_name", "") for t in (w.get("topics") or [])[:3]]

    # 过滤未来日期
    is_future = False
    if pub_date:
        try:
            d = datetime.strptime(pub_date, "%Y-%m-%d")
            if d > datetime.now():
                is_future = True
        except:
            pass

    return {
        "title": title,
        "doi": doi,
        "pub_date": pub_date,
        "cited": cited,
        "venue": venue,
        "authors": author_str,
        "abstract": abstract[:400] + ("..." if len(abstract) > 400 else ""),
        "has_abstract": bool(abstract),
        "has_doi": bool(doi),
        "has_venue": bool(venue),
        "topics": topics,
        "is_future": is_future,
    }


def print_papers(papers: list, label: str, max_show: int = 5):
    # 过滤掉未来日期的论文
    valid = [p for p in papers if not p["is_future"]]
    future_count = len(papers) - len(valid)

    print(f"\n{'='*80}")
    print(f"  {label}  —  共 {len(papers)} 篇" + (f"（含 {future_count} 篇未来日期已过滤）" if future_count else ""))
    print(f"  展示前 {min(max_show, len(valid))} 篇有效论文")
    print(f"{'='*80}")
    for i, p in enumerate(valid[:max_show], 1):
        print(f"\n  [{i}] {p['title']}")
        print(f"      日期: {p['pub_date']}  |  引用: {p['cited']}  |  期刊: {p['venue']}")
        print(f"      作者: {p['authors']}")
        if p['topics']:
            print(f"      主题: {' | '.join(p['topics'])}")
        if p['abstract']:
            print(f"      摘要: {p['abstract']}")


def explore_field(field: dict):
    name = field["name"]
    today = datetime.now().date()

    print(f"\n\n{'#'*80}")
    print(f"## {name}")
    print(f"## 今日: {today}")
    print(f"{'#'*80}")

    # 查找 topic_id
    topic_id, topic_name = find_topic_id(field["topic_search"])
    if not topic_id:
        print(f"  ❌ 未找到 topic，跳过")
        return

    print(f"\n  Topic: {topic_name} ({topic_id})")

    # 1. 最近 7 天最新发表
    week_ago = (today - timedelta(days=7)).isoformat()
    papers_week = get_works({
        "filter": f"topics.id:{topic_id},from_publication_date:{week_ago},type:article",
        "sort": "publication_date:desc",
        "per_page": 15,
    })
    parsed_week = [parse_work(w) for w in papers_week]
    print_papers(parsed_week, f"最近 7 天最新发表")

    # 2. 最近 30 天高被引
    month_ago = (today - timedelta(days=30)).isoformat()
    papers_month = get_works({
        "filter": f"topics.id:{topic_id},from_publication_date:{month_ago},cited_by_count:>2,type:article",
        "sort": "cited_by_count:desc",
        "per_page": 15,
    })
    parsed_month = [parse_work(w) for w in papers_month]
    print_papers(parsed_month, f"最近 30 天高被引 (>2次)")

    # 3. 最近 90 天热门
    three_months_ago = (today - timedelta(days=90)).isoformat()
    papers_3m = get_works({
        "filter": f"topics.id:{topic_id},from_publication_date:{three_months_ago},cited_by_count:>10,type:article",
        "sort": "cited_by_count:desc",
        "per_page": 10,
    })
    parsed_3m = [parse_work(w) for w in papers_3m]
    print_papers(parsed_3m, f"最近 90 天热门 (>10次引用)")

    # 数据质量
    valid_week = [p for p in parsed_week if not p["is_future"]]
    n = len(valid_week)
    print(f"\n  --- 数据质量（最近7天，过滤未来日期后）---")
    print(f"  有效论文: {n}")
    if n > 0:
        ha = sum(p['has_abstract'] for p in valid_week)
        hd = sum(p['has_doi'] for p in valid_week)
        hv = sum(p['has_venue'] for p in valid_week)
        print(f"  有摘要: {ha}/{n} ({ha/n*100:.0f}%)")
        print(f"  有 DOI: {hd}/{n} ({hd/n*100:.0f}%)")
        print(f"  有期刊: {hv}/{n} ({hv/n*100:.0f}%)")


def main():
    for field in FIELDS:
        explore_field(field)

    print(f"\n\n{'#'*80}")
    print("## v2 总结（topic_id 精确过滤 + type:article + 过滤未来日期）")
    print(f"{'#'*80}")
    print("  对比 v1 的全文 search，topic_id 方案应该精度更高。")
    print("  关注：论文是否都和领域相关、摘要质量是否够写科普。")


if __name__ == "__main__":
    main()
