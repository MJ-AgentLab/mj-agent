---
type: decisions-index
summary: Index of mj-agent architecture decision records in decisions/; superseded ADRs live under archive/decisions/superseded/.
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-13
track: shared
ai_visibility: source-of-truth
---

# decisions/ INDEX

> ✅ 平移完成 (M5-PR3a, 2026-06-03)：原 `docs/adr/` 20 个 active ADR 已 `git mv`
> 至本目录（per-file RENAME `[ADR]_NNN_*` → `ADR-NNN_*`），全仓 living 引用同步改写。
> 本 INDEX 当前为手工维护；Phase M5+ 末转由 `scripts/sdd/generate_index.py` 自动维护.

## Active ADRs

| ADR | Domain | Decision (state) | Summary |
|---|---|---|---|
| [ADR-000_Data_LLM_Boundary_Principles.md](./ADR-000_Data_LLM_Boundary_Principles.md) | DATA | accepted (active) | 最小必要出网、通道隔离、工具中介——后续所有安全相关决策的理论基础 |
| [ADR-001_Python_Only_Agent_Runtime.md](./ADR-001_Python_Only_Agent_Runtime.md) | SYS | accepted (active) | Agent 逻辑、tools、skills、memory 全部留在 Python；前端仅作通信与渲染 |
| [ADR-002_Skills_As_First_Class_Citizens.md](./ADR-002_Skills_As_First_Class_Citizens.md) | SKILL | accepted (active) | 所有专业能力以 skills/{name}/SKILL.md 格式封装，对齐 Claude Code skills 约定 |
| [ADR-003_Progressive_Disclosure.md](./ADR-003_Progressive_Disclosure.md) | PROMPT | accepted (active) | 全局 system prompt 只含身份与原则；具体能力按需加载 |
| [ADR-006_Fail_Safe_Reads.md](./ADR-006_Fail_Safe_Reads.md) | GUARDRAIL | accepted (active) | biz 库访问用只读账号 + SQL guardrail middleware 双层保护，四层防御 |
| [ADR-008_Co_Deployment_With_Upstream_Warehouse.md](./ADR-008_Co_Deployment_With_Upstream_Warehouse.md) | OPS | accepted (active) | mj-agent 是独立的 compose project（自带 postgres + redis 存储栈），通过 `mj-system-backend-network` 接入上游 |
| [ADR-009_Biz_Domain_As_Primary_Data_Source.md](./ADR-009_Biz_Domain_As_Primary_Data_Source.md) | INTEGRATION | accepted (active) | mj-agent 仅通过只读账号访问 biz 域，不访问 ODS/DWD 原始层 |
| [ADR-011_Doc_Versioning_And_Archive_Convention.md](./ADR-011_Doc_Versioning_And_Archive_Convention.md) | SYS | accepted (active) | 文档治理新增 Major.Minor 版本演进与 docs/archive/ 归档机制（HITL 触发） |
| [ADR-012_Two_Track_Documentation_Governance.md](./ADR-012_Two_Track_Documentation_Governance.md) | SYS | accepted (draft) | 引入双轨文档治理（Code_Side + Agent_Side + Meta 元层）+ skeleton-first 演进 |
| [ADR-013_Plugin_SKILL_md_Schema_Separation.md](./ADR-013_Plugin_SKILL_md_Schema_Separation.md) | SYS | accepted (draft) | marketplace plugin SKILL.md 使用 Claude Code 原生 schema（name + description），与 in-source schema 分离 |
| [ADR-014_Tri_Track_Documentation_Governance.md](./ADR-014_Tri_Track_Documentation_Governance.md) | SYS | accepted (active) | 引入第三轨 engineering-workflow（治理 .claude/ + HITL_Prompt + 工程流程 STANDARD）；A12-A14 门禁 |
| [ADR-016_In_Tree_Claude_Skills_Ecosystem.md](./ADR-016_In_Tree_Claude_Skills_Ecosystem.md) | WORKFLOW | accepted (active) | .claude/skills/ in-tree 工程编排技能命名空间 mj-agent-<group>-<verb>（5 family） |
| [ADR-020_Archive_Auto_Discovery.md](./ADR-020_Archive_Auto_Discovery.md) | SYS | accepted (active) | scripts/check_wikilinks.py 改为 auto-discover NEEDLES from 归档目录 [DEPRECATED]_*.md glob |
| [ADR-024_Eval_Framework_Spec.md](./ADR-024_Eval_Framework_Spec.md) | AGENT | accepted (active) | Agent_Side v1.1 → v1.2 archive ceremony；§4 EVAL Authoring 完整规范（4 子类 + body 八段） |
| [ADR-026_Multi_Environment_Compose_Profile.md](./ADR-026_Multi_Environment_Compose_Profile.md) | OPS | accepted (active) | docker-compose 4-file 分层 (base + override + test + prod) 实现 dev/test/prod 三环境部署 |
| [ADR-027_LLM_Provider_Abstraction.md](./ADR-027_LLM_Provider_Abstraction.md) | AGENT | accepted (active) | src/mj_agent/llm.py make_llm() 抽象为 provider 分支 factory（ark + local-openai-compat），支持 DGX-Spark |
| [ADR-028_MCP_Server_Inventory_And_Governance.md](./ADR-028_MCP_Server_Inventory_And_Governance.md) | WORKFLOW | accepted (active) | 引入 .mcp.json 13 servers + 新建 MCP_Server_Governance STANDARD |
| [ADR-029_Tool_Error_Surfacing_To_LLM.md](./ADR-029_Tool_Error_Surfacing_To_LLM.md) | AGENT | accepted (active) | SQL 工具异常通过 @wrap_tool_call 中间件转换为 ToolMessage，使 LLM 自纠正而非 graph 崩溃 |
| [ADR-030_Secrets_Bundle_Split_For_MCP_Isolation.md](./ADR-030_Secrets_Bundle_Split_For_MCP_Isolation.md) | OPS | accepted (active) | 把 MCP 基础设施 secrets（5 SSH + 10 PG URL）拆出到独立的 config/secrets-mcp.enc |
| [ADR-031_Spec_Anchored_Refactor.md](./ADR-031_Spec_Anchored_Refactor.md) | SYS | accepted (active) | mj-agent Maximum Spec-Anchored Refactor — Phase M0-M6 路线图 + 10 RD 矩阵 + 7 adapter 启用清单 |
| [ADR-032_Claude_Skill_Schema_Monitoring.md](./ADR-032_Claude_Skill_Schema_Monitoring.md) | WORKFLOW | accepted (active) | 为 .claude/skills/ ADR-013 native 2-field schema 建立 3-layer monitoring regime |
| [ADR-033_DGX_Ops_Sister_Repo_Boundary.md](./ADR-033_DGX_Ops_Sister_Repo_Boundary.md) | OPS | accepted (active) | DGX serving/ops 归独立姊妹仓 dgx-mlops；mj-agent 唯一 consumer、不在 DGX 部署、仅经 ADR-027 provider 抽象消费；跨仓 cross-ref ≤5（自设预算） |
| [ADR-034_HITL_Propose_Decide_Apply_Model.md](./ADR-034_HITL_Propose_Decide_Apply_Model.md) | WORKFLOW | accepted (active) | HITL 改「AI 提议 → Owner 拍板 → AI 落盘」；4 项 in-source 专属必停 deny→ask 逐写拍板门 + A13/A14 合并审查兜底；protected paths（.claude/** / .mcp.json）AI 改 + harness 强制 prompt 即拍板；runtime-* read-only → propose→拍板→apply；新增 External-Info Handoff；仅交互模式成立（auto classifier 硬拦放宽类）。supersede ADR-015 §决策点 4 残留 |
| [ADR-035_Codex_Full_Development_Participant.md](./ADR-035_Codex_Full_Development_Participant.md) | WORKFLOW | accepted (active) | Codex 由「只读外部评审 / 非参与」升为完整开发参与者（可运行命令 + 编辑/提交/迁移，受同一 HITL 必停 + 数据边界）；revise ADR-031 Phase M0 native 内容；数据边界 ADR-006/009/000 不变。**2026-07-06 amendment**：澄清两类使能——(A) standalone Codex（AGENTS.md 治理）已开、(B) Claude-Code-调用-Codex 插件仍延后；(A) 的 5 必停/数据边界 = AGENTS.md self-enforced prose（Codex 自守，mj-agent 技术门不约束）|
| [ADR-036_Dual_Agent_Thin_Adapter_And_Projection.md](./ADR-036_Dual_Agent_Thin_Adapter_And_Projection.md) | WORKFLOW | accepted (active) | 收录 dual-agent-compat v5 决策集 D-001~D-017：项目内 Kernel + 薄 adapter + manifest（sdd/development-agent.yml）+ V8/V9 checker + scoped 投影生成器 agents_sync（唯一豁免，仅 .agents/skills/ 与 .codex/config.toml）；产物入仓不可手改（--adopt 反灌）；MCP per-server 三档且 biz×5 + ssh-manager 永不投影；D-017 扩 A14 anchor 至派生面；canonical 10-enum 不变 |
| [ADR-037_Memory_PG_MCP_Projection_To_Codex.md](./ADR-037_Memory_PG_MCP_Projection_To_Codex.md) | WORKFLOW | accepted (active) | 授权把 mj-agent 自有 memory PostgreSQL MCP servers（pg-mj-agent-memory-*×5）投影进 Codex（`project-with-adr`→`project`，dual-agent-compat 议题 1）；memory 独立库 + 独立凭据、checkpoint 确含 biz 派生行但读它无法触达 biz 表 / 绕 L1/L1b；凭据经 env_vars 按名、零字面入仓（G7/PJ044）；biz×5 + ssh-manager 永 never；可逆（翻回 + re-sync） |
| [ADR-038_Memory_Checkpoint_At_Rest_Desensitization.md](./ADR-038_Memory_Checkpoint_At_Rest_Desensitization.md) | DATA | accepted (active) | memory checkpoint 中 execute_sql 逐字 biz 派生行的 at-rest 脱敏方向（ADR-037 后继）；Owner 两裁定 = Ruling 1 store-at-rest 最小化（ADR-037 投影维持）+ Ruling 2 机制 B（persist-time 确定性 per-column 摘要 + 留 executed_sql、可选叠 C TTL）；不放宽 ADR-006/009/000 数据边界；实现递延 #365 |
| [ADR-039_Codex_Cross_Carrier_Kernel.md](./ADR-039_Codex_Cross_Carrier_Kernel.md) | WORKFLOW | accepted (active) | 以单一 Epic、18 个严格串行 PR 与人工 merge barrier 闭合 Claude–Codex cross-carrier Agent Kernel；定向 revise ADR-036 D-011/D-012/D-014，其余边界保持不变 |

## Deprecated / Superseded ADRs

> M5-PR3b 完成：9 个 deprecated ADR（010 / 015 / 017-019 / 021-023 / 025）已由 `docs/archive/adr/`
> 平移至 `archive/decisions/superseded/`（+ `archive.yml` 清单 + `TOMBSTONE.md`；forward gateway 见
> [[archive/decisions/superseded/INDEX|archive/decisions/superseded/INDEX]]）.

## Archive Cross-Reference

详 `archive/decisions/` + `archive.yml` 字段（详 `sdd/archive.schema.json`）.

---

> *现 28 个 ADR 手工收录（23 前收录 + ADR-035/036/037/038/039）.* Phase M5+ 平移收尾时本 INDEX 转为自动生成.
