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

当前范围：Owner已明确授权离线核心编码，实施与验收见§8.3；上列仅为原Plan落盘轮次授权。CLI／actual、runtime修改及Git发布未授权。

## 2. 背景与 Repo Scan 事实

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
| AC-1 | 22条结果、缺观测、未知检查、非法输入反例 | 8a | 核心PASS；CLI文件入口延期 |
| AC-2 | AST／轨迹／错误回环及绑定角色正反例 | 8b、8c | 合成核心PASS；实际观测校准未执行 |
| AC-3 | fixture隔离、零值、placeholder、完整分母 | 8a、8c、8d | 核心PASS；无runtime基线 |
| AC-4 | manifest绑定与兼容键差异反例 | 8a、8d | 核心PASS；实际来源真实性未核验 |
| AC-5 | 精确阈值、红线、无基线、21/22下降 | 8d | 核心PASS；不扩展其他EVAL阈值 |
| AC-6 | 规范化回放一致与报告分类 | 8d | 核心PASS；CLI进程退出／文件输出延期 |
| AC-7 | 核心无IO／应用导入／网络哨兵、受控pytest、ruff/mypy | 8e | 核心PASS；CLI路径／重解析点／碰撞检查延期 |
| AC-8 | 文档、索引、trace、报告与范围核查 | 8e | 核心交付记录完成；main契约锚点仍缺，完整capability未验收 |

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
