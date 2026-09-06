# -*- coding: utf-8 -*-
"""Markdown → HTML 核心转换器（纯标准库，无第三方依赖）。

支持的块级语法：
  - 标题       # ~ ######
  - 围栏代码块 ```lang ... ```
  - 引用       > 开头
  - 无序列表   - / * / +
  - 有序列表   1. / 1)
  - 分割线     --- / ***（独占一行，至少 3 个符号）
  - 段落       （其余，连续行合并为一个段落）

支持的行内语法：
  - `行内代码`
  - **粗体**、*斜体*
  - [链接文字](url)、![图片说明](url)

支持的表格（GFM 风格，`|` 分隔，第二行必须是 `---`/`:--:` 分隔行）：
    | 列A | 列B |
    | --- | --- |
    | x   | y   |

用法：
    from md2html import convert
    html = convert(open("note.md", encoding="utf-8").read())
"""

import html
import re

# --------------------------------------------------------------------------
# 块级工具
# --------------------------------------------------------------------------

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
HR_RE = re.compile(r"^\s*([-*_])\s*\1\s*\1\1?\s*$")  # ---、***、___（>=3 个）
CODE_FENCE_RE = re.compile(r"^\s*```([\w+-]*)\s*$")   # 允许行首缩进
BLOCKQUOTE_RE = re.compile(r"^\s{0,3}>\s?(.*)$")      # 引用允许 <=3 个前导空格
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)[.)]\s+(.*)$")
BULLET_ITEM_RE = re.compile(r"^(\s*)[-*+]\s+(.*)$")


# --------------------------------------------------------------------------
# 表格
# --------------------------------------------------------------------------

def _split_cells(line: str) -> list[str]:
    """把一行 `| a | b |` 拆成单元格；支持 `\\|` 转义竖线。"""
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    parts = re.split(r"(?<!\\)\|", text)
    return [p.replace(r"\|", "|").strip() for p in parts]


def _is_sep_row(line: str) -> bool:
    """分隔行形如 | --- | :--: | :--- |，由冒号与连字符组成。"""
    cells = _split_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-+:?", c) for c in cells)


def _consume_table(lines: list[str], i: int) -> tuple[str | None, int]:
    """尝试把 lines[i:] 解析成表格。

    返回 (None, i) 表示不是表格；否则返回 (html, 消费后的新下标)。
    要求：当前行含 `|`，且下一行是分隔行。之后连续含 `|` 的行都是数据行。
    """
    if i + 1 >= len(lines) or "|" not in lines[i]:
        return None, i
    if not _is_sep_row(lines[i + 1]):
        return None, i
    header = _split_cells(lines[i])
    aligns = _split_cells(lines[i + 1])
    i += 2
    rows: list[list[str]] = []
    while i < len(lines) and lines[i].strip() and "|" in lines[i]:
        rows.append(_split_cells(lines[i]))
        i += 1

    def _align(sep: str) -> str:
        left = sep.startswith(":")
        right = sep.endswith(":")
        if left and right:
            return ' style="text-align:center"'
        if right:
            return ' style="text-align:right"'
        return ""

    def _cells(row: list[str], tag: str) -> str:
        cells = []
        for idx, cell in enumerate(row):
            style = _align(aligns[idx]) if idx < len(aligns) and tag == "th" else ""
            cells.append(f"<{tag}{style}>{inline(cell)}</{tag}>")
        return "".join(cells)

    lines_out = ["<table>"]
    lines_out.append("<thead><tr>" + _cells(header, "th") + "</tr></thead>")
    if rows:
        body = "\n".join(
            "<tr>" + _cells(r, "td") + "</tr>" for r in rows)
        lines_out.append("<tbody>\n" + body + "\n</tbody>")
    lines_out.append("</table>")
    return "\n".join(lines_out), i


def _split_blocks(text: str) -> list[str]:
    """按空行切块，去掉首尾空行。"""
    blocks: list[str] = []
    for raw in text.replace("\r\n", "\n").split("\n\n"):
        block = raw.strip("\n")
        if block.strip():
            blocks.append(block)
    return blocks


def _consume_fence(lines: list[str], i: int) -> tuple[str, str, int]:
    """从 lines[i]（``` 开头）收集到闭合围栏，返回 (语言, 内容, 新下标)。"""
    lang = CODE_FENCE_RE.match(lines[i]).group(1)
    i += 1
    body: list[str] = []
    while i < len(lines) and not lines[i].lstrip().startswith("```"):
        body.append(lines[i])
        i += 1
    return lang, "\n".join(body), i + 1  # 跳过闭合围栏


def _consume_quote(lines: list[str], i: int) -> tuple[str, int]:
    """收集连续的引用行（行首 > ），返回 (html, 新下标)。"""
    body: list[str] = []
    while i < len(lines) and BLOCKQUOTE_RE.match(lines[i]):
        body.append(BLOCKQUOTE_RE.match(lines[i]).group(1))
        i += 1
    inner = _render_blocks("\n".join(body))
    return f"<blockquote>\n{inner}</blockquote>\n", i


def _list_items(lines: list[str], i: int) -> tuple[list[tuple[str, str, str]], int]:
    """收集连续的列表项，返回 [(前导空白, 标记类型, 正文), ...] 与结束下标。"""
    items: list[tuple[str, str, str]] = []
    while i < len(lines):
        m = ORDERED_ITEM_RE.match(lines[i])
        kind = "ol"
        if not m:
            m = BULLET_ITEM_RE.match(lines[i])
            kind = "ul"
        if not m:
            break
        indent, content = m.group(1), m.group(2)
        items.append((indent, kind, content))
        i += 1
    return items, i


def _render_list(items: list[tuple[str, str, str]],
                 level: int = 0, start: int = 0) -> tuple[str, int]:
    """按缩进渲染列表项。

    每两格空格升一级；同级且同类型（ul/ol）的项并入同一个列表标签，
    更深的项作为上一个 <li> 的子列表递归渲染。

    返回 (html, 消费到的下标)。
    """
    i = start
    chunks: list[str] = []
    while i < len(items):
        indent, kind, content = items[i]
        if len(indent) // 2 != level:
            break
        # 收集同级同类型的一整组
        group_kind = kind
        lis: list[str] = []
        while i < len(items) and items[i][1] == group_kind and len(items[i][0]) // 2 == level:
            text = items[i][2]
            i += 1
            sub_html = ""
            if i < len(items) and len(items[i][0]) // 2 > level:
                sub_html, i = _render_list(items, level + 1, i)
            if sub_html:
                lis.append(f"<li>{inline(text)}\n{sub_html}</li>")
            else:
                lis.append(f"<li>{inline(text)}</li>")
        tag = "ol" if group_kind == "ol" else "ul"
        chunks.append(f"<{tag}>\n" + "\n".join(lis) + f"\n</{tag}>")
    return "\n".join(chunks), i


# --------------------------------------------------------------------------
# 行内
# --------------------------------------------------------------------------

def _escape(text: str) -> str:
    """文本内容转义（元素内容，转义 < > &）。"""
    return html.escape(text, quote=False)


def _escape_attr(text: str) -> str:
    """属性值转义（额外转义引号，防属性注入）。"""
    return html.escape(text, quote=True)


CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"!?\[([^\]]*)\]\(([^)\s]+)\)")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
# 斜体内容允许内嵌 **粗体**（一层），如 *a **b** c*
ITALIC_RE = re.compile(r"\*((?:\*\*[^*]+\*\*|[^*])+)\*(?!\*)")


def inline(text: str) -> str:
    """把一行文本里的行内语法转成 HTML。

    先解析、后转义：文字逐段按“文本/属性”分别转义一次，
    避免先整段转义导致的双重转义与属性注入。
    """
    out: list[str] = []
    buf: list[str] = []
    i, n = 0, len(text)

    def flush() -> None:
        if buf:
            out.append(_escape("".join(buf)))
            buf.clear()

    while i < n:
        m = CODE_SPAN_RE.match(text, i)
        if m:
            flush()
            out.append(f"<code>{_escape(m.group(1))}</code>")
            i = m.end()
            continue
        m = LINK_RE.match(text, i)
        if m:
            flush()
            is_image = m.group(0).startswith("!")
            url = _escape_attr(m.group(2))
            label = m.group(1)
            if is_image:
                out.append(f'<img src="{url}" alt="{_escape_attr(label)}"/>')
            else:
                out.append(f'<a href="{url}">{inline(label)}</a>')
            i = m.end()
            continue
        m = BOLD_RE.match(text, i)
        if m:
            flush()
            out.append(f"<strong>{inline(m.group(1))}</strong>")
            i = m.end()
            continue
        m = ITALIC_RE.match(text, i)
        if m:
            flush()
            out.append(f"<em>{inline(m.group(1))}</em>")
            i = m.end()
            continue
        buf.append(text[i])
        i += 1
    flush()
    return "".join(out)


# --------------------------------------------------------------------------
# 块级渲染
# --------------------------------------------------------------------------

def _render_blocks(text: str) -> str:
    """把整段 Markdown 文本按块渲染成 HTML（不含 <body> 壳）。"""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        # 围栏代码块
        if CODE_FENCE_RE.match(stripped):
            lang, body, i = _consume_fence(lines, i)
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>{_escape(body)}</code></pre>")
            continue
        # 标题
        m = HEADING_RE.match(stripped)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue
        # 分割线
        if HR_RE.match(stripped):
            out.append("<hr/>")
            i += 1
            continue
        # 引用（判定与消费必须同规：原始行最多 3 个前导空格，防“判了但吃不掉”死循环）
        if BLOCKQUOTE_RE.match(stripped) and BLOCKQUOTE_RE.match(line):
            html_block, i = _consume_quote(lines, i)
            out.append(html_block)
            continue
        # 表格（首行含 | 且下一行是分隔行）
        if "|" in stripped:
            table_html, i = _consume_table(lines, i)
            if table_html is not None:
                out.append(table_html)
                continue
        # 列表（按行连续收集）
        if ORDERED_ITEM_RE.match(stripped) or BULLET_ITEM_RE.match(stripped):
            items, i = _list_items(lines, i)
            out.append(_render_list(items)[0])
            continue
        # 段落：合并到下一个空行或其它块起点
        para: list[str] = [stripped]
        i += 1
        while i < n and lines[i].strip() and not (
            CODE_FENCE_RE.match(lines[i].strip())
            or HEADING_RE.match(lines[i].strip())
            or HR_RE.match(lines[i].strip())
            or BLOCKQUOTE_RE.match(lines[i].strip())
            or ORDERED_ITEM_RE.match(lines[i].strip())
            or BULLET_ITEM_RE.match(lines[i].strip())
        ):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# 对外接口
# --------------------------------------------------------------------------

def convert(markdown_text: str) -> str:
    """把 Markdown 文本转成 HTML 正文片段。"""
    return _render_blocks(markdown_text)


def first_heading(markdown_text: str) -> str:
    """取第一个 # 标题作为页面标题；没有则返回空串。"""
    for raw in markdown_text.replace("\r\n", "\n").split("\n"):
        m = HEADING_RE.match(raw.strip())
        if m:
            return m.group(2).strip()
    return ""


if __name__ == "__main__":
    import sys
    demo = sys.stdin.read()
    print(convert(demo))
