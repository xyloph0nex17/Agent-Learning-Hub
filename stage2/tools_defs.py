from rag_retrieve import vector_search
import os
import sqlite3
import re
import requests
import subprocess
import sys
import time
import json
from pathlib import Path
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(HERE, "data"))
CACHE_DIR = os.path.join(HERE, "cache")
DB_PATH = os.path.join(CACHE_DIR, "knowledge.db")

def search_local(query:str)->str:
    hits=vector_search(query)
    if not hits:
        return "EMPTY: 未命中"
    result=[]
    for i,(chunk,num) in enumerate(hits,start=1):
        result.append(f"路径{chunk['doc']}\n编号{chunk['id']}\n内容{chunk['text']}")
    return f"OK:{('\n\n').join(result)}"

# def read_file(path:str)->str:
#     allow=(".md",".txt",".py",".json")
#     target=os.path.abspath(os.path.join(DATA_DIR,path))
#     if not target.endswith(allow):
#         return "ERROR: 无读取这类文件的权限"
#     if not target.startswith(DATA_DIR):
#         return "ERROR: 超出工作区域"
#     try:
#         with open(target,encoding="utf-8") as f:
#             text=f.read()
#         return "EMPTY: 空文件" if not text else f"OK:{text[:2000]}"
#     except Exception as e:
#         return f"ERROR: 文件打开错误{e}"
    
def read_file(path: str) -> str:
    base = Path(DATA_DIR).resolve()

    try:
        target = (base / path).resolve()
        target.relative_to(base)
    except (ValueError, OSError, RuntimeError):
        return "ERROR: 超出工作区域或路径无效"

    allowed = {".md", ".txt", ".py", ".json"}
    if target.suffix.lower() not in allowed:
        return "ERROR: 无读取这类文件的权限"

    try:
        text = target.read_text(encoding="utf-8")
        return "EMPTY: 空文件" if not text else f"OK:{text[:2000]}"
    except OSError as e:
        return f"ERROR: 文件打开错误：{e}"

def build_db(force:bool=False):
    os.makedirs(CACHE_DIR, exist_ok=True)
    if os.path.exists(DB_PATH) and not force:
        return DB_PATH
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DROP TABLE IF EXISTS chunks")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS chunks(
                id TEXT,
                doc TEXT,
                title TEXT,
                text TEXT
            )"""
        )
        from rag_chunker import get_chunks
        chunks=get_chunks()
        conn.executemany("INSERT into chunks (id,doc,title,text) VALUES(?,?,?,?)",
        [(c["id"],c["doc"],c["title"],c["text"])for c in chunks])
    conn.close()
    return DB_PATH
    
def sql_query(QUERY:str):
    build_db()
    if not QUERY.strip().lower().startswith("select"):
        return "ERROR: 仅允许使用select查询"    
    try:
        conn=sqlite3.connect(DB_PATH)
        result=conn.execute(QUERY).fetchall()
        conn.close()
        
        return "EMPTY: 结果为空" if not result else f"OK: 结果为{result}"
    except Exception as e:
        return f"ERROR: 数据库报错{e}"

def fetch_webpage(url: str, retries: int = 3) -> str:
    if not re.match(r"^https?://", url):
        return "ERROR: URL 必须以 http:// 或 https:// 开头"
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
                time.sleep(1)                 
    else:
        return f"ERROR: Fetch error after {retries} attempts: {last_err}"

    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html) 
    text = re.sub(r"(?s)<[^>]+>", " ", html)                        
    text = re.sub(r"&[a-z]+;", " ", text)                          
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "EMPTY: 空页面"
    else:
        return f"OK: {text[:2000]}"


def run_python(code: str) -> str:
    try:
        p = subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        return "ERROR: execution timed out (10s)."
    out = (p.stdout or "") + (p.stderr or "")
    if p.returncode != 0:
        detail = out[:2000] or "没有错误输出"
        return f"ERROR: 程序运行失败（退出码 {p.returncode}）：\n{detail}"

    if not out.strip():
        return "EMPTY: 无输出"

    return f"OK: {out[:2000]}"
if __name__ == "__main__":
    #print(search_local(input()))
    #build_db()
    print(fetch_webpage(input()))
#"select * from chunks where id=?#,(01_what_is_an_agent.md#0)
