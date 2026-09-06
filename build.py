# -*- coding: utf-8 -*-
"""my-site 模块化构建脚本：content/ 下每个子目录 = 一个内容模块。

结构约定（目录即模块）：
    content/
    ├── index.md            # 主页文案（首个 # 作为站点标题，默认“个人网站”）
    ├── assets/             # 全局资源（图片等；md 里用 ../assets/ 引用）
    └── <模块名>/           # 每个模块一个目录
        ├── index.md        # 模块介绍：标题=模块名，正文=简介（驱动主页卡片与模块页）
        └── 条目.md ...     # 其余 md 都是该模块的条目

产物结构（GitHub Pages 从 /docs 发布）：
    docs/
    ├── index.html          # 主页：标题 + “添加新项目” + 各模块卡片
    ├── style.css
    ├── assets/…
    └── <模块名>/
        ├── index.html      # 模块浏览目录（模块介绍 + 条目列表）
        └── <条目>.html

用法：
    python build.py            # 全量重建 docs/
    python build.py --serve    # 构建后本地预览 http://127.0.0.1:8000
"""

import argparse
import html
import pathlib
import re
import shutil
import sys

from md2html import convert, first_heading

ROOT_DIR = pathlib.Path(__file__).resolve().parent
CONTENT_DIR = ROOT_DIR / "content"
ASSETS_DIR = CONTENT_DIR / "assets"
OUT_DIR = ROOT_DIR / "docs"

REPO = "Not1u/my-site"          # 用于“添加新项目”的 GitHub 新建文件直链
BRANCH = "main"


def _first_paragraph(body_html: str) -> str:
    """取转换后 HTML 的第一个 <p> 文本，去掉标签，用于卡片简介。"""
    m = re.search(r"<p>(.*?)</p>", body_html, re.S)
    if not m:
        return ""
    text = re.sub(r"<[^>]+>", "", m.group(1))
    text = html.unescape(text).strip()
    return text[:80] + ("…" if len(text) > 80 else "")


def _github_new_file_url(module_dir: str | None) -> str:
    """GitHub 网页“新建文件”直链；module_dir 为 None 时不预选目录。"""
    path = f"/content/{module_dir}" if module_dir else "/content"
    return f"https://github.com/{REPO}/new/{BRANCH}{path}"


# --------------------------------------------------------------------------
# 页面模板（当前为基础版，UI 后续统一优化）
# --------------------------------------------------------------------------

def _chrome(body: str, *, home: bool, module: str | None) -> str:
    back = "../index.html" if not home and module else "index.html"
    add_url = _github_new_file_url(module)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{{title}}</title>
<link rel="stylesheet" href="{back.replace('index.html', 'style.css')}"/>
</head>
<body>
<header class="sitehead">
  <a class="brand" href="{back}">个人网站</a>
  <a class="btn" href="{add_url}" target="_blank" rel="noopener">＋ 添加新项目</a>
</header>
<main>
{body}
</main>
<footer>由 my-site 生成</footer>
</body>
</html>"""


def _page(title: str, body: str, *, home: bool = False,
          module: str | None = None) -> str:
    page = _chrome(body, home=home, module=module)
    return page.replace("{{title}}", html.escape(title))


# --------------------------------------------------------------------------
# 构建
# --------------------------------------------------------------------------

def build() -> None:
    # 全量重建，删除的 md 产物自动消失
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    (OUT_DIR / "style.css").write_text(
        (ROOT_DIR / "style.css").read_text(encoding="utf-8"), encoding="utf-8")
    if ASSETS_DIR.exists():
        shutil.copytree(ASSETS_DIR, OUT_DIR / "assets")

    # 收集模块：content/ 下除 assets 外的子目录
    modules = sorted(
        p for p in CONTENT_DIR.iterdir()
        if p.is_dir() and p.name != "assets")
    module_info: list[tuple[str, str, str]] = []  # (目录名, 标题, 简介)

    for mdir in modules:
        name = mdir.name
        (OUT_DIR / name).mkdir(parents=True)
        index_md = mdir / "index.md"
        title = name
        intro = ""
        if index_md.exists():
            text = index_md.read_text(encoding="utf-8")
            title = first_heading(text) or name
            body_html = convert(text)
            intro = _first_paragraph(body_html)
        else:
            body_html = ""
        module_info.append((name, title, intro))

        # 条目页
        items: list[tuple[str, str]] = []  # (相对链接, 标题)
        for md in sorted(mdir.glob("*.md")):
            if md.name == "index.md":
                continue
            slug = md.stem
            text = md.read_text(encoding="utf-8")
            it_title = first_heading(text) or slug
            (OUT_DIR / name / f"{slug}.html").write_text(
                _page(it_title, convert(text), module=name), encoding="utf-8")
            items.append((f"{slug}.html", it_title))

        # 模块浏览目录页
        listing = ""
        if items:
            lis = "\n".join(
                f'<li><a href="{html.escape(rel)}">{html.escape(t)}</a></li>'
                for rel, t in items)
            listing = f'<h2>条目（{len(items)}）</h2>\n<ul class="note-list">\n{lis}\n</ul>'
        (OUT_DIR / name / "index.html").write_text(
            _page(title, body_html + listing, module=name), encoding="utf-8")

    # 主页
    index_md = CONTENT_DIR / "index.md"
    if index_md.exists():
        home_text = index_md.read_text(encoding="utf-8")
        home_title = first_heading(home_text) or "个人网站"
        home_body = convert(home_text)
    else:
        home_title, home_body = "个人网站", "<h1>个人网站</h1>"
    if module_info:
        cards = []
        for name, title, intro in module_info:
            count = len(list((CONTENT_DIR / name).glob("*.md"))) - 1
            desc = html.escape(intro) if intro else f"{count} 篇内容"
            cards.append(
                f'<a class="card" href="{name}/index.html">'
                f'<h2>{html.escape(title)}</h2>'
                f'<p>{desc}</p>'
                f'<span class="card-count">{count} 篇 ›</span></a>')
        home_body += ('\n<section class="modules">\n' + "\n".join(cards)
                      + "\n</section>")
    # 主页“＋ 添加新项目”默认落到第一个/notes 模块
    add_default = ("notes" if (CONTENT_DIR / "notes").is_dir()
                   else (module_info[0][0] if module_info else None))
    (OUT_DIR / "index.html").write_text(
        _page(home_title, home_body, home=True, module=add_default),
        encoding="utf-8")

    print(f"已构建：主页 + {len(module_info)} 个模块 → {OUT_DIR}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="my-site 模块化构建脚本")
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
        http.server.ThreadingHTTPServer(("127.0.0.1", args.port),
                                        handler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
