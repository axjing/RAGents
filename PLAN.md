# Ragent — Agentic RAG Implementation Plan

> 目标：从零构建一个名为 **Ragent** 的 Agentic RAG 系统。不依赖 langchain/llamaindex 等封装框架，
> 使用 agents 与 harness 等原创抽象实现复杂问答、多步推理、外部工具调用与多模态检索。

---

## 1. 项目愿景与核心定位

Ragent 不是"加一层 LLM 的向量检索"，而是一支**智能研究团队**：
- 每一组文档由一个独立的 **子 agent** 管理（文档集即 agent）。
- 一个**主控 agent（harness）**负责任务分解、子 agent 调度、结果综合与反思。
- 引入 **ReAct / Loops / Reflection / Tool-Calling** 范式，让系统在无法直接回答时主动"规划 → 行动 → 观察 → 反思"。
- **skill.md** 机制允许以声明式文件动态注册新能力（类似"技能卡"）。

---

## 2. 技术栈（硬性约束）

| 层 | 选型 | 备注 |
|---|---|---|
| 基础 LLM | Qwen3-VL、GLM、Llama 系列 | 同时适配 OpenAI/Azure/DashScope 等闭源 API，通过统一 `LLMProvider` 抽象 |
| 多模态 Embedding | Qwen2.5-VL / JinaCLIP / bge-m3 | 统一 `EmbeddingProvider`，支持文本/图像/文档页/视频帧/语音转写 |
| 文本检索 | BM25（Rank-BM25） | 与向量检索做**混合检索**与**重排** |
| 向量库 | PgVector + Milvus（双后端可切换） | PgVector 用于中小规模；Milvus 用于大规模向量与标量混合检索 |
| 关系数据库 | PostgreSQL | 存储文档元数据、agent 状态、会话历史、工具注册、skill 元数据 |
| 后端语言 | Python 3.12+ | FastAPI + Pydantic + asyncio |
| 前端 | TypeScript + React | Vite |
| 消息总线 | 进程内 `asyncio.Queue` 起步，预留 Redis Stream 接口 | agent 之间通过消息通信而非直接函数调用 |
| 部署 | Docker Compose（开发）+ 可选 Kubernetes | PostgreSQL + Milvus + FastAPI + 前端一体 |

> 禁止：langchain、llamaindex、以及任何"开箱即用"的 agent 框架。所有 agent/harness 逻辑必须自写。

---

## 3. 架构分层

```
┌────────────────────────────────────────────────────┐
│                     Frontend (React)               │
│  会话 UI、多模态上传、引用溯源展示、agent 可视化   │
└──────────────┬─────────────────────────────────────┘
               │ HTTP / WebSocket
┌──────────────▼─────────────────────────────────────┐
│                FastAPI Backend                     │
│  /chat  /upload  /agents  /skills  /admin          │
└──────────────┬─────────────────────────────────────┘
               │
┌──────────────▼─────────────────────────────────────┐
│              Harness 层（核心调度）                │
│  Planner → Router → Sub-Agents → Reflection Loop  │
│  + Tool Registry + Skill Registry + Memory Store  │
└──────────────┬─────────────────────────────────────┘
               │
┌──────────────▼─────────────────────────────────────┐
│              Retrieval 层                          │
│  HybridRetriever(BM25 + Vector) + Reranker         │
│  + MultimodalExtractor + Chunker + CitationIndex   │
└──────────────┬─────────────────────────────────────┘
               │
┌──────────────▼─────────────────────────────────────┐
│              Data 层                               │
│  PostgreSQL (metadata/sessions)                    │
│  PgVector / Milvus (vectors)                       │
│  Object Storage (files, images, video frames)      │
└────────────────────────────────────────────────────┘
```

---

## 4. 里程碑（Milestones）

### M0 — 脚手架与基础设施
- 目标：让项目"能跑起来"，具备可测试的骨架。
- 交付：
  - `backend/` Python 包结构（FastAPI app、settings、logging、db session）。
  - PostgreSQL + PgVector Docker Compose 启动脚本。
  - `frontend/` Vite + React + TS 基础工程。
  - `ragent.core` 抽象层：`LLMProvider`、`EmbeddingProvider`（各实现一个 mock 便于本地开发，再实现 Qwen/GLM/OpenAI）。
  - CI：GitHub Actions（lint + type-check + unit-test）。
- 验收：`POST /v1/ping` 返回 `{"ok":true}`；前端能连接并显示首页；一个测试用 `python -m ragent demo-chat "你好"` 能输出一段"hello agent"。

### M1 — 文档摄取与多模态索引
- 目标：用户上传文件 → 切分 → 向量化 → 入库 → 可检索。
- 关键模块：
  - **ingest**: `Document` 模型（统一抽象：pdf/docx/txt/md/html/音视频）。
  - **extractor**: 基于 `unstructured.io`（轻量自集成，不使用其 RAG 层）+ 自研 `ImageExtractor`、`VideoFrameExtractor`、`AudioTranscriber`。
  - **chunker**: 语义切分 + 递归切分 fallback；保留 parent-child 引用（用于引用溯源）。
  - **indexer**: 写入 PgVector（语义向量）+ Rank-BM25（词法索引）+ PostgreSQL（元数据）。
- 验收：上传 3 份 PDF/Markdown 文档，能返回 `ingest_id`；`GET /v1/retrieve?q=xxx` 返回 top-K chunk，带 `source_id / page / doc_title`。

### M2 — 单 Agent 与 ReAct 循环
- 目标：一个 agent 能独立完成"提问 → 检索 → 思考 → 回答"。
- 关键模块：
  - `Agent` 基类：`state`（Pydantic 模型）+ `think()` + `act()` + `observe()` 循环。
  - `ReActAgent`：标准 ReAct prompt 模板 + 解析 `Thought/Action/Action Input/Observation`。
  - `Tool` 抽象：`search_documents`, `search_web`（可选），`read_chunk`, `count_tokens`, `ask_user`。
  - `CitationIndex`：每次 tool 调用绑定 `source_id`，最终回答用 `[n]` 引用并在底部生成参考列表。
- 验收：对已索引文档集合提问，回答中至少包含一个真实引用；前端在 UI 中可点击跳转原文片段。

### M3 — Harness：多 Agent 协调与任务规划
- 目标：引入 **Harness**（总控），将复杂问题拆给多个子 agent。
- 设计：
  - `Planner`：接收用户问题 + 上下文，产出一个**计划图**（DAG，节点=子任务，边=依赖）。
  - `Router`：将子任务路由到最合适的子 agent（基于 skill 注册信息做匹配）。
  - `Synthesizer`：合并子 agent 的结果，生成最终回答。
  - `Reflection Loop`：对 Synthesizer 的产出做自检（是否答非所问？是否缺少引用？），必要时重新规划。
- 验收：给出一个跨 3 份文档的对比类问题，系统显示"问题分解 → 分派给 3 个子 agent → 汇总"的日志流。

### M4 — Skill 机制（skill.md）
- 目标：通过声明式 `skill.md` 文件动态注册能力，**无需重启服务即可扩展**。
- 设计：
  - `SkillSpec`（YAML/Markdown frontmatter）：`name, description, inputs, outputs, prompts, tools, examples`。
  - `SkillCompiler`：把 skill.md 编译为一个"模板化的 agent 实例"。
  - `SkillRegistry`：基于目录扫描；支持热 reload（watchdog）。
- 验收：新建 `skills/arxiv_search.skill.md`（描述一个查询 arXiv 的技能），无需重启，agent 可在 ReAct 循环中调用该 skill。

### M5 — 多模态输入 / 多模态召回
- 目标：文本、图像、文档、视频、语音均可作为 query 或作为被检索内容。
- 关键模块：
  - `MultimodalInput`：`TextInput / ImageInput / DocInput / VideoInput / AudioInput`。
  - `QueryFuser`：多模态 query → 统一 query vector + 文本描述（由 VLM 生成）。
  - `MultimodalRetriever`：在 text / image / video-frame / audio-transcript 多个集合中联合检索。
  - `Reranker`（LLM 或 cross-encoder）：跨模态重排。
- 验收：上传一张架构图并提问"此图中的数据流方向"，系统召回该图 + 相关文本段落并给出带引用的回答。

### M6 — 前端与交互体验
- 目标：对话体验接近 ChatGPT，但附加"agent 编排可视化 + 引用溯源"。
- 关键页面：
  - 会话页：消息气泡、引用脚注、"thinking trace"可折叠面板。
  - 知识库页：上传、管理、查看文档索引状态。
  - Agents 页：查看已注册 agent / skill；编辑 skill.md。
  - 可视化页：显示 Harness 的 DAG 执行过程（节点=子 agent，进度条）。
- 验收：完成一次跨文档多模态问答，前端流畅展示 plan / steps / sources。

### M7 — 性能、安全与生产化
- 目标：大规模（百万级 chunk）可用；安全；可观测。
- 任务：
  - 引入 Milvus 做向量规模测试；Benchmark：P@1 / MRR / 端到端时延。
  - **Guardrails**：prompt injection 检测、幻觉自检（citation-coverage 指标）。
  - 鉴权：API Key / OAuth2（JWT），按会话隔离。
  - 审计日志：每次 agent 行动落库，可追溯。
  - 可观测：OpenTelemetry → Prometheus + Grafana。

---

## 5. 目录结构（建议）

```
RAGents/
├── PLAN.md                        # 本文件
├── AGENTS.md                      # 开发规范
├── README.md
├── docker-compose.yml             # postgres + pgvector + milvus + minio
├── backend/
│   ├── pyproject.toml             # 包管理：poetry 或 uv
│   ├── src/ragent/
│   │   ├── __init__.py
│   │   ├── config/                # settings, env vars
│   │   ├── core/
│   │   │   ├── llm.py             # LLMProvider 基类 + Qwen/GLM/OpenAI impl
│   │   │   ├── embedding.py       # EmbeddingProvider 基类 + 多模态 impl
│   │   │   └── types.py           # 通用 Pydantic 模型
│   │   ├── db/                    # SQLAlchemy models + migrations (alembic)
│   │   ├── ingest/                # extractor, chunker, indexer
│   │   ├── retrieval/             # hybrid retriever, reranker, citation index
│   │   ├── agents/                # Agent 基类, ReActAgent, SubAgent
│   │   │   └── base.py
│   │   ├── harness/               # Planner, Router, Synthesizer, Reflection
│   │   ├── tools/                 # Tool 基类 + 内建工具
│   │   ├── skills/                # SkillSpec, SkillCompiler, SkillRegistry
│   │   ├── memory/                # 短期/长期记忆（session + user profile）
│   │   ├── api/                   # FastAPI routers
│   │   │   ├── v1/chat.py
│   │   │   ├── v1/ingest.py
│   │   │   ├── v1/agents.py
│   │   │   └── v1/skills.py
│   │   └── server.py              # FastAPI app 入口
│   └── tests/                     # pytest，每模块至少一个 e2e
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── app/                   # 路由与页面
│       ├── components/            # 聊天组件、上传组件、agent 可视化
│       ├── store/                 # nanostores（按 AGENTS.md 规范）
│       └── lib/                   # API client + utils
└── skills/                        # 运行时可热加载的 skill.md
    ├── search.skill.md
    ├── arxiv.skill.md
    └── summarize.skill.md
```

---

## 6. 核心数据模型（草案）

```python
# ragent/core/types.py
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from uuid import UUID

class DocType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"

class Chunk(BaseModel):
    id: UUID
    document_id: UUID
    doc_type: DocType
    text: str | None = None           # 文本或转写
    media_ref: str | None = None      # 对象存储路径（图像/视频帧/音频）
    page: int | None = None
    span: tuple[int, int] | None = None  # 原文字符起止
    embedding: list[float] | None = None
    metadata: dict = Field(default_factory=dict)

class ToolCall(BaseModel):
    tool_name: str
    arguments: dict
    observation: str | None = None
    citations: list[UUID] = Field(default_factory=list)
    ts: datetime = Field(default_factory=datetime.utcnow)

class AgentTrace(BaseModel):
    step: int
    thought: str
    tool_call: ToolCall | None = None
    reflection: str | None = None

class ChatTurn(BaseModel):
    user_query: str
    multimodal_inputs: list = Field(default_factory=list)  # 多模态附件
    plan_dag: dict | None = None                           # Harness 生成的 DAG
    traces: list[AgentTrace] = Field(default_factory=list)
    answer: str | None = None
    citations: list[Chunk] = Field(default_factory=list)
```

---

## 7. Harness 运行循环（核心算法）

```
输入: user_query, session_id, multimodal_inputs
输出: final_answer, citations, plan_dag, traces

1) QUERY_PARSE
   - 把多模态输入映射为"文本描述 + 联合向量"。

2) PLAN
   - 调用 LLM 生成一个任务分解 DAG：
     节点 = (sub_query, required_skill, candidate_docs)
     边   = 依赖关系
   - 通过 Reflected LLM 做一次 plan 自检与修正。

3) ROUTE
   - 对每个节点：
     a) 基于 SkillRegistry 匹配最合适的 sub-agent
     b) 注入该节点所需的文档集合 scoped retriever
     c) 并行/串行执行（按 DAG 拓扑排序）

4) EXECUTE (每个 sub-agent 的 ReAct 循环)
   while 未达到终止条件(步数/收敛/超时):
       thought  = agent.think(state)
       action   = agent.choose_tool(thought, tool_registry)
       obs      = tool_registry.run(action)           # 工具运行要绑定 source_id
       agent.observe(obs)
   answer_chunk = agent.synthesize()

5) SYNTHESIZE
   - 收集所有 sub-agent 的 answer_chunk
   - 由一个专用 agent 做综合："把这些子回答合并为一个完整、一致、带引用的最终答案"

6) REFLECT
   - 调用一个"校验 agent":
     * 回答是否覆盖了原问题所有要点？
     * 每个声明是否都有 citation 支持？
     * 是否存在内部矛盾？
   - 若校验失败，回到 PLAN（带失败原因）做最多 N 次 retry

7) PERSIST
   - 整个 plan_dag / traces / citations 落库（可审计、可回放）
   - 更新 session memory
```

---

## 8. 引用溯源（Citation Sourcing）

> 硬约束：**回答必须引用真实信息来源**。

- 机制：
  - 每个 `Chunk` 都有唯一 `id` 与 `document_id`。
  - tool `search_documents` 的返回体包含这些 id。
  - agent 在写入回答模板时，每段内容后必须带上 `[n]`。
  - `Synthesizer` 对引用覆盖率做检查，低于阈值（如 70%）则拒绝放行，强制重新检索。
  - 前端把 `[n]` 渲染为可点击脚注，跳转到 `chunk.span` 对应原文。

---

## 9. Skill.md 格式规范

每个 skill 是一个 Markdown 文件，YAML frontmatter 声明元数据，正文是 prompt 模板与示例。

```markdown
---
name: search_web
description: 当问题需要最新信息时使用搜索引擎
inputs:
  query: string
outputs:
  results: list[{title, snippet, url}]
tools: [http_get, bing_search]
examples:
  - query: "2026 年 Qwen3 的最新版本"
    note: 调用此 skill 而不是直接检索文档库
---

# System

你是一个 web search specialist。你擅长把自然语言查询翻译成关键词组合。

# Template

USER: {{query}}
STEP 1. 把问题改写为 3 个关键词查询。
STEP 2. 对每个查询调用 `bing_search`。
STEP 3. 用 `http_get` 打开 top-1 结果的正文前 2000 字符。
STEP 4. 返回去重合并后的摘要。

# Constraints

- 每个结果必须带 URL。
- 不做事实外推，snippet 内原文标注为引用。
```

`SkillCompiler` 的职责：解析 frontmatter → 渲染 prompt 模板 → 把 `tools` 绑定到工具注册表 → 产出一个 `AgentSpec`（即一个可实例化的 agent 蓝图）。

---

## 10. ReAct / Loops / Reflection 的具体落地

| 机制 | 位置 | 实现要点 |
|---|---|---|
| **ReAct** | `ReActAgent.act()` | `Thought / Action / Action Input / Observation` 四段式 prompt；用结构化解析器（regex + Pydantic）把 LLM 文本拆成 state 更新 |
| **Loops** | `Harness.run()` | DAG 节点的依赖循环；每个子 agent 内部也有步数上限的 self-loop |
| **Reflection** | `ReflectorAgent` | 独立的 LLM 调用，输入=（原问题，plan，已产出的回答，citations），输出=（ok / 需要重跑+原因）；最多 N 次 reflection |
| **Tool Calling** | `ToolRegistry` | 与 LLM 原生 function-calling 兼容（Qwen/GLM/OpenAI 都支持），同时提供"文本解析 fallback"，保证对任意 LLM 可用 |

---

## 11. 关键非功能性需求

- **可测试性**：每个模块必须有独立的 `MockProvider`，以便在无 GPU/无网络的环境跑 e2e 测试。
- **可观测性**：每个 agent step 产生 `AgentTrace`，包含 thought/tool/observation/引用；前端和日志同时可见。
- **可扩展性**：新增一个 LLM 只需实现 `LLMProvider`；新增一种文档只需新增一个 `Extractor`；新增一个能力只需写一个 `skill.md`。
- **安全**：永远不把原始文件路径暴露给前端；所有外部 HTTP 调用走白名单；prompt 注入检测至少做关键字黑名单 + LLM 判别两层。
- **不使用 langchain / llamaindex**：这是显式约束。任何 PR 若引入这些依赖，直接打回。

---

## 12. 开发顺序与任务拆分建议

1. **Week 1 — M0 + M1 骨架与 ingest 链**
   两人：一个做后端基础设施 + DB；一个做前端基础页。
2. **Week 2 — M2 单 Agent ReAct**
   全后端：`Agent` 基类 → `ReActAgent` → `Tool` 抽象 → 首个工具 `search_documents`。
3. **Week 3 — M3 Harness + M4 Skill**
   两人并行：Harness 调度 / Skill 编译器与热加载。
4. **Week 4 — M5 多模态**
   一人：EmbeddingProvider 多模态实现 + `MultimodalRetriever`；另一人继续完善 tool 生态。
5. **Week 5 — M6 前端深度交互**
   前端：会话流、引用可视化、agent DAG 动画。
6. **Week 6 — M7 生产化**
   全团队：鉴权、审计、benchmark、部署脚本。

---

## 13. 验收清单（Definition of Done）

- [ ] 一份文档能被 ingest → chunk → 向量化 → 入库。
- [ ] 单 agent 能基于文档回答问题，且答案中每段声明都可追溯到 chunk。
- [ ] Harness 能把一个跨文档对比问题拆成 ≥2 个子 agent 并行。
- [ ] 放一个新的 `skill.md` 到 `skills/` 目录后，agent 在下一轮对话即可调用。
- [ ] 上传图片提问能召回该图片 + 相关文本，并在答案中标注引用。
- [ ] 前端完整显示：问题、plan、每个子 agent 的 trace、最终答案、引用列表。
- [ ] Benchmark：在 ≥10 万 chunk 的测试集上，端到端时延 < 5s，P@1 ≥ 0.7。
- [ ] 项目内**不出现** langchain、llamaindex 依赖。

---

## 14. 下一步（立即行动）

1. 确认本 PLAN.md 的范围与里程碑，达成共识后进入 M0。
2. 初始化仓库结构（见 §5），创建 `backend/pyproject.toml` 与 `frontend/package.json`。
3. 写出 `ragent.core.LLMProvider` 与 `EmbeddingProvider` 的第一个实现（Qwen 或 OpenAI）。
4. 写第一个 e2e 测试：`ingest demo.md → ask question → assert answer contains citation`。

> "Start small, ship often, measure everything." —— 先让 M0 跑通，再逐里程碑迭代。