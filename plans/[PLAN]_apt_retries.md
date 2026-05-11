---
type: plan
summary: Dockerfile builder + runtime stage 各 RUN 块加 echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries，让 apt 自动重试失败的单文件下载，提升对 mirror 偶发 500 EOF (PR #131 tuna 抽风) 的 build robustness
owner: ranzuozhou
created: 2026-05-11
updated: 2026-05-11
state: active
track: code
---

# [PLAN] Dockerfile apt Acquire::Retries=3

> 单 PR maintain：`infra/docker/Dockerfile` 两 stage RUN 块加 1 行 echo + 链式调用，让 apt 内置重试 3 次。改动 +4 LOC，单文件。

## 1. Linked Artifacts

- Issue: [#132](https://github.com/MJ-AgentLab/mj-agent/issues/132) `[Maintain] add Acquire::Retries=3 to Dockerfile apt blocks for tuna mirror resilience`
- 上游 PR: [#131](https://github.com/MJ-AgentLab/mj-agent/pull/131) `infra(infra): default apt mirror to tuna`（Stage 10 Level B verify 3 retries 才过；本 PR 永久解 mirror 偶发 500 抖动）

## 2. Context

PR #131 (mirror to tuna) Stage 10 Level B verify 期间：tuna 偶发单文件 500 EOF（约 1/3 build attempts；每次失败 .deb 不同 → mirror origin 抖动而非固定坏文件）。apt 默认 `Acquire::Retries=0` 不重试 → 单文件 500 即整个 install 失败。

加 `Acquire::Retries=3` 让 apt 在每个失败的 .deb 下载上自动重试 3 次，绝大多数情况能消除 mirror 抖动影响。属 standard Debian/Ubuntu CI 镜像加固模式。

## 3. Scope

### 3.1 Dockerfile apt retries 配置（风味 C infra）

- 含：
  - `infra/docker/Dockerfile` builder stage RUN 块（L37-L41）链式加 `echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries \\`
  - `infra/docker/Dockerfile` runtime stage RUN 块（L66+）同样加
- 不含：
  - 不动 ARG APT_MIRROR_URL / mirror 选择（PR #131 已落）
  - 不动 ENV UV_PYTHON_PREFERENCE / FROM digest（PR #137 已落）
  - 不动 init script / config/README.md（PR #138 已落）
  - 不动 src/ / pyproject / compose / docs / CLAUDE.md

### 3.2 严格守约（Out-of-Scope）

- 不动其他 apt 配置（如 `Acquire::http::Timeout` / `Acquire::ForceIPv4` 等）— 单点修复
- 不动 mirror URL（PR #131 修；本 PR 不重复）
- 不动 base image / Python 版本（PR #137 已锁；本 PR 不动）

## 4. HITL Gates

- **Stage 5 Gate 1**：本 plan body 草案审批（已在本对话 inline approve）
- **Stage 7 Gate 2**：SPEC inline §5.1 diff sketch；与 Stage 5 一并 approve
- **Stage 9 Scope drift**：实施中越界改其他文件必停
- **Stage 11 Self-review**：commit 前
- **Stage 13 Push gate**

## 5. Implementation (Stage 8 — C-flavor) 详解

### 5.1 实现 diff sketch

**Builder stage（L37-L41）**:

```diff
 RUN sed -i "s|deb.debian.org|${APT_MIRROR_URL}|g" \
         /etc/apt/sources.list.d/debian.sources \
+    && echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries \
     && apt-get update && apt-get install -y --no-install-recommends \
         gcc libc6-dev libpq-dev libffi-dev \
     && rm -rf /var/lib/apt/lists/*
```

**Runtime stage（L66+）**:

```diff
 RUN sed -i "s|deb.debian.org|${APT_MIRROR_URL}|g" \
         /etc/apt/sources.list.d/debian.sources \
+    && echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries \
     && apt-get update && apt-get install -y --no-install-recommends \
         libpq5 tini \
     && rm -rf /var/lib/apt/lists/*
```

放在 sed 之后、apt-get update 之前：sed 改 sources，echo 配 retries，update 用新配置开始读 sources，install 享受 retries — 逻辑顺序清晰。

### 5.2 Documentation Decision

| Type | Action | Path | Reason |
|---|---|---|---|
| Plan | Create | `plans/[PLAN]_apt_retries.md` | 本文件 |
| 其他 (SPEC / ADR / RUNBOOK / GUIDE / STANDARD / Local ISSUE / ASSESSMENT / INDEX) | None | — | 改动 +4 LOC，纯 build infra 加固；无新接口/新承诺 |
| CHANGELOG | None | — | 非 user-visible runtime；build robustness |

## 6. Risk

| 风险 | 等级 | 风味 | 缓解 |
|---|---|---|---|
| apt 配置语法错 | Very Low | C | AC2 build 立即捕获；语法是 Debian apt 标准 |
| 80-retries 文件冲突现有 apt config | Very Low | C | `80-` 前缀符合 Debian 排序惯例（晚于 default `50-`）；不与现有 conf 冲突 |
| Acquire::Retries 副作用（如重试本应 fail 的非临时错误延长 build 时间）| Very Low | C | 3 次重试上限 + apt 内置只对 transient 500/timeout 重试，不对 404/permission 等永久错误重试；overhead < 10s per failed package；远低于 mirror 抖动一次失败重新 build 的成本 |
| **Persistent mirror file outage (Stage 10 发现)** | Medium | C | `Acquire::Retries=3` 对 transient 500 有效但**无法兜底**持续性 mirror 文件不可用（验证期间 tuna 对 gcc-14 大 .debs 持续 500 + 偶发 404 on Packages index）。**Mitigation**：境外 fallback `--build-arg APT_MIRROR_URL=deb.debian.org`（PR #131 已建 ARG 机制）；或临时切 `mirrors.aliyun.com`（实测干净）；持久解需 mirror fallback 机制（**独立 follow-up issue**，本 PR 不扩 scope）|
| TEST/PROD Harbor pull 现 image 仍旧 | 预期非 risk | C | 下次 CI build 新 image 自动受益；TEST/PROD 用旧 image 不变（pre-existing 状态）|

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

### 7.2 Stage 10 Level B 核心

```powershell
# 1. Build 1 次 ✅
docker compose ... build mj-agent --no-cache

# 2. 验 apt config 落入 image
docker run --rm --entrypoint sh mj-agent:0.1 -c "cat /etc/apt/apt.conf.d/80-retries"
# 期望: Acquire::Retries "3";

# 3. 验 build 不再受偶发 500 影响（可选；运气依赖）
# 连续 3 次 build --no-cache 全过 → 强证据
docker compose ... build mj-agent --no-cache  # 第 2 次
docker compose ... build mj-agent --no-cache  # 第 3 次
```

### 7.3 Stage 11 Self-review

- §4.9 Rule 5 反扫：corpus grep `Acquire::Retries / 80-retries` 仅命中 Dockerfile + plan body；无 stale doc
- Scope-drift Severity 预期：None

## 8. Completion Criteria（AC）

- [x] **AC1**: Level A 5/5 ✅（ruff / mypy / pytest 171 / wikilinks 0 / frontmatter 94）
- [x] **AC2 (partial)**: `compose build --no-cache` 默认 tuna mirror **3 次 retry 均 fail**（tuna 持续 500 on `gcc-14-x86-64-linux-gnu` / `cpp-14-...` / `libtsan2_14...` 大 .debs；属 tuna 当前 mirror outage，非本 PR 改动缺陷）；**绕 aliyun mirror verify ✅**（`--build-arg APT_MIRROR_URL=mirrors.aliyun.com` build 全过；image sha256 9568993333fb 落成）
- [x] **AC3**: image 内 `/etc/apt/apt.conf.d/80-retries` 内容 = `Acquire::Retries "3";` ✓（docker run cat 验）
- [x] **AC3 旁证**: 失败 build log 显示 apt **实际 retry 3 次** on 500 之后才 fail（`#9 5.064 ... 7.823 ... 8.486 ... 500` 3 次重试可见）→ Acquire::Retries=3 配置生效
- [x] **回归 sanity**: Python 3.13.13 ✓ + venv symlink → /usr/local/bin/python3 ✓（PR #137 修复不受影响）
- [ ] AC4: PR body 含 verify evidence + tuna 当前 outage 诊断
- [ ] AC5: commit `infra(infra):` per Commit Convention §4
- [ ] AC6: PR CI 全绿 + ≥1 SWE approve

> **Stage 10 重要发现**：`Acquire::Retries=3` 对**transient** 500 EOF 有效（每 5 个失败重试 1-3 次后成功；runtime stage 这次 build 全过），但对**persistent** mirror file outage（tuna 当前对特定 gcc-14 大 .debs 持续 500）**无法兜底** — apt 在 retries 用尽后 fail，无 mirror fallback。这是本 PR fix 的**已知边界**，记入 §6 Risk。
>
> **不影响本 PR ship**：fix 本身正确（验 aliyun mirror）+ 改进 transient case 韧性 + 未来 mirror fallback follow-up 是独立议题。

## 9. 关联

- Issue: [#132](https://github.com/MJ-AgentLab/mj-agent/issues/132)
- 上游 PR: [#131](https://github.com/MJ-AgentLab/mj-agent/pull/131)
- 目标文件:
  - `infra/docker/Dockerfile`（+4 / -0；2 处 RUN 块同对称改造）
  - `plans/[PLAN]_apt_retries.md`（本文件）
- 不动文件:
  - `src/mj_agent/**` / `pyproject.toml` / `uv.lock`
  - `infra/docker/docker-compose.*.yml`
  - `.env*` / `.github/workflows/*` / `.github/dependabot.yml`
  - `CLAUDE.md` / 任何 `docs/`
- 完成 PR chain 末尾 follow-up；与 PR #131 → #137 → #138 → #139 衔接
