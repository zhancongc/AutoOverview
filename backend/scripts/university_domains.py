"""
大学邮箱域名 → 大学名称映射表

用于从收件人邮箱地址推断其所在大学，个性化推广邮件。
"""
from __future__ import annotations

# 域名 → 大学名称（小写 key）
_DOMAIN_MAP: dict[str, str] = {
    # === UK Universities ===
    "ox.ac.uk": "University of Oxford",
    "cam.ac.uk": "University of Cambridge",
    "imperial.ac.uk": "Imperial College London",
    "ucl.ac.uk": "UCL",
    "ed.ac.uk": "University of Edinburgh",
    "manchester.ac.uk": "University of Manchester",
    "kcl.ac.uk": "King's College London",
    "lse.ac.uk": "London School of Economics",
    "bristol.ac.uk": "University of Bristol",
    "warwick.ac.uk": "University of Warwick",
    "gla.ac.uk": "University of Glasgow",
    "leeds.ac.uk": "University of Leeds",
    "sheffield.ac.uk": "University of Sheffield",
    "nottingham.ac.uk": "University of Nottingham",
    "birmingham.ac.uk": "University of Birmingham",
    "southampton.ac.uk": "University of Southampton",
    "york.ac.uk": "University of York",
    "durham.ac.uk": "Durham University",
    "st-andrews.ac.uk": "University of St Andrews",
    "exeter.ac.uk": "University of Exeter",
    "liverpool.ac.uk": "University of Liverpool",
    "cardiff.ac.uk": "Cardiff University",
    "qmul.ac.uk": "Queen Mary University of London",
    "bath.ac.uk": "University of Bath",
    "reading.ac.uk": "University of Reading",
    "surrey.ac.uk": "University of Surrey",
    "sussex.ac.uk": "University of Sussex",
    "bbk.ac.uk": "Birkbeck, University of London",
    "soas.ac.uk": "SOAS University of London",
    "aber.ac.uk": "Aberystwyth University",
    "stir.ac.uk": "University of Stirling",
    "hw.ac.uk": "Heriot-Watt University",
    "qub.ac.uk": "Queen's University Belfast",
    "ulster.ac.uk": "Ulster University",
    "lancaster.ac.uk": "Lancaster University",
    "newcastle.ac.uk": "Newcastle University",
    "le.ac.uk": "University of Leicester",
    "contacts.bham.ac.uk": "University of Birmingham",

    # === US Universities ===
    "harvard.edu": "Harvard University",
    "mit.edu": "MIT",
    "stanford.edu": "Stanford University",
    "berkeley.edu": "UC Berkeley",
    "columbia.edu": "Columbia University",
    "yale.edu": "Yale University",
    "princeton.edu": "Princeton University",
    "uchicago.edu": "University of Chicago",
    "upenn.edu": "University of Pennsylvania",
    "caltech.edu": "Caltech",
    "cornell.edu": "Cornell University",
    "bu.edu": "Boston University",
    "nyu.edu": "New York University",
    "gatech.edu": "Georgia Tech",
    "umich.edu": "University of Michigan",
    "illinois.edu": "University of Illinois",
    "utexas.edu": "University of Texas at Austin",
    "wisc.edu": "University of Wisconsin-Madison",
    "washington.edu": "University of Washington",
    "ucla.edu": "UCLA",
    "ucsd.edu": "UC San Diego",
    "northwestern.edu": "Northwestern University",
    "duke.edu": "Duke University",
    "jhu.edu": "Johns Hopkins University",
    "cmu.edu": "Carnegie Mellon University",
    "brown.edu": "Brown University",
    "dartmouth.edu": "Dartmouth College",
    "rice.edu": "Rice University",
    "vanderbilt.edu": "Vanderbilt University",
    "nd.edu": "University of Notre Dame",
    "usc.edu": "University of Southern California",
    "umn.edu": "University of Minnesota",
    "osu.edu": "Ohio State University",
    "psu.edu": "Penn State University",
    "purdue.edu": "Purdue University",
    "virginia.edu": "University of Virginia",
    "unc.edu": "UNC Chapel Hill",
    "ufl.edu": "University of Florida",
    "asu.edu": "Arizona State University",
    "colorado.edu": "University of Colorado Boulder",
    "arizona.edu": "University of Arizona",
    "indiana.edu": "Indiana University",
    "uga.edu": "University of Georgia",
    "ucdavis.edu": "UC Davis",
    "uci.edu": "UC Irvine",
    "ucsb.edu": "UC Santa Barbara",
    "ucsc.edu": "UC Santa Cruz",
    "ucr.edu": "UC Riverside",
    "ucmerced.edu": "UC Merced",
}


def get_university(email: str) -> str:
    """从邮箱地址推断大学名称。匹配失败返回空字符串。"""
    domain = email.split("@")[-1].lower().strip()

    # 精确匹配
    if domain in _DOMAIN_MAP:
        return _DOMAIN_MAP[domain]

    # 子域名匹配（如 student.manchester.ac.uk → manchester.ac.uk）
    for suffix, name in _DOMAIN_MAP.items():
        if domain.endswith("." + suffix):
            return name

    return ""


def get_university_abbrev(email: str) -> str:
    """获取大学缩写（用于邮件中的友好称呼）。"""
    uni = get_university(email)
    if not uni:
        return ""

    # 已知的简称映射
    _abbrevs = {
        "University of Oxford": "Oxford",
        "University of Cambridge": "Cambridge",
        "Imperial College London": "Imperial",
        "University of Manchester": "UoM",
        "King's College London": "KCL",
        "London School of Economics": "LSE",
        "University of Edinburgh": "Edinburgh",
        "University of Bristol": "Bristol",
        "University of Warwick": "Warwick",
        "University of Glasgow": "Glasgow",
        "University of Leeds": "Leeds",
        "University of Sheffield": "Sheffield",
        "University of Nottingham": "Nottingham",
        "University of Birmingham": "Birmingham",
        "University of Southampton": "Southampton",
        "University of York": "York",
        "Durham University": "Durham",
        "University of St Andrews": "St Andrews",
        "University of Exeter": "Exeter",
        "University of Liverpool": "Liverpool",
        "Cardiff University": "Cardiff",
        "Queen Mary University of London": "QMUL",
        "University of Bath": "Bath",
        "Newcastle University": "Newcastle",
        "University of Leicester": "Leicester",
        "Harvard University": "Harvard",
        "Stanford University": "Stanford",
        "Columbia University": "Columbia",
        "Yale University": "Yale",
        "Princeton University": "Princeton",
        "University of Chicago": "UChicago",
        "University of Pennsylvania": "Penn",
        "Cornell University": "Cornell",
        "Boston University": "BU",
        "New York University": "NYU",
        "Northwestern University": "Northwestern",
        "Duke University": "Duke",
        "Brown University": "Brown",
        "Dartmouth College": "Dartmouth",
        "University of Southern California": "USC",
        "University of Michigan": "UMich",
        "University of Washington": "UW",
        "University of Wisconsin-Madison": "UW-Madison",
        "University of Texas at Austin": "UT Austin",
        "University of Minnesota": "UMN",
        "Ohio State University": "OSU",
        "Penn State University": "Penn State",
        "University of Virginia": "UVA",
        "University of Florida": "UF",
        "University of Colorado Boulder": "CU Boulder",
        "University of Georgia": "UGA",
        "University of Notre Dame": "Notre Dame",
        "Queen's University Belfast": "QUB",
        "Lancaster University": "Lancaster",
    }

    return _abbrevs.get(uni, uni)
