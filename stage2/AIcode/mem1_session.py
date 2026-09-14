# -*- coding: utf-8 -*-
"""
Stage 2 · C1：短期上下文 vs 会话记忆

━━━ 先把两个概念分清楚 ━━━

① 短期上下文（context window）
   就是"这一次请求里模型能看到的全部消息"。它是一个【有上限的窗口】：
   你发多少 token，模型就看多少；超了就装不下。它本身不记得任何东西——
   模型每次回答都是"从零读一遍你给的这些消息"。

② 会话记忆（conversation memory）
   是【我们（宿主程序）跨轮维护并管理的那份历史】。模型没有内存，所谓"记得"，
   全靠我们把之前说过的话重新塞进下一次请求。所以"记忆"是一个工程问题：
   历史留多少？太长怎么办？

━━━ 对话一长为什么会失忆？两种原因 ━━━

  a) 装不下：历史超过 context window，早期消息被截断丢弃（或请求直接报错）。
  b) 留不下：为了控制成本/长度，我们主动截断历史（滚动窗口），早期的信息就没了。
  另外，历史越长越贵、越慢，也越容易让模型被无关内容干扰。

━━━ 本课演示的 4 种策略 ━━━

  1) 无记忆：每次只发 system + 当前这句话              -> 完全不知道之前说过什么
  2) 全量历史：把之前每一句都塞回去                     -> 记得住，但历史无限增长
  3) 滚动窗口：只保留最近 K 轮（这里 K=1）              -> 省 token，但早期信息丢失
  4) 摘要压缩：把旧对话压成一段摘要 + 保留最近原文      -> 既省 token 又留住关键事实

  生产系统常见做法是 3)+4) 混合：近期保留原文，久远的总结成摘要。
"""
import os

from openai import OpenAI

KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "key")
MODEL = "deepseek-chat"
SYSTEM = ("You are a helpful assistant. If the answer is not present in the "
          "conversation so far, say you don't know.")


def make_client() -> OpenAI:
    with open(KEY_FILE) as f:
        key = f.read().strip()
    return OpenAI(api_key=key, base_url="https://api.deepseek.com", timeout=60)


def ask(client: OpenAI, messages: list[dict]) -> str:
    """把一份历史发给模型，返回回复。"""
    resp = client.chat.completions.create(
        model=MODEL, messages=messages, temperature=0)
    return resp.choices[0].message.content or "(empty)"


def hist_chars(messages: list[dict]) -> int:
    """粗略衡量这份历史有多长（字符数，近似 token 成本）。"""
    return sum(len(m["content"]) for m in messages)


if __name__ == "__main__":
    client = make_client()

    # 上一轮对话（第 1 轮）已经发生过，内容如下：
    t1_user = "My name is Ada and I'm building a RAG application."
    t1_asst = "Nice to meet you, Ada! Happy to help with your RAG application."
    # 现在用户问第 2 轮，考验"记不记得第 1 轮"：
    t2_user = "What is my name, and what am I building?"
    # 摘要策略里，用这句话代表"把旧对话压缩后的结果"：
    summary = ("Summary of the earlier conversation: the user's name is Ada, "
               "and they are building a RAG application.")

    # ── 策略 1 & 3：无记忆 / 滚动窗口(只留最近 1 轮) ──────────
    # 两者发给模型的其实一模一样（历史里没有第 1 轮），所以结果相同
    no_mem = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": t2_user},
    ]

    # ── 策略 2：全量历史 ──────────────────────────────────────
    full = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": t1_user},
        {"role": "assistant", "content": t1_asst},
        {"role": "user", "content": t2_user},
    ]

    # ── 策略 4：摘要压缩（旧对话 -> 一句摘要；近期保留原文）──
    summarized = [
        {"role": "system", "content": SYSTEM},
        {"role": "system", "content": summary},
        {"role": "user", "content": t2_user},
    ]

    print("第 1 轮已经聊过：user 说「我叫 Ada，在做 RAG 应用」")
    print(f"现在第 2 轮问：「{t2_user}」\n")

    r_nomem = ask(client, no_mem)
    r_full = ask(client, full)
    r_sum = ask(client, summarized)

    print("=" * 72)
    print("策略 1  无记忆 / 策略 3  滚动窗口(只留最近1轮)")
    print(f"  历史长度: {hist_chars(no_mem)} 字符")
    print(f"  回答: {r_nomem}")
    print()
    print("策略 2  全量历史")
    print(f"  历史长度: {hist_chars(full)} 字符")
    print(f"  回答: {r_full}")
    print()
    print("策略 4  摘要压缩")
    print(f"  历史长度: {hist_chars(summarized)} 字符")
    print(f"  回答: {r_sum}")
    print("=" * 72)
    print("\n观察：全量和摘要都能答出 'Ada / RAG'；无记忆和朴素窗口答不出——")
    print("      同样的模型，差别只在'我们把多少历史塞回了它的上下文窗口'。")
