from openai import OpenAI

key = open("key").read().strip()
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "请给我今天的日期"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_today",
            "description": "获取今天的日期",
            "parameters": {"type": "object", "properties": {}},
        },
    }],
    tool_choice="required",   # 强制模型调用工具
)
msg = resp.choices[0].message
print("模型调用:", msg.tool_calls[0].function.name)
print("参数:", msg.tool_calls[0].function.arguments)