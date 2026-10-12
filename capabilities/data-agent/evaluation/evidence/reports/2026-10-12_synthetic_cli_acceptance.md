# #582 T-006 synthetic-only CLI 软件验收

本轮接受基线：Owner“采纳并授权离线 CLI 实施（推荐）”；并行归属：Owner“授权协调并由本线程接续（推荐）”。原任务已停止写入与测试、无在途操作，22份原候选已具名备份。实施者Codex（当前线程），无子Agent委派。基线5b8833c523f4401de7b70deb5a82b908f3a9c763；候选未提交，最终源码摘要见本报告末尾。

## 本地验证

- 公共入口main(argv, *, repo_root)为真实源码；必需--synthetic-fixture，manifest先读且source_kind必须synthetic_fixture。runtime_observation返回2/ACTUAL_ENTRY_DEFERRED；其余输入读取、replay与输出创建均未发生。
- 固定22-case与34条Agent角色review未改，expected标签不由实现生成。完整synthetic两目录回放，JSON/Markdown字节一致、退出3/SELFTEST_ONLY、metrics=null、baseline_eligible=false；合成确认红线失败返回6/SELFTEST_HARD_FAIL。真实子进程使用白名单环境及应用导入/秘密读取/网络哨兵。
- 初始RED：旧签名缺repo_root、缺开关仍读文件（2 FAIL）。Windows输出属性权限缺失先暴露再修复。OFFLINE/RECALL路径及fdopen构造泄漏反例分别观察3 FAIL、1 FAIL，修复后针对性绿色；未以异常被安全转2来伪装“未读取”。
- 本轮完整命令结果与exit见[原始离线验证记录](../bdd/2026-10-12_synthetic_cli_pytest.txt)。核心64项、CLI105项、BDD10项，共179项；旧145项及中间171项不替代最终候选结果。
- 四个新BDD覆盖确定性报告、actual早拒绝、危险路径及碰撞/部分失败，原六个核心BDD保留；见[BDD记录](../bdd/2026-10-12_synthetic_cli_scenarios_pass.md)。
- Ruff全仓、mypy全src、能力/trace/contract/BDD/INDEX/Python契约与文档检查：最终结果在下方矩阵。第三方gherkin的20条DeprecationWarning保留；不修改依赖或守卫来消除。
- 核心schema/judges、窗口/阈值/兼容键、原dataset/catalog和既有runtime未修改。三处报告文案替换与core docstring更正使当前报告字节/摘要变化；历史报告未重写。

## Agent 合成角色与独立 SWE 核验

Domain轮重新按固定reference核对daily下界2026-09-12、monthly下界2026-07-01，HP-03仅daily/30d或monthly/3m；保留明确用户窗口及signal例外。Prompt轮核对完整回复、拒答/澄清/披露、原始首次attempt与绑定review，不用关键词代替语义。34条原review保持hash-bound、期望labels未改。

SWE轮从原SQL/轨迹/回复/固定规则与实际diff独立复核：首轮失败仍保留，全部红线尝试不可被最后成功覆盖；22条计划分母不变，0.03精确边界与同条件兼容规则仍由原64项核心测试承接。CLI的运行报告明确synthetic，无法转成actual基线。这是同一Codex的分轮角色模拟，不是另一真人/子Agent的签署，不代替Owner最终接受。

## AI 自检与范围

- 新runner与私有_file_io独立于agent/server/tools/config；只采用标准库与既有锁定依赖。
- Windows固定NTFS逐组件句柄相对打开；祖先句柄不共享写入/删除，拒绝reparse、跨卷、最终路径逃逸、多链接与身份变化；读取10MiB+1上限。目录仅请求遍历/属性权限，文件使用NO_RECALL且拒绝OFFLINE/RECALL属性。
- 输出为新目录，父必须存在；FILE_CREATE保证独占，serialize在创建前，两份写完/关闭后才返回core分类。任何写入/关闭错误返回2，安全诊断可包含core_exit_code；保留部分新目录，不自动删除、不承诺报告对原子性或耐久性。
- 本轮只能证明已覆盖的Windows原生行为。Linux/macOS文件入口明确延期并返回FS_CAPABILITY_UNAVAILABLE，不尝试IO，不保留无法约束祖先rename的dir_fd候选。纯内存核心不受平台延期影响。没有取得Linux原生成功证据。
- 路径拒绝先于metadata；错误只含固定reason_code，不回显argv、路径、载荷、OS异常。审阅未发现新scope漂移；精确暂存仅批准的test_eval_runner.py与eval_cli/expected.json。
- 原并行候选及旧证据保留；真实main后对齐两份Python/CLI契约，原六个behavior场景不变。没有加入治理政策、CI/守卫/配置/依赖修改。
- A1/A2/A3：capability-package/draft元数据已核，working Plan active；根CHANGELOG frontmatter豁免。A4/A5本地链接/索引闭合；A6既有AGENTS高频runtime入口无变化，无需改写；A7–A14本任务未触相应保护资产。OB时间、边界、历史轮次与当前状态分别标识。
- 提交/推送/PR/Issue发布与关闭未授权、未执行；不存在本轮PR说明或commit SHA，不以工作区完成冒充远端交付。

## 延期与接受状态

| 对象 | 当前结论 |
|---|---|
| T-006 Windows synthetic-only CLI | VERIFIED_OFFLINE_SOFTWARE，供Owner接受 |
| Linux/macOS文件入口 | DEFERRED_FS_CAPABILITY；本轮无原生成功验证 |
| actual/runtime_observation文件入口与baseline CLI参数 | DEFERRED，不接受 |
| actual采样、来源/脱敏真实性、target审阅、runtime EVAL | NOT_RUN/DEFERRED |
| #582 / Plan / capability | OPEN / active / idea，last_verified=null |
| #161/#504/#583–#586及probe-fixture | 原scope/状态与不适用结论保持 |

Windows句柄分享/rename与相对RootDirectory行为依据[CreateFileW官方文档](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)及[NtCreateFile官方文档](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile)，并由本轮原生用例核验；平台延期是对缺能力的工程判断，不宣称跨平台通过。

## 最终验证矩阵与版本绑定


| 命令/检查 | 实际结果 |
|---|---|
| Hardened offline pytest（core + CLI + BDD） | exit0；179 passed，20条第三方DeprecationWarning |
| 全仓ruff / 全src mypy | 各exit0；ruff无错误，mypy55 source files |
| G1能力schema / G2 trace / G3契约 | 各exit0；各1P/0W/0F；3份契约文件 |
| G19 scenario trace / G21 acceptance | 各exit0；各10P/0W/0F；G21为静态证据选择，不替代真实测试 |
| G22 unautomated subset | exit0；0P/0W/0F，当前没有unautomated场景 |
| G9 INDEX --check --strict | exit0；1P/0W/0F，7 specs，无需重生成 |
| V1 Python --all默认模式 | exit0；12P/13W/0F，信息WARN保留；strict模式未声称零WARN |
| frontmatter / wikilinks官方检查 | 各exit0；151 canonical docs；0 archive/A4 root violations |
| 本轮相对链接及package元数据补充检查 | PASS；64个本地链接，0缺失，4份draft/version0.5 package Markdown |
| 改动/保护面与diff --check | PASS；无runtime/CI/守卫/依赖改动、无空白错误 |
| 原candidate备份 / Issue状态只读核查 | 原22份快照完整；#582/#161/#504/#583–#586 OPEN，#564 CLOSED |
| live/actual、CI远端运行、人工/外部Approve | NOT_RUN；本轮无PR或平台发布 |

候选摘要：f05fd48367e8a1a3b33d63d1f330835d8085541d8f8cbc1e06c9fe1fca4840eb；21份源码/契约/测试/固定输入原bytes绑定，算法与逐文件SHA见[版本绑定](2026-10-12_synthetic_cli_binding.json)。这是未提交候选摘要，不是commit或授权凭证。独立AST与34条review绑定复核的事实见[合成角色事实](2026-10-12_synthetic_cli_role_facts.json)。

反扫发现原#161文档与全局EVAL模板仍包含旧--eval/--profile示例；两者是延期actual入口的历史候选说明，本轮不改#161原scope或全局模板。当前supported调用只以本package RUNBOOK中的显式synthetic命令为准。后续actual方案需承接这些入口差异，不能把旧示例当可用命令。

初次相对路径调用G3触发既有checker的Path.relative_to异常，改用其支持的绝对capability参数后通过；未修改checker。补充链接扫描器的首个草案不支持括号文件名/escaped pipe，已复用现有clean_target/解析规则后复核，未对误报目标作修改。角色摘要独立复核先遗漏规范化LF，按原bytes契约补齐后34条全部匹配；不是观测或review改动。

自检结论：GO供Owner审阅本轮离线软件；无发布授权。12项清单的模块/边界/敏感信息/文档/分支/范围/双段/CHANGELOG/引用已核；commit message和PR字段为NOT_APPLICABLE（本轮未创建），system.md版本/EVAL backlog为NOT_APPLICABLE（未改runtime canonical）。A12–A14未触资产不重验作运行证明；安全固定期望、严格窗口和原API保持。


发布准备补充：CI采用Linux runner。本线程执行mypy --platform linux先观测私有Windows IO的6处attr-defined错误；补入sys.platform条件与显式成员类型后，Windows与Linux类型模型均55 source files通过，全仓ruff通过，179项相关离线测试重新通过。Linux类型检查是静态证据，不是Linux原生CLI实跑；actual/baseline与Linux/macOS文件入口仍延期，未改CI、守卫、核心规则或既有runtime。新候选摘要已同步版本绑定；旧摘要42f6de13…仅对应前一交付轮次。Git暂存/提交/普通双推/Draft PR具体发布方案已在本地准备，当前发布授权仍待Owner决定。

Git发布记录（与上文验收/准备时点分开）：Owner现已明确授权31文件精确暂存、两次提交、Gitee→origin普通双推及develop-base Draft PR，并允许核查CI。C1已实际提交28925619c45ce7c35a376754c439885c0300f510；author/committer为仓库既有身份ranzuozhou，Codex为实施者，不造Co-Authored-By。源码验证摘要不变。本报告写入C2前，文档/契约提交和远端发布尚未完成；后续真实SHA、PR URL与CI结果由任务记录报告，不预填通过或外部Approve。未授权转Ready、审核请求、merge、删除、Issue状态变化、actual/live或runtime/CI修改。
