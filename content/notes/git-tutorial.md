# Git 从零到实践 —— 完整中文教程

> 面向：Windows + PowerShell 环境（本机已装 Git 2.55）。
> 目标：学完你能独立完成「初始化 → 日常存档 → 分支管理 → 推送 GitHub/Gitee → 出问题回滚」。
> 配合 DSH：文档最后有「与智能体协作」的约定，读完后可以让 AI 直接帮你操作 git。

---

## 目录
1. [Git 是什么，为什么要用](#1-git-是什么为什么要用)
2. [环境与首次配置](#2-环境与首次配置)
3. [五步上手：最小闭环](#3-五步上手最小闭环)
4. [三个区域与日常操作](#4-三个区域与日常操作)
5. [撤销与回滚（按危险程度分级）](#5-撤销与回滚按危险程度分级)
6. [分支与合并](#6-分支与合并)
7. [远程仓库：GitHub / Gitee](#7-远程仓库github--gitee)
8. [个人项目"存档"工作流](#8-个人项目存档工作流)
9. [与 DSH 智能体协作的 git 约定](#9-与-dsh-智能体协作的-git-约定)
10. [附录：命令速查表](#10-附录命令速查表)

---

## 1. Git 是什么，为什么要用

**一句话**：Git 是"存档 + 时光机 + 多线平行世界管理"工具，替你记录每个文件的每次改动，随时可以回到任意历史版本、对比差异、多人/多机协同。

**和"复制文件夹存备份"的区别**：

| | 手动复制存档 | Git |
|---|---|---|
| 存了什么 | 整个文件夹（巨大） | 每次的**差异**（极小） |
| 能不能看历史 | 不能，只有最新 | 每次改动+作者+时间+原因 |
| 出错了能不能回来 | 难 | 一键回到任意版本 |
| 多版本并行 | 复制多个文件夹，乱 | 分支，干净利落 |
| 云备份 | 手动上传 | push 一条命令 |

**核心概念（先混个脸熟）**：
- **仓库（repository）**：被 git 管理的文件夹，根目录下会有一个隐藏的 `.git` 目录存放全部历史。
- **工作区**：你平时看到的、正在编辑的文件。
- **暂存区（index）**：`git add` 后文件进入的"待提交清单"。
- **版本库（commit 历史）**：`git commit` 把暂存区固化成一个不可变快照。
- **commit**：一次存档。每个 commit 有唯一 ID（40 位哈希，平时看前 7 位）。
- **HEAD**：指向"当前所在位置"的指针（通常指向当前分支的最新 commit）。
- **分支（branch）**：一条独立的提交线。默认主分支叫 `main`（旧项目叫 `master`）。
- **远程（remote）**：云端或其它机器上的同一仓库副本，常命名为 `origin`。

---

## 2. 环境与首次配置

本机 Git 已装好（`C:\Program Files\Git`，在 PATH 中），PowerShell 里直接敲 `git` 即可。

```powershell
# 查看版本
git --version

# 一次性配置身份（决定 commit 上署名谁，已配好可跳过）
git config --global user.name  "Not1u"
git config --global user.email "m13761790051@163.com"

# 查看当前全局配置
git config --global --list
```

> **Windows 提示**：首次 add 时常见 `LF will be replaced by CRLF` 警告，是行尾符自动转换提示，**无害**，不用管。
> 想安静一点可以执行 `git config --global core.autocrlf true`。

**常用设置建议**：
```powershell
git config --global init.defaultBranch main   # 以后 init 默认分支叫 main
git config --global core.autocrlf true        # Windows 行尾自动转换
git config --global pull.rebase false         # pull 用 merge（新手友好）
```

---

## 3. 五步上手：最小闭环

在 PowerShell 里实操一次（任选一个练习文件夹，如 `E:\练习`）：

```powershell
# 1) 进入/新建项目文件夹
mkdir E:\练习\hello-git
cd E:\练习\hello-git

# 2) 初始化仓库
git init -b main

# 3) 写一个文件
Set-Content -Path a.txt -Value "hello git" -Encoding UTF8

# 4) 存进版本库（add + commit 两步）
git add a.txt
git commit -m "第一次存档：添加 a.txt"

# 5) 查看成果
git status        # 干净 = 没有未存档改动
git log --oneline # 显示提交历史
```

改一改文件，再看 git 怎么"看见"你的改动：

```powershell
Add-Content -Path a.txt -Value "第二行内容" -Encoding UTF8
git status                # 红色/提示: modified a.txt（未暂存）
git diff                  # 看具体改了什么
git add a.txt
git commit -m "第二次存档：追加一行"
git log --oneline         # 现在有 2 个 commit 了
```

**到这里你已经会"存档"了。** 后面全是把这三个动作（改 → add → commit）用得更专业。

---

## 4. 三个区域与日常操作

```
工作区文件  --git add-->  暂存区(index)  --git commit-->  版本库(HEAD)
    (你的修改)            (待提交清单)        (永久快照)
```

| 命令 | 作用 |
|---|---|
| `git status` | 当前状态：哪些改了、哪些已暂存 |
| `git add 文件` | 把指定改动放入暂存区 |
| `git add -A` | 把**所有**改动（新增/修改/删除）放入暂存区 |
| `git add .` | 同上（当前目录内） |
| `git add -p` | 交互式挑选"一个文件里的部分行"暂存（精细提交用） |
| `git commit -m "说明"` | 把暂存区固化成一次存档 |
| `git commit -am "说明"` | 一步完成"已跟踪文件的 add + commit"（新文件仍需先 add） |
| `git diff` | 工作区 vs 暂存区的差异（还没 add 的改动） |
| `git diff --cached` | 暂存区 vs 上次提交的差异（已 add 未 commit 的改动） |
| `git log` | 提交历史（`--oneline` 一行一条，`-n 5` 只看 5 条） |
| `git show <commitID>` | 看某次提交改了什么 |

**提交信息（commit message）规范**——让人和 AI 都能看懂历史：
```
格式：<类型>: <干什么了>

feat: 新增扫码连接功能
fix: 修复连接失败时崩溃的问题
docs: 更新 README 安装说明
refactor: 重构 WebView 初始化代码
chore: 更新构建脚本
```

**`.gitignore`——让 git 无视某些文件**（密钥、构建产物、临时文件）：
在仓库根目录建一个 `.gitignore` 文本文件，每行一条规则：
```
build/
*.apk
密钥目录/
*.log
```
之后 `git add -A` 会自动跳过这些。

---

## 5. 撤销与回滚（按危险程度分级）

**原则：能"重做"的改动用 restore；已推送公网的提交用 revert；reset 只动本地时用。**

### 级别 0：还没 add（改乱了想放弃）
```powershell
git restore 文件.txt        # 把该文件还原成上次提交的样子（丢弃本次改动）
git restore .               # 还原全部
```
> 危险：被还原的改动**永久丢失**，没有后悔药。谨慎用。

### 级别 1：已经 add 了（想取消暂存，但保留改动）
```powershell
git restore --staged 文件.txt   # 从暂存区拿下来（文件改动还在工作区）
```

### 级别 2：已 commit，但想"补一刀"（改提交信息/补漏文件）
```powershell
git commit --amend -m "修正后的信息"   # 把最后一次提交替换掉（会生成新 ID）
```
> ⚠️ 只对**还没推送**的提交用；已 push 的不要 amend（历史会被改写，同步会乱）。

### 级别 3：已 commit 多步，想撤销某次（推荐 revert，安全）
```powershell
git log --oneline          # 找到要撤销的提交 ID
git revert <commitID>      # 生成一个"反向的新提交"来抵消它，历史不被改写
```
> revert 不删除历史、不影响别人，**任何情况都安全**，是"反悔"的首选。

### 级别 4：回退指针（reset，本地可用，推送过就麻烦）
三个模式对照（`<版本ID>` 可用 `HEAD`、`HEAD~1`(上一次)、`HEAD~3`(前三次) 或真实哈希）：

| 模式 | 版本库 | 暂存区 | 工作区 | 用途 |
|---|---|---|---|---|
| `git reset --soft <版本>` | 回退 | 保留 | 保留 | 想重新分组提交 |
| `git reset --mixed <版本>`（默认） | 回退 | 清空 | 保留 | 取消已 add |
| `git reset --hard <版本>` | 回退 | 清空 | **清空** | 彻底回到过去 ⚠️ |

```powershell
git reset --hard HEAD~1    # 丢弃最后一次提交及其所有改动（不可逆！）
git reset --hard <commitID> # 整体回到某个历史版本
```
> `--hard` 后工作区文件会被覆盖/删除，**无法找回**（除非有 reflog，见下）。新手慎用。

### 后悔药：reflog（reset --hard 后想找回）
```powershell
git reflog          # 列出所有"曾经到过"的位置（包括被 reset 掉的）
git reset --hard <旧ID>   # 从 reflog 里找回
```

---

## 6. 分支与合并

**为什么需要分支**：想在"存档主线"上试验新功能、改 bug，又不想把半成品混进主线 → 开一条平行线，做完再合回来。

```powershell
# 查看/新建/切换
git branch                # 列出本地分支（* 号=当前）
git branch 新功能名        # 新建分支（不切换）
git checkout -b 新功能名   # 新建并立即切换（老写法）
git switch -c 新功能名      # 新建并立即切换（新写法，推荐）
git switch main           # 切回主线

# 在分支上正常 改→add→commit，提交只属于当前分支
```

**合并回主线**：
```powershell
git switch main           # 先回到 main
git merge 新功能名         # 把分支内容并进来
git branch -d 新功能名     # 合并完删掉分支
```

**冲突（conflict）**：两人/两分支改了同一行时，merge 会停下：
```
<<<<<<< HEAD
主线里的版本
=======
分支里的版本
>>>>>>> 新功能名
```
解决步骤：
1. 打开文件，手动保留想要的写法，删掉 `<<<<<<< ======= >>>>>>>` 标记行；
2. `git add 该文件`；
3. `git commit -m "合并分支"`（git 会提示 merge 冲突已完成）。

**个人存档推荐**：`main` 永远保持"可用的正式版"；做新功能开分支，做完合回、打 tag 发版。

---

## 7. 远程仓库：GitHub / Gitee

本地仓库 ≠ 备份。要"电脑坏了也不丢 + 多台设备同步"，配一个云端远程。

### 7.1 生成 SSH 密钥（本机已生成 ✅）
已生成 ed25519 密钥。若换机器重做：
```powershell
ssh-keygen -t ed25519 -C "你的邮箱"
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub   # 复制输出的整行公钥
```

### 7.2 把公钥告诉 GitHub
1. 登录 [github.com](https://github.com) → 右上角头像 → **Settings**
2. 左侧 **SSH and GPG keys** → **New SSH key**
3. Title 随意（如 `DESKTOP-DELL`），Key 粘贴公钥整行 → **Add SSH key**

### 7.3 测试连通
```powershell
ssh -T git@github.com
# 首次会问是否信任主机，输入 yes；看到 "Hi Not1u! You've successfully authenticated" 即成功
```

### 7.4 在 GitHub 网页上建一个空仓库
New repository → 名字如 `dsh-mobile` → **不要**勾选 Add README（避免和本地冲突）→ Create。
创建后页面会给两条命令，照抄即可：

### 7.5 把本地仓库推上去
```powershell
# 在本地仓库目录里执行：
git remote add origin git@github.com:你的用户名/dsh-mobile.git   # 关联远程，命名 origin
git push -u origin main                                          # 首次推送（-u 记住对应关系）
```

### 7.6 之后的日常循环
```powershell
git add -A
git commit -m "说明"
git push            # 推送到云端
```
多台机器/换电脑拉下来：
```powershell
git clone git@github.com:你的用户名/dsh-mobile.git   # 首次拿全仓库
git pull                                             # 之后同步远程最新改动
```

**几个注意点**：
- 先 `git pull` 再 `git push`，有分歧时先解决再推；
- `git remote -v` 查看远程地址；
- 不想用 SSH 也可用 HTTPS + 个人访问令牌（PAT），但 SSH 更省事；
- Gitee 同理：公钥粘到 gitee.com → 设置 → SSH 公钥。

---

## 8. 个人项目"存档"工作流

把 git 当"自动存档系统"用的日常节奏：

1. **每完成一个有意义的改动就 commit 一次**（不要憋一整天一次提交）
2. **提交信息写清"做了什么+为什么"**（见第 4 节格式）
3. **发布一个版本就打 tag**
   ```powershell
   git tag v1.1                # 给当前 commit 打标签
   git tag -a v1.1 -m "DSH 手机端 1.1 正式版"   # 带说明的标签（推荐）
   git push origin v1.1        # 推送标签
   git tag                     # 查看所有标签
   ```
4. **想回到某个发布版**：`git checkout v1.1`（查看）/ `git switch -c 修复分支 v1.1`（基于它开分支改）
5. **每轮工作结束前检查**：`git status` 应干净；有未提交就补 commit

**小抄式的完整一轮**：
```powershell
git status                          # 看有什么改动
git diff                            # 确认改对没有
git add -A
git commit -m "feat: 增加xxx"
git push                            # 有远程时
git log --oneline -5                # 确认历史
```

---

## 9. 与 DSH 智能体协作的 git 约定

你在这套 Harness 里让我（智能体）做项目时，可以随时说"**用 git 存档**"，我会执行以上命令。为了让协作顺畅，建议项目根目录放一个 `git工作流规范.md`（已为 手机端APP 仓库建好），约定如下：

- 我在**每轮工作完成、确认结果无误后**，自动执行 `git add -A && git commit`，提交信息按 `<类型>: 描述` 规范写；
- **敏感文件（签名密钥、含 token 的配置）绝不提交**，靠 `.gitignore` 拦；
- 大版本完成后打 tag（如 `v1.1`），方便你随时回滚/对比；
- 涉及"撤销/回滚/force"等危险操作前，我会先说明后果再执行；
- 你说"不要自动存档"时，我只在明确要求后 commit。

> 把 git 命令直接交给智能体跑是安全的：git 每次改动都有记录、可回滚，比手改文件安全得多。

---

## 10. 附录：命令速查表

**开始**
```powershell
git init -b main          # 初始化
git clone <远程地址>       # 克隆远程仓库
```

**日常三连**
```powershell
git status                # 状态
git add -A                # 全加
git commit -m "msg"       # 存档
```

**查看**
```powershell
git log --oneline --graph -10   # 图形化最近10条
git diff                        # 未暂存差异
git diff --cached               # 已暂存差异
git show <ID>                   # 某次提交
```

**撤销**
```powershell
git restore 文件               # 丢弃工作区改动
git restore --staged 文件      # 取消暂存
git revert <ID>                # 安全撤销某次提交
git reset --hard <ID>          # 强回退（慎用）
git reflog                     # 后悔药
```

**分支**
```powershell
git branch                      # 列表
git switch -c 名字               # 新建并切换
git switch 名字                  # 切换
git merge 分支                   # 合并
git branch -d 分支               # 删分支
```

**远程**
```powershell
git remote -v                      # 查看远程
git remote add origin <地址>        # 关联
git push -u origin main            # 首次推送
git push                           # 推送
git pull                           # 拉取
git tag -a v1.1 -m "说明" && git push origin v1.1   # 打标签并推送
```

**其它**
```powershell
git stash          # 临时藏起未提交改动（换分支用）
git stash pop      # 取回
git config --global alias.lg "log --oneline --graph"   # 自定义别名：git lg
```

---
*学完标准：能不查资料独立完成「init → 多次 commit → 建分支改东西 → 合并 → 打 tag → 推 GitHub → revert 一次错误提交」。做到了，日常存档绰绰有余。*
