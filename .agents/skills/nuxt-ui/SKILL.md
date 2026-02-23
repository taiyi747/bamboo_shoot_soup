---
name: nuxt-ui
description: Ground Nuxt UI implementation help in official Nuxt UI documentation indexed by llms.txt. Use when users ask about Nuxt UI components, composables, theming, Tailwind Variants customization, Nuxt/Vue installation, integrations (icons, color mode, i18n, SSR), or migration across Nuxt UI versions, and answers should include ui.nuxt.com source links.
---

# Nuxt UI Skill

Use this skill to answer Nuxt UI questions with official documentation links instead of memory-only guidance.

## Workflow

1. Read `references/source-map.md` first to locate likely pages quickly.
2. Read `references/llms.txt` when the topic is not in the map or needs broader coverage.
3. Open the linked raw markdown pages from `ui.nuxt.com/raw/docs/...` before giving high-confidence implementation advice.
4. Prefer Nuxt UI v4 guidance by default; if the project is on older versions, use migration docs and call out version gaps.
5. Distinguish Nuxt integration from plain Vue integration when installation or runtime behavior differs.
6. Include concrete source links in the final answer and explicitly state version/framework context.

## Search Pattern

Use targeted text search on the local index file:

```powershell
Select-String -Path "skills/nuxt-ui/references/llms.txt" -Pattern "Form|Table|Modal|theme|css variables|useToast|installation/vue"
```

Then open the most relevant raw docs links from matched lines.

## Answer Rules

- State assumptions when framework context is unclear (`Nuxt` vs `Vue`).
- Highlight version-specific differences when migration docs indicate API/theme changes.
- Prefer component/composable API pages over marketing summaries for implementation details.
- Prefer official docs pages over third-party content for API semantics.
