# -*- coding: utf-8 -*-
"""my-site 构建脚本：把 content/ 下的 Markdown 构建成静态 HTML 到 docs/。

GitHub Pages 从仓库 main 分支的 /docs 目录发布，因此 docs/ 需要入库。

用法：
    python build.py            # 构建
    python build.py --serve    # 构建后本地预览 http://127.0.0.1:8000
"""

import argparse
import html
import pathlib
import shutil
import sys

from md2html import convert, first_heading

ROOT_DIR = pathlib.Path(__file__).resolve().parent
CONTENT_DIR = ROOT_DIR / "content"
NOTES_DIR = CONTENT_DIR / "notes"
ASSETS_DIR = CONTENT_DIR / "assets"
OUT_DIR = ROOT_DIR / "docs"

HOME_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<link rel="stylesheet" href="style.css"/>
</head>
<body>
<main>
{body}
</main>
<footer>由 my-site 生成</footer>
</body>
</html>
"""

NOTE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<link rel="stylesheet" href="../style.css"/>
</head>
<body>
<nav class="topnav"><a href="../index.html">← 首页</a></nav>
<main>
{body}
</main>
<footer>由 my-site 生成</footer>
</body>
</html>
"""


def _page(title: str, body: str, *, note: bool) -> str:
    tpl = NOTE_TEMPLATE if note else HOME_TEMPLATE
    return tpl.format(title=html.escape(title), body=body)


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 样式
    (OUT_DIR / "style.css").write_text(
        (ROOT_DIR / "style.css").read_text(encoding="utf-8"), encoding="utf-8")

    # 二进制资源（图片等）
    if ASSETS_DIR.exists():
        shutil.copytree(ASSETS_DIR, OUT_DIR / "assets", dirs_exist_ok=True)

    # 笔记页：content/notes/*.md → docs/notes/<slug>.html
    notes: list[tuple[str, str]] = []  # (相对路径, 标题)
    (OUT_DIR / "notes").mkdir(parents=True, exist_ok=True)
    for md in sorted(NOTES_DIR.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        slug = md.stem
        title = first_heading(text) or slug
        body = convert(text)
        (OUT_DIR / "notes" / f"{slug}.html").write_text(
            _page(title, body, note=True), encoding="utf-8")
        notes.append((f"notes/{slug}.html", title))

    # 首页：content/index.md → docs/index.html，并附“全部笔记”列表
    index_text = (CONTENT_DIR / "index.md").read_text(encoding="utf-8")
    index_body = convert(index_text)
    if notes:
        items = "\n".join(
            f'<li><a href="{html.escape(rel)}">{html.escape(title)}</a></li>'
            for rel, title in notes)
        index_body += f'\n<h2>学习笔记</h2>\n<ul class="note-list">\n{items}\n</ul>'
    (OUT_DIR / "index.html").write_text(
        _page("首页", index_body, note=False), encoding="utf-8")

    print(f"已生成 {len(notes)} 篇笔记 + 首页 → {OUT_DIR}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="my-site 构建脚本")
    parser.add_argument("--serve", action="store_true",
                        help="构建后本地预览 http://127.0.0.1:8000")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    build()
    if args.serve:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                    directory=str(OUT_DIR))
        http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
