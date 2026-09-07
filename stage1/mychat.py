from openai import OpenAI
from datetime import datetime
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
    }
]
REGISTRY={
    "clock":datetime.now    # 存"函数本身"（不带括号），调用时才真正执行
}
def dispatch(name:str,args:str)->str:
    func = REGISTRY[name]
    return str(func())   # 执行函数得到时间对象，转成字符串返回
    

resp = client.chat.completions.create(
        
    model="deepseek-chat",
    messages=[
        {"role":"system","content":"你可以根据用户的需求使用工具，但不是必须使用，只有用户提出相关问题时进行使用"},
        {"role":"user","content":"今天是几号"}
    ],
    tools=TOOLS,
)
print(resp.model_dump_json(indent=2))
msg = resp.choices[0].message
if msg.tool_calls :
    name=msg.tool_calls[0].function.name 
    args=msg.tool_calls[0].function.arguments 
    result = dispatch(name, args)
    print("工具执行结果:", result)
    