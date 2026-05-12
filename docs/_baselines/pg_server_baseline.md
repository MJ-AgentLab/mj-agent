---
type: standard
domain: SYS
summary: .claude/scripts/pg-server-{start.cmd,wrapper.mjs} 的内部基线快照；MCP §6 季度 audit 漂移检测基准
owner: 项目负责人
created: 2026-05-11
updated: 2026-05-11
state: active
track: engineering-workflow
---

# pg-server Wrapper Internal Baseline

> 本基线快照锁定 `.claude/scripts/pg-server-{start.cmd,wrapper.mjs}` 当前内容；作为 [[../infrastructure/mcp/[STANDARD]_MJ_Agent_MCP_Server_Governance|STANDARD MCP Server Governance]] §6 季度 audit 的漂移检测基准。
>
> **更新流程**：实际 wrapper script 改动 → PR-time diff vs 本 baseline → 本 baseline 同步更新 + bump `updated:` 字段。漂移阈值由 audit 决定（默认任何字符级改动即标 PR review 必须解释）。

## Baseline 内容（frozen at 2026-05-11）

`.claude/scripts/pg-server-start.cmd`（Windows entry）+ `.claude/scripts/pg-server-wrapper.mjs`（Node.js wrapper）通过 `pg.types.setTypeParser` overrides 修复第三方 `@modelcontextprotocol/server-postgres` 默认对 timestamp 列做 JS Date 转换的问题（导致 SELECT 返 UTC "Z" 字符串而非数据库原始字符串）。

详细参考实文件：

- `.claude/scripts/pg-server-start.cmd`
- `.claude/scripts/pg-server-wrapper.mjs`

## Audit 项

| 检查项 | 频率 | Reviewer | 操作 |
|---|---|---|---|
| 1. wrapper 字符级 diff vs 本 baseline | 每季度 | Tooling Reviewer | `git diff <last-baseline-update> -- .claude/scripts/pg-server-*` |
| 2. `pg.types.setTypeParser(1114/1184, ...)` overrides 完整保留 | 每季度 | SWE | grep wrapper.mjs |
| 3. 第三方 `@modelcontextprotocol/server-postgres` 是否新版（行为变化） | 每季度 | Tooling Reviewer | `npm view @modelcontextprotocol/server-postgres versions` |
| 4. 如 wrapper 已不需要（上游 npm package 已修复） | 每年 | Tooling Reviewer | 撤 wrapper + 直接用 `npx` |

## 历史

| 日期 | 触发 | 改动 |
|---|---|---|
| 2026-05-11 | PR-Γ（cross-repo cleanup 收尾） | 初始 baseline 创建（替代历史 "vs mj-system upstream" 漂移基准） |
