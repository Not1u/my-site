# my-site —— 个人网站（学习笔记区）

我的个人静态网站。内容用 **Markdown** 写在 `content/`，`python build.py`
构建成静态 HTML 输出到 `docs/`，由 **GitHub Pages** 从仓库 `main` 分支的
`/docs` 目录发布：本地 `git push` 即更新网站。

## 快速上手

```powershell
python build.py            # content/*.md → docs/ 静态站
python build.py --serve    # 构建后本地预览 http://127.0.0.1:8000
```

日常加内容只需三步（详见 `content/notes/如何给本站添加内容.md`）：

1. 在 `content/notes/` 里新建/修改 Markdown 笔记；
2. `python build.py` 重新生成；
3. `git add -A && git commit` 然后 `git push`，网站自动更新。

## 目录结构

```
my-site/
├── md2html.py      # Markdown → HTML 转换器（源自 md-blog 练习仓库）
├── build.py        # 构建脚本：content → docs
├── test_md2html.py # 转换器冒烟测试（python test_md2html.py）
├── content/        # 站点内容（源）
│   ├── index.md        # 首页
│   ├── notes/          # 学习笔记（Markdown）
│   └── assets/         # 图片等二进制，md 里用 ![](assets/文件名) 引用
├── style.css       # 站点样式（当前为基础版，UI 待优化）
└── docs/           # 构建产物 → GitHub Pages 发布目录（入库）
```

## GitHub Pages 配置（一次性）

仓库 Settings → Pages → **Deploy from a branch**：
分支 `main`，目录 `/docs`，保存即可。之后每次 push 自动发布。

## Git 约定

见仓库内 `git工作流规范.md`。
