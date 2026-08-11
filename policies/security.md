---
type: policy
artifact: security
state: draft
version: 0.2
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-11
track: shared
ai_visibility: source-of-truth
---

# Policy: Security

> secret 暴露 gate（§1）+ 漏洞 exception（§2 — **DECLINED**，无输入源）+ 2-bundle secrets
> 信任边界（§3）+ 跨仓 attribution 禁止规则（§4）。**本文件不再有待填充节**（v0.2）。

## §1 Secret 暴露 Gate（G7 — completion-audit PR2 实装）

`scripts/sdd/check_secret_exposure.py`（warning@ci；blocking flip 另走
`ci-blocking-gate-toggle` HITL）。**语义修正**（原 M0 skeleton TBD 措辞反了）：禁止入
git / image 的是**解密产物** — `.env` / `config/secrets*.conf` / `*.pem` / `*.key`；
`config/secrets.enc` / `config/secrets-mcp.enc` **密文 bundle 按 ADR-030 有意入库**，不在
禁止面。三项静态检查（CI 无 secrets 可跑）：

1. **tracked-files（FAIL）**：`git ls-files` 不得含 `.env` / `.env.*`（`.env.example` 除外）/
   `config/secrets*.conf` / `*.pem` / `*.key`。
2. **.gitignore 钉子（WARN）**：`.env` / `config/secrets.conf` / `config/secrets-mcp.conf`
   三条 ignore 必在。
3. **docker build-context（WARN）**：`docker/Dockerfile` 的 `COPY config/` + DEV compose
   `context: ../`（仓根）→ 根目录 `.dockerignore` 必须存在**且覆盖** `config/secrets*.conf`
   （`docker/.dockerignore` 对仓根 context 无效；空文件 / 无覆盖同样 WARN）。根目录
   `.dockerignore` 已 owner-approved 落地（2026-06-11 completion-audit follow-up）——
   本地解密产物自此物理上进不了 DEV image。

明文密码 / token / API-key pattern 的 active 文件内容扫描（原 TBD 第二句）不在 G7 静态
范围 — 依赖 secret-pattern 启发式，误报面大；→ Phase-2 与 EVAL evidence harness 一并评估。

## §2 漏洞 Exception 处理流程

> **Decision（2026-08-11；#482 `M6-FU-POLICIES-TBD-SWEEP`）**：原 skeleton 诉求
> "CVE / dependency vulnerability 的 exception 申请流程；ADR + 时限" **DECLINED — 不写**。
>
> 理由：**该流程当前没有任何输入源**。2026-08-11 实测仓库 `security_and_analysis`：
> `dependabot_security_updates` = **disabled**；Dependabot **alerts** = disabled
> （REST 返回 403 `Dependabot alerts are disabled for this repository`）；
> `secret_scanning` / `secret_scanning_push_protection` / `_validity_checks` 全 **disabled**。
> 仓内无 `.github/SECURITY.md`；`.github/dependabot.yml` 只配 **version updates**
> （`github-actions` / `docker` / `docker-compose` 三个 ecosystem，weekly，`target-branch:
> develop`），**不产生 CVE 告警**。给一条没有入口的路写审批规则，正是本 sweep 要消除的那类
> 失真——文档会教人走一条不存在的流程。处理姿态同 §1 尾段（把 pattern 扫描如实划到 G7 范围
> 外）与 `policies/git-branching.md` §1/§2 的 DECLINED 先例。
>
> **复活条件**（任一即重开）：(a) 仓库启用 Dependabot security updates 或 alerts；
> (b) 任何 SCA / 漏洞扫描工具进 CI；(c) 首次出现需要豁免决策的真实 CVE。届时由 owner 开 ADR
> 定义 **申请人 / 批准人 / 时限 / 记录位置** 四要素。
>
> **本块不代为决定安全姿态**："是否启用 Dependabot alerts" 属仓库设置面的独立决策（owner
> 域），本块只如实记录"当前未启用，故流程无输入源"这一事实。

## §3 2-Bundle Secrets 信任边界（per ADR-030）

| Bundle | 解密范围 | 用途 |
|---|---|---|
| `config/secrets.enc`（app bundle） | 6-8 keys：`POSTGRES_ANALYST_USER/PASSWORD` / `ARK_API_KEY` / `LLM_API_KEY` / `LANGSMITH_API_KEY` / `MJ_AGENT_MEMORY_USER/PASSWORD` | 写入 `.env`；Python runtime + docker compose 读取 |
| `config/secrets-mcp.enc`（MCP bundle） | 15 keys：5 SSH passwords + 10 PG URL overrides | 写入 OS User-level env（HKCU\Environment）；bypasses `.env`；Claude Code MCP server 启动时读取 |

**信任边界**：两 bundle 用同一 team password（AES-256-CBC + PBKDF2），但解密 destination
不同 → MCP 路径污染不会影响 app runtime.

## §4 跨仓 Attribution 禁止规则

mj-agent 的文档治理框架在 bootstrap 阶段曾参考上游业务仓库的实践；解耦已于 2026-05-11 完成
（`plans/[PLAN]_cross_repo_decoupling_cleanup.md`）。此后下列 4 条长期生效：

1. **prose 一律用"上游业务系统" / "上游业务仓库"**，不写上游仓名 literal。
2. **frontmatter 禁 `derives_from`**；lineage 只用 `supersedes` / `superseded_by`
   （per `policies/documentation.md` §6）。
3. **attribution 走 glossary 元文档**：需要归属上游时链到
   `docs/glossary/upstream_business_warehouse.md`（`GLOSSARY.md` 是全项目术语索引入口，
   专题深度词典在 `docs/glossary/`）；main / develop / SHA 的选择规则写在该 glossary 内，
   不在各文档就地重复。
4. **代码层 literal 保留**：docker external network 名、`MJ_AGENT_PG_BIZ_*` env 命名空间、
   MCP server id 等是**真实部署对象的精确引用**，不在禁止面——改写它们会让配置失效。

### §4.1 执行机制（实测 2026-08-11）

| 规则 | 载体 | 实际姿态 |
|---|---|---|
| 规则 2（`derives_from`） | `scripts/check_frontmatter.py` `FORBIDDEN_FIELDS` | **BLOCKING**（ci.yml 该 step 无 `continue-on-error`） |
| 规则 1 / 3 / 4 | `scripts/check_no_cross_repo_refs.py`（ci.yml step `No cross-repo refs (forward guard)`） | **warning**（姿态由脚本控制，见 §4.2） |

**两个 gate 的覆盖面各有边界，都不是全仓**：

- 规则 2 —— `check_frontmatter.py` 的 `SCAN_ROOTS` = `docs/` `plans/` `decisions/`
  `src/mj_agent/{skills,prompts}`。**`policies/` `sdd/` `capabilities/` `config/` `.github/`
  不在内**：这些目录的 frontmatter 若回写 `derives_from`，无 gate 拦截，须人工核。
- 规则 1/3/4 —— 扫 `docs/**/*.md` + 仓根 `CLAUDE.md` + `README.md`；**跳过**
  `docs/archive/**`（冻结快照；active 归档规约见 `policies/archive.md` —— 脚本 docstring
  里的 `ADR-019` 归因已随该 ADR superseded 到 `archive/decisions/superseded/` 而过时）、
  `CHANGELOG.md`（Keep-a-Changelog 不改历史）、
  in-source canonical（`src/mj_agent/skills/**/SKILL.md` + `prompts/*.md` —— 那是 runtime
  LLM 上下文，另由 runtime 契约治理）、以及 glossary 本身（它有意定义上游关系）。
  **`policies/` `sdd/` `decisions/` `plans/` `AGENTS.md` 同样在扫描面外**。

### §4.2 姿态由脚本控制 —— 与其他 gate 不同型

ci.yml 的 `No cross-repo refs` step **没有** `continue-on-error`，但脚本默认 warning-mode
（打印 findings 到 stderr 后 `exit 0`），所以实际永不阻塞。**flip 到 blocking 不是改
`continue-on-error`**，而是给该 step 加 `MJ_AGENT_CHECK_REFS_STRICT=1`。

该 gate **未在 `sdd/gates.md` 登记**（2026-08-11 两种口径实测零命中；对照 `find_stale_docs`
有 4 处登记）。故若将来追求 blocking，须**先补登记**再走 `ci-blocking-gate-toggle` 拍板
（per `policies/ci-gates.md` §4.1.1 —— 未注册者不享 streak 吸收）。脚本 docstring 记载其
原 "4-week-to-blocking" note 已由 #440 retired，warning 是当前姿态而非过渡态。

**当前残留**：**15 warnings / 11 文件**（2026-08-11 实测）—— `CLAUDE.md` · `README.md` ·
`docs/INDEX.md` · `docs/guide/` 4 份 GUIDE · `docs/infrastructure/git/` 4 份 GUIDE。
清理无日程绑定。

## §5 与其他 policy 联动

- `policies/data-boundary.md` §3 4 项专属必停 — secret 红线在 sql-guardrail / catalog 中的
  落地
- `policies/docker-runtime.md` §1 Image 红线 — secret 禁入 image
- `policies/ci-gates.md` §Settings 边界 — `permissions.deny` 红线列表

---

> *`state: draft` — §1·§3·§4 是 live SoT，§2 为 DECLINED 决策块（本文件不再有待填充节）。*
>
> *v0.2（2026-08-11）：#482 — 处置本文件在 `M6-FU-POLICIES-TBD-SWEEP` 中的 2 个 TBD 块。
> **§2 DECLINED**：CVE / dependency vulnerability exception 流程当前无任何输入源 —— 实测
> `dependabot_security_updates` / Dependabot alerts / `secret_scanning` 系列全 disabled，
> 无 `.github/SECURITY.md`，`dependabot.yml` 只配 version updates；写审批流程给不存在的入口
> 正是本 sweep 要消除的失真，故按 `git-branching.md` §1/§2 先例记 Decision + 复活条件，
> 并显式声明本块不代为决定"是否启用 alerts"这一 owner 域安全姿态。**§4 摘 TBD 壳并真值化**：
> 块内 4 条正文本已写全（cross-repo 解耦 2026-05-11 已完成），本次改为正式规则陈述，并把
> 原指向 AI 私有 memory 的出处改指仓内 `plans/[PLAN]_cross_repo_decoupling_cleanup.md`。
> 新增 §4.1/§4.2 两个子节记录**从实现取证**的执行机制。**三处如实修正**：(a) 原文"残留
> ~90 warnings"是陈旧数字，实测 **15 warnings / 11 文件**；(b) 规则 2 的 `derives_from`
> 禁令有 `check_frontmatter.py` `FORBIDDEN_FIELDS` 的 BLOCKING 背书（已验 `plans/` 内的
> `derives_from` 全是"提及"非"使用"，`OK: 136` 全绿），但其 `SCAN_ROOTS` 不含 `policies/`
> `sdd/` `capabilities/` `config/` `.github/`；(c) `check_no_cross_repo_refs` 的 warning
> 姿态**由脚本内部控制而非 `continue-on-error`**（该 step 根本没有这个键），且该 gate
> **未在 `sdd/gates.md` 登记** —— flip 到 blocking 须先补登记、且改的是
> `MJ_AGENT_CHECK_REFS_STRICT` 而非 `continue-on-error`。`state` 不动：内容填充 + decline
> 决策不构成 live-kernel-home 意义上的操作必要性（per #480 / `sdd/lifecycle.md` §4.1）。*
