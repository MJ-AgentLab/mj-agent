# 原生开发技能

同名技能在 `skills/` 直接维护，入口见 [技能索引](skills/SKILL_INDEX.md)。
共享边界见 [执行说明](references/execution-boundaries.md)。维护者为 Codex 与 Owner；不经生成器同步。
普通技能维护遵循任务授权；infra 冻结、runtime 目标、政策、原生配置及受保护动作仍须 Owner 决策。
运行 `python scripts/sdd/check_native_skills.py` 与 `python scripts/sdd/check_codex_native.py`；静态通过不证明宿主加载或服务可用。
