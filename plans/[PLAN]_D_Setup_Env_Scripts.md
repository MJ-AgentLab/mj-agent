---
type: plan
summary: PLAN D — 实现 scripts/setup-env.ps1 与 encrypt-secrets.ps1（Phase 0 / PR2 姊妹交付物）
owner: ranzuozhou
created: 2026-04-24
updated: 2026-04-30
state: completed
track: code
related:
  - ../README.md
  - ../.env.example
  - ../.gitignore
  - ../src/mj_agent/llm.py
  - ../src/mj_agent/config.py
  - ./[PLAN]_B_PR2_DB_Access_Doc.md
external:
  - D:/workspace/10-software-project/projects/mj-system/develop/scripts/setup-env.ps1
  - D:/workspace/10-software-project/projects/mj-system/develop/scripts/encrypt-secrets.ps1
  - D:/workspace/10-software-project/projects/mj-system/develop/config/secrets.example
---

## Context — 为什么现在做

`.env.example` 在第 35、68、79 行三处明示："此字段由 `scripts/setup-env.ps1` 从 `config/secrets.enc` 解密注入"。`README.md:44` 与 `src/mj_agent/llm.py:35` 也已经在文案里引用了该脚本的存在，但 **脚本本体尚未落地**。当前 Phase 0 的新开发者只能手工复制 `.env.example` 到 `.env` 再把 Ark Key 粘贴进去 —— 这个空档正是 `[PLAN]_B_PR2_DB_Access_Doc.md` 要在 PR2 关闭的；本 PLAN D 是 PR2 的姊妹交付物。

本计划在 mj-agent 仓内新建 `config/` 与 `scripts/` 目录，参照 `mj-system` 已上线、经过验证的 **OpenSSL AES-256-CBC + PBKDF2** 方案，最小化复用而非重写。

## 决策前提（已确认）

| 决策 | 选择 | 理由 |
| --- | --- | --- |
| 解密口令 | **独立于 mj-system** | 契合 ADR-006 数据边界隔离精神；mj-system 口令泄漏时 mj-agent 凭据仍安全 |
| 脚本范围 | **最小集**：setup-env + encrypt-secrets | Phase 0 够用；`verify-env.ps1` / `rotate-secrets.ps1` 按需再加 |
| `secrets.example` | **创建**（committed） | 明文 schema，新管理员能直接上手；与 mj-system 对称 |

## 交付物

### 新增文件

| 路径 | 提交状态 | 说明 |
| --- | --- | --- |
| `scripts/setup-env.ps1` | ✅ commit | 解密 + 幂等合并到 `.env` |
| `scripts/encrypt-secrets.ps1` | ✅ commit | 管理员加密工具 |
| `config/secrets.example` | ✅ commit | 明文 schema，列出 4 个密钥名 |
| `config/secrets.enc` | ✅ commit | 首次由管理员运行 `encrypt-secrets.ps1` 生成并提交；PR 中可先占位 |
| `config/secrets.conf` | ❌ gitignored | `.gitignore:22` 已经预留排除 |
| `config/README.md` | ✅ commit | 简短说明"如何获取口令 / 如何轮换" |

### 修改文件

| 路径 | 修改内容 |
| --- | --- |
| `README.md:44` | 把"手工 copy .env.example"替换为 "`.\scripts\setup-env.ps1`"，保留一句 fallback 提示 |
| `.gitignore` | 复核 `config/secrets.conf` 已排除（line 22）；无需新增 |
| `plans/[PLAN]_B_PR2_DB_Access_Doc.md` | 本 PLAN 不改，留给 PLAN B 作者在 PR2 文档中引用 `setup-env.ps1` |

## 实现要点

### 1. `scripts/setup-env.ps1`（约 220 行）

**直接复用** mj-system `setup-env.ps1` 骨架（源文件：`D:\workspace\10-software-project\projects\mj-system\develop\scripts\setup-env.ps1`），仅作以下 mj-agent 特化调整：

- **第 37 行 项目根校验**：`pyproject.toml` 存在性检查原样复用（mj-agent 同样是 uv 工程）
- **第 59-78 行 `Find-OpenSSL`**：**完全原样复用** —— 优先 Git for Windows 的 openssl，回避 Anaconda 构建差异导致的 bad-decrypt。这段已在 mj-system 生产环境验证，不要改
- **第 90 行 标题**：`"MJ System — .env Setup"` → `"mj-agent — .env Setup"`
- **第 120-123 行 空密钥防御**：保留 —— 若解密出的 `secrets.conf` 值全空（例如误把 `secrets.example` 当 `secrets.conf` 加密），脚本明确报错退出，避免静默写空密钥到 `.env` 又在 `llm.py:35` 反向指向脚本的死循环 UX
- **第 128-178 行 幂等对比**：完全复用。`[SKIP] / [CHANGED] / [NEW]` 三态输出 + `-Force` 覆盖。Phase 0 期间开发者频繁 `git pull` + 重跑脚本，此逻辑避免无谓覆盖确认
- **第 180-200 行 regex 合并**：完全复用。对每个 secret key 用 `(?m)^KEY=.*$` 匹配 `.env.example` 全文并替换，未匹配则追加并告警（保护未来新增密钥时不静默丢失）
- **第 207-212 行 "Next steps" —— 必须重写**：
  - 删除 mj-ops / mj-git plugin 脚本引用（mj-agent 无 plugin 密钥层）
  - 替换为：
    ```
    Next steps:
      1. Review .env and adjust POSTGRES_DEV_HOST / MJ_CONFIG_PROFILE if needed
      2. uv sync
      3. uv run langgraph dev
    ```
- **第 200 行 写入方式**：`[System.IO.File]::WriteAllText($EnvFile, $envContent, [System.Text.UTF8Encoding]::new($false))` —— UTF-8 无 BOM，保留。pydantic-settings 从 CWD 读 `.env` 工作正常
- **第 217-219 行 `finally` 清理**：保留。任何路径下都删除临时 `config/secrets.conf`

### 2. `scripts/encrypt-secrets.ps1`（约 100 行）

**完整复用** mj-system `encrypt-secrets.ps1`，仅改一处：

- **第 65 行 标题**：`"MJ System — Encrypt Secrets"` → `"mj-agent — Encrypt Secrets"`

加密命令（第 83 行）保持不变：
```
openssl enc -aes-256-cbc -pbkdf2 -md sha256 -salt -in secrets.conf -out secrets.enc -pass stdin
```
与 setup-env.ps1 第 99 行的解密参数完全对应，跨项目结构同构。

### 3. `config/secrets.example`

```
# mj-agent Secrets — 4 application-level variables
# Independent from mj-system (separate password, separate secrets.enc).
# Copy to secrets.conf, fill values, run .\scripts\encrypt-secrets.ps1

# §1 Database — analyst read-only role (ADR-006 L4)
POSTGRES_ANALYST_USER=
POSTGRES_ANALYST_PASSWORD=

# §2 LLM Provider — Volcengine Ark (fail-fast if missing)
ARK_API_KEY=

# §3 Observability (optional; leave blank if LANGSMITH_TRACING=false)
LANGSMITH_API_KEY=
```

**注意未列入** `POSTGRES_USER` / `POSTGRES_PASSWORD`（admin 账号）——  ADR-006 明确 agent 运行时不应接触，留在 `.env.example:19-20` 为空即可，脚本永不注入。

### 4. `config/README.md`（新增，约 40 行）

简短说明：
- 口令从哪里拿（团队内部渠道 —— 保持 placeholder，不写具体工具名）
- 新增密钥流程：编辑 `secrets.conf` → 跑 `encrypt-secrets.ps1` → `git add config/secrets.enc`
- 轮换流程：同上
- 为什么与 mj-system 独立口令：引用 ADR-006 数据边界隔离精神

### 5. `README.md:44` 修改

当前：
```
# 2. 准备 .env（Phase 0：手工 copy .env.example；PR2 起用 setup-env.ps1）
```

改为：
```
# 2. 准备 .env（解密团队密钥注入）
.\scripts\setup-env.ps1
# 没有团队口令？向管理员申请，或手工 copy .env.example 并填入本地可用的 ARK_API_KEY（不推荐）
```

## 关键参考文件

| 用途 | 文件 | 重点行 |
| --- | --- | --- |
| decrypt 直接参照 | `D:\...\mj-system\develop\scripts\setup-env.ps1` | 全部；重点 59-78、99-100、128-178、180-200 |
| encrypt 直接参照 | `D:\...\mj-system\develop\scripts\encrypt-secrets.ps1` | 全部 |
| schema 模板参照 | `D:\...\mj-system\develop\config\secrets.example` | 结构即可，内容重写 |
| 注入契约来源 | `.env.example` | 19-20（留空不注入）、36-37、69、80 |
| 已承诺的外部引用 | `src/mj_agent/llm.py` | 35-36（错误信息中引用脚本名） |
| pydantic-settings 装载 | `src/mj_agent/config.py` | `env_file=".env"` 从 CWD 读取 —— 脚本写仓库根即可 |
| gitignore 预留 | `.gitignore` | 17-19、22 |

## 跨项目隔离说明

mj-system 脚本默认后续还要跑 MCP plugin 的 `setup-ops-env.ps1` / `setup-git-env.ps1`（见 mj-system setup-env.ps1 210-211 行的 "Next steps" 文案）。mj-agent 无此分层，**此段文案必须彻底改写**，否则会把开发者引到不存在的路径。

两项目的加密文件 **故意不交叉可解**（独立口令），满足 ADR-006 安全边界精神 —— 即便 mj-system 口令泄漏，mj-agent 的 analyst 凭据与 Ark Key 仍受保护。mj-agent 与 mj-system 是独立项目（ADR-008），各自拥有 secrets 解密管道；同时部署在一台开发机时，分别运行两仓的 `setup-env.ps1`——这不是缺陷，是刻意设计。

## 端到端验证（执行人在实现完成后按序执行）

1. **静态 lint**
   ```powershell
   powershell -NoProfile -Command "& { `$e = `$null; [System.Management.Automation.Language.Parser]::ParseFile('scripts\setup-env.ps1', [ref]`$null, [ref]`$e); `$e }"
   # 返回空数组即通过
   ```

2. **首次加密（模拟管理员）**
   - `cp config/secrets.example config/secrets.conf`
   - 编辑 `secrets.conf`，填入测试值（`ARK_API_KEY=test-fake-key` 等）
   - `.\scripts\encrypt-secrets.ps1` → 输入口令两次
   - 断言：`config/secrets.enc` 生成；`config/secrets.conf` 按脚本提示手工删除

3. **首次解密（模拟开发者）**
   - 删除 `.env`（若存在）
   - `.\scripts\setup-env.ps1` → 输入相同口令
   - 断言：`.env` 被创建；4 个密钥被注入；`ARK_API_KEY=test-fake-key`；`POSTGRES_USER` 仍为空（未被注入）；`config/secrets.conf` 不残留

4. **幂等重跑**
   - 再跑一次 `.\scripts\setup-env.ps1`，同口令
   - 断言：输出 `[SKIP] .env is already up-to-date`，不进入覆盖确认

5. **篡改触发变更检测**
   - 编辑 `.env`，改 `ARK_API_KEY=changed-value`
   - 再跑 `.\scripts\setup-env.ps1`
   - 断言：输出 `[CHANGED] ARK_API_KEY = chan**** -> test****` 并询问确认；输入 `n` 拒绝后不覆盖

6. **错误口令**
   - `.\scripts\setup-env.ps1` 输入错误口令
   - 断言：输出 `[ERROR] Decryption failed — wrong password or corrupted file.`；退出码 1；`config/secrets.conf` 不残留

7. **缺 openssl 降级（可跳过）**
   - 临时将 `git.exe` 目录从本进程 PATH 移除
   - 断言：fallback 到 PATH 查找；仍能找到或给出明确错误

8. **Python 端联动**
   - 在步骤 3 之后执行：
     ```
     uv run python -c "from mj_agent.config import settings; print(bool(settings.ark_api_key.get_secret_value()))"
     ```
   - 断言：输出 `True`（pydantic-settings 成功从 `.env` 读到）

9. **pytest smoke（可选；需真实密钥）**
   - 用真实 `ARK_API_KEY` 重跑步骤 2-3
   - `uv run pytest tests/smoke -m smoke`
   - 断言：LLM smoke 测试通过（证明整条注入链路端到端工作）

## Out of Scope（刻意不做）

- **`verify-env.ps1`** —— 用户选择最小集；留待 Phase 1
- **`rotate-secrets.ps1`** —— 无主动轮换需求；当前以"重新加密并覆盖 `config/secrets.enc`"作为事实上的轮换路径
- **bash 版本脚本** —— Phase 0 全员 Windows，暂不维护 `.sh` 等价物
- **CI 集成** —— CI 走 GitHub Secrets（与 mj-system 同策略），不跑 `setup-env.ps1`
- **ADR-006/008/009 正文落地** —— 仅在 `config/README.md` 引用名称；正文在 mj-system 侧，由另外的 PLAN C 负责回填到 mj-agent

## 执行结果（2026-04-30）

分支：`maintain/setup-env-secrets`（worktree-style，从 `develop@7322a5c` 切出）。

### §交付物 实际产出

| 文件 | 状态 | 说明 |
| --- | --- | --- |
| `scripts/setup-env.ps1` | ✅ 落地 | 复用 mj-system 骨架，标题改 `mj-agent — .env Setup`，Next steps 重写为 `Review .env / uv sync / langgraph dev`（去 mj-ops/mj-git plugin 引用） |
| `scripts/encrypt-secrets.ps1` | ✅ 落地 | 仅改标题为 `mj-agent — Encrypt Secrets` |
| `config/secrets.example` | ✅ 落地 | 4-key schema：`POSTGRES_ANALYST_{USER,PASSWORD}` + `ARK_API_KEY` + `LANGSMITH_API_KEY` |
| `config/README.md` | ✅ 落地 | 口令获取/轮换流程 + 与 mj-system 独立口令的 ADR-006 边界理由 |
| `config/secrets.enc` | ✅ 落地 | 管理员首次加密产物，AES-256-CBC + PBKDF2 |
| `README.md:44` | ✅ 改 | Quick start §2 切到 `.\scripts\setup-env.ps1`，保留 fallback 提示 |

### §交付物 之外的修复（方案 C）

执行过程中发现 **`uv run langgraph dev` 在中文 Windows 上启动 fail**：

```
File "...\dotenv\parser.py", line 71, in __init__
    self.string = stream.read()
UnicodeDecodeError: 'gbk' codec can't decode byte 0xaf in position 99
```

根因：`langgraph_api/cli.py:222` 内部 `DotEnv(dotenv_path=env).dict()` 调用 python-dotenv 时 **不传 `encoding`**，落到 Python `open()` 默认编码；中文 Windows 默认 GBK 撞 UTF-8 字节 0xaf 直接抛 `UnicodeDecodeError`。

`setup-env.ps1` 第 200 行 UTF-8 无 BOM 写入是对的（pydantic-settings 也期望 UTF-8）；问题在 `.env.example` 模板的中文注释会被原样拷进 `.env`。

**纳入同一 maintain 分支的判断**：本分支目标是"setup-env 链路在 mj-agent 上端到端可用"，未消除 `langgraph dev` 启动崩溃就不算交付完成；方案 C 是必要的临门一脚。

**改法**：所有中文注释翻成英文，`##### N. Title #####` 章节风格保持，变量名 / 默认值 / 章节顺序 0 改动。验证：3164 bytes、0 个 non-ASCII 字节。

未来若团队希望恢复中文注释 / 中文 README，应在上游推 langgraph_api PR 让 `DotEnv()` 显式传 `encoding='utf-8'`，或本仓引入 `PYTHONUTF8=1` 启动包装层 —— 见 `[ISSUE] Python_Dotenv_GBK_On_Chinese_Windows`（如未来再撞到再起）。

### §端到端验证 实证矩阵

| § | 描述 | 状态 | 备注 |
| --- | --- | --- | --- |
| §1 | 静态 lint | ✅ | `Parser::ParseFile()` 0 errors（两脚本各跑一次） |
| §2 | 首次加密 | ✅ | `secrets.enc` 已生成；`secrets.conf` 按提示手工删除 |
| §3 | 首次解密 + 注入 | ✅ | `[OK] Decrypted 4 secrets` + `[Done] .env generated with 4 secrets injected` |
| §4 | 幂等重跑 | ✅ | 4 × `[SKIP]` + `[SKIP] .env is already up-to-date` |
| §5 | 篡改 [CHANGED] 检测 | ✅ | 第一次因 `Set-Content -NoNewline` 误用导致 `.env` 折成单行，4 key 全判 `[NEW]`（脚本行为正确，是测试方法 bug）；去掉 `-NoNewline` 后 `[CHANGED] ARK_API_KEY = chan**** -> 4541****` + 其余 3 个 `[SKIP]`，输 `n` 触发 `[ABORT]` |
| §6 | 错口令 catch | ✅ | openssl `bad decrypt` → 脚本 `[ERROR] Decryption failed`；`$LASTEXITCODE = 1`；`Test-Path config\secrets.conf = False`（`finally` 块清理） |
| §7 | openssl PATH fallback | ⏸️ skip | PLAN 允许跳过；本机 Git for Windows openssl 可用 |
| §8 | Python 联动 | ✅ 隐含 | `uv run langgraph dev` 成功 `Application started up in 11.743s`（make_graph → make_llm 隐含验证 settings + ark_api_key） |
| §9 | smoke | ⏸️ 视真实 key | 当前 `secrets.enc` 是测试值，未跑 `pytest tests/smoke -m smoke` |

### Commit 拆分

按 STANDARD §6.4 拆三个 commit（同一 maintain 分支内合规：§5.2 允许 `infra` + `docs`）：

1. `infra(infra): land setup-env.ps1 secrets-injection toolchain (PLAN D)` —— 主交付物（c8be5e2）
2. `infra(infra): convert .env.example to ASCII-only` —— 方案 C（94e9645）
3. `docs: backfill PLAN D execution log + CHANGELOG entry + CLAUDE.md note` —— 文档回填（本提交）
