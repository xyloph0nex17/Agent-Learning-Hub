# -*- coding: utf-8 -*-
"""
小步 C：完整 agent loop —— 模型自由选工具，程序真执行，结果喂回，直到最终回答。
复用 tools2_registry.py 里写好的菜单(TOOLS)和分发器(dispatch)。
"""
import json
from openai import OpenAI
from tools2_registry import TOOLS, dispatch   # 拿现成的用，不用重写

key = open("key").read().strip()
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

# 对话历史（会越滚越长：模型说的话、工具结果都会被存进来）
messages = [
    {"role": "user", "content": "请依次完成三件事："
                                "1) 用 search 搜索 agent 相关资料；"
                                "2) 用 calculator 计算 (12+8)*3；"
                                "3) 用 read_file 读 tools1_funcs.py 的第 1 行。"},
]

MAX_STEPS = 5   # 防止模型一直调工具停不下来

for step in range(1, MAX_STEPS + 1):
    print(f"\n===== 第 {step} 轮 =====")

    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=TOOLS,          # 每次都要带上菜单
    )
    msg = resp.choices[0].message

    # 情况 1：模型说"我要调工具"
    if msg.tool_calls:
        messages.append(msg)      # 把模型的话（含 tool_calls）存进历史
        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)   # 参数是 JSON 字符串，转成字典
            print(f"模型要调: {name}({args})")

            result = dispatch(name, args)   # 程序真正执行工具
            print(f"  执行结果: {result[:60]}...")

            # 把执行结果喂回给模型，tool_call_id 用来对上号
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        continue   # 继续下一轮：模型该基于结果组织回答了

    # 情况 2：模型不再调工具，直接给最终回答
    print(f"\n[最终回答]\n{msg.content}")
    break
else:
    print("\n超过最大步数，强制结束。")
