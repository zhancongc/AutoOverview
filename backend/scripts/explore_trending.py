#!/usr/bin/env python3
"""
OpenAlex 研究热点探索工具（v4: 支持自定义天数、领域、数量）

用法:
  python3 scripts/explore_trending.py                        # 所有领域，默认 7 天
  python3 scripts/explore_trending.py --field llm --days 14  # LLM 领域最近 14 天
  python3 scripts/explore_trending.py --field crispr --days 30 --max 10
  python3 scripts/explore_trending.py --list                 # 列出可用领域
  python3 scripts/explore_trending.py --field llm --days 7 --json  # 输出 JSON
"""
import subprocess
import json
import argparse
import sys
from datetime import datetime, timedelta
from urllib.parse import urlencode

BASE_URL = "https://api.openalex.org"

PREPRINT_SOURCES = [
    "zenodo", "figshare", "arxiv", "biorxiv", "medrxiv",
    "chemrxiv", "preprints.org", "ssrn", "researchgate",
    "academia.edu", "coursera", "slideplayer",
]

# 领域配置：key 用于 --field 参数
FIELDS = {
    "llm": {
        "name": "大语言模型 / NLP",
        "topic_id": "T10181",
        "topic_name": "Natural Language Processing Techniques",
        "title_search": "large language model",
    },
    "agent": {
        "name": "AI Agent / 多智能体",
        "topic_id": "T10456",
        "topic_name": "Multi-Agent Systems and Negotiation",
    },
    "robot": {
        "name": "具身智能 / 机器人",
        "topic_id": "T10653",
        "topic_name": "Robot Manipulation and Learning",
    },
    "mrna": {
        "name": "mRNA / 疫苗",
        "topic_id": "T10118",
        "topic_name": "SARS-CoV-2 and COVID-19 Research",
    },
    "crispr": {
        "name": "CRISPR 基因编辑",
        "topic_id": "T10878",
        "topic_name": "CRISPR and Genetic Engineering",
    },
    "quantum": {
        "name": "量子计算",
        "topic_id": "T10682",
        "topic_name": "Quantum Computing Algorithms and Architecture",
    },
}


def api_get(endpoint: str, params: dict = None):
    query = urlencode(params or {})
    url = f"{BASE_URL}/{endpoint}?{query}"
    r = subprocess.run(["curl", "-s", "--max-time", "15", url], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)


def get_works(params: dict):
    data = api_get("works", params)
    if not data:
        return []
    return data.get("results", [])


def is_preprint(w: dict) -> bool:
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    venue = src.get("display_name", "").lower()
    return any(p in venue for p in PREPRINT_SOURCES)


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
        "is_preprint": is_preprint(w),
    }


def get_valid(papers: list) -> list:
    """过滤掉预印本和未来日期"""
    return [p for p in papers if not p["is_future"] and not p["is_preprint"]]


def print_papers(papers: list, label: str, max_show: int = 5):
    valid = get_valid(papers)
    filtered = len(papers) - len(valid)

    print(f"\n{'='*80}")
    print(f"  {label}  —  共 {len(papers)} 篇" + (f"（过滤 {filtered} 篇预印本/未来日期）" if filtered else ""))
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


def build_works_params(field: dict, date_from: str, per_page: int = 20,
                       sort: str = "publication_date:desc",
                       extra_filter: str = "") -> dict:
    """构建查询参数"""
    f = f"topics.id:{field['topic_id']},from_publication_date:{date_from},type:article"
    if extra_filter:
        f += f",{extra_filter}"
    title_search = field.get("title_search")
    if title_search:
        f += f",title.search:{title_search}"
    return {"filter": f, "sort": sort, "per_page": per_page}


def explore_field(field: dict, days: int = 7, max_show: int = 5, per_page: int = 20):
    name = field["name"]
    topic_id = field["topic_id"]
    topic_name = field.get("topic_name", "")
    title_search = field.get("title_search")
    today = datetime.now().date()
    date_from = (today - timedelta(days=days)).isoformat()

    print(f"\n\n{'#'*80}")
    print(f"## {name}")
    print(f"## Topic: {topic_name} ({topic_id})" + (f" + title.search: '{title_search}'" if title_search else ""))
    print(f"## 时间范围: {date_from} ~ {today.isoformat()}（{days} 天）")
    print(f"{'#'*80}")

    # 最新发表
    params = build_works_params(field, date_from, per_page=per_page)
    papers = get_works(params)
    parsed = [parse_work(w) for w in papers]
    print_papers(parsed, f"最近 {days} 天最新发表", max_show=max_show)

    # 数据质量
    valid = get_valid(parsed)
    n = len(valid)
    preprints = sum(p["is_preprint"] for p in parsed)
    future = sum(p["is_future"] for p in parsed)
    print(f"\n  --- 数据质量 ---")
    print(f"  原始: {len(parsed)} 篇")
    print(f"  预印本: {preprints} 篇  |  未来日期: {future} 篇")
    print(f"  有效: {n} 篇")
    if n > 0:
        ha = sum(p['has_abstract'] for p in valid)
        hd = sum(p['has_doi'] for p in valid)
        hv = sum(p['has_venue'] for p in valid)
        print(f"  有摘要: {ha}/{n} ({ha/n*100:.0f}%)")
        print(f"  有 DOI: {hd}/{n} ({hd/n*100:.0f}%)")
        print(f"  有期刊: {hv}/{n} ({hv/n*100:.0f}%)")

    return valid


def explore_field_json(field: dict, days: int = 7, per_page: int = 20) -> list:
    """返回 JSON 格式的有效论文列表"""
    today = datetime.now().date()
    date_from = (today - timedelta(days=days)).isoformat()

    params = build_works_params(field, date_from, per_page=per_page)
    papers = get_works(params)
    parsed = [parse_work(w) for w in papers]
    valid = get_valid(parsed)

    # 输出时去掉内部标记
    output = []
    for p in valid:
        output.append({
            "title": p["title"],
            "doi": p["doi"],
            "pub_date": p["pub_date"],
            "cited": p["cited"],
            "venue": p["venue"],
            "authors": p["authors"],
            "abstract": p["abstract"],
            "topics": p["topics"],
        })
    return output


def list_fields():
    print("可用领域 (--field KEY):")
    print(f"{'KEY':<12} {'名称':<20} {'Topic ID':<10} {'Topic Name'}")
    print("-" * 80)
    for key, f in FIELDS.items():
        print(f"{key:<12} {f['name']:<20} {f['topic_id']:<10} {f['topic_name']}")


def main():
    parser = argparse.ArgumentParser(
        description="OpenAlex 研究热点探索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                                  所有领域，默认 7 天
  %(prog)s --field llm --days 14            LLM 领域最近 14 天
  %(prog)s --field crispr --days 30 --max 10
  %(prog)s --field llm --days 7 --json      输出 JSON 格式
  %(prog)s --list                           列出可用领域
        """,
    )
    parser.add_argument("--field", "-f", help="领域 key（如 llm, agent, crispr）")
    parser.add_argument("--days", "-d", type=int, default=7, help="时间范围（天），默认 7")
    parser.add_argument("--max", "-m", type=int, default=5, help="每个领域展示最大论文数，默认 5")
    parser.add_argument("--per-page", "-p", type=int, default=20, help="API 每页请求数，默认 20")
    parser.add_argument("--list", "-l", action="store_true", help="列出可用领域")
    parser.add_argument("--json", "-j", action="store_true", help="以 JSON 格式输出")
    args = parser.parse_args()

    if args.list:
        list_fields()
        return

    if args.field:
        key = args.field.lower()
        if key not in FIELDS:
            print(f"未知领域: {key}")
            print(f"可用领域: {', '.join(FIELDS.keys())}")
            print(f"用 --list 查看详情")
            sys.exit(1)

    fields_to_run = (
        [(args.field, FIELDS[args.field])] if args.field
        else list(FIELDS.items())
    )

    if args.json:
        all_results = {}
        for key, field in fields_to_run:
            all_results[key] = explore_field_json(field, days=args.days, per_page=args.per_page)
        print(json.dumps(all_results, ensure_ascii=False, indent=2))
    else:
        for key, field in fields_to_run:
            explore_field(field, days=args.days, max_show=args.max, per_page=args.per_page)

        print(f"\n\n{'#'*80}")
        print("## 完成")
        print(f"{'#'*80}")
        print(f"  领域: {', '.join(k for k, _ in fields_to_run)}")
        print(f"  天数: {args.days}")


if __name__ == "__main__":
    main()
