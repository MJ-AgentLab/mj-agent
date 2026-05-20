---
type: policy
artifact: documentation
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-05-20
track: shared
ai_visibility: source-of-truth
---

# Policy: Documentation

> Phase M0 — §Review Cadence (A6) native 段 ✓.
> 其余段（§docs-as-contract 原则 / §capability owner-review-rotation / §docs/ 过渡期）在
> Phase M2 内容填充.

## §1 docs-as-contract 原则

> TBD: Phase M2 — capability package 内文档的 owner / review / rotation 规则.

## §2 capability 文档套件

> TBD: Phase M2 — 详 `mj-agent-refactored-structure.md` §4.5 ~12-artifact 套件
> （spec / requirements / design / contracts / tasks / runbook / trace / evidence / prompts
> optional）.

## §3 docs/ 过渡期政策

> TBD: Phase M2 — Phase 0-5 docs/ 并存；Phase M5 末整体 archive ceremony
> （详 `mj-agent-refactored-structure.md` §16.2 + `sdd/workflows/archive-capability.md`）.

## §4 Review Cadence（A6 — Anthropic 大型代码库最佳实践；native）

CLAUDE.md（root + 4 subdir）+ `.claudeignore` + `.claude/settings.json` +
`.claude/plugins.json` + `.claude/hooks/` **每 3-6 月或新 Claude 模型发布后强制审计**.

| 触发 | 频率 | 责任人 | 检查项 |
|---|---|---|---|
| 定期 | 季度（每 3 月） | DRI（ranzuozhou） | 行数 / 命令链是否过时 / HITL 边界是否合理 / 4 项必停是否仍有效 |
| 模型 release | model major bump 1 周内 | DRI | 新模型行为变化（如 Opus 4.7 → 4.8）；旧 prompt 在新模型下是否反效果 |
| Phase 切换 | 每 Phase 末 | DRI + reviewer | Phase 引入的新 capability / gate 是否需在 CLAUDE.md 索引 |

**审计输出**：`evidence/ai-context-audit/<YYYY-MM>_audit.md`（capability 无关；属仓库级；
由 `.claude/hooks/stop-claude-md-improver/` 产出 diff 草案，user 审后落地）.

**触发 A6 时的产出物**：

1. CLAUDE.md（root + 4 subdir）的实际行数 vs 上限
2. 过时命令清单（运行失败的）
3. HITL 触发条件 vs 实际触发频率（过严 / 过松）
4. 4 项专属必停是否仍代表真实风险
5. 新 capability / gate 索引差距

**与其他文件联动**：

- `policies/ci-gates.md` §Review Cadence — 同期审计 settings.json + hooks 健康
- `mj-agent-doc-sync` skill — Phase 末 user 触发批量应用 proposed updates

## §5 capability owner / review / rotation 规则

> TBD: Phase M2 — capability owner DRI 模式；review rotation；on-call.

## §6 Frontmatter required fields

> TBD: Phase M2 — 详 sdd/templates/ 各模板首部 frontmatter；A2/A3 PR gate 联动校验.

---

> *Phase M0 — §Review Cadence native；其余 TBD Phase M2.*
