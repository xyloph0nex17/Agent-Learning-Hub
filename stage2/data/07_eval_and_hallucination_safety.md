# Evaluation and Hallucination Safety

Demos are not enough. Whether an agent is reliable is measured with a fixed test set. When you evaluate, record task success, the failure reason, the number of tool calls, cost, and latency. Then use traces to locate which layer failed — a bad prompt, a tool returning an empty result, retrieval missing the relevant content, or the model simply misunderstanding the request.

Hallucination is content that sounds plausible but has no supporting evidence. The most practical defense is to force grounding: let the model answer only from the retrieved fragments, and make every conclusion map to a specific chunk id or source. When the fact the model needs is not in the sources, it must say "the sources do not contain this" instead of inventing an answer.

Risky actions need a human approval gate: sending email, deleting files, making payments, or publishing content. You should also be aware of prompt injection, data exfiltration, and tool abuse. Text shown to the model may come from untrusted external content, so never treat every model utterance as an instruction to run a high-risk action.
