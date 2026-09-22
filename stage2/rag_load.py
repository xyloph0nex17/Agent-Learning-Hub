import os
import glob
import re
from typing import TypedDict

DIR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"data")

class Doc(TypedDict):
    title:str
    text:str
    path:str

def load_docs(dir_path:str=DIR_PATH)->list[Doc]:
    docs:list[Doc]=[]
    for data_file in sorted(glob.glob(os.path.join(dir_path,"*.md"))):
        with open(data_file,encoding="utf-8") as f:
            text = f.read()
        tmp=re.search(r"^#\s+(.+)$",text,re.M)
        title=tmp.group(1).strip() if tmp else os.path.basename(data_file)
        docs.append({
            "title":title,
            "text":text,
            "path":os.path.basename(data_file)
        })
    return docs
if __name__ == "__main__":
    docs=load_docs()
    print(f"共加载{len(docs)}篇文章")
    for d in docs:
        char = len(d["text"])
        print(f"语料库 {d["title"]} {d["path"]} 加载成功{char}字符")
    