# Multi-Agent Coordination

Multi-agent is not "let a few agents chat with each other". It is a coordination problem. If you simply let several models talk freely in one group, you quickly get endless debate, task drift, and context bloat. The reliable pattern is a supervisor or a state graph that orchestrates the work.

Common roles are the planner, the executor, the reviewer or critic, and the router. Each sub-agent needs a clear boundary: what it owns, what its input and output schema look like, and when it is considered done. Unclear boundaries are the root cause of most multi-agent project failures.

And when should you not use multi-agent? When a single agent plus a few tools can finish the job, one agent is simpler, cheaper, and more controllable. Multi-agent only pays off when a task genuinely splits into independent subtasks, each needing different tools or a different context window.
