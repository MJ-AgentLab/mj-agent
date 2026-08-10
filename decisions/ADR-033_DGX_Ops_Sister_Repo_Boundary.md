---
type: adr
domain: OPS
summary: DGX-Spark serving/ops 由独立姊妹仓 MJ-AgentLab/dgx-mlops 治理；mj-agent 是唯一 DGX consumer、不在 DGX 部署、仅经 ADR-027 provider 抽象消费 OpenAI-compat endpoint；跨仓 cross-ref 总数 ≤5（mj-agent 自设预算；计数单位 = 受治理跨仓锚点，2026-08-10 拍板）
owner: 项目负责人
created: 2026-06-11
updated: 2026-08-10
state: active
decision: accepted
track: shared
tags:
  - adr
  - dgx
  - dgx-mlops
  - sister-repo
  - boundary
  - llm-provider
---

# ADR-033: DGX Ops Sister-Repo Boundary

## Context

DGX-Spark (192.168.0.189) 实机就位，作为团队本地 LLM 算力节点；其 LLM serving（vLLM / SGLang / Ollama）与运维（驱动 / 容器 / 模型管理 / 监控）需要明确治理归属。

mj-agent 侧既有决策已确立纯消费侧立场：

- [[decisions/ADR-026_Multi_Environment_Compose_Profile|ADR-026]]（Multi-Environment Compose Profile）正文 2026-05-09 项目负责人决策句："DGX (192.168.0.189) 仅作算力节点，**不部署任何应用服务（含 mj-agent）**"——DGX 支持本质是 LLM provider 抽象，不引入 dgx profile
- [[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]]（LLM Provider Abstraction）：`make_llm()` provider 分支 factory，`LLM_PROVIDER=local-openai-compat` 即可消费任何 OpenAI-compat endpoint
- 二者为原 ADR-025（已 archive）拆分姊妹

外部驱动：2026-06-11 dgx-mlops 治理批次（r1-r3）项目负责人决策建立独立姊妹仓 `MJ-AgentLab/dgx-mlops` 治理 DGX serving/ops（M0-M7 分阶段 + D0-D7 硬件验证）。mj-agent 仓内需要一份边界决策记录，固化双仓职责分界、防止跨仓渗透，并为 dgx-mlops 侧 `capabilities/mj-agent/llm-provider-bridge/` 消费方契约预留 cross-ref 槽位。

## Decision

1. **DGX serving / ops 归姊妹仓**：DGX-Spark 的 LLM serving 与运维（驱动 / 容器 / 模型部署 / 监控 / 评测底座）由独立姊妹仓 **`MJ-AgentLab/dgx-mlops`** 治理；mj-agent 仓不承载任何 DGX serving/ops 资产。
2. **mj-agent 是唯一 DGX consumer**（当前阶段）：消费路径唯一——经 [[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]] provider 抽象（`LLM_PROVIDER=local-openai-compat` + `LLM_BASE_URL` + `LLM_MODEL_ID` 覆写；默认 `LLM_MODEL_ID` 是 Ark 云 id，切换时必须覆写）。
3. **DGX 不部署 mj-agent**：重申 ADR-026 正文 2026-05-09 决策句；`Profile` enum 维持 `dev|test|prod` 不扩 dgx——DGX 是 LLM-endpoint switch，不是 deploy target。
4. **跨仓反耦合预算**：dgx-mlops ↔ mj-agent 文档 cross-ref 总数 **≤ 5**（**mj-agent 自设约束**，非上游文档要求；防双仓互相渗透、保持各自可独立演进）；mj-agent 仓不存放任何 dgx-mlops 侧 secrets / runner 凭证；mj-agent 不替 dgx-mlops 执行任何 M/D-phase。

   **计数口径**（计数单位 2026-08-10 项目负责人拍板，issue #460；沿用并明确化 2026-07-01「语义 cross-ref」拍板，`plans/[PLAN]_255_dgx-cross-ref-t1.md` Task 4）：

   - **计数单位 = 受治理跨仓锚点（governed cross-repo anchor）** —— 既不是承载指针的文档份数，也不是指针出现次数。一个锚点 = 一处经 **HITL-CROSS**（双仓 owner 双签 + 双侧 PR）确立的受治理绑定所落成的 canonical 段落；双仓各自的锚点段落分别计 1（正向锚点与反向锚点各计各）。**只有绑定才产生锚点**——未经 HITL-CROSS 确立的提及一律不计（见下「不计」）。因此预算 ≤ 5 的实际含义是：双仓被契约钉死的位置总数不超过 5 处。
   - **通道折算**：dgx-mlops `capabilities/mj-agent/llm-provider-bridge/` 整体折算为**单一受管通道**（Decision 1 / Decision 2 指定的唯一耦合面），其内部文件之间以及对 mj-agent 的引用不逐份计入。
   - **不计**：自动生成的 INDEX 行 / CHANGELOG 历史条目 / 运维 SKILL 提及 / 对 mj-agent 代码 · `.env` · runtime 符号的提及（非文档指针）/ **非绑定性引用** —— 如 dgx-mlops `ADR-001` `ADR-003` 引本 ADR 作先例，引用不建立耦合、不计入。
   - **当前值 3 / 5**（2026-08-10 复核）：[[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]] §Cross-ref · 本 ADR §Cross-ref 槽位 · dgx-mlops `ADR-023-m7-phase2-e2e` 反向 anchor。

## Cross-ref 槽位（T-1 已填实 2026-06-29）

dgx-mlops `capabilities/mj-agent/llm-provider-bridge/` contract ID 集合：
- **PRIMARY（mj-agent 绑定）**：`CTR-AGENTOUT-001`（输出 schema）+ `CTR-BRIDGE-001`（跨仓 API 契约）
- **informational（追溯，不绑定）**：`CTR-VLLM-001`（vLLM served-model）+ `CTR-HEALTH-002`（`/health` 200）

cross-ref 状态 = **active**（2026-07-03；[[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]]
§Cross-ref 段；真实 e2e（T-5）已跑通，dgx-mlops `ADR-023-m7-phase2-e2e` / 分支 `feature/m7-phase2-e2e-closure`）。

## 跟踪锚点（T-1 / T-2 / T-5）

| 锚点 | 触发条件 | mj-agent 侧动作 | 形态 |
|---|---|---|---|
| **T-1** | dgx-mlops M2c（bridge contract draft 产生实 ID） | ADR-027 增 cross-ref 段 + 本 ADR 槽位填实 | documentation PR |
| **T-2** | dgx-mlops M4 末（中段同步） | 双方核对 cross-ref ID 一致性；无 drift 零改动，有 drift 走 documentation PR | 核对 +（条件）PR — ✅ done 2026-07-03（#255 comment；零 drift @ dgx-mlops `72933bb`） |
| **T-5** | dgx-mlops Phase 2 M7（真实 e2e 跑通） | cross-ref 状态 pending → active；是否在 `tests/integration` 加 e2e 标记用例由当批 HITL 决定 | 跨仓集成 +（条件）PR — ✅ done 2026-07-03 PR #274（e2e 标记用例：本批 HITL 决定不加，见 PR body） |

> T-3（dgx-mlops D7 readiness assessment 双签）与 T-4（model-id 选定后 `.env` 切换演练）为跨仓 HITL / 运维动作，无本仓 PR 面；全量定义见项目负责人 vault 执行计划 `[PLAN]_mj-agent_DGX_Consumer_Side_Execution.md` v1.1 §2。

## Consequences

- **正面**：职责单一——mj-agent 保持纯消费侧（provider 抽象已就位；endpoint probe 已含 tool-calling smoke，PR #254）；dgx-mlops 独立演进不牵动 mj-agent CI / 治理；跨仓耦合有显式预算可审计
- **负面**：跨仓同步点（T-1/T-2/T-5）依赖人工触发——锚点登记于本 ADR + GitHub issue，防止触发项只活在 vault 而蒸发；contract ID 在 dgx-mlops M2 前是占位
- **中性**：`.mcp.json` ssh-manager 已含 DGX LAN/WAN 条目（运维通道，与 LLM 消费正交，per [[decisions/ADR-028_MCP_Server_Inventory_And_Governance|ADR-028]]）；T-4 演练是 dev `.env` 临时运维动作非 PR（持久切换走 ADR-030 secrets.enc 管道）

## Alternatives considered

- **A. DGX ops 并入 mj-agent 仓（monorepo 化）**：拒绝。serving/ops 资产（CUDA / 驱动 / aarch64 镜像 / runner）与 data-agent 业务无共享 CI / 依赖面；并仓会把硬件迭代噪声引入 mj-agent 治理
- **B. DGX ops 并入上游 mj-system**：拒绝。DGX 服务对象是 mj-agent 的 LLM 消费（现阶段唯一 consumer）；mj-system 是数据仓侧，边界更远
- **C. 不立仓、临时脚本管理**：拒绝。dgx-mlops 已规划 M0-M7 治理（项目负责人 2026-06-11 批次决策）；临时态会让 serving 配置无 source of truth
- **D. `Profile` enum 扩 dgx**：已被 ADR-026 / ADR-027 否决（DGX 不部署 mj-agent；endpoint switch 非 profile）
- **E. 计数单位取「承载指针的文档份数」**（Decision 4 计数口径的备选，2026-08-10 评估）：拒绝。字面支持度最高，但按此读法实测 **16 份**（mj-agent 3 + dgx-mlops 13），当场超 ≤5 预算 3 倍——须同时上调上限或记 risk acceptance；且每次跨仓写文档都要重扫双仓才能报数，治理成本与「防渗透」的实际收益不匹配
- **F. 计数单位取「指针出现次数」**（同上批备选）：拒绝。最贴「指针」字面（逐处计），但实测 **73 处**（mj-agent 32 + dgx-mlops 41），超限 14 倍——数量型预算事实失效，只能改分层预算或废除数量约束。更关键的是：受管通道内部的密集互指恰是耦合被**正确收拢**的证据，把它计为渗透会激励拆散通道，与 Decision 1 / Decision 2 相悖

## References

- [[decisions/ADR-026_Multi_Environment_Compose_Profile|ADR-026]] — DGX 算力节点定位决策句来源；Profile enum 设计
- [[decisions/ADR-027_LLM_Provider_Abstraction|ADR-027]] — 唯一消费路径实现（`make_llm()` factory；T-1 已增 cross-ref 段，见 §Cross-ref）
- [[decisions/ADR-028_MCP_Server_Inventory_And_Governance|ADR-028]] — DGX SSH 运维通道（与 LLM 消费正交）
- [[archive/decisions/superseded/[DEPRECATED]_[ADR]_025_Multi_Environment_And_LLM_Provider_Abstraction|ADR-025（archive）]] — 历史 bundle ADR（ADR-026/027 拆分来源）
- `MJ-AgentLab/dgx-mlops`（姊妹仓）— `capabilities/mj-agent/llm-provider-bridge/` 消费方契约（`lifecycle: active` / `state: realized`，dgx-mlops PR #45 2026-07-07）
- 项目负责人 vault 执行计划 `[PLAN]_mj-agent_DGX_Consumer_Side_Execution.md` v1.1（PR-A #254 + 本 PR-B + T-1~T-5 定义）
