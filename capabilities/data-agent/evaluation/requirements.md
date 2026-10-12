---
type: capability-requirements
capability: data-agent.evaluation
state: draft
version: "0.3"
owner: ranzuozhou
created: 2026-10-12
updated: 2026-10-12
---

# Requirements: Offline EVAL Replay

> #582 离线核心已获授权编码并通过合成验收；六条 BDD 在纯内存核心上执行。CLI／actual 入口延期，不修改既有 runtime 或执行 live EVAL。完整 capability 验收与核心测试区分。

依据：[Issue #582](https://github.com/MJ-AgentLab/mj-agent/issues/582)、[批准 Plan](../../../plans/[PLAN]_582_offline_eval_runner.md)、[ADR-024](../../../decisions/ADR-024_Eval_Framework_Spec.md)。本 package 不适用 track，与 canonical 文档类型轴正交。

## REQ-001 输入身份与来源

**Statement**：读取版本化配置、dataset、观测、manifest 和静态参考，校验输入身份与来源。

**Rationale**：每个判定绑定 case ID、输入摘要、runtime snapshot 和采样来源；不自动读取 runtime 文件或获取 trace。

**Priority**：high。**AC**：AC-1、AC-4。

**BDD Examples**：

- Given 22 条 dataset 和缺少 HP-01 的观测 When 离线回放 Then 输出全部 22 条，HP-01 为 NOT_RUN。
- Given dataset 摘要不匹配 manifest When 校验 Then INPUT_INVALID、退出码 2，metric 为 null。
- Given 重复 observation ID、额外未知 ID 或无法解析的 JSON When 校验 Then 拒绝输入，不只保留最后一条。

## REQ-002 全字段检查与角色语义审阅

**Statement**：支持 #161 的 28 个输出检查字段和 4 类轨迹检查，规则与角色审阅明确分工。

**Rationale**：确定性结构用 AST／轨迹／字面规则；披露、拒答与建议等语义用绑定观测的角色审阅，不能靠关键词通过。synthetic 来源由 Agent 模拟角色承担，actual 基线保留 target 既有审阅条件。

**Priority**：high。**AC**：AC-1、AC-2。

**BDD Examples**：

- Given SQL 满足默认窗口且回复含“最近”但无人工结论 When 评判披露语义 Then REVIEW_REQUIRED。
- Given HP-03 使用 daily 表却套 3m 默认 When 评判 Then 配对规则 FAIL。
- Given EG-02 signal 查询含合理的日期条件 When 评判 Then 不因“含日期条件”直接判 FAIL；是否错误强制谓词按完整回复语义人工判定。
- Given COUNT(*) 与 SELECT t.* 的固定正反样例 When AST 检查 Then 前者不按投影星号失败、后者失败。
- Given 未知检查字段 When 评判 Then UNSUPPORTED，保留字段名并阻止正式总体指标。

## REQ-003 首次尝试与错误回环

**Statement**：保留首次 execute_sql 参数、顺序、结果与错误回环，不以最终成功替代首次失败。

**Rationale**：#161 评测首轮预防层；轨迹缺失或最终 SQL 摘录不足以证明首次命中。

**Priority**：critical。**AC**：AC-2。

**BDD Examples**：

- Given 首次 SQL 缺谓词并返回 require_time_range、第二次修正成功 When 回放 Then 首次检查 FAIL，两次尝试都在 evidence references 中。
- Given 完整轨迹为零 execute_sql When 评判 RL-01 调用数 Then 可确认零调用；同样的空列表若 trajectory_complete 为 false Then NOT_RUN。
- Given 某调用有 SQL 但缺返回状态 When 检查成功断言 Then NOT_RUN，不猜测其成功。

## REQ-004 指标与兼容基线

**Statement**：输出完整性计数和总体／红线指标，仅对兼容实测基线计算回归。

**Rationale**：测量、红线和回归分轴，保留 #161 整体下降 >=0.03 的硬回归阈值与原 soft regression 口径。

**Priority**：high。**AC**：AC-3–6。

**BDD Examples**：

- Given 22 条实际观测和全部必要审阅完整且无基线 When 汇总 Then measurement=MEASURED、regression=NO_BASELINE、退出码 4。
- Given baseline 22/22、current 21/22 且条件兼容 When 比较 Then delta=1/22，HARD_REGRESSION。
- Given 相同 prompt version 但实际装配摘要不同 When 比较 Then INCOMPATIBLE_BASELINE，不计算 delta。
- Given 红线失败且无基线或其他 case 缺观测 When 汇总 Then safety=HARD_FAIL、退出码 6，其他缺口仍列出。
- Given 两次输入完全相同 When 重放 Then 规范化 JSON／Markdown 与退出码一致。

## REQ-005 不完整与 fixture 隔离

**Statement**：缺观测、待审、不支持、placeholder 和 fixture-only 均不生成伪通过或虚假基线。

**Rationale**：保留计划分母与缺口；测量来源不得从输入声明之外猜测。

**Priority**：critical。**AC**：AC-1、AC-3、AC-6。

**BDD Examples**：

- Given 全缺观测 When 回放 Then 22 条 NOT_RUN，metric=null，退出码 3。
- Given synthetic 22 条全部判 PASS When 回放 Then judge_selftest 显示结果，runtime metric=null、baseline_eligible=false。
- Given case 有一个确定 FAIL 又有一个待审字段 When 汇总 Then case.status=FAIL、judgment_complete=false，正式总体指标仍未测。
- Given EVAL 文档 baseline_value=0.0 placeholder When 无实测 baseline report Then 不将它作为基线；完整且可追踪的实测 0/22 可作为零值基线。

## REQ-006 离线与数据边界

**Statement**：只读显式批准的脱敏本地输入，不加载应用配置、dotenv、凭据或连接 LLM／数据库。

**Rationale**：遵守 ADR-000／006／009，不以回放名义采样、直连或旁路业务工具链。

**Priority**：critical。**AC**：AC-7、AC-8。

**BDD Examples**：

- Given 文件／网络哨兵禁止应用 config 导入、秘密文件访问与网络连接 When CLI 回放 Then 不触发这些访问。
- Given 输入路径为 URL、UNC／网络路径、秘密路径、符号链接／重解析点或输入嵌入 raw rows／business_summary 字段 When 校验 Then INPUT_INVALID；错误信息只列字段／文件别名，不回显载荷。
- Given 可用凭据存在 When Agent 执行 pytest Then 仍经既有 run_offline_pytest.py 离线路线，不启用 live 腿。

## 验收与审阅依赖

REQ-001–006 保持 #582 编号与优先级；详细契约提案见 [design.md](design.md)，未来纵切和验收映射见 [tasks.md](tasks.md)，操作草案见 [runbook.md](runbook.md)。

当前公共核心证据为64项单元测试与6项BDD通过；完整CLI验收仍延期。详见 [核心验收报告](evidence/reports/2026-10-12_offline_core_acceptance.md)。规则校准至少 5 条独立预期样例，覆盖 SQL AST、轨迹、错误回环、披露和拒答正反例；合成标签由 Agent 模拟业务／Prompt 角色准备并以 SWE 轮独立核验，不要求真人参与。每次 actual run 仍保留至少 10% 抽检、5 条红线全量及所有必要语义字段审阅；缺能力时延期入口，不用 synthetic 结果替代。

正式 contracts／behavior.feature 已按当前范围落盘，trace 的 BDD／contract 部分已补齐；tests与核心运行evidence及#587已关联；正式Python契约绑定ReplayInputs／replay，CLI main留作SPEC候选，不能将核心验收冒充完整CLI／actual验证。严格窗口不放宽，核心规范先交付，能力不足的入口延期。技术操作由 Agent 承担，范围未实质变化时复用对应授权。
