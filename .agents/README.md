# 原生开发技能

同名技能在 `skills/` 直接维护，入口见 [技能索引](skills/SKILL_INDEX.md)。
共享边界见 [执行说明](references/execution-boundaries.md)。维护者为 Codex 与 Owner；不经生成器同步。
任务内技能维护自主；infra冻结按canonical摘要成组更新。runtime/合同按语义影响分类，治理/信任/权限实质变化由Owner决定，独立Agent配置/守卫负例核验，执行Agent按正常宿主机制启用项目范围信任并核加载；新App材料只经受控后台，既有秘密不读取。执行依据ADR-042。
运行 `python scripts/sdd/check_native_skills.py` 与 `python scripts/sdd/check_codex_native.py`；静态通过不证明宿主加载或服务可用。
