---
type: plan
summary: Issue 582 最小离线 EVAL runner 的观测回放、规则评判与回归报告实施计划
owner: ranzuozhou
created: 2026-10-12
updated: 2026-10-12
state: active
track: code
---

# [PLAN] Issue #582 最小离线 EVAL runner

## 1. 追踪与 Plan 落盘批准

- Issue：[GitHub #582](https://github.com/MJ-AgentLab/mj-agent/issues/582)。
- Repo Scan：2026-10-11 会话中的仓库事实核查；2026-10-12 落盘前复核 Issue 与工作树，基线仍为 `develop@c91d3151d14388f3caab689e5045344c6a134196`。
- Owner 于 2026-10-12（Asia/Taipei）回复“执行推荐”，批准上一轮提出的 Plan 落盘范围；本次仅新增本文件并执行文档静态校验。
- 本 Plan 已采纳，故 working-doc `state: active`；不表示 capability 已激活或 runner 已实现。实施、SPEC／契约落盘、提交、推送、PR、live 采样均不由本次落盘授权。
- 后续新 capability 推荐归属 `data-agent.evaluation`，adapter 为 `python`、`tdd-bdd`，按 [[sdd/workflows/new-capability|new-capability workflow]] 推进；新共享契约的具体差异另交 Owner 审阅。
- Owner：ranzuozhou；拟执行者：Codex；合成业务／Prompt 与 SWE 核验角色按后续 §8.2 由 Agent 模拟，不要求真人参与。

当前范围：T-006已随#589合并；Owner于2026-10-12采纳A并授权T-007a baseline CLI接入、G1工作树、契约/文档、离线测试与Agent合成验收，见§8.9。actual/live、外部连接、核心规则、文件后端、runtime/CI/守卫/个人配置及提交/推送/PR不在范围。

## 2. 背景与 Repo Scan 事实

本节表格保存Plan初次起草时的仓库事实；当前实现和授权以§7及§8.9为准，不把历史“模块不存在”等描述当现状。

本任务补齐评判框架缺口：消费经批准、脱敏的实际 runtime 观测，形成逐 case 判定、测量完整性、总体与红线指标及兼容基线的回归报告。采样与 target 的 EVAL 承接仍由各自 Issue 负责；runner 自测不能作为 runtime 行为通过证据。

| 维度 | 仓内事实 | 首版处理 |
|---|---|---|
| 模块 | 不存在 `src/mj_agent/evaluation/`；`mj_agent` 根包无配置加载，但 `tools/__init__.py` 导入 SQL execution／introspection，后者加载 settings | 新建独立纯解析模块，避免导入应用工具包 |
| API／Studio／Chainlit | 文档中的 `mj_agent.evaluation.runner` 命令为候选占位；无实际 runner 入口 | 独立离线 CLI，不挂入现有服务入口 |
| 业务数据流 | 当前用例依赖 QCM 表族、周期与时间谓词等语义 | 使用显式批准的静态映射／脱敏参考输入，不推断真实上游 schema |
| 数据库 | 回放不需要 biz pg、memory PostgreSQL 或 Redis | 不连接任何数据库，不采集观测 |
| 配置／环境／部署 | 应用 `config.py` 在模块级构造 settings | 只接收显式本地文件路径，不加载应用配置、dotenv、凭据或部署 profile |
| n8n | 本项目不使用 n8n | 不适用 |
| 测试 | `tests/eval/` 现有 15 条 QVL seed 仅校验格式与参考 SQL 的 precheck，不调用 LLM | 不作为 runtime 行为基线；以独立 CLI 离线 fixture 为主要测试入口 |
| 文档治理 | #161 已有 draft EVAL 和 22 条 dataset；`baseline_value: 0.0` 为 placeholder，Run History 为空；无 #582 Plan／capability suite | 本文件承接执行计划，后续独立形成 SPEC／RUNBOOK 与 evidence |

#161 的 dataset 含 10 条 happy-path、6 条 edge、5 条 red-line、1 条 regression，共 28 个 `expected_output` 检查字段及 4 类 `expected_trajectory` 检查。全部检查须有明确支持路线；未知字段不得静默忽略。

事实依据：[[docs/evaluation/outcome_first-turn-time-predicate_v1.0|#161 draft EVAL]]、`docs/evaluation/datasets/first_turn_time_predicate_v1.jsonl`、`tests/eval/`、`src/mj_agent/tools/__init__.py`、`src/mj_agent/tools/sql/{execute,introspect}.py`。本次未验证 live schema、数据库状态或实际模型行为。

反向扫描不涉及符号重命名、文件移动、SQL 对象迁移、catalog 漂移或 runtime canonical 修改。既有 EVAL 的 runner 示例已明确为候选占位；后续以新 RUNBOOK 记实际命令，不在本次修改 #161 的文档或范围。

## 3. Scope 与后续 SPEC 决策输入

### 3.1 首版范围

- 包含：独立离线 CLI、输入与 manifest 校验、观测回放、规则评判、人工审阅记录回放、逐 case 状态、指标与回归报告、确定性与离线边界验证。
- 首批验收集：#161 的既有 22 条用例。#504 与 #583–#586 后续提供各自 dataset、检查与获批阈值；不把它们标为本首版已支持或已完成。
- 不包含：自动采样、LLM judge、定时任务、CI blocking gate、A8／A11 waiver 翻转、应用 tool／middleware／入口改造、runtime prompt／skill／catalog／guardrail／precheck 编辑、外部依赖执行路线。
- 输入禁止包含原始 biz rows、`business_summary`、PII 或凭据。首版消费经批准的脱敏输入；来源声明和有限字段校验不等于 runner 能自行证明脱敏或采样真实性。

下列为已采纳的设计方向，具体字段、schema 版本、公开接口及退出码值在后续 SPEC 中定义，本 Plan 不代替完整契约。

### 3.2 输入与观测来源

输入为 EVAL 配置、dataset、逐 case 观测 JSONL、运行 manifest，以及可选的人工审阅记录和历史基线报告；不自动获取 trace、不读取 runtime 配置、不访问网络服务。

manifest 绑定 commit、实际装配的 prompt／skill 内容摘要、dataset 摘要、模型身份与采样参数、时间基准和观测来源，并记录 judge／配置版本。实际装配摘要不能仅用 frontmatter 中的版本或短 hash 代替。时间基准是离线断言依据，不声称已冻结真实数据库的 CURRENT_DATE。

观测须保留完整、按顺序关联的工具调用、首次 `execute_sql` 的 SQL 参数、返回状态与错误，以及必要的脱敏回复片段。最终修正成功 SQL 不得替代首次尝试；错误回环不因后续成功而消失。证明“零调用”需要完整轨迹，缺少调用记录不能当作零调用。

实际观测与 synthetic fixture 明确区分。后者仅用于 judge／runner 自测，不能进入 runtime baseline。重复 case ID、未知 observation ID、非法格式或来源不明的输入必须显式报告，具体拒绝规则写入 SPEC。

### 3.3 检查支持路线

| 检查面 | 评判路线 | 必须保留的边界 |
|---|---|---|
| SQL 谓词、周期、窗口、JOIN fact 侧、单语句／DDL、SELECT 星号 | 直接使用 `sqlglot` AST 与显式静态参考输入 | 不能只检索字符串；无法可靠解析或缺必要观测时明确报告 |
| 工具调用次数、entity_lookup、首次执行成功、错误回环 | 完整工具轨迹 | 关联调用与结果；不以最终成功覆盖首次失败 |
| `[数据边界]` 等明确字面要求 | 确定性规则 | 字面通过不代表整段拒答语义通过 |
| 窗口披露、拒答、替代建议、澄清选项、预算提示的语义 | `REVIEW_REQUIRED`，消费绑定观测摘要的人工记录 | 关键词命中不能推定语义通过；观测变化后旧审阅失效 |
| `acceptable_any` | 按完整分支分别评判 | 不把不同分支的条件混合凑成通过 |

HP-03 的 daily／30d 与 monthly／3m 必须成对判断。EG-02 的“无需强制时间谓词”不能解释成“出现时间谓词就失败”。这些语义在 SPEC 与固定正反样例中明确，不修改原 dataset。

rule_based 校准沿用至少 5 条人工标注样例并保留正反例；每次实际 run 保留至少 10% 抽检及全部 5 条 red-line 审阅。语义争议按 #161 的 human_review 优先口径处理；已确认的调用、错误及 SQL 事实保留，不因人工说明而从报告删除。

### 3.4 报告、测量与回归

逐检查保留证据与理由，逐 case 使用 `PASS / FAIL / NOT_RUN / UNSUPPORTED / REVIEW_REQUIRED`。已确认的失败不得被缺观测或待审状态遮蔽；状态合并规则和完整性字段在 SPEC 中定义。

报告分开表达测量完整性、红线失败与基线比较结果：

- 展示计划数、已观测数、已判定数、缺失数、待审数及不支持项；完整 suite 未判完时，正式指标保持未测，不删除缺失项提高通过率。
- `0.0` 是否是基线取决于测量记录与来源证明；现有 placeholder 不参与比较，实测为零不能仅因数值为零被拒绝。
- 首版只比较条件兼容、审阅完成的实际基线。缺基线为 `NO_BASELINE`，条件不匹配为 `INCOMPATIBLE_BASELINE`，两者均不能声称 regression PASS。
- 兼容性核对 dataset、judge／配置、target 摘要、模型与采样、时间基准和 provenance；commit 作为绑定来源记录，具体兼容字段由 SPEC 固定。
- #161 保留整体下降 `>= 0.03` 的硬回归阈值及原 soft regression 口径；22 条中一个通过变为失败即下降 `1/22 ≈ 0.04545`。红线失败独立报硬失败，即使没有基线。
- #161 不同版本 A/B 可分别报告；未经批准的跨版本比较不强算为历史回归。采样仍按该 Issue 的原范围另行批准。
- 相同输入重复回放，判定与规范化报告内容保持一致。退出状态区分输入非法、判定不完整、无基线、基线不兼容和红线／硬回归；报告保留并存原因，具体码值及优先级由 SPEC 定义。

## 4. Documentation Decision 与任务顺序

### 4.1 文档矩阵

实现主题属于 code；capability-package 工件按 policies/documentation.md §3.1 规则 9 不适用 track。working Plan 使用本文件，不复制一套长期 SPEC 到 `plans/`。下表是原 Plan 阶段的未来动作；2026-10-12 后续授权与实际文档进展另见 §8.1。

| Type | Action／Path | Existing Target | Reason／Evidence | Track | Required Before |
|---|---|---|---|---|---|
| Plan | Create：本文件 | 无同名或 #582 Plan | Stage 3 核查与 Owner 确认；承接 #582 | code | SPEC／Implementation |
| SPEC | Create：`capabilities/data-agent/evaluation/{spec.yml,requirements.md,design.md,contracts/,trace.yml}` | 无 evaluation capability suite | #582 REQ-001–006／AC-1–7；固定输入、状态、比较及离线契约 | 不适用（capability-package） | Implementation；具体契约另经 Owner 审阅 |
| ADR | None | ADR-024 及现有数据边界决议 | 沿用既有框架与约束，无新政策决策 | — | 如后续出现决策冲突再评估 |
| RUNBOOK | Create：`capabilities/data-agent/evaluation/runbook.md` | 无回放 RUNBOOK | AC-8；输入准备、人工审阅、回放、报告解释与排错 | 不适用（capability-package） | PR／Release |
| GUIDE | None | — | 首版操作集中在 RUNBOOK | — | — |
| STANDARD | None | 现有政策／SDD／文档规则 | 不改变门禁、waiver 或采样政策 | — | — |
| Local ISSUE | None | GitHub #582 | 已有独立问题锚，不重复开单 | — | — |
| ASSESSMENT | None | — | runner 回归报告记入 capability evidence，无优化前后实测 | — | — |
| CHANGELOG | 后续 Update：`CHANGELOG.md` | 根 CHANGELOG | 实施完成后记录新增离线 runner；本次只落 Plan | — | 实施后的 Commit／PR |
| INDEX | 后续 Update／Regenerate：`docs/INDEX.md`、`capabilities/INDEX.md` | 既有入口 | AC-8；canonical suite 形成后同步，本 working Plan 无新增 canonical 入口 | — | PR |

### 4.2 后续文档准备

先按 `sdd/templates/` 形成 requirements、design、契约草案、BDD examples／behavior.feature、tasks、trace 和 RUNBOOK；不自行发明 capability 元数据字段。新公开接口与共享契约具体差异经 Owner 审阅后，才进入获批实施范围。

### 4.3 未来实施纵切

主要测试入口为独立 CLI 的固定脱敏 fixture；每片从输入到报告端到端可验，预期全部为 A 纯代码。无 B runtime canonical 或 C infra 修改。

| 任务 | 内容与验证 | 依赖 | AC |
|---|---|---|---|
| Stage 8a：输入校验到缺观测报告 | 最小 CLI；22 条均有结果；缺观测、未知字段、重复 ID、非法输入正反 fixture | SPEC／契约获批 | AC-1、AC-3、AC-4 |
| Stage 8b：首轮 SQL 与轨迹评判 | 首次尝试、AST、调用次数、entity_lookup、错误回环到报告；首次失败后修正的固定反例 | 8a | AC-2 |
| Stage 8c：人工审阅回放 | 语义待审与人工记录绑定；失效记录、分支、正反校准样例 | 8b | AC-2、AC-3 |
| Stage 8d：指标与回归报告 | 未测、fixture-only、无基线、不兼容、阈值边界、红线、重复回放与退出状态 | 8c | AC-3–6 |
| Stage 8e：离线边界与文档收口 | 文件／网络访问负例；RUNBOOK、trace、evidence、INDEX、范围审阅 | 8d | AC-7、AC-8 |

以上任务待实施，不在本次创建源码、测试或 fixture。

## 5. 风险、恢复与 HITL

本次 Plan 落盘风险 Low；未来 runner 的公开输入／报告契约和安全判定按 High 处理。没有触及四项 in-source 专属必停面，也不借此授权编辑既有冻结契约。

| 风险 | 等级／风味 | 缓解与恢复 |
|---|---|---|
| 缺观测、待审或 fixture 被误算 PASS | High／A | 完整性与来源独立表达；固定负例；发现误判后停止将相关报告用于验收并离线重放 |
| 最终修正 SQL 掩盖首次失败 | High／A | 保留首次参数、调用关联与错误序列；用“失败后成功”反例验证 |
| 不兼容或占位基线生成回归 PASS | High／A | 审核基线来源与兼容条件；保留 NO_BASELINE／INCOMPATIBLE_BASELINE |
| 导入工具包间接加载 settings 或外部客户端 | High／A | 纯解析依赖和显式输入；文件访问／网络负例；不导入 agent、tools、config、LLM 或 DB 模块 |
| 时间、周期或回复语义被字符串规则误判 | High／A | AST 与批准的静态映射；不确定项人工审阅；版本化 judge 与校准记录 |
| 本 Plan 被解释为编码或 live 授权 | Low／文档 | §1／§3 明确当前授权；实施与新增契约具体差异另审阅 |

恢复只针对本任务新增资产，依据实施前 Git 基线逐项撤销；不回写 runtime、不覆盖其他任务内容，不删除其他人的文件。Git 提交、推送、PR、merge 与删除均沿用各自独立授权边界。

本次仅完成 Gate 1 的 Plan 采纳与落盘。后续 SPEC／契约需形成可审阅具体差异，业务／Prompt 与 SWE 独立审阅条件需落实；真实采样、外部 profile、CI gate 与 waiver 翻转继续单独审批。

## 6. 验证计划与本次记录

### 6.1 后续 runner 实施验证（尚未执行）

- 固定期望文件由人工独立编写，不由待测代码生成；使用临时目录，不依赖开发机绝对路径或个人配置。
- 主要入口为 CLI 离线 fixture；覆盖 §4.3 五片及 AC-1–8 的正反例。Agent／CI pytest 一律经既有受控 runner，不改变其执行边界。
- 新测试文件路径和 BDD steps 由 SPEC／tasks 阶段明确；独立离线测试优先只运行本次相关文件，再按失败或未解决问题决定扩展。

```text
uv run ruff check
uv run mypy src/mj_agent
uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py <本次获批的离线测试文件> -q
python scripts/check_frontmatter.py
python scripts/check_wikilinks.py
python scripts/sdd/check_capability_schema.py --all
python scripts/sdd/check_traceability.py --all
python scripts/sdd/check_contracts.py --all
python scripts/sdd/check_bdd_scenario_trace.py --all --scope full
python scripts/sdd/check_bdd_acceptance.py --all --strict
```

仅在 canonical suite 已形成且处于获批范围时校验相关 capability／BDD 链路。任何 static PASS、policy SKIP 或 runbook fallback 均不能替代实际 runner 测试／runtime EVAL 证据。凭据存在不启用外部测试；本首版不运行 live probe、容器生命周期或数据库／LLM 调用。

### 6.2 本次 Plan 文档校验

执行日期：2026-10-12（Asia/Taipei）。只运行既有 frontmatter／wikilinks 脚本与本文件的显式链接、内容及范围核对。使用已有 `.venv/Scripts/python.exe`、`-X utf8 -B`，未安装／同步依赖。

| 检查 | 实际结果与覆盖边界 |
|---|---|
| frontmatter 脚本 | exit 0／PASS；151 份 canonical docs 合法，包含本 Plan |
| wikilinks 脚本 | exit 0／PASS；13 份 archived files 的 archive-ref 为 0 violations；临时进程内 `MJ_AGENT_A4_STRICT=1` 时 5 份 root files 为 0 unresolved targets；未修改门禁配置 |
| 本 Plan 显式链接 | exit 0／PASS；单独调用既有 `scan_links` 核对本文件，0 violations；全仓脚本本身不覆盖 Plan 链接，故未用它替代此项 |
| 本 Plan 内容静态核对 | exit 0／PASS；8 个主体段、AC-1–8 映射齐全，owner／日期／state／track 合法，summary 46 字符；dataset 仍为 22 条、28 个输出字段、4 类轨迹字段 |
| 空白与文件范围 | exit 0／PASS；本 Plan 无尾随空白；已跟踪 diff 为空、`git diff --check` 无输出；新文件仅本 Plan，另有落盘前已存在的 `.playwright-mcp/`，未处理；HEAD 仍为上述基线 |
| A1／A2／A3 | PASS；working Plan 路径、前缀、元数据与 active／code 语义符合已采纳计划 |
| A4 | PASS；按上述全仓脚本与本文件单独链接核对分别记录覆盖 |
| A5／A6 | SKIP；仅 working Plan，无新增 canonical 入口、全局规则或高频运行信息，不触发 INDEX／AGENTS 同步 |
| A7–A14 | SKIP；不是 agent canonical、CONTRACT、开发技能或原生配置修改 |
| OB1 | SKIP；Plan 无本技能给定的长度硬阈值 |
| OB2–OB5 | 人工静态审阅 PASS；已完成／未来任务区分，未塞入实现代码或完整 SPEC，摘要明确，各段授权与 AC 状态一致 |

以上仅为文档静态证据，不证明 runner、BDD／TDD 或 runtime 行为通过。

### 6.3 Plan 落盘轮次自检范围

5a 无符号／路径／SQL 对象迁移，无 runtime canonical 或 catalog 编辑；5b 本 Plan 已形成；5c 本次无 canonical 入口、AGENTS 或 CHANGELOG 同步；5d 无已实施 SPEC Delta。scope drift 预期为 None。

## 7. 完成标准与当前状态

| AC | 完成证据 | 任务 | 当前状态 |
|---|---|---|---|
| AC-1 | 22条结果、缺观测、未知检查、非法输入反例 | 8a | 核心及Windows synthetic CLI PASS；actual入口延期 |
| AC-2 | AST／轨迹／错误回环及绑定角色正反例 | 8b、8c | 合成核心PASS；实际观测校准未执行 |
| AC-3 | fixture隔离、零值、placeholder、完整分母 | 8a、8c、8d | 核心PASS；无runtime基线 |
| AC-4 | manifest绑定与兼容键差异反例 | 8a、8d | 核心PASS；实际来源真实性未核验 |
| AC-5 | 精确阈值、红线、无基线、21/22下降 | 8d | 核心PASS；不扩展其他EVAL阈值 |
| AC-6 | 规范化回放一致与报告分类 | 8d | 核心及Windows synthetic CLI退出／输出PASS；actual比较延期 |
| AC-7 | 核心无IO／应用导入／网络哨兵、受控pytest、ruff/mypy | 8e | Windows synthetic CLI路径／重解析点／碰撞与baseline接入PASS；Linux/macOS延期 |
| AC-8 | 文档、索引、trace、报告与范围核查 | 8e | 核心与CLI含baseline契约已对齐真实API；actual／平台继续延期，完整capability未验收 |

#582 保持 OPEN；本次不勾选远端验收项。完成 runner 后仍需 Owner 验收及获批的交付流程；不自动关闭 #161、#504 或 #583–#586，不改变 #564 已按“覆盖与承接完成”关闭的结论。

## 8. 关联、实施来源与未验证项

- 来源矩阵：[GitHub #564](https://github.com/MJ-AgentLab/mj-agent/issues/564)。
- 保留既有 scope：[GitHub #161](https://github.com/MJ-AgentLab/mj-agent/issues/161)、[GitHub #504](https://github.com/MJ-AgentLab/mj-agent/issues/504)。
- 后续消费方：[E1 #583](https://github.com/MJ-AgentLab/mj-agent/issues/583)、[E2 #584](https://github.com/MJ-AgentLab/mj-agent/issues/584)、[E3 #585](https://github.com/MJ-AgentLab/mj-agent/issues/585)、[E4 #586](https://github.com/MJ-AgentLab/mj-agent/issues/586)。probe-fixture 为不适用，不纳入行为 EVAL。
- 依据：[[decisions/ADR-024_Eval_Framework_Spec|ADR-024]]、[[policies/ai-agent|AI agent policy]]、[[sdd/lifecycle|lifecycle]]、[[sdd/workflows/new-capability|new-capability workflow]]、[[docs/_templates/TEMPLATE_PLAN|Plan 模板]]。
- 未来目标：`src/mj_agent/evaluation/`、获批的离线测试／固定 fixture、`capabilities/data-agent/evaluation/` suite；具体文件清单待 SPEC／tasks 明确。
- Plan 落盘轮次实际目标：仅 `plans/[PLAN]_582_offline_eval_runner.md`。源码、runtime 资产、dataset、测试、既有契约、政策／SDD、CI、原生配置和其他工作树内容均未修改；后续 Stage 6 文档增量见 §8.1。
- 实施来源：Codex；HITL：Owner 已批准 Plan 落盘；BDD/TDD：计划已映射，未实施／未执行；Subagent dispatched：NONE。
- 未验证：runner 行为、人工校准、所有 #582 AC 的实施证据、实际观测、模型／数据库环境、live EVAL、远端 CI。未提交、推送或创建 PR，未发布 Issue 更新。

Plan 落盘轮次在文档校验结束；当时的下一阶段为独立 SPEC／契约草案及具体审阅。后续 Owner 回复“执行”后的范围和进展如下。

### 8.1 2026-10-12 后续 Stage 6 文档准备

Owner 在 Plan 落盘后回复“执行”，据既有下一阶段继续准备 SPEC／RUNBOOK 与具体契约审阅草案；暂不编码、修改 runtime 或执行 live EVAL 的边界保留。本轮形成 capabilities/data-agent/evaluation/ 的 spec.yml（idea）、requirements.md／design.md／runbook.md／tasks.md（draft）及部分 trace，并同步人工／生成索引。capability-package 工件不适用 track；last_verified=null，不用静态校验伪装运行验证。

正式 contracts/python.contract.yml 和 contracts/behavior.feature 的完整具体提案放在 design.md §3.1／§3.2，待 Owner 对差异批准后再落盘；尚无源码、测试、fixture、BDD／TDD 或实际采样。AC-1–7 均 NOT_RUN；AC-8 有 Plan／SPEC／RUNBOOK 草案，正式契约、实现验证与最终验收仍待完成。未提交、推送、创建 PR 或发布 Issue 更新。

本轮 G1／G2／G9 与文档静态检查通过；G3 实际 exit 1，原因 contracts/ directory missing。完整套件未满足，未把 G2 的部分链路结构 PASS 当承接验证完成；具体记录见 [[capabilities/data-agent/evaluation/design|SPEC design]] §5.1。

### 8.2 2026-10-12 Owner 四项执行原则

Owner 明确要求：Agent 承担技术操作，Owner 只补必要信息、作实质决定和授权；合成验收由 Agent 模拟角色并独立核验，不要求真人参与；严格窗口保留，缺能力时延期入口、核心可先交付；具体范围集中授权，未实质变化时复用。

据此继续当前已给出的 SPEC §2／两份具体契约及关联文档范围：落盘 python.contract.yml 和 behavior.feature，补 REQ→BDD→CONTRACT trace；Agent 准备并独立静态核验合成角色材料。合成来源保留 agent_simulated 标记，不冒充实际行为基线或真人签署。窗口／周期配对、完整 suite 分母、时间基准、兼容键及阈值均不放宽。

当前仅交付核心规范／契约，尚无核心源码。CLI 与 actual 入口能力不足时明确延期，既有暂不编码、runtime／live、Git 发布和 Issue 状态边界仍有效。技术文件整理、命令与静态验证由 Agent 执行；相同动作／对象范围不再重复确认。

合成材料与当前验证记录见 [[capabilities/data-agent/evaluation/evidence/reports/2026-10-12_agent_synthetic_review|Agent 合成角色静态核验]]。BDD automation_status 仍为 unautomated，真实 tests／PR／runner evidence 未填；本次不据静态门禁关闭 #582。

本轮 G1／G2／G3／G9 与 G19 结构／链接检查通过；G21 为六场景 RUNBOOK 延期说明 fallback，不是运行通过。Python API checker实际失败因源码不存在，CLI入口为 DEFERRED_NO_IMPLEMENTATION。合成窗口样例由既有sqlglot独立提取AST事实，比例阈值用精确分数核对；严格条件与仓内dataset／catalog摘要均未变，未执行SQL、runner、BDD／TDD或live。

### 8.3 2026-10-12 已授权离线核心编码与合成验收

Owner回答“授权离线核心编码（推荐）”，集中范围为独立evaluation核心、必要离线测试、Agent合成角色验收与回归报告；CLI／actual入口继续延期，不改既有runtime、不执行live，不提交／推送／创建PR。未实质变化的后续技术操作复用授权。

Agent通过git worktree add创建feature/582-offline-eval-core，基线仍为c91d3151d14388f3caab689e5045344c6a134196。实施来源Codex；Methodology=red-green；Subagent dispatched=NONE。固定合成期望先于实现，Domain／Prompt标签与SWE独立核验由同Agent分轮执行，不是独立真人或子Agent签署。

RED首先为缺mj_agent.evaluation模块；新增反例随后暴露日期溢出、单次拒绝误判回环、不自洽基线、缺观测绕过检查类型校验，均先红后修复。63项单元与6项BDD通过；重复核心回放的规范化结果一致。受控runner拒绝pytest_plugins绑定后，按既有tests/bdd/<domain>/<capability>单模块布局修正；未改守卫、runner或权限。

仅新增src/mj_agent/evaluation/五份私有核心源码、测试及固定fixture，更新本capability／Plan／索引／CHANGELOG。公开main契约不改，runner.py不存在；capability仍idea、last_verified=null，#582及其他Issue状态未动。部分测试构造虚构actual条件验证分支，未生成或保存actual报告、授权凭证或runtime基线。

交付与验证命令、结果、范围和延期清单见 [[capabilities/data-agent/evaluation/evidence/reports/2026-10-12_offline_core_acceptance|离线核心验收报告]]；合成回放JSON／Markdown为SELFTEST_ONLY，runtime metrics=null、baseline_eligible=false、分类码3。既有dataset／catalog摘要未变。

### 8.4 2026-10-12 提交与PR授权

Owner在收到核心交付及main契约检查失败说明后明确要求“提交PR”，授权本工作树已审阅成果的暂存／提交、按Gitee→origin普通双推和创建以develop为base的PR；不包含merge、删除、runtime改动或live EVAL。

按逻辑拆分核心／测试与契约／文档／证据两次提交。采用既有eval scope覆盖EVAL相关代码，不引入新scope。PR使用feature模板并保留全部HITL Inventory及Docker Impact；关联使用Refs #582，不声明关闭。公开main锚点仍延期，V1检查为CI阻断项，故创建Draft供审阅，不宣称已满足合并条件。先前“未提交／无PR”的记录描述交付轮次，不代表本次发布授权被禁止。

核心／测试已提交为007820e77e0e22ec36ee8d1f99d70de95f4595c8（17份文件）；实际author／committer为仓库配置身份ranzuozhou，Codex实施来源在本Plan与PR中声明，不伪造协作者trailer。契约／文档／证据随后独立提交；本节不预填尚未取得的远端结果。

### 8.5 #587 BLOCKED修复的集中批准

Owner已采纳具体提案：公开schema.ReplayInputs冻结dataclass（七bytes字段，reviews／baseline默认b''）及core.replay(inputs: ReplayInputs) -> dict[str, Any]，Python契约绑定这两个真实源码／符号；CLI main移为SPEC／T-006延期候选，现有69项测试迁移公共入口。同步相关文档、验证、提交、按Gitee→origin普通双推、更新#587正文，CI通过后转Ready。此授权不包含runtime／CI／审核规则修改、live、merge或任何Issue关闭。

审核账号答复“不指定”：不发送GitHub审核请求，真实Approve未获得前不宣称BLOCKED完全解除。原§8.4的已知V1失败与Draft状态为历史发布记录，当前是否Ready以实际远端状态为准。

TDD：两份测试先改公共导入，受控runner实际RED为缺replay的两处收集错误；实现后原69项GREEN。公开ABI字段／默认值／不可变性／签名另补1项，合计64项unit＋6项BDD。私有兼容别名保留，规则／固定期望不变，未新增依赖。具体验证与最新合成回放一致性见[[capabilities/data-agent/evaluation/evidence/reports/2026-10-12_public_core_contract|公共API契约修复证据]]。

### 8.6 2026-10-12 Agent-first试点的离线CLI软件交付

Owner明确要求IMPLEMENT Agent-first计划，覆盖#582 CLI文件接口、main公共契约、相关文档和离线验收。协调Agent委派Codex在feature/582-offline-eval-cli工作树实施，基线为develop@5b8833c523f4401de7b70deb5a82b908f3a9c763。旧草案／执行记录保留；不重建已合并#587核心、不改四项runtime面、不连接服务。

CLI新增普通本地输入、URL／UNC／秘密／重解析点及Windows网络驱动器拒绝、10MiB有界读取、固定报告独占创建、IO安全错误及实际进程退出。ReplayInputs／replay、32类规则、严格窗口、阈值及兼容性不变；当前报告移除过时CLI延期说明，历史报告不改。cli.contract.yml正式绑定main，原核心契约仍独立冻结。

TDD RED为缺runner模块；GREEN为136项unit与9项BDD，ruff与全src mypy通过。测试中的actual分支为具名虚构条件，实际runtime采样、来源／脱敏真实性及actual接受未验证；不关闭#582、Plan保持active、capability仍idea／last_verified=null。

复现与候选版本绑定见[[capabilities/data-agent/evaluation/evidence/reports/2026-10-12_offline_cli_acceptance|CLI软件验收记录]]。独立核验、平台门禁、Owner接受及发布由协调者分别记录；本委派不提交／推送／创建PR／merge。新CLI测试仅作具名本地暂存供既有硬化runner验证，不产生执行授权凭证。

### 8.7 2026-10-12 接续的 synthetic-only 接受基线

Owner在“整理 #564 EVAL 承接方案”线程明确选择“采纳并授权离线 CLI 实施（推荐）”，集中批准main(argv, *, repo_root)、显式synthetic开关、manifest先读且actual早拒绝、baseline文件参数延期、私有有界安全IO、新目录报告与真实进程退出、固定期望/必要CLI测试/四个BDD、正式契约与具名文档/证据同步。仅精确暂存tests/unit/test_eval_runner.py与tests/unit/fixtures/eval_cli/expected.json供受控runner验证；不commit/push/PR或发布/关闭Issue，不改既有runtime/CI/守卫，不执行actual/live。

同名并行候选出现后，Owner另明确选择“授权协调并由本线程接续（推荐）”。原协调任务已确认#582写入和测试停止、无在途操作，并转交feature/582-offline-eval-cli（HEAD 5b8833c）。22份原未提交候选已原bytes备份在develop/.mj-agent-local/582-t006-cli-proposal/parallel-handoff-snapshot；历史验收记录保留，旧145项证据不计本轮新方案通过。

目标源码为独立runner.py/私有_file_io.py；保留ReplayInputs/replay、schema/judges、32类检查、严格窗口/阈值/兼容键。接口为main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int；仅synthetic_fixture进入文件回放，actual标签在其余载荷读取/replay/输出创建前拒绝；所有路径受可注入普通本地root约束，输出必须新目录且父目录已存在。平台能力不足延期入口，不回退普通open。三处报告延期值和core docstring更正，历史报告不重写。交接中的cli.contract.yml保留并与同一main/本轮不变量对齐，不新增另一个CLI契约或删除原成果。

T-006a文件/来源拒绝，T-006b报告/进程，T-006c固定合成角色/相关回归，T-006d真实源码后的契约/BDD/文档/证据闭合。当前RED：公开签名缺repo_root、缺synthetic开关时仍读取输入；受控runner实测2 FAIL/72 deselected。actual文件入口、采样、baseline CLI输入及来源真实性继续延期；#582 OPEN、Plan active、capability idea/last_verified=null，其他Issue与probe-fixture原结论保持。

本轮接续交付结果：T-006a–d VERIFIED_OFFLINE_SOFTWARE（供Owner最终接受）；main与私有IO仅交付Windows固定NTFS synthetic文件入口。Linux/macOS缺等价祖先rename保护能力，入口DEFERRED_FS_CAPABILITY，不留不满足root约束的降级实现；这是已批准“缺能力延期入口”的适用，不降低窗口或接受条件。

最终fresh证据：64 core + 105 CLI unit + 10 BDD = 179 passed（20条第三方DeprecationWarning）；全仓ruff、全src mypy55文件通过。G1/G2/G3/G9各1P/0W/0F；G19/G21各10P/0W/0F，G22空subset；V1默认12P/13W/0F，信息WARN保留。原并行145项及中间171项只为历史/中间结果，不替代最终候选。169项unit与10项BDD为当前结果。

OFFLINE/RECALL与流构造泄漏反例分别实测RED再修复；拒绝哨兵补充assert_not_called/读取次数，防止“异常被转2”伪装成未触发IO。核心schema/judges/ABI、原固定fixture/期望、窗口/阈值/兼容键未改；仅指定的三个报告文案与core docstring更正改变当前报告字节，历史报告保留。原34条Agent角色review绑定与22条原SQL/轨迹/回复在独立SWE轮复核，无本线程子Agent委派。

当前版本绑定与双段自检、平台延期、逐命令证据见[[capabilities/data-agent/evaluation/evidence/reports/2026-10-12_synthetic_cli_acceptance|synthetic-only CLI验收]]；candidate UNCOMMITTED，源码/契约/测试/fixture摘要f05fd48367e8a1a3b33d63d1f330835d8085541d8f8cbc1e06c9fe1fca4840eb。spec/draft文档升0.5，last_verified仍null。只读核查#582/#161/#504/#583–#586 OPEN，#564 CLOSED；本轮未更新Issue、未commit/push/PR/merge、不改runtime/CI/守卫、不执行actual/live，Plan保持active。

发布准备补充：CI采用Linux runner。本线程执行mypy --platform linux先观测私有Windows IO的6处attr-defined错误；补入sys.platform条件与显式成员类型后，Windows与Linux类型模型均55 source files通过，全仓ruff通过，179项相关离线测试重新通过。Linux类型检查是静态证据，不是Linux原生CLI实跑；actual/baseline与Linux/macOS文件入口仍延期，未改CI、守卫、核心规则或既有runtime。新候选摘要已同步版本绑定；旧摘要42f6de13…仅对应前一交付轮次。Git暂存/提交/普通双推/Draft PR具体发布方案已在本地准备，当前发布授权仍待Owner决定。

### 8.8 2026-10-12 T-006 Git发布的集中批准与提交事实

Owner明确选择“授权提交、双推和 Draft PR（推荐）”：按已审阅31份文件清单精确暂存，feature/582-offline-eval-cli两次逻辑提交（代码/测试10份，契约/文档/证据21份），按Gitee→origin普通双推，以develop为base按保存正文创建Draft PR，并核查当前head的CI。允许仅补真实授权/提交/PR事实；不改既有runtime/CI、不执行actual/live，不转Ready、请求账号审核、合并、删除或关闭Issue。原暂不Git发布约束仅在这些动作和对象内解除，后续相同范围复用。

C1代码/测试实际提交28925619c45ce7c35a376754c439885c0300f510，消息feat(eval): add synthetic-only offline CLI；author/committer使用已核实仓库配置ranzuozhou，无伪造协作者trailer。精确10文件；源码/契约/测试/fixture原bytes验证摘要仍f05fd48367e8a1a3b33d63d1f330835d8085541d8f8cbc1e06c9fe1fca4840eb。C2将记录契约/文档/证据及本批准事实；当前记录时C2、双推和PR尚未执行，不预填未来SHA/URL/CI或Approve。

两端develop及本次base均5b8833c，提交前两端同名远端分支和PR均不存在。若后续tip/内容或宿主能力变化，仅暂停对应动作并按实际证据处理；不force、不改hook或工具路线规避拒绝。完整capability与#582接受尚未完成，Plan继续active/idea/null。

### 8.9 2026-10-12 T-007a 的集中实施授权与交付

Owner明确回复：“采纳 A，授权按上述范围实施 T-007a，创建 G1 工作树，完成 baseline CLI 参数、契约与文档同步、必要离线测试及 Agent 合成验收。”同时明确actual/live、外部连接、核心规则、文件保护后端、runtime、CI、守卫、个人配置保持不动；不提交、推送或创建PR，#582/Plan/capability状态保持。此为T-007a的新具体授权，不借用T-006授权扩展。

已核实develop与两份本地远端跟踪引用均a96d759c080f4568e6810084f90fadce7b2c75cf，已跟踪diff为空，既存.playwright-mcp保留；未联网重新确认远端tip或Issue状态。G1实际git worktree add ../feature/582-baseline-cli -b feature/582-baseline-cli develop，exit0；新工作树HEAD与基线一致，inside-work-tree=true。#589 MERGED/五项CI成功来自既有具名收尾记录与本地merge提交；未重复收尾或修改历史验收文件。

实施风味A，触发declared-contract-change已获上述批准。只改runner.py：可选--baseline读取原bytes、缺省b''、空/JSON object前置校验。两份main签名不变，核心/schema/judges/report/_file_io、窗口/阈值/兼容键、原dataset/catalog与runtime原bytes保持。合法JSON object不等于实测基线；synthetic仍NOT_EVALUATED，actual早拒绝覆盖baseline，原生Linux/macOS缺能力入口仍延期。

TDD观察16 FAIL/135 deselected（旧CLI不接受baseline）；当前64 core+156 CLI unit+11 BDD=231 passed，22条第三方gherkin DeprecationWarning保留。新测试诊断码期望曾与原NON_FINITE_JSON不符；属性注入首次发生在校验后，后改为系统元数据返回点；均只修测试，不改规则或保护后端。Agent模拟Domain/Prompt并以SWE轮核验22-case/34-review原始输入和baseline自测，Subagent dispatched=NONE，不要求真人参与合成验收。

[baseline CLI验收](../capabilities/data-agent/evaluation/evidence/reports/2026-10-12_baseline_cli_acceptance.md)记录离线门禁、可复现进程证据、角色事实和当前原bytes绑定。旧21文件绑定中behavior.feature因Git text=auto检出CRLF，LF对应历史hash；不冒称当轮raw fingerprint匹配旧值，当前证据重新绑定。历史合成报告固定复制成baseline.synthetic.json，不用待测代码生成期望或伪造actual基线。

任务依赖：T-007a文件适配独立交付→T-007b真实来源/脱敏/批准与independent_review路线→另批actual文件入口→各target验收；Linux/macOS等价保护能力独立验证，缺能力继续fail closed。#161的跨版本A/B不通过same_target_replay，需另议具体比较契约；#504/#583–#586继续各自dataset/阈值/scope，probe-fixture不适用。T-007剩余actual/来源/target/平台部分仍NOT_RUN/DEFERRED。

本轮软件VERIFIED_OFFLINE_SOFTWARE供Owner最终接受，candidate UNCOMMITTED；#582 OPEN、Plan active、capability idea/last_verified=null，无Git发布或Issue状态变化。恢复入口为实施前a96d759与固定输入；保留本轮输出，不自动覆盖/删除报告或处置其他工作树。完整验证与文档自检结论以验收报告为准。

## 8.9 T-007b — 已批准的纯内存来源检查子项

2026-10-12 Owner回复“执行待办推荐事项”，采纳集中确认A：在现有G1工作树新增纯内存inspect_source API、必要离线测试、契约/文档同步及Agent合成验收。此前T-007a批准不作为本项授权；本次授权单独覆盖新公开API与declared-contract-change。不得提交、推送或创建PR，不启用actual文件入口，不连接外部服务，不改runtime、CI、守卫、个人配置、核心/schema/judges/report或文件保护后端。#582 OPEN、Plan active、capability idea/last_verified=null保持。

实施顺序：复核T-007a原bytes绑定并保存38文件本地快照及tracked.patch → 固定独立expected与失败测试 → 新增src/mj_agent/evaluation/inspection.py → 新增BDD与离线回归/哨兵 → 同步契约文档 → Agent模拟Domain/Prompt并由同Agent独立SWE轮复核原输入及结果。Subagent dispatched=NONE；Owner只作最终接受，不参与常规构建。快照在.mj-agent-local/t007b/t007a-snapshot，原23文件fingerprint为5ccaea17f46a43cc23eb01671f998ca86e9542453c1f2bd41d01b9c578310df5；历史T-007a报告/绑定不覆盖。

公开签名inspect_source(inputs: ReplayInputs) -> dict[str, Any]，只消费既有七份bytes，复用既有schema._load校验，不调用replay/judge、不读取或解析引用目标、不连接服务。输出schema_version=offline-source-inspection-v1；input_status为VALID/INVALID，coherence_status为CONSISTENT/INCOMPLETE/NOT_CHECKED；固定source_evidence_status=UNVERIFIED、target_evidence_status=UNVERIFIED、review_coverage_status=NOT_CHECKED、runtime_metrics=null、baseline_eligible=false。exit_code是API返回分类：非法2，结构检查3；不新增CLI参数或进程入口。

结构层校验schema、eval/run身份、四份原bytes hash及22条case/5条红线集合；输出计划/观测/完整观测/提供与绑定review计数、缺观测ID、完整性缺口和逐提供review绑定诊断。完整性检查三项complete标志、unknown结果及execute_sql缺SQL；不执行SQL或判断语义。逐review只核验run/obs/config/reference/profile/revision关联及既有source-kind方法/合成引用链字段，不判断check适用性、审阅覆盖、真实性或角色结论。无review也不宣称必要审阅完成；VALID/CONSISTENT不代表实测、授权或target接受。异常仅输出稳定诊断码，不回显载荷/引用/异常。

必要测试：签名与固定expected、确定性/输入不变、schema/资源限额/重复key/ID/hash/来源字段拒绝、缺失或不完整观测、缺/过期/方法不合提供review、伪来源/目标引用始终UNVERIFIED、baseline报告不可互用、阻断文件/秘密/引用/网络/应用导入/replay/judge及跨平台内存路径；保留原231项离线回归。新增BDD承接REQ-001/005/006，全部使用具名synthetic或内存虚构条件，不生成actual观测包。

文档矩阵：Plan/SPEC/requirements/design/tasks/trace/python.contract/behavior.feature/RUNBOOK更新本项与延期边界，fixture README/CHANGELOG与现有索引同步；CLI契约及main、ADR、GUIDE、STANDARD、Issue状态、其他target原scope不变。新增来源检查验收、BDD新运行证据与原bytes绑定。完成标准为API与契约一致、必要离线测试及相关门禁新证据通过、Agent独立合成核验、范围无漂移、历史快照可恢复；软件通过不关闭整个T-007。

后续依赖：目前无获批脱敏观测包。未来真实包须绑定采样环境/run与采样/脱敏审阅引用、22条完整调用及结果（保留首次SQL与所有失败，无业务行数据）、真实loader body/active roster顺序/最终装配hash、全部语义与5红线+3非红线独立审阅；不能把旧34条synthetic review改名为actual审阅。actual文件入口与target接受待具体材料和另批方案，Linux/macOS待等价原生保护证明，缺能力继续fail closed。same_target_replay严格窗口/0.03阈值保持，#161跨版本A/B及#504/#583–#586原scope/状态保留。

T-007b最终软件结果：278项PASS（原64 core+44新inspection unit+156 CLI unit+14 BDD），28条第三方警告保留；首轮275为补充平台模型前的真实历史结果。5个独立进程核验normal/baseline/permuted输出hash一致、missing列缺口、fictional来源仍UNVERIFIED；禁止访问哨兵零触发。全仓ruff、全src Windows/Linux类型模型、G1/G2/G3/G19/G21/G22/G9和默认V1已完成新证据；V1 13P/14W/0F保留信息WARN，类型模型不代表原生入口成功。当前证据见[来源检查验收](../capabilities/data-agent/evaluation/evidence/reports/2026-10-12_source_inspection_acceptance.md)。状态VERIFIED_OFFLINE_SOFTWARE供Owner接受；candidate UNCOMMITTED，actual与平台仍延期，原状态保持。
