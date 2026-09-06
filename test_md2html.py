# -*- coding: utf-8 -*-
"""md2html 冒烟测试（无 pytest 等第三方依赖）。

运行：python test_md2html.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from md2html import convert, first_heading

_FAILED = []


def check(name: str, cond: bool) -> None:
    if cond:
        print(f"  ok: {name}")
    else:
        print(f"FAIL: {name}")
        _FAILED.append(name)


def main() -> int:
    print("[1] 行内语法")
    h = convert("# 标题\n\n正文 **粗** *斜* `码` [链](https://x)。")
    check("h1", "<h1>标题</h1>" in h)
    check("strong", "<strong>粗</strong>" in h)
    check("em", "<em>斜</em>" in h)
    check("code span", "<code>码</code>" in h)
    check("link", '<a href="https://x">链</a>' in h)

    print("[2] 列表与嵌套")
    flat = convert("- a\n- b")
    check("平级合并为一个 <ul>", flat.count("<ul>") == 1 and flat.count("<li>") == 2)
    nest = convert("- a\n- b\n  - c")
    check("缩进生成嵌套 <ul>", nest.count("<ul>") == 2 and nest.count("<li>") == 3)
    ol = convert("1. 一\n2. 二")
    check("有序列表", "<ol>" in ol and ol.count("<li>") == 2)

    print("[3] 代码块 / 引用 / 图片 / 分割线")
    code = convert("```py\nprint(1)\n```")
    check("围栏代码块", 'class="language-py"' in code and "print(1)" in code)
    img = convert("![图](p.png)")
    check("图片", '<img src="p.png" alt="图"/>' in img)
    bq = convert("> 引文")
    check("引用", "<blockquote>" in bq)
    hr = convert("---")
    check("分割线", "<hr/>" in hr)

    print("[4] 表格")
    tbl = convert("| 类型 | 用途 |\n| --- | --- |\n| feat | 新功能 |")
    check("table 标签", "<table>" in tbl)
    check("表头", "<th>类型</th>" in tbl)
    check("数据行", "<td>feat</td>" in tbl)

    print("[5] 标题提取")
    check("first_heading", first_heading("# 你好\n正文") == "你好")
    check("无标题为空", first_heading("正文") == "")

    print("[6] 评审回归（H1-H4）")
    xss = convert('[x](a"onmouseover=alert(1))')
    check("H1 链接属性注入被转义",
          'a&quot;onmouseover=alert(1"' in xss
          and 'href="a"onmouseover=' not in xss)
    imgxss = convert('![i](p"onerror=alert(1))')
    check("H1 图片属性注入被转义",
          'src="p&quot;onerror=alert(1"' in imgxss)
    amp = convert("[a&b](https://x/?a=1&b=2)")
    check("H2 & 只转义一次", "&amp;amp;" not in amp
          and 'href="https://x/?a=1&amp;b=2"' in amp and "a&amp;b" in amp)
    lb = convert("[**粗**](u)")
    check("H2 链接文字内可解析粗体", '<a href="u"><strong>粗</strong></a>' in lb)
    q1 = convert("   > hi")
    check("H3 缩进引用不死循环", "<blockquote>" in q1)
    q2 = convert("> a\n\n   > b")
    check("H3 多段缩进引用不崩溃", q2.count("<blockquote>") == 2)
    f1 = convert("  ```py\nx\n  ```")
    check("H4 缩进围栏不崩溃", "language-py" in f1 and "x" in f1)

    print()
    if _FAILED:
        print(f"失败 {len(_FAILED)} 项: {_FAILED}")
        return 1
    print("全部通过 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
