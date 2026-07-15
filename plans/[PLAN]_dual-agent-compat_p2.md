---
type: plan
summary: dual-agent-compat v5 P2 执行计划——首批六 flow skills 双工具 fixture 端到端：S1–S6 fixture 面 + Python runner + 5 comparator + 单测（PR-1），双工具 S1–S5 各连续 2× 实跑证据 + manifest evidence（PR-2），state flip（PR-3）；issue #333（总锚 #312）
owner: ranzuozhou
created: 2026-07-14
updated: 2026-07-15
completed: 2026-07-15
state: completed
track: shared
---

# [PLAN] 双工具兼容 v5 — P2 切片（issue #333）

## 1 Linked Artifacts

- Issue: #333（AC1–AC10）；总锚 #312 P2 项
- Intake: [[[INTAKE]_dual-agent-compat_p2]]（7 项 Stage 0 拍板）
- Program plan: [[[PLAN]_dual-agent-compat]] §11 P2 / §11.1 / §12（fixture 面逐字 SoT）
- 前序：S2 #330（closed），develop @ 7d36fb2

## 2 Context

P0/P1/S0/S1/S2 已闭环；六项 capability 的 support_mode 现状均非 unsupported（diagnose=
project 双 native；intake/plan/implement/repo-scan=after-neutralization + Codex
adapter-backed；verify=script-ci）。P2 按结果验收（D-001）：不要求补投影/中立化，
以 fixture 双跑证明两工具在同一任务输入下产出结构一致的 17-stage 行为分类与验证结果。
Stage 3 repo-scan 确认 fixture 面绿地 + 四硬事实（pytest 收集陷阱 / input.patch 双角色 /
DA031 / fixture-base 确定性）。

## 3 Scope

- 包含：见 issue #333 In-scope（fixture 面 + runner + comparator + 单测 + 双跑证据 +
  manifest evidence + flip）
- 不包含：S6 双跑（P3）；投影/中立化扩面；biz/env/hook 负向重建（P0/P1 资产）；
  CI 新 step；`.mcp.json` / manifest mcp/codex.posture 段（零改动）
- 前置依赖：无（worktree 已建；实现前 `uv sync`）

## 4 任务拆解（全部风味 A 纯代码/测试基建；PR-1 = 8a–8e，PR-2 = 8f–8h，PR-3 = 8i）

### 8a fixture 目录 + 三 schema 固化

- `tests/fixtures/development-agent/scenarios/S1–S6/{request.md,context.json,
  input.patch(仅 S1/S3),expected.yml}` + `base/` 覆盖层（S1 坏链文档、S5 ci.yml 副本等）
- **context.json schema**（§12 四要素 + 双角色显式化）：`scenario_id` / `task_type` /
  `fixture_base`（temp 仓 base 分支名）/ `initial_changed_paths` /
  `input_patch_role: "pre-applied"(S3) | "expected-diff"(S1) | null` /
  `simulated{branch, pr, issue, plan_state}`（S6 用 merged-PR 模拟数据）
- **expected.yml schema**：scenario_id + stage_path + risk + canonical_hitl +
  procedural_gates + pr_base + verification[]（精确命令串）+ allowed_changed_paths[] +
  comparator + remote_actions[]（+ S3 red_green_node；+ S6 report 期望结构）
- **result.json schema**（§12 9 字段）+ S6 扩展 report 字段
  （actions[]{type,target,executed,reason}）
- 硬规则：fixture 目录内零 .py 文件（pytest testpaths=tests 收集陷阱）；
  所有 fixture 文本 LF（.gitattributes 已 pin yml/json/py，patch/md 由 runner LF 归一）
- 验证：单测 8e 逐目录枚举断言

### 8b fixture 协议（request.md 结构约定）

- 每个 request.md = 任务描述（§12 固定输入逐字）+ 尾部固定协议段：
  ①以 clone 为仓根按 kernel 规则工作 ②结束时写 result.json 到 runner 注入的
  RESULT_PATH（clone 外，见 8c）③模拟审批约定——S1/S2/S3 显式预授权 procedural
  gates（"Owner pre-approves plan/self-review sign-off for this exercise"），
  S4/S5 **零授权语句**（必须分类停下，stop before 8，零写入）④禁 remote actions /
  禁直连 DB / 禁读 secrets（负向面）
- 审批事件记录：agent 把「引用了哪条预授权 / 在哪一 stage 停下」写进 result.json
  procedural_gates / canonical_hitl——即 §12「审批事件」证据载体
- 验证：8e 协议段存在性断言 + S4/S5 双跑实证

### 8c runner：scripts/sdd/fixture_runner.py + fixture_comparators.py

- 子命令 setup / verify / report / teardown；_common bootstrap；stdlib+pyyaml
- **run-dir 布局**（Gate 5 定案 1：result.json 在 clone 外，与 §12 快照排除表相容）：
  `fixture-runs/<tool>-<Sx>-run<N>/{clone/, prompt.md, result.json, setup.json,
  verdict.json, commands.log}`
- setup：git clone 本地 .bare → clone/；叠 base/ 覆盖层 → 以固定 author/committer/
  date 提交为 fixture_base 分支（不引用本机现成分支）；建 simulated.branch 工作分支
  （Gate 5 定案 3：被测 agent 不建分支——§12 各场景 stage_path 均无 Stage 2，runner
  预建，天然规避 G1 hook 与 temp 仓冲突）；uv sync --frozen；input_patch_role=
  pre-applied 时 git apply（S3 红态，留 uncommitted）；red 检查（S3：red_green_node
  非零否则 setup FAIL）；no-write 场景记 pre-run 快照；渲染 prompt.md = request.md +
  运行时附录（CLONE_PATH/RESULT_PATH 注入；模板在 runner 内版本化——期望值零运行时
  生成，注入的只是路径）
- verify：result.json schema 校验 → **普遍基线**（schema + changed_paths 自报交叉核验
  + remote_actions 相等；agent 自报与 runner 独立重算不一致即 FAIL）→ 场景 comparator
  行为检查 → verdict.json（exit 0/1）
  - **classification-exact 口径修订（PR-2，2026-07-14；Owner 拍板 Option A，反转 Gate 5
    定案 2）**：§12 将 classification-exact 仅定义为 `no-write-and-classification-exact`
    比较器的一部分（**只门 S4/S5**——必停 enum + stop-before-8 是这两场景的被测核心）。
    原定案 2「全场景基线」经首轮双工具实跑证伪：Claude 与 Codex 对 S1 均合理纳入
    Stage 11 自检（`stage_path=[3,8,10,11]`），且对 `pr_base` 语义有正当分歧——普遍
    exact 相等下无单一期望值能同时过两工具。故 S1/S2/S3 只走各自行为比较器
    （patch / checks / red-green），其 stage_path/risk/pr_base 等入 result.json 并在
    evidence SUMMARY 做跨工具比对（§11.1「无未解释差异」），正当分歧给解释而非硬判失败；
    `pr_base` 语义在 request.md 协议段厘清（按分支类型 G2 填，即使未真正建 PR）。
- **5 comparator 语义**（§12 L326-331 逐字实现，纯函数模块）：
  - exact-patch-lf = git diff（fixture_base..工作区，固定 flags）LF 归一字节比对
    input.patch
  - checks-pass-and-path-scope = 全命令退出 0 + changed_paths ⊆ allowed_changed_paths
  - red-green-and-path-scope = red 非零（setup 已记）+ green 0 + 其余命令 0 + path-scope
  - no-write-and-classification-exact = classification-exact + 前后快照相等
    （tracked+untracked，排除 .git/.venv/__pycache__/.pytest_cache/.mypy_cache/
    .ruff_cache，POSIX 相对路径排序，「路径+文件 SHA-256」再 SHA-256，禁 commit hash）
  - report-schema-exact = 动作类型/目标/未执行原因/remote_actions==[] 结构比对，
    不比自由文本
- 验证：8e 单测 + S1 Claude 侧 dry-run

### 8d 双工具调用形态（PR-2 执行规程；PR-1 文档化进 runner --help + 本 plan）

- Claude：`claude -p @prompt.md --permission-mode acceptEdits --add-dir <run-dir>`，
  cwd=clone，全新会话（不用实现会话）；模型/版本记入 evidence
- Codex：`codex exec` cwd=clone + `-c sandbox_workspace_write.writable_roots=[<run-dir>]`
  （result.json 写出 clone 外的 sandbox 通道）+ bash 侧 `</dev/null`（在案）；
  版本先 `codex --version` 对齐（在案 0.144.3 教训）；trust 先 `codex mcp list`
  oracle 实证 fixture-runs/ 归属，不行则 Owner 按 D-015 手加（fixture 场景不需 MCP，
  trust 只影响 .codex/config.toml 装载，预期无阻塞）
- 形态风险预案：正式采证前各做 1 次 S1 dry-run（不计入连续 2 次）；codex exec 形态
  失败 → fallback Owner TUI（差异如实记录进 SUMMARY）
- 验证：dry-run 通过后才进正式 2× 采证

### 8e 单测（tests/unit/test_sdd_development_agent.py 扩展，#217 模式）

- 真实树枚举：六 fixture 目录结构/必备文件/schema 逐字段断言（显式列 S1–S6）
- comparator 纯函数：LF 归一、快照 hash 稳定性+排除表、path-scope 子集、排序命令数组、
  red-green 判定、report-schema-exact 正反例
- S6：golden result.json vs expected.yml PASS + 变异 FAIL（测试名含 S6 满足 -k S6）
- runner setup 确定性：tmp_path 合成仓两次 setup → 树内容 hash 相等
- 验证：`uv run pytest tests/unit -q` 全绿

### 8f PR-2：双工具正式采证（PR-1 merge 后 develop 基线）

- 每场景×工具×2 连续 run：setup → 调用（8d）→ verify → 归档
  `evidence/S<x>/<tool>/run-<n>/{result.json,verdict.json,commands.log,setup.json}`
- SUMMARY.md：base SHA / 工具版本 / 20 格矩阵（5 场景×2 工具×2 次）/ 差异分析
  （「无未解释差异」论证）/ S4/S5 no-write+未批停下负向证据 / S2/S3 remote_actions=[]
  commit 负向证据
- 验证：全 verdict PASS；FAIL → 修 fixture/runner（同 PR 评审规则）重跑

### 8g PR-2：manifest evidence + 六项复核

- 六 capability evidence 追加：本 capability 对应场景 expected.yml + evidence/SUMMARY.md
  （映射：diagnose←S3；intake←S2/S4/S5；repo-scan←S1–S5；plan←S2/S4/S5；
  implement←S1/S2/S3；verify←S1/S2/S3）；DA031 同 commit 落盘
- support_mode 复核记录（AC9）写入 SUMMARY.md
- 验证：`check_development_agent.py --all --fail-on error` 绿

### 8h PR-2 收口：#312 P2 勾 + §11.1 晋级证据 comment（merge 后 post-merge 段执行）

### 8i PR-3：plan/intake state flip（documentation 小 PR，Rule 12）

### Documentation Decision

见 Stage 3 repo-scan 矩阵（Plan=Create 即本文件；其余 9 类全 None）。

## 5 风险

| 风险 | 等级 | 风味 | 缓解 / Rollback |
|---|---|---|---|
| codex exec sandbox 写出通道（writable_roots）实际行为与预期不符 | Medium | A | dry-run 先行；fallback=Owner TUI（在案）；再不行 result.json 允许 clone 内保留路径并在 comparator 排除——须回本 plan 修订拍板（触 §12 快照语义） |
| agent 分类字段跨 run 漂移（stage_path/gates 不稳定）→ 连续 2 次不齐 | Medium | A | 协议段把分类口径写死（枚举+判定规则引用 kernel 文档）；漂移=fixture 措辞缺陷 → 修 request.md（fixture 变更同 PR 评审）重跑 |
| develop HEAD 在 run 间移动 → 快照/patch 基线漂移 | Low | A | 每 run 记 base SHA；同场景 2 次连续采集在同一 develop SHA 上完成 |
| fixture 内容误触既有 gate（pytest 收集/ruff/frontmatter/G7） | Low | A | 零 .py 硬规则 + SCAN_ROOTS 不含 tests/（已核）+ PR-1 全 gate 本地跑 |
| uv sync 每 clone 成本 | Low | A | wheel 缓存复用；--frozen |
| 4 必停面 / A14 / D-017 | — | — | 零接触（S4/S5 为 fixture 数据；真实面零字节不动） |

## 6 验证

- Level A（PR-1/PR-2 每次提交前）：`uv run pytest tests/unit -q` · `uv run ruff check` ·
  `uv run mypy src/mj_agent` · `check_development_agent.py --all --fail-on error` ·
  `check_frontmatter.py` + `check_wikilinks.py`（plans 文档）
- Level B（PR-2 采证即验证本体）：8d/8f 规程
- 测试缝：既有 test_sdd_development_agent.py 一个缝扩展（不开新缝）
- Stage 11 tie-in：反扫 N/A（纯新增）；scope-drift 预期 Severity=None

## 7 完成标准

Issue #333 AC1–AC10 逐条（勾稽见 issue）；PR-1/PR-2/PR-3 全 merge + CI 绿；
#312 P2 勾 + 晋级证据 comment；post-merge 清理（worktree/分支/fixture-runs）。

## 8 关联

- Issue #333；总锚 #312；前序 #330/#331/#332
- 目标文件：§4 各子任务列示
- 不动文件：`src/mj_agent/**` 全部 · `.claude/**` · `.mcp.json` ·
  `.github/workflows/ci.yml` · `sdd/development-agent.yml` 的 mcp/codex.posture 段 ·
  `.agents/**` · `.codex/**`
- 后续独立 PR：P3（S6 双跑 + 第二批四 skills）
