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
所有回答使用中文，简洁明了，仅针对用户的问题。
"""
key=open(KEY_FILE).read().strip()
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

def answer(query:str):
    conv=[
        {"role":"system","content":SYSTEM},
        {"role":"user","content":query},
    ]
    #print(resp.model_dump_json(indent=2))
    #sys.exit(0)
    for i in range(5):
        resp=client.chat.completions.create(
                model=MODEL,
                messages=conv,# type: ignore
                tools=TOOLS,# type: ignore
            )
        msg=resp.choices[0].message 
        if resp.choices[0].finish_reason=="stop":
            return msg.content
        if resp.choices[0].finish_reason=="length":
            return "上下文过长"
        if resp.choices[0].finish_reason=="content_filter":
            return "无法满足要求"
        conv.append(msg) #type:ignore
        for tc in msg.tool_calls:# type: ignore
            args = json.loads(tc.function.arguments or "{}")#type:ignore

            tc_result=dispatch(tc.function.name,args)# type: ignore
            #print(f"[debug] {tc.function.name}({tc.function.arguments}) -> {tc_result}")# type: ignore
            conv.append({"role": "tool", "tool_call_id": tc.id, "content": tc_result})
        # print(resp.model_dump_json(indent=2))
        
    return "问题解决步骤有些复杂，超出最大步数限制，换个问题试试呢"

if __name__ == "__main__":
    while True:
        query=input("用户：")
        if(query.lower().strip()=="exit"):
            print("再见")
            break 
        print("AI:",answer(query))
# 根据本地文件，告诉我agent是什么