# Retrieval-Augmented Generation (RAG)

Large language models have a knowledge cutoff, and they know nothing about your private documents. Retrieval-Augmented Generation solves this: first retrieve the fragments relevant to a question from a corpus, then feed both the question and those fragments to the model so it answers from evidence instead of from memory.

The full pipeline has two phases. The offline indexing phase splits raw documents into small chunks, embeds each chunk into a vector, and stores them in an index. The online query phase embeds the user's question, finds the most similar chunks in the index, and hands them to the model to generate an answer.

Why chunk before retrieving? Context windows are limited, so you cannot stuff an entire document into the prompt; at the same time, smaller retrieval units are more precise — the model only needs the few paragraphs most relevant to the question. Chunk size is a trade-off: too small loses context, too large drags in irrelevant noise.

The key concept is grounding: every claim in the answer can be traced back to a real chunk. Give each chunk an id and ask the model to cite those ids, or to answer only from the given fragments. This is the most practical way to reduce hallucination — content the model states at least exists somewhere in the corpus.
