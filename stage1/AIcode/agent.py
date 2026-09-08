from openai import OpenAI

key = open("key").read().strip() 

client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

resp = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "user", "content": "鲁迅的原名是什么？"},
    ],
)
print(resp.choices[0].message.content)