# -*- coding: utf-8 -*-
"""
Stage 2 · A2：切块（chunking）
目标：把每篇文档切成"适合检索的小块"。

为什么要切块？
    1. 模型输入长度有限 —— 不能把整本文档塞进 prompt；
    2. 检索单元越小越精确 —— 模型只需要"和问题最相关的几段话"；
    3. 太大会混入无关内容，太小会丢失上下文。所以切块大小是个权衡。

怎么切（本步策略，两层）：
    先按空行把全文切成段落；
    段落如果仍然太长（> WINDOW 字符），再切成更小的块；
    英文文本会在单词边界处断开，避免把一个单词从中间切断。

每一块会带一个 id，格式：文档名#序号。后面 RAG 回答要"引用编号"就靠它。
"""
from rag1_load import load_docs

WINDOW = 200    # 单块字符上限（英文平均每词约 5-7 字符）


def split_paragraphs(text: str) -> list[str]:
    """按空行切段落，去掉空白段落。"""
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def split_long(text: str) -> list[str]:
    """把超过 WINDOW 的段落切小，并在英文单词边界处断开（避免切断单词）。"""
    if len(text) <= WINDOW:
        return [text]
    pieces = []
    start = 0
    while start < len(text):
        end = min(start + WINDOW, len(text))
        if end < len(text):                        # 没到末尾时，尽量断在空格处
            space = text.rfind(" ", start + 1, end)   # 窗口内最后一个空格
            if space > start:
                end = space
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        start = end + 1                            # +1 跳过作为断点的那个空格
    return pieces


def chunk_doc(doc: dict) -> list[dict]:
    """把一篇文档切成若干 chunk，每个 chunk 带唯一 id。"""
    chunks = []
    seq = 0
    for para in split_paragraphs(doc["text"]):
        for piece in split_long(para):
            chunks.append({
                "id": f"{doc['path']}#{seq}",   # 唯一编号，如 "04_xxx.md#2"
                "doc": doc["path"],
                "title": doc["title"],
                "text": piece,
            })
            seq += 1
    return chunks


def get_chunks(docs: list[dict] | None = None) -> list[dict]:
    """返回语料库全部 chunk（供后续步骤 import 复用）。"""
    docs = docs if docs is not None else load_docs()
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_doc(doc))
    return all_chunks


if __name__ == "__main__":
    chunks = get_chunks()
    print(f"共切出 {len(chunks)} 个 chunk\n")

    # 统计：每篇文档切成几块
    from collections import Counter
    per_doc = Counter(c["doc"] for c in chunks)
    for doc, n in per_doc.items():
        print(f"  {doc}: {n} 块")

    # 打印前 3 个 chunk 看看切得对不对
    print("\n--- 预览前 3 个 chunk ---")
    for c in chunks[:3]:
        print(f"\n[{c['id']}]（{len(c['text'])} 字符）")
        print(c["text"][:80].replace("\n", " ") + "...")
