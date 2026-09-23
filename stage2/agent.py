from openai import OpenAI
import os
from tools_regestry import dispatch,TOOLS
import sys
import json
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "key")
MODEL = "deepseek-chat"
SYSTEM="""
你是一个帮助用户解决问题的助手。
你可以调用工具，也可以不调用；当用户未明确要求时，由你自己判断是否需要调用工具。
涉及本地资源、外部网页的问题，需调用工具后根据其结果进行回答；若未拿到结果，只能回答无法确认，不得编造或根据记忆进行回答。
工具返回错误或无结果时，应调整参数或更换工具重试；仍无法获得依据时，如实说明。
工具结果以以下前缀标记状态：
- OK: 表示工具成功，后面的内容是结果；只根据这些内容回答。
- EMPTY: 表示工具成功但没有找到结果；不要据此推断事实，可尝试改写查询或换工具。
- ERROR: 表示工具执行失败；根据错误内容决定是否调整参数或换工具。重试仍失败时，如实说明。
所有回答使用中文，简洁明了，仅针对用户的问题。
"""
key=open(KEY_FILE).read().strip()
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
h_conv=[
    {"role":"system","content":SYSTEM},
]
def drop_conv():
    global conv_num
    while conv_num>5:
        h_conv.pop(1)
        while h_conv[1]["role"]!="user":
            h_conv.pop(1)
        conv_num-=1    
conv_num=0
def answer(query:str):

    drop_conv()
    t_conv=[]
    global conv_num

    t_conv.append({"role": "user", "content": query})    
    for i in range(5):
        try:
            resp=client.chat.completions.create(
                    model=MODEL,
                    messages=h_conv+t_conv,# type: ignore
                    tools=TOOLS,# type: ignore
                )
        except Exception as e:
            return f"模型调用失败,错误原因{e}"
        msg=resp.choices[0].message 
        if msg.tool_calls:
            t_conv.append(msg.model_dump(exclude_none=True))
            for tc in msg.tool_calls:# type: ignore
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError as e:
                    tc_result = f"ERROR: 工具参数不是合法 JSON:{e}，请重新生成参数。"
                else:
                    tc_result = dispatch(tc.function.name, args)
                t_conv.append({"role": "tool", "tool_call_id": tc.id, "content": tc_result})
            continue
        if msg.content:
            conv_num+=1
            t_conv.append({"role": "assistant", "content": msg.content})
            h_conv.extend(t_conv)
            return msg.content
        # print(resp.model_dump_json(indent=2))
        return f"模型没有返回有效内容，结束原因：{resp.choices[0].finish_reason}"
    
    return "问题解决步骤有些复杂，超出最大步数限制，换个问题试试呢"

if __name__ == "__main__":
    while True:
        
        query=input("用户：")
        if(query.lower().strip()=="exit"):
            print("再见")
            break 
        print("AI:",answer(query))
# 根据本地文件，告诉我agent是什么