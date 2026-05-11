---
type: plan
summary: Dockerfile FROM 回退 python:3.13-slim (digest d49c1ff8...) + ENV UV_PYTHON_PREFERENCE=only-system，解 uv-managed Python symlink 在 runtime stage 链断的 pre-existing image build bug (PR #131 Stage 17 暴露的 mj-agent crash exit 126)
owner: ranzuozhou
created: 2026-05-11
updated: 2026-05-11
state: active
track: code
---

# [PLAN] Dockerfile Python 3.13 baseline restore + uv-only-system

> 单 PR bugfix：Dockerfile FROM 从 `python:3.14-slim` 回退 `python:3.13-slim`（与 pyproject `requires-python=>=3.13,<3.14` + CLAUDE.md 原意一致）+ `ENV UV_PYTHON_PREFERENCE=only-system` 让 uv 用 slim 自带 python，消除 uv-managed Python symlink 漏 copy 到 runtime stage 的链断问题。改动 ≤ 6 LOC，单文件。

## 1. Linked Artifacts

- Issue: [#134](https://github.com/MJ-AgentLab/mj-agent/issues/134) `[Bugfix] runtime stage broken uv-managed Python symlink (mj-agent container crash exit 126)`
- Repo Scan: Stage 3 输出（Plan needs update; Risk High；4 选项；用户选 (a-2)）
- 上游触发: PR [#131](https://github.com/MJ-AgentLab/mj-agent/pull/131) Stage 17 post-merge AC3-5 verify
- Dependabot stale: commit `4a178ef maintain(infra)(deps): Bump python in /infra/docker`（digest bumped 3.13 → 3.14 但 `# tag` 注释漏 sync；导致 3-way 不一致暴露 venv bug）
- 关联 ADR / 历史：
  - CLAUDE.md "mirrors mj-system v3.2.2 · Python 3.13-slim"（原意基线）
  - PR #131 plan §5.2 ARG 设计权衡（参考结构）

## 2. Context

PR #131 (mirror to tuna) Stage 17 verify 暴露 mj-agent 容器 crash loop exit 126：

```
/app/entrypoint.sh: /app/.venv/bin/mj-agent: /app/.venv/bin/python3: bad interpreter: Permission denied
```

Stage 3 Repo Scan 深挖发现 **3-way 版本不一致**：

| Layer | Python 版本 |
|---|---|
| `pyproject.toml requires-python` | `>=3.13,<3.14` (3.13.x only) |
| Dockerfile FROM digest (`sha256:1697e8e8`) actual | **3.14.4** ❌ |
| Dockerfile `# tag: 3.13-slim` 注释 | `3.13-slim` (stale；Dependabot 漏 sync) |

uv 0.11.13 默认 `UV_PYTHON_PREFERENCE=managed`，因 slim 自带 3.14 ≠ pyproject 3.13 → uv 下载 managed Python 到 `/root/.local/share/uv/python/cpython-3.13-linux-x86_64-gnu/`。venv 内 `python3 → python → /root/.local/share/uv/...`（绝对路径）。`COPY --from=builder /app/.venv` 没带 `/root/.local/share/uv` → 运行时链断。

**期望产出**：mj-agent runtime container healthy，三 service `compose up -d` 全过；同时回归 Python 3.13 baseline（与 pyproject + 原意一致；修正 Dependabot stale comment）。

## 3. Scope

### 3.1 Dockerfile Python 3.13 回退 + uv only-system（风味 C infra）

- 含：
  - `infra/docker/Dockerfile:23` builder FROM 改 `python:3.13-slim@sha256:d49c1ff87eb98eac346fc250f52925f726eb913c43a92854246dd03c9692ad67`（Python 3.13.13；当前 `python:3.13-slim` tag 指向）
  - `infra/docker/Dockerfile:24` `# tag: 3.13-slim` 保留（现在事实一致）
  - `infra/docker/Dockerfile:24` 之后加 `ENV UV_PYTHON_PREFERENCE=only-system`（让 uv 走 slim 自带 `/usr/local/bin/python3` = 3.13.13，符合 pyproject）
  - `infra/docker/Dockerfile:46` runtime FROM 同步改 `python:3.13-slim@sha256:d49c1ff8...`
  - `infra/docker/Dockerfile:47` `# tag: 3.13-slim` 保留
  - runtime stage **不**加 `ENV UV_PYTHON_PREFERENCE`（runtime 不跑 uv sync；YAGNI）
- 不含：
  - 不动 PR #131 ARG APT_MIRROR_URL + sed（保留 tuna mirror 修复）
  - 不动 `pyproject.toml`（保 `requires-python=>=3.13,<3.14`）
  - 不动 `uv.lock`（依赖未变；只是用不同 Python 解析器）
  - 不动 `entrypoint.sh` / `src/` / `docs/`

### 3.2 严格守约（Out-of-Scope）

- 不升 Python 3.14（per HITL 决策 (a-2) 而非 (a-1)）
- 不 COPY `/root/.local/share/uv` 多带（per HITL 决策 (a-2) 而非 (b)）
- 不 ARG 化 Python 版本（YAGNI；Dependabot 继续按 digest 跟踪）
- 不动 `ghcr.io/astral-sh/uv` digest（独立 defer 议题）
- 不补 `CHANGELOG`（非 user-visible runtime；与原意 baseline 一致）

## 4. HITL Gates

- **Stage 5 Gate 1（Plan 确认）**：本 plan body 草案审批
- **Stage 7 Gate 2（设计确认）**：SPEC inline §5.2 4-选项对比 + (a-2) 选择 → 与 Stage 5 一并 approve
- **Stage 9 Scope drift**：实施中越界改其他文件必停
- **Stage 11 Self-review**：commit 前 §4.9 Rule 5 反扫
- **Stage 13 Push gate**：push 前 user 确认

## 5. Implementation (Stage 8 — C-flavor) 详解

### 5.1 实现 diff sketch（伪代码；非最终）

```dockerfile
# Builder stage L23-L25 改造
-FROM python:3.14-slim@sha256:1697e8e8d39bf168e177ac6b5fdab6df86d81cfc24dae17dfb96cfc3ef76b4dd AS builder
+FROM python:3.13-slim@sha256:d49c1ff87eb98eac346fc250f52925f726eb913c43a92854246dd03c9692ad67 AS builder
 # tag: 3.13-slim

+# uv preference: use slim's bundled /usr/local/bin/python3 (3.13.13, satisfies
+# pyproject requires-python=>=3.13,<3.14). Avoids uv-managed Python in
+# /root/.local/share/uv/ which doesn't survive COPY --from=builder /app/.venv
+# to runtime stage (see #134 / PR #131 Stage 17 finding).
+ENV UV_PYTHON_PREFERENCE=only-system
+
 # Default apt mirror = tuna; avoids Fastly anycast flakiness affecting
 ...

# Runtime stage L46 改造
-FROM python:3.14-slim@sha256:1697e8e8d39bf168e177ac6b5fdab6df86d81cfc24dae17dfb96cfc3ef76b4dd
+FROM python:3.13-slim@sha256:d49c1ff87eb98eac346fc250f52925f726eb913c43a92854246dd03c9692ad67
 # tag: 3.13-slim
```

### 5.2 设计选项权衡（inline SPEC；4 options 对比，per Stage 3 Repo Scan + HITL 决策）

| 选项 | 实现 | 影响 | Risk | 选用？ |
|---|---|---|---|---|
| (a-1) 升 Python 3.14 | pyproject `requires-python` 改 + ENV only-system | 测所有 dep 3.14 兼容；CHANGELOG | Medium-High | ❌ |
| **(a-2) 回退 3.13** | FROM digest 换 + ENV only-system | 最小侵入；与 pyproject + 原意一致 | Low-Medium | ✅ **本 PR** |
| (b) COPY uv-managed | runtime 加 `COPY /root/.local/share/uv` | image +50 MB；uv 漂移风险 | Low | ❌ |
| (c) uv pip + virtualenv | 改 uv workflow | 改动大；流程变 | High | ❌ |

**选 (a-2) 理由**：

- pyproject 明确 `requires-python=>=3.13,<3.14` → 3.13 是项目当前承诺
- CLAUDE.md 原意 "mirrors mj-system v3.2.2 · Python 3.13-slim"
- 修正 Dependabot 引入的 stale comment（commit 4a178ef）
- 改动 ≤ 6 LOC vs (b) 多带 50 MB；(a-1) 需 dep 测试
- 与 mj-system 上游一致（v3.2.2 也 3.13）

### 5.3 Documentation Decision

| Type | Action | Path | Reason |
|---|---|---|---|
| Plan | Create | `plans/[PLAN]_venv_uv_python_symlink_fix.md` | 本文件 |
| SPEC | None (inline §5.2) | — | 改动 ≤ 6 LOC |
| ADR | None | — | 不是新承诺；只是回归 baseline + 修 Dependabot stale；记入 commit + PR body 够 |
| RUNBOOK | None | — | — |
| GUIDE / STANDARD / Local ISSUE / ASSESSMENT / INDEX | None | — | — |
| CHANGELOG | None | — | 非 user-visible（dev container 内部；功能不变；只是修 broken image build）|

## 6. Risk

| 风险 | 等级 | 风味 | 缓解 / Rollback |
|---|---|---|---|
| python:3.13-slim 当前 digest (d49c1ff8) 后续 Dependabot bump | Low | C | Dependabot 按 sha 跟踪；bump 时同步更新 `# tag` 注释（如 4a178ef 的反面教训）|
| only-system 行为变化（uv 0.11.13 行为新 vs 旧）| Low | C | Stage 10 Level B build 全过即证；不动 uv.lock |
| 3.13 vs 3.14 base image Debian 版本差异（apt sources 改动是否同样适用）| Low | C | 两者都 trixie-based；PR #131 sed 替换 hostname 行为不依赖 Python 版本 |
| TEST/PROD Harbor pull 现 image 仍含 bug | 预期非 risk | C | merge 后下次 CI build 自动 push 新 image；TEST/PROD 用旧 image 仍 crash（pre-existing；本 PR merge 不改变现状）|
| 升 (a-1) Python 3.14 误选 | N/A | — | user 已选 (a-2)，明确 |
| **Stage 8 verify 暴露 pg auth pre-existing bug** | Medium | — | mj-agent-postgres volume 内 mj_agent_app role/password 与 .env 不匹配（commit c91ed81 rename 后 postgres-init 未重跑）；与 #134 venv 修**完全无关**；本 PR 不修复，开新 follow-up issue；可参考 PR #131 → #134 同模式 |

## 7. Verification

### 7.1 Stage 10 Level A（必跑）

```powershell
uv run ruff check
uv run mypy src/mj_agent
uv run pytest tests/unit
docker compose -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml config
uv run python scripts/check_wikilinks.py
uv run python scripts/check_frontmatter.py
```

### 7.2 Stage 10 Level B（核心 verify；HITL-confirm）

```powershell
# 必须重新 build (image 内 Python 版本变了)
docker compose -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml build mj-agent --no-cache

# 验 Python 版本 + venv 链接
docker run --rm --entrypoint sh mj-agent:0.1 -c "python3 --version"
# 期望: Python 3.13.13

docker run --rm --entrypoint sh mj-agent:0.1 -c "readlink /app/.venv/bin/python3"
# 期望: 解析到 /usr/local/bin/python3 (或其等价路径，**不**含 /root/.local/share/uv/)

docker run --rm --entrypoint sh mj-agent:0.1 -c "ls -la /app/.venv/bin/python3 && /app/.venv/bin/python3 --version"
# 期望: 链接有效 + 输出 Python 3.13.x

# 起 stack
docker compose -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml up -d

# 等 healthcheck (mj-agent start-period 20s + 一次 probe ~30s)
docker compose -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml ps
# 期望: mj-agent / mj-agent-postgres / mj-agent-redis 三 healthy

docker exec mj-agent mj-agent check
# 期望: ✅ DB OK + ✅ Ark LLM OK

netstat -ano | findstr ":8001 "
# 期望: 0.0.0.0:8001 LISTENING
```

### 7.3 Stage 11 Self-review

- §4.9 Rule 5 反扫：corpus grep `python:3.14-slim` / `1697e8e8d39bf168e177ac6b5fdab6df86d81cfc24dae17dfb96cfc3ef76b4dd`（旧 digest）仅命中 Dockerfile 自身 + 本 PR plan body context；无 stale doc
- mj-agent 扩展（SKILL.md / system.md / qcm_catalog.yaml）：N/A
- Scope-drift Severity 预期：none

## 8. Completion Criteria（AC checklist）

- [x] **AC1**: `docker compose config` 通过 — Stage 10 Level A exit 0
- [x] **AC2**: `compose build mj-agent --no-cache` 全过（一次过）；image `mj-agent:0.1` sha256 d78ae6cb
- [x] **AC3**: `docker run --rm mj-agent:0.1 python3 --version` → `Python 3.13.13` ✓（match pyproject `>=3.13,<3.14`）
- [x] **AC4**: `docker run --rm mj-agent:0.1 readlink /app/.venv/bin/python3` → `python` → `/usr/local/bin/python3` ✓（不含 `/root/.local/share/uv/`）
- [x] **AC5 core**: `compose up -d` mj-agent container **不再 crash exit 126**（本 PR 核心修复）— Up 49 sec health:starting；entrypoint.sh + Python imports 全过 (langgraph + psycopg_pool 已 import 并 attempt DB connect)
- [ ] **AC6 / AC5 full healthy**: ⚠️ **暴露 pre-existing pg auth bug**（NOT #134 引入）— `password authentication failed for user "mj_agent_app"`；mj-agent-postgres volume 内 user/password 与 .env 不匹配；commit c91ed81 role rename 后 postgres-init 未重跑（volume 非空时跳过）；→ **新 follow-up issue**
- [x] **AC7**: host port 8001 LISTENING ✓（TCP 0.0.0.0:8001 + [::]:8001）
- [x] **AC8**: Level A 5/5 ✅（ruff / mypy / pytest tests/unit / compose config / wikilinks 0 violations + frontmatter 92 docs）
- [ ] AC9: PR body 含 before/after evidence + 新 follow-up issue 引用
- [ ] AC10: commit `fix(infra):` per Commit Convention §4 (type=fix scope=infra in allowlist)
- [ ] AC11: PR CI 全绿 + ≥1 SWE approve

## 9. 关联

- Issue: [#134](https://github.com/MJ-AgentLab/mj-agent/issues/134)
- 上游 PR: [#131](https://github.com/MJ-AgentLab/mj-agent/pull/131)（Stage 17 暴露）
- Dependabot stale source: commit `4a178ef`（digest bump 漏 sync comment）
- 目标文件:
  - `infra/docker/Dockerfile`（+~6 / -2，2 处 FROM digest 改 + 1 处 ENV）
  - `plans/[PLAN]_venv_uv_python_symlink_fix.md`（本文件）
- 不动文件:
  - `pyproject.toml`（requires-python 不变）
  - `uv.lock`
  - `infra/docker/docker-compose.*.yml`
  - `infra/docker/entrypoint.sh`
  - `src/mj_agent/**`
  - `.env*`
  - `.github/workflows/*` / `.github/dependabot.yml`
  - `CLAUDE.md`
  - 任何 `docs/`
- 后续独立 PR（本 PR 不扩 scope）:
  - **[#132](https://github.com/MJ-AgentLab/mj-agent/issues/132)** apt `Acquire::Retries=3`（PR #131 follow-up）
  - **[#133](https://github.com/MJ-AgentLab/mj-agent/issues/133)** CLAUDE.md:126 stale ADR-025 ref
  - **[#135](https://github.com/MJ-AgentLab/mj-agent/issues/135)** plan state mark completed（#131 + 本 PR plan）
  - **[#136](https://github.com/MJ-AgentLab/mj-agent/issues/136)** mj-agent-postgres stale credentials for `mj_agent_app` role（本 PR Stage 8 verify 暴露；同 "fix N → expose N+1" 模式）
