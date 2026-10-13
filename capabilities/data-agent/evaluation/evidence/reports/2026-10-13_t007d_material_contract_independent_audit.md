# T-007d 材料契约文档独立技术审阅

核验者：`/root/t007_independent_review`；模型/effort继承主线程，未覆盖。检查点：2026-10-13T11:18:22.609513+00:00。

结论：AC-D1–D7内容核验PASS，D8文档/静态命令部分PASS；最终原bytes闭合集合须在本报告产出后生成并在独立ignored检查点复核。当前没有未解决的内容缺口。此结论仅证明已批准的材料/门禁**文档**范围，不认证真实包、actual/runtime、target或Owner最终版本接受。

## 输入版本与方法

工作树 `D:/workspace/10-software-project/projects/mj-agent/documentation/582-t007c-post-merge`，branch `documentation/582-t007c-post-merge`，基线C1 `d7a612b5b166cd06e9da2139894b4b08da6af03c`；C2未stage/commit，未来PR/CI没有预填。已读取root及capabilities/AGENTS，按mj-agent-doc-review/doc-validate执行静态文档核验。

Owner本轮“执行推荐，继续推进”采纳A：原13/fp817接受、具名docs正常提交/现有App仅GitHub普通PR/develop/CI及T007d仅文档定稿。当前C1真实commit/tree/配置作者已核，14份提交tree bytes与原stage记录及原接受13一致；App固定CLI的head/branch/daily与成功回执/撤销CONFIRMED匹配。没有独立在线重取GitHub：此前MCP Bad credentials拒绝保留，不重试/换路线；平台字段只审主线程原捕获。

只用静态源文件、Git对象、标准库JSON/AST和既有synthetic原bytes核关联；没有导入agent/config/prompts/skills loader或evaluation模块，没有调用replay/judge/新API，没有完整pytest重跑、采样、引用打开、秘密/业务/外部服务读取。只写本公开审阅与assigned ignored独立JSON。

## 逐AC期望与实际

| AC | 独立期望 | 结论 | 真实依据/限制 |
|---|---|---|---|
| D1 | 五必填/两可选七位置、四manifest hashes、全部附属材料及明确无循环raw指纹 | PASS | GUIDE§1/§2（37–65）；schema21–39/183–242。alias非空唯一、禁NUL/CR/LF，提供项按Unicode码点排序alias+NUL+rawsha+LF/UTF8/SHA256；缺省b''不伪造文件，外层同时绑定集合与索引原bytes。 |
| D2 | 22完整分母、首SQL/全部调用和失败、脱敏/数据边界，声明不证明完整 | PASS | GUIDE57–73；schema131–161/317–324，judges88–105/504–519。无rows/business_summary/PII/凭据/完整envelope，非SQL参数只附属材料，无法判断的文本/轨迹保留缺口。 |
| D3 | 采样commit的loader实际body、有序roster/Runtime、双LFjoin与UTF8摘要 | PASS | GUIDE75–81；agent25–37/69–81，prompts与skills loader22–33。两loader缓存frontmatter.load(...).content，parts顺序及精确字符串摘要一致；未导入runtime或用当前磁盘hash冒充历史运行。 |
| D4 | 原文件摘要与原case对象canonical分开；实际语义/5红线/前三非红线及绑定 | PASS | GUIDE83–89；schema37–39/272–333；judges52–74/334–353/419–427/512–516。原JSON对象而非pydantic补默认值，末尾单LF/UTF8；实际review.check_id含output.*及适用acceptable_any分支。 |
| D5 | Agent技术/Owner实质/软件不能证明的三界，无包不索取不存在材料 | PASS | GUIDE17–33/57–73/89/131。批准范围、最终文档接受、包用途、target接受分记；真实性/独立性不由字段/hash/方法标签证明，常规合成与命令由Agent承担。 |
| D6 | 严格窗口inclusive、完整分母/key/same_target/0.03/红线、完整保护不降级 | PASS | GUIDE91–106；judges188–258；report21–32/35–113/120–155；_file_io105–128/194–226/275–294。精确Fraction阈值>=3/100或red_drop>0；不新增保护实现、CI门禁或权限。 |
| D7 | 现API dict分类与文件CLI退出分开，D01–08固定synthetic分类及延期 | PASS | GUIDE108–131；inspection44–89；inspection_runner37–85；现Python/CLI契约。help0、合法仅检查3/单JSON、非法2无输出，close/write2可留部分；actual与非Windows保护不足不解锁。 |
| D8 | 实际文档/元数据/三INDEX/原输出与保护；后续最终raw闭集独立核 | PASS静态与原命令；最终绑定待外层核 | Plan§8.12、9处当前文档/三INDEX、新GUIDE和验证/执行载体均已读；7个最终命令原size/SHA/exit验证。独立报告先产出，最终binding后生成并只在ignored检查点核，C2/平台/最终Owner接受未预填。 |

D1初版只要求“固定算法”而未给算法，执行Agent已补齐GUIDE§2具体排序/分隔/空值与外层索引绑定；本检查点对修正后的真实文件核验，不降低AC。M-01–07均是材料侧文档，closed schema不接受新增环境/body/非SQL参数或批准容器，GUIDE类型正确，不是新的工具/跨服务/MCP机器CONTRACT或ADR。

## 固定synthetic与必要审阅的静态核验

原fixture为22 case/22观测/34 review。对解析的**原case观测对象**按schema37–39的canonical方法独立重算，34个case_observation_sha256全部匹配；run/config/reference原hash和judge_profile/revision也匹配，既有agent_simulated角色链保留。对真实dataset与judges中的ID/分支静态对照：24个直接output语义记录、2个声明的acceptable_any.clarifying_question分支、5个audit.red_line、3个audit.sample对应34提供项。非红线排序前三为EG-01/EG-02/EG-03；不缓存到GUIDE或选择容易通过项。

这只核固定记录的摘要/键关联，不执行judge、不认证语义或actual审阅覆盖。原独立inspection.expected.json明确VALID/CONSISTENT，同时source/target UNVERIFIED、coverage NOT_CHECKED、metrics null/baseline false；无review仍可CONSISTENT，不因上述34绑定升级coverage。D-02–08是文档预期分类，没有造actual包或把未执行的payload试验写成运行PASS。

## 主线程实际静态校验原输出复核

执行载体为[本轮原命令记录](2026-10-13_t007d_material_contract_execution.json)。逐项解码base64，原size/SHA及exit全部匹配；本核验没有重新运行命令。

| 命令类别 | 最终exit | 原size | 原SHA256 |
|---|---|---|---|
| diff --check | 0 | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| frontmatter：157 canonical | 0 | 58 | `865bc245cfdcce1e44f165b8308fc60c6c92c8648d669eeb003a463f625884d9` |
| archive/root A4 | 0 | 131 | `2b678ba532c119f2768788a64f9a8559ca9621501bd8dd57cbe72140a274c48a` |
| capability G1 strict | 0 | 224 | `313627934d4d2e42af725dac34065650705d653f9a70bb5ad5d371955d7a3142` |
| trace G2 strict | 0 | 227 | `77373f101ff2594042590cdadb87bdb54ca865dc56168022a15aeb0b5ee6fc8f` |
| contracts G3 strict（具名绝对路径） | 0 | 271 | `98f6acb5cb962a2db77176f0e6f98d00bab4492b7438f110cb4040f8a6487139` |
| INDEX G9 strict | 0 | 123 | `aab3ec3b620285b2ffe475c34d50d541c4289d3e6911022e18eb9824b0746e42` |

G3首次相对capability路径触发现有relative_to ValueError：exit1、1440bytes、SHA`886ae906325fc0c58663a6b020111fe8444188426102bf4edda803f1a6cead47`，原错误载体保留；同一具名目录用正常绝对路径参数后1P/0W/0F。checker/contracts/guard原bytes保持，参数调用修正不是MCP认证路线重试或改门禁。

GUIDE v0.1/draft/shared与七基础元数据完整，三INDEX同步；package draft/0.8、6REQ及trace/机器contracts不改。A6已核现有root入口仍准确，无AGENTS变更；A7–A11/A12–A14无runtime或原生资产变更，适用项SKIP。7项校验通过不等于actual/native保护运行证据。最终新增报告/绑定的相对链接与集合raw完整性由外层待完成，不预填整个D8闭合通过。

## 输入原bytes摘要

下列是不包含本报告或未来最终binding的输入子集。size/SHA均是读取时原bytes；21份源码/合同/trace/守卫及8份固定fixture同时与C1 Git blob逐字节一致。本文不写自身hash或包含自身的候选fingerprint，避免循环；外层绑定另核。

| 输入路径 | 原size | 原SHA256 |
|---|---|---|
| `docs/guide/[GUIDE]_Offline_EVAL_Actual_Material_Contract.md` | 16439 | `3c6c4e44a685591b657851e43519d6ecab06641f8526751cb04f8fd371b481f4` |
| `capabilities/INDEX.md` | 7617 | `9305f42ab996c4e516b7f0beb59bb07755a1cf00fb3e6bad98ac8c20e7b52fb8` |
| `capabilities/data-agent/evaluation/design.md` | 44159 | `e6a932d22a261ba76146712615d94febe2d41505f9efb54309f3b00e71b336fe` |
| `capabilities/data-agent/evaluation/requirements.md` | 10297 | `5a11b250708f03a91e46534cbf0cfe5bef04c52c6e693a3f1266db346f97ce1a` |
| `capabilities/data-agent/evaluation/runbook.md` | 15841 | `1626db1ebec244106d42e7993028d188c5b44abb2a95b1183148c4d8dcecf5c8` |
| `capabilities/data-agent/evaluation/spec.yml` | 4457 | `ddc7a0b4775e5b4795e5928c6317ac37417212b9ff34b6f3d1a4793059066fa7` |
| `capabilities/data-agent/evaluation/tasks.md` | 13463 | `e5c53c655452f97f1efbe787b77d6393285e1f73741a8f4ef251c0dbfa5f3927` |
| `docs/INDEX.md` | 40667 | `4a8a7363219545d10acd2be52ddfd2feb0bcb8bc7ce157e760dc84f035cde134` |
| `docs/guide/INDEX.md` | 1801 | `78e1176d6d51071cc5b26ae6b8b61812fef133c80fa8ab7f96c15d047f18a76c` |
| `plans/[PLAN]_582_offline_eval_runner.md` | 51948 | `4d0e588a748e57f844b05d0f7c0e16a93cbda8fbc241df61c6bfcd1e7da9954b` |
| `src/mj_agent/evaluation/schema.py` | 10669 | `ebe2dd6c21864d9737d6ae9ba695d37fe232fd7cc97e16e58871e0099d42e86c` |
| `src/mj_agent/evaluation/inspection.py` | 4222 | `f2cb8a6f169dc7e68df16c068581c75e34cc233e2d471d397d504f1cd0b3cfcb` |
| `src/mj_agent/evaluation/inspection_runner.py` | 3888 | `8d0fc1634d2b1abafd1c4f72d321106a8e586eb679c0c47bd673f56a824c107a` |
| `src/mj_agent/evaluation/_file_io.py` | 13194 | `23d144901d28c13b639f7ca63d03ae8f31a6946932269cd59eab9e63c3bafc06` |
| `src/mj_agent/evaluation/core.py` | 1412 | `885153b06e4174c4d772414fbaa7c62fb7a004d7eebebaa0d1570913e9985110` |
| `src/mj_agent/evaluation/runner.py` | 4250 | `35d392e12fd64b6fe9b84002c76052ce53424e12d14c6560997ccf609adef002` |
| `src/mj_agent/evaluation/judges.py` | 25945 | `9b92a1e293b4cb62b181242f31c153f1ab48d4814f8108723bbe1417d85b2288` |
| `src/mj_agent/evaluation/report.py` | 12351 | `fa8f1b310f700d1e773399e8cf6d6d596393392cabd1260909c207a4b9380174` |
| `src/mj_agent/agent.py` | 3894 | `82ce89456723e0a0c66b430b4537adaa1a1ec5189569ab9a5407d17fea92598d` |
| `src/mj_agent/prompts/__init__.py` | 1469 | `d7405b06f3b1f0c6a802da07cb5900f1ba4aa769f4b0af25d9c219929868dcac` |
| `src/mj_agent/skills/__init__.py` | 1470 | `c85eddd81939ca8b12f5f2c2b07bfb4b22adcac1382444b2f86044f43bd86432` |
| `capabilities/data-agent/evaluation/contracts/python.contract.yml` | 7585 | `85c11da53f2def1fc476a9c4f91b39abf2608dfd8accc324923db34303c2dbde` |
| `capabilities/data-agent/evaluation/contracts/cli.contract.yml` | 2064 | `3d06e9e1a1c16ed298b361c5de9039368aaa1b7cf2631c480d075e85bf4ba622` |
| `capabilities/data-agent/evaluation/contracts/inspection-cli.contract.yml` | 2229 | `066cdefeb2bcd4081e3a4b96e44c5d945947cd9070a0e9ca87421b965e1d2b05` |
| `capabilities/data-agent/evaluation/contracts/behavior.feature` | 6829 | `7cf174208752e7ac0ff9b8c2efc37377618430eab0738e08eaad9d38b7c0bbad` |
| `capabilities/data-agent/evaluation/trace.yml` | 8337 | `460c189148002590e301ac7383d04a38c8ab3626f36e1e48427fc1fa579d19e6` |
| `scripts/sdd/run_offline_pytest.py` | 53302 | `01d318939b15d60bc7e15a4de6ee0d643c6230bc0357b647599d839124b1d1eb` |
| `scripts/sdd/check_contracts.py` | 5854 | `d374d73ddccb51641c6e42e7ec2a1adb668d796caf9371c408fc5f3785cb26bc` |
| `scripts/sdd/delivery_evidence.py` | 32200 | `ee851a8a6f8ae5359b2022cb0b9cefb667347f9210b643a2a73aa976c4a31c37` |
| `scripts/sdd/delivery_executor.py` | 51203 | `a22ba4d5d56bec8b18a172ca5e25f26043baab9518af485b36cc728fcfccd8ee` |
| `.gitattributes` | 1839 | `1dccaf0734812c00570ef7241ac63393287bc431409439ea496e7d06d90e1c02` |
| `tests/unit/fixtures/eval_core/config.json` | 398 | `f0e5991fa9ab05615122727288af5a149c1e75275490cf6f483ec94f5f8cd052` |
| `tests/unit/fixtures/eval_core/dataset.jsonl` | 7872 | `6f6d8fb3a288a575a5e5db336b8429ad8d795955ae5929ec8e1e89b642df9079` |
| `tests/unit/fixtures/eval_core/observations.jsonl` | 9173 | `fdd1f5f66144109d50f13dd5fd3eb6c119d86f43bf5ffeac2649b5a2bf82118a` |
| `tests/unit/fixtures/eval_core/manifest.json` | 1534 | `55af4d887a7bb722c46119301984e61faa23529cea74b2e3672443b85a0a861c` |
| `tests/unit/fixtures/eval_core/reference.json` | 1335 | `57fbbddfd7f659e0ef198617a6317145ca7123e2286d56e438c1516ded5e041f` |
| `tests/unit/fixtures/eval_core/reviews.jsonl` | 24324 | `18041c8230c197261562e2e014e2cac5fe05e652f9385d193d9a8a5f0e9a371d` |
| `tests/unit/fixtures/eval_core/inspection.expected.json` | 666 | `e5e4181f78b4efc8595dbabaeead7e22cc8c65d4d864e87a59b368f91662ecda` |
| `tests/unit/fixtures/eval_cli/baseline.synthetic.json` | 31019 | `7c5047a7520ba216aef1d31dd2dcc742718baee2d1c7d1fb93aa863db501e999` |

## 保留与停止条件

无获批真实包，不再索取不存在材料；来源/脱敏/批准有效性、完整性真实性、真实独立审阅、target/runtime及Linux/macOS等价原生保护继续延期。Owner范围已批，最终文档版本接受、未来包/入口/实际回放授权均另记。严格窗口/22完整分母/same_target_replay/精确0.03/红线与数据/来源边界保持；#161/#504/#583–#586/probe-fixture原scope不动。

C1原13/历史45/47/49/57和合并版891的358P/36warnings/12.44s载体保留，当前不会将其写成C2新head运行结果。原feature及97备份不清理，Gitee延期；不merge/delete/改权限，不改API/schema/core/judges/report/_file_io/runtime/CI/guard或实现新的认证/入口。#582 OPEN、Plan active、capability idea/last_verified=null。实际技术拒绝保留原错并只停受影响步骤，不能改工具/凭据/权限绕过。

后续先生成不含自身的最终raw绑定，独立ignored记录核闭合、再核实际C2提交及累计PR正文/当前head CI；本公开报告不预填这些结果。
