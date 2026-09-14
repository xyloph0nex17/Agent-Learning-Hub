# The Agent Loop

Almost every agent runs on the same loop: observe, think, act, observe. The model sees the request, decides to answer directly or to call a tool, then the tool result is fed back to it, and the loop repeats until a final answer is produced.

The loop sounds simple, but production requires three safeguards. First, a maximum step limit: a model may keep requesting tools forever, so you need an upper bound to prevent infinite loops and runaway cost. Second, message history management: every assistant message, every tool call, and every tool result must be appended to the history, otherwise the model loses track of what it just did. Third, error handling: the API may time out and tools may throw exceptions, so every layer needs a catch so the loop never crashes.

A common misconception is that the agent loop is the model acting alone. In reality it is a protocol among the human, the model, and the tools: the model emits a tool_call request, the host program actually executes the tool, then returns the result as a tool message. Permission and control always stay with the host program, never with the model.
