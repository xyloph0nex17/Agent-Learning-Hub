# -*- coding: utf-8 -*-
"""
Stage 2 · 工具 1/3：把 5 类能力写成"边界处理完好"的真实工具函数
目标：先不接模型，把这 5 个普通 Python 函数各自写对、测对。

  1) search_local(query)   —— 搜索：在本地语料库做向量检索（复用 A5）
  2) read_file(path)       —— 文件：读 data/ 下的文本文件（白名单 + 目录限制）
  3) sql_query(sql)        —— 数据库：在本地 SQLite 知识库上执行只读 SELECT
  4) fetch_webpage(url)    —— 浏览器：抓取公开网页并转成纯文本（走系统代理）
  5) run_python(code)      —— 代码执行：子进程跑一段 Python，带超时

━━━ 一个关键观念：工具函数首先是"好函数"━━━
  工具结果的读者是【模型】。所以出问题时要返回【可读的错误字符串】而不是抛异常，
  让模型知道发生了什么、能否换个参数重试。stage1 的 tools1_funcs.py 就开始建立
  这个习惯，这里把它扩展到"真实能力"。

━━━ 安全边界（重要）━━━
  模型只能"请求"调用工具，真正执行的是宿主程序（我们）。所以每个工具都要自带
  边界：文件限定在 data/ 目录、SQL 只允许 SELECT、网页只允许 http(s)、代码有超时。
  注意 run_python 不是真沙箱，仅用于本地学习演示，不要执行不可信来源的代码。
"""
import os
import re
import sqlite3
import subprocess
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")      # 语料目录
CACHE_DIR = os.path.join(HERE, "cache")
DB_PATH = os.path.join(CACHE_DIR, "knowledge.db")


# ── 1) 搜索：本地语料库的语义检索 ──────────────────────────────
def search_local(query: str) -> str:
    """在本地语料库中检索与 query 最相关的几个片段。"""
    from rag5_retrieve import vector_search      # 延迟导入：只在真正调用时加载
    hits = vector_search(query, top_k=3)
    if not hits:
        return "No relevant content found."
    lines = []
    for i, (chunk, score) in enumerate(hits, start=1):
        lines.append(f"[{i}] ({chunk['doc']}, score={score:.3f}) {chunk['text'][:200]}")
    return "\n".join(lines)


# ── 2) 文件：读 data/ 下的文本文件（限目录 + 后缀白名单）────────
def read_file(path: str) -> str:
    """读取 data/ 目录下的文本文件。path 是相对 data/ 的路径。"""
    allowed = (".md", ".txt", ".json", ".py", ".csv")
    base = os.path.abspath(DATA_DIR)
    target = os.path.abspath(os.path.join(base, path))
    if not target.endswith(allowed):
        return f"Error: only {allowed} files are allowed."
    if not target.startswith(base):
        return "Error: path escapes the data directory."
    try:
        with open(target, encoding="utf-8") as f:
            content = f.read()
        return content[:2000] or "(empty file)"
    except Exception as e:
        return f"Error: {e}"


# ── 3) 数据库：把语料入库，支持只读 SQL 查询 ────────────────────
def build_db(force: bool = False) -> str:
    """把语料 chunk 导入 SQLite 表 chunks(id, doc, title, text)。"""
    from rag2_chunk import get_chunks
    os.makedirs(CACHE_DIR, exist_ok=True)
    if os.path.exists(DB_PATH) and not force:
        return DB_PATH
    chunks = get_chunks()
    con = sqlite3.connect(DB_PATH)
    con.execute("DROP TABLE IF EXISTS chunks")
    con.execute("CREATE TABLE chunks(id TEXT, doc TEXT, title TEXT, text TEXT)")
    con.executemany(
        "INSERT INTO chunks VALUES(?,?,?,?)",
        [(c["id"], c["doc"], c["title"], c["text"]) for c in chunks],
    )
    con.commit()
    con.close()
    return DB_PATH


def sql_query(sql: str) -> str:
    """在本地知识库上执行只读 SQL（只允许 SELECT）。"""
    build_db()                                   # 确保库存在
    if not sql.strip().lower().startswith("select"):
        return "Error: only SELECT queries are allowed."
    try:
        con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)   # 只读连接
        rows = con.execute(sql).fetchall()
        con.close()
        if not rows:
            return "(no rows)"
        rows = rows[:20]                         # 限制返回行数
        return "\n".join(" | ".join(str(x) for x in r) for r in rows)
    except Exception as e:
        return f"SQL error: {e}"


# ── 4) 浏览器：抓取公开网页 → 纯文本 ───────────────────────────
def fetch_webpage(url: str, retries: int = 3) -> str:
    """抓取一个公开网页，去掉 HTML 标签后返回纯文本（走系统代理）。

    网络会抖动（代理下偶发 SSL 失败），所以失败时退避 1 秒重试，最后仍失败
    就返回可读的错误字符串——这正是"工具会失败，要给模型一个兜底"的示例。
    """
    if not re.match(r"^https?://", url):
        return "Error: URL must start with http:// or https://"

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=15,
                             headers={"User-Agent": "Mozilla/5.0 (learning-bot)"})
            r.raise_for_status()
            html = r.text
            break
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(1)                    # 简单退避，再试一次
    else:
        return f"Fetch error after {retries} attempts: {last_err}"

    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)   # 去脚本/样式
    text = re.sub(r"(?s)<[^>]+>", " ", html)                        # 去标签
    text = re.sub(r"&[a-z]+;", " ", text)                           # 去实体
    text = re.sub(r"\s+", " ", text).strip()
    return text[:2000] or "(empty page)"


# ── 5) 代码执行：子进程跑 Python（10 秒超时）───────────────────
def run_python(code: str) -> str:
    """在子进程中执行一段 Python 代码并返回输出。

    安全说明：这【不是沙箱】。仅用于本地学习演示，
    绝不要拿它执行来自不可信来源（网页、用户输入）的代码。
    """
    try:
        p = subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        return "Error: execution timed out (10s)."
    out = (p.stdout or "") + (p.stderr or "")
    return (out[:2000] or "(no output)")


if __name__ == "__main__":
    print("=== 单独自测这 5 个工具（此时还没接模型）===\n")

    print("① search_local('what is an agent') ->")
    print("   " + search_local("what is an agent")[:150].replace("\n", "\n   "), "\n")

    print("② read_file('01_what_is_an_agent.md') ->")
    print("   " + read_file("01_what_is_an_agent.md")[:90].replace("\n", " "), "...\n")
    print("   read_file('../key') ->", read_file("../key"), "\n")

    print("③ build_db() ->", build_db(force=True))
    print("   sql_query('SELECT doc, COUNT(*) FROM chunks GROUP BY doc') ->")
    print("   " + sql_query("SELECT doc, COUNT(*) FROM chunks GROUP BY doc").replace("\n", "\n   "), "\n")
    print("   sql_query('DROP TABLE chunks') ->", sql_query("DROP TABLE chunks"), "\n")

    print("④ fetch_webpage('https://en.wikipedia.org/wiki/Retrieval-augmented_generation') ->")
    print("   " + fetch_webpage(
        "https://en.wikipedia.org/wiki/Retrieval-augmented_generation")[:150], "...\n")

    print("⑤ run_python('print(2**10)') ->", run_python("print(2**10)"))
    print("   run_python('while True: pass') ->", run_python("while True: pass"))
