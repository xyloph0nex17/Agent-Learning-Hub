# -*- coding: utf-8 -*-
"""
Stage 1 - 工具函数（实现侧）
一个"好用的工具函数"首先是：写得好、边界处理好的普通 Python 函数。
本文件先不接模型，先把函数本身写对、测对。
"""

def calculator(expression: str) -> str:
    """计算数学表达式，如 '(3+5)*2'。恒返回字符串。"""
    # 安全实现①：字符白名单 —— 只放行数字和四则运算符
    allowed = set("0123456789+-*/(). ")
    if any(c not in allowed for c in expression):
        return "错误：表达式含非法字符（只允许数字和 + - * / ( ) .）"
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"错误：无法计算（{e}）"


def search(query: str) -> str:
    """模拟联网搜索：按关键词返回几条结果文本（演示用假数据）。"""
    fake = {
        "agent": [
            "Anthropic · Building effective agents",
            "OpenAI · A practical guide to building agents",
        ],
        "python": [
            "Python 官方文档 https://docs.python.org/3/",
        ],
    }
    results = []
    for k, v in fake.items():
        if k in query.lower():
            results.extend(v)
    if not results:
        return "没有找到相关内容，试试别的关键词。"
    return "\n".join(f"- {r}" for r in results)


def read_file(path: str) -> str:
    """读取文本文件内容。安全实现②：类型白名单 + 禁止越出工作目录。"""
    import os
    allowed_ext = (".py", ".md", ".txt", ".json")
    base = os.path.abspath(os.getcwd())
    target = os.path.abspath(path)
    if not target.endswith(allowed_ext):
        return f"错误：只允许读取 {allowed_ext} 类型的文件"
    if not target.startswith(base):
        return "错误：不允许读取工作目录之外的文件"
    try:
        with open(target, encoding="utf-8") as f:
            content = f.read()
        return content[:2000] if content else "（空文件）"
    except Exception as e:
        return f"错误：{e}"


if __name__ == "__main__":
    print("=== 测试三个工具函数 ===")
    print("calculator('(3+5)*2') =", calculator("(3+5)*2"))
    print("calculator('__import__(\"os\")') =", calculator('__import__("os")'))
    print()
    print("search('agent'):\n", search("agent"))
    print()
    print("read_file 自身前 60 字:", read_file("tools1_funcs.py")[:60])
    print("read_file('../key'):", read_file("../key"))
