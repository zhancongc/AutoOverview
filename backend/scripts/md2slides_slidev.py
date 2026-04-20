#!/usr/bin/env python3
"""
Markdown 综述 → Slidev Markdown → 单文件 HTML 幻灯片

流程: input.md → 解析 → 生成 Slidev Markdown → npx slidev build → 输出 HTML

用法:
  python md2slides_slidev.py input.md [-o output_dir] [--title "标题"]
"""
import argparse
import re
import subprocess
import shutil
import json
from dataclasses import dataclass, field
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# 数据结构 & 解析（复用 md2slides.py 的逻辑）
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
    # Clean leading dot/space
    s.title = s.title.lstrip('. ')

# ═══════════════════════════════════════════════════════════════════════════════
# Slidev Markdown 生成
# ═══════════════════════════════════════════════════════════════════════════════

def shorten(text, limit=80):
    if len(text) <= limit:
        return text
    for sep in ['。', '；', '，', ' ']:
        pos = text[:limit+20].rfind(sep)
        if limit * 0.5 < pos < limit + 20:
            return text[:pos+1]
    return text[:limit] + '…'


def key_point(text):
    for sep in ['。', '！', '？']:
        if sep in text:
            return shorten(text[:text.index(sep)+1], 100)
    return shorten(text, 100)


def md_table(lines):
    return '\n'.join(l for l in lines if not _TABLE_SEP_RE.match(l.strip()))


def blocks_to_slidev(blocks, max_items=5):
    """将 blocks 转为 Slidev Markdown 片段"""
    parts, count = [], 0
    for b in blocks:
        if count >= max_items:
            break
        if b.type == 'table':
            parts.append(md_table(b.lines))
            count += 1
        elif b.type in ('list', 'olist'):
            for line in b.lines[:max_items]:
                text = re.sub(r'^[-*\d]+\.\s+', '', line)
                parts.append(f'- {shorten(text, 70)}')
                count += 1
        elif b.type == 'para':
            text = ' '.join(b.lines)
            parts.append(shorten(key_point(text), 100))
            count += 1
    return '\n'.join(parts)


def generate_slidev_md(title, meta_line, sections, references):
    """生成 Slidev Markdown 内容"""
    slides = []

    # ── Frontmatter ──
    slides.append(f"""---
theme: seriph
title: "{title}"
class: text-center
transition: slide-left
mdc: true
---

# {title}

<div class="abs-bl mx-14 my-12 flex flex-col text-left">
  <div class="text-sm opacity-70">{meta_line or "文献综述"}</div>
</div>""")

    # ── Outline ──
    main = [s for s in sections if s.level <= 2]
    half = (len(main) + 1) // 2
    left_items, right_items = [], []
    for idx, s in enumerate(main):
        label = f"**{s.number}.** {s.title}" if s.number and s.number != s.title else s.title
        if idx < half:
            left_items.append(f"- {label}")
        else:
            right_items.append(f"- {label}")

    slides.append(f"""---
layout: default
---

# 综述框架

<div class="grid grid-cols-2 gap-8 text-sm mt-2">
<div>

{chr(10).join(left_items)}

</div>
<div>

{chr(10).join(right_items)}

</div>
</div>""")

    # ── Content slides ──
    for section in sections:
        # Skip if title is same as main title (subtitle captured as section)
        if section.title == title:
            continue

        # Clean section title (remove leading dot)
        sec_title = section.title.lstrip('. ').strip()
        if not sec_title:
            continue

        # Section divider for main sections with subsections
        if section.level <= 2 and section.subsections:
            num_label = f"<div class=\"text-6xl font-light opacity-10 absolute top-8 right-12\">{section.number}</div>" if section.number else ""
            slides.append(f"""---
layout: section
---

{num_label}
# {sec_title}

""")

        # Decide layout
        subs = section.subsections
        n_sub = len(subs)
        has_table = any(b.type == 'table' for b in section.blocks)

        if n_sub >= 3 and not has_table:
            # Three-column card layout
            chunk_size = 3
            for ci in range(0, n_sub, chunk_size):
                chunk = subs[ci:ci+chunk_size]
                col_class = f"grid-cols-{len(chunk)}"
                cards = []
                for sub in chunk:
                    content = blocks_to_slidev(sub.blocks, 4)
                    sub_title = sub.title.lstrip('. ').strip()
                    cards.append(f"""<div class="border rounded p-3 bg-blue-50/40">
<div class="text-sm font-bold text-red-700 mb-1">{sub_title}</div>
<div class="text-xs leading-snug">

{content}

</div>
</div>""")
                slides.append(f"""---
layout: default
---

# {sec_title}

<div class="grid {col_class} gap-3 mt-2 text-xs">
{chr(10).join(cards)}
</div>
""")

        elif n_sub == 2 and not has_table:
            left = blocks_to_slidev(subs[0].blocks, 5)
            right = blocks_to_slidev(subs[1].blocks, 5)
            lt = subs[0].title.lstrip('. ').strip()
            rt = subs[1].title.lstrip('. ').strip()
            slides.append(f"""---
layout: default
---

# {sec_title}

<div class="grid grid-cols-2 gap-6 mt-2 text-xs">
<div>
<div class="text-sm font-bold text-red-700 mb-1">{lt}</div>

{left}

</div>
<div>
<div class="text-sm font-bold text-red-700 mb-1">{rt}</div>

{right}

</div>
</div>
""")

        elif has_table:
            tbl = [b for b in section.blocks if b.type == 'table']
            other = [b for b in section.blocks if b.type != 'table']
            intro = blocks_to_slidev(other, 2) if other else ''
            table_md = md_table(tbl[0].lines) if tbl else ''
            slides.append(f"""---
layout: default
---

# {sec_title}

<div class="text-xs mt-1">

{intro}

</div>

<div class="mt-2">

{table_md}

</div>
""")

        else:
            content = blocks_to_slidev(section.blocks, 6)
            if not content and n_sub == 0:
                continue
            slides.append(f"""---
layout: default
---

# {sec_title}

<div class="text-xs mt-1">

{content}

</div>
""")

    # ── References — compact ──
    if references:
        # Split into slides of ~30 refs each
        per = 30
        for start in range(0, len(references), per):
            chunk = references[start:start+per]
            half_r = (len(chunk)+1)//2
            left_refs = '\n\n'.join(shorten(r, 80) for r in chunk[:half_r])
            right_refs = '\n\n'.join(shorten(r, 80) for r in chunk[half_r:])
            slides.append(f"""---
layout: default
---

# 参考文献

<div class="grid grid-cols-2 gap-4 mt-2">
<div class="text-[0.45em] leading-tight text-gray-400">

{left_refs}

</div>
<div class="text-[0.45em] leading-tight text-gray-400">

{right_refs}

</div>
</div>
""")

    # ── Thank you ──
    slides.append("""---
layout: center
class: text-center
---

# 谢谢

<div class="opacity-50 text-sm mt-4">文献综述</div>
""")

    return '\n'.join(slides)


# ═══════════════════════════════════════════════════════════════════════════════
# Build Slidev → HTML
# ═══════════════════════════════════════════════════════════════════════════════

def build_slidev(md_path: str, output_dir: str) -> str:
    """调用 npx slidev build 生成 HTML SPA"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    slides_path = output_dir / "slides.md"
    build_dir = output_dir / "dist"

    # Build into separate dist/ to avoid source/output conflict
    # Slidev needs CWD to be the directory containing slides.md
    print(f"Building Slidev → {build_dir} ...")
    result = subprocess.run(
        ["npx", "-y", "@slidev/cli", "build", "slides.md", "--out", str(build_dir)],
        capture_output=True, text=True, timeout=300,
        cwd=str(output_dir)
    )

    if result.returncode != 0:
        print(f"Build stderr: {result.stderr[-500:]}" if result.stderr else "Build failed")
        if not (build_dir / "index.html").exists():
            raise RuntimeError("Slidev build failed: no index.html generated")

    # Move dist contents up to output_dir
    for f in build_dir.iterdir():
        target = output_dir / f.name
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.move(str(f), str(target))
    build_dir.rmdir()

    # Fix asset paths for file:// protocol
    for html_file in output_dir.glob("*.html"):
        content = html_file.read_text()
        content = content.replace('="/assets/', '="./assets/')
        html_file.write_text(content)

    return str(output_dir / "index.html")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Markdown 综述 → Slidev HTML 幻灯片'
    )
    parser.add_argument('input', help='输入 Markdown 文件')
    parser.add_argument('-o', '--output', help='输出目录（默认: input_slides/）')
    parser.add_argument('--title', help='覆盖标题')
    parser.add_argument('--no-build', action='store_true', help='只生成 Slidev MD，不构建 HTML')
    args = parser.parse_args()

    output_dir = args.output or Path(args.input).stem + '_slides'
    title_override = args.title or ""

    text = Path(args.input).read_text(encoding='utf-8')
    title, meta_line, sections, references = parse_markdown(text)
    if title_override:
        title = title_override

    slidev_md = generate_slidev_md(title, meta_line, sections, references)

    # Write intermediate MD
    md_path = Path(output_dir) / "slides.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(slidev_md, encoding='utf-8')
    print(f"Slidev MD: {md_path}")

    if not args.no_build:
        html_path = build_slidev(str(md_path), output_dir)
        print(f"HTML: {html_path}")
        # Open
        subprocess.run(["open", html_path])


if __name__ == '__main__':
    main()
