---
trigger: always_on
---

# LinkedIn Agent Skill Rules

Automatically route and execute LinkedIn workflows based on user prompt intent without requiring explicit mentions of skill names or slash commands:

- **LinkedIn Post Generation**: When the user requests a post or content for LinkedIn, follow the `li-post` procedure (3 hooks from `hooks.json`, single clear draft, humanize).
- **Text Humanization**: When the user asks to remove AI tells, em dashes, or make text sound natural/human, follow `li-human` (run `humanize.py` and `detect.py`).
- **Weekly Strategy & Planning**: Route to `li-plan`.
- **Comments & Engagement**: Route to `li-comment` (for commenting on others) or `li-reply` (for replies under own posts).
- **Carousels & Multi-Slide**: Route to `li-carousel`.
- **Profile / Headline Reviews**: Route to `li-profile`.
- **Outreach & DMs**: Route to `li-dm`.
- **Content Repurposing**: Route to `li-repurpose`.
- **Analytics & Post Performance**: Route to `li-audit`.

## Mandatory Grounding & Seniority Rules:
- **No Unverified Familiarity**: Never claim unconfirmed history or familiarity (no "I've been following your work", "impressed by [company]", "came across your work"). Open strictly based on concrete, verified observations from their profile (role, tech, specific system built).
- **Junior AI Engineer Only**: Always position as Junior AI Engineer / early-career builder.
- **Zero Em Dashes**: Hyphens and commas only.
- **NexusSwarm Fact Source (Strict Grounding - Zero Invention / Rounding)**: Use only facts in this brief; never invent, round up, or infer numbers/features. NexusSwarm is a 28-agent hierarchical platform (executive, manager, worker agents) automating requirements to deployment; built with AutoGen, FastAPI, React/TypeScript, NVIDIA NIM, MCP servers; dynamic model router cut average task time by 62% on NVIDIA NIM's free tier (from ~45s to ~17s; message must always say free tier); LLM gateway with guardrails against prompt injection, secret leakage, hallucinated imports; eval suite has 107 tasks across 9 categories (100 used per run); resilience suite blocked 4 attack tests (traps, injection, RCE patterns, CVE+fake package combo) + 1 deployment penalty check. NEVER say NexusSwarm is deployed or live (it is not right now). NEVER say 4 of 5 attacks blocked (say blocked 4 attack tests). Public number is 28 core agents (3 validation agents only if asked). No pitch/CV in first message; repo link shared only after reply/ask or follow-up after applying.
