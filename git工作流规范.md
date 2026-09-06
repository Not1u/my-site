# git 工作流规范（my-site 个人网站仓库）

约定与 `E:\HarnessWorkspace\练习\md-blog\git工作流规范.md`、`手机端APP` 仓库一致。

## 1. 提交时机

- 每完成一个**有意义的改动**提交一次（新功能、修 bug、加笔记、文档等），不要积压。
- 每轮工作结束时 `git status` 应为干净状态。
- 网站内容改动 = 源文件 + 重新构建的 `docs/` 一起提交。

## 2. 提交信息格式

```
<类型>: <一句话描述（中文）>

feat:     新功能
fix:      修复问题
docs:     文档/内容
refactor: 重构（行为不变）
chore:    构建/工具/杂务
```

## 3. 不入库内容（.gitignore 兜底）

- `__pycache__/`、`*.pyc`
- 含个人 token / 密码的配置文件
- 注：`docs/` 是发布产物，**需要入库**（GitHub Pages 从它发布）。

## 4. 版本标签

正式发布点用附注标签：

```
git tag -a v0.1 -m "说明"
git push origin v0.1
```

## 5. 分支策略

- `main` 永远保持**可用状态**。
- 试验性改动开分支：`git switch -c 功能名`，做完合并回 main。
- 危险操作（`reset --hard`、`force push`、`rebase`）原则上不做。

## 6. 智能体（DSH）执行规则

- 每轮工作完成后由智能体自动存档：`git add -A` → `git commit -m "<类型>: 描述"`。
- 用户说"不要自动存档"时，仅按明确指示执行。
- 提交前先 `git status` / `git diff` 自查。

## 7. 快速命令

```
git status                        # 看状态
git add -A && git commit -m "docs: 新增 XX 笔记"   # 存档
git log --oneline --graph -10     # 看历史
git push                          # 推送（网站自动更新）
```
