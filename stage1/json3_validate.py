import json
from openai import OpenAI
from pydantic import BaseModel, ValidationError

key = open("key").read().strip()
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

# 1. 先让模型输出（沿用 JSON mode，提示词写得很"宽泛"，不透露我们的契约细节）
resp = client.chat.completions.create(
    model="deepseek-chat",
    temperature=0,
    response_format={"type": "json_object"},
    messages=[
        {"role": "user", "content": "请列出鲁迅、玛丽·居里、图灵三位名人的信息，用 json 返回。"},
    ],
)

data = json.loads(resp.choices[0].message.content)
print("模型输出的 JSON：")
print(json.dumps(data, ensure_ascii=False, indent=2))

# 2. 定义【我们的契约】：我们要的字段、类型、结构
class Person(BaseModel):
    name: str
    birth_year: int          # 我们要整数年份，不接受 "1881-09-25" 这种字符串
    nationality: str
    fields: list[str]        # 我们要数组，不接受 "物理学、化学" 这种字符串
    achievements: list[str]

class People(BaseModel):
    people: list[Person]

# 3. 用契约去撞模型输出：不合约就立刻、响亮地失败
print("\n--- 用 pydantic 校验模型输出 ---")
try:
    parsed = People.model_validate(data)
    print("校验通过 ✅ 输出完全符合我们的契约")
except ValidationError as e:
    print("校验失败 ❌ 模型输出不符合契约，报错如下：")
    print(e)
