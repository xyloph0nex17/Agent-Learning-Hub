# -*- coding: utf-8 -*-
"""
Stage 2 · A1：加载本地语料库
目标：把 data/ 目录下的一批 .md 文件读进内存，变成结构化文档列表。

为什么先做这一步？
    RAG 的第一步永远是"有一个资料库"。这里的资料库就是 data/ 里的 8 篇 .md。
    后面所有的切块、检索、引用，都建立在这批文档之上。
"""
import glob
import os
import re

# 用 __file__ 定位 data/ 目录 —— 这样不管你在哪个目录运行，都能找到语料
# os.path.dirname(__file__)      -> .../stage2/AIcode
# 再拼上 "..", "data"           -> .../stage2/data
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def load_docs(data_dir: str = DATA_DIR) -> list[dict]:
    """读取 data_dir 下所有 .md，返回文档列表。

    每篇文档是一个字典：
        {"path": 文件名, "title": 标题, "text": 全文}
    """
    docs = []
    for path in sorted(glob.glob(os.path.join(data_dir, "*.md"))):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        # 标题取全文第一行 "# xxx" 的内容
        m = re.search(r"^#\s+(.+)$", text, re.M)
        title = m.group(1).strip() if m else os.path.basename(path)
        docs.append({
            "path": os.path.basename(path),
            "title": title,
            "text": text,
        })
    return docs


if __name__ == "__main__":
    docs = load_docs()
    print(f"共加载 {len(docs)} 篇文档，语料库就绪：\n")
    for d in docs:
        chars = len(d["text"])
        print(f"  [{d['path']}] {d['title']}（{chars} 字符）")
