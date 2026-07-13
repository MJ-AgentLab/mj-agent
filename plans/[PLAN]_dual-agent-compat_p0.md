---
type: plan
summary: 双工具兼容 v5 P0 执行计划（issue #313）——四组安全冲突消除 + 口径收敛，stacked 3-PR 链；含 Stage 3 repo-scan 增量与 4 项 Owner 拍板决策（教学面收敛/G1 regex 收紧/owner_approval_required 改名/Bash 白名单开发常用档）
owner: ranzuozhou
created: 2026-07-13
updated: 2026-07-13
state: active
track: shared
---

# [PLAN] 双工具兼容 v5 — P0 执行计划（issue #313）

## 1. Linked Artifacts

- Issue: #313（P0 执行）· 总锚 #312 · Program plan: [[[PLAN]_dual-agent-compat|v5 计划]]（§5 四组冲突 / §8.1 变更矩阵 / §11.1 晋级条件）
- Intake: [[[INTAKE]_dual-agent-compat_p0|Stage 0 Intake]]（2026-07-13）
- Repo Scan: Stage 3 对话输出（2026-07-13，6 维并行扫描；证据行号以 develop @ `2da5676` 为基准）
- 关联 ADR：[[../decisions/ADR-034_HITL_Propose_Decide_Apply_Model|ADR-034]]（hook/审批语义的上一次变更）· [[../decisions/ADR-035_Codex_Full_Development_Participant|ADR-035]]（双工具授权基础）· ADR-036 留 P1/S0 立
- Owner 拍板记录（2026-07-13，Stage 0 + Stage 3 共 7 项）：
  1. 总锚 issue + P0 issue + stacked 3-PR 链
  2. v5 port 为 `plans/[PLAN]_dual-agent-compat.md`
  3. ADR-036 留 P1/S0 期立
  4. **P0 只收教学面**——settings `mcp__pg-mj-system-biz-*`×5 allow 不动；权限收窄另登记议题（与 S2 MCP 面同期评估）
  5. **G1 regex 绕过 PR-2 顺手收紧**（`git checkout -q -b` / `git -C dir checkout -b` / `git checkout <ref> -b`）
  6. adapter schema 字段 `read_only_by_design` → **改名 `owner_approval_required`**（无 yml 实例，纯 spec 文本迁移）
  7. 裸 `Bash` 白名单取**开发常用档**（`Bash(git *)` / `Bash(gh *)` / `Bash(uv *)` / `Bash(python *)` / `Bash(rg *)` / `Bash(ls *)`；其余逐次提示）

## 2. Context

v5 已 Owner 拍板；§11.1 规定 P0 是 P1 的硬前置——四组冲突关闭前不得宣称双工具兼容。Stage 3 扫描核验 v5 §3 全部差距为真，并发现计划文本低估的 4 处改动面：① `TEMPLATE_REPO_SCAN_RESULT.md:58` 与 flow-repo-scan 强耦合（模板同教 `mcp postgres-*`）；② infra 读 env 面远宽于一句话（env-setup 有整张授权 Agent 读 .env 的边界表；probe 有 4 处残余读面）；③ runtime×4 body 已 ADR-034 化，read-only 残留实际在 6 处派生文档；④ 12→10 的最深漂移在 `[GUIDE]_MJ_Agent_SPEC_Authoring.md` §6 整段编号体系。

风味判定：P0 全程不触 `src/mj_agent/**`（无 B 风味），全部为 C（工程编排 skill / hook / settings / CI / 治理文档）。§3.1 必停 4 项（trigger 10-13）均不触发；High 风险来自 `.claude/**` 保护面、冻结 skill re-freeze、CI/模板口径与 hook 行为变更。

## 3. Scope

- 包含：v5 §8.1 矩阵 P0 行全部 + Stage 3 增量（模板、GUIDE、6 处 read-only 派生残留、G1 regex 收紧、Bash 白名单）
- 不包含：manifest / checker / 嵌套 AGENTS.md（P1）；投影生成器与 `.agents/`（S0/S1）；Codex 实机验证（P2+）；`src/mj_agent/**`；`.mcp.json`；settings biz MCP allow 收窄（另登记议题）；`tests/fixtures/development-agent/scenarios/S1-S6`（v5 §12 双工具 fixture，属 P1/P2——P0 只建四组冲突的负向/文案 fixtures）
- 前置依赖：无（P0 是链首）；PR-2 base = PR-1 分支，PR-3 base = PR-2 分支（stacked）

## 4. 任务拆解（Stage 8 编号 · 全部风味 C）

### PR-1 `maintain/313-dual-agent-compat-p0`——数据/secrets 边界 + plans 落盘

- **8a fixtures 先行（RED）**：新建 `tests/unit/test_dual_agent_compat.py`——真实仓文件内容断言（先例 `test_sdd_g21_evidence_predicate.py:341-368`）：
  - 禁止串：`flow-repo-scan/SKILL.md` 与 `TEMPLATE_REPO_SCAN_RESULT.md` 不含 `mcp postgres` 教学指引；infra 3 skill 不含 Agent 读 `.env` / `$env:LLM_API_KEY` 指令（精确到教学语句，放过 `--env-file .env` 等 docker 进程用法）
  - 必需串：flow-repo-scan 含 4-tool 链指引；infra 3 skill 含 sanitized 脚本指引
  - 提交时序：8a 先 commit（测试 RED，CI 允许单 commit 红）或 8a 与 8b-8d 同 PR 分 commit 呈现 red→green——采用**同 PR 分 commit**（先 test commit 后 fix commit），满足 §11.1「均有失败 fixture，修正后同一 fixture 通过」
- **8b flow-repo-scan 去 biz 直连**（4 处 + 模板 1 处）：
  - L108：工具列 `mcp postgres-* / Read qcm_catalog` → 4-tool 链（`uv run python` 调 `find_biz_context`/`list_biz_tables`/`describe_biz_table` 的可执行载体示例）+ `Read qcm_catalog`
  - L109：拆格——biz 侧 4-tool 链；memory 侧（mj-agent-postgres checkpointer）单独标识，保留 `mcp pg-mj-agent-memory-*` / `docker compose exec psql` 载体（非本次去除对象）
  - L115 硬规则：`mcp postgres \d+` → `describe_biz_table`
  - L291 工具表：替换 + 环境隔离重述为 env-guard（`.env` biz DSN 指向 prod 时禁 `execute_sql` 采样、仅 describe；兜底 = analyst RO + L1/L1b + statement_timeout）
  - L239 Evidence Map 行拆 biz / memory
  - `docs/_templates/TEMPLATE_REPO_SCAN_RESULT.md:58` 同步（同一改法）
- **8c infra-env-setup 去 Agent 读 env（整组同改）**：L43-51 边界表（Step 1/3 改「User or sanitized script」）、L59-66 Bash-读-.env 段、L136-164 Step 3 代码块（改为调用 sanitized 脚本）、L249-256 工具表、L280-286 Output Format；新建 `scripts/check_env_keys.ps1`（读 .env 判键存在性，仅输出键名 + present/missing 布尔，永不输出值；供任一工具/用户调用）——或复用 `uv run mj-agent check` 既有缝，二者取舍在 Stage 8 按最小新缝原则定（优先复用 `mj-agent check`，仅当其覆盖不足时建新脚本）
- **8d infra-llm-endpoint-probe + infra-docker-compose**：
  - probe：Step 0（L42-54）/ L89 / L104+L153（`$env:LLM_API_KEY` curl）/ L242 工具表 / L182 输出——探针执行体改为新脚本 `scripts/probe_llm_endpoint.ps1`（脚本内部读 env 并发起请求，向调用方仅返回 PASS/FAIL + 脱敏诊断），skill 正文只指挥跑脚本
  - docker-compose：仅 L106-110（Agent `Get-Content .env`）改 sanitized 缝 + L264 输出行改口；**全部 `--env-file .env` 保持不动**（docker 进程解析，非 Agent 读取）
- **8e 冻结 re-freeze（3 条目）**：按 contract header canonical algo（regex-strip frontmatter count=1 + LF-norm + sha256 UTF-8；description 走 native-parser 非 yaml）——**先复现 3 个旧 hash 证 algo 再记新值**；body_section_heads 按 NAIVE 扫描重算（含 fenced 块内 `##` 伪标题）；bump `frozen_at`；⚠️ 不得直接调 `body_sha256()`（3 个 description 含内嵌冒号会 yaml 炸、哈希整文件）
- **8f plans 落盘**：`[PLAN]_dual-agent-compat.md`（v5 port）+ 本文件 + `[INTAKE]_dual-agent-compat_p0.md`（本 PR 携带）

### PR-2 `maintain/313-dual-agent-compat-p0-pr2`——HITL 中立化 + Git guard + hook fail-closed + settings

- **8g hook fixtures 先行（RED）**：新建 `tests/unit/test_guard_git_workflow_hook.py`（subprocess 跑 `pwsh -NoProfile -File .claude/scripts/guard-git-workflow.ps1`，`shutil.which("pwsh")` 缺失即 `pytest.skip`；先例 `test_g24_live_exercise.py:21-52`）：
  - 正向（现状 GREEN，回归钉）：`git checkout -b x` → exit 2；`git switch -c x` → exit 2；`gh pr create` 无 `--base` → exit 2；合法命令（`git status`）→ exit 0；`gh pr create --base develop` → exit 0
  - 负向输入协议（现状 RED → 8h 后 GREEN）：非 JSON stdin → exit 2；空 stdin → exit 2；JSON 缺 `tool_input.command` → exit 2；未知 schema（无 `tool_name`/`hook_event_name`）→ exit 2
  - G1 绕过（现状 RED → 8h 后 GREEN）：`git checkout -q -b x` / `git -C dir checkout -b x` / `git checkout main -b x` → exit 2
- **8h guard-git-workflow.ps1 fail-closed 重写**：
  - stdin 协议：非 JSON / 空 / 缺 `tool_input.command` / 缺 `tool_name`+`hook_event_name` → stderr 结构化诊断 + exit 2；L21「never block」注释改为 fail-closed 设计声明
  - top-level try/catch → exit 2 兜底（脚本内部异常不再静默放行）；settings hooks 段评估显式 `timeout`（超时行为属 harness 语义，PR body 记录残余风险，不在脚本内可解）
  - G1 regex 收紧（拍板项 5）：允许 `checkout` 与 `-b` 间插入选项/引用（如 `git\s+(-\S+\s+)*checkout\s+.*-[bB]\b` 类形式，Stage 8 以测试驱动细化）；G2 保持
  - stderr 指引工具中立：在 CLAUDE.md 之外并列 `AGENTS.md` + `policies/git-branching.md`
- **8i runtime×4 审批中立化**：共享停点统一表述为 `OWNER_APPROVAL_REQUIRED`，随后给 per-harness 载体映射——Claude Code = AskUserQuestion + settings `ask` prompt（现文保留为载体注脚）；Codex = AGENTS.md 自守 prose（引用 §5.3）；eval-baseline 单载体（无 ask 门）不得机械复制「二次批准」句式。改动位置（Stage 3 已定位）：biz-catalog-sync L3/10/19/62/192-198/240-242/266-268/287/299；prompt-version-bump L3/10/19/64/212-218/276/299-301/318/331；skill-doc-improve L3/10/19/61/183-189/232/255-257/271/282；eval-baseline L3/10/20/73/269-275/339/348/365-367/388/403
- **8j AGENTS.md 双工具化（最小面）**：L11-12 定位改双工具共享契约；L18/27 Primary → full-responsibility peers；L31-33 「ask 门只绑 Claude」改为「Claude harness 门 + Codex AGENTS.md 自守，同一 canonical 停点」；L49-51 Codex 边界补 G1 worktree / G2 PR-base 纪律；L79-80 双契约分裂句改单源 Kernel 表述；L102/107-110 Path-B deferred 措辞保留（D-006）。全面叙事重构留 P1（嵌套 AGENTS.md 同批）
- **8k settings.json**（拍板项 7；窄化，agent 可提交；写入时权限 prompt 即拍板）：移除裸 `"Bash"`，加入 `Bash(git *)` / `Bash(gh *)` / `Bash(uv *)` / `Bash(python *)` / `Bash(rg *)` / `Bash(ls *)`；裸 `Edit`/`Write`/`Read` 不动（本切片外）；deny/ask 全部不动
- **8k-2 hook 行为描述反扫**：`policies/data-boundary.md:78-83`、`sdd/gates.md:83`、`CONTRIBUTING.md:63`、`GLOSSARY.md:133`、`policies/git-branching.md:71`、`[GUIDE]_Developer_Onboarding.md:241`、`mj-agent-git-{branch,pr}/SKILL.md` 引用段——仅在陈述变假处最小更新（fail-closed 语义 + 白名单化）

### PR-3 `maintain/313-dual-agent-compat-p0-pr3`——口径收敛 + fixtures 收口

- **8l PR 模板对齐 canonical**：L57 「12 项场景」→「10 项 canonical enum」；Trigger Inventory（L61-73，现 11 行）行名对齐——`prompt-version-bump`→`prompt-version-or-body-change`、`cross-capability contract change`→`declared-contract-change`、`.mcp.json 新增 server`→`mcp-server-trust-posture-change` 全集、L71+L72 并入 `bulk-content-purge-or-migration` / `secrets-grants-or-prod-config` 对应行（收敛为 10 行与 canonical 一一对应）
- **8m GUIDE + kernel 名称收敛**：`[GUIDE]_MJ_Agent_SPEC_Authoring.md` L209-217 整段重写对齐 canonical 10-enum（弃「12 通用+4 专属」编号体系）；`sdd/workflows/execution-loop.md:216` 括注 stale 名 `prompt-version-bump` → `prompt-version-or-body-change`（kernel 编辑，A 门适用）
- **8n read-only 叙事清理（6 处）**：`policies/claude-code-skill.md` §4（L33-39 重写：read-only→propose→拍板→apply + 「deny-list 三重保险」→ask 门）；`CLAUDE.md:159-160`（sync-allowlist §7 核对）；`docs/INDEX.md:237,259`（只改措辞，L259 的 37 计数句勿动）；`sdd/adapters/claude-code-skill.md` L106-107 字段改名 `owner_approval_required`（拍板项 6）+ L187-188 + L208 同步；`.github/ISSUE_TEMPLATE/agent.md:41`；`SKILL_INDEX.md` L97-99「（read-only）」标注 + L129-130 Anti-patterns
- **8o 计数收敛**：`sdd/adapters/claude-code-skill.md:27` 35→37（L143-156/244 的 34 = M2 历史观察，不改）；`ci.yml:144` gate label 去数字化（`34P/0W/0F clean` → 不含计数的表述；**不动 continue-on-error**，非 blocking-flip）；核对 `biz-catalog/runbook.md:237` 历史引述标注仍成立、G21/G22 keyword check 不受影响；SKILL_INDEX flow 行 9 vs on-disk 10 维持既登记 M-FU defer
- **8p flow-implement 硬编码清理 + 收口**：L289 删除（Reference Files 其余 8 条自洽）；L238-241 Source 列「user-global ~/.claude/」中立化为「外部插件（可选）」；L21/285 mj-system attribution 引用保留（跨仓 attribution 非可执行路径）；全部 fixtures GREEN 确认 + 12→10/35 误伤排除集复核（`execution-loop:226`、`Commit Convention:59,134`、`git-commit:90`、`flow-self-review:187,290`、`ADR-014:36,224` 不改）；§11.1 P0→P1 晋级证据汇总回填 issue #313

### Documentation Decision（§7.1 摘要；完整 10 行表见 Stage 3 输出）

Plan=Create（本 3 件，PR-1）；GUIDE=Update（SPEC_Authoring §6，PR-3）；INDEX=Update（docs/INDEX + SKILL_INDEX 措辞，PR-3）；SPEC/ADR/RUNBOOK/STANDARD/Local ISSUE/ASSESSMENT/CHANGELOG=None。

## 5. 风险（Risk Level: High）

| 风险 | 等级 | 风味 | 缓解 / Rollback |
|---|---|---|---|
| re-freeze hash 算错（yaml 炸 / naive section heads 漏 fenced `##`） | High | C | 先复现 3 个旧 hash 证 algo 再算新值（#304/#306 先例）；CI 不校验 hash——PR body 附人工复算记录；rollback = revert contract 条目 |
| hook fail-closed 误伤合法调用（手动跑脚本 / 空管道 exit 2） | Medium | C | 按 v5 §5.4 口径接受（stderr 诊断给出原因）；hook 仅挂 Claude PreToolUse，人工 shell 不受影响；G1 regex 收紧以测试驱动，正向 case 钉住不误拦 |
| docker-compose `--env-file` 被误删致变量注入全断 | High | C | 8d 显式「不动」清单 + 8a 测试放行 `--env-file`；rollback = revert |
| 裸 Bash 移除后提示量上升 / 白名单遗漏 | Low | C | 开发常用档 6 条前缀；遗漏项个人可经 settings.local.json 补充；观察一周再评估追加 |
| 12→10 / 35→37 全仓替换误伤自洽计数 | Medium | C | 排除集已固化（§4 8p）；逐处人工改，不做盲替 |
| `.claude/**` 逐写权限 prompt 中断流 | Low | C | 交互模式逐文件拍板即 HITL 本体（ADR-034）；classifier 拦截时按既往经验把该文件改动交 Owner 自行落盘 |
| ci.yml gate label 改动被误判 blocking-flip | Low | C | 仅动 name 字符串不动 `continue-on-error`；PR body 显式声明非 `ci-blocking-gate-toggle` |

## 6. 验证

### 6.1 Stage 10 Level A（只读 / 必跑，每 PR）

```
uv run ruff check
uv run mypy src/mj_agent
uv run pytest tests/unit tests/eval -q
python -m compileall src
uv run python scripts/check_wikilinks.py
uv run python scripts/check_frontmatter.py
uv run python scripts/sdd/check_claude_skill_contracts.py --all   # 37/37 PASS（Mode-A）
```

- PR-1 附加：re-freeze 人工复算记录（旧 hash 复现 + 新 hash + section_heads diff）
- PR-2 附加：hook 测试矩阵全绿（正向 5 + 负向 4 + 绕过 3）
- PR-3 附加：`rg -n 'mcp postgres' --glob '!archive/**'`（教学面仅剩豁免命中）、`rg -n '\b34P\b'`（仅历史文件）、误伤排除集逐条 spot-check

### 6.2 Level B

无（P0 无运行时行为变更，不需 DB/LLM/compose）。

### 6.3 Stage 11 tie-in

- 反向扫描：hook 行为描述 8 文件（8k-2 清单）、3 skill 名引用面（SKILL_INDEX / INDEX / Onboarding）
- scope-drift 预期：Severity ≤ Minor（文件清单已闭合；新增文件仅 2 测试 + ≤2 脚本 + 3 plans）

## 7. 完成标准（AC）

- [ ] §5 四组冲突各有失败 fixture 且修正后同一 fixture 通过（red→green commit 序可查）
- [ ] hook 负向 4 类 + G1 绕过 3 类 → 非零退出；正向 5 类不误拦
- [ ] flow-repo-scan + 模板无 raw biz PG 教学；infra 3 skill 无 Agent 读 env 指令；memory PG 单独标识
- [ ] 3 个冻结条目 re-freeze（旧 hash 先复现），`check_claude_skill_contracts.py --all` 37/37
- [ ] PR 模板 = canonical 10；GUIDE §6 对齐；read-only 残留 6 处清零；`owner_approval_required` 改名落地
- [ ] 35→37 / 34P 收敛且误伤排除集未被改动
- [ ] settings：裸 Bash 移除 + 6 条前缀白名单（deny/ask 不动）
- [ ] 3 PR 全部 CI 绿 + Owner review + merge；#312 P0 勾选 + #313 关闭
- [ ] `[PLAN]_dual-agent-compat_p0.md` 与 `[INTAKE]` state flip completed（post-merge）

## 8. 关联

- Issue: #313（本切片）/ #312（总锚）
- 目标文件：`.claude/skills/{mj-agent-flow-repo-scan,mj-agent-infra-env-setup,mj-agent-infra-docker-compose,mj-agent-infra-llm-endpoint-probe,mj-agent-runtime-*×4,mj-agent-flow-implement}/SKILL.md` · `.claude/skills/SKILL_INDEX.md` · `.claude/scripts/guard-git-workflow.ps1` · `.claude/settings.json` · `docs/_templates/TEMPLATE_REPO_SCAN_RESULT.md` · `.github/PULL_REQUEST_TEMPLATE.md` · `.github/workflows/ci.yml` · `.github/ISSUE_TEMPLATE/agent.md` · `AGENTS.md` · `CLAUDE.md` · `policies/claude-code-skill.md` · `sdd/adapters/claude-code-skill.md` · `sdd/workflows/execution-loop.md`（L216 名称括注）· `docs/INDEX.md` · `docs/guide/[GUIDE]_MJ_Agent_SPEC_Authoring.md` · `capabilities/infrastructure/mcp-server-governance/contracts/claude-skill.contract.yml` · 新增 `tests/unit/test_dual_agent_compat.py` / `tests/unit/test_guard_git_workflow_hook.py` / `scripts/probe_llm_endpoint.ps1`（视 8c 取舍 ± `scripts/check_env_keys.ps1`）· plans 3 件
- 不动文件：`src/mj_agent/**`（含 4 必停面）· `.mcp.json` · `config/secrets*.enc` / `.env` · settings deny/ask 段 · `archive/**` · 历史 plans/evidence 引述
- 后续独立 PR / 议题登记：P1+S0（manifest/checker/嵌套 AGENTS.md/ADR-036）；settings biz MCP allow 收窄（S2 同期评估）；SKILL_INDEX flow 行回填（既有 M-FU）；hook timeout harness 语义（PR-2 body 记录）
