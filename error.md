# Stage 2 问题与优化清单

> 使用方法：严格按编号逐项修改；完成并验证后，把 `[ ]` 改成 `[x]`。  
> 范围说明：本清单检查的是 `stage2/AIcode/` 之外的个人练习代码；`AIcode/` 仅作为参考。

## 推荐修改顺序

`P0-1 → P0-2 → P0-3 → P1-1 → P1-2 → P1-3 → P1-4 → P1-5 → P2 → P3`

先让程序可运行，再补可靠性与引用校验，最后优化检索效果和代码风格。每次只改一项并单独测试，便于定位问题。

## P0：当前会阻止程序运行的问题

### [x] P0-1 修复空的 `except` 代码块

- 文件：`stage2/tools_agent.py`
- 位置：解析 `tc.function.arguments` 的 `except JSONDecodeError:` 后面。
- 现状：`except` 下面没有缩进代码，会直接产生 `IndentationError`，文件无法运行。
- 修改目标：解析失败时给 `args` 一个明确处理结果，不能继续使用未赋值的 `args`。
- 推荐思路：将“参数 JSON 非法”的说明作为对应的 tool message 返回给模型，让模型重新生成参数；不要直接让整个程序退出。
- 验收：`python -m py_compile stage2/tools_agent.py` 无报错。

### [x] P0-2 正确导入 `JSONDecodeError`

- 文件：`stage2/tools_agent.py`
- 现状：代码写了 `except JSONDecodeError`，但只导入了 `json`，没有直接导入这个名字。
- 两种正确写法任选一种：
  - 使用 `except json.JSONDecodeError:`；
  - 或增加 `from json import JSONDecodeError`。
- 验收：构造非法 JSON 时能够进入异常分支，不出现 `NameError`。

### [x] P0-3 避免解析失败后继续访问未定义的 `args`

- 文件：`stage2/tools_agent.py`
- 现状：如果 `json.loads()` 失败，后面仍执行 `dispatch(..., args)`；此时 `args` 可能没有赋值。
- 修改目标：异常分支执行完后，应 `continue`，或为本次工具调用直接生成错误结果，不能再调用真实工具。
- 验收：让测试数据中的 `arguments` 等于 `"{bad json"`，程序不崩溃，且模型能收到可理解的错误消息。

## P1：README 要求的可靠性能力

### [x] P1-1 捕获模型 API 调用异常

- 文件：`stage2/tools_agent.py`
- 现状：网络超时、限流、认证失败都会直接终止程序。
- 修改目标：在 `client.chat.completions.create(...)` 外捕获异常，返回清楚的失败信息；是否重试应设置有限次数。
- 验收：使用错误 key 或模拟网络异常时，CLI 不显示未处理异常栈。

### [x] P1-2 检查 `msg.tool_calls` 是否存在

- 文件：`stage2/tools_agent.py`
- 现状：代码直接遍历 `msg.tool_calls`。在部分非 `stop` 返回场景中，它可能是 `None`。
- 修改目标：只有存在工具调用时才遍历；没有正文也没有工具调用时，返回明确错误。
- 验收：模拟 `tool_calls=None` 时不出现 `TypeError: 'NoneType' is not iterable`。

### [ ] P1-3 阻止完全相同的重复工具调用

- 文件：`stage2/tools_agent.py`
- 参考：`stage2/AIcode/robust1_errors.py`
- 现状：模型可反复使用同一组参数调用同一个工具，直到耗尽最大步数。
- 修改目标：保存 `(工具名, 规范化参数)`；重复时不再次执行，而是提示模型更换参数或策略。
- 注意：参数可用 `json.dumps(args, sort_keys=True, ensure_ascii=False)` 规范化。
- 验收：相同调用连续出现两次时，真实工具只执行一次。

### [x] P1-4 区分 dispatch 的错误类型

- 文件：`stage2/tools_regestry.py`
- 现状：所有执行异常都返回 `error:{e}`，未知工具的提示也缺少工具名。
- 修改目标：至少区分：
  1. 未知工具；
  2. 参数缺失、参数名错误等 `TypeError`；
  3. 工具内部执行异常。
- 验收：分别调用不存在的工具、漏传参数、传错参数名，返回三种清晰提示且程序不崩溃。

### [x] P1-5 识别并明确反馈空结果

- 文件：`stage2/tools_agent.py`、`stage2/tools_defs.py`
- 现状：不同工具分别返回“未命中”“空字符串”“(no output)”等，agent 很难统一判断。
- 修改目标：约定统一、可识别的工具结果，例如 `ERROR:`、`EMPTY:`、`OK:`，或统一 JSON 结构。
- 验收：检索未命中、SQL 零行、空文件、网页空正文时，模型都能知道应换参数/工具，而不是编造答案。

### [ ] P1-6 增加程序侧引用编号校验

- 文件：`stage2/rag_answer.py`
- 参考：`stage2/AIcode/robust2_citations.py`
- 现状：SYSTEM 只是要求模型正确引用，属于软约束；模型仍可能生成不存在的 `[4]`、`[8]`。
- 修改目标：
  1. 用正则提取回答里的所有 `[n]`；
  2. 检查编号是否位于 `1..len(hits)`；
  3. 有越界编号时，把错误反馈给模型并有限重试；
  4. 有事实结论的回答至少需要一个引用。
- 验收：给校验函数输入 `"结论 [1]，补充 [7]"`，当有效编号只有 `{1,2,3}` 时，应识别出 `7` 非法。

### [ ] P1-7 给 `rag_answer.query()` 增加 API 异常处理

- 文件：`stage2/rag_answer.py`
- 现状：key 缺失、认证失败、超时或限流都会直接抛异常。
- 修改目标：返回用户可理解的错误，并区分“检索失败”和“生成失败”。
- 验收：key 不存在或无效时，程序不会输出未处理异常栈。

## P2：工具安全边界

### [ ] P2-1 修复文件目录边界判断

- 文件：`stage2/tools_defs.py`
- 现状：使用 `target.startswith(DATA_DIR)` 判断是否越界；路径字符串前缀并不等同于父子目录关系。
- 修改目标：使用 `os.path.commonpath()` 或 `pathlib.Path.resolve()` 后检查目标确实位于 `data/` 内。
- 同时建议：扩展名判断使用小写形式，避免 `.MD` 等大小写差异。
- 验收：`../key`、绝对路径、相似前缀目录都被拒绝；合法的 `data/*.md` 可以读取。

### [ ] P2-2 让 SQL 连接真正只读

- 文件：`stage2/tools_defs.py`
- 现状：只用 `startswith("select")` 判断，但 SQLite 连接本身仍有写权限；查询还会先 `fetchall()` 再截取 20 条。
- 修改目标：
  - 只允许单条 `SELECT`；
  - 拒绝多语句；
  - 使用 `file:...?...mode=ro` 只读连接；
  - 使用 `fetchmany(20)`，避免先加载全部结果。
- 验收：普通 SELECT 正常；UPDATE、DELETE、DROP、多语句均被拒绝；大结果最多返回 20 行。

### [ ] P2-3 明确 `run_python()` 不是安全沙箱

- 文件：`stage2/tools_defs.py`、`stage2/tools_regestry.py`
- 现状：虽然有 10 秒超时，但代码仍可读取/修改文件、联网和启动子进程。
- 修改目标：在 docstring、工具描述和 README/笔记中明确“只执行可信的学习代码，不用于生产环境”。
- 建议：在最终研究助手中默认关闭该工具，或增加人工确认。
- 验收：阅读工具 schema 时，模型和开发者都能看到风险说明。

### [ ] P2-4 改进网页 URL 校验

- 文件：`stage2/tools_defs.py`
- 现状：正则只检查字符串以 `http://` 或 `https://` 开头，没有确认主机名；也没有处理重定向后的地址风险。
- 修改目标：至少使用 `urllib.parse.urlparse()` 验证 scheme 和 hostname。
- 进阶项：生产环境应阻止 localhost、回环地址和内网地址，防止 SSRF。
- 验收：`https://`、`http://`、无主机名 URL 被拒绝，正常公网 URL 可通过。

### [ ] P2-5 正确处理 HTML 实体

- 文件：`stage2/tools_defs.py`
- 现状：`re.sub(r"&[a-z]+;", " ", text)` 会丢弃实体内容，也覆盖不了数字实体。
- 修改目标：使用标准库 `html.unescape()`；需要更可靠正文提取时再学习 BeautifulSoup/readability。
- 验收：`Tom &amp; Jerry` 转换为 `Tom & Jerry`。

## P3：RAG 检索质量与缓存

### [ ] P3-1 为输入和零向量增加保护

- 文件：`stage2/rag_retrieve.py`、`stage2/rag_embed.py`
- 现状：空查询、空 chunks 或零向量可能导致 `np.vstack()` 错误或归一化除零，产生 `NaN`。
- 修改目标：校验空字符串、`top_k <= 0`、空语料、零范数。
- 验收：空查询和空语料返回空结果或清晰错误，不产生 warning/traceback。

### [ ] P3-2 让 embedding 缓存自动失效

- 文件：`stage2/rag_embed.py`
- 现状：只要两个缓存文件存在就直接使用；修改语料、分块参数或模型后仍可能读到旧向量。
- 修改目标：缓存元数据至少记录：
  - embedding 模型名；
  - chunks 内容哈希；
  - chunk 数和向量数。
- 不一致时自动重建缓存。
- 验收：修改任意一篇 `data/*.md` 后，下一次加载能检测变化并重建。

### [ ] P3-3 调整分块大小并增加 overlap

- 文件：`stage2/rag_chunker.py`
- 现状：按 200 个字符切分且没有重叠，容易割裂完整语义；它统计的是字符，不是 token。
- 修改目标：把 `window` 和 `overlap` 做成参数；可先实验 `window=500, overlap=80`，但不要把该数值当成固定最佳答案。
- 验收：长段落相邻 chunks 有适量重叠，且循环一定向前推进、不会死循环。

### [ ] P3-4 增加相关度阈值或“不相关”判断

- 文件：`stage2/rag_retrieve.py`、`stage2/rag_answer.py`
- 现状：向量检索永远返回 top-k，即使所有片段都与问题无关，因此 `if not hits` 很少生效。
- 修改目标：通过一组相关/不相关测试问题确定最低相似度，或在生成前增加相关性判断。
- 验收：知识库完全不涉及的问题能够返回“资料不足”，而不是强行引用前三条。

### [ ] P3-5 解决中文查询与英文 embedding 模型的语言错配

- 文件：`stage2/rag_embed.py`、`stage2/rag_answer.py`
- 现状：语料和 `BAAI/bge-small-en-v1.5` 都偏英文，但程序允许用户直接用中文查询，检索质量可能不稳定。
- 方案任选其一：
  1. 初学版明确要求英文检索词；
  2. 检索前把中文问题翻译成英文；
  3. 换用多语言 embedding 模型。
- 验收：准备中英文同义问题，比较 top-3 命中结果。

### [ ] P3-6 评估混合检索

- 文件：未来可新增 BM25 模块，或复用 `AIcode/rag3_bm25.py` 的思路。
- 现状：当前只有向量检索；专有名词、文件名、编号等精确词可能不占优势。
- 修改目标：学习完成向量检索后，再组合 BM25 与 vector 分数或使用 RRF 排名。
- 验收：语义改写问题和精确关键词问题都能稳定命中正确文章。

## P4：配置、命名与代码维护

### [ ] P4-1 延迟创建 LLM client

- 文件：`stage2/tools_agent.py`
- 现状：模块导入时立即读取 key 并创建 client，导致单元测试和复用困难。
- 修改目标：封装 `make_client()`；运行 `answer()` 或主程序时再读取配置。
- 建议：优先读取环境变量，学习阶段可保留 key 文件作为回退。
- 验收：没有 key 时仍能 import `tools_agent`，只在真正调用模型时提示配置错误。

### [ ] P4-2 统一工具参数命名

- 文件：`stage2/tools_defs.py`、`stage2/tools_regestry.py`
- 现状：`sql_query(QUERY)` 使用大写参数，其他参数均为小写。
- 修改目标：统一改为 `sql`，并同步 schema 中的 `properties` 和 `required`。
- 验收：`dispatch("sql_query", {"sql": "SELECT ..."})` 能正常执行。

### [ ] P4-3 修正文件名拼写

- 文件：`stage2/tools_regestry.py`
- 现状：`regestry` 应拼写为 `registry`。
- 修改目标：重命名为 `tools_registry.py`，并同步所有 import。
- 建议：等功能稳定后再做，避免和逻辑修改混在一起。
- 验收：全项目搜索 `regestry` 没有残留，相关脚本仍可运行。

### [ ] P4-4 清理未使用导入和调试代码

- 涉及：
  - `stage2/tools_agent.py` 的 `sys`；
  - `stage2/tools_defs.py` 的 `json`；
  - `stage2/rag_embed.py` 的 `TypedDict`；
  - 注释掉的调试语句和文件尾测试注释。
- 修改目标：功能稳定后清理，不要早于 P0/P1。
- 验收：清理后 `python -m compileall -q stage2` 通过。

### [ ] P4-5 改善格式和可读性

- 范围：`stage2/*.py`
- 现状：导入顺序、运算符空格、函数间空行和变量命名不统一。
- 修改目标：先人工按 PEP 8 整理；后续可以学习 Ruff/Black，但不要让格式化掩盖逻辑改动。
- 验收：每次提交只包含一种目的明确的修改。

## P5：README 中尚未落地的学习目标

### [ ] P5-1 实现自己的会话记忆

- 当前状态：只有 `AIcode/mem1_session.py` 示例，个人代码尚未实现。
- 学习目标：理解无记忆、全量历史、滚动窗口、摘要压缩的区别。
- 验收：连续两轮对话中，模型能根据你选择的策略正确记住或遗忘第一轮信息。

### [ ] P5-2 实现自己的长期记忆

- 当前状态：只有 `AIcode/mem2_longterm.py` 示例。
- 学习目标：只保存跨会话仍有价值的用户事实，并在新会话中重新注入。
- 验收：关闭程序再启动后，能够加载已保存事实；一次性闲聊不应被长期保存。

### [ ] P5-3 整合最终研究助手

- 建议文件：`stage2/research_assistant.py`
- 前置条件：至少完成 P0、P1、P2-1、P2-2、P3-4。
- 目标流程：用户主题 → 多次检索/工具调用 → 筛选证据 → 生成回答 → 校验引用 → 输出来源。
- 验收：
  - 有资料的问题能给出可核验引用；
  - 无资料的问题明确拒答；
  - 工具失败不会导致程序崩溃；
  - 不会无限重复同一调用。

## 每完成一项都建议运行的检查

```powershell
python -m py_compile stage2/tools_agent.py
python -m compileall -q stage2
```

涉及纯函数时，优先写不调用模型、不访问网络的确定性测试，例如：

- 非法 JSON 参数是否被捕获；
- 重复工具调用是否被阻止；
- 路径穿越是否被拒绝；
- 非 SELECT SQL 是否被拒绝；
- 越界引用是否被识别；
- 空查询、空语料、零向量是否被安全处理。

## 当前进度概览

- [x] 文档加载
- [x] 基础分块
- [x] embedding 与向量缓存
- [x] top-k 向量检索
- [x] 基础 RAG 回答提示词
- [x] 五类工具定义与注册
- [x] 基础 agent loop
- [ ] agent loop 当前可运行（被 P0 阻塞）
- [ ] 工具失败、空结果、重复调用的完整护栏
- [ ] 程序侧引用校验
- [ ] 会话记忆
- [ ] 长期记忆
- [ ] 最终研究助手
