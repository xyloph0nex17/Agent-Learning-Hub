from rag_embed import load_cache
from rag_embed import embed_text
from rag_chunker import Chunk
import numpy as np
from operator import itemgetter


def vector_search(query: str, top_k: int = 3) -> list[tuple[Chunk, float]]:
    chunks, vecs = load_cache()
    qv = embed_text([query])[0]
    qv_n = qv / np.linalg.norm(qv)
    vecs_n = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    sims = vecs_n @ qv_n
    ranked = sorted(zip(chunks, map(float, sims)), key=itemgetter(1), reverse=True)
    return ranked[:top_k]
if __name__ == "__main__":
    query = input()
    for chunk, score in vector_search(query):
        print(f"[{score:.3f}] ({chunk["doc"]}) {chunk["text"][:60]}...")
#What is an agent?