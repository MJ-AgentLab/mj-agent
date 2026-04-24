# mj-agent

Python 3.13 项目，使用 [`uv`](https://github.com/astral-sh/uv) 管理依赖与运行时。

## Clone

GitHub（默认 `origin`）：

```bash
git clone https://github.com/MJ-AgentLab/mj-agent.git
cd mj-agent
```

Gitee 镜像（远端名 `gitee`）：

```bash
git clone https://gitee.com/ranzuozhou/mj-agent.git
cd mj-agent
```

为已克隆的仓库追加双远端：

```bash
git remote add origin https://github.com/MJ-AgentLab/mj-agent.git
git remote add gitee  https://gitee.com/ranzuozhou/mj-agent.git
```

使用 PowerShell 脚本克隆 bare 仓库：

```powershell
powershell -ExecutionPolicy Bypass -File .\mj-agent-clone-bare.ps1 `
    -RepoUrl https://github.com/MJ-AgentLab/mj-agent
```

## Quick start

```bash
uv sync
uv run python main.py
```
