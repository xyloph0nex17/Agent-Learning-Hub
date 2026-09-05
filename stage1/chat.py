from openai import OpenAI

key = open("key").read().strip()
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

# 对话历史：从一条 system 消息开始（设定身份/规则）
messages = [
    {"role": "system", "content": "你是一个乐于助人的助手，回答尽量简洁。"},
]

print("开始聊天吧（输入 exit 退出）\n")

while True:
    user_input = input("你: ")
    if user_input.strip().lower() in ("exit", "quit"):
        print("再见！")
        break

    # 1. 把用户这次说的话追加进历史
    messages.append({"role": "user", "content": user_input})

    # 2. 把【完整历史】发给模型
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
    )

    # 3. 取出模型回答并打印
    reply = resp.choices[0].message.content
    print(f"\nAI: {reply}\n")

    # 4. 【关键】把模型的话也存回历史，否则下一轮它不记得
    messages.append({"role": "assistant", "content": reply})
