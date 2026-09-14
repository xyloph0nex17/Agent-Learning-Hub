# -*- coding: utf-8 -*-
"""
Stage 2 · C2：长期记忆（跨会话持久化）

━━━ 和 C1 的区别 ━━━
  C1 的"会话记忆"在会话结束时就没了（历史随进程消失）。
  C2 的"长期记忆"要【跨会话】活下来——所以必须写进磁盘。

  关键认识：模型自己没有内存。所谓"记得"，永远是我们把记忆读出来、
  塞进新会话的上下文。长期记忆 = 一个持久化文件 + 每次会话开头把它注入。

━━━ 两个重要设计问题 ━━━
  1) 记什么？   不是所有话都该记。原则：只存"跨会话仍然有用的事实"，
                例如用户偏好、正在做的项目、长期约定。寒暄、一次性问题不记。
                本课让【模型自己抽取】，体现"主动选择"而不是无脑全存。
                存太多会污染后续会话——记忆是有成本的。
  2) 存哪里？   本课用最简单的 JSON 文件（cache/memory.json）。
                真实系统会用 SQLite、向量库，甚至专门的记忆服务（如 mem0）。

━━━ 怎么运行 ━━━
  python AIcode/mem2_longterm.py a     # 会话 A：聊几句，抽取并保存长期记忆
  python AIcode/mem2_longterm.py b     # 会话 B：全新会话，加载记忆 -> 看它记不记得
  python AIcode/mem2_longterm.py       # 默认：先 A 后 B（同进程演示）
  分开跑 a / b 更能说明问题：两个进程不共享任何内存，靠的就是那个 JSON 文件。
"""
import json
import os
import sys

from openai import OpenAI

KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "key")
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
MEM_FILE = os.path.join(CACHE_DIR, "memory.json")
MODEL = "deepseek-chat"
SYSTEM = "You are a helpful assistant."


def make_client() -> OpenAI:
    with open(KEY_FILE) as f:
        key = f.read().strip()
    return OpenAI(api_key=key, base_url="https://api.deepseek.com", timeout=60)


# ── 长期记忆的读写：就是一个 JSON 文件 ─────────────────────────
def load_memory() -> list[str]:
    if not os.path.exists(MEM_FILE):
        return []
    with open(MEM_FILE, encoding="utf-8") as f:
        return json.load(f).get("facts", [])


def save_memory(facts: list[str]) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        json.dump({"facts": facts}, f, ensure_ascii=False, indent=2)


def extract_facts(client: OpenAI, dialogue: str) -> list[str]:
    """让模型从一段对话里挑出"值得长期记住"的事实。"""
    prompt = (
        "Extract LONG-TERM memory from the conversation below.\n"
        "Return ONLY a JSON array of short strings: durable facts and preferences "
        "about the user that matter across future sessions (name, project, "
        "preferences). Ignore small talk and one-off questions.\n\n"
        f"Conversation:\n{dialogue}"
    )
    resp = client.chat.completions.create(
        model=MODEL, temperature=0,
        messages=[{"role": "user", "content": prompt}])
    text = resp.choices[0].message.content or "[]"
    # 模型有时会包 ```json ... ```，这里截取第一个 [ 到最后一个 ]
    start, end = text.find("["), text.rfind("]")
    try:
        return json.loads(text[start:end + 1]) if start != -1 else []
    except Exception:
        return []


def chat(client: OpenAI, messages: list[dict]) -> str:
    resp = client.chat.completions.create(
        model=MODEL, messages=messages, temperature=0)
    return resp.choices[0].message.content or "(empty)"


# ── 会话 A：聊天 -> 抽取 -> 保存 ──────────────────────────────
def session_a(client: OpenAI) -> None:
    print("=== 会话 A：和助手聊几句 ===")
    turns = [
        ("user", "Hi! I'm Ada. I'm building a RAG application in Python."),
        ("assistant", "Nice to meet you, Ada! How can I help with your RAG app?"),
        ("user", "I prefer concise answers, and I work on this project alone."),
        ("assistant", "Got it — concise answers from here on."),
    ]
    for role, text in turns:
        print(f"  {role}: {text}")

    dialogue = "\n".join(f"{r}: {t}" for r, t in turns)
    facts = extract_facts(client, dialogue)

    # 合并去重后保存（真实系统还会做冲突检测/更新，这里从简）
    merged = sorted(set(load_memory()) | set(facts))
    save_memory(merged)
    print(f"\n  模型抽取到 {len(facts)} 条值得长期记住的事实，已写入 {MEM_FILE}:")
    for fact in merged:
        print(f"    - {fact}")


# ── 会话 B：全新会话，只靠加载的记忆 ──────────────────────────
def session_b(client: OpenAI) -> None:
    print("=== 会话 B：完全新的会话（不共享任何历史）===")
    facts = load_memory()
    print(f"  启动时从磁盘加载了 {len(facts)} 条长期记忆：")
    for fact in facts:
        print(f"    - {fact}")

    # 把记忆注入 system —— 这就是"让它记得"的全部魔法
    memory_block = "\n".join(f"- {f}" for f in facts)
    system = (SYSTEM + "\n\nKnown facts about the user (from long-term memory):\n"
              + memory_block) if facts else SYSTEM

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "What do you remember about me?"},
    ]
    print("\n  问: What do you remember about me?")
    print("  答:", chat(client, messages))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    client = make_client()
    if mode in ("a", "both"):
        session_a(client)
    if mode in ("b", "both"):
        print()
        session_b(client)
    if mode == "both":
        print("\n注：会话 B 用的是全新的 messages（没有任何历史），它能答出来，")
        print("    唯一的原因就是磁盘上的 memory.json 被读出来注入了上下文。")
