# -*- coding: utf-8 -*-
"""
Stage 2 · A4：embedding —— 把"文字"变成"语义向量"
目标：用本地英文模型 bge-small-en-v1.5 把语料的每个 chunk 编码成向量，并缓存到磁盘，
      供 A5 做向量检索直接加载（不用每次重复编码）。

━━━ 先讲清楚 embedding 的底层逻辑 ━━━

1) 为什么文字能变成"向量"？
   计算机没法直接比较"两句话意思像不像"。但我们希望做到：把每句话放进一个
   多维空间里的一个点，让"意思相近的句子，点的位置也相近"。
   这个"把句子映射成坐标（一串数字）"的操作，就叫 embedding（嵌入）。

2) 从 one-hot 到稠密向量（理解的关键）
   最笨的编码是 one-hot：每个词独占一个维度，词越多维度越大，且任何两个词
   都互相正交（夹角 90°，相似度恒为 0）——它完全表达不了语义。
   embedding 的做法：用一个固定长度（这里是 384）的"稠密"向量表示文本，
   向量里每个位置的数值由神经网络在【海量语料】上训练出来。训练目标就是让
   "出现在相似语境里的文本" 学到的向量更接近。

3) 为什么"语义相近 → 向量夹角小"？
   这其实不是魔法，而是训练目标本身：模型在海量句子上学会"这个词/句平时和
   谁一起出现"，于是把语义压进了向量方向。例如模型见过大量"猫"和"宠物"共现、
   "苹果(水果)"和"香蕉"共现，它们的向量就会靠拢。
   向量之间的"像不像"，常用【余弦相似度】衡量（A5 会用）：
        cos(a, b) = a·b / (|a|·|b|)     取值 [-1, 1]，越接近 1 越像
   它只关心两个向量的【方向】，不关心长度，正好适合比语义。

4) 和 A3 关键词检索的本质区别
   关键词检索比"字面"：查询和文档必须出现完全相同的词才能命中。
   embedding 检索比"语义"：查询里没有的词，只要意思接近，向量依然靠得近。
   例：查 "How to stop the model from making things up"——字面上语料里没有这句话，
   但语料里讲 "hallucination / no supporting evidence" 的那段向量和它很接近，
   向量检索就能命中；关键词检索(BM25)字面匹配不上。

5) 代价67
   向量检索不是免费的午餐：要下载模型(约 95MB)、把每块都编码一遍（离线一次），
   在线查询时也要把 query 编码一次；而且向量检索的解释性差（说不清"为什么是
   这块"）。好的工程常用 hybrid：关键词 + 向量一起，互相兜底。
"""
import json
import os

import numpy as np
from fastembed import TextEmbedding

from rag2_chunk import get_chunks

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
CHUNKS_CACHE = os.path.join(CACHE_DIR, "chunks.json")
VECS_CACHE = os.path.join(CACHE_DIR, "vectors.npy")
MODEL_NAME = "BAAI/bge-small-en-v1.5"   # 384 维，英文语义，仅 ~67MB

_model = None


def get_model() -> TextEmbedding:
    """单例加载模型：只加载一次，避免重复占内存。"""
    global _model
    if _model is None:
        print(f"加载 embedding 模型 {MODEL_NAME} ...")
        _model = TextEmbedding(MODEL_NAME)   # 首次会从 HF 下载，之后走本地缓存
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """把一批文本编码成向量矩阵，形状 (N, 384)。"""
    vecs = list(get_model().embed(texts))    # fastembed: 逐条产出 numpy 向量
    return np.vstack(vecs)


def build_and_save(chunks: list[dict] | None = None) -> tuple[list[dict], np.ndarray]:
    """把全部 chunk 编码成向量，保存到 cache/。返回 (chunks, vecs)。"""
    chunks = chunks if chunks is not None else get_chunks()
    os.makedirs(CACHE_DIR, exist_ok=True)
    vecs = embed_texts([c["text"] for c in chunks])
    with open(CHUNKS_CACHE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)     
    np.save(VECS_CACHE, vecs)                      
    return chunks, vecs


def load_cached() -> tuple[list[dict], np.ndarray]:
    """加载缓存；没有缓存就先构建。A5 直接用它。"""
    if os.path.exists(CHUNKS_CACHE) and os.path.exists(VECS_CACHE):
        with open(CHUNKS_CACHE, encoding="utf-8") as f:
            chunks = json.load(f)
        vecs = np.load(VECS_CACHE)
        return chunks, vecs
    return build_and_save()


def cos(a: np.ndarray, b: np.ndarray) -> float:
    """余弦相似度：a·b / (|a||b|)，越接近 1 表示越相似。"""
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


if __name__ == "__main__":
    # ① 先真正把语料向量化并缓存（后面 rag5 会用）
    chunks, vecs = build_and_save()

    # ② 亲手"看"一下 embedding：用 4 句话算两两余弦
    print("\n--- 语义相似度演示（看数值感受 embedding）---")
    demo = [
        "Large language models have a knowledge cutoff",             # 0
        "The model only knows facts from before its training date",  # 1
        "Retrieval-augmented generation can fix outdated knowledge", # 2
        "It is sunny today, a good day for a walk",                  # 3
    ]
    dv = embed_texts(demo)
    print(f"\nBase sentence: \"{demo[0]}\"")
    for i in (1, 2, 3):
        sim = cos(dv[0], dv[i])
        print(f"  vs \"{demo[i]}\"  cosine = {sim:.3f}  "
              f"{'← semantically close' if sim > 0.5 else '← unrelated'}")
    print("\n看：意思接近的句子(0↔1, 0↔2)余弦大，无关句(0↔3)余弦小——这就是语义空间。")
