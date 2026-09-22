from tools_defs import search_local,read_file,sql_query,fetch_webpage,run_python
TOOLS=[
    {
        "type":"function",
        "function":{
            "type":"object",
            "name":"search_local",
            "description":"返回本地文库中与文本相关性最高的三段文字,采用embed实现,仅支持英文文本",
            "parameters":{
                "type":"object",
                "properties":{
                    "query":{"type":"string","description":"一段英文文本"},
                },
                "required":["query"],
            }
        }
    },
    {
        "type":"function",
        "function":{
            "type":"object",
            "name":"read_file",
            "description":"读取制定工作区内的某一文件的内容",
            "parameters":{
                "type":"object",
                "properties":{
                    "path":{"type":"string","description":"文件名的相对路径"},
                },
                "required":["path"],
            }
        }
    },
    {
        "type":"function",
        "function":{
            "type":"object",
            "name":"sql_query",
            "description":"查询数据库内对相关信息",
            "parameters":{
                "type":"object",
                "properties":{
                    "QUERY":{"type":"string","description":"数据库查询语句,仅允许SELECT命令"},
                },
                "required":["QUERY"],
            }
        }
    },
    {
        "type":"function",
        "function":{
            "type":"object",
            "name":"fetch_webpage",
            "description":"抓取网页文字内容",
            "parameters":{
                "type":"object",
                "properties":{
                    "url":{"type":"string","description":"需要抓取网页信息的网址"},
                },
                "required":["url"],
            }
        }
    },
    {
        "type":"function",
        "function":{
            "type":"object",
            "name":"run_python",
            "description":"执行一段python代码",
            "parameters":{
                "type":"object",
                "properties":{
                    "code":{"type":"string","description":"需要执行的代码"},
                },
                "required":["code"],
            }
        }
    },
]

REGISTRY={
    "search_local":search_local,
    "read_file":read_file,
    "sql_query":sql_query,
    "fetch_webpage":fetch_webpage,
    "run_python":run_python,
}
def dispatch(func:str,args:dict)->str:
    if func not in REGISTRY:
        return f"该函数未定义"
    try:
        return REGISTRY[func](**args)
    except Exception as e:
        return f"error:{e}"
    