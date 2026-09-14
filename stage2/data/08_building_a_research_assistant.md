# Building a Research Assistant

A research assistant is the typical RAG application: the user gives a topic, and the agent searches for material, filters what is relevant, summarizes it, and produces an answer with citations. What separates it from a toy RAG demo is orchestration.

A working assistant needs at least four parts: a corpus (local documents or fetched web pages); a retrieval module that turns the topic into search queries and finds the most relevant fragments; a summarizer that combines several fragments into one coherent report; and a citation mechanism so that every claim in the report is tagged with its source. Search queries often need several iterations — when the first round of results is weak, you refine the queries based on what was already found.

Engineering must also handle practical failures: retrieval may return empty results, so you broaden the keywords or switch sources; near-duplicate fragments must be deduplicated so one sentence is not repeated three times in the summary; fetched pages may fail or come back empty and need a retry or a skip. Finally the report must let a reader verify every claim — give the document title and source path, and in the web case the original URL. An answer without verifiable sources is just an AI-generated summary, not research.
