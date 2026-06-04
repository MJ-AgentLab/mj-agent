---
type: adr
domain: AGENT
summary: src/mj_agent/llm.py make_llm() 抽象为 provider 分支 factory（ark + local-openai-compat），支持 DGX-Spark vLLM/SGLang/Ollama 等 OpenAI-compatible local endpoint；Profile enum 不扩 dgx（DGX 不部署 mj-agent）
owner: 项目负责人
created: 2026-05-11
updated: 2026-05-11
state: active
decision: accepted
track: code
tags:
  - adr
  - llm
  - provider
  - dgx
  - abstraction
---

# ADR-027: LLM Provider Abstraction

> **历史**：本 ADR 与 [[decisions/ADR-026_Multi_Environment_Compose_Profile|ADR-026]] / [[decisions/ADR-028_MCP_Server_Inventory_And_Governance|ADR-028]] 由历史 ADR-025 拆分而来（ADR-025 已 archive）。本 ADR 聚焦 LLM provider 抽象一题。

## Context

`src/mj_agent/llm.py` 早期硬编码 Volcengine Ark；DGX-Spark (192.168.0.189) 即将上线作为团队本地 LLM 算力节点（vLLM / SGLang / Ollama serving；deployment 责任另议）。mj-agent 需要无侵入路径切到 OpenAI-compatible local endpoint。

项目负责人 2026-05-09 决策的 5 项关键约束：

1. **DGX 仅作算力提供，不部署任何应用服务（含 mj-agent）** → DGX 支持本质是 LLM endpoint 切换，**不**是新加 profile（详见 [[decisions/ADR-026_Multi_Environment_Compose_Profile|ADR-026]] §D.3 OOS）
2. LLM serving 部署责任另议；mj-agent 仅做消费侧
3. 默认行为完全保持 Ark 路径，向后兼容现有 `.env`
4. local endpoint 使用 OpenAI-compatible API（vLLM / SGLang / Ollama / TGI / llama.cpp 标准协议）
5. Ark `extra_body.thinking` DeepSeek 推理参数不应误传给 OpenAI-compatible local server（否则 422）

## Decision

### D.1 `make_llm()` provider 分支 factory

`src/mj_agent/llm.py` 从单一 Ark 路径扩展为 provider 分支：

| Provider | base_url | api_key | extra_body | 适用 |
|---|---|---|---|---|
| `ark`（默认） | `effective_llm_base_url` fallback `ark_base_url` | `effective_llm_api_key` fallback `ark_api_key` | `{"thinking": {"type": "enabled\|disabled"}}` | 公网 Ark + DeepSeek V3 |
| `local-openai-compat` | `llm_base_url`（必填；缺即 `LLMConfigError`） | `llm_api_key` 或 `"EMPTY"` sentinel | **不带**（vLLM/SGLang/Ollama 不接受 Ark `thinking` 参数） | DGX-Spark vLLM/SGLang/Ollama/TGI/llama.cpp |

### D.2 `Profile` enum 不变

`Profile` 保持 `Literal["dev","test","prod"]` 三值；**不**引入 "dgx"。理由：

- DGX 不部署 mj-agent → 没有 dgx 部署单元
- DGX 支持是 **LLM endpoint 切换**，正交于 `MJ_CONFIG_PROFILE`（决定 biz pg host）
- 加 dgx profile 会引入混淆（profile 通常意味"部署单元"）

### D.3 向后兼容

- `LLM_PROVIDER` 默认 `ark`
- `effective_llm_*` cached_property fallback 至 `ark_*` 字段
- 现有 `.env` 不动则 `make_llm()` 行为完全一致
- 切换路径：`.env` 设 `LLM_PROVIDER=local-openai-compat` + `LLM_BASE_URL=http://192.168.0.189:8000/v1` 即可消费 DGX vLLM；无需新写 compose 文件 / 改 `Profile` enum / 重启 mj-agent 容器（dev mode）

### D.4 Endpoint 健康验证

新建 `mj-agent-infra-llm-endpoint-probe` SKILL（in-tree workflow skill；ADR-013 native schema）：

- Step 1：reachable check（`curl -sI ${LLM_BASE_URL}/models` 或 Ollama `/api/tags` fallback）
- Step 2：model id match（响应 JSON `data[].id` 包含目标 model）
- Step 3：1-token chat smoke（`POST /chat/completions` with `max_tokens=1`）

3 步全过 → endpoint 可用；任一失败 → 输出诊断 + 建议（vLLM serve 重启 / SGLang `--port` 检查 / Ollama `pull` 模型 / 网络连通性）。

## Consequences

### 正面

- **DGX 算力消费即插即用**：开发者切 env vars 即可消费 DGX vLLM；不需新写 compose / 改 enum
- **向后兼容**：现有 dev / Phase 1 流程行为完全一致
- **Provider 解耦**：未来加新 provider（如 OpenRouter / Together AI）只需扩 factory 分支，不破坏 `make_llm()` API
- **诊断友好**：`/mj-agent-infra-llm-endpoint-probe` 提供 3-step probe；快速定位 endpoint 问题

### 负面

- **配置面增加**：`.env.example` 新增 `LLM_PROVIDER` / `LLM_BASE_URL` / `LLM_API_KEY` 三个字段；onboard 开发者需理解 provider 选择
- **Test coverage**：`tests/unit/test_llm.py` 需覆盖两 provider 分支 + `LLMConfigError` 路径；smoke test 当前仅 Ark 路径
- **`extra_body.thinking` 默认行为差异**：Ark provider 携带、local-openai-compat 不带；新 provider 加入时需明确决定是否携带

### 暂未实现（用户决策；out-of-scope）

- **LLM serving 容器部署**：DGX 上 vLLM / SGLang / Ollama 服务的部署责任另议（专门 issue）
- **Multi-model routing**：mj-agent 默认全部任务走单一 LLM；未来可扩按任务类型路由（如 reasoning 任务用 DeepSeek，summary 用本地小模型）— Phase 4+ 评估
- **Cost / latency tracking per provider**：LangSmith trace 已记 token 用量，但 provider-level cost dashboard 未自建

## Alternatives considered

- **A. 仅扩 `LLM_BASE_URL` + 让 user 自己保证 OpenAI-compat**：拒绝。`extra_body.thinking` 误传 422 是真实问题；factory 必须在 client init 时就分支
- **B. 引入 LangChain 的 `ChatOpenAI` + `ChatVolcengine` 自动路由**：拒绝。LangChain 的 provider 集成层已经做这件事，但本仓 `llm.py` 已直接用 `langchain_openai.ChatOpenAI` + Ark base_url override；factory 分支比框架级路由更轻量、可观测
- **C. 在 `Profile` enum 加 dgx**：用户决策 1 否决；详见 §Context 决策 1
- **D. 等 mj-agent K8s 化后用 service mesh 路由**：拒绝。Phase 1-2 阶段 K8s 不在范围；本 ADR 解决 Phase 1 实际需求

## References

- [[decisions/ADR-026_Multi_Environment_Compose_Profile|ADR-026]] — `Profile` enum 设计；DGX 不部署 mj-agent 决策起源
- [[decisions/ADR-028_MCP_Server_Inventory_And_Governance|ADR-028]] — DGX SSH 通过 MCP `ssh-manager` 访问（运维路径，与 LLM 消费正交）
- [[archive/decisions/superseded/[DEPRECATED]_[ADR]_025_Multi_Environment_And_LLM_Provider_Abstraction|ADR-025（archive）]] — 历史 bundle ADR
- `src/mj_agent/llm.py` — `make_llm()` factory 实现
- `src/mj_agent/config.py` — `Settings` `llm_provider` / `llm_base_url` / `llm_api_key` / `effective_llm_*` 字段
- `.env.example` 中 LLM provider 段（含 ark / local-openai-compat 两 provider 注释）
- `mj-agent-infra-llm-endpoint-probe` SKILL — 3-step endpoint probe
- 实施 PR：[#101](https://github.com/MJ-AgentLab/mj-agent/pull/101)（PR-2 of original ADR-025 4-PR sequence）
