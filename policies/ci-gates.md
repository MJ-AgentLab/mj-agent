---
type: policy
artifact: ci-gates
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
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

## §6 CI gate 命名映射

> TBD: Phase M2-M3 — `sdd/gates.md` G1-G28 与 `.github/workflows/ci.yml` step 名的双向映射.

---

> *Phase M0 — §Review Cadence native；其余 TBD Phase M2-M3.*
