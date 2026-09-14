import os
from openai import OpenAI
from chunker import Chunk 
from retrieve import vector_search
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "key")
MODEL = "deepseek-chat"
SYSTEM = (
    "你是一名帮助用户搜寻信息的助手，下面有几条规则你必须遵守：\n"
    "1. 你回答的信息都必须来源于用户提供的片段，不能用片段之外的知识补充。\n"
    "2. 每条结论后面用 [n] 标明来自哪条片段，并说明该片段的来源文章。\n"
    "3. 只能引用片段里真实存在的编号，不能虚构编号或来源。\n"
    "4. 假如片段里找不到和问题相关的信息，直接说明没有相关信息，不能编造。\n"
    "5. 资料是英文的：用户用中文提问时，请先理解英文片段，再用中文回答。\n"
    "6. 用与用户提问相同的语言回答，保持简洁。"
)
def build_context(hits: list[tuple[Chunk, float]]) -> str:
    blocks = []
    for i, (chunk, _score) in enumerate(hits, start=1):
        blocks.append(f"[{i}] (来源: {chunk['doc']})\n{chunk['text']}")
    return "\n\n".join(blocks)


def query(q_text: str, top_k: int = 3) -> str:
    hits = vector_search(q_text, top_k) 
    if not hits:
        return "没有检索到相关资料。"

    prompt = f"问题：{q_text}\n\n片段（共 {len(hits)} 条）：\n{build_context(hits)}"
    key = open("/home/xyx/Agent-Learning-Hub/key").read().strip()
    client = OpenAI(api_key=key, base_url="https://api.deepseek.com", timeout=60)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content or "(空回复)"
if __name__ == "__main__":
    q_text = input("你想查询的信息:")
    print(query(q_text))