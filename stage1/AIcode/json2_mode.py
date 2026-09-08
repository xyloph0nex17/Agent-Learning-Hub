import json
from openai import OpenAI

key = open("key").read().strip()
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

resp = client.chat.completions.create(
    model="deepseek-chat",
    temperature=0,
    response_format={"type": "json_object"},   # ← 台阶 2 的主角：JSON mode
    messages=[
        {"role": "user", "content": "请列出鲁迅、玛丽·居里、图灵这三位名人的信息，"
                                    "用 json 格式返回（不要多余文字，不要 markdown 代码块）。"},
    ],
)

raw = resp.choices[0].message.content
print("原始输出：\n", raw)

print("\n--- json.loads ---")
data = json.loads(raw)   # JSON mode 下预期稳定成功
print("解析成功 ✅")

# 取出最外层列表（键名是模型起的，先动态取第一个）
people = data[list(data.keys())[0]]

print("\n--- 逐条看字段（三条的键集合一致吗？） ---")
for i, p in enumerate(people, 1):
    print(f"第{i}条:", sorted(p.keys()))
