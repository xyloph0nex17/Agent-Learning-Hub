from openai import OpenAI
from datetime import datetime
import json
key=open("/home/xyx/Agent-Learning-Hub/key").read().strip()
client=OpenAI(api_key=key,base_url="https://api.deepseek.com")

TOOLS=[
    {
        "type":"function",
        "function":{
            "name":"clock",
            "description":"获取当前日期和时间，仅当用户询问时间相关或需要时间信息时调用",
            "parameters":{
                "type":"object",
                "properties":{},
            },
        },
    },
    {
        "type":"function",
        "function":{
            "name":"read_file",
            "description":"读取当前目录下的文本文件"
        },
        "parameters":{
            "type":"object",
            "properties":{
                "path":{"type":"string","description":"文件路径的相对路径"},
            },
            "required":["path"],
        }
    }
]
def read_file(path:str)->str:
    import os
    allow_suf = (".py",".md",".txt",".json")
    allow_pre = os.path.abspath(os.getcwd())
    target = os.path.abspath(path)
    if not target.endswith(allow_suf):
        return f"错误，只允许读取{allow_suf}类型的文件"
    if not target.startswith(allow_pre):
        return "错误，超出工作区域"
    try:
        with open(target,encoding="utf-8") as f:
            content=f.read()
        return content[:5000] if content else "(空文件)"
    except Exception as e:
        return f"错误:{e}"
    
REGISTRY={
    "clock":datetime.now,
    "read_file":read_file,
}
def dispatch(name:str,args:str)->str:
    func = REGISTRY[name]
    args_dict = json.loads(args) if args else {}   # "{}" 字符串 → {} 字典
    try:
        return str(func(**args_dict))
    except TypeError as e:
        # 参数缺失/不对 → 把错误返回给模型，让它补全参数重试
        return f"调用工具 {name} 失败：{e}。请检查并补充必要参数。"
    



def solve(user_text:str):
    conv = [
        {"role":"system","content":"你可以根据用户的需求使用工具，但不是必须使用，只有用户 提出相关问题时进行使用"},
    ]
    conv.append({"role":"user","content":user_text})
    for step in range(5):
        
        resp=client.chat.completions.create(
            model="deepseek-chat",
            messages=conv,
            tools=TOOLS
        )
        msg=resp.choices[0].message
        if msg.tool_calls != None:
            conv.append(msg)
            for fc in msg.tool_calls:
                result=dispatch(fc.function.name,fc.function.arguments)
                conv.append({"role":"tool","tool_call_id":fc.id,"content":result})
        else:
            print(msg.content)
            return
    print("超出最大步数限制")

if __name__ == "__main__":
    while(True):
        user_text=input("你: ")
        if user_text.strip().lower() in ("exit","quit"):
            print("再见！")
            break
        solve(user_text)
# mychat.py第12行是什么
# 现在是几点