---
name: mj-agent-infra-llm-endpoint-probe
description: This skill performs a 4-step healthcheck against an OpenAI-compatible local LLM endpoint hosted on DGX-Spark (192.168.0.189) — for the mj-agent local-openai-compat provider path (ADR-027 / PR-2 of multi-env+DGX+MCP bundle). It probes (1) LLM_BASE_URL env present + non-empty, (2) GET /v1/models returns ≥1 model with id matching LLM_MODEL_ID (or Ollama /api/tags fallback), (3) 1-token chat completion smoke, (4) tool-calling smoke — minimal tools array via default auto tool choice plus one named tool_choice discriminating retry, asserting finish_reason=tool_calls + parseable function arguments (mj-agent binds ALL_TOOLS into create_agent, so tool-calling is a hard dependency). Reports endpoint reachability + model-list match + chat smoke result + tool-calling capability verdict + actionable troubleshooting (DNS / firewall / wrong base URL / missing model / missing tool parser flags / Ollama vs vLLM endpoint shape difference). Make sure to use this skill whenever the user says "DGX endpoint check", "vLLM healthcheck", "SGLang healthcheck", "Ollama healthcheck", "local LLM probe", "/v1/models 探针", "DGX vLLM 是否可达", "LLM_BASE_URL 验证", "local-openai-compat 探活", "endpoint reachable", "LLM probe DGX", "DGX vLLM endpoint test", "本地 LLM 探针", or "LLM provider 切换后探活" in the mj-agent context. Do not use for: Ark endpoint healthcheck (Ark is probed implicitly by ChatOpenAI lazy init + `mj-agent check`; no /v1/models probe needed because ARK_API_KEY validation is sufficient); Studio probe + 5-walkthrough matrix (use mj-agent-infra-studio-probe); biz pg connectivity check (use mj-agent-infra-storage-stack troubleshooting or `mj-agent check`); Docker compose lifecycle (use mj-agent-infra-docker-compose); env / secret 配置 (use mj-agent-infra-env-setup); modifying LLM provider code in src/mj_agent/llm.py (that is C-flavor infra change; use /mj-agent-flow-implement); deploying or operating the LLM serving container itself (out of mj-agent governance — LLM serving deployment 责任另议).
---

# mj-agent Infra — LLM Endpoint Probe

## Overview

4-step health probe for the OpenAI-compatible local LLM endpoint that mj-agent consumes when `LLM_PROVIDER=local-openai-compat` (ADR-027 + PR-2 of multi-env+DGX+MCP bundle).

DGX-Spark (192.168.0.189) is the team's local LLM compute node — vLLM / SGLang / Ollama / TGI / llama.cpp container served by other-team / dedicated-repo (deployment责任另议). mj-agent only consumes the endpoint via `LLM_BASE_URL` + `LLM_API_KEY`. This skill verifies reachability + correct model + 1-token chat + tool-calling **before** mj-agent runtime depends on it.

**Stage 10 sub** of the 17-stage 执行闭环；典型在 self-review 前用于 `LLM_PROVIDER=local-openai-compat` 模式的 endpoint 验证；与 `mj-agent-infra-studio-probe` 互补（Studio 测 graph 行为，本 skill 测纯 LLM endpoint）。

## When to Use

**MUST run when**：
- 用户说 "DGX endpoint 健康 / vLLM 健康 / SGLang 健康 / Ollama 健康 / local LLM 探针"
- `.env` 中 `LLM_PROVIDER` 从 `ark` 切到 `local-openai-compat` 时（首次切换必须探活）
- DGX vLLM 容器重启后 / 新镜像部署后
- mj-agent runtime 报 `OpenAIError: Connection refused` / `model not found` / `extra_body unsupported`
- `/mj-agent-infra-studio-probe` 失败且根因可能是 LLM endpoint

**MAY skip when**：
- `LLM_PROVIDER=ark`（Ark 通过 ChatOpenAI lazy init 自动报错；`mj-agent check` 已覆盖）
- LLM endpoint 已用 `mj-agent check` 通过且最近未改动

**MUST NOT use for**：
- ❌ Ark endpoint 探活（Ark 只需 `mj-agent check` 验证 `ARK_API_KEY`；无 `/v1/models` 端点契约）
- ❌ Studio + R1/R2 数据边界测试 → `/mj-agent-infra-studio-probe`
- ❌ biz pg 连通 → `/mj-agent-infra-storage-stack` 或 `mj-agent check`
- ❌ docker compose 启停 → `/mj-agent-infra-docker-compose`
- ❌ 修改 `src/mj_agent/llm.py` factory 逻辑 → `/mj-agent-flow-implement`
- ❌ 部署 / 运维 LLM serving 容器（out-of-scope；mj-agent 仅消费侧）

## Workflow

### 执行：脱敏脚本探针（Step 0-3b 一次跑全）

任一执行者（Claude Bash tool / Codex / user 终端）统一调用：

```powershell
powershell.exe -NoProfile -File scripts/probe_llm_endpoint.ps1
# pwsh 亦可：pwsh -NoProfile -File scripts/probe_llm_endpoint.ps1
# 输出：STEPn PASS|FAIL|WARN|NOT-APPLICABLE 逐行 + VERDICT 收尾
# exit 0 = 全 pass（或 provider=ark 不适用）；3 = tool-calling 警告；2 = 配置缺失；1 = 探针失败
```

脚本内部读 `.env`（`LLM_PROVIDER` / `LLM_BASE_URL` / `LLM_MODEL_ID` / `LLM_API_KEY`）并组装请求；对调用方只输出键名、`set|EMPTY` 状态、每步判定与截断响应片段——**凭据值永不回显**。Agent 不得自行读取 `.env` / 进程环境组装 curl 请求（v5 §5.2 secrets 边界）。以下 Step 0-3b 小节解释脚本各步判定与排障动作。

### Step 0: Pre-check（脚本 STEP0 行）

- `STEP0 NOT-APPLICABLE` → `LLM_PROVIDER=ark`，无需 endpoint 探活（`mj-agent check` 已覆盖）
- `STEP0 FAIL LLM_BASE_URL/LLM_MODEL_ID EMPTY/MISSING` → STOP；先 `/mj-agent-infra-env-setup` 或手填 `.env` 后重跑

### Step 1: Endpoint Reachability + /v1/models（脚本 STEP1 行）

脚本探 `GET $LLM_BASE_URL/models`（vLLM / SGLang / TGI / llama.cpp 的 OpenAI-compatible 路径）；`LLM_BASE_URL` 含 `:11434` 时自动 fallback 到 Ollama `/api/tags`。

判定：

| 返回 | 含义 | 行动 |
|---|---|---|
| 200 + JSON 含 `data: [...]`（vLLM/SGLang）或 `models: [...]`（Ollama） | endpoint 可达 + 服务健康 | → Step 2 |
| Connection refused | endpoint 未启动 / 防火墙 / 错误端口 | troubleshoot：检查 vLLM 容器状态、`192.168.0.189:8000` 是否可 telnet |
| 404 | 路径错（vLLM 不应在 `/v1/models` 404） | LLM_BASE_URL 末尾应是 `/v1`，不是 `/v1/` 或裸 host |
| 401 | 需 API key | LLM_API_KEY 必填（vLLM 用 `--api-key` 启动时） |
| timeout | 网络 / DGX 主机 down | LAN 探：`Test-NetConnection 192.168.0.189 -Port 8000` |

### Step 2: Model ID Match（脚本 STEP2 行）

脚本从 `/models` 响应提取 model id 列表比对 `LLM_MODEL_ID`：命中 → 模型已加载 + id 匹配；无匹配 → `STEP2 FAIL` 并列出 endpoint 实际加载的所有 model ids（建议 `.env` 改 `LLM_MODEL_ID` 或 serving 侧改 `--model`）。

### Step 3: 1-Token Chat Completion Smoke（脚本 STEP3 行）

脚本发最小 chat 调用（1 token max；**不带 extra_body**——vLLM/SGLang/Ollama 不支持 Ark thinking 参数）。失败模式：

- 400 invalid params → 检查 model id / messages 结构
- 422 → vLLM/SGLang 严格 schema；可能 max_tokens 字段名差异（应 `max_tokens` 不是 `max_completion_tokens`）
- 500 → vLLM 模型加载失败 / OOM；查 vLLM 容器日志

判定：

| 返回 | 含义 | 行动 |
|---|---|---|
| 200 + valid JSON 含 `choices[0].message.content` | endpoint + 模型 + chat 全 OK | → Step 3b |
| 任何 4xx / 5xx | smoke fail | 详查响应 body；troubleshoot 见上 |

### Step 3b: Tool-calling Smoke

mj-agent runtime 把 `ALL_TOOLS` 全量绑定进 `create_agent`（清单见 `src/mj_agent/tools/__init__.py`）——endpoint 只过 Step 3 chat 而无 tool-calling 时，graph 实际不可用。本步用最小 tools 数组验证 tool-calling 能力。

脚本主路径用**默认 auto tool choice**（贴 `create_agent` 生产路径）+ prompt 强引导 + 低 temperature：单 function schema（`get_current_time`，含 required 参数 `timezone`——零参工具 `arguments="{}"` 信号弱）；max_tokens 给足 tool-call JSON（128，非 Step 3 的 1-token 风格）；**不带 extra_body**。

断言（全部成立才记 ✅，脚本 `STEP3B PASS`）：

- `choices[0].finish_reason == "tool_calls"`
- `choices[0].message.tool_calls[0].function.name` 是合法工具名（本例 `get_current_time`）
- `choices[0].message.tool_calls[0].function.arguments` 可 JSON 解析且含 required 参数（`timezone`）

**判别重试**：auto 路径无 tool_call 时，脚本自动同 payload 追加 `"tool_choice": {"type": "function", "function": {"name": "get_current_time"}}` 补发**一次**（named/guided decoding 不依赖 `--enable-auto-tool-choice`，可区分 parser 缺失与模型能力缺失）：

| auto | named | 判定 | 输出 |
|---|---|---|---|
| ✅ | （不补发） | tool-calling 可用 | → Step 4 |
| ❌ | ✅ | endpoint 未开 tool parser | ⚠ 兼容性警告：serving 侧需 vLLM `--enable-auto-tool-choice --tool-call-parser <模型族>`（见 §Troubleshooting） |
| ❌ | ❌ | 模型不具备 tool-call 能力 | ⚠ 兼容性警告：该模型不适配 mj-agent（ALL_TOOLS 硬依赖）；换模型走 dgx-mlops HITL-MODEL |

两类失败均输出**兼容性警告**而非硬失败——probe 报告照常产出 4 步全量结果（Verdict 降级为 ⚠）。

### Step 4: Output

```markdown
## LLM Endpoint Probe Report

### Configuration
- LLM_PROVIDER = local-openai-compat
- LLM_BASE_URL = <url>
- LLM_MODEL_ID = <id>
- LLM_API_KEY  = <set|EMPTY>

### Step 1: Reachability
- ✅ /v1/models returned 200 (or fallback /api/tags for Ollama)
- Endpoint type detected: vLLM | SGLang | Ollama | TGI | llama.cpp | unknown

### Step 2: Model ID Match
- ✅ <LLM_MODEL_ID> found in endpoint's loaded models
- (or) ❌ <LLM_MODEL_ID> NOT in [list] — actions: change .env LLM_MODEL_ID or restart server with correct --model

### Step 3: Chat Smoke
- ✅ 1-token chat returned: <truncated content>

### Step 3b: Tool-calling
- ✅ auto tool choice: finish_reason=tool_calls + valid function.name + parseable arguments
- (or) ⚠ auto ❌ / named ✅ — endpoint 未开 tool parser（vLLM 需 --enable-auto-tool-choice --tool-call-parser）
- (or) ⚠ auto ❌ / named ❌ — 模型不具备 tool-call 能力（mj-agent ALL_TOOLS 硬依赖；→ dgx-mlops HITL-MODEL）

### Verdict
- ✅ ALL pass — `mj-agent serve` should work with current LLM provider config
- (or) ⚠ PASS with tool-calling warning — Step 1-3 通过但 Step 3b 兼容性警告（mj-agent runtime 不可用：先开 tool parser 或换模型）
- (or) ❌ FAIL at Step <n> — see Troubleshooting

### Next
- → /mj-agent-infra-studio-probe (verify graph behavior end-to-end)
- → mj-agent serve (Chainlit UI on host:8001)
```

## §Troubleshooting

| 症状 | 可能原因 | 修复 |
|---|---|---|
| Connection refused @ Step 1 | vLLM 容器未启 / 端口错 / DGX 主机不可达 | (a) SSH DGX 查容器 `docker ps`；(b) `Test-NetConnection 192.168.0.189 -Port 8000` 测端口；(c) 检查 LLM_BASE_URL host 与 port |
| 404 @ /v1/models | LLM_BASE_URL 路径错 | 末尾应是 `/v1` 不是 `/v1/` 或裸 host；vLLM 标准路径 `http://<host>:8000/v1` |
| 401 unauthorized | LLM 服务启用了 --api-key 但 .env LLM_API_KEY 未设 | 与 vLLM 部署方对齐 token 值，填入 .env LLM_API_KEY |
| Step 2 model id 不匹配 | vLLM `--model meta-llama/Llama-3-70B` 与 .env `LLM_MODEL_ID=deepseek-v3-2-251201` 不一致 | (a) 改 .env LLM_MODEL_ID 对齐 vLLM 实际 load 的 model；(b) 或要求 vLLM 改 --model；mj-agent 不强制单一 model |
| Step 3 422 with `extra_body unsupported` | mj-agent llm.py 在 local-openai-compat 路径误传 `extra_body.thinking` | 检查 `src/mj_agent/llm.py` `make_llm()` local 分支不应含 extra_body（PR-2 设计已修；此为 regression 信号）|
| Step 3 500 model load failed | vLLM 模型权重缺失 / OOM | SSH DGX 查 vLLM 容器日志；mj-agent 侧无修复手段 |
| Step 3b auto 路径无 tool_calls（named 可通） | endpoint 未开 tool parser | vLLM 启动加 `--enable-auto-tool-choice --tool-call-parser <模型族>`（如 hermes / llama3_json / deepseek_v3；flag 拼写以执行时 vLLM 版本 tool_calling 文档为准）；SGLang / Ollama 查各自 tool-call 开关 |
| Step 3b 422 或 tools 字段被忽略 | serving 层不支持 / 未启用 tools | 查 serving 启动参数与版本（OpenAI-compat 层须支持 tools）；vLLM 同上行 flag |
| Step 3b auto + named 双败（持续无 tool_call） | 模型不具备 tool-call 能力 | 该模型不适配 mj-agent（ALL_TOOLS 硬依赖，清单见 `src/mj_agent/tools/__init__.py`）；换模型走 dgx-mlops HITL-MODEL |
| Ollama 走 /v1/models 返 404 | Ollama 默认不开 OpenAI compatible 模式 | Ollama 启动加 `OLLAMA_HOST=0.0.0.0:11434 ollama serve`；本 skill Step 1 fallback 自动探 /api/tags |

## What This Skill DOES NOT DO

- ❌ 不替代 /mj-agent-infra-env-setup（env / secret 配置）
- ❌ 不替代 /mj-agent-infra-studio-probe（graph 行为 + R1/R2 数据边界）
- ❌ 不替代 mj-agent check（biz DB + memory DB + provider creds 完整 healthcheck）
- ❌ 不修改 `.env` LLM_PROVIDER / LLM_BASE_URL（仅 read-only 探针）
- ❌ 不修改 `src/mj_agent/llm.py` factory（C 风味 infra；用 /mj-agent-flow-implement Step 3c）
- ❌ 不操作 LLM serving 容器（out-of-scope；deployment 责任另议）
- ❌ 不在 ark provider 模式下生效（Ark 无 /v1/models 端点契约；用 mj-agent check 替代）

## Sub-skill / Tool Calls

| Tool | 用途 |
|---|---|
| Bash `powershell.exe -NoProfile -File scripts/probe_llm_endpoint.ps1` | Step 0-3b 全量探针（脚本内部读 `.env` + 组装请求；对外只回脱敏诊断） |
| Bash `powershell.exe -NoProfile -Command 'Test-NetConnection ...'` | Step 1 FAIL 后的端口连通性排障 |

## Reference Files

- [[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]]（PR-Γ 落地；LLM provider 抽象决策）
- [[../../../src/mj_agent/llm.py|src/mj_agent/llm.py]]（make_llm() factory；ark vs local-openai-compat 分支）
- [[../../../src/mj_agent/config.py|src/mj_agent/config.py]]（llm_provider / llm_base_url / llm_api_key + effective_llm_* cached_property）
- [[../../../src/mj_agent/tools/__init__.py|src/mj_agent/tools/__init__.py]]（ALL_TOOLS 清单；Step 3b tool-calling 硬依赖的事实源）
- [[../../../src/mj_agent/server/cli.py|cli.py]]（mj-agent check provider-aware；与本 skill 互补）
- [[../../../docs/guide/[GUIDE]_Developer_Onboarding|Developer Onboarding]] §7（端到端 5 项验证；LLM 是 H1/H2/H3 happy path 前置条件）
- [[../../../sdd/workflows/execution-loop|sdd/workflows/execution-loop]]（Stage 10 Local Verification；原 HITL_Prompt §4.10，M6 PR4 archived → kernel）
- vLLM docs: https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html
- vLLM tool calling: https://docs.vllm.ai/en/stable/features/tool_calling.html
- Ollama OpenAI compat: https://github.com/ollama/ollama/blob/main/docs/openai.md
- mj-system upstream `.claude/skills/mj-sys-ops-env-setup`（间接派生源；mj-agent 简化为单一 endpoint 探针，不含 mj-system 多 SSH 编排）

## Anti-patterns

- ❌ 不在 `LLM_PROVIDER=ark` 模式下跑（Ark 无 /v1/models 端点契约；strict 探针无意义）
- ❌ 不带 `-m` timeout 跑 curl（DGX 不可达时会挂死）
- ❌ 不在 Step 3 chat smoke 带 `extra_body`（vLLM/SGLang/Ollama 不接受；探针应 mirror llm.py local 分支行为）
- ❌ 不在 Step 3b tool-calling smoke 带 `extra_body`（同 Step 3；探针 mirror llm.py local 分支行为）
- ❌ Step 3b 不超 1 次工具往返（断言 tool_calls 产生即止；不执行工具、不回传 tool result、不做 agent loop）
- ❌ 不修复 LLM serving 容器问题（out-of-scope；troubleshoot 仅给客户端侧建议）
- ❌ 不用 production model 跑 smoke 时 `max_tokens` 忘 cap（DGX 算力宝贵；冒烟用 1 token，tool-calling 用 ≤128）

## Handoff

```
LLM endpoint probe 完成
下一步：
- 全 pass → /mj-agent-infra-studio-probe (graph 行为 + R1/R2)
- Step 1 fail → SSH DGX 排查 vLLM 容器 / 网络
- Step 2 fail → 改 .env LLM_MODEL_ID 或对齐 vLLM --model
- Step 3 fail → 检查 src/mj_agent/llm.py local 分支不带 extra_body
- Step 3b warning → serving 侧加 tool parser flag（vLLM --enable-auto-tool-choice --tool-call-parser）或换模型（dgx-mlops HITL-MODEL）
- 准备 dev → mj-agent serve (Chainlit on host:8001)
```
