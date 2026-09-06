# my-site —— 个人网站（模块化）

我的个人静态网站。内容按**模块**分区：`content/` 下每个子目录是一个内容模块
（目录里的 `index.md` 是模块介绍，其余 md 是条目）。`python build.py`
构建成静态 HTML 到 `docs/`，由 **GitHub Pages** 从 `main` 分支 `/docs` 发布。

线上地址：<https://Not1u.github.io/my-site/>

## 加内容（三选一）

1. **纯浏览器**：点站点右上角「＋ 添加新项目」→ GitHub 网页编辑器写 md →
   提交 → **GitHub Actions 自动构建发布**（约 1 分钟）。
2. **本机**：写 md → `python build.py` → commit + push。
3. **加新模块**：`content/` 下新建目录 + `index.md`，主页卡片自动出现。

## 本地构建

```powershell
python build.py            # content/ → docs/（先清空旧产物再全量重建）
python build.py --serve    # 构建后本地预览 http://127.0.0.1:8000
python test_md2html.py     # 转换器冒烟测试
```

## 目录结构

```
my-site/
├── .github/workflows/build-site.yml  # push 后自动重建 docs/ 并提交
├── md2html.py / test_md2html.py      # Markdown → HTML 转换器（源自 md-blog）
├── build.py                          # 模块化构建脚本
├── .gitattributes                    # 统一 LF 换行
├── content/                          # 站点内容（源）
│   ├── index.md                      #   主页文案
│   ├── assets/                       #   全局图片资源（md 里用 ../assets/ 引用）
│   └── notes/                        #   ★ 示例模块：学习笔记
│       ├── index.md                  #       模块介绍（卡片/目录页头部）
│       └── *.md                      #       每篇一个条目
├── style.css                         # 样式（基础版，UI 待优化）
└── docs/                             # 构建产物 → Pages 发布目录（入库）
```

## Git 约定

见仓库内 `git工作流规范.md`。
