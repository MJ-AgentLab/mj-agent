# P3 冻结审阅包 — G-P3-ATOMIC

状态：准备完成，待具体组批准和 Owner 人工应用；**正式 P3 仍部分完成/未切换**。
本包不构成审批凭证。已有旧补丁被本摘要绑定的版本替代，禁止混用。

- 工作树：`D:\workspace\10-software-project\projects\mj-agent\maintain\codex-dev-mode-migration`
- HEAD：`20e2f24c352cf640d9dd33234b128ca897804b99`；分支：`maintain/codex-dev-mode-migration`
- 补丁 SHA256：`abdf11bc9fc44286ab2b5cc32294e7385d0af97c8b8dc7d6c099210cd6734741`
- 188 项：42 新增、130 修改、16 必要旧机制测试文件删除提案。没有旧客户端源/投影资产批量删除。
- 正式文件未应用；暂存区为空；P1 原有共享拆分和 P0–P2 当前成果已核验保留。

## 审批集合（必须一次批准、一起应用）

| 子集 | 内容 | 文件数 | 依据与当前状态 |
|---|---|---:|---|
| A1_OWNERSHIP_POLICY | 入口/37技能/共享资源/所有权/定向 ADR 与政策（含6非客户端 adapter 的必要指针更正，现址与业务规则保留） | 69 | 计划 §4.5 + 对应保护面；准备获授权，正式具体差异待批准 |
| A2_CONFIG_GUARDS | 原生配置/MCP 工具/守卫；只承接8服务，Owner动作仍 block，不修改个人配置或激活信任 | 8 | 计划 §4.5 + 对应保护面；准备获授权，正式具体差异待批准 |
| A3_CONTRACT | 8 infra 冻结、header/schema/检查器及 MCP/必要跨 capability 声明消费者 | 8 | 计划 §4.5 + 对应保护面；准备获授权，正式具体差异待批准 |
| A4_CI | V4、V8–V13 CI/门禁替换及 V12 具名退役；blocking 效果单列 | 2 | 计划 §4.5 + 对应保护面；准备获授权，正式具体差异待批准 |
| A5_TEST_DISPOSITION | 16旧机制测试文件删除提案、混合文件拆分保留、安全继任测试与新增 blocking 测试 | 36 | 计划 §4.5 + 对应保护面；准备获授权，正式具体差异待批准 |
| A6_DIRECT_CONSUMERS | setup/扫描域/索引/模板/README/上手指南/stale-docs/build-ignore/EOL直接消费者 | 65 | 计划 §4.5 + 对应保护面；准备获授权，正式具体差异待批准 |

逐文件 A/M/D、前后摘要、授权依据与恢复来源见 `p3-cutover-files.json`；每个子集准确文件集合见
`p3-authorization-map.json`。批准须覆盖上述六个子集和16项具名测试处置，不使用“迁移全部放行”。
ADR-040 的 active/accepted 是**批准并应用后的目标状态**；目前只是候选元数据，未预占正式编号。
其他历史 ADR 不改；8项 infra 旧16/新16摘要重新计算成功，见 `p3-infra-freeze-map.json`。

## 门禁、消费者与验证

V4、V8–V13 的旧保护→新承担者→正反验证→处置见 `p3-gate-map.md`。
完整 workflow、门禁注册、schema、契约、直接调用者、扫描域和必要 pytest 处置均进入同一补丁。
非客户端 adapter 保留现址与有效规则；只修正必要开发技能引用，不全目录重构。
P2 37项/296维/142案例身份保留；两处 INDEX/AGENTS label 与共享根路径说明见 addendum；
381 必需资源在无旧客户端的非 Git 静态夹具存在，6 示例不计 PASS。

54 项合成离线用例 PASS；正向/负向、命令、cwd、Python/平台、输出与当前候选摘要见
`p3-completion-verification.json`。V4/V8–V11、V13 的候选执行体、六个 capability schema/trace/
contract、自动索引、文档、ruff、离线边界均完成静态验证。跨仓/归档扫描保留 WARN，原树对照随证据。
非法配置失败、秘密不回显、Owner编辑硬阻断、G1/G2及 malformed wire均有反例。

**未验证**：完整新 pytest（tracked-only runner 与未跟踪候选不兼容，且本阶段禁止暂存）；实际 CI、
宿主加载/hooks/model、服务/真实凭据/平台矩阵。没有用另一 pytest 路线绕过安全 runner。
静态通过/旧 P1 122 项复跑/Owner 批准不能抵充这些结果。P2 临时审阅脚本不进入正式 CI。
首次新 gate CI 锚点在真实应用后记录，不能继承旧生成 gate 的 streak。

## 人工应用步骤

1. Owner 审阅并批准 G-P3-ATOMIC 的具体六子集；批准前不要应用。
2. Codex 停止本工作树自动写入。只在本机普通 PowerShell 操作下列目录；不要改变权限、停 hook、
   自动信任或激活 hooks；不要使用 --reject/force 或自动解决冲突。
3. 先核对 `p3-review-freeze.json` 绑定的 manifest/patch/恢复源摘要，再逐项核对当前身份：

```powershell
Set-Location -LiteralPath 'D:/workspace/10-software-project/projects/mj-agent/maintain/codex-dev-mode-migration'
$p3Evidence = 'evidence/codex-only-migration'
$p3Freeze = Get-Content -LiteralPath "$p3Evidence/p3-review-freeze.json" -Raw | ConvertFrom-Json
foreach ($p3BoundFile in $p3Freeze.files.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath "$p3Evidence/$($p3BoundFile.Name)" -Algorithm SHA256).Hash.ToLowerInvariant() -ne $p3BoundFile.Value) { throw "Changed review file: $($p3BoundFile.Name)" }
}
if ((Get-FileHash -LiteralPath "$p3Evidence/$($p3Freeze.package)" -Algorithm SHA256).Hash.ToLowerInvariant() -ne $p3Freeze.package_sha256) { throw 'Review package changed; stop' }
$p3Manifest = Get-Content -LiteralPath 'evidence/codex-only-migration/p3-cutover-files.json' -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $p3Manifest.backup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $p3Manifest.backup_sha256) { throw 'Recovery source changed; stop' }
if ((git rev-parse HEAD) -ne $p3Manifest.head) { throw 'HEAD changed; stop' }
if ((git branch --show-current) -ne $p3Manifest.branch) { throw 'Branch changed; stop' }
if ((git diff --cached --name-only)) { throw 'Index changed; stop' }
if ((Get-FileHash -LiteralPath 'evidence/codex-only-migration/p3-cutover-proposal.diff' -Algorithm SHA256).Hash.ToLowerInvariant() -ne $p3Manifest.patch_sha256) { throw 'Patch changed; stop' }
foreach ($p3File in $p3Manifest.files) {
    if ($null -eq $p3File.current_sha256) {
        if (Test-Path -LiteralPath $p3File.target) { throw "Unexpected existing target: $($p3File.target)" }
    } else {
        if (-not (Test-Path -LiteralPath $p3File.target -PathType Leaf)) { throw "Missing target: $($p3File.target)" }
        if ((Get-FileHash -LiteralPath $p3File.target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $p3File.current_sha256) { throw "Changed target: $($p3File.target)" }
    }
}
foreach ($p3Input in $p3Manifest.p0_p2_prerequisites.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath $p3Input.Name -Algorithm SHA256).Hash.ToLowerInvariant() -ne $p3Input.Value) { throw "Changed prerequisite: $($p3Input.Name)" }
}
git apply --check -- 'evidence/codex-only-migration/p3-cutover-proposal.diff'
if ($LASTEXITCODE -ne 0) { throw 'Patch check failed; stop and return for revision' }
```

确认身份未变化、检查通过且审批覆盖后，人工执行：

```powershell
git apply -- 'evidence/codex-only-migration/p3-cutover-proposal.diff'
if ($LASTEXITCODE -ne 0) { throw 'Application failed; stop' }
```

上述命令不暂存、不提交。补丁只适用于冻结前置字节；已有P0–P2未提交成果不能从HEAD推定。
本轮 `git apply --check` 已成功；恢复补丁也在静态夹具目标状态完成 --check，未实际应用任何补丁。

## 应用后 Codex 验证

逐项核对 manifest proposed_sha256（删除项确认不存在），复算8 infra摘要并核对配置与资源/消费者。
从正式根执行证据中的原生检查与54项 unittest；运行共享安全 runner时仍遵守其 tracked-only规则。
如尚因未跟踪交付文件不能运行完整pytest，明确 NOT_TESTED 并单独确认合法后续路线，不能暂存或放宽。
只有实证应用成功的项才能退出对应执行阻断；否则整组仍未完成。宿主/服务/平台未验证状态保留。
不得进入 P4/P5、开issue/分支、提交/推送/PR。

## 成组恢复来源

1. **当前准确工作字节**：`.mj-agent-local/p3-preapply-public.zip` + manifest SHA；包含所有非 ADD 目标
   的原始字节（精确集合以 ZIP/manifest 的非 ADD 项为准），包括P1已拆分的旧测试及新共享测试。
   `p3-cutover-recovery.diff` 是按本包目标状态生成的整组恢复差异。只在逐项新身份相符时先 --check，
   再由 Owner 人工恢复；不选择性恢复旧generator后覆盖原生入口。
2. **已提交基线**：manifest HEAD 的 `<commit>:<path>` 可恢复基线 Git 文件；
   不用于替代P1当前修改、未跟踪共享测试或P0–P2成果。工作树原始 CRLF/LF 字节由ZIP保存。
3. **未提交P0–P2**：`.mj-agent-local/p3-entry-public-backup.zip`（63项，摘要见p3-entry.json）；
   另有本轮入口 `.mj-agent-local/p3-completion-entry-public.zip`（88项，含此前P3准备）。
   这些本地恢复源不能自行清理；HEAD不含这些成果。
4. 恢复前暂停整组消费者、保存应用后的新增工作；不使用 git reset --hard / git clean。
   若身份不同，停止并重新审阅差异，不强制覆盖。恢复代码不等于恢复凭据/数据库/容器。

## 未决项与P4输入

U01 memory备份/schema、U02后台生命周期、U06 snapshot/EVAL维持 UNMET_DEPENDENCY / NOT_TESTED；
U03真实凭据/OS注入/平台与U05服务/远端写维持 NOT_TESTED。
U04 = 人工路线已选定，具体组待批准/人工应用/验证；自动受保护写入仍 BLOCKED_EXECUTION_ROUTE。
U07 = 候选消费者闭合准备完成，正式消费者尚未切换，不能记已闭合。
P4需正式应用后身份与验证、最终交付清单、未跟踪文件纳入方式、实际平台/宿主版本及人工信任取证。
旧客户端源/投影链/lock/旧合同仍物理保留，仅候选扫描域退出；P5逐文件清理批准尚未发生。
