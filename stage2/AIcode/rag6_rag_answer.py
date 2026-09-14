# -*- coding: utf-8 -*-
"""
Stage 2 · B1：把 RAG 拼成闭环 —— 检索片段 + LLM 组装"有依据"的回答
目标：用户提问 → 检索出最相关的 top_k 个 chunk → 给每个 chunk 编个号 →
      把"问题 + 编号片段"一起交给 DeepSeek → 模型只基于片段作答并引用编号。

━━━ 这一步在学什么（grounding / citations）━━━

1) 什么是 grounding（接地）？
   不带检索的 LLM 靠"记忆"回答，会一本正经地胡说（幻觉）。
   RAG 的做法是：把检索到的片段作为"证据"塞进 prompt，要求模型
   【只根据这些片段说话】。模型说的每一句话，都能在片段里找到出处。

2) 为什么片段要编号 [1][2][3]...？
   编号 = 给模型一个"可引用"的锚点。prompt 里告诉模型"回答每条结论
   后面用 [n] 标明来自哪段"，这样：
     - 用户能看到答案的出处，能自己回去验证；
     - 模型被迫"点对点"对着片段写，不容易东拉西扯。
   这就是 README 里 "answer with citations" 的落地。

3) 怎么防"幻觉引用"？
   prompt 里明确三条硬规则：
     - 只能引用真实存在的编号（没有 [5]，就不准写 [5]）；
     - 片段里没有答案时，必须直说 "sources 里没有"，而不是编；
     - 禁止使用片段之外的外部知识。
   规则本身不能 100% 约束模型，但配合"片段里有足够上下文"就能大幅
   降低幻觉。D 小节还会教"程序侧校验引用编号是否真实存在"（更强的一层）。

4) 为什么调 deepseek 而检索那段是自己写的？
   检索（BM25/向量）是确定性代码，我们完全可控、可解释；
   生成（把片段组织成自然语言回答）才需要 LLM。RAG 的精髓就是
   "用可控的检索兜住不可控的生成"。
"""
import os

import numpy as np
from openai import OpenAI

from rag3_bm25 import search as bm25_search      # A3：关键词检索
from rag4_embed import embed_texts, load_cached  # A4：向量检索

# key 在仓库根目录；用 __file__ 向上两级定位，不依赖当前工作目录
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "key")

SYSTEM = (
    "You are a research assistant that answers ONLY from the source snippets "
    "provided by the user.\n"
    "Rules:\n"
    "1. Base every claim only on the given snippets. Never use outside knowledge.\n"
    "2. After each claim, cite the snippet number(s) in brackets, e.g. [1] or [2][4].\n"
    "3. Only cite numbers that actually exist in the snippets.\n"
    "4. If the snippets do not contain enough information to answer, reply exactly: "
    "\"The provided sources do not contain this information.\"\n"
    "5. Answer in the same language as the question, and be concise."
)


def retrieve(question: str, mode: str = "vector", top_k: int = 4) -> list[dict]:
    """检索出 top_k 个最相关的 chunk。

    mode="vector"：A4/A5 的向量检索（比语义）；
    mode="bm25"  ：A3 的关键词检索（比字面）。
    返回 [(chunk, 分数), ...]，调用方按需编号。
    """
    if mode == "bm25":
        return bm25_search(question, top_k)

    chunks, vecs = load_cached()
    qv = embed_texts([question])[0]
    qv_n = qv / np.linalg.norm(qv)
    vecs_n = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    sims = vecs_n @ qv_n                       # 余弦 = 点积（已归一化）
    order = np.argsort(-sims)
    return [(chunks[i], float(sims[i])) for i in order[:top_k]]


def build_prompt(question: str, hits: list[tuple[dict, float]]) -> str:
    """把检索结果转成带编号的片段文本，拼进给模型的 prompt。"""
    parts = []
    for i, (chunk, score) in enumerate(hits, start=1):
        parts.append(f"[{i}] (source: {chunk['doc']})\n{chunk['text']}")
    snippets = "\n\n".join(parts)
    return f"Question: {question}\n\nSource snippets:\n{snippets}"


def answer(question: str, mode: str = "vector", top_k: int = 4) -> tuple[str, list[tuple[dict, float]]]:
    """完整 RAG：检索 → 编号 → 交给模型 → 返回 (模型回答, 检索到的片段)。"""
    # 1) 检索 + 编号
    hits = retrieve(question, mode, top_k)
    prompt = build_prompt(question, hits)

    # 2) 让模型基于片段作答
    try:
        with open(KEY_FILE) as f:
            key = f.read().strip()
    except OSError:
        return f"(找不到 key 文件: {KEY_FILE})", hits

    client = OpenAI(api_key=key, base_url="https://api.deepseek.com", timeout=60)
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,          # 低温度：让它老实照片段说，少发挥
    )
    return resp.choices[0].message.content or "(空回复)", hits


def show(question: str, mode: str = "vector", top_k: int = 4) -> None:
    """打印一次完整 RAG 过程：检索片段 + 最终带引用回答。"""
    print("\n" + "=" * 70)
    print(f"Q: {question}")
    print("=" * 70)

    text, hits = answer(question, mode, top_k)

    print(f"\n--- 检索到的 {len(hits)} 个片段（这就是给模型的'证据'）---")
    for i, (chunk, score) in enumerate(hits, start=1):
        print(f"  [{i}] ({chunk['doc']}) {chunk['text'][:90].replace(chr(10),' ')}...")

    print("\n--- 模型回答（应带 [n] 引用）---")
    print(text)


if __name__ == "__main__":
    # 演示：资料里能答的
    show("What is an agent?")
    show("Why do we need to chunk documents before retrieval?")
    show("How can I reduce hallucination and make my agent give grounded answers?")

    # 演示：资料里没有的 —— 模型必须承认"没有"，而不是编
    show("What is the capital of France?", top_k=2)
