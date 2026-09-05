# -*- coding: utf-8 -*-
"""
小步 B：把真实函数"登记"给模型，并让程序能自动找到并执行。
三样东西：菜单(TOOLS)、注册表(REGISTRY)、分发器(dispatch)
"""

# 第 1 步：把上一步写好的真实函数拿过来用
from tools1_funcs import calculator, search, read_file

# 第 2 步：菜单 TOOLS —— 这是给【模型】看的，告诉它有哪些工具可用
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式，例如 '(3+5)*2'",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "要计算的表达式"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "搜索资料，参数是关键词",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取当前目录下的文本文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"}
                },
                "required": ["path"],
            },
        },
    },
]

# 第 3 步：注册表 REGISTRY —— 一个简单的"名字对应到函数"的字典
# 字典 = { "键" : "值" }，这里键是模型看到的名字，值是真正的函数
REGISTRY = {
    "calculator": calculator,
    "search": search,
    "read_file": read_file,
}

# 第 4 步：分发器 dispatch —— 给它名字和参数，它去注册表里找出函数并执行
def dispatch(name: str, args: dict) -> str:
    func = REGISTRY[name]   # 查字典：REGISTRY["calculator"] 得到 calculator 函数
    return func(**args)     # **args 把 {"expression":"..."} 展开成 expression="..."

# 第 5 步：测试（先不接模型，假装是模型发来的调用请求）
if __name__ == "__main__":
    fake_calls = [
        {"name": "calculator", "args": {"expression": "(3+5)*2"}},
        {"name": "search", "args": {"query": "agent"}},
        {"name": "read_file", "args": {"path": "tools1_funcs.py"}},
    ]
    for c in fake_calls:
        print(f"调用 {c['name']} ->", dispatch(c["name"], c["args"]))
