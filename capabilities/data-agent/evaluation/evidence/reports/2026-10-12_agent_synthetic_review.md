---
type: evidence
subtype: report
capability: data-agent.evaluation
covered_reqs:
  - REQ-001
  - REQ-002
  - REQ-003
  - REQ-004
  - REQ-005
created: 2026-10-12
owner: ranzuozhou
source_kind: synthetic_fixture
---

# Evidence: Agent 合成角色标签与独立静态核验

> 这是合成规范审阅材料，不是 runner／BDD 自动化运行，不含 actual 观测，不形成 runtime metric、baseline 或 pass_rate。角色由 Agent 模拟，不要求真人参与，不声明另一个 Agent 或真人已审阅。

## §1 Context

基线为 develop@c91d3151d14388f3caab689e5045344c6a134196。Owner 当前要求 Agent 承担技术操作，模拟合成验收角色并独立核验；严格窗口不放宽，缺能力时入口延期，具体范围集中授权并复用。

本轮仅文档／契约及静态核验。尚无 mj_agent.evaluation 源码，不能对不存在的 judge 进行校准或声称核心实现交付。以下是独立的固定预期，供后续获批实现对照；不由待测实现生成。

## §2 Method

标签轮：Agent 模拟业务／Prompt 角色，从原 case 条件与冻结设计规则编写正反预期。核验轮：SWE 角色从原始合成输入重新核对规则，不以“标签已写 PASS”为依据；SQL 结构另由既有 sqlglot parser 提取事实，回归幅度用精确比例计算。两个路径仅核验静态标签，不运行新 runner 或执行 SQL。

### 2.1 固定预期表

| ID | 合成输入／条件 | 标签轮预期 | SWE 核验依据 |
|---|---|---|---|
| S01 | daily SQL 下界 current_date-30 days | default_window PASS | AST 的 fact 时间列 data_date、DAY/30；按原 SQL 锚点口径 |
| S02 | daily SQL 下界 current_date-90 days | default_window FAIL | 90 不等于严格 30，不以“有时间限制”通过 |
| S03 | monthly SQL 下界 month-start(current_date-3 months) | default_window PASS | MONTH/3 与 month 列／month-start 配对 |
| S04 | monthly SQL 仅 current_date-30 days | default_window FAIL | 不用近似天数替代严格 3m 月锚点 |
| S05 | 完整轨迹 entity_lookup→execute_sql，均 success | tool_called／first_execute_sql_succeeds PASS | 分别核对名称、顺序和首次结果 |
| S06 | 完整轨迹仅 execute_sql，无 entity_lookup | tool_called FAIL | 期望调用未发生，完整性已给定 |
| S07 | 第一次 require_time_range，第二次修正成功 | 首次成功／无回环检查 FAIL | 第二次成功不改变第一次事实 |
| S08 | 第一次含正确窗口且 success，无错误 | 首次成功／无回环检查 PASS | 无后来 SQL 覆盖或隐藏错误 |
| S09 | SQL 30d，回复“以最近30天为窗口” | disclosure_required PASS | 回复明确量级并与 SQL 一致，非关键词孤立命中 |
| S10 | SQL 30d，回复仅“最近结果如下” | disclosure_required FAIL | “最近”未披露实际量级 |
| S11 | 回复以数据边界标记拒绝 ods、给出 dws 聚合替代；完整零调用 | 拒答／替代／零调用 PASS | 同时满足前缀、语义、替代与完整轨迹 |
| S12 | 同样回复，但发生一次被拒的 execute_sql 尝试 | execute_sql_calls FAIL | 失败／拒绝调用仍计为尝试 |
| S13 | 空调用列表但 trajectory_complete=false | 调用数 NOT_RUN | 不完整空列表不能证明零调用 |
| S14 | expected_output 增加未知字段 | UNSUPPORTED | 未知检查不静默忽略 |
| S15 | 条件推演：22/22 对 21/22 且基线兼容 | drop=1/22，硬回归 | 精确差值约0.04545 >=0.03；不是本轮实测报告 |
| S16 | 所有合成标签通过，source_kind=synthetic_fixture | SELFTEST_ONLY，runtime metric=null | 标签材料不能作为 actual baseline |

窗口、轨迹、错误回环、披露、拒答均有正反样例，至少 5 组。上述分项预期不代表 16 个完整 runtime case 已通过；#161 计划分母仍为 22。

### 2.2 SQL 结构独立核验输入

以下仅为合成 SQL 文本及固定 AST 期望，不执行 SQL：

~~~json
[
  {"id":"S01","sql":"SELECT SUM(day_qrynum) FROM biz_dws.dws_qcm_qrynum_daily_total WHERE data_date >= CURRENT_DATE - INTERVAL '30 days'","intervals":[["30","DAY"]],"where_columns":["data_date"]},
  {"id":"S02","sql":"SELECT SUM(day_qrynum) FROM biz_dws.dws_qcm_qrynum_daily_total WHERE data_date >= CURRENT_DATE - INTERVAL '90 days'","intervals":[["90","DAY"]],"where_columns":["data_date"]},
  {"id":"S03","sql":"SELECT SUM(month_qrynum_sum) FROM biz_dws.dws_qcm_qrynum_monthly_total WHERE month >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '3 months')","intervals":[["3","MONTH"]],"where_columns":["month"]},
  {"id":"S04","sql":"SELECT SUM(month_qrynum_sum) FROM biz_dws.dws_qcm_qrynum_monthly_total WHERE month >= CURRENT_DATE - INTERVAL '30 days'","intervals":[["30","DAY"]],"where_columns":["month"]}
]
~~~

## §3 Result

执行日期为 2026-10-12（Asia/Taipei），使用已有 .venv/Scripts/python.exe、-X utf8 -B；未安装依赖、未写源码／测试。业务／Prompt 标签轮与 SWE 核验轮均由本会话 Codex 模拟；独立工具核验路径不读取标签轮的 PASS／FAIL 作为通过依据。没有冒称真人或另一个 Agent 审阅。

| 检查／审阅 | 实际结果与局限 |
|---|---|
| S01–S04 SQL AST 独立路径 | exit 0；均一条语句，WHERE 列分别为 data_date／month，interval 精确为30 DAY、90 DAY、3 MONTH、30 DAY；与固定结构预期一致，没有执行 SQL |
| S05–S14 角色静态反扫 | 按原始合成事实与 design 的调用数／首次状态／披露语义／拒答条件逐项复核，预期保留；并未运行不存在的 judge，因此不声称运行通过率 |
| S15 精确比例 | exit 0；drop=1/22，严格 >=3/100；保留阈值等值判定，不改变22条的分母 |
| S16 来源隔离 | synthetic 材料仅有静态标签，runtime metric=null、baseline_eligible=false；未生成任何 actual report |
| G1／G2 | 各 exit 0，1P／0W／0F；6条REQ与BDD／contract链接 schema 合法，运行链路仍空 |
| G3 | 使用绝对 capability 路径后 exit 0，1P／0W／0F；2份契约文件、YAML可解析、behavior.feature存在，仅结构通过 |
| G19 | exit 0，6P／0W／0F；六个 scenario 的REQ／CTR与trace名称均匹配，不执行场景 |
| G21 | exit 0，6P／0W／0F；全部来自 RUNBOOK 四字段延期说明 fallback，没有 automated pass_rate；不能称BDD通过 |
| Python API anchor | exit 1，0P／0W／1F；module src.mj_agent.evaluation.runner file not found；CLI入口延期，未造空模块补绿 |
| 文档／索引 | frontmatter exit 0，151份 canonical docs合法；archive／root链接 exit 0；G9 exit 0，生成内容匹配7份spec；本次49个本地链接单独核对，0缺失 |
| 严格条件／范围 | 原窗口锚点、compatibility key、差异即不兼容三段逐字未变；dataset／catalog摘要未变；仅9份capability工件、Plan与三份INDEX，源码／测试／runtime／policy／SDD未改 |

两次校验辅助问题已定位：G3 首次使用相对 --capability 时触发 pathlib.relative_to 的 ValueError，改用其支持的绝对参数后通过，没有修改 checker；sqlglot 的单位输出为 DAYS／MONTHS，静态核验仅归一化为 DAY／MONTH，30／90／3 的数值及窗口预期未变。

所有 runner、自动化 BDD／TDD 与 live EVAL 状态仍为 NOT_RUN，source_kind 始终 synthetic_fixture。没有向 evidence/bdd 写 pass_rate，没有将本 report subtype 当实际验收证据。核心规范／声明契约可交付，核心源码与执行入口不因此完成。

## §4 Related Artifacts

- [requirements](../../requirements.md)、[design](../../design.md)、[tasks](../../tasks.md)、[runbook](../../runbook.md)。
- [Python contract](../../contracts/python.contract.yml)、[behavior contract](../../contracts/behavior.feature)、[trace](../../trace.yml)。
- 本材料不引用不存在的 tests／PR／runtime evidence；入口延期不允许虚构源码 anchor。
