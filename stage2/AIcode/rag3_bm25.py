# -*- coding: utf-8 -*-
"""
Stage 2 · A3：关键词检索的底层逻辑（倒排索引 + BM25 打分）
目标：零依赖、纯本地，把"搜索引擎/检索是怎么工作的"讲清楚。

要回答"资料库里哪几块和我的问题最相关"，先解决两个问题：
  ① 怎么把一个文本拆成可比较的"词"？    —— 分词（tokenize）
  ② 怎么快速找到包含这些词的 chunk？     —— 倒排索引（inverted index）
  ③ 怎么给命中的 chunk 打分排序？        —— BM25

关于分词（纯英文语料）：
  英文文本天然用空格和标点分隔：统一小写后，按"连续字母数字"切出单词即可，
  不需要词典，也没有任何语言特化处理——这是英文分词最朴素的实现。

关于倒排索引：
  正向思路是"每个 chunk 里有哪些词"（读一遍全部文档才能查）。
  倒排索引反过来：记"每个词出现在哪些 chunk 里"，像书后面的关键词索引页。
  查的时候只需查问题里的几个词，立刻定位到候选 chunk，不用扫全库。

关于 BM25：
  朴素匹配只算"有没有命中"。BM25 考虑三件事，给命中程度打分：
    - TF  词频：这个词在这一块出现得越多越相关；
    - IDF 稀有度：烂大街的词（如"的""是"）命中一次说明不了问题，稀有词更值钱；
    - 长度归一：很长的块"容易"命中，要打折，避免长块总靠"量大"胜出。
"""
import math
import re

from rag2_chunk import get_chunks


# ---------- ① 分词：文本 -> 词列表 ----------
def tokenize(text: str) -> list[str]:
    """把一段英文文本切成词。

    小写化后，按"连续字母/数字"切出单词即可——空格和标点会自动把词隔开，
    无需词典，不做任何语言特化。这是英文分词最朴素的实现。
    """
    return re.findall(r"[a-z0-9]+", text.lower())


# ---------- ② 倒排索引 ----------
def build_index(chunks: list[dict]) -> tuple[dict, list[int]]:
    """构建倒排索引。

    返回 (inverted, doc_len)：
      inverted:  dict 词 -> {chunk下标: 在该 chunk 出现次数(tf)}
      doc_len:   list  每个 chunk 的词总数
    """
    inverted: dict[str, dict[int, int]] = {}
    doc_len = []
    for i, c in enumerate(chunks):
        toks = tokenize(c["text"])
        doc_len.append(len(toks))
        for t in toks:
            post = inverted.setdefault(t, {})   # 词 -> 一个字典
            post[i] = post.get(i, 0) + 1        # 记录"在 chunk i 又出现一次"
    return inverted, doc_len


# ---------- ③ BM25 打分 ----------
def bm25(query: str, chunks: list[dict],
         inverted: dict, doc_len: list[int],
         top_k: int = 3, k1: float = 1.5, b: float = 0.75) -> list[tuple[dict, float]]:
    """给每个 chunk 算一个相关分，返回分数最高的 top_k 个。"""
    N = len(chunks)
    avgdl = sum(doc_len) / max(1, N)          # 平均块长，用于长度归一
    scores = [0.0] * N

    for t in set(tokenize(query)):            # 对问题里的每个词
        post = inverted.get(t)
        if not post:                          # 词在语料里完全没出现 -> 跳过
            continue
        n = len(post)                         # 这个词出现在几个 chunk 里
        # IDF：词越稀有，命中越有信息量。加 1 保证结果非负、无平滑问题
        idf = math.log(1 + (N - n + 0.5) / (n + 0.5))
        for i, tf in post.items():
            dl = doc_len[i]
            # 长度归一的分母：块越长，b 会把它的 tf 压得越多
            denom = tf + k1 * (1 - b + b * dl / avgdl)
            scores[i] += idf * tf * (k1 + 1) / denom

    ranked = sorted(range(N), key=lambda i: scores[i], reverse=True)
    return [(chunks[i], scores[i]) for i in ranked if scores[i] > 0][:top_k]


# ---------- 对外接口：给后面的步骤用 ----------
_chunks_cache = None
_index_cache = None
_len_cache = None


def search(query: str, top_k: int = 3) -> list[tuple[dict, float]]:
    """关键词检索入口：给一句话，返回最相关的 chunk（分数从高到低）。"""
    global _chunks_cache, _index_cache, _len_cache
    if _chunks_cache is None:
        _chunks_cache = get_chunks()
        _index_cache, _len_cache = build_index(_chunks_cache)
    return bm25(query, _chunks_cache, _index_cache, _len_cache, top_k)


if __name__ == "__main__":
    chunks = get_chunks()
    inverted, doc_len = build_index(chunks)
    print(f"语料共 {len(chunks)} 个 chunk，倒排索引含 {len(inverted)} 个词条\n")

    for q in ["What is an agent",
              "How to prevent hallucination",
              "Why chunk documents before retrieval"]:
        print(f"\n=== 查询: {q!r} ===")
        for c, score in bm25(q, chunks, inverted, doc_len, top_k=3):
            print(f"  [{score:6.2f}] ({c['doc']}) {c['text'][:46]}...")
