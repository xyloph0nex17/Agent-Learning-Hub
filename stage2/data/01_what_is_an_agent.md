# What Is an Agent

An agent is a program that perceives its environment, makes decisions, and takes actions to accomplish a goal. The biggest difference from a regular script: a script's execution path is hard-coded by the programmer, while an agent decides at each step what to do next.

A useful rule of thumb: if a task is predictable and the flow is fixed, a plain script is enough — adding an agent only introduces uncertainty. Agents shine in tasks that need multiple rounds of search, verification, and iteration, where every step is uncertain.

An LLM alone is not an agent; it is a reasoning engine. An agent = LLM + tools + a control loop (deciding when to think, when to act, when to stop) + memory. A large part of an agent's real capability comes from the surrounding engineering: tool protocols, permissions, state, and logs.
