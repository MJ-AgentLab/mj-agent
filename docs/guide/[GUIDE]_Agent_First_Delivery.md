---
type: guide
domain: WORKFLOW
summary: 使用接受基线、任务授权、独立核验和可恢复证据自主交付 mj-agent 软件
owner: ranzuozhou
created: 2026-10-12
updated: 2026-10-29
state: draft
track: engineering-workflow
---

# mj-agent Agent-first 交付指南

> **适用范围**：mj-agent 工程交付与治理改造。
> **目标受众**：Owner、工程师、执行与独立核验 Agent。
> **版本**：v0.6 草案。
> **最后更新**：2026-10-29。
> **规则依据**：本项目 ADR-042 及现行政策。
> **关联文档**：[[policies/ai-agent|AI Agent Boundaries]]、[[policies/git-branching|Git Branching]]、[[sdd/workflows/execution-loop|Execution Loop]]。

## TL;DR

阅读约 6 分钟。用既有任务记录分别保存接受基线和动作授权，Agent 自主构建/验证，Owner 作实质决定并接受成果；平台前置不足时记录真实状态。

## Prerequisites

读者应了解本项目永久数据与秘密边界，并能定位任务 Plan、政策和接受证据。独立Agent审阅真实配置/守卫负例，执行Agent走正常宿主和受控后台路线；Owner在聊天决定实际成果/SHA。既有秘密不读取，新后台/实际启动能力未实现不得PASS。

## 目录

- §0 适用场景
- §1 启动与自主推进
- §2 PR 与执行身份
- §3 启动前置与平台核验
- §4 独立核验与验收包
- §5 检查点、恢复与接受

## §0 适用场景

用于边界明确的软件交付试点、治理迁移和交接恢复。Humans steer. Agents execute. Harness assures. 本指南连接已有记录与规则，具体行为以政策、契约和任务接受基线为准。

## §1 启动与自主推进

在 Issue、Plan 或 capability tasks 中分别记录接受基线与执行授权。接受基线包含目标、使用者、范围、可观察 AC、必要运行条件、风险及延期；授权包含允许动作、精确对象、环境、权限、副作用、资源限制、失效及停止条件。普通技术选择、测试安排和局部修复由 Agent 决定；实质取舍先给具体选项及推荐理由。

技术权限、工具存在或 CI 通过不产生授权。授权未撤销且目标、对象、环境、权限和风险边界未实质变化时复用。普通代码内容更新仍需核验实际 diff/SHA，但不自动要求重复批准。具名删除、权限变化及高风险不可逆操作单列控制条件；秘密和 biz 旁路始终禁止。

### Working 与原意入口

新材料按 `plans/<topic>/` 聚合，主 `[PLAN]_<topic>.md` 与目录一致；四种 topic 仅用真实主要 Issue/PR，整体集成 PR 优先，未明省 P。主要关联首次明确/纠错/明确更换才受控补号，同步活动引用和路由，task_id/INTENT ID/固定历史基线不变，不追随子 PR 改名。Intake 可先建目录，独立报告任务可始终无 Plan，共享材料一个主归属，子 Plan 各有目录，不强制 INDEX。

先由 doc-author 保存原意：独立 [INTENT 正本](../intent/README.md)或简单任务唯一 Issue 原意区；来源/维护责任不明只存 working 草稿。flow-intake 澄清实施范围，flow-plan 编排实施，不新增 flow-intent。Plan 写清完整可恢复接受基线、本次承担/依赖/背景，回答 [Plan 模板](../_templates/TEMPLATE_PLAN.md) 的七题；doc-plan 仍只做实际对象缺口评估。

working 七字段必填含 track，不强制 domain/version；新 Plan draft，有明确采纳依据后 active。仅主 Plan completed 必须 AC 满足、成果可用、Owner 明确接受准确版本；Report/Intake/Assessment 可由 Agent 按自身交付条件完成，自身含 Owner 接受仍满足。报告完成不表示整体接受，独立任务整体接受在已有 Issue/会话/任务记录表达，不补 Plan；主 Plan 的一次明确接受可覆盖整体范围。完成原位保留，working GC/候选检测已退出；旧根文件兼容、历史不默认迁移。

运行 `python scripts/check_frontmatter.py`、`python scripts/check_working_docs.py`、`python scripts/check_wikilinks.py` 核元数据、目录/唯一主Plan和按位置解析的深相对链接。机器 PASS 不证明真实编号、来源忠实、接受决定或运行。

## §2 PR 与执行身份

单 Issue 同时一个主 PR（通常 target develop），分段则主 PR 依次；强依赖任务需子 PR 时用 `feature/task-<任务标识>-integration`。任务记录登记每条精确子 head → integration base、预期贡献和最终 base，创建命令显式传 base。集成分支验证累计差异与组合 AC，子 PR 已合并只表示候选集成。实施前核实平台规则、CI触发及merge是否导致部署。历史release develop→main是独立发布流程，须Owner接受、具名发布授权及未来规则映射；当前有限解析器不声称支持。

专用执行 App 仅安装本仓库，日常无 Administration、Checks write 或 bypass。Owner在聊天对实际成果/SHA作批准或接受决定；Agent依该真实决定用不同于PR作者/最后推送者的Owner身份执行平台有效审核，补推重新取得有效决定/审核。治理交付所需 Workflows write 属临时、仓库全域权限，Agent结束后按授权移除临时权限、撤销token并关闭通道，逐项留证。仅新建单仓App私钥/短期token经受控后台创建、DPAPI保存、签名、注入和撤销，模型/聊天/日志不可见；现有应用/MCP/DB/个人秘密永不读取。

平台尚未配置或宿主未加载时记录未验证/依赖阻塞，不能以文件修改声称完成。首期门禁仍可能由候选自身降低，Owner 对门禁、保护及接受基线的人工审核提供过渡补偿；独立受控强制核验系统延期。

## §3 启动前置与平台核验

**本任务 Q10/Q11 适用范围**：Owner 批准 `agent-first-delivery` / `maintain/agent-first-delivery` 及原已授权具名 canary 向 `MJ-AgentLab/mj-agent` 的 origin 发布，Gitee 被动镜像延期；宿主项目/hooks 运行验收独立延期。具体接受基线、精确对象、授权和实际状态以[任务 Plan](../../plans/[PLAN]_agent_first_delivery.md)为准。两项均为 DEFERRED，不计 PASS；默认双推和原生信任规则保留，既有秘密不读、新 App 例外不扩 Gitee。GitHub 闭环仍须实际 CI/平台 canary、有效独立审核、版本核验及 Owner 接受；宿主延期不是加载证明。

1. 核Owner本次目标/对象/权限/规则授权及实际基线。读取`.github/agent-first/`的App manifest和ruleset，独立Agent读取真实配置/守卫、复现必要负例并输出证据；不以文本签字或静态PASS代实际加载。
2. 执行Agent通过正常受控路线新建`mj-agent-delivery-executor` App，仅安装本仓。作者/推送/PR/merge身份无Administration、Checks write和bypass；规则应用使用Q3明确授权的管理路线，不能给执行App增加管理权限。
3. `scripts/sdd/delivery_executor.py`后台只处理本次新App材料：创建私钥/短期token、DPAPI保存、签名、进程注入和撤销。值不进入模型、聊天、命令输出或日志，公开接口只返回脱敏状态/非秘密ID。原应用/MCP/DB/个人秘密不读取、不搬迁、不借用；后台未实现或未验证时保持UNMET_DEPENDENCY/NOT_TESTED。
4. 当前项目配置按 [Codex开发配置](../../policies/codex-development.md) 采用MCP-only结构，不注册项目hooks/rules；基本项目/MCP信任及实际功能按任务需要核验，不以旧守卫加载取证阻塞普通交付。历史Q11延期原记录保留，未测不改写成PASS。
5. 从项目根运行`uv run --frozen --no-sync python scripts/sdd/check_delivery_platform.py`只核准备文件；加`--inspect --repository MJ-AgentLab/mj-agent`只读核远端，未提供新App后台时仍不能证明执行身份。提供`--executor-vault <仓外具名目录> --permission-phase bootstrap`会实际调用后台创建并撤销新App短期token，返回单仓权限和同一App/installation/repository身份观察；这项副作用须属于已有新App授权。CONFIG_VALID仅准备文件有效，CONFIG_VERIFIED仅已观察平台配置有效；均不证明宿主加载、canary或Owner接受。
6. Owner在聊天依据实际成果/SHA与证据作决定后，Agent核决定未撤销且版本/风险仍匹配，使用不同于作者/最后推送者的Owner身份执行平台审核。不能由技术检查、App作者或自写授权记录替代Owner决定；补推使旧有效性需重判。精确具名canary验证红灯/讨论/最后推送审核与无bypass合并，未做项保持NOT_RUN。
7. Agent在范围授权内撤回临时Workflows write、撤销新App短期token并关闭临时通道，分别核真实结果，不输出凭据。原工程师向导已superseded，仓外旧向导文件保留历史，不删除；撤销或正常执行机制不足只阻塞相应项。

Manifest的webhook关闭和URL占位只说明准备格式，不证明GitHub注册已接受。App创建、平台规则、信任加载与恢复均须实际运行证据，不能因新执行主体决定提前PASS。

GitHub对没有规则写权限的请求隐藏`bypass_actors`；缺失字段保持未知。[GitHub规则API](https://docs.github.com/en/rest/repos/rules#get-a-repository-ruleset)说明该可见性限制。已获具名管理核验授权时，可明确加`--management-inspect`：新App实际身份核验先通过，再由`ranzuozhou`管理身份仅作同仓规则GET；保护字段必须与App观察相同，只补隐藏的actor事实并记录来源。App本身的can-bypass仍必须由App观察，管理身份不得代替日常执行，不给App新增Administration；权限拒绝不触发备用路线。

后台在筛选公开规则参数前，计算原始`id/name/target/enforcement/conditions/rules`完整规范JSON的`protection_sha256`；未公开的规则参数仍绑定其中。管理GET必须与该完整摘要匹配，再补隐藏actor。缺失、非JSON、错配或格式无效的摘要不能通过；不能为了让两份投影一致而删除保护参数。

分层路由在既有Plan放 `agent-first-routes` 块，准确字段与例子见Plan模板；前置未满足保持active=false，名字及登记本身不生成操作授权。新证据artifact只记录授权范围观察，不认证授权来源。

### 受控后台入口

后台从已审阅版本启动，Python使用`-I`隔离启动，进程环境只保留非秘密系统变量。新App存储目录必须位于仓外，末级名称固定为`mj-agent-delivery-executor`；不打开或复制其中DPAPI文件。以下参数说明不产生新增操作授权：

- `serve --vault-dir <仓外具名目录>`：仅监听本机回环的随机端口，返回公开注册/结果入口。GitHub转换返回的新私钥在后台加密保存；回调临时代码被消费后重定向至不含代码的结果页。注册不自动完成安装。
- `audit --vault-dir <目录> --permission-phase bootstrap|daily`：实际核App、installation、授权层及token单仓范围，并在返回前撤销token。`public-get`仅查询具名仓库和规则的公共元数据，不接受任意API或秘密输出。
- `push`、`pr-create`、`merge`：只支持本仓具名动作、显式分支/base及实际版本核对；沿用任务登记路由及正常仓库门禁。不提供任意命令、凭据dump或bypass。

注册attempt、token创建、平台动作或撤销结果未知时，保留检查点并先对账；不能删除标记重试、用旧身份补做或因进程成功宣称业务通过。关闭注册服务只停止监听；临时Workflows权限移除和token撤销各自核实际结果。

执行前只读取Git配置名称并拒绝未知或可执行来源。Owner Q9定向允许规范名称`alias.pushall`及合法分支名下的`vscode-merge-base`缓存键：固定内建命令不会选择该alias，IDE键不决定后台base/head。不读取真实值、不调用alias、不修改持久配置；其他alias/未知键、credential/header/include/gpg及active hook仍拒绝。该分类依赖已核验工具版本和固定命令集合；两者或键的使用方式变化后重新评估，不能借此解除其他实际拒绝。

通用软件证据使用`evidence/delivery/agent-first.suite.json`，不把Linux上的Windows原生SKIP计作通过。注册或使用Windows后台前，另运行`evidence/delivery/executor-windows.suite.json`取得同一版本的实际DPAPI/junction/句柄合成检查；该包证明所测宿主的软件行为，仍不证明真实App、来源认证或hooks启用。其他宿主必须重新核验。

## §4 独立核验与验收包

核验者读取真实 diff、产物及基线，独立建立期望并复现关键检查。按风险覆盖工程、领域、Prompt 和供应链视角；不规定真人或人数。委派包含目标/AC/决定位置、输入范围依赖、真实工作区及比较版本、产物及证据要求、授权资源停止条件和返回点。并行写使用独立工作区或明确文件归属，共享资源写由协调者排序。

未参与实现的独立上下文模拟使用者、运维与审查者，同对象最多两轮，仍有分歧汇总给 Owner；证据绑定实际 commit SHA、环境和时点，模拟不替代 Owner 最终接受。

每个交付单元提供成果使用入口、逐 AC 预期/实际、版本环境时点、复现方式与证据位置、未实测/延期、风险与恢复、待决定事项。CI 仓外 artifact 绑定 head/base、测试版本、产物/输入/依赖摘要、环境、命令退出及逐 AC 状态。基线、产物或环境变化后重判证据有效性；HTTP 成功、命令成功、零行和 workflow 结束不独自证明业务正确。

本次治理软件交付执行新的证据要求，并设计#582治理证据格式。Owner已将#582 CLI实现/commit转交“整理 #564 EVAL 承接方案”，新CLI接受基线与实际交付由接手会话维护；原边界和未提交材料保留，转交不计交付PASS。历史 capability 逐步迁移；synthetic 和虚构 actual 条件只证明离线软件行为，不产生真实 runtime 来源或基线。缺少非核心能力可以延期对应入口，核心自身 AC 通过后分段交付；延期影响整体基线时由 Owner 决定。

后续主线状态：#589已将synthetic-only CLI合入develop，#582/其Plan仍OPEN/active，actual/live未运行。原转交记录是当时检查点；当前治理组合验证以实际更新后的develop为准，不重建已实现CLI或把其合入等同整体EVAL接受。

### 原始归档跨宿主核验

`scripts/sdd/verify_delivery_archive.py` 只读原始交付 ZIP，并依据调用者明确指定的预期版本核对真实 Git 对象、suite、基线、输入、日志、JUnit 身份和逐 AC。验证机 HEAD 可以不同于原测试版本；必须已有原 head/base/tested 对象，缺失时先通过正常只读 Git 获取，或保留缺依赖。不能重建等价对象、替换原执行路径或把验证机时间写成原运行时间。

调用时提供原 ZIP 与其 SHA-256，以及 `--repository`、`--head-sha`、`--base-sha`、`--tested-sha`、`--tested-tree`、`--suite`、`--execution-kind`、`--run-url`；`--report` 指向仓外的新文件，`--repo-root` 可指已有 Git 对象库。各项预期应来自已核版本和原运行记录，不能仅采用待验 ZIP 自报的值。准确参数、不变量及负例见 [portable verifier SPEC](../design/sdd/[SPEC]_Portable_Delivery_Evidence_Verification.md)。

成功返回 exit0 / `INTEGRITY_VERIFIED`；完整性拒绝为 exit1，非法输入或缺工具/对象为 exit2。归档不提取，最多 64 MiB、512 个普通成员、单成员 32 MiB、展开总量 128 MiB；秘密路径、链接、重解析点、覆盖报告及混合原输出根均拒绝。新报告保留原执行版本、环境、时间和路径，并另记验证机信息。它不重跑原命令、不认证执行来源，也不改变原 `delivery_evidence.py run/check` 的结果或历史失败。

### 历史 capability 软件证据刷新

`evidence/delivery/legacy-capabilities.suite.json` 选择旧六项能力中的 13 个离线 BDD 身份及 11 个纯软件控制，并检查历史迁移清单。通过 `delivery_evidence.py run` 在实际已提交、干净且依赖锁定的候选上生成仓外证据，再用原 `check` 核验同一执行版本；移到另一宿主后可使用上述原 ZIP 完整性核验。

清单 `evidence/delivery/legacy-capabilities-migration.json` 保存原 20 个文件的摘要、每个场景的软件覆盖、政策 SKIP、未运行和 G21 接口迁移状态。清单本身是准备记录，实际结果在绑定版本的新包中；软件 SELFTEST 不能成为 actual 运行、来源认证或 Owner 接受。未选中的外部/持久化场景及未迁移的 G21 接口继续按原状态跟踪。

本次后续任务 Q27 已允许正常 Owner Git 不可见认证，将已接受的 develop 快进到具名 Gitee 镜像。具体动作和实际读回结果见[后续 Plan](../../plans/[PLAN]_agent_first_delivery_followups.md)及其仓外证据；原 Q10 的当时延期记录保留，不扩大到其他仓库、分支、凭据或 force push。

## §5 检查点、恢复与接受

阶段完成、集成前和交接时，在现有记录保存目标/AC/授权、workspace/ref/SHA/集成状态、证据、在途动作、失败未知延期、下一步及停止条件。换窗、压缩及再委派后先读取记录并核实现状；超时或结果未知先对账运行状态和副作用，再决定是否重试，成功动作不重复。

分别表达候选已集成、已验证、已交付、待 Owner 接受、已接受、部分完成、延期、失败和未知。主 Plan 只有对应接受基线满足、成果可用且 Owner 明确接受准确版本后才标 completed；其他 working 按自身已确定交付条件，报告完成不推导整体接受。仓库批准、部署授权、实际运行验证和业务接受各自留证。

局部可逆动作在授权内完成；共享环境核对目标与并发。恢复随风险使用回滚 PR、备份恢复、补偿或降级；存在文档不等于恢复已验证。actual 采样、部署自动化、独立可信核验和实际恢复演练为延期。评价时记录 Owner 常规介入、周期、缺陷返工、门禁负例、证据完整性、恢复结果及资源消耗。

## 关联文档

- [ADR-043](../../decisions/ADR-043_Working_Doc_And_Intent_Governance.md)
- [ADR-042](../../decisions/ADR-042_Agent_First_Delivery_Governance.md)
- [Plan 模板](../_templates/TEMPLATE_PLAN.md)
- [开发入口](../../AGENTS.md)

## 更新记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-10-12 | v0.1 | 建立任务授权、独立核验、仓外证据和平台启动指引；#582 转交另会话 |
| 2026-10-12 | v0.2 | Owner Q4/Q5/Q6取消工程师向导；受控新App后台、独立Agent审阅/正常宿主项目启用和依据真实聊天决定执行平台审核，实际能力未验证 |
| 2026-10-12 | v0.3 | Q9定向惰性配置兼容与完整规则摘要比较；实际App/宿主/平台状态由Plan和仓外运行证据分别记录 |
| 2026-10-12 | v0.4 | Q10限定本任务origin发布、Gitee镜像延期；Q11宿主运行验收延期，默认双推/原生信任及实际GitHub门禁保留 |
| 2026-10-13 | v0.5 | 新增原始 ZIP 跨宿主完整性核验、历史 capability 软件证据刷新入口；区别原执行与新验证，记录 Q27 具名镜像后续 |

| 2026-10-29 | v0.6 | #608：working目录/原意入口/七题、按文档完成及整体接受、独立验收两轮与新校验入口 |
