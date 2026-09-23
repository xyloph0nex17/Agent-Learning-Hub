from typing import TypedDict
from rag_load import Doc, load_docs
WINDOW=200

class Chunk(TypedDict):
    id:str
    doc:str
    title:str
    text:str

def split_paragraph(text:str)->list[str]:
    result=[]
    for p in text.split("\n\n"):
        if p.strip():
            result.append(p.strip())
    return result
def split_long(text:str)->list[str]:
    st=0
    if len(text)<=WINDOW:
        return [text.strip()]
    result=[]
    while st<len(text):
        ed=text.rfind(" ",st,st+WINDOW) if st+WINDOW<len(text) else len(text)
        if ed==-1:
            ed=st+WINDOW
        piece=text[st:ed].strip()
        if piece:
            result.append(piece)
        st=ed+1
    return result
def split_doc(doc:Doc)->list[Chunk]:
    cnt=0
    chunks:list[Chunk]=[]
    for para in split_paragraph(doc["text"]):
        for piece in split_long(para):
            chunks.append({
                "id": f"{doc["path"]}#{cnt}", 
                "doc": doc["path"],
                "title": doc["title"],
                "text": piece,
            })
            cnt+=1
    return chunks
            
def get_chunks(docs:list[Doc]|None=None)->list[Chunk]:
    docs = docs if docs is not None else load_docs()
    result=[]
    for doc in docs:
        result.extend(split_doc(doc))
    return result
if __name__ == "__main__":
    res=get_chunks()
    print(res[:10])
        
        
        
    
