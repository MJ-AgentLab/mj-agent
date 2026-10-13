# #582 T-007c synthetic来源检查CLI本地候选

> 当前状态：OWNER_ACCEPTED_OFFLINE_SOFTWARE。Owner于2026-10-13回复“接受”，接受本轮T-007c本地软件候选及已核验原bytes版本。以下交付时点的OWNER_ACCEPTANCE_PENDING等记录保留历史；当前接受范围见文末。整个#582/T-007与actual/runtime/target接受及Linux/macOS原生保护仍延期。

2026-10-13 Owner采纳A，授权新G1工作树、独立CLI、契约/文档、固定离线测试、独立Agent合成验收与原bytes绑定，交付本地候选供接受。基线fd045520c0123627e53d23c0ad58bf97a6b3552e，feature/582-source-inspection-cli，candidate UNCOMMITTED。执行Codex；独立核验/root/t007_independent_review。Owner最终接受尚未记录。

唯一新增源码inspection_runner.py，公开main(argv=None, *, repo_root=None)。现有ReplayInputs/replay/inspect_source/runner、core/schema/judges/report/_file_io及runtime不改。无actual/live、采样、外部连接、提交/推送/PR/评论/关闭Issue、删除、权限或个人配置变化。#582 OPEN、Plan active、capability idea/last_verified=null；其他target/probe-fixture原scope保持。

## 新鲜验证

| 检查 | 实际结果 |
|---|---|
| Hardened offline pytest | exit0，340 unit+18 BDD=358 passed，36条第三方gherkin DeprecationWarning保留，11.29s |
| 新unit子集 | exit0，76 passed，原156 CLI unit未在子集中运行 |
| Ruff全仓 | exit0，All checks passed |
| mypy Windows/Linux模型 | 各exit0，57source files；Linux模型不是原生成功 |
| G1/G2/G3/G9 | 各exit0，1P/0W/0F；G3相对capability参数曾ValueError，使用实际绝对路径后成功，未改checker |
| G19 / G22 | G19 exit0，18P/0W/0F；G22 exit0，0P/0W/0F |
| G21当前严格完整性 | exit0，0P/0W/0F；14历史DEFERRED、4新SELFTEST，不声称runtime PASS |
| V1默认 | exit0，14P/15W/0F，public_invariants等信息WARN保留 |
| frontmatter / wikilinks | 各exit0，154canonical docs合法；13archive/5root引用0问题；package/Plan另查 |
| BDD JUnit补充运行 | exit0，18 passed/36warnings，2.76s；原log/JUnit/hash及实际scenario-test-ID绑定 |
| 独立Agent合成核验 | 14种真实新进程PASS_SYNTHETIC_SOFTWARE；另hardened故障/保护子集17PASS；18受保护文件raw MATCH |
| actual/来源真实性/target接受/Linux或macOS原生成功 | NOT_RUN/DEFERRED，不计软件通过 |

原始pytest与18场景记录见[运行日志](../bdd/2026-10-13_source_inspection_cli_pytest.txt)、[BDD证据](../bdd/2026-10-13_source_inspection_cli_scenarios_pass.md)。

    uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit/test_eval_core.py tests/unit/test_eval_runner.py tests/bdd/data_agent/evaluation/test_evaluation_bdd.py -q --tb=short

复用develop既有.venv解释器，实际代码/子进程PYTHONPATH指向新G1工作树。没有安装/同步依赖、新venv、staging或配置变更。测试使用tmp_path及白名单进程环境，不依赖开发机具体工作树。

## RED/GREEN与实现边界

新增59项断言先观察模块缺失59FAIL/156deselected。最小包装器后57PASS/2FAIL：新测试误改os.name影响Path类型，实际得ABSOLUTE_ROOT_REQUIRED；修测试为sys.platform模型，不改后端。补原生属性/祖先锁/引用不读/限额负例后76PASS。组合首轮357PASS/1FAIL为新BDD误用helper名missing_observation，修为既有missing后358PASS。平台模型只证明拒绝，不冒充原生Linux/macOS成功。新增import排序I001由定点ruff修正。

五必填与可选reviews/baseline原bytes经既有后端进入ReplayInputs；可选缺省b''。synthetic开关必需，manifest先读，actual/未知来源2且无其余输入/inspector/输出。路径词法拒绝可更早；显式baseline空/非object分别BASELINE_INPUT_EMPTY/BASELINE_NOT_OBJECT，非法解析和API INVALID均先于输出创建返回2。

VALID的CONSISTENT/INCOMPLETE只写inspection.json，原offline-source-inspection-v1结构/固定状态保持，退出3；help0不读文件。不新增EVAL判定、语义/适用性/coverage检查、runtime metric或baseline资格。source/target UNVERIFIED、review coverage NOT_CHECKED、runtime_metrics=null、baseline_eligible=false不可提升。

文件保护完全复用原Windows fixed NTFS后端，root/祖先共享句柄/卷/最终路径/单链接/前后身份/限额与新目录exclusive保持。write/close故障2，安全附inspection_exit_code，部分新输出保留；无自动删除/覆盖、原子提交或fsync耐久性承诺。原32类judge、严格窗口、完整分母、same_target_replay、精确0.03及红线优先由原回归保持。

## 版本、文档与恢复

新Python module及独立inspection-cli契约、4新BDD、trace/requirements/design/tasks/spec/RUNBOOK、Plan、fixture README、CHANGELOG与两处INDEX同步；现有cli.contract.yml及纯内存API边界保留。历史T-007a/b UNCOMMITTED与报告不倒写。本轮G1前18份保护文件原bytes在本地固定，当前七份输入/原expected均不改。

先前T-007b历史46binding当前39raw匹配、5换行检出差异、2治理集成内容差异；旧指纹仅属历史，本轮新raw binding独立固定，不归一化输入。真实材料清单见RUNBOOK §4.4；其他工具参数摘要/环境/loader正文在附属脱敏材料绑定，现有schema不扩展，CLI不读取这些引用。

恢复：保留新工作树、输入/输出与证据，停止使用错误报告作接受依据；修正后新目录重试。不删除旧备份/历史证据或处置其他工作树。整个T-007、#582和target/runtime接受不随本子项通过。风险/决定为已批准新入口契约；方法A/red-green，委派独立Agent。实际矩阵、逐AC、scope与raw binding将在本轮完成时追加。

## 独立合成验收与AC结果

[独立原始角色事实](2026-10-13_source_inspection_cli_role_facts.json)、[子进程验收载体原bytes](2026-10-13_source_inspection_cli_verifier.txt)、[独立报告](2026-10-13_source_inspection_cli_independent_audit.md)。独立Agent先于代码从AC建立期望，读取真实源码/七输入/原fixed expected，再运行新进程及fault子集，不从程序结果生成预期。

| AC | 结果与证据边界 |
|---|---|
| AC-C1 | 签名/help/必需synthetic与未知参数固定断言通过；help不读文件 |
| AC-C2 | actual/unknown仅manifest read1、inspect/write0；缺模式read/inspect/write0，无输出 |
| AC-C3 | 原bytes缺省/传递与固定baseline验证；空/非object拒绝；不比较或认证 |
| AC-C4 | hash/schema/调用顺序/限额/禁字段负例2无目录，API INVALID同样前置拒绝 |
| AC-C5 | 正常/无review/缺HP01/虚构refs/负review/unknowncheck均3，缺口与完整分母保留，固定状态不升级 |
| AC-C6 | normal/repeat/baseline规范单JSONhash相同；新进程无core/judge/report/runner/app/client及秘密/网络/引用访问 |
| AC-C7 | 同原后端保护，独立17fault/close/collision/parent/属性/hardlink/平台拒绝模型通过；部分输出保留 |
| AC-C8 | protected18raw MATCH；旧固定输入/expected不变，新契约/trace/文档/原bytes闭合 |

Agent验收载体首轮预import新入口再runpy导致RuntimeWarning，修为只预装并监测inspection/_file_io；第二轮错误假设HP01有2条review，原bytes实际1条，独立expected bound33修正前32。两次只修验收载体/自身期望，原运行目录/日志保留，不改软件/门禁，最终14种新进程通过。原raw facts保留准确过程，不冒称真人或actual签署。

G21首次使用旧pass_rate格式得到18DEFERRED；读真实checker后用既有hardened --junitxml路线生成18-case原始JUnit和log/hash，新增4场景SELFTEST。旧排序首选历史14报告仍DEFERRED，不改旧记录/loader/门禁或将合成标成actual。绑定辅助第一次误将role-review连字符转下划线，JUnit真实ID为rolereview；改辅助映射以实际18ID校验，未造XML或改测试。

## AI自检与scope

Scope drift=None；风味A，已批准新入口/declared-contract-change。只新增包装器及独立契约/本轮证据，扩展既有已跟踪unit/BDD和具名文档；无新插件/依赖/CI/守卫/权限。受保护源码及runtime无diff，原cli.contract.yml不改。

12项自检：模块边界、纯synthetic输入/无秘密或调试、文档/分支/范围/双段/CHANGELOG与引用一致。Commit message与PR字段因无发布对象SKIP；runtime版本/EVAL backlog因未改runtime canonical SKIP。5a无rename/move/delete/SQL对象/正文迁移；5b新契约与evidence已形成；5c已有INDEX/CHANGELOG同步，AGENTS无需扩写；5d SPEC Delta=None（JSON单输出、拒绝顺序、诊断/限额/部分故障/未测/恢复均覆盖）。

文档A1–A3 PASS：Plan active/code、4package draft/0.8、idea/null保持，package不增加track；根CHANGELOG元数据豁免。A4全仓及具名相对链接分别核对；A5入口已同步；A6未改变高频runtime或全局规范；A7–A14无对应资产改动SKIP。OB1长度静态审阅，不新增硬阈值；OB2–5历史/当前、软件/actual接受、结构/真实性边界清楚。

本轮版本和原bytes见[绑定](2026-10-13_source_inspection_cli_binding.json)。它不是commit/SHA或授权凭证；排除本验收及binding自身，记录base/branch/候选和所有实际原bytes。软件VERIFIED_OFFLINE_SOFTWARE，本地交付OWNER_ACCEPTANCE_PENDING；本Plan继续active，整个T-007与capability接受未完成。

## 最终本地交付检查点

独立Agent最终复算45份原bytes size/SHA全部MATCH，指纹e5616a7bf29563ba6cb217b2f1ab976469de07167c1ddc9b9ca63e6922549aab；18份保护全匹配，log/JUnit/18场景及14进程事实一致。binding与本验收排除自引用正确。本轮15份修改+11份新文件、未stage；HEAD仍fd045520，scope=None、diff --check通过。95个具名本地链接0缺失，package draft/0.8、Plan active、idea/null元数据核验通过。全仓ruff最终再次exit0；Git将来转换换行的提示保留，不改Git配置。

develop最终仍fd045520，仅既有.playwright-mcp/未跟踪，tracked diff空；其他工作树/旧备份未动。本地候选软件交付完成，OWNER_ACCEPTANCE_PENDING；未执行actual/live或Git发布/删除/权限动作。此报告追加不改变已独立核验的45份绑定文件。

## 2026-10-13 Owner接受记录

Owner在本会话明确回复“接受”，接受T-007c Windows synthetic-only来源检查CLI本轮本地软件成果。接受版本为feature/582-source-inspection-cli，基线/HEAD fd045520c0123627e53d23c0ad58bf97a6b3552e，candidate UNCOMMITTED，原bytes指纹e5616a7bf29563ba6cb217b2f1ab976469de07167c1ddc9b9ca63e6922549aab。接受记录前再次核45份文件size/SHA全部匹配、未stage；软件验证与独立核验保持。本报告在binding明确排除集合内，接受记录不改变已核验的45份原bytes。

本子项状态OWNER_ACCEPTED_OFFLINE_SOFTWARE。此决定只接受T-007c本地软件，不扩展Git发布、删除、权限或actual/live授权；不表示已提交/推送/创建PR/集成。本轮不关闭#582或整个T-007，Plan active、capability idea/last_verified=null保持。真实观测包、来源/脱敏/批准及独立审阅真实性、target/runtime接受和Linux/macOS原生保护继续DEFERRED/UNVERIFIED；不以合成验收补造通过。

## 发布待办执行记录（当前）

Owner在接受本地软件并总结会话后回复“授权执行待办”。当前承接已接受T-007c的正常stage/commit、发布准备及CI核查；不包括actual/live、采样、删除、权限或既有保护面修改。具体发布路线不从工具权限推定。原“未stage/未提交”属于前述交付时点；本节按新授权记录真实操作。

C1已正常提交：5ffb15fa5f690551cd32e8579e47d61b457646e8，feat(eval): add synthetic-only source inspection CLI，精确4份源码/测试/README。实际Git author/committer为仓库原配置ranzuozhou；实施来源Codex。该Git元数据不是App平台作者，不伪造bot。C2将精确提交24份契约/文档/证据与原bytes属性，实际SHA提交后写入本地publication/outcome.json；此处不预填未来SHA。

发布准备初检再次核45原bytes全部匹配；后续发布保真补充记录唯一audit EOF变化及新index绑定，不倒写原接受记录。本轮新鲜相关测试358PASS/36既有第三方警告，12.12s。两个远端develop均fd045520且同名feature引用不存在，尚无该head的PR。core/schema/judges/report/_file_io/runtime与已接受版本不变。OPEN/active/idea/null保持。

受控新App当前daily audit真实exit0/EXECUTOR_VERIFIED，App5284037、installation170545174、repository1172583390；仅Metadata read、Contents/PR write，单仓短期token后台撤销CONFIRMED。模型未读vault/私钥/token或已有秘密。

独立Agent依据真实后台与既有闭环核验：正常本地Git提交与App平台作者分记；backend push仅GitHub origin，pr-create只能普通PR（没有Draft参数）。本轮常规Draft建议改为正常受支持普通PR，不改后台或权限。Gitee没有该后台路线，其他任务Q10例外不覆盖本分支，新的GitHub-only/镜像延期决定仍待Owner。当前未观察实际工具拒绝；路线未支持和例外待决定不冒称BLOCKED_EXECUTION_ROUTE。尚未push/创建PR/平台审核/merge。

发布保真补充：暂存时实测两个原Windows日志被text=auto转换CRLF→LF，导致stage hash与原execution hash不同。为两份本轮具名日志精确设置-text whitespace=cr-at-eol，为本轮verifier精确设置-text；不禁止diff或全局whitespace，不改输入/日志来补绿。按正常git add --renormalize刷新后，三个index blob与原bytes完全一致。独立Agent已复算，BDD log/JUnit与carrier原hash保持。仅清理新audit/本验收末尾空行，原audit接受时点raw另存本地；旧45 binding不改写。C2由原22份加.gitattributes及[publication binding](2026-10-13_source_inspection_cli_publication_binding.json)，共24份，总代码/文档28份；新发布绑定按47份真实index blob记录，指纹7ae23994362fccb02588a5accf8e18049d35f051d9a6a99b1448a298e0095454。Owner已接受的软件逻辑不变。
