# #582 T-007a baseline CLI 软件验收

本轮状态：VERIFIED_OFFLINE_SOFTWARE，供Owner最终接受；candidate UNCOMMITTED。Owner于2026-10-12明确采纳A并授权G1工作树、baseline CLI、两份main契约/行为契约、具名文档、必要离线测试与Agent合成验收。实施者Codex，同Agent分轮，无子Agent委派。基线a96d759c080f4568e6810084f90fadce7b2c75cf，分支feature/582-baseline-cli；工作树经G1创建并核实inside-work-tree=true。

T-006已随#589合并；五项CI成功来自既有收尾记录，本轮未联网重验。历史报告不改；不提交、推送、PR、发布评论、关闭Issue或重复收尾。#582/Plan/capability继续OPEN/active/idea，last_verified=null；#161/#504/#583–#586与probe-fixture原scope/状态及不适用结论保持。

## 本地验证

| 检查 | 本轮实际结果与边界 |
|---|---|
| Hardened offline pytest | exit0；64 core+156 CLI unit+11 BDD=231 passed；22条第三方gherkin DeprecationWarning保留 |
| 全仓Ruff | exit0，无错误 |
| 全src mypy Windows模型 | exit0，55 source files |
| 全src mypy Linux模型 | exit0，55 source files；仅静态类型模型，不是Linux原生CLI成功 |
| G1 schema / G2 trace / G3 contracts | 各exit0，1P/0W/0F；两份YAML与behavior.feature |
| G19 scenario trace / G21 acceptance | 各exit0，11P/0W/0F；G21读取本轮实际BDD pass_rate=1.0，不代替进程证据 |
| G22 unautomated | exit0，0P/0W/0F，当前11个场景均automated |
| G9 INDEX --check --strict | exit0，1P/0W/0F，7 specs；无需重生成 |
| V1 Python契约默认模式 | exit0，12P/13W/0F；信息WARN保留，不声称strict零WARN |
| frontmatter / wikilinks | 各exit0；151 canonical docs合法；archive引用和5个root入口均0问题 |
| 具名新增/修改文档本地链接与元数据 | 独立补充检查exit0：176个本地链接、0缺失；4份draft/0.6、Plan active、idea/null保持；全仓脚本不覆盖全部capability/Plan相对链接 |
| actual/live与远端CI重跑 | NOT_RUN，未连接服务，不产生实际EVAL或来源接受 |

Agent/CI测试通过既有scripts/sdd/run_offline_pytest.py，复用develop的既有.venv解释器；没有安装/同步依赖、创建venv或修改个人配置。测试与子进程绑定当前工作树src，临时目录和白名单子进程环境不依赖开发机固定路径。复现入口：

    uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit/test_eval_core.py tests/unit/test_eval_runner.py tests/bdd/data_agent/evaluation/test_evaluation_bdd.py -q

原始本轮完整输出见[pytest记录](../bdd/2026-10-12_baseline_cli_pytest.txt)，[BDD记录](../bdd/2026-10-12_baseline_cli_scenarios_pass.md)覆盖11个场景。既有受控runner接受已跟踪测试模块的工作区修改，未暂存任何文件或绕过检查。

TDD RED实测exit1：16 failed/135 deselected，旧CLI在参数层拒绝--baseline，因而manifest-only与原bytes/格式诊断断言失败。最小实现后首轮150P/1F，失败为新测试误写NON_FINITE_NUMBER，而既有解析器为NON_FINITE_JSON；仅修期望。属性注入首次位于_info校验后，导致3F/228P；改为系统GetFileInformationByHandle返回点注入后231P。核心和_file_io未修改，不以INTERNAL_ERROR/exit2代替“未触发IO/核心”的证明。G22首次命令误指不存在脚本，保留exit1；定位既有check_bdd_unautomated.py后exit0，未修改checker。

## API、输入与进程结果

main(argv, *, repo_root)、ReplayInputs/replay签名保持。唯一源码变更是runner.py：可选--baseline、同一后端有界原bytes读取、空文件和JSON object前置校验。缺省b''；显式空文件BASELINE_INPUT_EMPTY，null/数组/标量BASELINE_NOT_OBJECT，非法JSON/UTF-8及既有重复key/非有限数/深度规则均安全返回2，不调用replay或创建输出。合法JSON object只表示解析成功，不认证基线来源/有效性。

actual manifest仍在其余载荷（含baseline）读取、replay、输出之前返回2/ACTUAL_ENTRY_DEFERRED；无效路径可在manifest读取前被词法拒绝。10MiB、root边界、秘密/网络/设备/软硬链接/reparse/别名/替换和独占输出保护沿用原后端。输出写入/关闭故障保持2，部分目录保留；不承诺报告对原子提交或fsync耐久性。

SELFTEST_ONLY仍退出3，合成确认红线失败仍退出6；baseline不掩盖安全失败。actual的0/4/5/7仍不可达，help0不表示EVAL通过。synthetic在核心基线比较之前返回NOT_EVALUATED，delta=null、runtime metrics=null、baseline_eligible=false；baseline参数尚不交付实际比较。

留存的三次真实进程回放分别不带/带/重复带baseline，白名单环境加应用导入/秘密读取/网络拒绝哨兵，三次exit3、stdout/stderr为空，JSON和Markdown字节一致。详情和逐输出SHA见[角色与进程事实](2026-10-12_baseline_cli_role_facts.json)。复现synthetic命令见[RUNBOOK](../../runbook.md)，baseline使用tests/unit/fixtures/eval_cli/baseline.synthetic.json。

baseline固定文件为2026-10-12_synthetic_replay.json历史SELFTEST_ONLY报告的原bytes复制，SHA-256为7c5047a7520ba216aef1d31dd2dcc742718baee2d1c7d1fb93aa863db501e999；保留CLI_ENTRY_DEFERRED历史文案，不重写旧报告。它不是有效runtime基线；固定期望不由本次待测实现生成。当前manifest仍只绑定config/dataset/observations/reference原bytes；baseline/reviews摘要单独保存在验收事实与版本绑定，不新增schema或报告字段。

## Agent 合成角色与独立 SWE 核验

Domain轮核对固定reference：daily下界2026-09-12、monthly下界2026-07-01，HP-03仅daily/30d或monthly/3m成对，EG-06用户窗口下界2026-09-28；signal例外与全部22条原dataset保持。Prompt轮核对原始回复/首次轨迹与语义标签，34条review保留agent_simulated和两轮引用，不改expected.json或按新程序生成期望。

SWE轮从原始JSON独立计算规范化观测摘要及config/reference原bytes绑定，34条全部匹配；再对照固定case标签与真实CLI报告、基线原bytes、无比较/无runtime指标与三次进程结果。原64项核心测试继续覆盖首次失败、完整分母、同条件兼容、精确0.03及红线优先。角色事实为同一Codex分轮模拟，不是外部签署，不替代Owner最终接受或actual独立审阅。

## AI 自检、文档与范围

实现风味A；declared-contract-change已获得本轮明确批准。两份契约的main不变量同步，新增1个baseline隔离BDD；既有actual早拒绝携带unread baseline，危险路径BDD覆盖baseline，unit保留config/output原覆盖并新增baseline。scope-drift=None；代码只有runner.py，辅助解析/IO不新增公开符号，不导入服务/配置，不新增依赖。

| 改动组 | scope与原因 |
|---|---|
| runner.py | 可选参数、原bytes传递和格式闸；Plan §8.9/SPEC §2.1/§5.7 |
| 两份main YAML、behavior.feature、trace | Owner批准的契约差异和REQ-004/005/006→BDD→测试→证据 |
| test_eval_runner.py、BDD steps、固定synthetic baseline、fixture README | 必要输入/保护/进程反例与固定资料来源；原core和expected不改 |
| spec/requirements/design/tasks/runbook、Plan | 当前状态、授权、退出/输入语义、来源与平台延期，历史记录保留 |
| docs/capabilities INDEX、CHANGELOG | 入口和可见参数同步 |
| 本轮evidence | 自动测试、合成角色、进程与raw-byte版本绑定；不保存actual报告 |

A1–A3：Plan active/code，4份package Markdown draft/0.6，capability idea/null；capability-package不新增track字段，根CHANGELOG元数据豁免。A4显式链接补查；A5两处入口同步、自动INDEX无需生成；A6既有高频runtime入口和政策未变化，不改AGENTS。A7–A14无相应资产变更，SKIP；不把守卫静态/未触及当宿主加载证明。OB历史/当前和软件/实际验收分开，不宣称延期通过。

12项自检：模块、数据来源（纯synthetic）、敏感信息、文档、分支、范围、双段、CHANGELOG、反扫均通过；commit message和PR字段为NOT_APPLICABLE（本轮禁止发布）；system版本/EVAL backlog为NOT_APPLICABLE（未改runtime canonical）。5a无rename/move/SQL迁移或runtime改动；反扫只命中原#161和全局EVAL模板旧--eval/--profile占位，保留原scope，本轮supported调用以RUNBOOK为准。5b本轮只新增evidence；5c入口与日志同步；5d新增baseline文义与实现闭合，无后续SPEC Delta。

[版本绑定](2026-10-12_baseline_cli_binding.json)覆盖23份源码/契约/测试/固定输入原bytes，candidate UNCOMMITTED，非commit或授权凭证；15份既有核心/后端/固定输入原bytes匹配历史绑定。旧behavior.feature在develop检出为CRLF，LF内容对应旧hash；本轮绑定当前工作树raw bytes，不冒称旧指纹仍匹配，也不规范化输入来补绿。当前指纹：5ccaea17f46a43cc23eb01671f998ca86e9542453c1f2bd41d01b9c578310df5。

## 延期与恢复

T-007a仅文件接入VERIFIED_OFFLINE_SOFTWARE。actual文件入口、真实来源/脱敏/批准与independent_review链、采样及target接受继续DEFERRED/NOT_RUN；Agent_simulated不得改名替代actual审阅。#161跨版本A/B不满足same_target_replay，另需具体比较契约；其他targets不因本次接口完成而通过。

Linux/macOS原生入口仍DEFERRED_FS_CAPABILITY；本轮只证明Windows固定NTFS及既有fail-closed模型。无等价祖先rename保护不开放入口、不回退普通open。恢复以a96d759和固定输入为依据，停止使用错误软件/报告，保留本轮部分输出，修正后换新目录；不自动删除、覆盖、回写runtime或处置其他工作树。

结论：GO供Owner审阅本轮离线软件，不代表完整#582/target接受或Git发布授权。
