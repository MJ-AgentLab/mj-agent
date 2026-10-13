---
type: spec
domain: WORKFLOW
summary: 对原始交付 ZIP 进行跨宿主只读完整性核验，保留执行版本、布局及来源限制
owner: ranzuozhou
created: 2026-10-13
updated: 2026-10-13
state: draft
version: v0.1
track: engineering-workflow
task_type: 7
---

# [SPEC] Portable Delivery Evidence Verification

## §0 Task Type Identification

Engineering-workflow infra；新增兼容的只读工程 CLI，不改 runtime/API、现有 run/check、G21/G8、门禁来源或接受标准。对应 [后续 Plan](../../../plans/[PLAN]_agent_first_delivery_followups.md) ZIP-001 至 ZIP-004。

## TL;DR

核验对象是原 archive 的字节及其声明的执行版本。验证机的路径和 HEAD 分别记录，不能替代原执行事实。新的 integrity 报告不认证来源、不授权操作、不生成 Owner 接受或实际 runtime 基线。

## §1 Context（背景）

当前 delivery_evidence.check 要求检查机 HEAD 与 tested_sha 一致，并按检查机 output-dir 展开 argv；原 Ubuntu artifact 搬至 Windows 后无法用原 check 完整核验。该限制与失败历史保留，新增动作解决存储位置与宿主变化，不降低原检查。

## §2 Scope（范围）

只读原 ZIP、明确预期的版本与原 suite、真实 Git 对象及其 bound blobs，重新核验原 logs/JUnit/逐 AC；写新的独立报告。排除运行候选命令、安装依赖、网络请求、checkout/reset、修改原 archive、源认证、业务接受、actual 来源真实性及跨仓配置。

## §3 Contract（契约）

新脚本 `scripts/sdd/verify_delivery_archive.py` 提供可注入 repo_root 的 `main`。CLI 必填 `--archive`、`--archive-sha256`、`--repository`、`--head-sha`、`--base-sha`、`--tested-sha`、`--tested-tree`、`--suite`（原相对路径）、`--execution-kind`、`--run-url`、`--report`；可选 `--repo-root` 指已有 Git 对象库。不允许只从待验 artifact 自选预期值。

核 Git 对象、head/base/tested 的现有合法关系与 tree、suite/harness/dependency/unit baseline/input 的字节及 Git blobs；原 suite 有序命令、expected_exit、run URL、环境与时间顺序、log/JUnit 摘要、test_integrity 和逐 AC 完整核验。未找到原 tested 对象必须失败或缺依赖，不能用当前 HEAD 或等价 tree 伪装原对象。

`resolved_argv` 除 `{output_dir}` 展开外必须逐字符相同。原执行 output root 必须来自原记录中一致且合法的展开；验证机位置只用于寻找 archive 字节，不可全局路径替换、模糊匹配或跳过字段。source_kind、execution_source 和三项 claims 按原规则一致，claims 始终 false。

ZIP 成员须唯一、普通文件、安全相对路径、准确匹配声明日志/JUnit及 delivery.json；拒绝绝对/逃逸/链接/设备/秘密路径、歧义目录及超限内容。归档只读且不提取到原工程路径。报告新建且不得覆盖、不得处于秘密/间接路径；其状态仅表达完整性核验结果、预期/原执行绑定、验证机版本、原归档摘要及限制。

## §4 Configuration（配置）

无新增环境变量或凭据。归档最多 64 MiB、512 个普通成员，单成员最多 32 MiB、展开总大小最多 128 MiB；Git 调用有界。沿用 Git 无 replace-object、无父进程 Git 重定向、白名单环境纪律；不读取用户配置/秘密，不发起网络请求。

## §5 Error handling（错误处理）

版本/内容/结果/来源/布局不一致为拒绝，缺文件、对象、工具或非法输入明确失败/缺依赖。成功为 `INTEGRITY_VERIFIED`/exit0，完整性拒绝 exit1，输入或 `UNMET_DEPENDENCY` 为 exit2。输出只给安全错误类型，不泄露原载荷、环境值或原始 Git 错误。

## §6 Rollback / Compatibility（回滚 / 兼容性）

现 `delivery_evidence.py run/check` 及原 artifact 格式保持。原 check 的不支持/失败不能因新增报告消失。新动作可用新 PR 回退，原 archive/历史证据不需迁移或回滚；不包含平台权限或生产操作。

## §7 Verification（验证）

正例用真实临时 Git 对象和固定预期测试结果证明原执行版本与验证机 HEAD/归档位置不同仍能验证；原 Ubuntu 布局在 Windows 核验时保存原字符。负例覆盖 Plan ZIP-004，全量重算日志/JUnit/AC，不只断言实现返回值。具名原归档仅在实际对象可得时验证，缺对象不得计通过。

此动作未执行原测试、未验证 actual 来源或 runtime；SELFTEST 保持 SELFTEST，来源认证与 Owner 接受单独记录。适用 unit/CLI/ruff/type/doc 检查；其他平台的原生路径保护未运行时单列。

## §8 Observability（可观测性）

新报告记录观察时点、CLI 参数中的预期版本、原 archive 摘要、原 execution binding、验证机 Git/平台、核验结论与限制；逐项拒绝可定位到安全类型。原 execution 时间和路径保留，不把验证报告生成时间伪装成原测试运行时间。

## §9 Open questions（开放问题）

新动作不用于替代独立可信门禁。控制源与来源认证按 Q24 的独立方案另行决定；本 SPEC 不为该方案授予权限。普通参数名、有限资源上限与错误编码随实现精确同步。

## 关联文档

- [后续 Plan](../../../plans/[PLAN]_agent_first_delivery_followups.md)
- [Agent-first 交付指南](../../guide/[GUIDE]_Agent_First_Delivery.md)
- [接受及执行边界](../../../policies/ai-agent.md) §4

## 更新记录

- 2026-10-13：从原 check 的实际跨宿主限制建立新增只读核验基线。
