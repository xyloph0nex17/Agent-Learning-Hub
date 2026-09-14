# -*- coding: utf-8 -*-
"""
Stage 2 · D2：防"幻觉引用"——程序侧强校验，而不只是在 prompt 里请求
（对应 README Stage2 todo 4 的后半 + todo 5 的"给出来源/证据"）

━━━ 问题：光靠 prompt 约束不住 ━━━
  B1 里我们在 prompt 写了"只准引用真实存在的编号"。但这只是【软约束】：
  模型仍可能写出 [5]（当只给了 4 段时），甚至引用一个根本不存在的小节。
  一旦引用是假的，答案看着有出处、其实无法验证——比"没有引用"更危险。

━━━ 解法：宿主程序做硬校验 ━━━
  给模型一段编号 [1..k]，回复后我们用代码：
    1) 用正则抽出回答里所有 [n]；
    2) 检查每个 n 是否落在合法范围 [1..k]；
    3) 有越界引用 -> 判定失败 -> 把错误反馈回去，让它重答（最多重试 N 次）。
  这是"生成 -> 校验 -> 打回重试"的闭环，可靠性靠代码而不是靠祈祷。

  更严格的校验还可以：要求回答问题必须至少有一个引用、检查引用段落是否真的
  支持那句话（相关性/蕴含判断）。本课实现最核心的"编号存在性"校验。
"""
import os
import re

from openai import OpenAI

# 复用 B1 已经写好的检索与 prompt 组装，避免重复造轮子
from rag6_rag_answer import KEY_FILE, SYSTEM, build_prompt, retrieve

MODEL = "deepseek-chat"


def make_client() -> OpenAI:
    with open(KEY_FILE) as f:
        key = f.read().strip()
    return OpenAI(api_key=key, base_url="https://api.deepseek.com", timeout=60)


def validate_citations(text: str, valid_ids: set[int]) -> tuple[set[int], list[int]]:
    """抽出回答里的 [n]，返回 (引用到的编号集合, 越界的编号列表)。"""
    cited = {int(m) for m in re.findall(r"\[(\d+)\]", text)}
    invalid = sorted(c for c in cited if c not in valid_ids)
    return cited, invalid


def generate(client: OpenAI, question: str, hits: list, feedback: str | None = None) -> str:
    prompt = build_prompt(question, hits)
    if feedback:
        prompt += f"\n\nIMPORTANT CORRECTION: {feedback}"
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": prompt}],
        temperature=0.2)
    return resp.choices[0].message.content or "(empty)"


def answer_checked(client: OpenAI, question: str, top_k: int = 4,
                   max_retry: int = 2) -> None:
    """检索 -> 生成 -> 校验引用 -> 不合格就打回重试，打印全过程。"""
    hits = retrieve(question, "vector", top_k)
    valid_ids = set(range(1, len(hits) + 1))
    print(f"\nQ: {question}")
    print(f"有效引用编号: {sorted(valid_ids)}")

    text, cited, invalid = "", set(), []
    for attempt in range(1, max_retry + 1):
        text = generate(client, question, hits, feedback=(
            f"Your previous answer cited {invalid}, but those ids do not exist. "
            f"Use ONLY ids {sorted(valid_ids)}, or say the sources do not contain it."
        ) if invalid else None)
        cited, invalid = validate_citations(text, valid_ids)
        status = "OK" if not invalid else f"INVALID {invalid} -> retry"
        print(f"  attempt {attempt}: cited={sorted(cited) or '[]'}  {status}")
        if not invalid:
            break

    print("  final answer:", text.replace("\n", " ")[:200], "...")


if __name__ == "__main__":
    print("=== ① 确定性演示：校验器本身能抓到假引用 ===")
    fake_answer = "Chunking matters for precision [1]. See also the appendix [7]."
    cited, invalid = validate_citations(fake_answer, {1, 2, 3, 4})
    print(f"  回答: {fake_answer}")
    print(f"  引用到: {sorted(cited)}   越界(不存在): {invalid}  <- 被抓住\n")

    client = make_client()

    print("=== ② 真实演示：正常问题（引用都合法）===")
    answer_checked(client, "What is an agent?", top_k=4)

    print("\n=== ③ 真实演示：资料里没有的问题（应拒绝，而不是编造引用）===")
    answer_checked(client, "According to the knowledge base, who invented the BM25 "
                           "ranking function and in which year?", top_k=4)
