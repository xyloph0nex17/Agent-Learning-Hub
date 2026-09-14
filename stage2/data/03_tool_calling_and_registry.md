# Tool Calling and the Registry

To let a model call tools, engineering keeps three things: a tool menu (the schema shown to the model), a registry (mapping names to real functions), and a dispatcher (turning a model's request into a real function call).

The TOOLS menu is JSON that describes which tools exist and what parameters each one takes. It only influences the model's decision to call a tool; it executes nothing. The real function code sits behind a wall — this wall is the safety boundary. The model can only "request" a call; whether it runs, and whether the arguments are valid, is decided by the host program.

The REGISTRY is essentially a dictionary: the key is the name the model sees, and the value is the real Python function. A dispatcher receives a name plus a parameter dict, looks up the function, and runs it. Arguments arrive from the model as JSON strings, so they must be parsed into a dict and expanded into keyword arguments.

Tool functions should be written as well-behaved ordinary functions: allowlist the permitted characters, restrict accessible paths, and catch exceptions so they return a readable error string instead of raising. The reader of a tool result is the model, so give it a chance to retry with different arguments or switch to another tool.
