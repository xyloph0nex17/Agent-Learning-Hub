# -*- coding: utf-8 -*-
"""
Stage 2 · 工具 2/3：把 5 个真实函数"登记"给模型
三件套（和 Stage 1 的 tools2_registry.py 一模一样，只是这次面对 5 个真实工具）：

  1) TOOLS     —— 给【模型】看的菜单：JSON schema，说明有哪些工具、每个参数长什么样。
                  它只影响"模型决定调用哪个"，本身不执行任何代码。
  2) REGISTRY  —— 给【程序】看的注册表：名字 -> 真正的 Python 函数。
  3) dispatch  —— 分发器：收到 (工具名, 参数字典) 就查表执行，并把结果/错误变成字符串。

注意描述（description）用英文写：这份菜单的读者是模型，而我们的 demo 是英文语料，
工具描述也保持英文，模型对"什么时候该用哪个工具"的判断会更准。
"""
from tools1_defs import (fetch_webpage, read_file, run_python, search_local,
                         sql_query)

# ── 1) 菜单：给模型看的 ────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_local",
            "description": "Search the local knowledge base for snippets relevant "
                           "to a question. Use this for concept questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file under the data/ directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string",
                             "description": "Path relative to data/, e.g. '01_what_is_an_agent.md'"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sql_query",
            "description": "Run a read-only SQL SELECT query on the local knowledge "
                           "base table `chunks(id, doc, title, text)`.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "A SELECT statement"}
                },
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_webpage",
            "description": "Fetch a public web page and return its plain text. "
                           "Use this for information not in the local knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "An http(s) URL"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Execute a short Python snippet in a subprocess (10s timeout) "
                           "and return its output. Use this for calculations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to run"}
                },
                "required": ["code"],
            },
        },
    },
]

# ── 2) 注册表：名字 -> 真实函数 ────────────────────────────────
REGISTRY = {
    "search_local": search_local,
    "read_file": read_file,
    "sql_query": sql_query,
    "fetch_webpage": fetch_webpage,
    "run_python": run_python,
}


# ── 3) 分发器：查表 + 执行 + 兜底 ──────────────────────────────
def dispatch(name: str, args: dict) -> str:
    """给工具名和参数字典，找到并执行函数；任何异常都变成可读字符串返回。"""
    func = REGISTRY.get(name)
    if func is None:
        return f"Error: unknown tool '{name}'."
    try:
        return str(func(**args))
    except TypeError as e:
        # 参数缺失/名字不对 —— 把错误还给模型，让它补全参数重试
        return f"Tool '{name}' called with wrong arguments: {e}"
    except Exception as e:
        return f"Tool '{name}' failed: {e}"


if __name__ == "__main__":
    # 不接模型，先假装是模型发来的调用请求（name + 参数字典）
    fake_calls = [
        ("search_local", {"query": "why chunk documents"}),
        ("sql_query", {"sql": "SELECT COUNT(*) || ' chunks' FROM chunks"}),
        ("run_python", {"code": "print(sum(range(1, 11)))"}),
        ("read_file", {"path": "../key"}),               # 越界，应被拒绝
        ("sql_query", {"sql": "DROP TABLE chunks"}),      # 非 SELECT，应被拒绝
        ("fly_to_moon", {}),                              # 不存在的工具，应报错
    ]
    for name, args in fake_calls:
        print(f"调用 {name}({args})")
        print("  -> " + dispatch(name, args)[:160].replace("\n", "\n     "))
        print()
