---
type: guide
domain: SYS
summary: mj-agent 试用分析师 day-1 上手指南—— 30 分钟内拿到内网 Chainlit URL、跑通月报场景闭环、知道何时该写 ISSUE 反馈
tags:
  - guide
  - onboarding
  - analyst
  - phase1
aliases:
  - mj-agent Analyst Day-One
  - 分析师试用上手指南
created: 2026-05-07
updated: 2026-05-07
state: draft
version: v0.1
track: code
derives_from: ""
owner: 项目负责人
---

# mj-agent 分析师 Day-One 上手指南

> **适用范围**：mj-agent Phase 1 试用闭环（sub 1.I）阶段，3-5 名内网分析师 day-1 上手 30 分钟内跑通"问问题 → 拿数据 → 给反馈"全链路
> **目标受众**：业务/数据分析师（非开发；不需要看代码）
> **版本**：v0.1
> **最后更新**：2026-05-07
> **派生自**：mj-agent 原生
> **关联文档**：[[runbook/dev_deployment|DEV Deployment Runbook]]、`[TEMPLATE]_Trial_Issue.md`（vault）、[[../mj-agent-roadmap-v1.6|路线图 v1.6]]

---

## TL;DR

- **阅读时间**：~10 分钟
- **涵盖范围**：Chainlit 入口怎么打开、5 个高频问法模板、3 类常见错误怎么读、何时写 ISSUE 反馈
- **适用场景**：刚拿到 mj-agent 试用邀请的分析师；day-1 用之前从头到尾扫一遍

## Prerequisites

- **目标读者**：业务/数据分析师；理解 QCM (Query Counter Metric) 业务概念；能在 Lark/Slack 写工单
- **必备知识**：
  - 公司内网 VPN 连通
  - 大致知道想分析的指标族（qrynum / tntcnt）+ 周期（日/周/月/季/年）
- **建议了解**：
  - SQL 基础（不强制，agent 会代写；但能读懂结果集字段名更顺）
  - mj-system QCM 维度命名（_total / _by_industry / _by_tenant 等；agent 会自动选）

---

## 目录

- §1 第一次访问 mj-agent
- §2 5 个高频问法（直接抄）
- §3 怎么读 agent 的回复
- §4 3 类常见错误 + 自救
- §5 何时写 ISSUE / 怎么写
- §6 试用 ≥ 2 周内你的"角色"

---

## §1 第一次访问 mj-agent

1. 打开浏览器，进 `http://<DEV-host-ip>:8001`
   - 具体 IP 由项目负责人在试用启动邮件 / 群通知里给
   - 如果打不开 → §4 错误 1
2. 看到 Chainlit "Welcome to mj-agent" 页面 + 下方输入框
3. 输入第一个测试问题：

   ```
   biz 域有哪些表？
   ```

4. 等 5-15 秒，agent 会列出 65+ 张 `biz_dws.dws_qcm_*` 表 + 2 张 dwd dim 表 + 3 张 signal 表
5. 这条问答的目的是确认链路通：UI ↔ LLM ↔ biz DB 全栈正常

> **如果 §1 第 4 步没拿到表列表** → 写 ISSUE，标 P0；项目负责人会在 24h 内排查（多半是 DEV DB 没起 healthy）。

## §2 5 个高频问法（直接抄）

| # | 场景 | 抄这句 |
|---|---|---|
| 1 | 单日查询量 | "近 7 天每天的 qrynum 是多少？" |
| 2 | 日环比异常 | "上周哪一天的 qrynum 环比掉得最多？" |
| 3 | 月度同比 | "2026 年 4 月 vs 2025 年 4 月，月查询量差了多少？" |
| 4 | top tenant | "上月查询量最高的 5 家租户是谁？分别多少？" |
| 5 | 月报 | "帮我出 2026 年 4 月的月报" |

> **场景 5 要走 monthly-report skill**——agent 会输出 Markdown 模板 + Excel 附件 + 趋势图 PNG。如果只回了文字没附件，写 ISSUE 标 P1 → 触发 monthly-report skill 漂移调试。

## §3 怎么读 agent 的回复

agent 的每条结论都包 4 段（envelope，参见 ADR-008）：

| 段 | 在哪里看 | 你要看什么 |
|---|---|---|
| 业务结论 | 文字段开头 | 一句话回答你的问题（这是给"老板"看的） |
| 执行的 SQL | 折叠的 ```sql 块 | 怀疑结果不对时打开核对（"它是不是查错周期了？"） |
| 字段说明 | 文字段中部 | qrynum vs prev_day_qrynum vs dod_qrynum_diff 这三种语义不要混 |
| 数据边界提示 | 文字段尾部 | 看到 `truncated=true` 说明结果被截断到 500 行；要全量请加 LIMIT 或换 aggregate |

> **看到 `[数据边界]` 段时务必读完**——agent 拒绝跑某些查询是设计行为（4 层防护），不是 bug：
> - "需要时间窗" → 加"近 7 天 / 近 1 个月"
> - "禁止 SELECT *" → 让 agent 列具体列
> - "biz_ods 不可见" → 你看到的 ods 表不在分析师权限内，问 dws 同名替代

## §4 3 类常见错误 + 自救

### 错误 1：Chainlit 打不开 / 502

**自救**：换浏览器试一次；如果还不行 → 写 ISSUE P0 + 附 `<DEV-host-ip>:8001` 截图。**不要**自己重启容器（你没权限；项目负责人会处理）。

### 错误 2：agent 一直转圈 > 60s

**自救**：刷新页面重问一次，问题精简（去掉 "你帮我..." 之类语气词）。还转圈 → 写 ISSUE P1 + 附原问题 + LangSmith trace ID（在 agent 回复底部）。

### 错误 3：返回结果"看起来不对"

**自救路径**（不要直接 ISSUE）：

1. 打开折叠的 SQL 块——核 `WHERE` 时间谓词、表名、维度
2. 比对你心里的"正确 SQL"差在哪
3. 如果是周期错（你要月级，agent 给了日级）→ 重问时显式说"按月"
4. 如果是维度错（你要按行业，agent 给了按租户）→ 重问时显式说"按行业 (industry_code)"
5. 重问 2 次仍不对 → 写 ISSUE P1 + 附原问题 + 错 SQL + 你期望的 SQL

> **agent 不会 100% 对**——它的目标是让你少写 SQL，不是替代 SQL 思维。把它当"会查表的实习生"。

## §5 何时写 ISSUE / 怎么写

ISSUE 是试用阶段最重要的反馈通道。模板在 vault `[TEMPLATE]_Trial_Issue.md`，复制到群发的 ISSUE 表单（Lark 多维表 / 或共享 Markdown 文档）。

P 级判定：

| P 级 | 标准 | 24h 处置 |
|---|---|---|
| **P0** | 服务不可用：UI 打不开 / 任何问题都 timeout / 返回数据明显被改写 | 项目负责人当天 hotfix |
| **P1** | 单类场景挂：某 skill 反复给错、某 5+ 提问类无法满足、特定客户名永解析不出 | 计入下周 sprint，本周 milestone 末批量处理 |
| **P2** | 体感问题：响应慢但 < 30s / UI 小 bug / 文案晦涩 / 想要某 nice-to-have | 累积；试用结束统一对账，决定是否进 Phase 2 |

写 ISSUE 必填 5 项：

1. **复现命令**：你给 agent 的原文（一字不漏）
2. **期望**：你心里的正确答案/结果
3. **实际**：agent 给的回复（截图 + 折叠 SQL）
4. **trace ID**：agent 回复底部的 langsmith URL 后缀（用于回放）
5. **频率**：第几次出现 / 是否可稳定复现

## §6 试用 ≥ 2 周内你的"角色"

- **不是测试员**——你的任务是用真实业务问题撞 mj-agent，看哪些撞不动
- **不要自降难度**——比如把"我们行业本月查询量同比 vs 上月"改成更"agent friendly"的"qrynum 月环比"。前者才是真用例
- **写 ISSUE 比当面吐槽更值钱**——文字记录可被项目负责人用 LangSmith trace 反向回放；当面说会丢信息
- **2 周末参与对账**——项目负责人会拉你 review Phase 1 退出标准 [[../[CHECKLIST]_Phase_1_Exit|Checklist]]，特别是 E1（5 skill 可用）/ E4（月报场景）/ E8（实体解析命中率）三项与你最相关

## 关联文档

- [[runbook/dev_deployment|DEV Deployment Runbook]]：你拿到的内网 URL 来自哪
- vault [[../[TEMPLATE]_Trial_Issue|Trial Issue 模板]]：怎么写 ISSUE
- vault [[../[CHECKLIST]_Phase_1_Exit|Phase 1 Exit Checklist]]：试用末对账表
- [[mj-agent-roadmap-v1.6|路线图 v1.6]]：本试用所属 Phase 1 在整个项目的位置

## 更新记录

| 日期 | 版本 | 变更 |
| --- | --- | --- |
| 2026-05-07 | v0.1 | 初稿；sub 1.I 试用阶段分析师 day-1 入口 |
