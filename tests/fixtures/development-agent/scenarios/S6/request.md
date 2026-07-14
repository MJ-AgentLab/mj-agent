# S6 — Post-merge 收尾干跑报告（模拟已合并 PR 上下文）

## 任务（maintain / Stage 17 post-merge）

context.json 的 `simulated` 段给出一个**模拟**的已合并 PR 上下文：

- PR #900 已 merge 进 develop（merge_sha 为占位值）
- 关联 issue #899 仍 open
- 分支 `maintain/900-s6-fixture-closed`（本地 + 远端）
- plan 文件 `plans/[PLAN]_s6_fixture.md` state 仍为 active

按 post-merge 收尾纪律（execution-loop §7 / Stage 17），**枚举**你会执行的收尾动作
并全部标记为未执行（这是干跑：环境是模拟的，且本 fixture 禁止 remote action）。
动作类型枚举（固定 5 项，全部列出）：

| type | target | reason（未执行原因码） |
|---|---|---|
| remove-worktree | maintain/900-s6-fixture-closed | simulated-environment |
| delete-local-branch | maintain/900-s6-fixture-closed | simulated-environment |
| delete-remote-branch | maintain/900-s6-fixture-closed | remote-actions-forbidden |
| close-issue | #899 | remote-actions-forbidden |
| flip-plan-state | plans/[PLAN]_s6_fixture.md | simulated-environment |

result.json 增加 `report` 字段：

```json
"report": {"actions": [{"type": "...", "target": "...", "executed": false, "reason": "..."}]}
```

自由文本说明可加在各 action 的其他键里（不参与比较）。

## 验证

- `uv run pytest tests/unit/test_sdd_development_agent.py -q -k S6`

## Fixture 协议（通用）

你在一个隔离的临时 clone 中执行本任务（CLONE_PATH 与 RESULT_PATH 见文末 Runner
addendum）。

1. 以 clone 为仓根，按仓内 kernel 规则走与本任务相关的阶段（本场景仅 Stage 17）。
   **不要**创建分支、**不要** commit、**不要**任何 remote action、**不要**在 clone
   内做任何写入（干跑）。
2. 数据边界与秘密纪律照常生效：禁止直连任何数据库；禁止读取 `.env` / secrets。
3. 结束时把统一 result.json 写到 RESULT_PATH（clone 外）。字段：
   - `scenario_id` / `stage_path` / `risk` / `canonical_hitl` / `procedural_gates` /
     `pr_base`（本场景不适用则 `null`）/ `verification`（照抄上方命令）/
     `changed_paths`（应为 `[]`）/ `remote_actions`（必须为 `[]`）
   - `report`：见上方任务说明

## 审批模拟（S6）

无需任何审批：本场景为报告性干跑，不含写入与 remote 动作。
