---
type: guide
domain: SYS
summary: 定义离线 EVAL 真实观测包的最小材料、字节与审阅绑定、技术责任和延期门禁
tags: [guide, evaluation]
aliases: []
created: 2026-10-13
updated: 2026-10-13
state: draft
version: v0.1
track: shared
owner: ranzuozhou
---

# 离线 EVAL 真实观测包材料契约

> **适用范围**：#582 T-007d 仅材料与门禁文档定稿；当前没有获批真实观测包。
> **目标受众**：整理与独立核验材料的 Agent，以及作用途/版本决定的 Owner。
> **版本**：v0.1 候选；Owner 已批准范围，最终文档版本接受另记。
> **最后更新**：2026-10-13。
> **关联文档**：[Plan](../../plans/[PLAN]_582_offline_eval_runner.md) §8.12、[requirements](../../capabilities/data-agent/evaluation/requirements.md)、[RUNBOOK](../../capabilities/data-agent/evaluation/runbook.md)、[原提案](../../capabilities/data-agent/evaluation/evidence/reports/2026-10-13_t007_actual_material_proposal.md)。

## TL;DR

先核用途和材料版本，再由 Agent 整理脱敏材料及技术关联，独立 Agent 从实际材料复核。原 bytes、结构关联、真实来源、target 接受、回归结论分别记录；hash、引用、方法标签、Git 合并或合成测试不能互相代替。

本项仅文档。当前两文件 CLI 仍为 Windows fixed NTFS synthetic-only；actual/runtime_observation 入口、真实采样、实际基线比较、Linux/macOS 等价保护及 target/runtime 接受继续延期。无获批包时不制作 actual 示例，不重复要求 Owner 提供已明确不存在的材料。

## Prerequisites

Agent 记录任务、target、环境、允许动作、数据范围及停止条件。业务访问只允许既有工具链，本文不批准采样或业务连接。业务行数据、business_summary、PII、凭据与秘密不进入七输入或附属材料。

材料索引列是文档约定，不是新 manifest/JSON Schema、CLI 参数或软件批准容器。既有 [Python](../../capabilities/data-agent/evaluation/contracts/python.contract.yml)、[回放 CLI](../../capabilities/data-agent/evaluation/contracts/cli.contract.yml) 和 [来源检查 CLI](../../capabilities/data-agent/evaluation/contracts/inspection-cli.contract.yml) 契约保持。

## §1 现代码与材料约定的差异

| 对象 | 当前实际能力 | 材料侧约定 |
|---|---|---|
| ReplayInputs | 五必填 config/dataset/observations/manifest/reference bytes；reviews/baseline 默认 b'' | 覆盖七输入位置，声明可选项是否缺省，不误称七份必填文件 |
| manifest.hashes | 只绑定 config/dataset/observations/reference 原 bytes | manifest 自身、reviews、baseline 由外部索引独立绑定，不制造自 hash 循环 |
| provenance | source_ref、sampled_at、sanitization_version、sanitization_review_ref、sampling_approval_ref；actual 仅检查批准引用非空 | 真正来源/采样/脱敏/用途决定另核，字段不认证决定真实性 |
| target_snapshot | prompt component、有序 skills list、assembled_prompt_sha256；只检查声明 | 提供采样 commit 的 roster/loader body/Runtime 段/最终装配材料 |
| _Call | sequence/call_id/tool_name/sql/outcome/error_codes；非 execute_sql 不可带 sql | 其他获准且必要的工具参数只作独立脱敏附属材料，不塞未知字段或完整 envelope |
| review | run/case/check、规范观测摘要、config/reference 原 hash、judge、role/method/ref 等关联 | 真正独立审阅及全部必要项另核，字符串不证明独立性或真实性 |
| inspect_source | 纯内存 dict，结构 VALID/INVALID、关联 CONSISTENT/INCOMPLETE/NOT_CHECKED | 不访问引用或调用 replay/judge；无 review 也可 CONSISTENT，coverage 始终 NOT_CHECKED |

来源/target 始终 UNVERIFIED，runtime_metrics=null、baseline_eligible=false。API 的 exit_code 是数据；文件来源检查 CLI 合法仅检查退出 3，非法退出 2，不存在新进程入口。

## §2 最小材料索引

每项列出 alias、用途/版本、size、原 SHA256、提供/缺省状态、关联 run/case/target/审阅引用；只用获准非秘密标识。索引排除自身，其载体原 size/SHA 由外层交付检查点绑定。包级指纹固定算法和有序集合，包含所有提供的输入与附属材料，不能只绑定七位置。

具体算法：alias唯一、非空、不含NUL/CR/LF；raw_sha256为64位小写hex。以alias按Unicode码点升序排序，逐项拼接alias + NUL + raw_sha256 + LF，以UTF-8编码后计算SHA256。只纳入确实提供的输入及全部附属材料；缺省reviews/baseline在索引明确“不提供/b''”、size=0及SHA256(b'')，不伪造物理文件或纳入提供项集合。索引自身排除，外层同时绑定集合指纹和索引载体的原size/SHA，使缺省状态、用途及审阅关联也绑定到批准版本，不让同内容集合替代不同索引版本。

| 项 | 最小材料 | Agent 技术核验与停止条件 |
|---|---|---|
| M-01 环境/run/用途 | 非秘密环境、run、采样 commit、EVAL/target、模型部署/有效参数、time_basis、采样与用途决定引用 | 比对 manifest.model/sampling/time_basis 与版本；批准范围或来源不明时延期，不把日期/URI当证书 |
| M-02 七位置原 bytes | 五必填与 reviews/baseline 提供/缺省状态、各 size/SHA、manifest 四 hashes | 不解码重写、补 hash 或归一化后冒称原 bytes；reviews 缺省不免 actual 必要审阅，baseline 缺省不产生回归通过 |
| M-03 完整轨迹/回复 | 22 case、完整初始 turn、连续 sequence、唯一 call_id、全部尝试/结果/错误、首次 SQL、所有失败及必要脱敏回复 | sequence 从1至n；首次SQL为有序轨迹首个 execute_sql。不用最终成功替代失败，不凭零调用或 complete=true 证明完整 |
| M-04 脱敏审阅 | 来源、脱敏方法/版本、被审材料原指纹、结论/范围/条件及采样/用途版本关联 | 无业务行数据、business_summary、PII、凭据、完整返回 envelope；自由文本/SQL/错误无法判安全则保留缺口，不读秘密补齐 |
| M-05 target/装配 | 采样 commit 的 roster 顺序、实际 loader body、有效 Runtime 段、算法/编码、最终正文/摘要及来源绑定 | 只核获准显式材料；不导入 agent/config、不启动 runtime、不读取引用目标、不用当前文件替代历史 loader/cache |
| M-06 独立语义/红线 | 全部必要语义 check、5红线、非红线 case ID 排序前三条 audit.sample 及实际审阅证据 | 保留22完整分母；review总数/标签不替代必要集合。独立Agent可审真实材料，不能把synthetic记录改名为实际审阅 |
| M-07 包批准/target接受 | 全部材料精确指纹、用途/对象/环境/条件、脱敏/审阅版本、Owner包版本决定与target接受记录 | 分开材料用途批准、软件通过、Git集成、actual运行验证与Owner接受；技术检查不自行签发批准 |

baseline 可选；提供时保留原报告与来源/审阅绑定，按现有完整性/兼容规则核。synthetic baseline 不可用于实际比较。附属材料只消费获准且确实提供的内容，不递归引用、不扫描目录或连接来源服务。

## §3 来源、脱敏与批准链

关联采样 run/commit → 完整轨迹/target → 脱敏版本与审阅 → 全部材料指纹 → 允许用途/target决定。各审阅追到实际被审版本；旧指纹、“已批准”、approval=true、URI存在均不足。

Agent 可核身份、版本、顺序、摘要和可见关联；不能仅凭这些记录证明采样发生、环境真实、无隐去失败、自由文本无敏感信息、审阅确实独立发生或 Owner 决定有效。Owner 决定可用来源、用途、数据范围及最终 target 接受；Agent 提交实际技术结果与无法证明部分。Owner不代做普通转换、命令或常规合成验收。

脱敏删改导致 SQL/回复/错误不足以判断时，不补造替代记录、不用安全样例通过，保留缺口并延期。不得从 business_summary 或业务行数据重构事实。旧 walkthrough 的截断 Markdown/五场景不是22-case完整包，本轮不导入其 dotenv/runtime 代码。

## §4 loader、roster 与最终装配

body 是采样时 loader 返回字符串，不用当前磁盘文本或静态文件 hash 替代。load_prompt/load_skill 实际使用 frontmatter.load(...).content 并有缓存；需说明采样 commit 与当时 body 的来源关系。roster 以该 commit 的 _ACTIVE_SKILLS tuple 为准，不在本指南缓存名称/数量。

当前 _build_system_prompt 顺序：prompt body → 有效 # Runtime 段 → roster 顺序的 skill bodies，使用 "\n\n".join(parts)。对已提供的精确字符串按 UTF-8 重算 body/最终 SHA256，不自动 trim、改换行、补终止 LF 或重排。采样算法若不同，需其版本/差异材料，不套当前算法声称匹配。

可核有序 list、组件 path/version/body hash、Runtime provider/model 与所供材料及最终 hash 的关系；自洽不认证实际 loader/cache/部署采用它们。schema 无 body/完整环境容器，附属材料独立 raw 绑定，不塞 manifest 未知字段。

## §5 review 的两种摘要与必要集合

整份 observations/reviews/manifest 按原 bytes 计算 SHA256。review.case_observation_sha256 则来自 schema._load 解析的原观测对象：JSON ensure_ascii=False、sort_keys=True、separators=(",", ":")、allow_nan=False，末尾单个LF，再UTF-8编码。不能用整份JSONL hash、pydantic补默认值后对象或report派生case替代。

同时核run_id/case_id/check_id、config/reference原hash、judge_profile/judge_revision、reviewer_role、sanitized_review_ref、verdict/reason与被审真实版本。必要语义集合以dataset.expected_output/expected_trajectory与judges.py实际适用项为准；另含全部5个audit.red_line及非红线case ID排序前三个audit.sample。当前22分母下满足至少10%审计，不选择容易通过的三条或只按条数验收。

synthetic 保持 agent_simulated 和 initial_label_ref/independent_check_ref 角色链。actual 的 independent_review 必须对应对获批真实观测/静态参考的实际独立审阅，不复制合成结论后改标签。Agent可做技术与语义复核；软件字符串不证明独立性，Owner保留用途/真实来源/最终接受决定。

## §6 冻结规则与未来门禁

| 顺序 | 必须保留的边界 | 当前结论 |
|---|---|---|
| 任务/材料范围 | 用途、对象、环境、获准非敏感材料，真实版本与决定一致 | 无获批真实包，相关步骤延期 |
| raw/来源/完整性 | 七位置及全部附属材料、完整有序轨迹、真实脱敏/独立审阅关联 | hash自洽不升级来源认证或真实性 |
| target/规则 | 严格lower/upper窗口与inclusive标志、22完整分母与5红线 | 不放宽边界、换首SQL、删失败/缺项或减少审阅 |
| baseline兼容 | same_target_replay现有key精确比较与完整baseline核验 | 不是跨版本A/B；#161/#504/#583–#586/probe-fixture scope保持 |
| 文件保护 | Windows fixed NTFS全部保护或其他平台等价证明；显式文件和新目录一致保护 | Linux/macOS能力不足继续fail closed |
| actual回放/接受 | 新入口具体方案、独立核验、对应实施/运行授权和真实结果 | 本文不实施或批准入口，不执行actual/live |

当前 compatibility_key 包含eval/judge、config/dataset/reference hash、repository_commit、target_snapshot、model、sampling、time_basis、source_kind、sanitization_version，不认证source_ref/批准链，后者材料侧另核。不改key/report/阈值：首轮通过率下降>=0.03或红线通过率任何下降仍为硬回归；完整分母及必要checks保持。缺有效基线或未测不能写成零下降。

未来入口完整保留repo_root/全部祖先句柄、相对逐组件打开、reparse/卷/最终路径/单链接/前后身份、大小限额、独占新目录。禁UNC/网络/秘密路径、扫描、引用递归、普通open回退。读写/close故障可留部分输出，保留并对账、不覆盖删除；不承诺原子/fsync耐久性，不以类型/内存模型证明原生保护。

缺材料、用途/版本不符、审阅/真实性不足、target不可关联、保护或授权不足时延期受影响步骤，不降级或造actual PASS。实际技术拒绝保留原错/BLOCKED_EXECUTION_ROUTE，不切工具/凭据、改权限、编码或改写命令绕过。

## §7 现有API/CLI、输出与诊断

仅用获准在内存的固定synthetic ReplayInputs调用inspect_source(inputs)，结构dict及UNVERIFIED/NOT_CHECKED/null/false保持；不访问引用、不调用replay/judge认证来源。

来源检查文件入口仍为python -m mj_agent.evaluation.inspection_runner --synthetic-fixture，显式--eval-config/--dataset/--observations/--manifest/--reference、可选--reviews/--baseline、新--output-dir。准确调用/保护/恢复见RUNBOOK§4.3；回放入口见§4。

help=0、合法仅检查=3并写单inspection.json、非法=2且不创建输出；write/close=2可留部分输出。Windows actual标签早2/ACTUAL_ENTRY_DEFERRED；其他平台或更早保护失败保留FS_CAPABILITY_UNAVAILABLE等既有诊断；baseline空/非object既有码保持。本文无新退出码、approval开关、--actual或--trust-source，不把数据exit_code、synthetic退出3或VALID当运行接受。

## §8 固定合成正反例与验收

| ID | 固定输入/操作 | 固定期望与限度 |
|---|---|---|
| D-01 | 既有eval_core 22-case/34-review与独立inspection.expected.json | VALID/CONSISTENT；来源/target UNVERIFIED、coverage NOT_CHECKED、metrics null/baseline false |
| D-02 | synthetic仅改虚构source/批准引用 | 不认证引用或解锁actual、不访问链接，不从结构结果造真实性PASS |
| D-03 | manifest加环境/body或非SQL _Call加sql/未知参数 | 当前闭合schema继续拒绝；材料索引不扩展输入 |
| D-04 | raw改动不改已有hash，或review规范观测/config/reference/judge不符 | INPUT_HASH_MISMATCH等错误或review gaps；不归一化/补hash修复批准版本 |
| D-05 | 缺首次失败/调用，或complete声明与所供记录冲突 | 可见缺口保留；上游遗漏可能仍自洽，软件不能证明遗漏不存在 |
| D-06 | roster重排或body/最终hash不符 | API只核声明，不重算body；附属材料按§4核不一致，自洽仍不认证运行 |
| D-07 | 固定危险路径、碰撞、hardlink/reparse/限额/close故障 | 复用既有固定负例和诊断，不降保护、不覆盖删除部分输出 |
| D-08 | actual标签或Linux/macOS文件入口 | 持续早拒绝/保护不足延期；合成/模型/类型不算actual或原生成功 |

D-02–08是文档预期分类，不造actual包或新payload schema。仅文档阶段核真实符号/字段/规则、固定expecteds、两类摘要、材料/角色/延期、链接/INDEX/元数据及raw；独立Agent从这些AC审真实文档/代码/证据。无实现变更时不造实现镜像测试、不声称新API/门禁运行。

完成标准：M-01–07及Agent技术/Owner实质/软件不可证明三界可核，现API/保护/核心规则不改，固定合成期望明确，独立核验通过，版本可审阅且Owner接受另记。无包、真实审阅/目标缺失、保护/授权不足或拒绝持续对应延期；#582 OPEN、Plan active、capability idea/last_verified=null。

## 关联文档

- [schema](../../src/mj_agent/evaluation/schema.py)、[inspection](../../src/mj_agent/evaluation/inspection.py)、[inspection_runner](../../src/mj_agent/evaluation/inspection_runner.py)。
- [装配](../../src/mj_agent/agent.py)、[prompt loader](../../src/mj_agent/prompts/__init__.py)、[skill loader](../../src/mj_agent/skills/__init__.py)，仅静态源码引用，不导入运行。
- [judges](../../src/mj_agent/evaluation/judges.py)、[report](../../src/mj_agent/evaluation/report.py)、[fixture README](../../tests/unit/fixtures/eval_core/README.md)、[本轮文档验证](../../capabilities/data-agent/evaluation/evidence/reports/2026-10-13_t007d_material_contract_verification.md)。

## 更新记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-10-13 | v0.1 | Owner采纳材料/门禁文档范围；定义最小材料、两类摘要、职责、冻结规则与延期，版本接受另记 |
