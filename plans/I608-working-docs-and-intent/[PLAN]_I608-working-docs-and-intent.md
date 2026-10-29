---
type: plan
summary: "落实任务工作目录、INTENT 原意机制与安全兼容校验（Issue #608）"
owner: ranzuozhou
created: 2026-10-29
updated: 2026-10-29
state: active
track: engineering-workflow
---

# Plan — I608-working-docs-and-intent

## 1. 目标、使用者与原意来源

为任务执行者、文档维护者和独立验收者交付一致可用的规则、模板、原生技能及离线校验。
原意唯一正本为 [Issue #608](https://github.com/MJ-AgentLab/mj-agent/issues/608) 的 Scope、
Acceptance Criteria 与 Owner 最终方案；本任务是简单单任务机制交付，不另造正式 INTENT。
Owner 在创建本执行会话的交接中明确采纳最终 A–F 方案及四项 grilling 决定，并授权实施。
方案采纳、执行授权与未来成品接受分别记录；当前没有 Owner 对未来成品的接受。

### 1.1 完整接受基线快照

下列为 2026-10-29 从 Issue 正本读取的完整 16 项 AC；本 Plan 在提交后以固定提交位置保存可恢复快照。
本 Plan 承担全部 AC。主要 Issue 为真实 #608，主要 PR 尚未创建，故 topic 省略 P；后续整体主 PR
明确时按受控改名补齐，task_id 与固定提交证据不随路径自动变化。没有新增跨任务 INTENT/REQ 系统。

- [ ] AC-1：任务目录名与主 `[PLAN]_<topic>.md` 的 topic 完全一致；支持 `I<issue>-P<pr>-<slug>`、仅 I、仅 P、无编号四种格式。slug 为小写英文/数字/短横线；编号只来自本仓本任务的真实主要关联，各最多一个。（命名 checker 正负例）
- [ ] AC-2：主题稳定；主要关联首次明确、编号纠错或明确更换时可受控同步改目录/主文件并修复活动引用；不自动追随后续子/补丁/收尾 PR；不改变 task_id、历史基线或 INTENT ID。（改名/引用/路由回归）
- [ ] AC-3：working 统一进入所属任务目录；共享材料唯一主归属；Intake 可先保存；独立 working 任务可以始终没有主 Plan。仅已形成 Plan 的目录要求一个主 Plan。报告可按用途命名。（目录和工作流场景）
- [ ] AC-4：多 PR 时主要 PR 优先代表整体交付的集成 PR，没有明确主要 PR 就省略 P 段，不猜第一条或最新 PR。（技能/模板和场景核验）
- [ ] AC-5：working 必填 type/summary/owner/created/updated/state/track 七字段；新 Plan 默认 draft，有明确采纳依据后 active；不增固定人工停点。（schema/模板回归）
- [ ] AC-6：仅主 Plan completed 必须 AC 满足、成果可用及 Owner 明确接受准确版本；其他 working 按自身交付条件由 Agent 标 completed。报告 completed 仅为交付完成，独立任务整体接受仍由 Owner 在已有记录表达。（状态正负例和独立验收）
- [ ] AC-7：取消 working 物理归档、180 天 GC、候选检测与相关 CI 调用；废弃 draft 保持 draft；archived 仅历史兼容，不改变其他 canonical 归档机制。（规则反扫/CI/回归）
- [ ] AC-8：正式 INTENT 位于 `docs/intent/[INTENT]_INT-YYYY-NNN_<English_Topic>.md`，采用上游八项 type/domain/summary/owner/created/updated/state/intent-id 加 track，version 可选。（专属校验及模板）
- [ ] AC-9：INTENT 五正文、真实来源和责任、原意核对/内容接受/授权/交付接受分记；简单任务可用 Issue 原意区作唯一正本；来源或维护责任不明只存 working 草稿。（author/intake 场景）
- [ ] AC-10：正式 INTENT 只允许 draft/active/deprecated；ID 跨年/修订不换、删除撤销不释放；创建和合并前含 deprecated 查重；共享冲突及 999 耗尽由 Owner 决定；Plan/Issue 完成不传播 INTENT 状态。（ID/状态/集合读取失败负例）
- [ ] AC-11：固定提交或完整可恢复快照绑定接受基线；旧接受不自动覆盖新内容；活动链接修复与历史证据保持分开。（基线/迁移场景）
- [ ] AC-12：真实业务原意使用中性选项，工程/机制/授权问题提供推荐；不以 AI 建议、预选、沉默或超时代替决定。（技能内容及模拟使用场景）
- [ ] AC-13：Plan 含目标范围、接受基线/授权、依赖、风险、逐 AC 验证、产物/检查点和独立使用七题；doc-plan 保持缺口评估职责。（模板/技能一致性审查）
- [ ] AC-14：嵌套路由、目录归属、深层相对链接、新旧布局均有可复现正负例；保留重复路由、路径重解析点及非法输入拒绝，沿用 task_id/head/base 实际约束。（离线单测/CLI）
- [ ] AC-15：政策、模板、技能、导航和实际 checker 同步；相关 lint/type、离线 unit、文档和 native 检查通过或准确列未测。（适用命令矩阵）
- [ ] AC-16：未参与实现的独立上下文模拟使用者/运维/审查者，核真实成品行为，证据绑定 commit SHA、环境、时点；同一对象最多两轮，Owner 最终接受另记。（独立合成验收包）

### 1.2 已定解释与约束

- 目录可始终只有 Intake 或 Report；仅形成主 Plan 的目录要求目录 topic 与唯一主 Plan 完全一致。
- 多 PR 的主要 PR 优先整体集成；不明确则省略 P，不猜分支数字或第一/最新 PR。
- 仅主 Plan 的 completed 要求 AC 满足、成果可用与 Owner 明确接受准确版本。其他 working 按自身交付条件。
- Report completed 只表文档交付；整体任务接受仍在已有 Issue/会话表达，不补造主 Plan 或接受系统。
- 新任务使用嵌套目录；旧根布局兼容。无历史批量迁移、资料删除或冻结证据改写。
- 正式 INTENT 独立 canonical，五正文、九字段、三状态、固定 ID；Issue 进度、Plan 实施、SPEC 行为与 Report 结论各自归属。
- 结构检查不能证明原意忠实、真实编号来源或 Owner 决定。接受绑定固定提交文件或完整可恢复快照；新内容不继承旧接受。

## 2. 范围、排除与延期

范围：policies / lifecycle / execution-loop 权威正文；新 ADR；模板、开发技能、导航与交付指南；
working/INTENT/frontmatter/相对链接检查；受限嵌套路由发现；GC 退出活动链；离线回归与独立验收。
排除：业务 SQL、runtime prompt/skills、catalog、DB、Docker/生产、秘密、权限配置、历史批量迁移、
强推/改历史和删除。canonical 既有归档不变；retired fidelity/golden 不复活。
非核心：宿主实际信任/受控后台能力不在本任务变更范围；发布按真实可用身份执行，缺能力登记真实阻塞。

## 3. 执行授权与停止条件

动作：本 worktree 的文档/脚本/测试实施、离线核验、明确集合 stage/commit、普通 push 与单主 PR
（base=develop）。Owner 已在 Issue 与交接集中授权，不按普通版本迭代重新审批。
对象/环境：MJ-AgentLab/mj-agent，maintain/608-working-docs-and-intent，本机 Windows worktree；
初始 HEAD e195bfeb75bef9526b9df2c0d06db01388ca8725。权限保持既有，使用正常宿主与发布身份。
副作用/资源：本地文件/索引/提交，授权分支普通远端推送和主 PR；不连接业务库或外部测试依赖。
停止：目标/范围/环境/权限/不可逆风险实质新增，或真实技术拒绝只暂停受影响动作并保留原错；
禁止绕权限、借用既有秘密或改配置。merge 等待 Owner 对实际成品的明确接受与有效平台审核。

## 4. 依赖、任务与文档决策

事实扫描：task_delivery.py 当前只读 plans 根；frontmatter 已递归但无专属 INTENT/working 规则；
wikilinks 未覆盖深层 Markdown 相对链接；lifecycle/archive/post-merge 仍有 working GC；
技能存在 track/active/completed/分支猜号/working 排除冲突。均在本次修复。

| 任务 | 依赖 | 产物与方法 | 负责人 |
|---|---|---|---|
| 目录、INTENT、链接与 GC 校验 | 既有 checker / tests 约束 | 先失败测试再实现；CLI/负例 | validators Agent |
| 政策、模板、ADR 与导航 | Issue 已定机制 | 真实来源、版本纪律、反扫 | governance_docs Agent |
| 技能与共享执行说明 | 权威规则与模板 | 按实际分支同步，不刷新冻结 infra | skills Agent |
| 嵌套路由与安全回归 | 现有 guard 消费接口 | 有限两层扫描、重解析点/大小/重复拒绝 | 主 Agent |
| 集成、检查、恢复点与主 PR | 上述产物 | 离线矩阵、独立验收、普通提交推送 | 主 Agent |
| 独立合成验收 | 实际候选提交 | 未参与实现的上下文从 AC 验成品，最多两轮 | 待委派 |

Documentation Decision 按实际类型：Plan Create；INTENT 正式文件 None（Issue 原意区已足够）；
ADR Create；政策/lifecycle/workflow Update；Plan/SPEC/Assessment/Repo Scan 模板 Update；
INTENT/Intake/Report 模板 Create；开发技能/共享引用/导航/GUIDE Update；
SPEC 正式文件 None（既有接口不新增公共行为契约）；Report 候选验收证据 Create；
RUNBOOK/业务 STANDARD/runtime EVAL/CHANGELOG None（本维护任务无该类新需求）。
不固定十类、不给未涉及类型补造工件。共享报告唯一主归属在本目录，子 Plan 如有须各自目录。

## 5. 风险、恢复与监控

| 风险 | 缓解/恢复/观察点 |
|---|---|
| 新布局遗漏路由或放宽安全读取 | 仅根+一层任务目录，逐层拒 symlink/reparse，保大小/重复/异常输入与真实head/base约束 |
| 新专属 schema 误伤历史 | 旧根兼容，新增嵌套布局正负例；不自动迁移 |
| 活动引用修复改写接受历史 | 新活动链接更新，固定提交/快照仍可恢复；改名核源/目标/Git状态/引用/路由并登记 |
| 文档声称机器已认证真实决定 | 语义独立审阅，未验证列 UNKNOWN；结构 PASS 与接受分记 |
| 发布身份不可用或技术拒绝 | 保留原错、记录 BLOCKED_EXECUTION_ROUTE；本地产物与离线验证继续 |
| 多面规则不一致 | 同批反扫政策/模板/技能/CLI，独立使用者/运维/审查者验收 |

恢复点为授权普通 commit；修复用新增提交，不 reset/rebase/force push。定期核 origin/develop 差异，
授权内 merge develop（不制造无差异提交）。新权限/删除另行 Owner 决定。

## 6. 验证、版本与独立使用七题

复用已锁定环境 D:/workspace/10-software-project/projects/mj-agent/develop/.venv，
在本 worktree 显式运行；uv --frozen --no-sync，不机械 sync。新增测试进入明确 stage 集合后
通过 scripts/sdd/run_offline_pytest.py；外部依赖恒 SKIP_POLICY_EXTERNAL_DEPENDENCY。
适用：ruff、mypy src/mj_agent、offline tests/unit、frontmatter、wikilinks、
check_working_docs、check_codex_native、check_native_skills。每条记录命令、exit、候选 SHA、
环境/时点与逐 AC 结果，失败/未测不计 PASS。无需 DB、容器或 live probe。

1. 问题范围：见 §1–2，交付可运行治理机制而非停在建议。
2. 权威预期与冲突：Issue/Owner 决定掌原意与接受；政策掌规则；真实代码掌实现行为；旧冻结证据保留。
3. 文件入口/顺序：AGENTS → 共享边界 → Issue/本 Plan → 目标规则/局部 AGENTS → 对应源码/模板/技能。
4. 工具身份/输入：真实 worktree/ref/SHA；主要 Issue608；PR 未知先省 P；测试只消费已跟踪明确集合。
5. 授权/停止：见 §3，技术拒绝不改写绕过。
6. 方法/版本/环境/批次：行为红绿测试；文档反扫；最终候选 commit 独立最多两轮，机器结构与语义分记。
7. 候选完成/正式生效：本地验证及独立验收产生候选交付；主 PR 必要门禁/平台审核与 Owner 接受另记。

## 7. 检查点、产物与未知

2026-10-29 启动：实际路径/分支正确、工作区干净，Issue16AC已读，Serena正常激活目标worktree。
本 Plan 初建 draft；事实/任务依赖已核定，依据 Owner 对最终 A–F方案的明确采纳与本会话执行授权转 active，不增固定人工停点。
首批路由回归观察 RED：15 failed / 3 passed；实现后与既有交付边界合跑 GREEN：30 passed，ruff适用文件通过。
方法为受控 offline runner 红绿；嵌套四命名、受控补号保 task_id、旧布局/无Plan目录、重复块/JSON/路由、逐层重解析点与大小限制均覆盖。
核心恢复点：7c891f28bb815d8053d2b4e6f8bab268b6dcaba8（路由与完整AC基线，文件即本Plan当时路径）、eb9980e31e5e96fee1ca5cca96c31453d93faf08（校验器/GC/CI）、b68be18a27f97b02e446aee544983eb138943e10（政策/模板/导航）。上述为可恢复完整文件位置，非以hash或摘要替代基线。
完整本地矩阵：ruff PASS；mypy 57源文件 PASS；受控 offline unit 1936 passed、2 skipped、30 subtests passed（203.81s）。SKIP分别为Windows无权创建真实symlink和非Windows平台专属event-loop用例；不计通过。
文档：frontmatter161件、working目录/深链接、strict wikilinks、loop章节引用及native schema/resources均PASS；native只STATIC_PASS，host NOT_TESTED/rule_loading UNKNOWN，不冒充加载。
校验器 focused 136 passed/1 symlink SKIP；mock reparse负例另有覆盖，不当真实symlink创建证据。三个实施Agent已返回实际贡献；独立验收上下文已从Issue16AC建立预期，等待最终候选提交。
发布前事实：已核同一App5284037/installation170545174/repository1172583390，daily仅metadata read、contents/pull_requests write，短期token撤销CONFIRMED。CI成品变更需要Workflows write，当前尚无本任务权限扩大决定；受影响发布步骤待具名决定，不擅扩权或借身份。Gitee无本任务具名可用执行身份，为非核心镜像NOT_EXECUTED/DEFERRED，恢复须具名合法身份及动作范围，不以该缺能力阻塞本地核心。
Owner新增指令：真实未决取舍使用Matt Pocock grilling，选项标推荐；提问保持待答，沉默/超时/预选不作决定；已定方案不重问。
当前未知：最终主 PR编号、最终候选提交、独立验收结果、CI、Owner成品接受。
后续填写验证证据与改名记录，主 Plan 在未获 Owner 明确准确版本接受前保持 active。

## 8. 接受记录

原意核对/方案采纳：Owner 最终 A–F 与四项 grilling，由本执行会话交接及 Issue608保存。
执行授权：本执行会话明确指令与 Issue608 Verification Plan。
独立技术验收：待实际候选提交。
交付/Owner接受：尚未发生。机器PASS、PR合并或文档完成不代替该决定。

