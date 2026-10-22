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
- **NexusSwarm Fact Source (Strict Grounding - Zero Invention / Rounding)**: Use ONLY verified facts: 28-agent multi-agent platform on AutoGen, FastAPI, React and NVIDIA NIM; executive/manager/worker hierarchy automating software and AI engineering from requirements through deployment; dynamic model router cut average task time by 62% on NIM's free tier by routing tasks to right-sized models instead of one large model; guardrails against prompt injection, secret leakage, hallucinated imports; evaluated with a 100-task, 9-category benchmark suite and a resilience test report where 4 of 5 attack tests were blocked. Never invent, round up, or infer others.
