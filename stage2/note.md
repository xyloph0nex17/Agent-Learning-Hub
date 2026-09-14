# Stage 2 · Learn Tool Use, RAG, And Memory

对应 README「Stage 2」的五项 todo。目标产出：一个**资料研究助手**——输入主题，自动检索、筛选、总结并输出引用。

## Stage 1 -> Stage 2 的衔接

- Stage 1 你会了：LLM 对话、结构化 JSON、把工具登记给模型（TOOLS/REGISTRY/dispatch）、完整 agent loop（tools4_chat）。
- Stage 2 的增量：**给 agent 一个"能自己查资料"的知识源**（RAG）、**让它记住以前聊过什么**（memory）、**让它说出来的每句话有出处**（citations）、并且**处理好各种失败**。

一句话概括 Stage 2 在做什么：
> 让 agent 从"只会用计算器的小助手"变成"能查自己资料库、记得住事情、说话有依据的研究员"。

## 当前状态（2026-09-09：demo 已改成英文版）

- 语料库 `data/*.md`：8 篇**英文**原创短文（AI Agent 主题，概念与之前中文版一一对应）。
- 检索：`rag3` 纯英文分词（小写 + 按连续字母/数字切词），不处理中文。
- embedding：本地模型 `BAAI/bge-small-en-v1.5`（384 维，英文语义，约 67MB）。
- 教学注释/说明仍是中文，方便对照；跑 demo 时查询用英文即可。
- 语料变化后需删除 `AIcode/cache/` 再跑 `rag4_embed.py` 重新生成向量。

## 学习地图

分 5 个小节（A=检索与RAG，B=带引用的回答，C=记忆，D=可靠性，E=研究助手）。每步一个可运行文件，全部在 `AIcode/` 里。

| 小节 | 步骤 | 文件 | 学什么 |
| --- | --- | --- | --- |
| A 检索与RAG | ✓ A1 | `rag1_load.py` | 加载本地语料库（data/ 下的 .md） |
| | ✓ A2 | `rag2_chunk.py` | 为什么要把长文切成小块(chunk)，怎么切 |
| | ✓ A3 | `rag3_bm25.py` | 关键词检索的底层：分词、倒排索引、BM25 打分 |
| | ✓ A4 | `rag4_embed.py` | embedding 的底层逻辑 + 装库把语料变向量 |
| | ✓ A5 | `rag5_retrieve.py` | 向量检索（余弦相似度），对比 keyword vs vector |
| B 带引用回答 | ✓ B1 | `rag6_rag_answer.py` | 检索片段 + LLM 组装成"有依据"的回答（RAG 闭环） |
| T 工具接入 | ✓ T1 | `tools1_defs.py` | 5 类真实工具：搜索/文件/数据库/浏览器/代码执行（含边界与重试） |
| | ✓ T2 | `tools2_registry.py` | TOOLS 菜单 + REGISTRY 注册表 + dispatch 分发器 |
| | ✓ T3 | `tools3_agent.py` | agent loop 让模型自主选择并调用工具 |
| C 记忆 | ✓ C1 | `mem1_session.py` | 短期上下文 vs 会话记忆（4 种历史管理策略对比） |
| | ✓ C2 | `mem2_longterm.py` | 长期记忆（JSON 持久化 + 跨会话注入） |
| D 可靠性 | ✓ D1 | `robust1_errors.py` | 工具失败(重试)、空结果、重复调用、参数错误 的护栏 |
| | ✓ D2 | `robust2_citations.py` | 防"幻觉引用"：程序侧校验 [n] 是否真实，越界就打回重试 |
| E 研究助手 | E1 | `research_assistant.py` | 最终产出：资料研究助手（自主用工具研究 + 引用） |

## A3 速查：BM25 打分公式

给每个 chunk（当作"文档" $D$）和查询 $Q$ 打分，表示相关程度：

$$score(D,Q)=\sum_{t\in Q} IDF(t)\cdot\frac{f_{t,D}(k_1+1)}{f_{t,D}+k_1\big(1-b+b\frac{|D|}{avgdl}\big)}$$

外层是对查询里每个词 $t$ 的贡献求和（每个查询词各投一票）；每票 = 词的稀有度权重 × 词在这块文档里的充分度。

### IDF —— 这个词稀有吗

$$IDF(t)=\ln\Big(1+\frac{N-n_t+0.5}{n_t+0.5}\Big)$$

- $N$：全部 chunk 数；$n_t$：包含词 $t$ 的 chunk 数。$n_t$ 越小（词越稀有）分数越高。
- 细节：$+0.5$ 平滑防除零；$\ln$ 压缩差距，避免稀有词指数级碾压；外层 $+1$ 保证 IDF 恒正。

### TF 饱和项 —— 出现得多，但收益递减

$$\frac{f_{t,D}(k_1+1)}{f_{t,D}+k_1\big(1-b+b\frac{|D|}{avgdl}\big)}$$

- 词频 $f$ 越大越相关，但**边际收益递减**：出现第 3 次和第 20 次差别很小，防止"刷词文档"靠重复关键词取胜。
- $k_1$ 控制饱和快慢（越大越接近线性），经验值 1.2~2.0。
- 长度项 $1-b+b\frac{|D|}{avgdl}$：块越长（$|D|$ 大）分母越大 → 同样词频被打折。因为长文档词多、绝对次数天然高，不代表更相关。
- $b$ 控制长度惩罚力度，经验值约 0.75。

### 记忆口诀

> **求和** = 每个查询词投票；**IDF** = 稀有词权重高；**TF 饱和** = 同一词刷多了不值钱；**长度归一** = 长文要打折自证。

### 和代码对照（rag3_bm25.py）

```python
idf   = math.log(1 + (N - n + 0.5) / (n + 0.5))
denom = tf + k1 * (1 - b + b * dl / avgdl)
scores[i] += idf * tf * (k1 + 1) / denom
```

> 来源：源自 Robertson & Walker 的概率检索模型（RSJ）；$k_1$、$b$ 是在 TREC 评测集上经验调参得到的，非理论必然。

## A4/A5 速查：embedding 与向量检索

embedding = 把文字映射成"语义向量"。本课用 `fastembed`（装进 `.venv`，无 torch，轻量）+ 英文模型 `BAAI/bge-small-en-v1.5`（384 维，~67MB，纯英文语义）。

- **为什么能表达语义**：one-hot 每个词一维、互相正交、相似度恒 0；稠密向量由神经网络在海量语料上训练，让"意思相近的句子 → 向量方向接近"。
- **余弦相似度**：$cos(a,b)=\frac{a\cdot b}{|a||b|}$，越接近 1 越像。归一化（长度变 1）后 余弦 = 点积，可矩阵一次算完所有 chunk。
- **vs 关键词检索**：BM25 比"字面"（必须出现同样的词）；向量检索比"语义"（同义改写也能命中）。代价：要下载模型、离线把语料编码一遍、解释性差。
- **工程惯例**：keyword + vector 混合（hybrid），互相兜底。

运行产物（已生成，勿删）：

```
stage2/AIcode/cache/chunks.json     # 66 个 chunk 原文
stage2/AIcode/cache/vectors.npy     # 66×384 的向量矩阵
```

实测对比（`rag5_retrieve.py` 输出）：

| 查询 | 关键词 BM25 | 向量检索 |
| --- | --- | --- |
| "What is an agent?" | 命中 01 | 命中 01（0.97 / 0.83 / 0.76） |
| "How do I stop my model from making things up and force grounded answers?" | 靠字面词命中 04/07 | 命中 05/04 的 grounding / evidence 语义段 |
| "Why chunk long documents before retrieval?" | 命中 04 | 第一命中是 "Why chunk before retrieving"（0.84） |

## 每步怎么跑

代码不依赖"在哪运行"，会用 `__file__` 自动定位 `data/` 目录。所以直接：

```bash
cd /home/xyx/Agent-Learning-Hub/stage2
python AIcode/rag1_load.py      # 换成你想跑的步骤文件名
```

## 进度打卡（对应 README todo）

- [x] 会做检索增强生成：chunk、embed、retrieve、answer with citations（A1-A5 + B1 已跑通）
- [x] 会把搜索、数据库、文件、浏览器、代码执行接成工具（T1-T3：5 类工具模型可自主调用）
- [x] 会区分短期上下文、会话记忆、长期记忆（C1/C2 已跑通）
- [x] 会处理工具失败、空结果、重复调用、幻觉引用（D1 护栏 + D2 引用校验）
- [x] 会让 agent 在回答里给出来源或证据（rag6 带 [n] 引用 + D2 程序侧校验）
