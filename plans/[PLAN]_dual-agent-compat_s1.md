---
type: plan
summary: 双工具兼容 v5 S1 执行计划（issue #326）——skills 投影首批：全5白名单闭包收口（中立化4出边）+ agents_sync 生成器（sync/--check/--adopt）+ .agents.lock.json + 5 技能字节同一投影入仓 + drift gate warning 首发 + AGENTS.md 契约条，stacked 2-PR 链；含 Stage 3 关键发现（F10 EOL 双平台）与 3 项 Owner 拍板记录
owner: ranzuozhou
created: 2026-07-14
updated: 2026-07-14
completed: 2026-07-14
state: completed
track: shared
---

# [PLAN] 双工具兼容 v5 — S1 执行计划（issue #326）

## 1. Linked Artifacts

- Issue: #326（S1 执行）· 总锚 #312 · Program plan: [[[PLAN]_dual-agent-compat|v5 计划]]（§4.4 投影三档 / §8 目标文件 / §10 投影 checker 规则 / §11 S1 / §11.1 S1→S2 晋级 / §12 投影域验收）
- Intake: [[[INTAKE]_dual-agent-compat_s1|Stage 0 Intake]]（2026-07-14；3 项 Owner 拍板：白名单全5+中立化4出边 / 2-PR stacked / issue #326+INTAKE 落盘）
- Repo Scan: Stage 3 对话输出（2026-07-14；证据以 develop @ `0cd1b2d` 为基准）
- 关联 ADR：[[../decisions/ADR-036_Dual_Agent_Thin_Adapter_And_Projection|ADR-036]]（D-011~D-017 已收口；本切片是 D-012/D-014 的首次产物落地）
- 既定机器契约（S0 遗产，本切片**不得另立口径**）：V9 `check_agents_projection.py` 已固化闭包窄定义（仅 `## Handoff*` 段出边）、reconcile 全量对账、lock 语义（`name → sha256:<body_sha256>`，LF 归一 + strip frontmatter）、`.agents/` 存在时 PJ011 warning→error 翻转

## 2. Context

P1+S0（#320）已闭环：manifest 37 条目（projection 🟢5/🟡21/🔴11）+ V8/V9 已挂 CI warning + ADR-036 + 根/4 嵌套 AGENTS.md 就位。V9 真实树实测 **0E/4W**，4 条闭包 warning 即白名单定案依据：`flow-diagnose→flow-plan`、`flow-diagnose→flow-verify`、`git-delete→flow-intake`、`git-push→git-pr`。闭包数学推论（Stage 3 复核）：`git-commit` Handoff 出边指向 `git-push`——任何含 git-commit 的收窄方案仍需中立化出边，零编辑方案仅剩 `{git-sync}` 单技能（低于 §4.4 的 3-5 口径）→ Owner 拍板**全 5 + 中立化 4 出边**（manifest 零改动，闭包永久闭合于 5）。

风味判定：全切片 C（工程编排技能源 / scripts / tests / CI / 治理文档）。`.claude/skills/**` 是 track C（两类 skill 严格区分），编辑不构成 B 风味 runtime-skill-content-change；白名单 5 技能均不在冻结 8 内。§3.1 必停 4 项（trigger 10-13）不触发；High 来自 CI workflow 变更 + protected-path 源编辑 + `.agents/**`/`agents_sync.py` 受保护邻接面创建（§17 v5 / D-017）。

Stage 3 关键发现与设计裁定：

1. **F10 EOL 双平台（关键约束）**：`.gitattributes` 仅 `* text=auto`（`.md` 未 pin `eol=lf`）+ 本机 `autocrlf=true` → SKILL.md 在 Windows 检出 CRLF、ubuntu CI 检出 LF。因此 `agents_sync` **一切比较（--check / golden / lock）均 LF 归一后进行**（与 V9 `_normalized_body_hash` 同口径）；投影写盘 = 复制源文件**原始磁盘字节**（同平台源/产物检出约定一致 → 本地平凡字节同一；git `text=auto` 保证仓内 blob 均为 LF → 跨平台仓内字节同一）；生成式 README 比较同样 LF 归一。**不改 `.gitattributes`**（避免全仓 renormalize 波及）。
2. **Handoff 标题连带中性化**：`flow-diagnose` 的 `## Handoff to mj-agent-flow-verify` 与 `git-push` 的 `## Handoff to mj-agent-git-pr` 标题含集外技能名（无 `/` 前缀，V9 不抓）——一并改为 `## Handoff`（对齐 git-delete 风格），保持投影语义干净；`git-commit` 的 `## Handoff to mj-agent-git-push` 指向集内技能，**不动**。段外 `/mj-agent-*` 引用（如 flow-diagnose L84/L88-91）不在闭包扫描范围，**不动**。
3. **agents_sync CLI 形态**：单文件自建 argparser（互斥：位置参数 `sync` / `--check` / `--adopt <name>`）；`doctor` 属 S3，本切片不实现（帮助文案注明）。生成期纯语法变换——零 env 解析、零网络、零 secrets 读取；`main(argv=None, repo_root=None)` 注入式（#217 教训）；sys.path bootstrap 仿 `check_runtime_skill_contracts.py:36-39`。退出码 0（一致/成功）/ 1（drift 或 reconcile 违规，文案给规定动作）/ 2（用法或 manifest 不可读）。
4. **产物形态**：`.agents/skills/<name>/SKILL.md` ×5（源字节复制，目录内仅此一文件——5 个源目录已核实均只含 SKILL.md）+ `.agents/README.md`（目录级 GENERATED 横幅 + 语义差异声明：Claude harness ask 门/hook 在 Codex 不在场，投影技能内必停语义为 AGENTS.md 自律义务 + 修改路径 = 改源+重跑 sync）+ `.agents.lock.json`（仓库根；`{"<name>": "sha256:<hex>"}` 排序键、每条目一行）。lock 哈希 = 产物 LF 归一后 `body_sha256`（与 V9 `check_lock` 逐字节同口径）。
5. **gates.md 登记 = V10**（§2 表下一空位）：`agents_sync.py --check`（drift gate，warning@ci 首发；blocking 转正属 S3/P4，另走 `ci-blocking-gate-toggle`）。
6. **CI 注释同步**：V8/V9 block 注释与 V9 step name 写死 "0E/4W (S1 whitelist signals)"——PR-A 闭包收口后失真，随 PR-A 同步为 0E/0W（纯注释/名称，无 gate 语义变更）；PR-B 在同 block 内加 drift step 并补块注释。
7. **既有测试连带**：`test_sdd_development_agent.py:133` docstring "S0 empty state" 在 PR-B 产物落地后过时 → PR-B 顺手更新（断言本身 exit-0 语义两 PR 后均成立，不动）。

## 3. Scope

- 包含：program plan §11 S1 全部条目——闭包收口（中立化 4 出边）、`agents_sync.py`（emitter A + lock + reconcile）、🟢 5 技能投影产物 commit 入仓、skills drift gate warning 首发、AGENTS.md 投影契约条、V9 联动核验
- 不包含：`.codex/config.toml` / MCP emitter B / 3 spikes（S2 硬前置）；`doctor`（S3）；drift gate blocking 转正（S3/P4）；冻结 8 infra skill（白名单已排除）；manifest `projection` 字段改动（全 5 方案零改动）；`.mcp.json`；扩投影面超出 `.agents/skills/`（须重新拍板，D-011）；`src/mj_agent/**`
- 前置依赖：P1+S0 已 merge（develop @ 0cd1b2d）；PR-B base = PR-A 分支（stacked，A 先合 `--delete-branch` → 核对 B baseRefName 已翻 develop → 合 B）

## 4. 任务拆解（Stage 8 编号 · 全部风味 C）

### PR-A `maintain/326-s1-closure`——闭包收口：中立化 4 出边 + CI 注释同步 + plans 落盘

- **8a 中立化 ×3 文件 4 出边**（`.claude/skills/**` protected，逐写权限 prompt = 拍板载体）：
  - `mj-agent-flow-diagnose/SKILL.md` Handoff 段：`/mj-agent-flow-verify` → 「Stage 10 本地验证（`sdd/workflows/execution-loop.md` §5 验证矩阵）」；`/mj-agent-flow-plan` → 「Stage 4 计划环节（execution-loop §4 映射表）立 follow-up」；标题 `## Handoff to mj-agent-flow-verify` → `## Handoff`；集内 `/mj-agent-git-commit` 保留。
  - `mj-agent-git-delete/SKILL.md` Handoff 段：`/mj-agent-flow-intake` → 「Stage 0 任务受理（execution-loop §4 映射表）起首」；集内 `/mj-agent-git-sync` 保留。
  - `mj-agent-git-push/SKILL.md` Handoff 段：`/mj-agent-git-pr` → 「创建 Pull Request（`gh pr create` 显式 `--base`，per `policies/git-branching.md` G2）」；标题 `## Handoff to mj-agent-git-pr` → `## Handoff`。
  - 验证：`check_agents_projection.py --all` → **0E/0W**；`check_claude_skill_contracts.py --all` 仍 37/37 PASS（5 技能非冻结面）。
- **8b CI 注释同步**：ci.yml V8/V9 block 注释 "Baseline 0E/4W (S1 whitelist signals)" 与 V9 step name "0E/4W closure signals" → 0E/0W 表述（无 `continue-on-error` 变更）。
- **8c plans 落盘**：`[INTAKE]_dual-agent-compat_s1.md` + 本文件（随本 PR 携带）。

### PR-B `maintain/326-s1-agents-sync`（base=PR-A）——生成器 + 产物 + gate + 契约条

- **8d 生成器 `scripts/sdd/agents_sync.py`**：读 manifest `projection: project` 集 →
  - `sync`：逐技能复制 `.claude/skills/<name>/SKILL.md` 原始字节 → `.agents/skills/<name>/SKILL.md`；生成 `.agents/README.md`（固定模板）；重算 `.agents.lock.json`；**全量 reconcile**——删除 project 集外的 `.agents/skills/*` 孤儿目录；幂等（无变化时零写盘、输出 up-to-date）。
  - `--check`：不写盘；LF 归一比较（产物 ≟ 源、README ≟ 模板、lock ≟ 重算值、目录集 ≟ project 集）；任一 drift → exit 1 + 文案给规定动作（「改源 + `agents_sync.py sync` + 重提交；产物不可手改（D-012）；反灌走 `--adopt` + 对应 HITL」；merge 冲突规定动作 = merge 源后重跑 sync 覆盖，不手工三方合并产物）。
  - `--adopt <name>`：显式反灌——把产物内容写回源 SKILL.md 并提示对应 HITL 义务（`.claude/skills` protected prompt 即拍板载体）；随后需重跑 `sync` 对齐 lock。
- **8e 单测 `tests/unit/test_agents_sync.py`**（tmp_path 合成仓 + 真实树钉线）：幂等（二跑零变化）；drift 三态（一致 0 / 手改产物 1 / 改源未 sync 1，且文案含规定动作）；reconcile 负向（孤儿目录：sync 清理、--check FAIL；多出文件 FAIL）；golden-file 跨 EOL（同一内容 CRLF/LF 两种检出形态 → lock 哈希与 --check 结论一致）；V9 集成（sync 后 tmp 仓 `v9_main --all` 0 violations；手改产物 → PJ033）；`--adopt` 正向；真实树 `--check` exit 0 钉线。另：更新 `test_sdd_development_agent.py:133` 过时 docstring。
- **8f 产物入仓**：在 PR-B 分支实跑 `agents_sync.py sync` → `.agents/skills/` ×5 + `.agents/README.md` + `.agents.lock.json` 一并 commit（产物与 lock 必须同 commit 落地，PJ030）。
- **8g CI drift step**：V8/V9 block 内 V9 后新增 step（`continue-on-error: true`，warning 姿态）`uv run python scripts/sdd/agents_sync.py --check` + 块注释补 drift gate 描述；`sdd/gates.md` §2 注册 **V10 Agents-Sync-Drift**（真值 warning@ci；blocking 转正属 S3/P4 另走 `ci-blocking-gate-toggle`）。
- **8h AGENTS.md 契约条**：根 `AGENTS.md` 新增「Generated projections（`.agents/`）」小节——产物生成器 100% 所有、不可手改；修改路径 = 改源（源自身的门照走）+ `python scripts/sdd/agents_sync.py sync` + 同 PR 提交；`--adopt` 反灌须 Owner HITL；产物 merge 冲突 = merge 源后重跑 sync 覆盖；投影技能内必停语义在 Codex 侧为 AGENTS.md 自律义务（harness ask 门/hook 不在场）；Codex 经 `.agents/skills` 原生发现。footer 加注记行。
- **8i adapters 登记**：`sdd/adapters/development-agent.md` §Standards/§CI Gate/§Current Implementation Status 增 agents_sync CLI 契约摘要 + V10 指针 + S1 状态行。
- **8j 收口**：全量 Level A + GitHub CI 实跑（drift step 出现且 job 绿；ubuntu 侧 golden 稳定即 §11.1 双平台证据之一）+ #326 AC 勾选证据 + §11.1 S1→S2 晋级证据回填（Codex 实机发现验证 defer 至 post-merge Owner trust 配合）。state flip post-merge 另开小 PR（#319/#325 先例）。

### Documentation Decision（§7.1 摘要）

Plan=Create（本 2 件，PR-A）；SPEC/ADR/RUNBOOK/GUIDE/STANDARD/Local ISSUE/ASSESSMENT/CHANGELOG/INDEX=None（CHANGELOG=None 按 p1s0 先例；ADR-036 已收口 D-011~D-017；无新 canonical 文档）。

## 5. 风险（Risk Level: High）

| 风险 | 等级 | 风味 | 缓解 / Rollback |
|---|---|---|---|
| 中立化措辞损伤 Claude 侧 Handoff 可用性（丢 slash 入口） | Low | C | 仅 Handoff 段集外出边改 kernel stage 指针（段外 slash 引用全保留）；rollback = revert PR-A |
| Windows/ubuntu EOL 差异令 golden/--check 双平台不稳（F10） | Medium | C | 一切比较 LF 归一（V9 同口径）+ 跨 EOL golden 单测钉住；不改 .gitattributes 避免全仓 renormalize |
| 产物/lock 分离落地触发 PJ030 | Low | C | 8f 产物+lock 同 commit；--check 在 CI 兜底 |
| classifier 非确定性拦 `.claude/skills` 编辑 | Medium | C | 交互模式逐写 prompt（= 拍板）；被拦则按既往教训一次即停、把 diff 交 Owner 自行落盘 |
| agents_sync 与 V9 口径漂移（两处实现） | Medium | C | lock 算法直接 import `_common.frontmatter.body_sha256` + V9 集成单测（sync 产物喂 v9_main）钉住 |
| CI drift step 被误判 blocking flip | Low | C | `continue-on-error: true` 显式 + PR body 声明非 `ci-blocking-gate-toggle` |
| Codex 原生发现 `.agents/skills` 后双发现/重名（F9） | Low | C | 字节同一投影（行为等价兜底）+ `.claudeignore` 已含 `.agents/`（S0）+ 应急开关 = 清空投影重生成 |
| stacked 合并顺序事故三次发生 | Medium | C | A 先合 `--delete-branch` → **核对 B baseRefName 已翻 develop** → 合 B（每步核对入 AC） |

## 6. 验证

### 6.1 Stage 10 Level A（只读 / 必跑，每 PR）

```
uv run ruff check
uv run mypy src/mj_agent
uv run pytest tests/unit tests/eval -q          # develop 本机 .env 下 #298 已知 2 假红除外
python -m compileall src
uv run python scripts/check_wikilinks.py
uv run python scripts/check_frontmatter.py
uv run python scripts/sdd/check_claude_skill_contracts.py --all    # 37/37 PASS
uv run python scripts/sdd/check_development_agent.py --all --fail-on error
uv run python scripts/sdd/check_agents_projection.py --all         # PR-A 后 0E/0W；PR-B 后含产物仍 0E/0W
```

- PR-B 附加：`uv run python scripts/sdd/agents_sync.py --check`（exit 0）· drift 演练三态（手改产物→1；改源未 sync→1；恢复→0）· `sync` 幂等二跑零 diff（`git status --short` 空）

### 6.2 Level B

- Codex 实机发现/调用投影技能（§11.1 S1→S2 晋级要件）：依赖 Owner 每工程师×每 worktree 人工 trust（D-015 只读红线）——**defer 至 post-merge**，Owner 配合执行并回填 #326。

### 6.3 Stage 11 tie-in

- 反向扫描：Handoff 中立化不改任何函数/路径/表名——不触发 5 类反扫；`SKILL_INDEX.md` 不含 Handoff 出边陈述（核对即可）；gates.md V9 行与 ci.yml 注释的 0E/4W 陈述由 8b/8g 消化
- scope-drift 预期：Severity ≤ Minor（文件清单已闭合；新增 = 1 生成器 + 1 测试 + 7 产物文件 + 2 plans）

## 7. 完成标准（AC）

- [ ] 4 条集外出边中立化 + 2 个 Handoff 标题中性化；V9 真实树 `--all` 0E/0W（PR-A）
- [ ] `agents_sync.py sync` 幂等；`--check` drift 三态正确且文案给规定动作；`--adopt` 反灌可用并提示 HITL
- [ ] `.agents/skills/` ×5 + `.agents/README.md` + `.agents.lock.json` 同 commit 入仓；lock 哈希与 V9 `check_lock` 互认（V9 集成测试）
- [ ] golden-file 跨 EOL 单测绿（Windows 本机）+ GitHub CI（ubuntu）绿 = §11.1 双平台证据
- [ ] reconcile 负向用例（孤儿清理 / 多出文件 FAIL）单测绿
- [ ] CI drift step（warning 姿态）接入 + gates.md V10 注册 + adapters doc 登记
- [ ] 根 AGENTS.md 投影契约条落地
- [ ] 每 PR Level A 全绿；2 PR 依序 merge（A 先合 `--delete-branch` → 核对 B baseRefName → 合 B）；#326 关闭；#312 S1 行勾选 + 晋级证据回填
- [ ] post-merge follow-up：两 plans state flip（另开小 PR）+ Codex 实机发现验证（Owner trust 配合）回填 #326

## 8. 关联

- Issue: #326（本切片）/ #312（总锚）
- 目标文件：`.claude/skills/mj-agent-flow-diagnose/SKILL.md` · `.claude/skills/mj-agent-git-delete/SKILL.md` · `.claude/skills/mj-agent-git-push/SKILL.md` · `scripts/sdd/agents_sync.py`〔新〕· `.agents.lock.json`〔新〕· `.agents/skills/mj-agent-{flow-diagnose,git-commit,git-push,git-sync,git-delete}/SKILL.md`〔新〕· `.agents/README.md`〔新〕· `tests/unit/test_agents_sync.py`〔新〕· `tests/unit/test_sdd_development_agent.py`（docstring）· `.github/workflows/ci.yml` · `AGENTS.md` · `sdd/gates.md` · `sdd/adapters/development-agent.md` · plans 2 件〔新〕
- 不动文件：`src/mj_agent/**` · `sdd/development-agent.yml`（全 5 方案零改动）· `.mcp.json` · `.claude/settings.json` · 冻结 8 `infra-*` SKILL.md · `config/secrets*.enc` / `.env` · `.gitattributes` · `archive/**`
- 后续独立 PR / 议题：S2（3 spikes + emitter B + MCP gate day-1 blocking）；S3（doctor + blocking 转正 + 两项独立拍板议题）；plans state flip 小 PR；#312 递延 4 议题
