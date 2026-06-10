---
type: policy
artifact: security
state: draft
version: 0.1
owner: ranzuozhou
created: 2026-05-20
updated: 2026-06-10
track: shared
ai_visibility: source-of-truth
---

# Policy: Security

> Phase M0 skeleton — secret 暴露 gate + 漏洞 exception + 2-bundle secrets 信任边界 + 跨仓
> attribution 禁止规则. 详细内容在 Phase M2 内容填充.

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
   `context: ../`（仓根）+ 根目录无 `.dockerignore` → 本地解密过的 `config/secrets*.conf`
   会被打进 DEV image（`docker/.dockerignore` 对仓根 context 无效）。已知 gap 如实 WARN；
   是否补根目录 `.dockerignore` 是 owner 决策项。

明文密码 / token / API-key pattern 的 active 文件内容扫描（原 TBD 第二句）不在 G7 静态
范围 — 依赖 secret-pattern 启发式，误报面大；→ Phase-2 与 EVAL evidence harness 一并评估。

## §2 漏洞 Exception 处理流程

> TBD: Phase M2 — CVE / dependency vulnerability 的 exception 申请流程；ADR + 时限.

## §3 2-Bundle Secrets 信任边界（per ADR-030）

| Bundle | 解密范围 | 用途 |
|---|---|---|
| `config/secrets.enc`（app bundle） | 6-8 keys：`POSTGRES_ANALYST_USER/PASSWORD` / `ARK_API_KEY` / `LLM_API_KEY` / `LANGSMITH_API_KEY` / `MJ_AGENT_MEMORY_USER/PASSWORD` | 写入 `.env`；Python runtime + docker compose 读取 |
| `config/secrets-mcp.enc`（MCP bundle） | 15 keys：5 SSH passwords + 10 PG URL overrides | 写入 OS User-level env（HKCU\Environment）；bypasses `.env`；Claude Code MCP server 启动时读取 |

**信任边界**：两 bundle 用同一 team password（AES-256-CBC + PBKDF2），但解密 destination
不同 → MCP 路径污染不会影响 app runtime.

## §4 跨仓 Attribution 禁止规则

> TBD: Phase M2 — cross-repo decoupling cleanup 延续（per memory
> `project_cross_repo_decoupling_completion`）：
> - prose 用"上游业务系统" / "上游业务仓库"
> - frontmatter 禁 `derives_from: mj-system`
> - mj-system attribution 用 wikilink 到 `GLOSSARY.md` / `docs/glossary/
>   upstream_business_warehouse.md` 元文档（main/develop/SHA 选择规则在 glossary 内）
> - 代码层 literal（`mj-system-backend-network` / `MJ_AGENT_PG_BIZ_*`）保留作真实部署对象的
>   精确引用

forward guard：`scripts/check_no_cross_repo_refs.py`（warning mode active；残留 ~90
warnings 待 Phase E+ 清理）.

## §5 与其他 policy 联动

- `policies/data-boundary.md` §3 4 项专属必停 — secret 红线在 sql-guardrail / catalog 中的
  落地
- `policies/docker-runtime.md` §1 Image 红线 — secret 禁入 image
- `policies/ci-gates.md` §Settings 边界 — `permissions.deny` 红线列表

---

> *Phase M0 skeleton — `state: draft`. Phase M2 内容填充.*
