---
type: evidence
summary: >-
  Epic #499 PR-P1a runtime feasibility probe —— 具名 producer
  `scripts/sdd/run_codex_carrier_probe.py` 对 18 required source candidates 在
  root/nested/worktree + isolated/actual-user-layer 布局的 deterministic-gate-v1
  真实探测（70 cases 全 PASS，verdict=PASS，unit 级标签 PASS_CANDIDATE）与
  model-telemetry-v1 真实模型触发遥测（18 capability x 正/负 prompt x 3 runs）。
  新发现：codex-cli 0.147.0 discovery 描述预算 = 1024 字符（确定性 prefix 截断），
  12/18 raw candidate 超限，其中 2 项为现役 byte-copy。
owner: ranzuozhou
created: 2026-08-14
updated: 2026-08-14
state: active
track: agent
---

# Runtime Feasibility Probe — Epic #499 (PR-P1a)

> 承载 `plans/[PLAN]_codex_cross_carrier_kernel.md` §2.8.6（probe schemas）与 §5.4
> （P1a 定义）。Delivery unit = **PR-P1a**，AC = **AC-09**，merge condition =
> deterministic **`PASS_CANDIDATE`**（§5.1 row 5）。

## 0. 入场锚点与 Owner 拍板记录

| 项 | 值 |
|---|---|
| 探测 revision | `33dd984fa64204ecdf9ec5391281415f684e0b24`（= PR-0d merge commit = `origin/develop`） |
| 前序 unit | PR-0d = [#505](https://github.com/MJ-AgentLab/mj-agent/pull/505)，MERGED `2026-08-14T06:14:16Z` |
| 前序 Stage 17 ledger | [#499 comment 5290178278](https://github.com/MJ-AgentLab/mj-agent/issues/499#issuecomment-5290178278)，body SHA-256 `c5d75b2900a7c41d7dc242c0c7a610342b4f29c6525b437115c89313c60f1de3`（纯 LF；raw 与 LF-归一同值），18 records 全终态 |
| 本 unit branch | `documentation/499-runtime-feasibility`，`git worktree add` 自 `origin/develop`（G1） |
| Task-0 preflight | `task0_freeze --check` = `TASK0_FREEZE_CLEAN`，identity `36f64771efeed88ca95bc98fadf3b3a0d1e56cc0b3e9f46afa675d9dbf88a6a7` 不变 |
| codex 载体 | codex-cli **0.147.0**（npm vendor 原生 `codex.exe`） |

**Owner 拍板（本 unit，均在实施前取得）**：

1. **telemetry leg 授权真实运行**（sanctioned probe 载体；每 capability×prompt 恰 3 次真实 Codex 调用）。
2. **`PASS_CANDIDATE` 为 unit 级标签**：JSON `verdict` 严格用 §2.8.6 闭合枚举（本次 = `PASS`）；
   PASS_CANDIDATE 表示「在候选工件（raw byte copy，production renderer 到 PR-B 才存在）上取得
   deterministic PASS」，per §5.6 不足以进 C0。
3. **Codex project trust 视为就位**：`~/.codex/config.toml` 容器级条目
   `d:\workspace\10-software-project\projects\mj-agent` → `trusted`（#330 spike：容器条目覆盖其下 worktree）。
4. **det-05 判据重拍板（机制级）**：实施中实测推翻了 Gate 1「全文不截断才 PASS」的前提
   （见 §3 发现 F-P1a-1）；Owner 改批机制级判据 —— 预算确定性可测且呈现形态合法
   （完整 或 确定性 prefix 截断），超限本身记数据不判 FAIL。

## 1. 交付面（Gate 1 批准的 exact scope，全部新增、零修改现有文件）

| 文件 | 角色 |
|---|---|
| `scripts/sdd/run_codex_carrier_probe.py` | 具名 producer：`emit-fixtures` / `deterministic` / `telemetry` 三模式 |
| `tests/unit/test_run_codex_carrier_probe.py` | 20 条 contract 测试（synthetic repo + injectable fake runner，不真调 codex） |
| `evidence/development-agent-v8/probe/fixtures/deterministic-expected.json` | 预提交期望值（pinned@`33dd984fa642`：18 ids、source raw SHA、description 长度与预测呈现模式、budget=1024） |
| `evidence/development-agent-v8/probe/fixtures/prompt-corpus.json` | 预提交 prompt corpus（18 capability × 正/负 = 36 条；自然用户口吻，不点名 skill） |
| `probe/deterministic-gate-v1-20260814T083847Z-33dd984fa642.json` | deterministic 真实 run 结果（run-ID 命名，fail-closed 不覆盖；§2） |
| `probe/model-telemetry-v1-20260814T083913Z-33dd984fa642.json` | telemetry 真实 run 结果（§4） |
| 本文件 | tracked 证据摘要 |

Raw 捕获（prompt-input JSON / mcp list / exec 事件流）落 **gitignored** `.mj-agent-local/probe/<run-id>/`，
tracked 结果只存 digest —— user-layer 配置细节（server 名单等）不入库（镜像 §2.8.7 ready-host 的
local/tracked 分离）。

## 2. deterministic-gate-v1 结果（真实 run）

结果工件：[`probe/deterministic-gate-v1-20260814T083847Z-33dd984fa642.json`](./probe/deterministic-gate-v1-20260814T083847Z-33dd984fa642.json)。

- **verdict = `PASS`**；70 cases 全 PASS（58 `OK` + 12 `OK_DETERMINISTIC_TRUNCATION`）。
- `repo_head = 33dd984fa642…`，`codex_build = codex-cli 0.147.0`。
- **unit 级标签 = `PASS_CANDIDATE`**（候选工件等级；只有 PR-P1b 用 production renderer 的 `PASS` 才允许 C0）。

### Case 家族（70 = 1+18+18+1+18+5+4+3+2）

| 家族 | 数 | 判什么 | 载体 |
|---|---:|---|---|
| det-01 manifest-required-inventory | 1 | manifest 派生 required 集 == §2.2.1 的 18 | `sdd/development-agent.yml` 静态派生 |
| det-02 source-present | 18 | source blob 存在、raw SHA 与 fixture 一致、frontmatter name==id 且有 description | git blob（非工作区字节） |
| det-03 derived-path | 18 | `.agents/skills/<id>/SKILL.md` 路径安全（NFC/segment/无盘符） | 纯静态 |
| det-04 casefold-collision | 1 | 18 派生路径 casefold 互不冲突 | 纯静态 |
| det-05 description-budget | 18 | 呈现形态 == fixture 预测（complete/truncated），机制级判据 | staged 布局 `codex debug prompt-input` |
| det-06 artifact-digest | 5 | 现役 byte-copy artifact raw SHA == source raw SHA | git blob |
| det-07 fresh-discovery | 4 | fresh 进程 discovery 集合精确匹配（staged-root/staged-nested/staged-worktree=18；real-root-user-layer=5） | `debug prompt-input`（无模型调用） |
| det-08 config/trust route | 3 | user-layer trust 条目覆盖仓根；staged 差分（trust-less=`[]`，trusted=canary）；real 树 project 8 server 全载入 | trust 表头解析 + `mcp list --json` 三态差分 |
| det-09/10 hook/rule canary | 2 | `features list` `hooks stable true` + exec `--dangerously-bypass-hook-trust` / `--ignore-rules` 旗标在位 | 构建面存在性（执行级 canary 归 PR-D1a） |

布局矩阵满足 §5.4：staged root / nested cwd / linked worktree（各配 isolated `CODEX_HOME`，trust 由
临时 fixture config 提供，**绝不写用户级 config**，D-015 不触）+ 真实仓根 × actual user layer。
staging 一律取 **git blob 字节**（`.gitattributes` 使 Windows 检出 CRLF 而 blob LF，工作区字节身份
在 Linux CI 不可复现——PR-0d 判例）。

### Producer 设计点（plan 留白处，Gate 1 拍板）

- `observed_class` 闭合枚举 = `TRIGGERED_TARGET | TRIGGERED_OTHER | NOT_TRIGGERED | UNPARSEABLE`。
- run-ID = `<schema>-<YYYYMMDDTHHMMSSZ>-<head12>`（§2.8.1），同路径已存在即 fail-closed exit 2。
- canonical JSON 序列化：重编码解析结果逐字节复现文件（测试断言）。
- 子进程环境走具名 allowlist（credential 类变量结构性排除，值零日志）。

## 3. 新发现（本 probe 产出的 runtime 事实）

**F-P1a-1｜Codex discovery 描述预算 = 1024 字符。** `codex debug prompt-input` 中每个 skill 的
description 单行呈现，超过 1024 字符即确定性截断为「1021 字符前缀 + `...`」（两次独立 run
逐字节一致）。**12/18** raw candidate 超限：

| candidate | desc 字符 | | candidate | desc 字符 |
|---|---:|---|---|---:|
| flow-implement | 1521 | | flow-plan | 1155 |
| flow-review-respond | 1391 | | flow-scope-drift | 1095 |
| **flow-diagnose（byte-copy）** | **1322** | | flow-intake | 1063 |
| flow-post-merge | 1315 | | **git-sync（byte-copy）** | **1062** |
| flow-self-review | 1236 | | git-branch…git-push 等 6 项 | 712–879（完整呈现） |
| flow-verify | 1180 | | doc-validate | 1143 |
| flow-repo-scan | 1179 | | | |

- 对 13 项 translated：§2.4 终态本就用紧凑 `codex_discovery_summary` 替换 description，预算事实
  正是 summary 设计的输入依据。
- **对 2 项现役 byte-copy（git-sync / flow-diagnose）：今天生产树的 Codex discovery 已在截断其
  description**（byte-copy 终态无 summary 兜底）。建议 Owner 择机立 follow-up：缩短这 2 个 source
  description（`.claude/**` 拍板 + `agents_sync` 重投影），不在 P1a scope。

**F-P1a-2｜跨 harness frontmatter 宽松性。** 真实 skill 的 description 含 `": "`（如
"Do not use for: …"）——不是严格 YAML，但 Claude/Codex loader 均按行式宽松解析接受。probe 的
frontmatter 解析器与之对齐（首个 smoke run 曾因 `yaml.safe_load` 全军 FRONTMATTER_INVALID，
已修并加钉测试）。

**F-P1a-3｜模型自述不可作触发证据。** 试点 run 中模型在 `agent_message` 里宣称「我会使用
`mj-agent-git-commit` 技能」，与其后是否真的读取 carrier 无必然一致。分类器排除全部
`agent_message`（prose）事件，只认非 prose 事件中的结构化信号（命令串引用
`agents/skills/<id>/SKILL.md`，斜杠方向归一），与 §2.8.6「禁止用模型回答冒充」同构。

## 4. model-telemetry-v1 结果（真实 run）

结果工件：[`probe/model-telemetry-v1-20260814T083913Z-33dd984fa642.json`](./probe/model-telemetry-v1-20260814T083913Z-33dd984fa642.json)，
raw SHA-256 `f3bbec455d35cf14b206d77b0aca699e563cc61c52b7cd3ece7f09bb32cf37fd`。
run 窗口 `2026-08-14T08:39:13Z → 09:59:49Z`（约 80 分钟，108 次真实 `codex exec` 串行）。

| 项 | 值 |
|---|---|
| `model_id` | `gpt-5.6-terra`（CLI `-m` 显式钉定） |
| `codex_build` | codex-cli 0.147.0 |
| `repetitions` | 3（每 capability×prompt 恰 3 行，机器断言） |
| `prompt_fixture_sha256` | `64aa18debf2a5ee5cc2774863bd1f1b8343a2b88b082e78de347d3be9675c31f`（§2.7 wire，已独立复算） |
| `sampling_config` | `reasoning_effort/temperature/seed = null`（运行时未公开可固定）；`cli_args_sha256 = 22a169ef5acf5207…`；`project_config_sha256 = 38e0b9de817f645c…`（= canonical-null 的 absent-value digest——telemetry 布局无 project config 生效） |
| `warnings` | `["EXEC_TIMEOUT"]`（仅 1/108 行：`mj-agent-flow-intake--positive` run 2 在 180s 截止被 kill，截止前已观测到 TRIGGERED_TARGET） |

**Observation 分布（108 行 = 18 capability × 2 prompt × 3 run；分布是观察数据，不参与任何 verdict）**：

| | TRIGGERED_TARGET | TRIGGERED_OTHER | NOT_TRIGGERED |
|---|---:|---:|---:|
| positive（54 行） | **54** | 0 | 0 |
| near-negative（54 行） | 18 | 15 | 21 |
| 合计 | 72 | 15 | 21 |

- **Positive 隐式触发 54/54（18/18 capability 各 3/3）**——含 §3 F-P1a-1 中 12 个描述被截断的
  candidate：截断后的 1021 字符前缀在本 corpus 上仍足以驱动正确的隐式选择。这是对「预算截断
  是否破坏触发」的直接遥测回答（样本有限，不外推为保证）。
- Near-negative 的 18 行 TRIGGERED_TARGET / 15 行 TRIGGERED_OTHER 说明邻近请求经常仍会咨询
  相关 carrier（如「撤销上次提交」也读 git-commit skill）——这是 PR-B 设计
  `required_trigger_terms` 正/负 golden 的实测输入，不判对错。

telemetry 的结构性纪律（schema 即约束）：

- **AC-09 结构性成立**：`model-telemetry-v1` 顶层键中**没有 verdict**；两份 JSON 互不聚合，
  telemetry 任何结果都无法改变 deterministic verdict（测试断言 `"verdict" not in doc`）。
- 只记 metadata（`observed_class` / `warning_codes`）：**无 transcript、无 Secrets、无
  chain-of-thought**；prompt 正文不进结果文件（测试断言）。
- `temperature` / `seed` 运行时未公开可固定 → JSON `null`（不猜默认值）；`model_id` 经 CLI
  显式钉定（`-m gpt-5.6-terra`，镜像 Owner user-layer doctor 报告的有效模型；钉定进入
  `cli_args_sha256` 可复验，钉≠猜）。
- 每 (capability, prompt) 恰 3 行 observation，`run_index` ∈ {1,2,3}，按
  `capability_id, prompt_id, run_index` 排序（schema 强制 + 测试断言）。
- 运行环境：staged 18-candidate 布局 + `--ignore-user-config`（auth 走真实 `CODEX_HOME`，
  user-layer MCP server 不加载）+ read-only sandbox + `--ephemeral` + prompt 走 stdin
  （Windows headless 四坑判例）。

## 4b. Stage 11 对抗性自评审记录

5 攻击透镜（schema / verdict 完整性 / 测试可靠性 / 边界安全 / evidence 准确性）+ 逐 finding
refuter，共 21 agents：**16 findings → 11 CONFIRMED / 5 REFUTED**（SC-02 与 EV-1 是同一
run-ID 主张的两处透镜命中，均被驳回）。全部 confirmed 缺陷已修复并各配
negative control（测试 20 → 26 条，下表 11 行与 CONFIRMED 数一致）；修复后 deterministic
正式 run **重新生成**（旧产物删除），telemetry 首次部分 run 中止弃用（其 tracked 工件从未存在）。

Confirmed 修复清单：

| ID | 缺陷 | 修复 |
|---|---|---|
| SC-01 (HIGH) | telemetry `project_config_sha256` 恒 JSON null，违反 §2.8.1「所有 `*_sha256` = 64-hex」 | 缺失 config 记 domain-separated absent-value digest（canonical null 的 SHA-256）；测试断言 64-hex |
| P1A-VI-01 (HIGH) | det-08 real-project-config 在 config 缺失/无 server 时空集互等假 PASS | 缺失 → `BLOCKED_PREREQUISITE` / `PROJECT_CONFIG_ABSENT` |
| TS-01 (HIGH) | 自述排除的 decoy 测试空转（decoy 文本无可命中信号） | decoy 改含真实 carrier path，仅 prose 排除能拦住；另加独立 prose 排除单测 |
| EV-2 (MED) | `SystemExit("msg")` 实际 exit 1，与「fail-closed exit 2」文档矛盾 | `_die()` 统一 stderr + exit 2；测试断言 `code == 2` |
| P1A-VI-02 (MED) | trust 判定只看 `[projects.X]` 节头，不看 `trust_level` 值 | 解析 (path, trust_level)，仅 `"trusted"` 计为覆盖；负例测试（untrusted/缺值） |
| TS-02 (MED) | det-02 纯 digest 失配误标 `FRONTMATTER_INVALID` | 分因：`SOURCE_DIGEST_MISMATCH` / `FRONTMATTER_INVALID` / `MISSING_SOURCE`；测试钉 reason |
| TS-03 (MED) | 测试假 runner 复用被测模块的 frontmatter 解析器（回归自相抵消，mutation 已证） | 假 runner 改用独立行扫描 |
| TS-04 (MED) | 分类器 `value == cid` 结构化臂零覆盖 | 专项单测（TRIGGERED_TARGET / TRIGGERED_OTHER） |
| SC-03 (LOW) | corpus 不在仓根下时 set-digest 键退化为裸文件名 | 越界 fail-closed exit 2 |
| SC-04 (LOW) | corpus/fixture 加载不拒重复键、不查 (capability, prompt) 唯一性 | `_strict_json_loads`（重复键拒绝）+ corpus 逐条校验（exact keys / 唯一 / 非空）；重复项测试 |
| TS-05 (LOW) | 预算 1024 无字面钉线（常量改动测试全盲） | `DISCOVERY_BUDGET_CHARS == 1024` 字面单测 |

REFUTED（读理由后接受）：SC-02/EV-1（run-ID 非幻影——producer 启动即定 run-ID，文件按其落盘）、
SC-05（corpus 非 §2.8.6 注册 schema 工件，canonical JSON 约束不及）、P1A-VI-03（假 runner 复用
helper 的泛化主张不成立；其成立部分即 TS-03 已单独修复）、P1A-VI-04（det-03/04 由常量派生但
verdict 层可证伪，plan 只约束 verdict 面）。

## 5. Rollback / repair（§5.1.1）

新 evidence correction PR；**不得把 telemetry 升格为 verdict**。deterministic 若在未来复跑中出现
FAIL/ERROR/BLOCKED_PREREQUISITE，按 §5.4 停在 A0 之前。

## 6. 与后续 unit 的接口

- **PR-A0/PR-B**：F-P1a-1 的预算事实 + 12 项超限清单是 `codex_discovery_summary` authoring 的
  直接输入；`DISCOVERY_BUDGET_CHARS = 1024` 常量在 producer 内有单一定义可引用。
- **PR-P1b**：复用本 producer 的 deterministic 骨架，替换 staging 为 production renderer 输出，
  merge condition 升格为 `PASS`（§5.6）。
- **PR-D1a**：det-09/10 只证明 hook/rule 构建面在位；执行级 canary（真实 hooks.json/rules 装载）
  归 PR-D1a。
