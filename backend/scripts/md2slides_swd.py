#!/usr/bin/env python3
"""
Markdown 综述 → senangwebs-deck (SWD) 单文件 HTML 幻灯片转换器

输出单文件 HTML，使用 CDN 加载 SWD + Tailwind，双击即可打开。

用法:
  python md2slides_swd.py input.md [-o output.html] [--title "标题"]
"""
import argparse
import html as html_mod
import re
from dataclasses import dataclass, field
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# CSS 覆盖 — 密集中文学术内容优化
# ═══════════════════════════════════════════════════════════════════════════════

CSS_OVERRIDE = r"""
  .swd-slide {
    padding: 2.5rem 3.5rem !important;
    font-size: 20px !important;
    line-height: 1.65 !important;
  }

  [data-swd-id] h1 { font-weight: 700; font-size: 1.8em; line-height: 1.3; }
  [data-swd-id] h2 { font-weight: 700; font-size: 1.45em; margin-bottom: 0.5em; line-height: 1.35; }
  [data-swd-id] h3 { font-weight: 700; font-size: 1.1em; margin: 0.7em 0 0.3em; line-height: 1.3; color: #1e40af; }
  [data-swd-id] p { font-size: 0.92em; margin: 0.4em 0; line-height: 1.6; }
  [data-swd-id] ul, [data-swd-id] ol { line-height: 1.75; margin: 0.3em 0; }
  [data-swd-id] li { margin-bottom: 0.2em; font-size: 0.9em; }

  /* Tables */
  [data-swd-id] table { width: 100%; border-collapse: collapse; font-size: 0.82em; margin: 0.6em 0; }
  [data-swd-id] th { background: #2563eb; color: #fff; padding: 0.5em 0.7em; text-align: left; font-weight: 600; font-size: 0.95em; }
  [data-swd-id] td { padding: 0.45em 0.7em; border-bottom: 1px solid #e2e8f0; }
  [data-swd-id] tr:nth-child(even) td { background: #f8fafc; }

  /* Blockquote */
  [data-swd-id] blockquote {
    border-left: 4px solid #2563eb; margin: 0.8em 0;
    padding: 0.6em 1em; background: #dbeafe;
    border-radius: 0 8px 8px 0; font-size: 0.88em; color: #1e40af;
  }

  /* Two/Three cols fill */
  [data-swd-layout="two-cols"] .swd-slide,
  [data-swd-layout="three-cols"] .swd-slide {
    display: flex !important;
    gap: 1.5rem !important;
    align-items: flex-start !important;
  }
  [data-swd-column] { flex: 1; min-width: 0; }
  [data-swd-column] h3:first-child { margin-top: 0; }

  /* Cover / section slides */
  [data-swd-layout="cover"] .swd-slide,
  [data-swd-layout="section"] .swd-slide {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
  }

  /* Text helpers */
  .text-muted { color: #64748b; }
  .text-primary { color: #2563eb; }
  .text-sm { font-size: 0.82em; }
  .text-xs { font-size: 0.72em; }
  .mt-1 { margin-top: 0.5em; }
  .mt-2 { margin-top: 1em; }
  .mb-1 { margin-bottom: 0.5em; }
  .text-center { text-align: center; }
  .font-bold { font-weight: 700; }
  .text-blue { color: #2563eb; }
  .text-red { color: #dc2626; }
  .text-green { color: #16a34a; }

  /* Section number watermark */
  .section-num {
    font-size: 4em; font-weight: 300; color: rgba(37,99,235,0.08);
    position: absolute; top: 0.3em; right: 0.5em; line-height: 1;
  }

  /* Reference grid */
  .ref-grid { columns: 2; column-gap: 1.5em; font-size: 0.6em; line-height: 1.3; color: #64748b; }
  .ref-grid p { margin: 0 0 0.3em 0; break-inside: avoid; }

  /* Card style for subsections */
  .swd-card {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 8px; padding: 0.8em 1em;
  }
  .swd-card-accent {
    border-left: 3px solid #2563eb;
  }

  /* Divider */
  .slide-divider { width: 50px; height: 3px; background: #2563eb; margin: 0.6em 0; border-radius: 2px; }
"""

# ═══════════════════════════════════════════════════════════════════════════════
# HTML 模板
# ═══════════════════════════════════════════════════════════════════════════════

HTML_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/senangwebs-deck/dist/swd.css">
<script src="https://cdn.tailwindcss.com"></script>
<style>{css}</style>
</head>
<body>

<main class="w-full h-screen bg-gray-100 flex items-center justify-center">
<div class="container shadow-lg">

<div
  data-swd-id="presentation"
  data-swd-theme="academic"
  data-swd-transition="slide"
>

{slides}

</div>
</div>
</main>

<script src="https://cdn.jsdelivr.net/npm/senangwebs-deck/dist/swd.js"></script>
</body>
</html>"""

# ═══════════════════════════════════════════════════════════════════════════════
# 数据结构 & 解析（复用 md2slides.py 逻辑）
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ContentBlock:
    type: str
    lines: list = field(default_factory=list)

@dataclass
class Section:
    title: str
    number: str = ""
    level: int = 2
    blocks: list = field(default_factory=list)
    subsections: list = field(default_factory=list)

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
    title, meta_line, sections, references = "", "", [], []
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

    current_section, current_subsection = None, None
    prev_blank, current_block, in_refs = True, None, False

    def flush():
        nonlocal current_block
        if current_block and current_block.lines:
            (current_subsection or current_section).blocks.append(current_block)
        current_block = None

    def start(typ, line=""):
        nonlocal current_block
        flush()
        current_block = ContentBlock(type=typ)
        if line:
            current_block.lines.append(line)

    while i < len(lines):
        line, stripped = lines[i], lines[i].strip()
        i += 1
        if _EMPTY_RE.match(stripped):
            flush(); prev_blank = True; continue
        if re.match(r'^#{0,3}\s*(参考文献|References)\s*$', stripped, re.I) or \
           re.match(r'^(参考文献|References)\s*$', stripped, re.I):
            flush(); in_refs = True; continue
        if in_refs:
            if _REF_LINE_RE.match(stripped):
                references.append(stripped)
            continue

        m = _HEADING_RE.match(stripped)
        if m:
            lv, ht = len(m.group(1)), m.group(2).strip()
            if lv == 1 and current_section is None and sections:
                prev_blank = False; continue
            flush()
            if lv <= 2:
                current_subsection = None
                current_section = Section(title=ht, level=lv)
                _ext_num(current_section); sections.append(current_section)
            else:
                current_subsection = Section(title=ht, level=lv)
                _ext_num(current_subsection)
                if current_section:
                    current_section.subsections.append(current_subsection)
            prev_blank = False; continue

        m = _NUM_HEADING_RE.match(stripped)
        if m and len(stripped) < 45:
            num, ht = m.group(1), m.group(2).strip()
            parts = num.split('.')
            flush()
            if len(parts) >= 2 and parts[-1] and parts[-1].isdigit():
                current_subsection = Section(title=ht, number=num, level=3)
                if current_section:
                    current_section.subsections.append(current_subsection)
            else:
                current_subsection = None
                n = parts[0].rstrip('.')
                current_section = Section(title=ht, number=n, level=2)
                sections.append(current_section)
            prev_blank = False; continue

        m = _BOLD_HEADING_RE.match(stripped)
        if m and len(stripped) < 80:
            flush()
            ht = m.group(1).strip()
            current_subsection = Section(title=ht, level=3)
            if current_section:
                current_section.subsections.append(current_subsection)
            prev_blank = False; continue

        if prev_blank and len(stripped) < 25 and \
           not stripped.startswith(('-', '*', '|', '#', '>', '[', '`')) and \
           (current_block is None or not current_block.lines):
            flush()
            if current_section is None:
                current_section = Section(title=stripped, level=2)
                sections.append(current_section)
            else:
                current_subsection = Section(title=stripped, level=3)
                current_section.subsections.append(current_subsection)
            prev_blank = False; continue

        prev_blank = False
        target = current_subsection or current_section
        if not target:
            continue

        if _TABLE_ROW_RE.match(stripped) or _TABLE_SEP_RE.match(stripped):
            if not current_block or current_block.type != 'table':
                start('table', stripped)
            else:
                current_block.lines.append(stripped)
        elif _UNORDERED_LIST_RE.match(stripped):
            if not current_block or current_block.type != 'list':
                start('list', stripped)
            else:
                current_block.lines.append(stripped)
        elif _ORDERED_LIST_RE.match(stripped):
            if not current_block or current_block.type != 'olist':
                start('olist', stripped)
            else:
                current_block.lines.append(stripped)
        else:
            if not current_block or current_block.type != 'para':
                start('para', stripped)
            else:
                current_block.lines.append(stripped)

    flush()
    return title, meta_line, sections, references


def _ext_num(s: Section):
    m = re.match(r'^(\d+(?:\.\d+)*)\s*', s.title)
    if m:
        s.number = m.group(1).rstrip('.')
        s.title = s.title[m.end():].strip()
    s.title = s.title.lstrip('. ')

# ═══════════════════════════════════════════════════════════════════════════════
# 内联 Markdown → HTML
# ═══════════════════════════════════════════════════════════════════════════════

def inline_md(text: str) -> str:
    text = html_mod.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'\[(\d+(?:[,，]\s*\d+)*)\]', r'<span class="text-primary font-bold">[\1]</span>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


def shorten(text: str, limit: int = 80) -> str:
    if len(text) <= limit:
        return text
    for sep in ['。', '；', '，', '、', ' ']:
        pos = text[:limit + 20].rfind(sep)
        if limit * 0.5 < pos < limit + 20:
            return text[:pos + 1]
    return text[:limit] + '…'


def extract_key_point(text: str) -> str:
    for sep in ['。', '！', '？']:
        if sep in text:
            first = text[:text.index(sep) + 1]
            return shorten(first, 90)
    return shorten(text, 90)

# ═══════════════════════════════════════════════════════════════════════════════
# 表格
# ═══════════════════════════════════════════════════════════════════════════════

def parse_table(lines: list) -> str:
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
# Slide 渲染
# ═══════════════════════════════════════════════════════════════════════════════

def _slide(layout: str, content: str) -> str:
    """生成一个 SWD slide 的 HTML"""
    return f'<div data-swd-layout="{layout}">\n  <div class="swd-slide">\n{content}\n  </div>\n</div>\n'


def render_blocks(blocks: list, max_items: int = 5) -> str:
    """渲染内容块为 HTML"""
    parts, count = [], 0
    for b in blocks:
        if count >= max_items:
            break
        if b.type == 'table':
            parts.append(parse_table(b.lines))
            count += 1
        elif b.type in ('list', 'olist'):
            tag = 'ul' if b.type == 'list' else 'ol'
            items = []
            for l in b.lines[:max_items]:
                text = re.sub(r'^[-*\d]+\.\s+', '', l)
                items.append(f'<li>{shorten(inline_md(text), 70)}</li>')
            parts.append(f'<{tag}>{"".join(items)}</{tag}>')
            count += len(items)
        elif b.type == 'para':
            text = ' '.join(b.lines)
            parts.append(f'<p>{inline_md(extract_key_point(text))}</p>')
            count += 1
    return '\n'.join(parts)


def render_title_slide(title: str, meta_line: str) -> str:
    meta = inline_md(meta_line) if meta_line else "文献综述"
    content = f"""
    <h1>{inline_md(title)}</h1>
    <div class="slide-divider" style="margin:0.8em auto"></div>
    <p class="text-muted">{meta}</p>
    <p class="text-muted text-sm mt-2">Powered by AutoOverview</p>
"""
    return _slide('cover', content)


def render_outline_slide(sections: list) -> str:
    main = [s for s in sections if s.level <= 2]
    if not main:
        return ""
    items = []
    for s in main:
        num = f'<span class="text-primary font-bold">{s.number}</span>' if s.number else ''
        sep = ' · ' if num else ''
        label = s.title if len(s.title) <= 20 else s.title[:18] + '…'
        items.append(f'<li>{num}{sep}{inline_md(label)}</li>')

    half = (len(items) + 1) // 2
    left = '\n'.join(items[:half])
    right = '\n'.join(items[half:])

    content = f"""
    <h2>综述框架</h2>
    <div class="slide-divider"></div>
    <div style="display:flex;gap:2em;margin-top:0.8em">
      <div style="flex:1"><ul>{left}</ul></div>
      <div style="flex:1"><ul>{right}</ul></div>
    </div>
"""
    return _slide('default', content)


def render_section_divider(section: Section) -> str:
    num_html = f'<div class="section-num">{section.number}</div>' if section.number else ''
    content = f"""
    {num_html}
    <h1 style="font-size:2em">{inline_md(section.title)}</h1>
"""
    return _slide('section', content)


def render_subsection_card(sub: Section) -> str:
    content = render_blocks(sub.blocks, 4)
    return f"""<div class="swd-card swd-card-accent">
  <h3>{inline_md(sub.title)}</h3>
  {content}
</div>"""


def render_subsection_col(sub: Section) -> str:
    content = render_blocks(sub.blocks, 5)
    return f"""<h3>{inline_md(sub.title)}</h3>
  {content}"""


def detect_layout(section: Section) -> str:
    has_table = any(b.type == 'table' for b in section.blocks)
    n_sub = len(section.subsections)
    if has_table:
        return 'table'
    if n_sub >= 3:
        return 'three_col'
    if n_sub == 2:
        return 'two_col'
    if n_sub >= 4:
        return 'two_col'
    return 'list'


def render_content_slide(section: Section) -> str:
    layout = detect_layout(section)
    num = f'<div class="section-num">{section.number}</div>' if section.number else ''
    title_html = f'<h2>{inline_md(section.title)}</h2>\n<div class="slide-divider"></div>'

    if layout == 'table':
        tbl = [b for b in section.blocks if b.type == 'table']
        other = [b for b in section.blocks if b.type != 'table']
        table_html = parse_table(tbl[0].lines) if tbl else ''
        intro = render_blocks(other, 2) if other else ''
        content = f"    {num}\n    {title_html}\n    {intro}\n    {table_html}"
        return _slide('default', content)

    if layout == 'three_col':
        subs = section.subsections[:3]
        cols = '\n'.join(f'<div data-swd-column>\n{render_subsection_card(s)}\n</div>' for s in subs)
        content = f"    {num}\n    {title_html}\n    {cols}"
        return _slide('three-cols', content)

    if layout == 'two_col':
        subs = section.subsections
        if len(subs) == 2:
            l = render_subsection_col(subs[0])
            r = render_subsection_col(subs[1])
        else:
            half = len(subs) // 2
            l = '\n'.join(render_subsection_card(s) for s in subs[:half])
            r = '\n'.join(render_subsection_card(s) for s in subs[half:])
        content = f"""    {num}
    {title_html}
    <div data-swd-column>
      {l}
    </div>
    <div data-swd-column>
      {r}
    </div>"""
        return _slide('two-cols', content)

    content_html = render_blocks(section.blocks)
    content = f"    {num}\n    {title_html}\n    {content_html}"
    return _slide('default', content)


def should_split(section: Section) -> bool:
    total = sum(len(' '.join(b.lines)) for b in section.blocks)
    for sub in section.subsections:
        total += sum(len(' '.join(b.lines)) for b in sub.blocks)
    return total > 400 or len(section.subsections) > 3


def render_sub_slide(section: Section, sub: Section) -> str:
    full = f"{section.number}.{sub.number}" if sub.number else section.number
    num = f'<div class="section-num">{full}</div>' if full else ''
    content_html = render_blocks(sub.blocks, 6)
    content = f"""    {num}
    <h2>{inline_md(sub.title)}</h2>
    <div class="slide-divider"></div>
    {content_html}"""
    return _slide('default', content)


def render_references_slide(references: list) -> str:
    if not references:
        return ""
    ref_items = '\n'.join(f'<p>{inline_md(shorten(r, 80))}</p>' for r in references)
    content = f"""
    <h2>参考文献</h2>
    <div class="slide-divider"></div>
    <div class="ref-grid">{ref_items}</div>
"""
    return _slide('default', content)


def render_thank_you(title: str) -> str:
    content = f"""
    <h1 style="font-size:2.5em;color:#2563eb">谢谢</h1>
    <div class="slide-divider" style="margin:0.8em auto"></div>
    <p>{inline_md(title)}</p>
    <p class="text-muted text-sm mt-2">文献综述</p>
"""
    return _slide('section', content)

# ═══════════════════════════════════════════════════════════════════════════════
# 主生成流程
# ═══════════════════════════════════════════════════════════════════════════════

def generate_slides(md_path: str, output_path: str, title_override: str = "") -> str:
    text = Path(md_path).read_text(encoding='utf-8')
    title, meta_line, sections, references = parse_markdown(text)
    if title_override:
        title = title_override

    slides = []
    slides.append(render_title_slide(title, meta_line))

    main = [s for s in sections if s.level <= 2]
    if main:
        slides.append(render_outline_slide(sections))

    for section in sections:
        if section.title == title:
            continue
        sec_title = section.title.lstrip('. ').strip()
        if not sec_title:
            continue

        if section.level <= 2 and section.subsections:
            slides.append(render_section_divider(section))

        if should_split(section) and section.subsections:
            for sub in section.subsections:
                slides.append(render_sub_slide(section, sub))
        else:
            slides.append(render_content_slide(section))

    ref = render_references_slide(references)
    if ref:
        slides.append(ref)

    slides.append(render_thank_you(title))

    slides_html = '\n'.join(slides)
    html = HTML_TEMPLATE.format(
        title=html_mod.escape(title),
        css=CSS_OVERRIDE,
        slides=slides_html,
    )

    Path(output_path).write_text(html, encoding='utf-8')
    return output_path

# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Markdown 综述 → SWD 单文件 HTML 幻灯片'
    )
    parser.add_argument('input', help='输入 Markdown 文件路径')
    parser.add_argument('-o', '--output', help='输出 HTML 文件路径（默认: input_swd.html）')
    parser.add_argument('--title', help='覆盖演示文稿标题')
    args = parser.parse_args()

    output = args.output or str(Path(args.input).stem) + '_swd.html'
    result = generate_slides(args.input, output, title_override=args.title or "")
    print(f'Generated: {result}')


if __name__ == '__main__':
    main()
