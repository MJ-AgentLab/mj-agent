# #582 T-007b 纯内存来源检查软件验收

本轮状态VERIFIED_OFFLINE_SOFTWARE，供Owner最终接受；candidate UNCOMMITTED。2026-10-12 Owner“执行待办推荐事项”采纳集中确认A，独立授权纯内存inspect_source API、必要离线测试、正式契约/文档同步及Agent合成验收；不借用T-006或T-007a授权扩大范围。实施者Codex，同Agent模拟Domain/Prompt并在独立SWE轮核验，Subagent dispatched=NONE，不要求真人参与合成验收。

工作树feature/582-baseline-cli，基线a96d759c080f4568e6810084f90fadce7b2c75cf，沿用既有G1工作树。本轮新增接口只使用既有schema._load，core/schema/judges/report/main/_file_io及窗口/阈值/compatibility规则原bytes保持T-007a状态；runtime、CI、守卫、个人配置、依赖与其他capability未改。无actual/live、采样、外部连接、提交、推送、PR、评论或Issue关闭；远端状态未联网重验。#582/Plan/capability保持OPEN/active/idea，last_verified=null；#161/#504/#583–#586原scope/状态及probe-fixture不适用结论保留。

## 本地验证

| 检查 | 新运行结果及实际覆盖 |
|---|---|
| Hardened pytest | exit0，108 core/inspection unit +156 CLI unit +14 BDD =278 passed，28条第三方gherkin DeprecationWarning保留 |
| 全仓Ruff | exit0；仅新增模块import排序曾触发I001，定点修复后通过 |
| 全src mypy Windows / Linux模型 | 各exit0，56 source files；Linux模型不是原生文件入口验证 |
| G1 schema / G2 trace / G3 contract | 各exit0，1P/0W/0F |
| G19 scenario trace / G21 acceptance | 各exit0，14P/0W/0F；读取本轮BDD事实，不替代进程证据 |
| G22 unautomated | exit0，0P/0W/0F；14场景均automated |
| G9 INDEX --check --strict | exit0，1P/0W/0F，7 specs，无需重生成 |
| V1默认Python契约 | exit0，13P/14W/0F；新增public_invariants信息WARN保留，不冒称strict零WARN |
| frontmatter / wikilinks | 各exit0，151 canonical docs合法，13份archive与5份root入口0问题；package/Plan相对链接另做具名补充检查 |
| 具名补充核验 | exit0，18修改+14新增文件均在授权范围；46文件raw binding、194本地链接0缺失、38快照文件通过；18项T-007a绑定保持、历史证据不变、无暂存、HEAD未变 |
| git diff --check | 独立exit0；Git将来转换换行的提示保留，不修改输入或Git配置 |
| 5个独立进程合成核验 | 每个验收进程exit0；API返回分类3；normal/baseline/permuted结果hash一致，missing正确列缺口，fictional引用仍UNVERIFIED；禁止访问0次 |
| actual/live、来源真实性、target接受、Linux/macOS原生文件入口 | NOT_RUN/DEFERRED；批准、结构检查、类型模型均不替代运行证据 |

当前测试复用develop已有.venv解释器，无安装/同步依赖或新venv。每个测试进程绑定当前工作树src，白名单环境、不携凭据；不使用local配置或secret值。复现入口（已有离线环境）：

    uv run --frozen --no-sync python scripts/sdd/run_offline_pytest.py tests/unit/test_eval_core.py tests/unit/test_eval_runner.py tests/bdd/data_agent/evaluation/test_evaluation_bdd.py -q --tb=short

[原始pytest记录](../bdd/2026-10-12_source_inspection_pytest.txt)、[14场景BDD记录](../bdd/2026-10-12_source_inspection_scenarios_pass.md)。44项新增unit与3项新BDD覆盖本项；原231项全部保留通过。内存win32/linux/darwin三个平台模型只验证API不依赖原生后端。TDD初始41 FAIL/64 deselected，因为模块缺失；新增模块后38P/3F，三项期望需遵循既有Pydantic包装为INVALID_INPUT_SCHEMA，仅修测试。首次参数自动ID包含大字节串，诊断过长且结果为39F/4E，改为固定短ID后得到有效RED；未改变runner或绕过拒绝。首轮275PASS后补3个平台模型，最终278PASS。辅助搜索曾误指两个不存在的BDD脚本；定位实际check_bdd_scenario_trace/check_bdd_acceptance后正常运行，未修改checker。

## API、输出和契约差异

公开签名为inspect_source(inputs: ReplayInputs) -> dict[str, Any]，位于src/mj_agent/evaluation/inspection.py，正式Python契约新增第四个module/export及invariants/non_actions。ReplayInputs/replay/main和CLI契约不改；无新增CLI参数或进程入口。输出为offline-source-inspection-v1，和offline-report-v1不同，不能互当runtime baseline。

- input_status VALID/INVALID仅代表既有schema、身份、hash及资源限额；coherence_status CONSISTENT/INCOMPLETE/NOT_CHECKED只代表提供记录的结构完整性。
- counts为planned_cases/observed_cases/complete_observations/provided_reviews/bound_reviews；gaps列缺观测ID、三complete标志/unknown调用/SQL为null及提供review绑定诊断，按稳定顺序输出。结构非法时counts/gaps/source_kind均null。
- 提供review仅检查run/obs/config/reference/profile/revision关联和原来源方法/合成链字段；不判断check适用性、必要审阅覆盖或语义verdict。无review也可CONSISTENT，review_coverage_status始终NOT_CHECKED。
- source_evidence_status及target_evidence_status始终UNVERIFIED；sampling_approval_ref、independent_review标签或目标hash不构成有效授权、脱敏/来源真实性或实际装配证明。
- runtime_metrics=null、baseline_eligible=false；exit_code是返回数据：2非法、3仅检查，绝非新增CLI成功退出码。无measurement/cases/compatibility_key/Markdown，不解析引用、执行SQL或调用replay/judge。
- 不回显SQL、reply、来源路径/引用或原始异常，不加入当前时间/随机ID，相同bytes确定性一致、输入不变。固定期望inspection.expected.json在实现前独立写定，未用待测代码生成。

详细映射见[design](../../design.md)、[Python契约](../../contracts/python.contract.yml)、[RUNBOOK](../../runbook.md)和[Plan](../../../../../plans/[PLAN]_582_offline_eval_runner.md)。requirements/spec/tasks/trace/行为契约、fixture README、CHANGELOG及两处已有INDEX同步；四份package文档version0.7/state=draft，SPEC idea/null、Plan active保持。ADR/GUIDE/STANDARD无需新增，既有CLI/生产或其他target契约无需扩展。

## Agent合成验收与来源边界

Domain轮从原22-case/5红线集合、完整观测与严格0.03/same_target_replay规则整理期望；Prompt轮核对34条synthetic关联/方法/双引用及目标声明，不证明真人审核或真实性。SWE独立从原bytes重算四份manifest hash和34条run/obs/config/reference/profile/revision关联，再运行5个新进程验证API，不从API输出生成期望。

[角色事实](2026-10-12_source_inspection_role_facts.json)记录5进程、零禁止访问、输入hash及复查数量；[验收脚本原bytes快照](2026-10-12_source_inspection_verifier.txt)可复制回.mj-agent-local/t007b/acceptance.py后以既有Python运行复现。原始inputs在加载后，调用期间builtins/io/os/Path文件操作、socket/subprocess audit全部拒绝；从新进程加载接口时meta-path拒绝应用/core/judges/report/_file_io/客户端导入，并检查没有相应模块。五个验收进程的exit0只表示软件断言完成，API分类始终3；未执行EVAL进程。

fictional分支只在内存中替换明确虚构的来源/批准/脱敏/target声明和方法标签，检验它们无法提升UNVERIFIED；未生成或接受actual观测包，亦未把34条synthetic记录当作actual审阅。缺观测结构允许整理但不得宣称真实target或完整审阅接受。当前Owner确认没有获批脱敏包。

后续actual需真实22-case完整调用结果/首次SQL/全部失败、采样与脱敏批准引用、真实loader body/active roster顺序/Runtime段与最终装配hash、全部必要语义及5红线+3非红线审阅。旧walkthrough仅5场景/截断Markdown且加载dotenv，不导入或执行；无法当作完整包。实际文件入口与target接受待材料和另批范围，Linux/macOS须等价原生保护证明，缺能力继续fail closed。#161跨版本A/B不冒充same_target_replay；其他target窗口/阈值/原scope保持。

## AI自检与恢复

范围对照Plan §8.9与SPEC §2.6：只新增本项模块和具名测试/证据、更新已批准文档；原T-007a变更保留。API仅导入typing及既有schema，没有配置、采样、服务或judge依赖。固定input/schema/核心与backend字节核对未变；不存在rename/move/delete、SQL重命名或runtime body改动，5a反扫未要求更新runtime入口。新接口仅更新evaluation现有索引，不触发根AGENTS内容扩写；CHANGELOG为Unreleased不意味着发布。

12项自检：模块边界/合成数据边界/无秘密与调试/文档同步/范围与双段/CHANGELOG/引用通过；commit message及PR字段在本轮无提交/PR对象，SKIP；runtime prompt bump不涉及。实际来源/外部catalog镜像未验证，保持未测；此结论只支持软件结果审阅，不触发Git发布。

T-007a实施前23文件fingerprint 5ccaea17f46a43cc23eb01671f998ca86e9542453c1f2bd41d01b9c578310df5已逐项匹配，38文件及tracked.patch保存在.mj-agent-local/t007b/t007a-snapshot；历史T-007a报告/绑定未覆盖。新binding由[本轮原bytes绑定](2026-10-12_source_inspection_binding.json)记录，排除自引用的本binding及本验收Markdown。恢复时先保留当前候选并核对快照，不自动删除或覆盖工作树/历史输出；本轮无不可逆变更。

补充检查脚本首次沿用T-007a的新旧证据名/事实schema和README允许变更清单，核对失败后修正自身映射，没有修改交付代码或守卫。仓内原dataset以CRLF检出，直接与Git LF blob比较曾失败；当前raw hash 01703f365dec13b091f00070ffafdcd93a4a8c269089fce8ab2483f4570b58a3与develop和历史锚点一致，catalog raw hash 29f93fd5362884c84745f965b8863c8d964fa6fceae7fcae437b28304810342e同样一致。分别核对历史原bytes hash及Git规范内容后通过，没有归一化输入；新46文件绑定均保存原bytes，fingerprint为0e4d630cd1401b0411a668da609987de08147c00a1423ce6d46cf213deb80212。
