---
type: plan
summary: Dockerfile builder + runtime stage 参数化 apt mirror (ARG APT_MIRROR_URL 默认 mirrors.tuna.tsinghua.edu.cn) + sed 替换 deb822 sources，修复 Fastly anycast 持续 500 导致的 DEV `compose up --build` 全失败
owner: ranzuozhou
created: 2026-05-11
updated: 2026-05-11
completed: 2026-05-11
state: completed
track: code
---

# [PLAN] Dockerfile apt mirror → tuna (Fastly flakiness recovery)

> 单 PR maintain 任务：`infra/docker/Dockerfile` 加 ARG + sed 把 apt 拉包从 Fastly anycast `deb.debian.org` 切到清华 mirror。改动 ≤ 10 LOC，单文件，可逆。

## 1. Linked Artifacts

- Issue: [#130](https://github.com/MJ-AgentLab/mj-agent/issues/130) `[Maintain] Switch apt mirror to tuna to fix Fastly anycast flakiness`
- Repo Scan Result: 本 PR 对话 Stage 3 输出（Plan Verdict = still valid，Risk = Medium）
- 前置 PR: 无（独立 issue）
- 关联 ADR / 历史 PR：
  - ADR-026 [[../docs/adr/[ADR]_026_Multi_Environment_Compose_Profile|Multi-Environment Compose Profile]] — 4-file compose 分层架构基线
  - PR #52（commit d2ee751 `maintain(infra): pin Docker base images to digest + extend Dependabot`）— Dockerfile digest pin 的设计先例
  - PR #98 commit 34e82f0 `feat(infra): 4-file docker-compose layering for dev/test/prod` — compose 4-file 引入

## 2. Context

mj-agent Dockerfile 当前 builder + runtime 两 stage 各有一个 `apt-get install` RUN 块，均连接 Debian 官方源 `deb.debian.org`（走 Fastly 全球 anycast）。本次 `/mj-agent-infra-docker-compose` DEV `up -d --build` 跑了 4 次都失败于 `[builder 2/8] apt-get install gcc libc6-dev libpq-dev libffi-dev`：

| Try | 代理路径 | 出口 IP | 失败模式 |
|---|---|---|---|
| 1-3 | 直连 | 146.75.114.132 (fastlydns.net) | 个别 .deb 500；最后 Packages index 404 |
| 4 | Clash LAN 7890 (allow-lan) | 199.232.162.132 (fastlydns.net) | 拉 57.9 MB 后 libgcc-14-dev / libisl23 仍 500 |

两个 IP 都属 Fastly anycast — VPN 节点位置只决定 BGP 给哪个 POP，**origin 后端本身在抽风**时换 POP 不解决。已实测 `mirrors.tuna.tsinghua.edu.cn` 9.67 MB Packages.xz 1.73s 完成（5.6 MB/s）+ Content-Length 与 Fastly 一致 → 国内 mirror 单 origin，稳定性远高于 anycast POP。

**期望产出**：`docker compose -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.override.yml up -d --build` 在大陆环境恢复可用；境外贡献者可显式 `--build-arg APT_MIRROR_URL=deb.debian.org` 回切。

## 3. Scope

### 3.1 Dockerfile 参数化 apt mirror（风味 C）

- 含：
  - `infra/docker/Dockerfile:23` 之后（builder stage） 加 `ARG APT_MIRROR_URL=mirrors.tuna.tsinghua.edu.cn` + 4 行注释（解释默认值 + 回切方式）
  - `infra/docker/Dockerfile:26-28` builder apt-get RUN 块前补 1 行 `sed -i "s|deb.debian.org|${APT_MIRROR_URL}|g" /etc/apt/sources.list.d/debian.sources &&` 链式调用
  - `infra/docker/Dockerfile:46` 之后（runtime stage）同样加 ARG（每个 stage 必须独立 declare，ARG 不跨 FROM）
  - `infra/docker/Dockerfile:50-52` runtime apt-get RUN 块同样改造
- 不含：
  - 不改 `infra/docker/docker-compose.{override,test,prod}.yml`（依赖 Dockerfile 默认值；Harbor pull 路径自动受益于下次 CI build）
  - 不改 `.env` / `.env.example`（ARG 是 build-time 非 runtime env）
  - 不改 `src/` / `pyproject.toml` / `uv.lock`（依赖未变）
- 风味：**C infra**
- 验证：见 §7

### 3.2 严格守约（Out-of-Scope）

- 不修改 `infra/docker/docker-compose.*.yml` 任一文件
- 不增 `build.args` 透传机制到 compose 层（Dockerfile 默认值 = tuna 已满足；待未来 "DEV 与 CI 必须用不同 mirror" 明确需求出现再加）
- 不改 mj-system 上游 Dockerfile（跨仓不改）
- 不动 `ghcr.io/astral-sh/uv` digest pin（commit d2ee751 已 defer 的独立议题）
- 不修复 `CLAUDE.md:126` 的 stale "ADR-025" 引用（独立 docs PR；属 doc cleanup follow-up）
- 不修改 `src/mj_agent/{skills,prompts,agent.py,tools,biz_catalog}/` 任何文件（in-source canonical / biz catalog / SQL guardrail 是 HITL §3.1 mj-agent 专属必停项；本 PR 不涉）
- 不开 CI image build step（`.github/workflows/ci.yml` 不动；CI 仍只跑 pytest + lint + type）

## 4. HITL Gates

- **Stage 5 Gate 1（Plan 确认）**：本 plan body 草案审批 → 落盘后由用户在 Stage 5 显式 approve
- **Stage 7 Gate 2（设计确认）**：SPEC inline 入 §5 实现路径（C 风味小改不立独立 SPEC 文件，per HITL_Prompt §4.6）→ 与 Stage 5 一次性 approve
- **Stage 9 Scope drift gate**：实施中如越界改其他文件，必停
- **Stage 11 Self-review**：commit 前 §4.9 Rule 5 反向扫描判断；mj-agent 扩展含 in-source canonical 反向扫描
- **Stage 13 Push gate**：push 前由用户确认

## 5. Implementation (Stage 8 — C-flavor) 详解

### 5.1 实现 diff sketch（伪代码；非最终）

```dockerfile
# Builder stage (Dockerfile L23 之后插入；L26-28 改造)
FROM python:3.14-slim@sha256:... AS builder
# tag: 3.13-slim

# 新增：apt mirror 参数化（解决 Fastly anycast 持续 500；境外贡献者
# 可 --build-arg APT_MIRROR_URL=deb.debian.org 回切）
ARG APT_MIRROR_URL=mirrors.tuna.tsinghua.edu.cn

# 改造：apt-get update 前插 sed
RUN sed -i "s|deb.debian.org|${APT_MIRROR_URL}|g" \
        /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
        gcc libc6-dev libpq-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Runtime stage (Dockerfile L46 之后插入；L50-52 改造) 同样模式
FROM python:3.14-slim@sha256:...
# tag: 3.13-slim

ARG APT_MIRROR_URL=mirrors.tuna.tsinghua.edu.cn

# libpq5 = analyst psycopg client; tini = PID-1 signal handling.
RUN sed -i "s|deb.debian.org|${APT_MIRROR_URL}|g" \
        /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
        libpq5 tini \
    && rm -rf /var/lib/apt/lists/*
```

### 5.2 设计选项权衡（inline SPEC）

| 选项 | 默认值 | DEV 行为 | TEST/PROD CI build 行为 | 境外开发者 |
|---|---|---|---|---|
| **A（采用）** Dockerfile ARG default=tuna | tuna | 自动用 tuna（透明）| CI 用 tuna（CI 在境内 → 受益）| `--build-arg APT_MIRROR_URL=deb.debian.org` 显式回切 |
| B Dockerfile ARG default=deb.debian.org + compose override 注入 args | deb.debian.org | 需 override.yml 加 `args:` 块；漏配则失败 | CI 不传 args 仍 fastly fail | 不传 args 即原行为 |
| C 硬编码 tuna 不加 ARG | tuna | 自动 | 自动 | 无回切（需改文件） |

**采用 A**：Dockerfile 默认 tuna，compose 不动。理由：

- 修复主目标是 DEV/CI 在大陆环境恢复 build；硬选 tuna 默认是符合实际部署假设
- ARG 提供回切机制，覆盖境外贡献者边缘场景
- compose 层零改动 = 最小侵入；如未来需要 DEV/CI 差异化 mirror，再补 `args:` 不为时晚

### 5.3 Documentation Decision（§7.1 矩阵）

| Type | Action | Path | Reason |
|---|---|---|---|
| Plan | Create | `plans/[PLAN]_dockerfile_apt_mirror_tuna.md` | 本文件 |
| SPEC | None (inline §5.2) | — | C 风味小改；ADR-026 已 cover compose 架构 |
| ADR | None | — | 非架构决策 |
| RUNBOOK | None | — | 无运维流程变化 |
| GUIDE / STANDARD | None | — | 无新规则/操作 |
| Local ISSUE | None | — | Risk=Medium 非长期知识锚点 |
| ASSESSMENT | None | — | 无基线对比需求 |
| CHANGELOG | None | — | 非 user-visible（build-time 内部）|
| INDEX | None | — | 无新 canonical |

## 6. Risk

| 风险 | 等级 | 风味 | 缓解 / Rollback |
|---|---|---|---|
| tuna trixie-security 同步滞后 < 12h | Low | C | 接受非 prod 环境延迟；critical CVE 时 `--build-arg APT_MIRROR_URL=deb.debian.org` 显式拉 Fastly（Fastly 自愈后即可）|
| tuna 短时维护停机 | Low | C | ARG 回切；或换 `mirrors.aliyun.com`（实测 2.8 MB/s 同步内容） |
| **tuna 偶发单文件 500 EOF**（Stage 8 verify 发现）| Medium | C | 容器内 apt 多并发请求偶尔触发 tuna `500 reading HTTP response body: unexpected EOF`（host curl `--noproxy` 直连 5.6 MB/s 干净，但容器内 1.1 MB/s + 偶发 EOF）。本 PR build 3 次重试才全过。**Follow-up**：开 issue 加 `Acquire::Retries=3` apt 配置（独立 PR，本 PR 不扩 scope）|
| sed 误改 deb822 schema 结构 | Very Low | C | sed 仅替换 hostname 字段；AC2 (compose build) 立即捕获 |
| TEST/PROD Harbor pull 镜像不变直到下次外部 CI build | 预期非 risk | C | 设计预期；TEST/PROD 主机如需立即受益可 `compose ... build --pull` 本地重建（绕 Harbor）|
| 触发 §3.1 通用 6（生产配置 / 部署）| Medium | C | 走完整 HITL Stage 5/7/9/11/13 gates；本 plan 详述 |
| 触发 §3.1 mj-agent 专属 10-13 | **未触发** | — | 不涉 in-source canonical / system.md / qcm_catalog / SQL guardrail |

## 7. Verification

### 7.1 Stage 10 Level A（只读 / 必跑）

```powershell
# Lint / Type / Unit（PR 卫生 gate；非 Dockerfile 直接影响）
uv run ruff check
uv run mypy src/mj_agent
uv run pytest tests/unit

# Compose lint（Dockerfile + override.yml 解析）
docker compose -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml config

# 文档 check（本 PR 新增 plan body 触发）
python scripts/check_wikilinks.py
python scripts/check_frontmatter.py
```

### 7.2 Stage 10 Level B（HITL-confirm 后跑）

```powershell
# 核心 verify — Fastly 抽风期间这是 mirror 切 tuna 的唯一硬证据
docker compose -f infra/docker/docker-compose.mj-agent.yml `
               -f infra/docker/docker-compose.override.yml build mj-agent --no-cache

# 起 stack (mj-agent 单独起；storage 已 Up 17h+)
docker compose ... up -d

# 容器健康
docker exec mj-agent mj-agent check
# 期望：✅ DB OK + ✅ Ark LLM OK

# 端口
netstat -ano | findstr ":8001 "
# 期望 LISTENING

# 回切机制 evidence-only AC（Fastly 抽风时可能 fail，不阻塞）
docker compose ... build mj-agent --no-cache --build-arg APT_MIRROR_URL=deb.debian.org
```

### 7.3 Stage 11 AI Self-review tie-in

- §4.9 Rule 5 反向扫描：本 PR 仅文本替换 hostname + ARG 引入，无 rename / move / SQL / DDD / perf；反向扫描 `deb.debian.org` corpus 仅命中 Dockerfile 自身（已在 Repo Scan 验证）
- mj-agent 扩展（runtime SKILL.md / system.md / qcm_catalog.yaml）：N/A，未涉
- Scope-drift Severity 预期：none（diff 严格限于 `infra/docker/Dockerfile` + `plans/[PLAN]_dockerfile_apt_mirror_tuna.md`）

## 8. Completion Criteria（AC checklist）

- [x] **AC1**: `docker compose -f infra/docker/docker-compose.mj-agent.yml -f infra/docker/docker-compose.override.yml config` 通过 — verified Stage 10 Level A (exit 0)
- [x] **AC2**: `docker compose ... build mj-agent --no-cache` 全过；apt-get 不再报 Fastly 500/404 — verified Stage 10 Level B（image `mj-agent:0.1` 784MB built；build log 显示 `Get: mirrors.tuna.tsinghua.edu.cn/debian/...` 全程；3 次重试达成全过，详见 §6 Risk "tuna 偶发单文件 500" 行）
- [ ] **AC3-5 deferred to Stage 17 post-merge**（在 develop/ worktree 含 .env 时跑）：`compose up -d` 三 service healthy / port 8001 LISTENING / `mj-agent check` ✅。Dockerfile mirror 改动是 build-time only，runtime image 内容（libpq5 + tini + venv + appuser）功能不变；Stage 8 verify 已覆盖 build path
- [x] **AC6**: `uv run ruff check` / `mypy src/mj_agent` / `pytest tests/unit` 全过 — Stage 10 Level A (171 passed in 10s; mypy 42 files clean; ruff all-pass)
- [x] **AC7**: `check_wikilinks.py` 0 violations + `check_frontmatter.py` 91 canonical docs pass — Stage 10 Level A
- [ ] AC8: PR description 含 4 次失败 evidence + 三 mirror 测速对比 + 失败 IP + **本次 verify 3-retry finding**
- [ ] AC9: commit message 走 `infra(infra):` 类型（per Commit Convention §4，scope=`infra` 是 12 项闭合 allowlist 中"跨领域兜底"槽位，覆盖 Dockerfile；`docker` 不在 allowlist — 修正自 Stage 11 self-review 发现）
- [ ] AC10: PR 通过 CI（unit + eval + integration + contract）+ ≥1 SWE approve
- [ ] AC11: merge 后 develop 上跑 `compose ... up -d --build` 验 mj-agent 主服务 healthy（Stage 17 post-merge；同时回填 AC3-5）

## 9. 关联

- Issue: [#130](https://github.com/MJ-AgentLab/mj-agent/issues/130)
- 前置 PR: 无
- 目标文件:
  - `infra/docker/Dockerfile`（+6 行，2 处 ARG + 2 处 sed）
  - `plans/[PLAN]_dockerfile_apt_mirror_tuna.md`（本文件）
- 不动文件（特别声明）:
  - `infra/docker/docker-compose.*.yml`（全部 4 个）
  - `.env*`
  - `src/mj_agent/**`
  - `pyproject.toml` / `uv.lock`
  - `.github/workflows/*` / `.github/dependabot.yml`
  - `CLAUDE.md`（A6 gate 不触发；CLAUDE.md:126 stale ref 是独立 follow-up）
  - 任何 `docs/`
- 后续独立 PR / follow-up:
  - **docs cleanup**: `CLAUDE.md:126` 把 `ADR-025` 引用更新到 `ADR-026`（属 documentation/ 分支；本 PR 无关）
