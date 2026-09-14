# -*- coding: utf-8 -*-
"""
Stage 2 · 工具 3/3：接上 agent loop，让模型自己决定用哪个工具
这是"把能力接成工具"的最后一环：不再是我们指定调用哪个函数，
而是把 5 个工具的菜单交给模型，它根据用户请求自己选。

和 Stage 1 的 tools4/tools3 loop 结构一样：
  模型要调工具 -> 我们 dispatch 真正执行 -> 把结果作为 tool 消息喂回 -> 直到最终回答。
区别只是这次工具是"真实能力"（本地检索、SQL、文件、网页、代码）。

观察重点（跑的时候看 trace）：
  - 同一个模型面对不同请求，会自动切换不同工具；
  - 工具返回错误时，模型往往能自己"换个参数/换个工具"再试。
"""
import json
import os

from openai import OpenAI

from tools2_registry import TOOLS, dispatch     # 复用第 2 步的三件套

KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "key")
MODEL = "deepseek-chat"
MAX_STEPS = 6

SYSTEM = (
    "You are a helpful assistant with tools. Decide by yourself which tool to call.\n"
    "You can: search the local knowledge base, read files under data/, run read-only "
    "SQL on the local `chunks` table, fetch public web pages, and run short Python code.\n"
    "Ground factual answers in tool results. If a tool returns an error, adapt: "
    "try different arguments or another tool."
)


def run(task: str, show_trace: bool = True) -> str:
    """跑一个任务，返回最终回答；show_trace 时打印每一步工具调用。"""
    with open(KEY_FILE) as f:
        key = f.read().strip()
    client = OpenAI(api_key=key, base_url="https://api.deepseek.com", timeout=90)

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": task},
    ]

    for step in range(1, MAX_STEPS + 1):
        try:
            resp = client.chat.completions.create(
                model=MODEL, messages=messages, tools=TOOLS)
        except Exception as e:
            return f"(model call failed: {e})"

        msg = resp.choices[0].message

        if msg.tool_calls:                       # 模型要调工具
            messages.append(msg)
            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except Exception:
                    args = {}
                result = dispatch(name, args)     # 宿主程序真正执行
                if show_trace:
                    print(f"  [step {step}] {name}({args})")
                    print(f"            -> {result[:90].replace(chr(10), ' ')}...")
                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": result})
            continue

        return msg.content or "(empty reply)"     # 模型给出最终回答

    return "(hit max steps without a final answer)"


if __name__ == "__main__":
    tasks = [
        # 每个任务"暗示"了不同工具，看模型是否能选对
        "Use the local knowledge base to explain why chunking matters before retrieval.",
        "How many chunks are stored in the database? Answer using a SQL query.",
        "Compute 2**20 + 1 with code and give me the exact number.",
        "Read 05_memory_layers.md and list the memory layers it describes.",
        "Fetch https://www.python.org and summarize what the page is about.",
    ]
    for t in tasks:
        print("=" * 72)
        print("TASK:", t)
        print("TRACE:")
        answer = run(t)
        print("\nANSWER:", answer)
        print()
