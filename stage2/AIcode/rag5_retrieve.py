# -*- coding: utf-8 -*-
"""
Stage 2 · A5：向量检索（余弦相似度）—— 并与 A3 关键词检索对比
目标：把用户问题也编码成向量，和语料里每个 chunk 的向量算余弦相似度，
      取最接近的 top_k 个作为检索结果；再和 BM25 的结果摆在一起对比。

为什么这样能检索？
   所有向量都在同一个"语义空间"里：query 的向量和 chunk 的向量，
   谁的方向最接近（余弦最大），谁就最可能是答案。向量检索本质是
   "在 512 维空间里找最近的邻居"。

归一化技巧：
   先把所有向量归一化成长度 1（除以模长），这时 余弦 = 点积。
   点积可以用矩阵乘法一次性算完所有 chunk，非常快：
       sims = vecs_norm @ query_norm          # 一次算出所有相似度
"""
import numpy as np
from operator import itemgetter

from rag3_bm25 import search as bm25_search     # A3 的关键词检索
from rag4_embed import embed_texts, load_cached  # A4 的向量


def vector_search(query: str, top_k: int = 3) -> list[tuple[dict, float]]:
    """向量检索入口：给一句话，返回最相关的 chunk（相似度从高到低）。"""
    chunks, vecs = load_cached()                       # 读取缓存好的语料向量

    qv = embed_texts([query])[0]                       # query 也编码成向量
    qv_n = qv / np.linalg.norm(qv)                     # 归一化 query
    vecs_n = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)  # 归一化所有 chunk
    sims = vecs_n @ qv_n                               # 余弦 = 点积（向量已归一化）

    # 排序：把 (chunk, 分数) 配成对，直接按分数降序取前 top_k
    # sorted 自带 reverse，不用再靠"取负"绕开升序；itemgetter(1) 表示按第 1 项(分数)比较
    ranked = sorted(zip(chunks, map(float, sims)), key=itemgetter(1), reverse=True)
    return ranked[:top_k]


def compare(query: str, top_k: int = 3) -> None:
    """把 关键词检索 和 向量检索 的结果并排打印，看差别。"""
    print(f"\n{'='*64}\n查询: {query!r}\n{'='*64}")

    print("\n[关键词 BM25]（A3，比字面）")
    hits = bm25_search(query, top_k)
    if not hits:
        print("  （没有命中 —— 字面上一个词都对不上）")
    for c, s in hits:
        print(f"  [{s:6.2f}] ({c['doc']}) {c['text'][:44]}...")

    print("\n[向量检索]（A5，比语义）")
    for c, s in vector_search(query, top_k):
        print(f"  [{s:.3f}] ({c['doc']}) {c['text'][:44]}...")


if __name__ == "__main__":
    print("首次运行会自动生成向量缓存，请稍候……")
    load_cached()

    # 演示 1：字面能匹配 —— 两种检索都应该行
    compare("What is an agent?")

    # 演示 2：字面几乎匹配不上、但语义相同 —— 这是向量检索的主场
    compare("How do I stop my model from making things up and force grounded answers?")

    # 演示 3：A3 时代发现的"标题虚高"问题，向量检索有没有改善？
    compare("Why chunk long documents before retrieval?")

    # 你也可以自己输一句试试：手动运行时加 --ask 才进入（避免自动化运行卡住）
    if "--ask" in __import__("sys").argv:
        print("\n" + "─" * 64)
        while True:
            q = input("\n输入一句话做检索对比（直接回车退出）: ").strip()
            if not q:
                break
            compare(q, top_k=2)
