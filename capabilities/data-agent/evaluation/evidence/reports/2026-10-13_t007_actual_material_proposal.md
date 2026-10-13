# T-007剩余范围：真实观测包材料契约与门禁提案

状态：方案草案，供Owner作下一范围决定。#599已集成T-007c，但没有获批真实观测包；本提案不生成包、不采样、不执行actual/live，不新增API/CLI/schema，不提升来源或target状态。建议T-007d先仅定稿文档中的材料/责任/门禁，actual文件入口另批并延期。

## 1. 当前代码与材料之间的差异

- 既有ReplayInputs为config/dataset/observations/manifest/reference五份必填bytes，reviews/baseline缺省b''。manifest.hashes只绑定config/dataset/observations/reference四份；reviews、baseline及manifest原bytes应在外部材料索引独立绑定，不把四项hash称作七输入绑定，也不让manifest自hash循环。
- manifest.provenance已有source_ref、sampled_at、sanitization_version、sanitization_review_ref、sampling_approval_ref；actual标签仅要求批准引用存在，不能认证引用、采样或授权有效。
- target_snapshot.skills是有序list，已有component与assembled_prompt_sha256，可核声明名单顺序/摘要。实际_ACTIVE_SKILLS及loader输出body/Runtime段/最终装配正文仍需附属材料证明关联；有序声明也不能证明运行时确实使用该名单。
- _Call仅接受sequence/call_id/tool_name/sql/outcome/error_codes。非SQL工具参数、采样环境、loader正文与审阅链不属于现有闭合schema；它们放在独立、已脱敏材料侧，不塞新字段。
- inspect_source不访问引用、不调用replay/judge；无review也可CONSISTENT，review coverage仍NOT_CHECKED。两个Windows文件CLI仍synthetic-only；actual早拒绝2/ACTUAL_ENTRY_DEFERRED，Linux/macOS缺保护2/FS_CAPABILITY_UNAVAILABLE。新提案不改变这些事实。

## 2. 最小材料与职责

以下为拟定文档契约的最小索引，当前没有对应实际文件。索引描述alias、size、原SHA256及关联，不能用approval=true、URI存在或hash匹配当批准凭证。

| 材料 | Agent技术核验 | Owner的必要实质决定/软件证明限度 |
|---|---|---|
| 采样环境、run/commit、模型/有效sampling/time_basis | 与manifest身份一致，非秘密环境标识、版本及引用齐全 | Owner批准采样/用途/数据范围；软件不能证明运行发生于所称环境 |
| 七份输入原bytes索引 | 四manifest hashes及全部原bytes size/SHA；reviews逐case规范化观测摘要另核，不与整文件raw hash混同 | 引用本身不认证来源；baseline存在也不代表有效或可比较 |
| 完整有序调用与失败轨迹 | 22-case完整分母、唯一call_id/连续sequence、全部状态/错误、首次SQL不被最终SQL覆盖；未知/缺记录保留缺口 | 软件不能证明上游没有遗漏调用；零调用必须有真实完整性依据 |
| 脱敏及数据边界审阅 | 无rows/business_summary/PII/凭据容器、非白名单envelope；只处理获准非敏感材料 | 有限schema/scanner不能证明自由文本无敏感内容，Owner决定审阅来源与包版本可用范围 |
| loader/roster/装配材料 | 对提供body与Runtime段按明确算法重算，逐项比对有序名单与最终摘要，不导入runtime/config或读引用目标 | 声明body/hash不证明实际cache/装配，真实来源与target采样绑定仍须可靠材料 |
| 独立语义/红线审阅 | run/case/check及规范观测/config/reference/judge绑定；全部必要语义项、5红线与按case ID选至少3条非红线审计 | 独立Agent可承担真实技术审阅，但必须实际审获批观测与参考；不能把agent_simulated旧标签改名为independent_review。真实性/独立性不由方法字符串证明 |
| 包级用途批准与target绑定 | 精确包指纹、目标/EVAL范围、条件、时效、review版本引用相符；保留批准/集成/验证/接受分别记录 | Owner决定该真实版本的用途与最终target接受；软件不能自行签发批准或把技术通过等同接受 |

业务行数据、business_summary、PII或凭据不进入输入/附属材料。真实来源材料未就绪时不构造actual包、不要求Owner补不存在材料；Agent负责后续技术整理，Owner不代做常规命令/转换/合成验收。

## 3. 推荐顺序与现有接口

1. 先把本表、原bytes索引/角色责任及拒绝清单定稿为文档；保持所有当前合同/API/CLI/退出码，文档范例明确synthetic或不可执行占位，不制作actual manifest/观测样本。
2. 用现有固定synthetic bytes和inspect_source(inputs)说明结构/关联层能核什么；API仍返回结构字典，VALID/INVALID与CONSISTENT/INCOMPLETE/NOT_CHECKED仅描述结构/关联，UNVERIFIED/NOT_CHECKED/null/false保持。文件CLI仍按现契约返回2/3；技术过程不访问引用或装配目标、不调用replay/judge来认证来源。
3. 独立Agent从AC审真实文档/原代码/固定expecteds，核差异与缺口，不要求真人参与常规合成核验；此阶段不计actual/runtime通过。
4. 当真实材料和Owner用途决定实际具备时，再提出Windows actual文件入口的具体新G1实施方案。入口授权不能从T-007a/b/c或本文继承；Linux/macOS必须另具等价保护，否则继续延期。

拟议文档阶段没有新进程入口或退出码。若引用现有CLI，仅使用现有--synthetic-fixture与显式五输入、可选reviews/baseline及新output-dir；原bytes/保护/拒绝顺序保持。不新增--actual、--approved、--trust-source或跳过审阅/保护的开关。

## 4. 未来actual入口的必要门禁（仅设计，不实施）

前置顺序应为：任务/目标/环境授权 → 包级真实用途决定与精确raw版本 → 来源/脱敏/完整轨迹和真实独立审阅关联 → target/严格窗口/兼容条件 → Windows等价完整文件保护 → 才可另批actual回放与基线比较。材料缺失、批准版本不匹配、真实性不可判、保护不具备时延期对应步骤，不以声明字段、固定标签、合成包或技术绿灯解锁。

same_target_replay保持同commit/target/model/sampling/time/source兼容、完整分母、0.03阈值及红线。baseline读取不等于比较成功，全部尝试/首SQL/失败轨迹与必要审阅不能被省略。#161跨版本A/B、#504/#583–#586及probe-fixture原scope保留。

文件保护至少完整复用当前Windows fixed NTFS根/全部祖先句柄、相对逐组件打开、reparse/卷/最终路径/单链接/前后身份/大小限额及独占新目录。所有显式文件一致保护；禁止目录扫描、网络路径、秘密路径、引用递归、普通open回退。读写/close失败与部分输出保留、不覆盖/删除、不承诺原子/fsync的限制不降低。本阶段不修改或声称实现该未来入口。

## 5. 固定合成正反例与验收

| 范例/核验 | 固定期望与界限 |
|---|---|
| 既有22-case/34-review synthetic输入 | 原inspection.expected不由待测代码生成；API为VALID/CONSISTENT，文件CLI退出3，但来源/target仍UNVERIFIED |
| 虚构来源/批准/target引用 | 不能升级来源、审阅覆盖或批准，引用不访问 |
| 在manifest塞environment/loader body，或_Call塞其他工具参数 | 当前闭合schema仍拒绝；附属材料不能成为绕过extra-forbid的载荷 |
| raw字节改动或review规范观测/config/reference绑定不匹配 | 技术不一致可检出，不归一化输入补hash，不代替真实性判断 |
| 声明完整却缺首次失败/调用/语义审阅 | 保留缺口；schema中的complete声明、CONSISTENT或零调用本身不是实际完整性/覆盖证明 |
| roster重排/assembled hash或body不一致 | 核声明顺序和提供body重算；即便一致仍不能认证实际loader运行 |
| 新目录碰撞、secret/UNC/越界/hardlink/reparse、close故障 | 复用现有固定负例与诊断，拒绝/部分输出保持，不改保护后端或删除输出 |
| actual标签与Linux/macOS入口 | 现有早拒绝继续，不生成actual通过证据；模型/类型检查不算原生成功 |

文档阶段必要检查为实际符号/字段逐项对照、明确raw与规范摘要、引用/格式/INDEX闭合、独立Agent从AC审阅，以及相关既有离线核验。没有新增实现时不声称运行新API或为文档另造实现镜像测试。未来获批实现才按新G1做固定正反例RED/GREEN及新raw绑定。

完成标准：材料、缺口、角色责任、门禁与现契约差异可逐项核查；独立审阅通过；所有真实来源/授权/target/runtime未验证项诚实保留；Owner只需确认新文档契约范围。延期条件：无获批包（当前事实）、独立真实审阅未形成、target未绑定、平台保护不足、任务授权缺失或实际技术拒绝。保持#582 OPEN、Plan active、idea/last_verified=null，不关闭T-007。

## 6. 待Owner集中确认

- A（推荐）：只将T-007d限定为材料契约与actual门禁的文档定稿，采纳上述最小材料/责任边界；API/CLI/schema、actual入口、采样、live、权限及删除不在范围。无真实包也能完成具体材料规范，避免把软件结构检查升级成实质批准。
- B：保留本提案，T-007d整体延期；当前仅完成T-007c集成文档收尾。

本提案不是新入口或新的实质契约范围授权；当前文档G1候选的提交/发布范围与后续材料契约定稿分别由Owner决定。参见[合并后核验](2026-10-13_source_inspection_cli_post_merge.md)与[Plan当前检查点](../../../../../plans/[PLAN]_582_offline_eval_runner.md)。
