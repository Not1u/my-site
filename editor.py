# -*- coding: utf-8 -*-
"""my-site 本地写作编辑器（零依赖，仅本机可用）。

为什么需要它：站点是静态站，浏览器页面无法写入仓库；本服务在**你电脑上**
负责把编辑内容写成 md → 重建站点 → git 提交并推送，编辑器界面仍在浏览器里。

运行：
    python editor.py            # 打开 http://127.0.0.1:8010
    python editor.py --port 8010 --no-push   # 只保存不推送（调试用）

接口：
    GET  /            编辑器页面
    GET  /api/list    现有模块与条目
    POST /api/preview {content}           → 转换后的 HTML（预览=发布一致）
    POST /api/save    {module,slug,content} → 写 md + 重建 + 提交 [+推送]
"""

import argparse
import json
import pathlib
import re
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ROOT_DIR = pathlib.Path(__file__).resolve().parent
CONTENT_DIR = ROOT_DIR / "content"
MODULE_DIRS = [p for p in CONTENT_DIR.iterdir()
               if p.is_dir() and p.name != "assets"]

SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def _modules() -> dict[str, list[str]]:
    """{模块名: [条目 slug, ...]}，index.md 是模块介绍不算条目。"""
    out: dict[str, list[str]] = {}
    for p in sorted(CONTENT_DIR.iterdir()):
        if not p.is_dir() or p.name == "assets":
            continue
        items = sorted(m.stem for m in p.glob("*.md") if m.name != "index.md")
        out[p.name] = items
    return out


def _run(args: list[str], timeout: int = 120) -> tuple[int, str]:
    """在仓库根目录跑命令，返回 (返回码, 合并输出)。"""
    try:
        proc = subprocess.run(args, cwd=str(ROOT_DIR), capture_output=True,
                              text=True, encoding="utf-8", timeout=timeout)
        text = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, text.strip()
    except subprocess.TimeoutExpired:
        return 1, f"命令超时：{' '.join(args)}"


def _slug_from_content(content: str) -> str:
    """从第一个 # 标题生成 ASCII 文件名；不行就退回时间戳。"""
    for line in content.replace("\r\n", "\n").split("\n"):
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m:
            s = re.sub(r"[^A-Za-z0-9]+", "-", m.group(1).strip()).strip("-").lower()
            if s:
                return s
    return time.strftime("note-%Y%m%d-%H%M%S")


def _save(module: str, slug: str, content: str, do_push: bool) -> dict:
    """写文件 + 重建 + 提交 +（可选）推送。返回结果字典。"""
    # 安全校验：module 必须是 content 下的模块目录
    module_dir = CONTENT_DIR / module
    if not module_dir.is_dir() or module_dir.resolve() == CONTENT_DIR.resolve():
        return {"ok": False, "error": f"非法模块：{module}"}
    if not slug or not SLUG_RE.match(slug):
        return {"ok": False, "error": f"文件名需为英文/数字/-/_：{slug!r}"}
    target = (module_dir / f"{slug}.md").resolve()
    if not str(target).startswith(str(CONTENT_DIR.resolve())):
        return {"ok": False, "error": "路径越界，已拒绝"}

    target.write_text(content, encoding="utf-8")

    code, log = _run([sys.executable, "build.py"])
    if code != 0:
        return {"ok": False, "error": f"重建失败\n{log}"}

    code, log = _run(["git", "add", "--", "docs", f"content/{module}"])
    if code != 0:
        return {"ok": False, "error": f"git add 失败\n{log}"}
    code, log = _run(["git", "commit", "-m", f"docs: 编辑器新增《{slug}》"])
    if code != 0:
        # 无改动（内容与上次相同）不算错
        if "nothing to commit" in log:
            return {"ok": True, "message": f"已保存（无变化）：{module}/{slug}.md", "pushed": False}
        return {"ok": False, "error": f"git commit 失败\n{log}"}

    pushed = False
    push_msg = ""
    if do_push:
        code, push_log = _run(["git", "push"])
        pushed = code == 0
        push_msg = push_log if not pushed else "已推送"

    return {
        "ok": True,
        "message": f"已保存：{module}/{slug}.md" + (f"（{push_msg}）" if do_push else "（未推送）"),
        "pushed": pushed,
    }


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>写作编辑器 — my-site</title>
<style>
  body { margin:0; font:15px/1.6 system-ui,"Segoe UI","Microsoft YaHei",sans-serif; background:#faf9f6; color:#1f2328; }
  header { display:flex; align-items:center; gap:12px; padding:10px 16px; background:#fff; border-bottom:1px solid #d8dee4; }
  header h1 { font-size:16px; margin:0 auto 0 0; }
  .btn { border:1px solid #d8dee4; background:#fff; border-radius:6px; padding:6px 12px; cursor:pointer; font-size:14px; }
  .btn.primary { background:#0969da; border-color:#0969da; color:#fff; }
  .btn:disabled { opacity:.5; cursor:default; }
  .layout { display:grid; grid-template-columns:220px 1fr 1fr; height:calc(100vh - 49px); }
  .side { border-right:1px solid #d8dee4; background:#fff; overflow:auto; padding:10px; }
  .side h2 { font-size:13px; color:#57606a; margin:10px 4px 4px; }
  .side ul { list-style:none; margin:0 0 10px; padding:0; }
  .side li a { display:block; padding:4px 8px; text-decoration:none; color:#1f2328; border-radius:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .side li a:hover, .side li a.on { background:#eaeef2; }
  .side button.new { width:100%; margin-bottom:6px; }
  .main { display:flex; flex-direction:column; }
  .main input[type=text] { border:1px solid #d8dee4; border-radius:6px; padding:8px 10px; margin:10px 10px 0; font-size:15px; }
  .main textarea { flex:1; border:none; resize:none; outline:none; padding:12px; font:14px/1.7 Consolas,monospace; background:#fff; margin:10px; border:1px solid #d8dee4; border-radius:6px; }
  iframe { width:100%; height:100%; border:none; background:#fff; }
  #log { position:fixed; left:0; right:0; bottom:0; max-height:120px; overflow:auto; background:#1f2328; color:#9ecbff; font:12px Consolas,monospace; padding:8px 12px; display:none; white-space:pre-wrap; }
</style>
</head>
<body>
<header>
  <h1>✏️ 写作编辑器</h1>
  <button class="btn primary" id="btnSave">保存并发布</button>
  <button class="btn" id="btnPrev">预览</button>
  <span id="hint" style="color:#57606a;font-size:13px"></span>
</header>
<div class="layout">
  <div class="side">
    <h2>模块 / 条目</h2>
    <button class="btn new" id="btnNew">＋ 新建（默认 notes）</button>
    <div id="tree"></div>
  </div>
  <div class="main">
    <input id="slug" type="text" placeholder="文件名（英文/数字/-，留空自动生成）"/>
    <textarea id="content" placeholder="# 标题&#10;&#10;正文…（Markdown）"></textarea>
  </div>
  <div><iframe id="preview" title="预览"></iframe></div>
</div>
<div id="log"></div>
<script>
const $ = (id) => document.getElementById(id);
let current = { module: "notes", slug: "" };

async function api(path, body) {
  const opt = body ? { method: "POST", headers: { "Content-Type": "application/json" },
                      body: JSON.stringify(body) } : {};
  const r = await fetch(path, opt);
  return r.json();
}
function log(msg) { const l = $("log"); l.style.display = "block"; l.textContent += msg + "\\n"; l.scrollTop = l.scrollHeight; }
function setHint(t) { $("hint").textContent = t; }

async function refreshTree() {
  const data = await api("/api/list");
  $("tree").innerHTML = "";
  for (const mod of Object.keys(data)) {
    const h = document.createElement("h2");
    h.textContent = mod + (mod === "notes" ? "（默认）" : "");
    $("tree").appendChild(h);
    const ul = document.createElement("ul");
    const items = [["（模块目录页）", "index"], ...data[mod].map(s => [s, s])];
    for (const [label, key] of items) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.textContent = label; a.href = "#";
      if (mod === current.module && key === current.slug) a.classList.add("on");
      a.onclick = async (ev) => { ev.preventDefault(); await loadNote(mod, key); };
      li.appendChild(a); ul.appendChild(li);
    }
    $("tree").appendChild(ul);
  }
}
async function loadNote(mod, slug) {
  current = { module: mod, slug: slug };
  await refreshTree();
  setHint(mod + "/" + (slug === "index" ? "index.md（模块介绍）" : slug + ".md"));
  // 本地读取源文件
  const src = await fetch("/raw/" + mod + "/" + (slug === "index" ? "index.md" : slug + ".md"));
  if (src.ok) { const text = await src.text(); $("content").value = text; } else { $("content").value = ""; }
  $("slug").value = slug === "index" ? "" : slug;
}
async function preview() {
  const html = await api("/api/preview", { content: $("content").value });
  $("preview").srcdoc = "<style>body{font:15px/1.7 system-ui,sans-serif;margin:24px}pre{background:#f6f8fa;padding:10px;border-radius:6px;overflow:auto}</style>" + html.html;
}
async function save() {
  $("btnSave").disabled = true; $("btnSave").textContent = "保存中…";
  try {
    const res = await api("/api/save", { module: current.module, slug: $("slug").value.trim(), content: $("content").value });
    log((res.ok ? "✅ " : "❌ ") + (res.message || res.error || "未知结果"));
    setHint(res.message || res.error || "");
    await refreshTree();
    if (!res.ok) log(res.error || "");
  } finally { $("btnSave").disabled = false; $("btnSave").textContent = "保存并发布"; }
}
$("btnSave").onclick = save;
$("btnPrev").onclick = preview;
$("btnNew").onclick = async () => {
  current = { module: "notes", slug: "" };
  $("slug").value = ""; $("content").value = ""; $("preview").srcdoc = "";
  setHint("正在编辑新笔记（模块 notes）"); await refreshTree();
};
$("content").addEventListener("input", () => setHint("未保存：notes/" + ($("slug").value.trim() || "新文件") + ".md"));
refreshTree();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # 静默访问日志
        pass

    def _send(self, code: int, body: bytes, ctype: str = "text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        # 客户端编码可能不一致，多试几种再解析
        for enc in ("utf-8-sig", "utf-8", "gb18030"):
            try:
                return json.loads(raw.decode(enc))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        return {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, PAGE.encode("utf-8"))
        elif path == "/api/list":
            self._send(200, json.dumps(_modules(), ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")
        elif path.startswith("/raw/"):
            rel = path[len("/raw/"):]
            f = (ROOT_DIR / rel).resolve()
            if str(f).startswith(str(CONTENT_DIR.resolve())) and f.is_file():
                self._send(200, f.read_text(encoding="utf-8").encode("utf-8"))
            else:
                self._send(404, b"not found")
        else:
            self._send(404, b"not found")

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/preview":
            data = self._read_json()
            import md2html
            html = md2html.convert(data.get("content", ""))
            self._send(200, json.dumps({"html": html}, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")
        elif path == "/api/save":
            data = self._read_json()
            module = (data.get("module") or "notes").strip()
            slug = (data.get("slug") or "").strip()
            content = data.get("content") or ""
            if not content.strip():
                self._send(200, json.dumps(
                    {"ok": False, "error": "内容为空，未保存"},
                    ensure_ascii=False).encode("utf-8"),
                    "application/json; charset=utf-8")
                return
            if not slug:
                slug = _slug_from_content(content)
            result = _save(module, slug, content, do_push=not self.server.no_push)
            self._send(200, json.dumps(result, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")
        else:
            self._send(404, b"not found")


def main() -> int:
    parser = argparse.ArgumentParser(description="my-site 本地写作编辑器")
    parser.add_argument("--port", type=int, default=8010)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--no-push", action="store_true",
                        help="保存后不推送（调试用）")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.no_push = args.no_push
    print(f"✏️  写作编辑器已启动：http://{args.host}:{args.port}"
          + ("（--no-push 模式）" if args.no_push else ""))
    print("Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
