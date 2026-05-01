# mj-agent secrets

本目录承载 mj-agent 运行所需的 4 个敏感变量的加密分发与解密注入：
`POSTGRES_ANALYST_USER` / `POSTGRES_ANALYST_PASSWORD` /
`ARK_API_KEY` / `LANGSMITH_API_KEY`。

## 文件清单

| 文件 | 状态 | 用途 |
| --- | --- | --- |
| `secrets.example` | committed | 明文 schema，列出所有应注入的密钥名（值留空） |
| `secrets.enc` | committed | AES-256-CBC + PBKDF2 加密的密钥包，由 `..\scripts\encrypt-secrets.ps1` 生成 |
| `secrets.conf` | gitignored | 解密或编辑过程中的明文中间产物，**永不提交**（`.gitignore` 已排除） |

## 获取口令

口令通过团队内部安全渠道分发，不在本仓出现、不在群聊广播、不进 issue。
新成员加入项目时向项目负责人申请。

## 开发者：从加密包恢复 .env

```powershell
.\scripts\setup-env.ps1
# 提示输入口令，脚本自动解密、合并到 .env、清理临时 secrets.conf
```

幂等：重跑会比对每个变量并以 `[SKIP]` / `[CHANGED]` / `[NEW]` 标注，
仅在差异存在时才请求覆盖确认。强制覆盖加 `-Force`。

## 管理员：新增或轮换密钥

```powershell
# 1. 准备明文
cp config\secrets.example config\secrets.conf
# 编辑 secrets.conf 填入新值（或修改既有值）

# 2. 加密
.\scripts\encrypt-secrets.ps1
# 提示输入口令两次（一致才会写入）

# 3. 提交加密包，删除明文
git add config\secrets.enc
Remove-Item config\secrets.conf  # 切勿提交

# 4. 通过安全渠道告知团队"口令已轮换"
```

新增密钥时，需要在三处同步登记：
- `config/secrets.example` 增加键名（值留空）
- `.env.example` 增加键名（值留空，注释中写明"由 setup-env.ps1 注入"）
- `src/mj_agent/config.py` 的 `Settings` 类增加对应字段

## 与 mj-system 的口令独立

mj-agent 的 `secrets.enc` 与 mj-system 的同名文件**故意采用不同口令**，
契合 ADR-006 数据边界隔离精神：mj-system 口令泄漏时 mj-agent 的
`analyst` 凭据与 Ark API key 仍受保护。co-deployment 场景下需要
**依次**运行两个仓的 `setup-env.ps1`，这是刻意设计而非缺陷。
