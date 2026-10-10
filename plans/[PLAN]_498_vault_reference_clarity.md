---
type: plan
summary: Issue 498 修正八处当前 SDD 来源说明并登记十四处历史引用的保留边界
owner: ranzuozhou
created: 2026-10-10
updated: 2026-10-10
state: active
track: engineering-workflow
---

# Issue #498 仓外来源引用治理

## 1. 追踪与上下文

- Issue：[GitHub #498](https://github.com/MJ-AgentLab/mj-agent/issues/498)，保持 OPEN。
- 基线：`develop@aa70360bc123c668afc5e42c31c5c2cb766467b6`；2026-10-10 HEAD 与远端 develop 一致。原 Issue 取证基线为 `4b2730e`，新增 #579 只改变 #563 收尾文档，本单 15 文件 / 22 处引用数量未变。
- Owner 批准记录（2026-10-10，本次会话）：「批准 #498 的推荐方案及候选差异：修正 8 处当前 SDD 引用，14 处历史引用具名保留，新增 working Plan。开始实施并验证，issue 保持 OPEN。」该批准覆盖本 Plan Gate 1、八份 SDD 受保护来源表达修改及十四项具名历史接受。
- 批准的文档修复包：A11–A18 八处当前 SDD 来源说明修正；A01–A10、B01–B02、C01–C02 十四处历史项具名保留。
- 发布批准（2026-10-10，本次会话）：在上述九文件实施与验证结果、分支及待提交 / 推送 / 创建 PR 的报告后，Owner 回复「批准」。本轮按同一九文件修复包进行 commit、Gitee → origin 普通 push、创建面向 develop 的 PR；merge 由 Owner 人工执行，Issue 保持 OPEN。
- 实施分支：`documentation/498-vault-reference-clarity`；工作树：`D:/workspace/10-software-project/projects/mj-agent/documentation/498-vault-reference-clarity`，按 G1 从上述基线创建。

## 2. Scope

- 修正七份 SDD adapter 的来源说明、一份 new-capability 工作流的蓝图引用；同步这八份文档的 version / updated / 修订脚注。
- 保留归属：实施蓝图与通用手册分别注明实际标题、完整本机路径和核验版本；规则主体仍在仓内。
- 历史 Plan、readiness 评估、completion assessment、policy 修订说明、JSON 输出保持原文；本 Plan 逐项登记定位、来源与保留理由，Owner 已接受为具名残留。
- P01–P04 四处已限定引用原始字节不变；`learning/`、archive、旧客户端已退出资产、runtime Prompt / SKILL / SQL / catalog、原生配置、CI gate 均无修改。
- 不复制 vault 文档、不修改仓外文件、不改变旧文档 state、不引入新的运行行为或依赖。

## 3. 来源核验与 Documentation Decision

| 来源 | 已核验版本 | 核验范围 |
|---|---|---|
| S1 `D:/Document/My-Local-Vault/sdd-development/mj-agent/spec-anchored-calm-lampson.md` | v2.2，2026-05-20 | 实施方案；有 §6、§9、§10 与 R-G21，没有手册 §22/§23/§25 |
| S2 `D:/Document/My-Local-Vault/sdd-development/mj-agent/mj-agent-refactored-structure.md` | v2.2，2026-05-20 | 目标结构蓝图；§4.5 12-artifact 套件存在 |
| S3 `D:/Document/My-Local-Vault/sdd-development/mj-agent/mj-agent-refactor-completion-assessment.md` | v1.1，2026-06-11 | 自述保留 v1.0 评估快照；不把当前 v1.1 冒充原引用 v1.0 |
| S4 `D:/Document/My-Local-Vault/sdd-development/通用 Spec-Anchored 项目构建、重构、运行与治理手册.md` | v1.2，2026-05-20 | §22.1/22.4/22.5/22.6、§23、§25 存在；没有 Contract Adapter 专章 |

仓外文档只作历史归属和章节出处，不作为 Codex 的执行规则。当前根 AGENTS、policies、SDD 与 contracts 保持规则权威。

| Type | Action | Path / Existing Target | Reason / Evidence | Track | Required Before |
|---|---|---|---|---|---|
| Plan | Create | `plans/[PLAN]_498_vault_reference_clarity.md` | 承载本包步骤、分类账与历史具名接受；#498 AC-1/2/3 | engineering-workflow | 实施，Owner Gate 1 后 |
| SPEC | None | — | 无接口 / 行为变化 | — | — |
| ADR | None | — | 不新增长期架构或修改既有决策 | — | — |
| RUNBOOK | None | — | 无操作 / 部署变化 | — | — |
| GUIDE | None | — | 来源说明已在既有 SDD 文档就地修复 | — | — |
| STANDARD | None | — | 不新建 STANDARD；下表列既有 kernel 类型的实际变更 | — | — |
| Local ISSUE | None | GitHub #498 | 既有 Issue 与 Plan 足够，不重复建问题文档 | — | — |
| ASSESSMENT | None | 历史 completion assessment | 接受具名保留，原论断 / 状态 / 内容不动 | shared | — |
| CHANGELOG | None | `CHANGELOG.md` | 仅引用表达修复，无运行行为变化 | — | — |
| INDEX | None | 既有 INDEX | 无 canonical 路径新增 / 迁移；working Plan 不入 canonical INDEX | — | — |

既有 kernel 文件不伪装成新 STANDARD，实际 Update 面为以下八份：

| ID | Update target | version | 具体差异 |
|---|---|---|---|
| A11 | `sdd/adapters/bdd-tdd.md` | 0.3 → 0.4 | 完整 S1 v2.2 历史蓝图 + 完整 S4 v1.2 §25（§25.1–§25.8） 章节出处；updated=2026-10-10，追加脚注 |
| A12 | `sdd/adapters/contract.md` | 0.1 → 0.2 | 完整 S1 v2.2 历史蓝图；Contract 分类归于本文规则，保持 Agent_Side attribution；updated=2026-10-10，追加脚注 |
| A13 | `sdd/adapters/docker-container.md` | 0.4 → 0.5 | 完整 S1 v2.2 历史蓝图 + 完整 S4 v1.2 §23 章节出处；updated=2026-10-10，追加脚注 |
| A14 | `sdd/adapters/langchain-agent.md` | 0.2 → 0.3 | 完整 S1 v2.2 历史蓝图 + 完整 S4 v1.2 §22.4 章节出处；updated=2026-10-10，追加脚注 |
| A15 | `sdd/adapters/prompt.md` | 0.3 → 0.4 | 完整 S1 v2.2 历史蓝图 + 完整 S4 v1.2 §22.5 章节出处；updated=2026-10-10，追加脚注 |
| A16 | `sdd/adapters/python.md` | 0.2 → 0.3 | 完整 S1 v2.2 历史蓝图 + 完整 S4 v1.2 §22.1 章节出处；updated=2026-10-10，追加脚注 |
| A17 | `sdd/adapters/runtime-skill.md` | 0.4 → 0.5 | 完整 S1 v2.2 历史蓝图 + 完整 S4 v1.2 §22.6 章节出处；updated=2026-10-10，追加脚注 |
| A18 | `sdd/workflows/new-capability.md` | 0.1 → 0.2 | 完整 S2 v2.2 §4.5 出处；updated=2026-10-10，追加脚注 |

## 4. 任务与执行顺序

1. 已完成：Owner 批准八份 SDD 来源表达修改、新 working Plan、十四处历史项具名保留；批准仅绑定这些对象与表达差异，原文见 §1。
2. 已完成：复核基线、四份仓外来源与八份历史保护文件摘要，均与批准候选一致；按 G1 在上述独立 worktree 实施。develop 的既有未提交内容不携入、不覆盖。
3. 已完成：写入正式 working Plan，state=active 并记录实际决定；应用八份已批准候选差异。来源头部保持原行数，修订脚注只追加文末，降低旧锚位移风险。
4. 已完成：核验保留项、四处 P 字节、元数据、引用扫描与近邻负控；适用文档、原生静态与 Level A 离线检查实跑结果见 §6。
5. 在已获对应发布授权时同步 Issue 的实际处置账与验证结果，保持 OPEN，所有未完成 AC 如实保留。commit / push / PR / merge 分别按既定 Owner gate。

### 历史保留账（Owner 已于 2026-10-10 接受，原文保持）

| ID | 目标与基线定位 | 明确来源 | 保留理由 |
|---|---|---|---|
| A01 | `plans/[PLAN]_spec_anchored_refactor.md:134` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/spec-anchored-calm-lampson.md` | 原任务拟更新到 v2.3；当前源稿仅核验 v2.2，不改写任务完成状态 |
| A02 | `plans/[PLAN]_spec_anchored_refactor.md:156` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/spec-anchored-calm-lampson.md` | §10 R-G21，保留当时 hook 方案语义 |
| A03 | `plans/[PLAN]_spec_anchored_refactor.md:686` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/mj-agent-refactor-completion-assessment.md` | 原引用 v1.0 §4.2；当前源稿 v1.1，保留历史评估版本 |
| A04 | `plans/[PLAN]_spec_anchored_refactor.md:709` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/spec-anchored-calm-lampson.md` | §10，保留历史风险依据 |
| A05 | `plans/[PLAN]_spec_anchored_refactor.md:751` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/spec-anchored-calm-lampson.md` | §6 各 Phase 验收标准，保留历史验收依据 |
| A06 | `plans/[PLAN]_spec_anchored_refactor.md:774` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/spec-anchored-calm-lampson.md` | §9，保留历史终标准引用 |
| A07 | `evidence/ai-context-audit/2026-05-22_a3-readiness-eval.md:77` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/spec-anchored-calm-lampson.md` | §10 R-G21，保留 readiness 评估当时观察 |
| A08 | `evidence/ai-context-audit/2026-05-22_a3-readiness-eval.md:91` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/spec-anchored-calm-lampson.md` | §10 R-G21，保留历史出处 |
| A09 | `evidence/assessments/[ASSESSMENT]_Spec_Anchored_Refactor_Completion.md:35` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/mj-agent-refactored-structure.md` | 原对比基线 v2.2；原文声明 §0–§3 等为 v1.0 历史原文 |
| A10 | `evidence/assessments/[ASSESSMENT]_Spec_Anchored_Refactor_Completion.md:375` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/mj-agent-refactor-completion-assessment.md` | 保留源稿归属；当前源稿 v1.1，不替换为仓内派生件 |
| B01 | `policies/ai-agent.md:323` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/mj-agent-refactored-structure.md` | 历史修订说明，当前正文不依赖 vault；同时涉及实施蓝图 S1 |
| B02 | `policies/data-boundary.md:174` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/mj-agent-refactored-structure.md` | 历史修订说明，当前正文不依赖 vault |
| C01 | `evidence/codex-only-migration/p4-owner-relay/O2-boundary-stop-20260921.json:176` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/mj-agent-refactored-structure.md` | 保留原始 aggregatedOutput；是 B01 历史复本 |
| C02 | `evidence/codex-only-migration/p4-owner-relay/O2-success-20260921.json:137` | `D:/Document/My-Local-Vault/sdd-development/mj-agent/mj-agent-refactored-structure.md` | 保留原始 aggregatedOutput；是 B01 历史复本 |

A01–A10 仍是历史正文 / 出处引用，不与 B/C 混为一种语义；共同点是本包原文不改、来源在本账明确。最终原谓词残留目标为 7 文件 / 14 处（A 历史 10 + B 2 + C 2），只允许本账具名项；任何新命中或遗漏项均失败。
原始 25 处对账：5 处已由原生迁移删除 + 8 处本包当前正文修正 + 10 处 A 历史接受 + 2 处 B 历史接受。C 两处历史输出为后来新增复本，单列保留。
P01/P02：ADR-031 第135/137行；P03/P04：旧 refactor Plan 第50/51行；四行逐字节保持。已删除 hook README 的3处、capabilities/CLAUDE.md的1处、旧claude-code-skill adapter的1处不恢复。

## 5. 风险与恢复

| 风险 | 等级 | 控制 / 恢复 |
|---|---|---|
| SDD 元规则来源说明受保护 | Medium，Owner 必停 | 限定八份文件和候选差异；Owner 已批准，见 §1。不是四项 runtime in-source 修改。 |
| 将历史计划 / 评估换成当前论断 | Medium | 十四处历史项原始字节不动；新账明确历史版本与当前源稿差异。 |
| 本机 vault 其他读者不可达 | Low | 明示本机来源和核验版本，规则主体仍在仓内；不复制仓外资产。 |
| 误把实施方案当作手册章节 | Medium | S1 与 S4 分列；已核验章标题；Contract 分类归于本文，不制造不存在的专章。 |
| 头部行号位移 / 无关 diff | Low | 候选保持来源头部原行数，仅追加2行脚注；重扫路径+行号锚。 |
| 部分执行或宿主拒绝 | Medium | 对账已执行项；保留原错并按证据定位，受阻步骤返回 BLOCKED_EXECUTION_ROUTE；不换路线绕过。 |
恢复来源为基线 aa70360bc123c668afc5e42c31c5c2cb766467b6 的 Git blob；正式变更可逐文件恢复，但不覆盖用户其他未提交内容。

## 6. 验证矩阵

- 专项：扫描 Git 跟踪工作树文本和新增 Plan，核对 A/B/C/P 分类；残留只允许本账14项；新 working Plan 中来源引用均带完整路径。未提交的 HEAD / index 仍是基线，不能混报为实施后的数量。
- 原文保护：逐文件比较七份历史内容的字节摘要；P 四行从 Git blob 提取原始字节比较；确认 learning/、旧资产和 state 未被改动。
- 元数据 / 语义：八份 YAML 严格解析；只变 version/updated；adapter 的规则清单、契约路径和命令保持一致；Contract 仅替换出处自述。
- 文档：`uv run --frozen --no-sync python scripts/check_frontmatter.py`、`uv run --frozen --no-sync python scripts/check_wikilinks.py`；另按 kernel 自有键集核验八份 SDD（frontmatter 全仓脚本不覆盖 sdd/）。
- 原生：`uv run --frozen --no-sync python scripts/sdd/check_codex_native.py`、`uv run --frozen --no-sync python scripts/sdd/check_native_skills.py`，记录实际环境与输出；不把静态通过视为宿主批准。
- 检查负控：bare-name 应判未限定、完整路径应判已限定、空集必须失败；未登记残留应失败。
- CI、ruff、mypy、unit/eval 按修复时适用矩阵与授权验证；本包没有代码变化，不新增与实现镜像的测试。离线外部项统一 SKIP_POLICY_EXTERNAL_DEPENDENCY；本包无 live probe、容器、部署或凭据动作。
- 草案准备记录只证明候选差异 / 来源事实；完整检查在批准后的真实 worktree 上执行，不报告未跑检查为 PASS。

### 2026-10-10 本地验证实跑记录

环境：Windows，Python 3.13.5，uv 0.11.21；上述独立工作树，复用 develop 的既有 `.venv`，所有 uv 命令带 `--frozen --no-sync`，未同步依赖。以下是本次实施后的证据，不以批准前候选检查替代。

| 检查 | 实际结果 | exit / 边界 |
|---|---|---|
| 专项引用 / 原文 / 来源 / 元数据核对 | PASS：原始基线 16文件/25行；实施前 15文件/22行；工作树 7文件/14行，全部与具名账相符，无新未分类项 | 0；新增 Plan 同时扫描；原谓词按 `.md/.yml/.yaml/.py/.json` 物理行统计，排除 learning/archive/秘密路径 |
| 原文与差异保护 | PASS：八份历史保护文件原始字节摘要不变、P 四行不变；八份 SDD 与批准候选逐行一致，仅来源说明 / 元数据 / 修订脚注变化；既有 state 不变 | 0；Git diff 为八份修改 + 一份新增 Plan，其他面不动 |
| 反向引用与负控 | PASS：1019 行既有目标路径引用不变；55 处旧定位锚不变（54 历史 JSON + 1 sdd/gates）；裸名 / 相对路径、完整路径、空集、遗漏及未登记项负控通过 | 0；新增 Plan 的分类账为新增说明，未改写旧输出 |
| `python scripts/check_frontmatter.py` | PASS：150 canonical docs | 0；另对八份 SDD 自有键集严格解析，无重复键 |
| `python scripts/check_wikilinks.py`，`MJ_AGENT_A4_STRICT=1` | PASS：13 个归档文件自动发现，0 archive-ref violations；根5文件 0 unresolved targets | 0 |
| `python scripts/sdd/check_codex_native.py` | STATIC_PASS，errors=[] | 0；rule_loading UNKNOWN、Owner approval NOT_ASSESSED、host_enforcement NOT_TESTED；不作宿主批准证据 |
| `python scripts/sdd/check_native_skills.py` | STATIC_PASS，errors=[] | 0；host / services NOT_TESTED |
| `ruff check` | PASS：All checks passed | 0 |
| `mypy src/mj_agent` | PASS：48 source files 无类型问题 | 0 |
| `python -m compileall -q src tests scripts` | PASS | 0 |
| `python scripts/sdd/run_offline_pytest.py tests/unit -q` | PASS：1095 passed，30 subtests passed，1 skipped，1 warning，90.02s | 0；skip 是 non-Windows 场景；warning 是第三方 Pydantic class-based config 弃用提醒 |
| `python scripts/sdd/run_offline_pytest.py tests/eval -q` | PASS：93 passed，6.69s | 0 |
| `git diff --check` | PASS | 0 |

专项结果与命令摘要保存于本工作树被忽略的 `.mj-agent-local/issue-498/`，正式范围与核验结论在本 Plan 留痕。没有新增镜像实现的持久测试。

未验证项：完整 GitHub CI、未受本次来源表达修复影响的 capability / runtime / infra gate、宿主 enforcement 与 live / 容器 / 部署均未运行；离线外部测试不启用，统一遵循 SKIP_POLICY_EXTERNAL_DEPENDENCY。BDD/TDD 无运行行为变化，未作红绿测试声明。

Issue 状态：GitHub 页面于上述本地验证时显示 OPEN。GitHub API 两次只读请求网络超时，页面读取成功；上述实施阶段没有改写 Issue 正文、发布评论或关闭 Issue。上述验证时尚未暂存或提交；本轮发布已获批准，见 §1。Plan 保持 active，人工 merge 与最终验收仍待 Owner。

## 7. 完成标准

- [x] AC-1（本地）：A/B/C/P 全部登记，原25处及新增C复本数量闭环；Owner 接受保留项有实际记录。
- [x] AC-2（本地）：八处当前正文出处修正，来源文件 / 版本 / 实际章节核验；十处 A 历史具名接受。
- [x] AC-3（本地）：B 两项与 C 两项单列接受，原始历史内容 / JSON 输出不变。
- [x] AC-4（本地）：P 四行、learning 与已退出旧资产保护通过。
- [x] AC-5（本地）：八份 SDD version / updated / 脚注正确，既有 state 不变，Owner 对实际受保护修改已批准。
- [x] AC-6（本地）：按当前适用矩阵提供实跑证据与 PASS/WARN/SKIP，负控与空集失败验证完成，未跑项单列。
- [x] AC-7（本地）：反扫定位锚与全仓引用扫描闭环，残留14项全部与账匹配，无新未分类命中。
- [ ] 经批准的发布动作分别完成；Owner 人工 merge 与最终验收之前 Issue 保持 OPEN。

## 8. 关联与来源报告

- #498；#482/#483 历史 TBD 清理先例；#499/ADR-040 原生资产退出；#563/#578 当前离线验证口径。
- Codex：来源核验、候选差异、正式 Plan 与八份 SDD 修改、提交前自检及获批发布执行；验证结果记录于 §6。
- HITL：Plan Gate 1、八份 SDD 受保护表达变更及十四项历史接受已由 Owner 于 2026-10-10 批准；本包 commit / 普通 push / PR 创建已获本轮批准，见 §1。人工 merge 与最终验收仍按 Owner gate。
- BDD/TDD：无行为变更，不改规则；委派：NONE。

## 9. 提交前 AI 自检与发布对象

本地验证证据见 §6；本节为 AI 对最终差异的判断，不将测试通过当作自检结论。

| 文件 | Plan 锚点 | 差异与归类 |
|---|---|---|
| `sdd/adapters/bdd-tdd.md` | §3 A11 | 来源说明 / 元数据 / 追加脚注，in-scope；无 BDD/TDD 规则变化 |
| `sdd/adapters/contract.md` | §3 A12 | 来源说明 / 三处出处自述 / 元数据 / 脚注，in-scope；无契约变更 |
| `sdd/adapters/docker-container.md` | §3 A13 | 来源说明 / 元数据 / 脚注，in-scope；无 Docker 配置变更 |
| `sdd/adapters/langchain-agent.md` | §3 A14 | 来源说明 / 元数据 / 脚注，in-scope；无 agent 行为变化 |
| `sdd/adapters/prompt.md` | §3 A15 | 来源说明 / 元数据 / 脚注，in-scope；无 runtime Prompt 变化 |
| `sdd/adapters/python.md` | §3 A16 | 来源说明 / 元数据 / 脚注，in-scope；无 Python 代码变化 |
| `sdd/adapters/runtime-skill.md` | §3 A17 | 来源说明 / 元数据 / 脚注，in-scope；无 runtime SKILL body 变化 |
| `sdd/workflows/new-capability.md` | §3 A18 | 来源说明 / 元数据 / 脚注，in-scope；12-artifact 规则不变 |
| `plans/[PLAN]_498_vault_reference_clarity.md` | §3 Plan Create、§4 | 已批准的 working Plan、分类账、验证与发布记录，in-scope |

Scope drift：None，9/9 对齐；风味为文档 / SDD 元规则来源表达，未进入 runtime in-source 或 infra 实施面。风险 Medium（九文件及受保护 SDD 来源表达），对应修改已获 Owner 批准，结论 GO。

十二项自检：1 模块边界 PASS；2 真实来源 PASS（四份 vault 实读核验，无 biz 访问）；3 秘密 / 调试 / 个人配置 PASS（本机绝对路径是本任务已批准的来源定位，不是运行配置）；4 文档同步 PASS；5 提交格式 PASS；6 documentation × docs PASS；7 scope drift None；8 本地验证与 AI 自检分段 PASS；9 CHANGELOG N/A（仅文档）；10 documentation PR 模板及完整 Inventory / Docker Impact 已准备；11 5a 反扫 PASS；12 system.md version / EVAL backlog N/A（没有 runtime 改动）。

5a：既有路径及行号锚保持，历史十四项有具名处置，src/runtime 规则不变。5b：Create 行对应本 Plan 已创建。5c：没有 canonical 迁移、新高频入口或运行变化，INDEX / AGENTS / CHANGELOG 无同步缺口。5d：不涉及 SPEC Delta。

同一问题的 SDD 修复与配套 Plan 合为一个逻辑提交；跨 sdd / plans 治理目录按提交规范 §4.4 省略 scope。拟标题：`docs: clarify vault sources and retain historical references for #498`，正文使用 `Refs: #498`，PR 不使用自动关闭关键字。发布对象为上述分支、Gitee 与 origin 既有远端、GitHub `MJ-AgentLab/mj-agent` 的 develop base。

发布前远端只读核验：develop tip 仍为 aa70360bc123c668afc5e42c31c5c2cb766467b6，两端同名分支均不存在；同 repo/head/base 未找到既有 PR。实际 commit SHA、每端 push 结果及 PR URL 由工具成功后报告，不提前填写成功状态。
