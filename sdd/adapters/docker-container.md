---
type: sdd-adapter
artifact: docker-container
state: draft
version: 0.3
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-04
track: code
ai_visibility: source-of-truth
---

# Adapter: Docker Container

> Phase M2 内容化 — Docker Container adapter 治理 `docker/`（M5-PR2 自 `infra/docker/` 平移完成）
> 全部容器化制品：`Dockerfile` + 4-file compose 链 + 运行时 expected state.
> §Standards / §BDD Rules / §TDD Rules 各段顶部 cross-ref 蓝图
> `spec-anchored-calm-lampson.md` 手册 §23 Docker/Container Adapter Standards（注意：本
> adapter 唯一 cross-ref §23 而非 §22.X；其他 6 adapter 走 §22.1-§22.7）.

## §Scope

**Included** — Docker Container adapter 治理：

- `docker/Dockerfile`（M5-PR2 自 `infra/docker/Dockerfile` 平移完成）
- `docker/compose.yaml`（compose base）+ 3 profile overlays
  （`compose.override.yml` dev / `compose.test.yml` test /
  `compose.prod.yml` prod；ADR-026 4-file layering）
- `docker/entrypoint.sh` —— 容器启动脚本
- `docker/postgres-init/01-bootstrap-mj-agent-memory.sh` —— pg init 脚本
- 容器运行时状态（healthcheck / network attach / port binding / volume mount / depends_on
  graph）
- 独立 compose project（per ADR-008）+ 依赖 `mj-system-backend-network` external network
  （consumer 角色访问 analyst RO biz pg）

**Excluded** — 其他 adapter 治理：

- mj-system 上游 compose / Dockerfile（out of mj-agent governance；trust boundary 在
  `network attach` 层）
- `.github/workflows/*.yml` CI — SDD Kernel 自治理（非 Docker container adapter scope）
- Python 包构建 (`pyproject.toml` / `uv.lock`) → `python` adapter（虽然 Dockerfile `COPY` 它们
  入 image，但 image 内 Python 包结构治理由 python adapter 负责）

**Adapter 唯一 multi-contract pattern** — 与其他 6 adapter 单 contract 不同；本 adapter 同时
治理 3 contract（详 §Contract Output）.

## §Contract Output

本 adapter 唯一 **multi-contract pattern**；3 contract 各管一维度，同一 capability 可全用或
部分用：

- `<capability>/contracts/docker.contract.yml` — Dockerfile build contract（base image 固定引用
  （含 uv 工具镜像）/ apt deps + retries / Python version pin / `uv` install mode / non-root user /
  `exposed_port`（标量）/ forbidden-in-image 黑名单）；schema 见
  `sdd/templates/contracts/docker.contract.yml.template`
- `<capability>/contracts/compose.contract.yml` — 4-file profile layering schema（base +
  override + test + prod；`project_name` 跨 profile 不变；`attached_networks`；
  `env_file_explicit: true` 强制 `--env-file .env` 显式传递）；schema 见
  `sdd/templates/contracts/compose.contract.yml.template`
- `<capability>/contracts/runtime.expected.yaml` — 运行时 expected state（**`.yaml` 后缀**而非
  `.yml`；per C6 + 蓝图 §3.2 + §19.2）；M2 期 skeleton；M4 完整化（详 §Standards §Runtime
  Expected schema 子节）

M1 已落地 `capabilities/infrastructure/docker-compose/` capability：当前已含
`docker.contract.yml` + `compose.contract.yml` 两 contract（V5 5.1 已 PASS 2P/4W/0F）；
`runtime.expected.yaml` 待 M4 完整化.

## §Standards

> 本节对应蓝图手册 §23 Docker/Container Adapter Standards.

`freeze_anchor`：per-file string path（如 `docker/Dockerfile`；M5-PR2 自 `infra/docker/` 平移后
freeze_anchor 字符串已同步更新）；M2 新 contract **不涉**本 adapter 治理的必停 surface（4 项专属
必停均在 src/agent/prompt/skill family；docker family 不在内）.

### §Image schema (`docker.contract.yml`)

M1 起为**嵌套块**结构：real contract 自 `bc230a4`（Pilot 4 baseline）即为 nested，`d3f0f0b`
（M5-PR1）把 M0 扁平 template 对齐过来——本节 prose 当时漏改，故长期描述已退役的扁平形。下列
括注的扁平旧名**均非**现行 contract 字段；其中仅 `user_required` / `healthcheck_required` 在
`scripts/sdd/check_docker_contracts.py`（`:123` / `:137`）保留向后兼容 fallback，
`build_args_no_secrets` / `exposed_ports` 无任何读取方，纯历史名：

- `dockerfile.path` / `dockerfile.freeze_anchor` — Dockerfile 路径 + 行数锚
  （`docker/Dockerfile`；M5-PR2 自 `infra/docker/Dockerfile` 平移）
- `base_image.{builder_stage,runtime_stage}.image` — 每 stage 的 base image 固定引用（当前两者
  同为 `python:3.13-slim` + 同 digest）。**非**可选集合：minor 由 `.github/dependabot.yml`
  ignore-list 锁死（#294），只允许同 tag 线内 digest bump
- `base_image.uv_binary.image` — builder 工具镜像（经 `COPY --from=` 引入，非 `FROM`）；
  供应链面等同 base image（per #408）
- `builder_stage_contract.build_args{}` — 构建期 ARG 契约（当前仅 `APT_MIRROR_URL`）
- `runtime_stage_contract.user.non_root: true` — `USER` directive 必填（防 root 容器逃逸）
  （旧扁平名 `user_required: non-root`）
- `runtime_stage_contract.copied_paths_allowlist[]` — `COPY` 路径白名单
  （`/app/.venv` / `/app/src` / `/app/pyproject.toml` …）
- `runtime_stage_contract.forbidden_in_image[]` — image 内黑名单（`.env` / `config/secrets.enc` /
  `config/secrets-mcp.enc` / private keys）；「`ARG` 不得传 secret」由本项末条覆盖
  （旧扁平名 `build_args_no_secrets: true`）
- `healthcheck{}` — `HEALTHCHECK` 契约块（cmd / interval / timeout / start_period / retries）
  （旧扁平名 `healthcheck_required: true`）
- `runtime_stage_contract.exposed_port` — `EXPOSE` 端口（mj-agent 主 port 8000；**标量**，非列表）
  （旧扁平名 `exposed_ports[]`）

### §Compose schema (`compose.contract.yml`)

- `compose_files[]` — 4-file layering 顺序（base + override + test + prod；ADR-026）
- `project_name_stable: true` — compose project name 跨 profile 不变（避免 dev/test/prod 容器
  误删彼此 volume）
- `networks_explicit: true` — `networks` 段显式声明（不允许 default network 模式）
- `external_networks[]` — 依赖的 external network（`mj-system-backend-network` consumer 角色）
- `env_file_explicit: true` — `--env-file .env` CLI flag 强制（compose 在 `docker/` 子目
  录时不自动 load .env；必须 explicit pass）
- `secret_substitution_only_for[]` — 允许 substitute secret env var 的字段白名单
  （`postgres_password` / `mj_agent_memory_password`）

### §Healthcheck schema

- 每容器必填 healthcheck（mj-agent / mj-agent-postgres / mj-agent-redis 三服务都有）
- `type: http | cmd` — HTTP probe 或 cmd probe
- `path` (HTTP) — 探针 URL（mj-agent `/health` 走 `mj-agent check` 链）
- `cmd` (CMD) — shell 命令（pg: `pg_isready`；redis: `redis-cli PING`）
- `interval / timeout / retries` — 探针节奏（M3+ 起 contract 字段化；M2 默认 compose 内联）

### §Runtime Expected schema (`runtime.expected.yaml`)

**M2 skeleton（仅最小验证 schema 存在；防字段 ambiguity 造成 contributor 误判完整度）**：

- `containers[].name` — 服务名（验证 compose `services:` 顶层 key 与本 contract 一致）
- `containers[].port` — 容器内端口占位（仅记录；不强制与 `EXPOSE` 一致）

**M4 完整化字段（M2 期不在 contract；M4 落地后 mandatory）**：

- `containers[].host_port_map` — 宿主端口映射（如 8001 → 8000）
- `containers[].healthcheck` — 与 `compose.contract.yml` healthcheck 双向校验
- `networks: {internal, external}` — 内/外 network 完整拓扑
- `volumes[]` — 持久化 volume 列表（`mj-agent-pg-data` / `mj-agent-redis-data`）
- `depends_on` — 服务依赖图（agent → postgres → redis 启动顺序契约）
- `expected_log_lines[]` — 启动 1 分钟内必现的关键日志（M4+ smoke layer）
- `metric_endpoints[]` — Prometheus / OTel 输出端点（M5+ observability layer）

**注**：`runtime.expected.yaml` 后缀 `.yaml`（**非 `.yml`**）per C6 + 蓝图 §3.2 + §19.2；
contract loader 严格按后缀查找；M3+ 后续 contributor 误改成 `.yml` 会触发 validator 找不到
文件.

## §BDD Rules

> 本节对应蓝图手册 §23 BDD Rules（docker-container behavior scenario tagging）.

**`@adapter:docker-container` 何时用** — 容器运行时 + compose 装配行为 scenario：

- `compose up` / `compose down` 顺序行为（如 dev profile 启动后 healthcheck PASS）
- Healthcheck 探针行为（HTTP 200 / pg_isready / redis-cli PING）
- Network attach 行为（`mj-system-backend-network` external network 不存在时 compose up 应失败
  并给明确错误）
- Profile overlay 行为（test profile 用 test biz pg；prod profile 用 prod biz pg）

**`@adapter:docker-container` 何时 NOT 用**：

- Dockerfile lint（`USER` 非 root / `ARG` 无 secret）→ 走 `hadolint` 工具 gate +
  `check_docker_contracts.py` schema 校验；不入 BDD
- compose YAML syntax error → 走 `docker compose config` validate；不入 BDD
- Python 包构建（`pyproject.toml` 解析）→ `@adapter:python`

**`@adapter:docker-container` + `@hitl` 用于生产 compose 变更**（HITL #8 生产 Docker compose
变更必停）；**cross-ref 边界声明**：

- HITL #8 由 **workflow 层**（cross-capability-change workflow + PR reviewer）强制；adapter
  层 §CI Gate **不**开 `Manual HITL gate` 子标题（与 `prompt.md` / `runtime-skill.md` 的
  Script gate + Manual HITL gate pattern 显式区分）
- 本 adapter 没有 mj-agent 4 项专属必停 surface 触达（4 必停均在 src/agent/prompt/skill
  family）；生产 compose 变更属 cross-capability HITL signal，非命名 gate
- 防未来 contributor 误以为 docker-container adapter 应有 named manual gate；HITL #8 → 走
  workflow 层 review checklist 不走 adapter contract YAML 字段

**`@risk:high` 配套 BDD 必填** — destructive teardown（`docker compose down -v --rmi local`
H3 hard-confirm）+ network 切换 scenario（如 dev → test profile 切换时不应保留 dev volume）.

**示例 `.feature` scenario fragment**：

```gherkin
@adapter:docker-container @risk:high @hitl
Scenario: prod compose up fails fast when external network is missing
  Given mj-system-backend-network does not exist on host
  When operator runs "docker compose -f compose.yaml -f compose.prod.yml up -d"
  Then the command exits non-zero
  And stderr contains "external network mj-system-backend-network not found"
  And no mj-agent container is created
```

## §TDD Rules

> 本节对应蓝图手册 §23 TDD Rules（docker contract-test-first + compose dry-run）.

**Contract-test-first 限于 schema layer**：

- `docker.contract.yml` 的 `base_image` / `runtime_stage_contract.forbidden_in_image` /
  `runtime_stage_contract.exposed_port` 字段变更 → 必先有 failing test（解析 Dockerfile + 比对
  contract）
- `compose.contract.yml` 的 `compose_files[]` 顺序 / `external_networks[]` 变更 → 必先
  failing test
- `runtime.expected.yaml` 字段从 M2 skeleton → M4 完整化是单向扩展（不删字段）；新增字段必先
  failing test

**Compose 变更必先 dry-run**：

- `docker compose --env-file .env -f <files> config` 解析校验（`docker-tdd-contract-test`
  gate 的核心实现）
- 任何 profile 切换 PR 必跑 dry-run 输出对比；改动不影响 spec → 不算 schema drift

**`docker-bdd-scenario-check` + `docker-tdd-contract-test` 双 gate**：

- `docker-bdd-scenario-check`（M3 warning / M4 blocking）— Compose API mock 启动 + healthcheck
  契约验证；对应 §BDD Rules 的 `@adapter:docker-container` 行为 scenario
- `docker-tdd-contract-test`（M3 blocking）— Dockerfile lint + compose config dry-run + schema
  cross-check；对应 §TDD Rules schema-layer test-first

**Red-Green-Refactor 软模式 RD10=C** — AI-generated Dockerfile / compose 变更允许 "test
alongside change"（同一 PR 内含 test + 实装；不强制先 commit failing test）；人工编写仍严格
red-green.

**`_common.yaml_io` 接口共享** — Stage A 实装；本 adapter 与 prompt / runtime-skill /
claude-code-skill adapter 共用 YAML 解析：

```python
# scripts/sdd/_common/yaml_io.py 公开符号：

load_yaml(file_path: Path) -> dict | None
    # 安全加载 YAML；语法错误返回 None；不抛异常

dump_yaml(data: dict, file_path: Path) -> None
    # 写 YAML；M3+ 验证脚本用于 frozen_at 时间戳重签
```

**G28 联动** — 3 contract 任一字段增删 → 必须配套 `tests/contracts/infrastructure/
docker-compose/test_*_contract.py` 内 failing→green 转变.

## §CI Gate

### §Script gate

`scripts/sdd/check_docker_contracts.py`（Stage A 实装；composite validator 同时校验
`docker.contract.yml` + `compose.contract.yml`；`check_runtime_expected.py` 是独立脚本走
M3+ 路径）.

- **Phase**: M2 warning / **M3 blocking**（per `sdd/gates.md` G3 切换节奏）
- **Triggers**: `capabilities/infrastructure/docker-compose/contracts/docker.contract.yml` 或
  `compose.contract.yml` 存在
- **Modes**: `--dry-run` / `--capability <path>` / `--all`
- **Output**: `PASS` / `WARN` / `FAIL` + 详细错误（`USER` 缺失或为 root / `forbidden_in_image`
  路径被 `COPY`/`ADD` / `external_networks` 不匹配 / `env_file_explicit` 违反）；`base_image`
  **无 allowlist 校验**，仅 `base_image.runtime_stage.image` 的信息性 WARN
- **Implementation**: Dockerfile 解析（line-by-line + regex）+ compose YAML 解析（via
  `_common.yaml_io.load_yaml`）+ schema cross-check

### §V5 5.2 sub-flags deferred

- 当前实装：core `check_docker_contracts.py` 已 actionable（Stage A V5 5.1 跑通
  `capabilities/infrastructure/docker-compose/` 实测 **2P/4W/0F PASS**）
- Deferred：`--bdd` / `--tdd` / `--compose-config` 3 个 sub-flag 推到 `M3-FU-V5-SUBFLAGS`
  （per `plans/[PLAN]_spec_anchored_refactor.md` §M3 Task Breakdown；commit `fe0c82e`）
- M2 期评估：V5 是 partial-impl 但 core docker-contract 已 actionable；sub-flag 不阻塞 M2
  PR-M2-2 + PR-M2-3
- Sub-flag 落地后将整合 `docker-bdd-scenario-check` + `docker-tdd-contract-test` + `docker
  compose config` dry-run 三能力到单脚本入口

### §Baseline noise

- M2 期 0 noise（V5 5.1 在 `docker-compose` pilot capability 实测 PASS）
- M2 末 CI toggle PR-M2-3 新增 6 adapter gate warning 含本 gate（`continue-on-error: true`）；
  与 G1/G2/G9 blocking 切换分离
- M3 切 blocking 前需在 develop 上跑 `--all` mode 跨 M1 5 capability 0 violation 验证（per
  CI gate 切换 SOP）

**M2 → M3 切换条件**：

- `--all` 模式在 M1 docker-compose capability + Stage C 新 contract 上跑通 PASS
- V5 5.2 sub-flags M3-FU 完成（独立小 PR）
- `runtime.expected.yaml` M4 完整化字段 schema 稳定（M3 期可继续 skeleton；M4 起强制）

---

> *Phase M2 content — `state: draft`.*
