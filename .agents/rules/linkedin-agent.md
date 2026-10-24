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
- **Experience Portfolio (Strict Grounding - Zero Invention / Rounding)**:
  * **NexusSwarm (Personal Project)**: 28-agent hierarchical platform (AutoGen, FastAPI, React/TS, NVIDIA NIM, MCP) automating requirements to deployment; dynamic model router cut average task time by 62% on NVIDIA NIM's free tier (~45s to ~17s; message must always say free tier); LLM gateway with guardrails blocking 4 attack tests; 107-task eval suite across 9 categories. NEVER say deployed or live.
  * **Greybox (Current Professional Role - AI Product Developer)**: Agentic AI system on GCP with hybrid keyword-and-semantic retrieval across ~2,000 video transcripts, 66.7% top-3 accuracy, 100% groundedness, 81.4/100 persona-fidelity score.
  * **Brain MRI Tumor Classification (Personal Project - Computer Vision)**: 18,000-plus image brain MRI dataset, 5 CNN architectures, reliability-ranking AI agent, Grad-CAM explainability.
  * **Clinical Reasoning Engine (Personal Project - Healthcare NLP)**: Clinical NLP reasoning engine, 94.2% top-1 and 100% top-3 diagnostic accuracy across 1,000-case benchmark, zero hallucinated evidence.
  * **IIIT Pune (Education / Academic Background)**: B.Tech in Computer Science and Engineering from IIIT Pune.
- **Role-Based Message Structure**:
  1. Personalized 1-sentence opening observation based on profile facts (`Hi [Name], noticed your focus on [specific tech/system] at [Company].`).
  2. 1 or 2 matching projects/experiences from the portfolio above tailored to the reader's role.
  3. The ask: `I'm exploring junior AI engineering roles, open to remote or relocation, and wondered if your team has openings.`
  No em dashes, no link, never say deployed or live, strictly junior AI engineer roles.


