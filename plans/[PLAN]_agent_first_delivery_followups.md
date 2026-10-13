---
type: plan
summary: 推进 Agent-first 延期待办，先刷新旧能力离线软件证据并增加跨宿主只读完整性核验
owner: ranzuozhou
created: 2026-10-13
updated: 2026-10-13
state: active
track: engineering-workflow
---

# [PLAN] Agent-first 交付后续

## 接受基线

来源为 Owner 本会话「执行待办」及 Q24/Q25/Q26 的实际选择。已接受治理及原 completed Plan 不重开、不改写；本任务从 develop `fd045520c0123627e53d23c0ad58bf97a6b3552e` 继续。#582 的 replay/CLI 兼容及整体接受仍归接手会话。

第一交付单元包含旧六 capability 的离线证据刷新和新增 ZIP 只读 portable verifier。逐步迁移不表示所有旧能力已通过 G21。原 20 个 evidence 文件保持字节不变，已核查 16 个 high/critical 旧场景仍由有效 runbook fallback 记录为 DEFERRED；第七 evaluation 不在本单元迁移范围。

| AC | 可观察接受条件 |
|---|---|
| EVID-001 | 明确选择现有 13 个离线 BDD 身份，真实执行，无失败、错误或跳过；每项从原 requirements/feature 建立软件预期 |
| EVID-002 | 新 suite 绑定实际版本、SUT、测试、基线、输入、hardened runner 与依赖锁，原输出/JUnit/逐 AC 可复现，全部为 SELFTEST_SOFTWARE/software_test |
| EVID-003 | 旧 20 文件内容摘要不变；迁移清单分别列历史、软件 SELFTEST、外部政策 SKIP、未运行及 G21 接口迁移状态，禁止将软件证据提升为 actual、来源认证、Owner 接受或 runtime baseline |
| ZIP-001 | 新只读 verifier 以调用者明确的 repository/head/base/tested SHA/tree、执行种类及 run URL 核原 ZIP 与实际 Git 对象/版本绑定，不依赖验证机 HEAD 等于执行版本 |
| ZIP-002 | 验证原归档摘要、成员安全、suite/依赖/输入/SUT blobs、原 argv 与 resolved_argv、log、JUnit、完整 test identities 和逐 AC；只因存储路径/宿主不同允许完整性验证，任何版本、结果或来源变化必须拒绝 |
| ZIP-003 | 不改写原 archive/原执行布局/原 claims；生成新的验证报告，不能声明执行来源已认证、业务接受或真实 runtime；旧 run/check 与 required checks 原逻辑保持 |
| ZIP-004 | 负例覆盖错 SHA/tree/合并父序、缺对象、改 blob/log/JUnit、缺失/重复 testcase、SKIP/FAIL 冒充 PASS、混合输出根/未声明 argv 改动、路径逃逸/链接/重解析点、重复 ZIP 成员、来源重标及 claims=true |

严格窗口与 #582 的既定阈值、32 类检查不在此单元改动。任何受测 Git 对象缺失、原字节或基线不可得均标缺依赖/未验证，不生成替代对象或放宽门禁。

## 执行授权

Owner 的新执行指令授权本任务普通计划、实现、离线验证、必要文档及局部修复。工作区为 `D:/workspace/10-software-project/projects/mj-agent/maintain/agent-first-evidence-followups`，分支 `maintain/agent-first-evidence-followups`，由正常 worktree add 从已核版本建立。未跟踪内容及其他工作区保持，原治理与 canary 保留。

本地离线准备 READY；已用既有 uv.lock 完成 offline/frozen sync。Git 发布范围、Gitee 执行身份、精确新平台对象、实际运行资源及资源预算在各自具名方案核实后推进；工具存在及旧 Q21 版本批准不能代替新候选的有效仓库审核。不得自动复用已结束的临时 Workflows write，日常 executor 不扩大权限。

Q24 已选 Team + 独立核验 App/可信源：准备 `MJ-AgentLab/mj-agent-delivery-harness` 及私有 `mj-agent-delivery-verifier`，后者仅本仓 Metadata/Contents/PR read、Checks write，无 Administration、Contents/PR write、bypass；新材料拟受控后台不可见托管，候选运行不带发布凭据。实际创建/安装/规则激活前仍须核精确对象和版本。

Q25/Q28 已选既有 local-openai-compat 正常应用配置载体，公开目标仅 localhost/127.0.0.1 或 192.168.0.189，3 个固定无业务数据用例、tools=[]、最多 3 次生成、每次最多 64 输出 token、30 秒、无重试或新增付费；不改 .env、不回退 Ark、不访问 biz 或 storage 写入。具体服务、模型/revision 与候选版本尚未绑定，先完成独立离线负例和预检，缺绑定停止相应运行。

Q26 已选 `mj-agent-delivery-drill-20261013` 本地隔离演练：独立网络/容器/卷/端口、仅测试数据；先核具体资源及副作用，不复用现有固定名称或跨仓网络。Q29 已选隔离项目专属应用备份/恢复接口设计：完整覆盖 checkpoint 四表的字段、历史、namespace、父关系和 pending writes 的 task_path/idx，一致快照，仅恢复到具名空目标，经正常应用进程和隔离专属角色执行；无任意 SQL/DSN、既有数据库或 biz 入口。先完成精确契约、负例及数据/配置恢复 AC 再核实际资源/版本/副作用；禁止 Agent 直接 DB 客户端、pg_dump/psql/卷拷贝，新增秘密仅受控后台不可见处理。

秘密、业务数据工具链、禁入服务、宿主审批和技术拒绝边界保持。原 MCP 失败不改写；GitHub CLI 使用正常 opaque 认证，不读取个人凭据。删除、共享/生产写入、权限修改、信任激活、新收费及不可逆动作不从普通实施推定。风险/对象/环境/权限实质变化只停受影响步骤；未知结果先对账，成功项不重复。

## 任务与依赖

1. 旧 capability 刷新：输入现 requirements/feature/test/SUT → 新 suite 和历史迁移清单 → EVID-001/002/003 → 独立重算日志/JUnit/历史摘要。第一单元不修改 G21/G8，不称仓外包已成为旧 G21 接口。
2. 归档核验：按 [portable verifier SPEC](../docs/design/sdd/[SPEC]_Portable_Delivery_Evidence_Verification.md) 实施新增只读 CLI 与有意义负例 → ZIP-001/002/003/004 → 实际归档独立核验。旧 run/check 不改。
3. Team 可信源：固定核验定义、控制/发布身份分离、来源绑定 required check、红灯隔离负例方案；准备后再执行精确激活决定。候选可改自身门禁的风险在完成前保留。
4. Gitee：Q27 选择 Owner 正常 Git 不可见认证，定向替代本任务 Q10 延期/新增独立身份条件。已核真实 origin/gitee 目标、源 fd045520 和目标 5d4b0cd5 的祖先关系，正常一次 push 将具名 develop 快进到已接受 fd045520，再以 ls-remote 读回同 SHA；记录在仓外 `gitee-mirror-q27.json`。Git 协议未返回实际账户 ID，不能额外宣称已认证用户身份。本后续分支先 GitHub PR/实际版本审核，后续镜像仅同步已接受 develop；不 force/删除/改远端或个人配置、不扩其他仓库，实际拒绝时保留原错不换路线。
5. 宿主：实际 codex-cli0.147.0 公开协议重新生成，仅 hooks/list/cwds，未发现项目限定信任写入或过滤原始个人命令的接口；不调用原始列表或改个人配置。实际加载/canary 未验证，待正常受支持入口。
6. 隔离部署/恢复：具体资源、受控备份接口及业务断言方案就绪后才执行。现有 Docker 两卷与网络不因无运行容器视为空资源。
7. actual：按 Q25 单独准备采样生产者及审阅链，不将 synthetic 材料重标，不代接手会话修改 evaluation 接受标准。

| 文档类型 | 本单元动作及理由 |
|---|---|
| Plan | 新建本 Plan，旧 completed Plan 保留 |
| SPEC | 新建 portable verifier SPEC，规定新的工程 CLI 不变量 |
| ADR | 本单元无长期信任/权限决定；可信源或备份边界具体方案另记 |
| RUNBOOK | 迁移清单给复现入口；实际部署/恢复 runbook 在对应方案就绪后更新 |
| GUIDE | 同步现交付指南的新完整性核验用法，区别行为/来源认证 |
| STANDARD | 不改变现标准 |
| Local ISSUE | 不机械新增；继续复用本 Plan 与原 trace |
| ASSESSMENT | 仓外验收/迁移报告，实测与未测分开 |
| CHANGELOG | 新 CLI 行为就绪后按实际变更判断 |
| INDEX | 登记新 SPEC/迁移入口，其他条目不改写历史 |

使用普通单 PR，目标 develop；第一单元可独立接受，其他单元不随之完成。共享工作树按文件归属并行：协调者负责 Plan/SPEC/指南/INDEX；证据执行者负责新 suite/迁移清单/对应测试；归档执行者负责新 verifier/对应测试；环境核验者只准备仓外方案。委派均传本文件、真实 worktree/base、AC、产物、限制和返回点；沿用现模型真实配置，未新增付费/权限。

## 验证与验收包

新行为先红态负例再实现；适用 targeted unit、13 BDD、ruff/mypy、文档/原生资产与 schema/trace 检查。整个相关离线矩阵在实现稳定后运行一次，失败修复后只重测受影响项。外部依赖仍 SKIP_POLICY_EXTERNAL_DEPENDENCY，不以凭据存在启用。

新鲜 collector 包在实际已提交候选版本/clean tree上生成到仓外 `D:/workspace/10-software-project/projects/mj-agent-delivery-evidence/agent-first-delivery-followups/2026-10-13/`；原产物不改、不覆盖、不复制为新 SHA。可移植核验先用真实 Git 临时夹具负例，再对具名原产物验证；对象缺失先补正常只读对象获取或标缺依赖，不伪造 Git 来源。

验收包给成果入口、逐 AC、版本/环境/时点、命令原输出和 JUnit、原字节/输入摘要、复现、限制/延期、风险/恢复、Owner 实质决定。独立核验从 AC 建立期望并读真实成果，不能以另一 Agent 的 PASS 摘要代替。第一单元不能证明所有旧 capability 行为或已实现独立可信执行。

## 检查点与完成

当前本地 worktree 从 fd045520 创建，未提交/发布；新 suite/verifier 实施中，新平台身份/规则、容器、备份恢复、实际采样未执行。Q24–Q29 已分别明确方向、预算及备份载体，后续精确资源/版本前置尚未满足。Q27 的原已接受 develop 镜像快进已读回验证；旧 Q10 的当时延期及宿主/MCP 限制原记录保持。

阶段结束、集成前、交接时在仓外新检查点保存实际 ref/SHA、授权、证据、失败/未知/延期及下一步；不覆盖上轮已完成收尾事实。只有对应 AC 满足、成果可用并获得 Owner 实际版本接受后才 completed；集成、验证、交付、接受分别记录。
