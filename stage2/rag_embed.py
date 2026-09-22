import os
from fastembed import TextEmbedding
import numpy as np
from typing import TypedDict
from rag_chunker import Chunk
from rag_chunker import get_chunks
import json
CACHE_DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)),"cache")
CHUNK_CACHE=os.path.join(CACHE_DIR,"chunk.json")
VECS_CACHE=os.path.join(CACHE_DIR,"vecs.npy")
MODEL_NAME = "BAAI/bge-small-en-v1.5"

_model = None
def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model=TextEmbedding(MODEL_NAME)
    return _model

def embed_text(text:list[str])->np.ndarray:
    vecs=list(get_model().embed(text))
    return np.vstack(vecs)

def build_cache(chunks:list[Chunk]|None=None)->tuple[list[Chunk],np.ndarray]:
    chunks=chunks if chunks is not None else get_chunks()
    os.makedirs(CACHE_DIR,exist_ok=True)
    vecs=embed_text([piece["text"] for piece in chunks])
    with open(CHUNK_CACHE,"w",encoding="utf-8") as f:
        json.dump(chunks,f,ensure_ascii=False)
    np.save(VECS_CACHE,vecs)
    return chunks,vecs

def load_cache()->tuple[list[Chunk],np.ndarray]:
    if os.path.exists(CHUNK_CACHE) and os.path.exists(VECS_CACHE):
        with open(CHUNK_CACHE,encoding="utf-8") as f:
            chunks=json.load(f)
        vecs=np.load(VECS_CACHE)
        return chunks,vecs
    return build_cache()

def cos(a:np.ndarray,b:np.ndarray)->float:
    return float(a@b/(np.linalg.norm(a)*np.linalg.norm(b)))