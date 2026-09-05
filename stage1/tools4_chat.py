# -*- coding: utf-8 -*-
"""
小步 D：可交互、带错误处理的最小 agent。
功能：像聊天一样一直用；它会自己决定要不要调工具。
新增：超时、API失败兜底、工具执行失败兜底、每问最多5轮。
"""
import json
from openai import OpenAI
from tools2_registry import TOOLS, dispatch

key = open("key").read().strip()
client = OpenAI(api_key=key, base_url="https://api.deepseek.com", timeout=30)  # 超时30秒

def answer(user_text: str) -> str:
    """给一句用户的话，返回 agent 的最终回答。"""
    messages = [
        {"role": "system", "content": "你可以调用工具来完成用户请求；不需要工具时直接回答。"},
        {"role": "user", "content": user_text},
    ]

    for step in range(1, 6):   # 每个问题最多 5 轮，防止死循环
        # 兜底①：请求模型可能失败（网络、超时、限流）
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat", messages=messages, tools=TOOLS)
        except Exception as e:
            return f"(调用模型失败) {e}"

        msg = resp.choices[0].message

        # 模型要调工具
        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                    result = dispatch(tc.function.name, args)
                except Exception as e:   # 兜底②：工具自己出错也不能让程序崩
                    result = f"工具执行出错: {e}"
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            continue

        # 模型直接回答
        return msg.content or "(空回复)"

    return "(超过轮数上限，未得到最终回答)"


if __name__ == "__main__":
    print("和一个会自己调用工具的小 agent 聊天吧（输入 exit 退出）\n")
    while True:
        user_text = input("你: ")
        if user_text.strip().lower() in ("exit", "quit"):
            print("再见！")
            break
        print("\nAI:", answer(user_text), "\n")
