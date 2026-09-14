# Memory: Context, Session, and Long-Term

An agent's "memory" is not a single thing. There are at least four distinct layers, and mixing them up is how context balloons and models get dumber over a long conversation.

The first layer is short-term context: the messages the model can currently see inside its context window. It is bounded, and when it overflows you must truncate or compress. The second layer is conversation memory: what happened during one session, usually handled by keeping the message history well managed — a rolling window, or summaries of older turns. When the session ends, this memory is usually gone.

The third layer is long-term memory: important facts that survive across sessions, such as user preferences or project conventions. In practice you must actively decide what to store, persist those facts to something durable (a JSON file, SQLite, or a vector store), and load them back at the start of the next session. The fourth layer is the external knowledge base: the content RAG retrieves. Strictly speaking that is reference material rather than memory, because it does not accumulate over time; it is fetched on demand from documents.

The golden rule: not everything should be remembered. The context window cannot hold all of history, and stuffing long-term memory with trivia pollutes the model's judgment. Distinguishing transient working state from facts worth keeping forever is the core of designing a memory system.
