# git 学习笔记（练手实录）

这份笔记记录我在 md-blog 项目里实际用到的 git 命令与要点，
写完一次就在这里追加一次，用真实历史当教材。

## 最小闭环：改 → add → commit

```powershell
git status                 # 先看状态
git add -A                 # 全部改动进暂存区
git commit -m "feat: 说明"  # 固化成一个快照
git log --oneline --graph  # 看历史
```

- `git status`：红色 = 已改未暂存；绿色 = 已暂存待提交。
- 提交信息格式 `<类型>: 一句话`：feat / fix / docs / refactor / chore。
- 每完成一个有意义的改动就提交，不要攒一大堆。

## 常用检查命令

- `git diff`：看还没 add 的具体改动
- `git diff --cached`：看已 add 未 commit 的改动
- `git log --oneline -10`：最近 10 条提交
- `git show <ID>`：某次提交改了什么

## 提交信息规范速记

| 类型 | 用途 |
| --- | --- |
| feat | 新功能 |
| fix | 修 bug |
| docs | 文档 |
| refactor | 重构（行为不变） |
| chore | 构建/工具/杂务 |

## 学到的坑

- `git init` 作用在**当前目录**——先 `cd` 到项目目录再 init，或加 `-C` 指定。
- 新仓库还没 commit 前，删 `.git` 即可完全还原；一旦 commit 就留下历史。
- `LF will be replaced by CRLF` 警告无害，是 Windows 行尾符自动转换。

## 分支与合并（本仓库实录）

```powershell
git switch -c 表格语法     # 从 main 开新分支并切换
git switch main            # 切回主线
git merge --no-ff 表格语法  # 合并（--no-ff 保留分支拓扑，历史图更清晰）
git branch -d 表格语法      # 合并完删除分支
git log --oneline --graph  # 看分叉与合并的形状
```

## 版本标签（v0.1 实录）

```powershell
git tag -a v0.1 -m "说明"   # 附注标签（推荐）
git tag -n                  # 列出标签
git show v0.1 --no-patch    # 看标签指向谁
```

## revert 撤销（安全反悔，历史不丢）

```powershell
git revert --no-edit HEAD   # 生成一条反向提交抵消最近提交
```

- revert **不改写历史**：原提交还在，只是多了条反向提交，任何情况都安全。
- 只适合撤销"已提交的改动"；还没 add 的用 `git restore`。

## 今天另一个大坑：程序"死循环"

- 症状：python 跑起来没输出、CPU 一直 100%。
- 排查：`faulthandler.dump_traceback_later(5, exit=True)` 5 秒后自动打印卡住的堆栈；
  monkeypatch 打日志看函数被重复调用。
- 根因：`_consume_table` 内部推进了行号，但**没把新行号返回给主循环**，
  主循环 `continue` 后行号不变 → 永远处理同一行。
- 教训：解析器里"消费了多少输入"必须通过返回值传出来，主循环每次都要前进。

## 让 AI 子代理做代码评审（实战）

- 用后台子代理独立评审代码：不共享本对话上下文，能发现"当局者迷"的问题。
- 评审结论要**逐条亲自复现**再动手，别直接照单全收（这次 4 条高危全部属实）。
- 修复后把评审用例加进测试，防止将来改回归。

### 本次评审抓到的 4 个高危 bug

| 编号 | 问题 | 修复 |
| --- | --- | --- |
| H1 | 属性注入：url/alt 里的 `"` 未转义，可注入 `onmouseover` 等事件 | 属性值用 `html.escape(quote=True)` |
| H2 | 先整段转义再拼 HTML → `&` 双重转义、链接文字内粗体被转义成字面量 | 改为"先解析、输出时逐段单次转义" |
| H3 | 行首空格的引用：判定用 stripped、消费用原始行 → 判了却吃不掉 → 死循环 | 引用正则允许 ≤3 空格，判定与消费同规 |
| H4 | 行首空格的围栏：判定匹配、消费崩溃（None.group）→ 整站构建中断 | 围栏正则允许行首缩进，闭合行 lstrip 判定 |

- 教训：H3 和表格死循环是**同一类 bug**（判定与消费规则不一致 / 行号不推进），
  写解析器时"判定用的行"和"消费用的行"必须是同一条规则。
- 转义分两类：文本内容 `quote=False`，属性值必须 `quote=True`。
