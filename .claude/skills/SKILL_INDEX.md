---
type: skill-index
state: active
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-07-23
track: engineering-workflow
ai_visibility: source-of-truth
---

# .claude/skills/ SKILL_INDEX — 5-Layer Dual Index

> Phase M0 — RD3=C：物理 namespace（`mj-agent-<group>-<verb>`）**不重命名**；本 INDEX 提供
> 5-layer 逻辑分层供 AI 快速定位 skill.
> active skill 实装计数以 `scripts/sdd/check_claude_skill_contracts.py --all` 为 SoT（当前
> **37**）；§1 逐家 active 列已与 §2 逻辑层对齐（flow-diagnose 回填 §2 Layer 1，#307）.

## §1 Physical Namespace（5 family；ADR-016；不重命名）

| Family | Prefix | Count（active） | Total（M6 末） |
|---|---|---|---|
| flow | `mj-agent-flow-*` | 10 | 10 |
| git | `mj-agent-git-*` | 9 | 9 |
| doc | `mj-agent-doc-*` | 6 | 6 |
| runtime | `mj-agent-runtime-*` | 4 | 4 |
| infra | `mj-agent-infra-*` | 8 | 12 (Phase 2-3 +4) |
| evidence | `mj-agent-evidence-*` | 0 | 4 (Phase 6 新增) |

## §2 Logical Layer（5 层；本 INDEX 提供）

### Layer 1: SDD 编排型（16）— flow + doc

任务触发时识别 stage / 拆分 capability scope / 撰写 plan / 验证 / self-review.

| Skill | Stage | 触发场景 |
|---|---|---|
| `mj-agent-flow-intake` | 0 Intake | 接收用户请求并拆解 issue 与 capability scope |
| `mj-agent-flow-repo-scan` | 3 Repo Scan | 任务开始前扫描仓库结构产出 RepoScanResult |
| `mj-agent-flow-plan` | 4 Plan | 撰写 / 更新 PR 级 plan 文件并对齐 capability spec |
| `mj-agent-flow-implement` | 8 Implementation | 落地 Stage 8 实施（A 代码 / B in-source canonical / C infra） |
| `mj-agent-flow-diagnose` | 8/10 邻接 | 硬 bug / 性能回归 / flaky 的纪律化诊断（红信号先行）；由 flow-implement Step 3b 委派 |
| `mj-agent-flow-verify` | 10 Verification | 跑测试 + contract / runtime 验证 |
| `mj-agent-flow-self-review` | 11 Self-review | 提交前自检 diff + plan-vs-diff 漂移 |
| `mj-agent-flow-scope-drift` | 9 Scope Drift | 检测 PR scope 偏离 plan 时触发 HITL |
| `mj-agent-flow-review-respond` | 15 Review/CI | 回应 reviewer 评论 |
| `mj-agent-flow-post-merge` | 17 Post-merge | 合并后更新 trace + evidence + 关联 plan 状态 |
| `mj-agent-doc-plan` | 4 sub | 撰写 capability requirements/design 计划 |
| `mj-agent-doc-author` | 6 | 撰写正式文档（adr/spec/runbook/assessment） |
| `mj-agent-doc-validate` | 11 sub | frontmatter / wikilink / contract 字段校验 |
| `mj-agent-doc-sync` | 8 sub | CLAUDE.md / INDEX 同步刷新 |
| `mj-agent-doc-review` | 15 sub | reviewer 视角的文档质量审查 |
| `mj-agent-doc-migrate` | archive workflow | 执行文档批量迁移 / 归档 ceremony |

### Layer 2: 工程执行型（9）— git

PR 工作流：起 issue → branch → commit → push → PR → review → merge → cleanup.

| Skill | Stage | 触发场景 |
|---|---|---|
| `mj-agent-git-issue` | 1 | 起 issue（含 archive / runtime / agent 三新类） |
| `mj-agent-git-branch` | 2 | worktree-add 新分支（5 → 11 branch type） |
| `mj-agent-git-commit` | 12 | 提交（11 commit type allowlist 检查） |
| `mj-agent-git-push` | 13 | 推送（含 G1/G2 hook enforcement 自检） |
| `mj-agent-git-pr` | 14 | 创建 PR（手册 §9.3 模板） |
| `mj-agent-git-review-pr` | 15 | review 别人的 PR |
| `mj-agent-git-check-merge` | 16 | 合并前检查（CI green / scope drift / HITL） |
| `mj-agent-git-delete` | 17 sub | 删除已合并分支 + worktree |
| `mj-agent-git-sync` | 17 sub / hotfix | 同步 develop ← main |

### Layer 3: 技术栈校验型（8 + Phase 2-3 +4）— infra + stack

Stack 启停 / 探针 / contract 反向校验.

| Skill | Phase | 触发场景 |
|---|---|---|
| `mj-agent-infra-docker-compose` | active | 3 profile compose 启动 / 切换 / debug |
| `mj-agent-infra-storage-stack` | active | mj-agent-postgres + redis 启停 + 健康自检 |
| `mj-agent-infra-llm-endpoint-probe` | active | LLM endpoint 4 步健康探针（ark / DGX；含 tool-calling smoke） |
| `mj-agent-infra-env-setup` | active | 首次 clone 后 setup-env / setup-mcp-secrets 端到端 |
| `mj-agent-infra-env-teardown` | active | 3-level safety teardown |
| `mj-agent-infra-studio-probe` | active | LangGraph Studio 启动 + 1-shot 测试问答 |
| `mj-agent-infra-app-start` | active | app runtime 有序启动（prereq→storage→check→launch→verify；slim HITL H1-H4） |
| `mj-agent-infra-app-stop` | active | app runtime 非破坏停止（host tree-kill + Level-1 down；破坏性转 env-teardown） |
| `mj-agent-stack-docker-contract` | Phase M2-M3 | docker.contract.yml + compose.contract.yml 反向校验 |
| `mj-agent-stack-compose-config` | Phase M2-M3 | docker compose config 输出 vs runtime.expected.yaml |
| `mj-agent-stack-prompt-regression` | Phase M2-M3 | system.md / SKILL.md regression eval（ADR-024 联动） |
| `mj-agent-stack-agent-eval` | Phase M2-M3 | LangChain tool schema + HITL behavior eval |

### Layer 4: 领域执行型（4；propose → 拍板 → apply）— runtime

提议 src/mj_agent/ 关键文件 diff + impact，**Owner 拍板后经 `ask` 门直接 Edit 落盘**（详
`policies/data-boundary.md` §3 4 项专属必停 + ADR-034 deny→ask）.

| Skill | 触发场景 |
|---|---|
| `mj-agent-runtime-skill-doc-improve` | 提议 `src/mj_agent/skills/*/SKILL.md` body 修改 diff（propose→拍板→apply） |
| `mj-agent-runtime-prompt-version-bump` | 提议 `system.md` version bump diff（propose→拍板→apply） |
| `mj-agent-runtime-biz-catalog-sync` | 提议 `qcm_catalog.yaml` 同步上游 DB（propose→拍板→apply） |
| `mj-agent-runtime-eval-baseline` | 跑 EVAL framework baseline 测试（Phase 2 EVAL framework 落地后启用） |

### Layer 5: 证据型（Phase 6 新增 4）— evidence

PR merge 后写 evidence + 事故复盘 + runtime / security capture.

| Skill | Phase | 触发场景 |
|---|---|---|
| `mj-agent-evidence-closeout` | M6 | PR merge 后写 `evidence/verification/` + 更新 trace.yml |
| `mj-agent-evidence-postmortem-author` | M6 | 事故 → postmortem 模板撰写 |
| `mj-agent-evidence-runtime-capture` | M6 | 抓取 healthcheck / metrics 快照入 `evidence/runtime/` |
| `mj-agent-evidence-security-capture` | M6 | 抓取 secret scan / image vulnerability / SQL injection test 入 `evidence/security/` |

## §3 HITL Stage Mapping

> 详 `sdd/workflows/execution-loop.md` §1（17-stage loop）+ `policies/ai-agent.md` §4（必停 surface）.

每 stage 至少 1 个 skill；多数 stage 由多个 skill 协作（如 Stage 8 由 `mj-agent-flow-implement`
+ `mj-agent-runtime-*`（runtime 触发时）+ `mj-agent-doc-sync`（doc 同步）协作完成）.

> **操作型 HITL 节点（infra app-lifecycle）**：`mj-agent-infra-app-start`（Stage 10 sub；H1 redirect
> env-setup / H2 运行时 choice / H3 `check --live` FAIL conditional / H4 启动模式 choice）+
> `mj-agent-infra-app-stop`（Stage 17 sub；H1 info / H2 多目标 choice / H3 破坏性边界 STOP 节点转
> env-teardown）。slim 粒度：AskUserQuestion 仅留给真选择；非破坏命令（`up -d` / `check --live` /
> launch / `taskkill` / Level-1 `down`）由 harness Bash 权限 prompt 当执行拍板（ADR-034）.

## §4 Anti-patterns

- ❌ 不要直接读 SKILL.md body — 用 `Skill` 工具 invocation（per Claude Code skill 系统）
- ❌ 不要在 `runtime-*` skill 内未经 `OWNER_APPROVAL_REQUIRED` 拍板直接 Edit
  `src/mj_agent/skills/`、`prompts/`、`agent.py`、`tools/`、`biz_catalog/`（ADR-034
  propose→拍板→apply；详 `policies/data-boundary.md` §3）
- ❌ 不要混用 in-tree skill schema 与 in-source skill schema — 13-field `sdd/adapters/runtime-skill` vs 2-field
  ADR-013 native（详 `sdd/constitution.md` §3.3）

## §5 Related

- `sdd/adapters/claude-code-skill.md` — Claude Code skill adapter contract
- `policies/claude-code-skill.md` — in-tree workflow skill 治理政策
- `policies/data-boundary.md` §3 — 4 项专属必停（runtime family propose→拍板→apply；ADR-034 deny→ask）

---

> *Phase M0 — `state: active`*; 物理 namespace 不变；逻辑层在每 Phase 末刷新（per A6 review
> cadence）.
