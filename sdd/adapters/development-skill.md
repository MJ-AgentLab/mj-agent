---
type: sdd-adapter
adapter: development-skill
state: active
version: "1.0"
owner: ranzuozhou
created: 2026-09-18
updated: 2026-09-18
track: engineering-workflow
ai_visibility: source-of-truth
---

# Native development skills

Rule body: `policies/development-skills.md`; discovery/index: `.agents/skills/SKILL_INDEX.md`.
Name/description schema, references and frozen infra contracts are checked by
`scripts/sdd/check_native_skills.py`. Runtime skill/prompt/SQL/catalog adapters are unchanged.
Owner approval and actual execution route are separate; hooks remain fail closed.
