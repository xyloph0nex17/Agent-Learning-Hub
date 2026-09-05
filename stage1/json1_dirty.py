import json
from openai import OpenAI

key = open("key").read().strip()
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

resp = client.chat.completions.create(
    model="deepseek-chat",
    temperature=0,   # 低温减少随机，让输出稳定些（方便你观察"结构问题"而非"随机问题"）
    messages=[
        {"role": "user", "content": "请列出鲁迅、玛丽·居里、图灵这三位名人的信息，用 JSON 返回。"},
    ],
)

raw = resp.choices[0].message.content
print("原始输出：\n", raw)

print("\n--- 尝试 json.loads ---")
try:
    data = json.loads(raw)
    print("解析成功，得到：", data)
except json.JSONDecodeError as e:
    print("解析失败：", e)
