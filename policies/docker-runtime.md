---
type: policy
artifact: docker-runtime
state: draft
version: 0.4
owner: ranzuozhou
created: 2026-05-20
updated: 2026-08-11
track: shared
ai_visibility: source-of-truth
---

# Policy: Docker Runtime

> Docker 运行时红线政策. **五节均为 live 规则体**：§1-§3 分别约束镜像内容 / network 拓扑 /
> healthcheck，§4 是 `docker/` 下**审批级别**（谁必须签字）的 kernel SoT，含生产红线与供应链面，
> §5 记与其他 policy 的联动。**约束面（§1-§3）与审批面（§4）是两件事**——本文件任何一节讲「必须
> 满足什么」，都不同时决定「改它要找谁签字」，后者一律回 §4 取。

## §1 Image 红线

镜像**内容**约束（secrets / 用户 / 构建面固定引用）。**审批级别不在本节**——任何 Dockerfile
改动该找谁签字，一律见 §4。

四条红线如下。**载体强度差别很大，不要因为都写在本节就当成同一档**：只有 I2 有 blocking 机器
校验，I1 / I4 是 warning，I3 完全没有机器校验、只靠 §4 的人工拍板。

| # | 红线 | 当前实现 | 执行载体 |
|---|---|---|---|
| I1 | 解密产物不得进入 image | `docker/Dockerfile` 的 `COPY` 面仅 6 项（下方列全）；唯一可能夹带解密产物的 `COPY config/` 由**仓根** `.dockerignore` 剔除；`docker/entrypoint.sh` 不做解密 | G7 check (3)（warning@ci）+ V5 `forbidden_in_image` 项（FAIL，但只扫字面量——见下 I1 注） |
| I2 | runtime stage 必须以非 root 运行 | `USER appuser`（uid/gid 1000）`docker/Dockerfile:114`；用户创建于 `:79-80`，`/app` 与 `/var/lib/mj-agent` chown 给 appuser `:101` | **V5 FAIL（blocking@ci）—— 本节唯一被机器强制的一条** |
| I3 | 外部 registry 镜像引用必须 tag + digest 双钉，且不得经 `ARG` 参数化 | builder / runtime 两个 stage 同为 `python:3.13-slim` + 同 digest（`:25` / `:62`）；uv 工具镜像 `ghcr.io/astral-sh/uv:0.12.1` + digest（`:46`，经 `COPY --from=` 引入） | **无机器校验** → 只靠 §4 的 Owner 拍板 + reviewer + PR 模板勾选 |
| I4 | build context 根必须有 `.dockerignore`，且覆盖 `config/secrets*.conf` | 仓根 `.dockerignore`（2026-06-11 owner-approved 落地） | G7 check (3)（warning@ci） |

**I1 — 禁止面的准确边界**。禁的是**解密产物**（`.env` / `config/secrets*.conf` / `*.pem` /
`*.key`）；密文 bundle `config/secrets*.enc` 按 ADR-030 **有意**在允许范围内（不解密即无用）。
规则细则与 G7 三项检查不在本节复制，见 `policies/security.md` §1。Dockerfile 的完整 `COPY` 面 =
`pyproject.toml` + `uv.lock` + `README.md`（`:51`）· `src/`（`:58`）· builder 产物四项（`:88-91`）·
`config/`（`:96`）· `docker/entrypoint.sh`（`:97`）。

> ⚠ **V5 那条不要当成全覆盖。** 它对契约里 `forbidden_in_image` 的每一项做的是「`COPY` / `ADD`
> 行里是否出现该**字面路径**」的正则匹配，而 `COPY config/` 并不含 `config/secrets.enc` 这个
> 字面量 → 不触发。真正兜住解密产物的是 G7 + 仓根 `.dockerignore`；V5 只挡「把禁止路径直接写进
> COPY 行」这一类粗错。

**I3 — 两条钉法的维护主体不同，别当成同一个机制。**

- `python:3.13-slim` 线由 `.github/dependabot.yml` 的 docker 生态自动 bump digest，且已 ignore
  `version-update:semver-major` 与 `semver-minor`（#294）——只允许同 tag 线内 digest 流动；跨
  minor / major 必须人工 PR，同批同步 `requires-python` 与 `uv.lock`。
- uv 工具镜像那行**是手工维护的**：Dependabot 无法刷新 `COPY --from=` 形式的镜像引用（upstream
  `dependabot-core#5103`），所以它不会自动更新；也**刻意不**参数化成 build ARG——ARG 会把 #405
  移除的可变性重新装回去。
- 供应链爆炸半径上二者等同：uv 构建出的 `/app/.venv` 被整体 `COPY` 进 runtime image（per #408）。

**I4 — 「哪一个 `.dockerignore` 生效」是本节最容易踩的一条。** 仓内有**两个**（仓根 +
`docker/.dockerignore`），**只有仓根那个生效**：Docker 仅在 **build context 根**解析
`.dockerignore`（或与 Dockerfile 同路径的 `<dockerfile>.dockerignore`，本仓无此文件），而两条
构建路径的 context 都是仓根——

- DEV compose：`build.context: ../`（`docker/compose.override.yml:20`）；
- CI `docker-build`：`docker build -f docker/Dockerfile` 以 `.` 为 context
  （`.github/workflows/docker-build.yml:112-116`）。

⇒ `docker/.dockerignore` 对**现存全部**构建路径无效。该结论有实现背书而非仅散文：G7 的判定分支
本身就是「`COPY config/` + context 为仓根 → 检查**仓根** `.dockerignore`」，其代码注释直接写着
`docker/.dockerignore` is ineffective（`scripts/sdd/check_secret_exposure.py:23` / `:165`），
`policies/security.md` §1 第 3 项是同一裁定。

覆盖面差异如实记：仓根 `.dockerignore` 是**最小必要**清单（解密产物 + 本地私有配置 + 少量构建
无关大目录），**没有**照搬 `docker/.dockerignore` 里 `docs/` `plans/` `notes/` `research/`
`artifacts/` 等条目——这些目录仍会进 build context。该差异只影响 context 传输体积，**不影响
镜像内容**（没有任何 `COPY` 触达它们）。

> **遗留（本次不动）**：`docker/.dockerignore` 是惰性文件——没有 gate 读它，也没有构建路径用它，
> 而它比真正生效的那份「看起来更全」，容易被下一位读者当成排除清单的真相源。处置（删除，或保留
> 并在文件头写明「仅为 context 改为 `docker/` 时预留」）属 `docker/**` 改动，不在本 policy 的
> 落笔面内，已随本次填充登记为 follow-up。

## §2 Network 隔离

网络**拓扑**约束。审批级别见 §4 的 network 行。

| # | 规则 | 当前实现 |
|---|---|---|
| N1 | mj-agent 是独立 compose project，与上游业务系统各自 up / down | `name: mj-agent`（`docker/compose.yaml:71`），跨 4 个 compose 文件不变（ADR-026 §D.3 · ADR-008 §Decision） |
| N2 | `mj-system-backend-network` 只消费、不拥有 | 声明为 `external: true`（`compose.yaml:222-224`，本仓内别名 `mj-system-network`）；本仓不创建、不管理其生命周期，缺失时 compose 启动 fail-fast |
| N3 | 存储栈挂私有 bridge，够不到外部网络 | `mj-agent-storage` bridge（`compose.yaml:226-231`，标签 `isolation: internal`）；mj-agent-postgres（`:166-167`）与 mj-agent-redis（`:210-211`）**只**挂它 |

**接触面的准确形状**：三个服务里只有 `mj-agent` 同时挂两张网（`compose.yaml:108-110`）——这是它
作为 biz 只读消费者所需的**充分且必要**接触面：memory pg 与 redis 走内部 bridge，biz pg 走
external network（`mj-postgres:5432`，analyst RO role）。两个存储容器完全够不到 external network。

> ⚠ **network 隔离 不等于 宿主不可达——这条差距如实记录，本节不代为改判。**
> 三个服务在 base `compose.yaml` 里都把端口发布到宿主（8001 / 5433 / 6379），且 TEST 与 PROD
> overlay **没有**撤销发布（实测两份 overlay 只增加 `deploy` / `logging` / `labels`，零 `ports`
> 字段）。redis 的 `requirepass` 还是**条件性**的：`MJ_AGENT_REDIS_PASSWORD` 未设时以无认证启动
> （`compose.yaml:183-190`）。所以 `compose.yaml:181-182` 那句「DEV 可接受，因为网络是 bridge
> 隔离的」只在**容器间**成立，对宿主面不成立。收紧发布面属运行时配置变更（触 §4 的 prod 红线），
> 须走该节的审批级别，不由本节单方面决定。

**执行载体：本节无机器校验。** V5 的 `--compose-config` 只做静态检查——每个 compose 文件 YAML
可加载、base 文件有 `services`、合并后每个服务有 `image` 或 `build`；它**不**校验 `name`、不校验
networks 拓扑、也不校验端口发布面。`runtime.expected.yaml` 的 `networks` 与 `network_reachability`
段描述的是 M4 目标态，其断言器 `scripts/sdd/check_runtime_expected.py` **尚未实装**（该 YAML 尾注
自陈 TBD Phase M3；V6 gate 亦标 SKELETON BY DESIGN）。⇒ N1-N3 目前靠 reviewer + §4 审批兜底。

拓扑决策原文见 ADR-008 §Decision（网络拓扑 / 存储栈独立 / 依赖前置）与 ADR-026 §D.1 · §D.3；
契约镜像见 `capabilities/infrastructure/docker-compose/contracts/compose.contract.yml` 的
`networks` 段。

## §3 Healthcheck 必填

三个容器（mj-agent / mj-agent-postgres / mj-agent-redis）各自必填 healthcheck；服务间启动序由
`depends_on` 的 `condition: service_healthy` 串起（`docker/compose.yaml:96-100`）。

**探针定义全部在 base `docker/compose.yaml`，三个 overlay 零 healthcheck 字段**（实测）——即
DEV / TEST / PROD 共用同一套探针，profile 之间没有健康判据差异：

| 容器 | 探针 | interval | timeout | retries | start_period | 源 |
|---|---|---|---|---|---|---|
| mj-agent | `mj-agent check` | 30s | 10s | 3 | 30s | `compose.yaml:102-107` |
| mj-agent-postgres | `psql` 对目标库跑一次 `SELECT 1` | 10s | 5s | 5 | 30s | `compose.yaml:145-164` |
| mj-agent-redis | `redis-cli ping`（按是否启用 `requirepass` 分支） | 10s | 3s | 5 | 5s | `compose.yaml:199-208` |

**镜像内另有一份 `HEALTHCHECK`**（`docker/Dockerfile:122-123`，`start-period` 为 **20s**）。compose
的 healthcheck 覆盖镜像内定义，所以 mj-agent 在栈内生效的是上表的 30s；镜像内那份是脱离 compose
直接 `docker run` 时的兜底。探针命令走 `mj-agent check` 的**默认**模式——凭据存在性 + 同步
memory-DB ping + env drift，离线安全；`--live` 才额外做 async checkpointer / biz DB / 1-token LLM
往返（`src/mj_agent/server/cli.py:7-9` · `:134-180`），**有意不接**进探针：它会突破 10s timeout，
且等于每 30s 打一次 LLM。

**为什么 pg 探针不用 `pg_isready`**：`pg_isready` 在服务器开始接受连接时即返 0，**不验证目标库
是否已由 init 脚本建出** → 会提前绿灯，把失败级联成 mj-agent 侧的 `password authentication
failed`。裁定与推理写在 `compose.yaml:146-159` 的注释里。⚠ `sdd/adapters/docker-container.md`
§Healthcheck schema 仍以 `pg_isready` 举例，与本裁定相反——以本节与 compose 实现为准。

**执行载体（三层，都不覆盖「运行时真的 healthy」）**：

- V5 `--bdd`：逐 service 检查 **contract 文件**里有没有 `healthcheck` 键（WARN）——判的是
  `compose.contract.yml`，**不是** compose 文件本身。
- V5 docker 侧：契约有 `healthcheck` 块但 `docker/Dockerfile` 无 `HEALTHCHECK` 指令 → WARN。
- `runtime.expected.yaml` 描述 up 之后的期望态，其断言器尚未实装（同 §2）。

> **已知契约漂移（本次不修，登记为 follow-up）**：`compose.contract.yml` 记 mj-agent-postgres 的
> 探针为 interval 30s / retries 3 / timeout 10s，与实际（10s / 5 / 5s）不符；mj-agent 条目缺
> `timeout`；redis 条目只记两条命令、无时序字段。`runtime.expected.yaml:20` 的
> `max_to_healthy_sec: 60` 是按 Dockerfile 的 start_period 20s 推算的，没跟上 compose 的 30s 覆盖。
> 改契约本身是 canonical `declared-contract-change`（Owner 拍板），不属本节的文档填充动作。

> **审批级别——本次刻意不补 §4 行。** healthcheck 面的必停当前由两个 entry adapter 承载：
> `docker/AGENTS.md` §Hard stops 与 `docker/CLAUDE.md` §4 项专属必停，二者均标
> `OWNER_APPROVAL_REQUIRED`。§4 仍无对应行，这是本次填充**有意**保留的状态：给 §4 加行会牵出
> 「哪个 canonical enum 锚定该面」这一姿态问题——`secrets-grants-or-prod-config` 现锚的是 prod
> compose 与 Dockerfile 外部镜像引用，而 healthcheck 字段住在 base `compose.yaml`；按 #413 先例
> 应扩既有 enum 的 surface anchor 而非新增第 11 项，属 Owner 决策，不由内容填充顺带完成。
> **触发条件**：Owner 就锚点作出决定后，把结论落成 §4 的一行，并同步撤掉两个 entry adapter 里
> 「§4 尚无对应行，暂沿用本节级别」的过渡措辞。在此之前，以两个 adapter 标注的级别为准。

## §4 变更 HITL 触发条件（生产红线 + 供应链面）

本节是 `docker/` 下**审批级别的 kernel SoT**。`docker/AGENTS.md` §Hard stops 与
`docker/CLAUDE.md` §专属必停 是它的两个 entry adapter——它们**点名对象**、回指本节取级别。
下表列出 `docker/` 各触发面及其 HITL 级别（`docker/compose.prod.yml` 为 Phase M5 自
`infra/docker/docker-compose.prod.yml` 平移）：

| 触发 | HITL 级别 |
|---|---|
| compose.prod.yml 字段修改 | ≥ 2 reviewer + 项目负责人 |
| `docker/Dockerfile` **外部 registry 镜像引用**变更：`FROM <image>` + `COPY --from=<registry image>`（内部 `COPY --from=<stage>` 如 `--from=builder` **不**在内） | `OWNER_APPROVAL_REQUIRED`（改前 Owner 拍板）+ ≥ 2 reviewer |
| `docker/Dockerfile` 其余修改 | ≥ 2 reviewer |
| network 配置（external network / internal network）变更 | ≥ 2 reviewer + 上游业务系统 DRI 联络 |

> **两条 Dockerfile 行按「被点名的对象」划分，不按「影响范围」判断**（per #408 / #413）：Owner
> 拍板只挂在外部 registry 镜像引用上；其余 Dockerfile 行——含 `COPY --from=builder` 一类内部
> stage 拷贝——留在 ≥ 2 reviewer 档，**级别未上调，不是新增必停**。
> 原措辞「Dockerfile 在 prod 部署影响范围内修改」已废除：该谓词需逐次判断且没有可检查的边界，
> 实际会把整份 Dockerfile 悄悄纳入必停面，与 #408 明确排除内部 stage 拷贝的裁定冲突。
> **口径变化如实记录**：级别不变，但覆盖面由条件谓词「prod 影响范围内」**收敛为无条件全文件**
> ——原先需逐次判断的行，现在一律 ≥ 2 reviewer。
> **本表尚未覆盖 healthcheck 面**：该面的必停暂由两个 entry adapter 自带级别承载，不受上面
> 「其余修改」行辖制；补不补本表行取决于一个尚未拍板的 enum 锚点问题，判据与触发条件见 §3 末段。
> canonical enum 锚点 = `secrets-grants-or-prod-config`（`policies/ai-agent.md` §4）。

## §5 与其他 policy 联动

- `policies/data-boundary.md` §1 数据-LLM 三原则 — 通道隔离原则的 Docker 落地表现
- `policies/security.md` §1 — G7 secret 暴露 gate 的三项检查（§1 I1 / I4 的规则细则住在那里，
  本文件不复制）；§3 — 2-bundle secrets 信任边界

---

> *`state: draft` — 五节均为 live SoT；自 v0.4 起本文件**无待填充块**。`state` 不动：per #480 /
> `sdd/lifecycle.md` §4.1，翻 `active` 的判据是操作必要性，内容填充本身不构成该判据。*
>
> *v0.4（2026-08-11）：#482 — 处置本文件在 `M6-FU-POLICIES-TBD-SWEEP` 中的 3 个 TBD 块，
> **全部 filled、无 decline**。三块的共同取证结论一致：约束实体早已在 `docker/` 落地，是文档没
> 跟上。**§1** 落 I1-I4 四条红线，逐条标注当前实现（含行号锚）与执行载体，并明写载体强度不等
> ——只有 I2 非 root 有 blocking 机器校验（V5 读契约 `runtime_stage_contract.user.non_root` 后
> 反查 Dockerfile 的 `USER` 指令），I3 外部镜像引用**完全无机器校验**（V5 对 `base_image` 只发
> informational WARN，`docker-build` 只验可构建）。**§1 的关键取证发现**：仓内有**两个**
> `.dockerignore`，而**只有仓根那个生效**——DEV compose `build.context: ../` 与 CI 的
> `docker build … .` 两条路径 context 都是仓根，仓内也无 `<dockerfile>.dockerignore`；该结论由
> G7 实现自身背书（`check_secret_exposure.py` 的判定分支与代码注释）。同时如实记录两份文件的
> 覆盖面差异（仓根那份不含 `docs/` `plans/` 等条目，故这些目录仍进 build context，只影响体积不
> 影响镜像内容），并把惰性文件 `docker/.dockerignore` 的处置登记为 follow-up。**§2** 落 N1-N3
> 三条拓扑规则，并如实记录一条差距：**network 隔离不等于宿主不可达**——三个服务在 base compose
> 里都发布端口到宿主，TEST / PROD overlay 实测零 `ports` 字段即未撤销发布，redis 的 `requirepass`
> 又是条件性的，故 compose 注释里「bridge 隔离故 DEV 可接受」只在容器间成立。收紧发布面触 §4 的
> prod 红线，本节不代为改判。**§3** 落三容器探针实测值表（全部定义在 base compose、三 overlay
> 零 healthcheck 字段 ⇒ 三 profile 共用同一套判据），记镜像内 `HEALTHCHECK` 与 compose 的覆盖
> 关系、`mj-agent check` 默认模式与 `--live` 的分界（从 `server/cli.py` 取证）、以及 pg 探针
> 不用 `pg_isready` 的裁定。**三处如实修正 / 登记**：(a) `sdd/adapters/docker-container.md`
> §Healthcheck schema 仍以 `pg_isready` 举例，与 compose 内的裁定相反，已在 §3 标明以实现为准；
> (b) `compose.contract.yml` 的 mj-agent-postgres 探针时序（30s / 3 / 10s）与实际（10s / 5 / 5s）
> 不符、mj-agent 缺 `timeout`、redis 无时序字段，且 `runtime.expected.yaml:20` 的
> `max_to_healthy_sec` 按 Dockerfile 的 20s 而非 compose 的 30s 推算——改契约是 canonical
> `declared-contract-change`，登记为 follow-up 不在本次动；(c) V5 的 `forbidden_in_image` 检查
> 只做 COPY 行字面量匹配，`COPY config/` 不触发，故它**不是**解密产物的全覆盖载体。**刻意不做
> 的一件事**：不给 §4 补 healthcheck 行——该面的 canonical enum 锚点属 Owner 姿态决策（按 #413
> 先例应扩既有 anchor 而非加第 11 项），判据与触发条件写在 §3 末段，§4 注同步指向它。*
