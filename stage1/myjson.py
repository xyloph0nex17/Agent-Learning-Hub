from openai import OpenAI

key = open("/home/xyx/Agent-Learning-Hub/key").read().strip()
client = OpenAI(api_key=key,base_url="https://api.deepseek.com")
resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role":"user","content":"请告诉我现在的时间,用json格式输出。"},
    ],
    response_format={"type":"json_object"},
)
print(resp.model_dump_json(indent=2))