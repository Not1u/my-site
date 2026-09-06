# 如何给本站添加内容

本站结构：**源内容在 `content/`，构建产物在 `docs/`，GitHub Pages 从 `docs/` 发布**。

## 加一篇学习笔记（日常最常用）

1. 在 `content/notes/` 新建一个 `.md` 文件（文件名建议用英文，便于网址）；
2. 文件开头用 `# ` 写标题（会作为页面标题）；
3. 需要插图时，图片放进 `content/assets/`，md 里这样引用：

   ```
   ![](../assets/图片名.png)
   ```

   > 注意路径带 `../`：源目录里从 notes 指向 assets，构建后页面也在
   > docs/notes/ 下指向 docs/assets，两级目录结构一致，所以照写即可。

4. 重新生成并本地检查：

   ```powershell
   python build.py
   python build.py --serve   # 打开 http://127.0.0.1:8000
   ```

5. 存档并发布：

   ```powershell
   git add -A
   git commit -m "docs: 新增笔记《xxx》"
   git push
   ```

   推上去后 GitHub Pages 约几十秒内自动更新。

## 修改/删除

- 改内容：直接编辑对应 md → 重新 `build.py` → commit + push。
- 删除一篇：删掉 md 文件 → 重新构建（旧 html 会残留在 docs/，手动删对应文件）→ commit + push。

## 以后想扩展

- 新开一个内容区（如随笔/相册）：在 `content/` 下加子目录，并让 `build.py`
  增加对应的遍历与首页分组（当前只扫 `notes/`）。
- 样式统一在 `style.css` 调整——现阶段先不动，等 UI 阶段一起做。

## 内容格式约定（待细化）

- 目前以 **Markdown 文本**为主（纯文本、git diff 友好）；
- 图片等二进制放 `assets/`（命名规则、压缩策略以后再定）。
