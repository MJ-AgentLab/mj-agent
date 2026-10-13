---
type: sdd-adapter
adapter: development-skill
state: active
version: "1.0"
owner: ranzuozhou
created: 2026-09-18
updated: 2026-10-12
track: engineering-workflow
ai_visibility: source-of-truth
---

# Native development skills

Rule body: `policies/development-skills.md`; discovery/index: `.agents/skills/SKILL_INDEX.md`.
Name/description schema, references and frozen infra contracts are checked by
`scripts/sdd/check_native_skills.py`. Runtime skill/prompt/SQL/catalog adapters are unchanged.
Owner chat decisions bind the actual result/SHA; Agent executes the platform review using a distinct Owner identity. Independent Agent review precedes project-only host trust activation through normal mechanisms. Existing secrets remain unread; only new single-repository App material is handled by the private backend. Unsupported/refused routes remain unverified; hooks fail closed.
