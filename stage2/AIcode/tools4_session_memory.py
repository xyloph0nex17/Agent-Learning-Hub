# -*- coding: utf-8 -*-
"""Stage 2 · C1：给 tool agent 加入会话记忆。

本例把完整对话历史保存在当前 Python 进程的 conversation 列表中。
同一进程内的后续提问会带上之前的用户消息、工具调用、工具结果和助手回答。
程序退出后列表消失，因此这还不是跨会话的长期记忆。

运行方式（在项目根目录执行）：
    python stage2/AIcode/tools4_session_memory.py
"""
import json
import os

from openai import OpenAI

from tools2_registry import TOOLS, dispatch

KEY_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "key"
)
MODEL = "deepseek-chat"
MAX_STEPS = 5

SYSTEM = (
    "你是一个帮助用户解决问题的助手。可以根据需要调用工具。\n"
    "涉及本地资源或外部网页的问题，必须根据工具结果回答；"
    "没有得到依据时要如实说明，不得编造。\n"
    "工具失败或没有结果时，可以调整查询或更换工具；仍然没有依据时，"
    "要说明无法确认。所有回答使用中文，简洁明了。"
)

# 会话记忆：system prompt 只放一次，之后每轮复用这份历史。
conversation: list[dict] = [
    {"role": "system", "content": SYSTEM},
]


def make_client() -> OpenAI:
    with open(KEY_FILE, encoding="utf-8") as key_file:
        key = key_file.read().strip()
    if not key:
        raise ValueError(f"API key 文件为空：{KEY_FILE}")
    return OpenAI(api_key=key, base_url="https://api.deepseek.com", timeout=90)


def answer(client: OpenAI, query: str) -> str:
    """回答一个问题；成功完成的整轮对话会存入 conversation。"""
    # 先在本轮副本中工作。API 失败或步数耗尽时，不保存不完整的一轮。
    turn = conversation.copy()
    turn.append({"role": "user", "content": query})

    for _step in range(1, MAX_STEPS + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=turn,  # type: ignore[arg-type]
                tools=TOOLS,  # type: ignore[arg-type]
            )
        except Exception as e:
            return f"模型调用失败：{type(e).__name__}: {e}"

        choice = response.choices[0]
        message = choice.message

        # 工具调用消息和对应结果都要保存在本轮上下文中，供模型下一步读取。
        if message.tool_calls:
            turn.append(message)  # type: ignore[arg-type]

            for tool_call in message.tool_calls:
                try:
                    args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError as e:
                    result = f"工具参数不是合法 JSON：{e}"
                else:
                    result = dispatch(tool_call.function.name, args)

                turn.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                })
            continue

        # 最终回答也必须加入历史，否则下一轮模型看不到自己刚才说过什么。
        if message.content:
            turn.append({"role": "assistant", "content": message.content})
            conversation[:] = turn
            return message.content

        return f"模型没有返回有效内容，结束原因：{choice.finish_reason}"

    return "工具调用超过最大步数，本轮没有保存到会话记忆中。"


if __name__ == "__main__":
    try:
        client = make_client()
    except (OSError, ValueError) as e:
        raise SystemExit(f"无法创建模型客户端：{e}") from e

    print("输入 exit 退出；退出后本例的会话记忆会清空。")
    while True:
        query = input("用户：").strip()
        if query.lower() == "exit":
            print("再见")
            break
        if not query:
            continue
        print("AI：", answer(client, query))
