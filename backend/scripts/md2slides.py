#!/usr/bin/env python3
"""
Markdown 综述 → reveal.js 单文件 HTML 幻灯片转换器

核心原则：slides 展示关键词和要点，不是搬原文。
- 段落 → 提取核心观点，一句话概括
- 列表 → 每项截断到关键词
- 大段内容 → 强制拆分到多个 slide
- 参考文献极小字体密集排列

用法:
  python md2slides.py input.md [-o output.html] [--title "标题"] [--lang zh|en]
"""
import argparse
import html as html_mod
import re
from dataclasses import dataclass, field
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# CSS 模板 — 紧凑版，专为短视频优化
# ═══════════════════════════════════════════════════════════════════════════════

CSS_TEMPLATE = r"""
:root {
  --ink: #1a1a2e;
  --paper: #faf8f5;
  --warm-gray: #6b6b7b;
  --accent: #c0392b;
  --accent-bg: rgba(192,57,43,0.08);
  --border: #e0dcd6;
  --card-bg: #ffffff;
  --shadow: rgba(26,26,46,0.06);
  --font-serif: 'Crimson Pro','Noto Serif SC','Georgia',serif;
  --font-sans: 'Source Sans 3','Noto Sans SC',sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--font-sans);background:var(--paper);color:var(--ink)}
.reveal{font-family:var(--font-sans);font-size:14px;line-height:1.4}
.reveal .slides{text-align:left}
.reveal .slides section{padding:20px 40px;height:100%;overflow:hidden}
.reveal h1,.reveal h2,.reveal h3{
  font-family:var(--font-serif);color:var(--ink);
  text-transform:none;letter-spacing:normal;font-weight:600;
}
.reveal h1{font-size:1.5em;line-height:1.25}
.reveal h2{font-size:1.2em;margin-bottom:0.3em}
.reveal h3{font-size:0.95em;margin-bottom:0.25em;color:var(--accent)}
.reveal p{margin-bottom:0.3em;line-height:1.4}
.reveal strong{color:var(--ink);font-weight:600}

/* Layout */
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}
.three-col{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;align-items:start}

/* Cards */
.card{
  background:var(--card-bg);border:1px solid var(--border);
  border-radius:6px;padding:10px 12px;box-shadow:0 1px 4px var(--shadow);
}
.card-accent{border-left:3px solid var(--accent)}
.card h3{font-family:var(--font-sans);font-size:0.85em;font-weight:600;color:var(--accent);margin-bottom:4px}
.card p,.card li{font-size:0.75em;line-height:1.35}

/* Tables */
.reveal table{width:100%;border-collapse:collapse;font-size:0.65em;line-height:1.3}
.reveal thead th{background:var(--ink);color:white;padding:4px 6px;text-align:left;font-weight:500;font-size:0.9em}
.reveal tbody td{padding:3px 6px;border-bottom:1px solid var(--border);vertical-align:top}
.reveal tbody tr:nth-child(even){background:rgba(0,0,0,0.02)}

/* Lists */
.reveal ul,.reveal ol{margin-left:1em;margin-bottom:0.3em}
.reveal li{margin-bottom:0.15em;line-height:1.35;font-size:0.82em}

/* Highlights */
.highlight{color:var(--accent);font-weight:600}
.tag{display:inline-block;background:var(--accent);color:white;padding:1px 6px;border-radius:2px;font-size:0.7em;font-weight:600}
.small{font-size:0.75em;color:var(--warm-gray)}
.tiny{font-size:0.6em;color:var(--warm-gray);line-height:1.25}
.divider{width:50px;height:2px;background:var(--accent);margin:8px 0;border-radius:2px}
.section-num{font-family:var(--font-serif);font-size:3em;font-weight:300;color:rgba(192,57,43,0.1);position:absolute;top:12px;right:30px;line-height:1}

/* Timeline */
.timeline{position:relative;padding-left:20px}
.timeline::before{content:'';position:absolute;left:6px;top:4px;bottom:4px;width:2px;background:var(--border)}
.timeline-item{position:relative;margin-bottom:6px}
.timeline-item::before{content:'';position:absolute;left:-20px;top:5px;width:8px;height:8px;border-radius:50%;background:var(--accent)}
.timeline-item h4{font-size:0.8em;font-weight:600;margin-bottom:1px}
.timeline-item p{font-size:0.72em;color:var(--warm-gray);margin:0}

/* Title */
.title-slide-content{display:flex;flex-direction:column;justify-content:center;align-items:center;height:100%;text-align:center}
.title-slide-content h1{font-size:1.8em;font-weight:700;margin-bottom:8px;line-height:1.3}
.title-subtitle{font-size:1em;color:var(--warm-gray);font-style:italic;font-family:var(--font-serif);margin-bottom:16px}
.title-meta{font-size:0.8em;color:var(--warm-gray)}
.title-divider{width:80px;height:2px;background:var(--accent);margin:14px auto;border-radius:2px}

/* Section Divider */
.section-divider{display:flex;flex-direction:column;justify-content:center;align-items:center;height:100%;text-align:center}
.section-divider h1{font-size:1.8em;color:var(--accent);margin-bottom:6px}
.section-divider p{font-size:0.85em;color:var(--warm-gray)}

/* Thank You */
.thank-you{display:flex;flex-direction:column;justify-content:center;align-items:center;height:100%;text-align:center}
.thank-you h1{font-size:2.5em;color:var(--accent);margin-bottom:8px}
.thank-you p{font-size:0.95em;color:var(--warm-gray)}

/* References — extremely compact */
.ref-grid{columns:3;column-gap:14px;font-size:0.55em;line-height:1.2;color:var(--warm-gray)}
.ref-grid p{margin:0 0 2px 0;break-inside:avoid}

/* Reveal overrides */
.reveal .slide-number{font-family:var(--font-sans);font-size:0.6em;color:var(--warm-gray);background:transparent}
.reveal .controls{color:var(--accent)}
"""

# ═══════════════════════════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ContentBlock:
    type: str          # 'paragraph', 'list', 'ordered_list', 'table'
    lines: list = field(default_factory=list)

@dataclass
class Section:
    title: str
    number: str = ""
    level: int = 2
    blocks: list = field(default_factory=list)
    subsections: list = field(default_factory=list)

# ═══════════════════════════════════════════════════════════════════════════════
# Markdown 解析（与之前相同）
# ═══════════════════════════════════════════════════════════════════════════════

_HEADING_RE = re.compile(r'^(#{1,4})\s+(.+)$')
_NUM_HEADING_RE = re.compile(r'^(\d+(?:\.\d+)*)\.?\s+(.+)$')
_BOLD_HEADING_RE = re.compile(r'^\*\*(.+?)\*\*$')
_TABLE_ROW_RE = re.compile(r'^\|.+\|$')
_TABLE_SEP_RE = re.compile(r'^\|[\s:|-]+\|$')
_UNORDERED_LIST_RE = re.compile(r'^[-*]\s+')
_ORDERED_LIST_RE = re.compile(r'^\d+\.\s+')
_REF_LINE_RE = re.compile(r'^\[(\d+)\]\s*')
_EMPTY_RE = re.compile(r'^\s*$')


def parse_markdown(text: str) -> tuple:
    lines = text.split('\n')
    title = ""
    meta_line = ""
    sections = []
    references = []
    i = 0

    title_lines = []
    while i < len(lines) and len(title_lines) < 2:
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        m = _HEADING_RE.match(line)
        if m and m.group(1) == '#':
            title = m.group(2).strip()
            i += 1
            break
        title_lines.append(line)
        i += 1

    if not title and title_lines:
        title = title_lines[0]
    if len(title_lines) > 1:
        meta_line = title_lines[1]

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('文献统计') or line.startswith('Literature'):
            meta_line = line
            i += 1
            continue
        break

    current_section = None
    current_subsection = None
    prev_was_blank = True
    current_block = None
    in_references = False

    def flush_block():
        nonlocal current_block
        if current_block and current_block.lines:
            target = current_subsection or current_section
            if target:
                target.blocks.append(current_block)
        current_block = None

    def start_block(block_type, first_line=""):
        nonlocal current_block
        flush_block()
        current_block = ContentBlock(type=block_type)
        if first_line:
            current_block.lines.append(first_line)

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        i += 1

        if _EMPTY_RE.match(stripped):
            flush_block()
            prev_was_blank = True
            continue

        if re.match(r'^#{0,3}\s*(参考文献|References)\s*$', stripped, re.I) or \
           re.match(r'^(参考文献|References)\s*$', stripped, re.I):
            flush_block()
            in_references = True
            continue

        if in_references:
            if _REF_LINE_RE.match(stripped):
                references.append(stripped)
            continue

        # ## 标题
        m = _HEADING_RE.match(stripped)
        if m:
            level = len(m.group(1))
            heading_text = m.group(2).strip()
            if level == 1 and current_section is None and sections:
                continue
            flush_block()
            if level <= 2:
                current_subsection = None
                current_section = Section(title=heading_text, level=level)
                _extract_section_number(current_section)
                sections.append(current_section)
            else:
                current_subsection = Section(title=heading_text, level=level)
                _extract_section_number(current_subsection)
                if current_section:
                    current_section.subsections.append(current_subsection)
            prev_was_blank = False
            continue

        # 数字编号行
        m = _NUM_HEADING_RE.match(stripped)
        if m and len(stripped) < 45:
            num, heading_text = m.group(1), m.group(2).strip()
            parts = num.split('.')
            if len(parts) >= 2 and parts[-1] and parts[-1].isdigit():
                flush_block()
                current_subsection = Section(title=heading_text, number=num, level=3)
                if current_section:
                    current_section.subsections.append(current_subsection)
                prev_was_blank = False
                continue
            elif len(parts) == 1 or (len(parts) == 2 and parts[-1] == ''):
                flush_block()
                current_subsection = None
                current_section = Section(title=heading_text, number=parts[0], level=2)
                sections.append(current_section)
                prev_was_blank = False
                continue

        # 粗体行
        m = _BOLD_HEADING_RE.match(stripped)
        if m and len(stripped) < 80:
            flush_block()
            heading_text = m.group(1).strip()
            current_subsection = Section(title=heading_text, level=3)
            if current_section:
                current_section.subsections.append(current_subsection)
            prev_was_blank = False
            continue

        # 短文本行标题
        if (prev_was_blank
                and len(stripped) < 25
                and not stripped.startswith(('-', '*', '|', '#', '>', '[', '`'))
                and (current_block is None or not current_block.lines)):
            flush_block()
            if current_section is None:
                current_section = Section(title=stripped, level=2)
                sections.append(current_section)
            else:
                current_subsection = Section(title=stripped, level=3)
                current_section.subsections.append(current_subsection)
            prev_was_blank = False
            continue

        prev_was_blank = False

        # 内容块
        target = current_subsection or current_section
        if not target:
            continue

        if _TABLE_ROW_RE.match(stripped) or _TABLE_SEP_RE.match(stripped):
            if not current_block or current_block.type != 'table':
                start_block('table', stripped)
            else:
                current_block.lines.append(stripped)
            continue

        if _UNORDERED_LIST_RE.match(stripped):
            if not current_block or current_block.type != 'list':
                start_block('list', stripped)
            else:
                current_block.lines.append(stripped)
            continue

        if _ORDERED_LIST_RE.match(stripped):
            if not current_block or current_block.type != 'ordered_list':
                start_block('ordered_list', stripped)
            else:
                current_block.lines.append(stripped)
            continue

        if not current_block or current_block.type != 'paragraph':
            start_block('paragraph', stripped)
        else:
            current_block.lines.append(stripped)

    flush_block()
    return title, meta_line, sections, references


def _extract_section_number(section: Section):
    m = re.match(r'^(\d+(?:\.\d+)*)\s*', section.title)
    if m:
        section.number = m.group(1)
        section.title = section.title[m.end():].strip()
    if section.number.endswith('.'):
        section.number = section.number[:-1]

# ═══════════════════════════════════════════════════════════════════════════════
# 内联 Markdown → HTML
# ═══════════════════════════════════════════════════════════════════════════════

def inline_md(text: str) -> str:
    text = html_mod.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'\[(\d+(?:[,，]\s*\d+)*)\]', r'<span class="tag">[\1]</span>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


def shorten(text: str, limit: int = 80) -> str:
    """截断文本，适合 slides 的短句"""
    if len(text) <= limit:
        return text
    # 优先在句号/分号处截断
    for sep in ['。', '；', '，', '、', ' ']:
        pos = text[:limit + 20].rfind(sep)
        if limit * 0.5 < pos < limit + 20:
            return text[:pos + 1]
    return text[:limit] + '…'


def extract_key_point(text: str) -> str:
    """从段落中提取关键观点（一句话）"""
    # 如果有句号，取第一句
    for sep in ['。', '！', '？']:
        if sep in text:
            first = text[:text.index(sep) + 1]
            return shorten(first, 90)
    return shorten(text, 90)

# ═══════════════════════════════════════════════════════════════════════════════
# 表格
# ═══════════════════════════════════════════════════════════════════════════════

def parse_table(lines: list[str]) -> str:
    data_lines = [l for l in lines if not _TABLE_SEP_RE.match(l.strip())]
    if not data_lines:
        return ""

    rows = []
    for line in data_lines:
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rows.append(cells)

    if not rows:
        return ""

    col_count = len(rows[0])
    for row in rows:
        while len(row) < col_count:
            row.append("")

    parts = ['<table><thead><tr>']
    for cell in rows[0]:
        parts.append(f'<th>{inline_md(cell)}</th>')
    parts.append('</tr></thead><tbody>')

    for row in rows[1:]:
        parts.append('<tr>')
        for cell in row:
            parts.append(f'<td>{inline_md(cell)}</td>')
        parts.append('</tr>')

    parts.append('</tbody></table>')
    return ''.join(parts)

# ═══════════════════════════════════════════════════════════════════════════════
# Slide 渲染 — 紧凑版
# ═══════════════════════════════════════════════════════════════════════════════

def render_title_slide(title: str, meta_line: str, lang: str) -> str:
    subtitle = "Literature Review" if lang == 'en' else "文献综述"
    meta = inline_md(meta_line) if meta_line else subtitle
    return f'''<section>
  <div class="title-slide-content">
    <h1>{inline_md(title)}</h1>
    <div class="title-divider"></div>
    <p class="title-subtitle">{subtitle}</p>
    <p class="title-meta">{meta}</p>
  </div>
</section>'''


def render_outline_slide(sections: list[Section], lang: str) -> str:
    heading = "Outline" if lang == 'en' else "综述框架"
    main = [s for s in sections if s.level <= 2]

    def cards(items):
        parts = []
        for s in items:
            num = f'<span class="highlight">{s.number}</span>' if s.number else ''
            label = s.title if len(s.title) <= 20 else s.title[:18] + '…'
            parts.append(
                f'<div class="card" style="padding:8px 10px">'
                f'<p style="margin:0;font-size:0.82em"><strong>{num}</strong> '
                f'{num and "· " or ""}{inline_md(label)}</p></div>'
            )
        return '\n'.join(parts)

    # 自动选择列数：≤4 用两列，>4 用三列
    col = 'two-col' if len(main) <= 4 else 'three-col'
    return f'''<section>
  <h2>{heading}</h2><div class="divider"></div>
  <div class="{col}" style="margin-top:10px">{cards(main)}</div>
</section>'''


def render_section_divider(section: Section) -> str:
    num = f'<span class="section-num">{section.number}</span>' if section.number else ''
    return f'''<section>
  <div class="section-divider">{num}<h1>{inline_md(section.title)}</h1></div>
</section>'''


# ── 紧凑内容渲染 ──

def render_blocks_compact(blocks: list[ContentBlock], max_items: int = 5) -> str:
    """渲染内容块为紧凑 HTML，控制总量"""
    parts = []
    item_count = 0
    for block in blocks:
        if item_count >= max_items:
            break
        if block.type == 'table':
            parts.append(parse_table(block.lines))
            item_count += 1
        elif block.type == 'list':
            items = []
            for l in block.lines[:max_items]:
                text = l.lstrip('- ').lstrip('* ')
                text = re.sub(r'^\d+\.\s+', '', text)
                items.append(shorten(inline_md(text), 70))
            parts.append('<ul>' + ''.join(f'<li>{it}</li>' for it in items) + '</ul>')
            item_count += len(items)
        elif block.type == 'ordered_list':
            items = []
            for l in block.lines[:max_items]:
                text = re.sub(r'^\d+\.\s+', '', l)
                items.append(shorten(inline_md(text), 70))
            parts.append('<ol>' + ''.join(f'<li>{it}</li>' for it in items) + '</ol>')
            item_count += len(items)
        elif block.type == 'paragraph':
            text = ' '.join(block.lines)
            parts.append(f'<p class="small">{inline_md(extract_key_point(text))}</p>')
            item_count += 1
    return '\n'.join(parts)


def render_subsection_card(sub: Section) -> str:
    """子 section → 紧凑卡片"""
    content = render_blocks_compact(sub.blocks, max_items=4)
    return f'''<div class="card card-accent">
  <h3>{inline_md(sub.title)}</h3>{content}
</div>'''


def render_subsection_compact(sub: Section) -> str:
    """子 section → 紧凑 HTML"""
    content = render_blocks_compact(sub.blocks, max_items=5)
    return f'''<div><h3>{inline_md(sub.title)}</h3>{content}</div>'''


# ── 布局检测 ──

def detect_layout(section: Section) -> str:
    has_table = any(b.type == 'table' for b in section.blocks)
    n_sub = len(section.subsections)
    if has_table:
        return 'table'
    if n_sub == 3:
        return 'three_col'
    if n_sub >= 2:
        return 'two_col'
    return 'list'


def render_content_slide(section: Section) -> str:
    layout = detect_layout(section)
    num = f'<span class="section-num">{section.number}</span>' if section.number else ''

    if layout == 'table':
        tbl = [b for b in section.blocks if b.type == 'table']
        other = [b for b in section.blocks if b.type != 'table']
        table_html = parse_table(tbl[0].lines) if tbl else ''
        intro = render_blocks_compact(other, 2) if other else ''
        return f'''<section>{num}
  <h2>{inline_md(section.title)}</h2><div class="divider"></div>
  {intro}{table_html}
</section>'''

    if layout == 'three_col':
        cards = [render_subsection_card(s) for s in section.subsections[:3]]
        return f'''<section>{num}
  <h2>{inline_md(section.title)}</h2><div class="divider"></div>
  <div class="three-col" style="margin-top:8px">{''.join(cards)}</div>
</section>'''

    if layout == 'two_col':
        subs = section.subsections
        if len(subs) == 2:
            l = render_subsection_compact(subs[0])
            r = render_subsection_compact(subs[1])
        elif len(subs) == 3:
            l = render_subsection_compact(subs[0])
            r = '\n'.join(render_subsection_card(s) for s in subs[1:])
        else:
            half = len(subs) // 2
            l = '\n'.join(render_subsection_compact(s) for s in subs[:half])
            r = '\n'.join(render_subsection_compact(s) for s in subs[half:])
        return f'''<section>{num}
  <h2>{inline_md(section.title)}</h2><div class="divider"></div>
  <div class="two-col" style="margin-top:8px"><div>{l}</div><div>{r}</div></div>
</section>'''

    content = render_blocks_compact(section.blocks)
    return f'''<section>{num}
  <h2>{inline_md(section.title)}</h2><div class="divider"></div>{content}
</section>'''


def should_split(section: Section) -> bool:
    total_chars = sum(len(' '.join(b.lines)) for b in section.blocks)
    for sub in section.subsections:
        total_chars += sum(len(' '.join(b.lines)) for b in sub.blocks)
    return total_chars > 400 or len(section.subsections) > 3


def render_sub_slide(section: Section, sub: Section) -> str:
    sec_num = section.number
    sub_num = sub.number or ""
    full = f"{sec_num}.{sub_num}" if sub_num else sec_num
    num = f'<span class="section-num">{full}</span>' if full else ''
    content = render_blocks_compact(sub.blocks, max_items=6)
    return f'''<section>{num}
  <h2>{inline_md(sub.title)}</h2><div class="divider"></div>{content}
</section>'''


# ── 参考文献 — 极致紧凑 ──

def render_references_slide(references: list[str], lang: str) -> str:
    if not references:
        return ""
    heading = "References" if lang == 'en' else "参考文献"
    # 所有引用放在一个 slide，三列极小字体
    ref_items = '\n'.join(f'<p>{inline_md(r)}</p>' for r in references)
    return f'''<section>
  <h2>{heading}</h2><div class="divider"></div>
  <div class="ref-grid">{ref_items}</div>
</section>'''


def render_thank_you(lang: str, title: str) -> str:
    text = "Thank You" if lang == 'en' else "谢谢"
    return f'''<section>
  <div class="thank-you"><h1>{text}</h1><div class="title-divider"></div>
    <p>{inline_md(title)}</p></div>
</section>'''

# ═══════════════════════════════════════════════════════════════════════════════
# 主生成流程
# ═══════════════════════════════════════════════════════════════════════════════

def generate_slides(md_path: str, output_path: str, title_override: str = "",
                    lang: str = "zh") -> str:
    text = Path(md_path).read_text(encoding='utf-8')
    title, meta_line, sections, references = parse_markdown(text)

    if title_override:
        title = title_override

    slides = []

    # 1. 标题
    slides.append(render_title_slide(title, meta_line, lang))

    # 2. 大纲
    main = [s for s in sections if s.level <= 2]
    if main:
        slides.append(render_outline_slide(main, lang))

    # 3. 内容
    for section in sections:
        if section.level <= 2 and section.subsections:
            slides.append(render_section_divider(section))

        if should_split(section) and section.subsections:
            for sub in section.subsections:
                slides.append(render_sub_slide(section, sub))
        else:
            slides.append(render_content_slide(section))

    # 4. 参考文献（1 页）
    ref = render_references_slide(references, lang)
    if ref:
        slides.append(ref)

    # 5. 致谢
    slides.append(render_thank_you(lang, title))

    # 拼装
    slides_html = '\n\n'.join(slides)
    html = HTML_TEMPLATE.format(
        title=html_mod.escape(title),
        css=CSS_TEMPLATE,
        slides=slides_html,
    )

    Path(output_path).write_text(html, encoding='utf-8')
    return output_path

# ═══════════════════════════════════════════════════════════════════════════════
# HTML 模板
# ═══════════════════════════════════════════════════════════════════════════════

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400&family=Source+Sans+3:wght@300;400;500;600;700&family=Noto+Serif+SC:wght@400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
  <style>{css}
  </style>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/white.css">
</head>
<body>
<div class="reveal">
  <div class="slides">
{slides}
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<script>
  Reveal.initialize({{
    hash: true, slideNumber: 'c/t', showSlideNumber: 'all',
    transition: 'fade', transitionSpeed: 'default',
    backgroundTransition: 'fade',
    width: 1100, height: 750, margin: 0.02,
    controls: true, progress: true, center: false
  }});
</script>
</body>
</html>"""

# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Markdown 综述 → reveal.js 单文件 HTML 幻灯片'
    )
    parser.add_argument('input', help='输入 Markdown 文件路径')
    parser.add_argument('-o', '--output', help='输出 HTML 文件路径（默认: input_slides.html）')
    parser.add_argument('--title', help='覆盖演示文稿标题')
    parser.add_argument('--lang', choices=['zh', 'en'], default='zh', help='语言（默认: zh）')
    args = parser.parse_args()

    output = args.output or str(Path(args.input).stem) + '_slides.html'
    result = generate_slides(args.input, output, title_override=args.title or "", lang=args.lang)
    print(f'Generated: {result}')


if __name__ == '__main__':
    main()
