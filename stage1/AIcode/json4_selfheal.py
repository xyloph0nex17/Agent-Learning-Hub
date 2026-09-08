import json
from openai import OpenAI
from pydantic import BaseModel, ValidationError

key = open("key").read().strip()
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

# --- 契约 ---
class Person(BaseModel):
    name: str
    birth_year: int
    nationality: str
    fields: list[str]
    achievements: list[str]

class People(BaseModel):
    people: list[Person]

# --- 对话历史（注意：这次它会被越滚越长，因为要保存模型每轮的输出）---
messages = [
    {"role": "user", "content": "请列出鲁迅、玛丽·居里、图灵三位名人的信息，用 json 返回。"},
]

MAX_ATTEMPTS = 3   # 防止死循环烧钱

for attempt in range(1, MAX_ATTEMPTS + 1):
    print(f"\n===== 第 {attempt} 次尝试 =====")

    resp = client.chat.completions.create(
        model="deepseek-chat",
        temperature=0,
        response_format={"type": "json_object"},
        messages=messages,
    )
    raw = resp.choices[0].message.content

    # 记录模型这次的回答（之后要让模型"看见自己说过什么"）
    messages.append({"role": "assistant", "content": raw})

    # 第一关：语法层
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print("❌ 语法层失败:", e)
        error_report = f"你的输出不是合法 JSON：{e}"
    else:
        # 第二关：契约层
        try:
            parsed = People.model_validate(data)
            print("✅ 校验通过！结果如下：")
            print(json.dumps(parsed.model_dump(), ensure_ascii=False, indent=2))
            break   # 通过就退出循环
        except ValidationError as e:
            print("❌ 契约层失败，报错如下：")
            print(e)
            error_report = str(e)

    # 关键一步：把【精确报错】喂回给模型，请它自己修正
    messages.append({
        "role": "user",
        "content": f"上面的输出没有通过校验，错误报告如下：\n{error_report}\n"
                   "请根据错误报告修正，重新输出完整且符合要求的 json（不要任何解释，只要 json）。",
    })
else:
    print(f"\n超过最大尝试次数 {MAX_ATTEMPTS} 次，放弃。")
