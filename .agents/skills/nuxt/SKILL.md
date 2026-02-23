---
name: nuxt
description: Ground Nuxt implementation help in official Nuxt documentation indexed by llms.txt. Use when users ask about Nuxt 4/3 setup, routing, data fetching, rendering modes, Nitro server APIs, composables, modules, deployment, testing, or migration/upgrade work and answers should include nuxt.com source links.
---

# Nuxt Skill

Use this skill to answer Nuxt questions with official documentation links instead of memory-only guidance.

## Workflow

1. Read `references/source-map.md` first to locate likely pages quickly.
2. Read `references/llms.txt` when the topic is not in the map or needs broader coverage.
3. Open the linked raw markdown pages from `nuxt.com/raw/docs/...` before giving high-confidence implementation advice.
4. Prefer Nuxt 4.x guidance by default; switch to Nuxt 3.x only when the user or repository clearly targets Nuxt 3.
5. Include concrete source links in the final answer and explicitly state the version context.

## Search Pattern

Use targeted text search on the local index file:

```powershell
Select-String -Path "skills/nuxt/references/llms.txt" -Pattern "useFetch|runtime config|route rules"
```

Then open the most relevant raw docs links from matched lines.

## Answer Rules

- State assumptions when version is unclear.
- Highlight version-specific differences (Nuxt 4 vs Nuxt 3) when they affect behavior.
- Prefer docs pages over blog posts for API semantics.
- Use blog posts mainly for release context and timelines.
