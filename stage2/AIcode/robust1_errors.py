# -*- coding: utf-8 -*-
"""
Stage 2 · D1：把"工具出错"当成常态来设计
（对应 README Stage2 todo 4 的前半：工具失败、空结果、重复调用）

━━━ 为什么这一步重要 ━━━
  真实 agent 跑起来，出错才是常态：网络会抖、查询会落空、模型会原地打转
  （反复用同样的参数调同一个工具）。如果不在【宿主程序】这层兜住，
  要么程序崩，要么模型被错误信息带偏，要么无限循环烧钱。

  prompt 里写"请小心"没用；可靠性的关键在【代码】里加护栏。

━━━ 本课的 4 道护栏 ━━━
  ① 工具失败  -> 重试(退避) + 最终变成可读错误字符串（fetch_webpage 已内置）
  ② 空结果    -> 把"空"翻译成明确提示，引导模型换查询/换工具，而不是喂空串
  ③ 重复调用  -> 记住 (工具名+参数)，同样的请求再来就直接拦下并提示换策略
  ④ 参数错误  -> dispatch 兜住 TypeError/异常，让模型自己补参数重试

  把这些护栏包在 dispatch 外面，就得到一个"抗错 loop"。下面先做确定性演示
  （不调模型，直接看护栏行为），再接进 agent loop 跑一个真实任务。
"""
import json
import os
import time

from openai import OpenAI

from tools2_registry import TOOLS, dispatch

KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "key")
MODEL = "deepseek-chat"
MAX_STEPS = 6
SYSTEM = (
    "You are a careful tool-using assistant. If a tool returns no result or an "
    "error, ADAPT: try different arguments, broaden the query, or switch tools. "
    "Never call the same tool with identical arguments twice. "
    "If the data truly is not available, say so."
)


def make_client() -> OpenAI:
    with open(KEY_FILE) as f:
        key = f.read().strip()
    return OpenAI(api_key=key, base_url="https://api.deepseek.com", timeout=90)


# ── ① 失败重试（通用包装器）────────────────────────────────
def call_with_retry(func, args: dict, retries: int = 2, delay: float = 1.0) -> str:
    """执行 func(**args)，失败退避重试，最终仍失败则返回可读错误字符串。"""
    last = None
    for attempt in range(retries + 1):
        try:
            return str(func(**args))
        except Exception as e:
            last = e
            if attempt < retries:
                time.sleep(delay)
    return f"Error: '{func.__name__}' failed after {retries + 1} attempts ({last})."


# ── ② 空结果识别 ───────────────────────────────────────────
def is_empty(result: str) -> bool:
    """判断工具结果是不是"没拿到有用东西"。"""
    r = (result or "").strip().lower()
    return (not r) or any(k in r for k in
                          ("no rows", "no output", "empty page",
                           "no relevant content", "empty file"))


# ── ③④ 护栏版分发器 ────────────────────────────────────────
def safe_dispatch(name: str, args: dict, seen: set) -> str:
    """在 dispatch 外面加护栏：防重复调用、识别空结果、兜异常。"""
    key = (name, json.dumps(args, sort_keys=True, ensure_ascii=False))
    if key in seen:                                   # ③ 重复调用
        return (f"Error: you already called {name} with the same arguments. "
                f"Try different arguments or another tool.")
    seen.add(key)

    try:
        result = dispatch(name, args)                 # ④ 参数/执行异常在 dispatch 内兜住
    except Exception as e:
        return f"Error: {name} crashed: {e}"

    if is_empty(result):                              # ② 空结果 -> 明确提示
        return (f"No usable result from {name}. "
                f"Consider broadening the query or using another tool.")
    return result


# ── 把护栏接进 agent loop ──────────────────────────────────
def run_guarded(task: str, show_trace: bool = True) -> str:
    client = make_client()
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": task}]
    seen: set = set()

    for step in range(1, MAX_STEPS + 1):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS)
        msg = resp.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except Exception:
                    args = {}
                result = safe_dispatch(name, args, seen)
                if show_trace:
                    print(f"  [step {step}] {name}({args})")
                    print(f"            -> {result[:95].replace(chr(10), ' ')}...")
                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": result})
            continue

        return msg.content or "(empty reply)"

    return "(hit max steps without a final answer)"


if __name__ == "__main__":
    print("=== 确定性演示：直接看护栏行为（这里不调模型）===\n")

    print("① 重复调用：同一个工具、同样的参数，第二次被拦")
    seen = set()
    print("  1st:", safe_dispatch("run_python", {"code": "print(1)"}, seen))
    print("  2nd:", safe_dispatch("run_python", {"code": "print(1)"}, seen), "\n")

    print("② 空结果：查一个不存在的内容")
    print("  ->", safe_dispatch(
        "sql_query", {"sql": "SELECT text FROM chunks WHERE text LIKE '%zzzzz%'"}, set()), "\n")

    print("③ 工具失败：抓一个不存在的域名（会重试后返回错误字符串）")
    print("  ->", safe_dispatch(
        "fetch_webpage", {"url": "https://no-such-domain-xyz123.example"}, set())[:110], "\n")

    print("④ 参数错误：给错参数名")
    print("  ->", safe_dispatch("read_file", {"pathx": "oops.md"}, set()), "\n")

    print("=== 接入 agent loop：让它对付一个会落空的任务 ===")
    task = ("Find any chunk whose text contains the word 'zzzzz' using SQL, "
            "and search the knowledge base for anything about it. "
            "If there is nothing, just say the data is not available.")
    print("TASK:", task)
    print("TRACE:")
    print("\nANSWER:", run_guarded(task))
