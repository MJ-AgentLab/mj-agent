---
type: policy
artifact: ci-gates
state: draft
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-06-04
track: engineering-workflow
ai_visibility: source-of-truth
---

# Policy: CI Gates

> Phase M0 — §Review Cadence (A6) native 段 ✓.
> 其余段（§Gate 推进策略 / §例外处理 / §豁免申请流程）在 Phase M2-M3 内容填充.

## §1 Gate 推进策略

> TBD: Phase M2-M3 — 详 `sdd/gates.md` §5 启用矩阵 + 每 gate 启用前 1 周 dry-run 校验机制.

## §2 例外处理规则

> TBD: Phase M2-M3 — gate 失败但需 ship 时的 emergency override 流程（双 reviewer + 时限
> 偿还 spec debt）.

## §3 豁免申请流程

> TBD: Phase M3 — gate 长期豁免（如某 capability 在 deprecating phase）的 ADR 申请规则.

## §4 Review Cadence（A6 — Anthropic 大型代码库最佳实践；native）

`.claude/settings.json` + `.claude/hooks/` + `.github/workflows/ci.yml` + `.mcp.json` **每 3-6
月或 model release 后强制审计**.

| 触发 | 频率 | 责任人 | 检查项 |
|---|---|---|---|
| 定期 | 季度（每 3 月） | DRI | `permissions.deny` 红线列表 / `enabledPlugins` 漂移 / hooks 健康 / ci.yml gate 状态 |
| 模型 release | model major bump 1 周内 | DRI | 新 model 是否需新 permission 边界 / hook 是否在新 model 下仍触发 |
| MCP server 季度审计 | 季度 | DRI + reviewer | `.mcp.json` 13 server trust posture + credential mode（per A14 PR gate + `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md`） |
| Gate 启用前 | gate blocking 切换前 1 周 | DRI | dry-run violation 数量 + 影响范围 |

**审计输出**：`evidence/ai-context-audit/<YYYY-MM>_ci_audit.md`（与 `policies/documentation.md`
§Review Cadence 同周期，并入同一 evidence file）.

## §5 Settings 边界（B2 团队 vs 个人）

| 文件 | 范围 | 含义 |
|---|---|---|
| `.claude/settings.json` | 团队共享（commit） | `permissions.deny` 红线（4 项必停文件 + secrets.enc + `Bash(rm -rf:*)`）+ `enabledPlugins` + hooks 配置 |
| `.claude/settings.local.json` | 个人（gitignore） | `permissions.allow` 白名单（个人偏好的 Bash 命令豁免）+ 个人偏好 |

### §5.1 A13 — `.claude/settings.json` PR 阻塞条件（engineering-workflow track）

> 上文 §4 Review Cadence + 本节 §5 边界表把 `permissions.deny` 红线 + 季度审计
> 框定为 **审计** cadence；本子节把 A13 升格为 **PR 阻塞 ruleset** —— 任一 PR 触动
> `.claude/settings.json` 时 reviewer 必须按以下 3 条逐项核对，任一不满足即阻塞合并。
> 源：Meta_Framework STANDARD §7.7 A13；决策依据
> [[../decisions/ADR-013_Plugin_SKILL_md_Schema_Separation|ADR-013]]（in-tree vs marketplace
> 配置分离，settings.json 属项目级 in-tree）+
> [[../decisions/ADR-032_Claude_Skill_Schema_Monitoring|ADR-032]]（engineering-workflow
> 配置漂移监控）。Phase C `[STANDARD]_MJ_Agent_Claude_Code_Settings_v1.0` 落地后本节迁为
> cross-ref。

任一 PR 变更 `.claude/settings.json` 时，下列 3 条为 **阻塞条件**（A13；与 §4 季度审计
红线列表同源但语义不同 —— 审计是周期性巡检，本节是逐 PR 的 hard gate）：

| # | 阻塞条件 | 判定 | 不满足后果 |
|---|---|---|---|
| (a) | `permissions.allow` **不出现裸 `Bash`**（无 sub-pattern 限定） | 必须用 scoped 形式（如 `Bash(uv run *)` / `Bash(git status:*)`）；裸 `Bash` = 无界 shell 授权 | 阻塞合并；要求改 scoped pattern |
| (b) | `permissions.deny` **必须携带 secret pattern 兜底** | 含 `.env` / `secrets.enc` / API-key glob（如 `Read(./.env)` / `Edit(./.env)` / `Write(./.env)` / `Read(**/secrets*.enc)`）；与 §5 边界表「红线（4 项必停文件 + secrets.enc）」一致 | 阻塞合并；缺失即补齐 deny 条目 |
| (c) | `enabledPlugins` **增删需 PR body 描述用途与来源** | 任何 `enabledPlugins` add/remove 必须在 PR body 给出 justification（用途 + 来源 + trust posture） | 阻塞合并；要求补 PR body 说明 |

**与 §4 关系**：§4 季度 / model-release 审计是 cadence 巡检（catch 漂移）；§5.1 是 PR-time
hard gate（catch 引入）。两者共用同一 `permissions.deny` 红线定义，避免双源漂移。

**Cross-ref**：`.claude/skills/` 新建目录的准入规则（A13 的姊妹门，针对 skill 目录而非
settings.json）见 `sdd/adapters/claude-code-skill.md` §Scope「`.claude/` 新目录准入规则」；
`.mcp.json` server 增删（A14）见 `policies/ai-agent.md` §4
`mcp-server-trust-posture-change` + `docs/infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance.md`。

## §6 CI gate 命名映射

> TBD: Phase M2-M3 — `sdd/gates.md` G1-G28 与 `.github/workflows/ci.yml` step 名的双向映射.

---

> *Phase M0 — §Review Cadence native；其余 TBD Phase M2-M3.*
