# Workspace Guidelines: LinkedIn & Content Automation

## Automatic Skill Activation (No Explicit Mentions Required)

Whenever the user's request involves LinkedIn, social content, or humanizing text, automatically activate and follow the corresponding skill procedures without waiting for or requiring the user to type slash commands or name the skills:

1. **Writing Posts**: When asked to draft, write, or turn an idea into a LinkedIn post:
   - Follow the [`li-post`](file:///c:/New%20folder%20(2)/.agents/skills/li-post/SKILL.md) workflow.
   - Select 3 distinct hook formulas from `hooks.json`, draft on the strongest, run through humanizer, and present in a copy-ready block.

2. **Humanizing & AI Detection**: When asked to review, edit, or clean any text to sound natural, less robotic, remove em dashes, or avoid AI detection:
   - Follow the [`li-human`](file:///c:/New%20folder%20(2)/.agents/skills/li-human/SKILL.md) workflow.
   - Strip invisible characters, collapse em dashes, replace slop words, and evaluate against the 5-check detection panel using `detect.py`.

3. **Content Planning**: When asked what to post, for a content calendar, or weekly planning:
   - Follow the [`li-plan`](file:///c:/New%20folder%20(2)/.agents/skills/li-plan/SKILL.md) workflow.

4. **Commenting**: When given someone else's post to comment on or engage with:
   - Follow the [`li-comment`](file:///c:/New%20folder%20(2)/.agents/skills/li-comment/SKILL.md) workflow.

5. **Reply Management**: When given comments on the user's posts to respond to:
   - Follow the [`li-reply`](file:///c:/New%20folder%20(2)/.agents/skills/li-reply/SKILL.md) workflow.

6. **Carousels & Document Posts**: When asked for slides, PDF carousels, or multi-card posts:
   - Follow the [`li-carousel`](file:///c:/New%20folder%20(2)/.agents/skills/li-carousel/SKILL.md) workflow.

7. **Profile Optimization**: When asked to critique, rewrite, or score a LinkedIn headline, about section, or profile:
   - Follow the [`li-profile`](file:///c:/New%20folder%20(2)/.agents/skills/li-profile/SKILL.md) workflow and rubric.

8. **DMs & Connection Requests**: When asked to write connection notes, outreach messages, or follow-ups:
   - Follow the [`li-dm`](file:///c:/New%20folder%20(2)/.agents/skills/li-dm/SKILL.md) workflow.

9. **Inbox Triage**: When given incoming messages or connection requests to filter or reply to:
   - Follow the [`li-inbox`](file:///c:/New%20folder%20(2)/.agents/skills/li-inbox/SKILL.md) workflow.

10. **Repurposing Content**: When given a long asset (video, transcript, newsletter, blog, or notes) to turn into LinkedIn content:
    - Follow the [`li-repurpose`](file:///c:/New%20folder%20(2)/.agents/skills/li-repurpose/SKILL.md) workflow.

11. **Content Audits**: When given analytics or past post performance data:
    - Follow the [`li-audit`](file:///c:/New%20folder%20(2)/.agents/skills/li-audit/SKILL.md) workflow.

## Strict Grounding & Anti-Fabrication Rules for Outreach & DMs

1. **Never Claim Unverified Familiarity or False History**:
   - The generator must NEVER claim a relationship, familiarity, or history that isn't confirmed true.
   - Absolutely NO "I've been following your work", "I've been following [Company]'s work", "I came across your work", "I've been watching [Company]", or "I've been impressed by [Company]'s work".
   - Open based ONLY on concrete and verifiable facts from their profile: their actual role, what they specifically build, or a direct factual observation from their headline, about section, or company domain.

2. **Junior Seniority Level Only**:
   - Strictly identify as a Junior AI Engineer / Early-Career AI Engineer. Never claim or request senior roles.

3. **Clean Typography**:
   - Zero em dashes (`—`). Use hyphens (`-`) or commas (`,`).

4. **Experience & Project Portfolio (Strict Grounding - Zero Invention / Rounding)**:
   - When writing outreach messages for Shaurya, select 1 or 2 relevant projects or experiences tailored to the person's role and domain.
   - **NexusSwarm (Personal Project)**: 28-agent hierarchical platform of executive, manager and worker agents automating requirements to deployment. Built with AutoGen, FastAPI, React/TypeScript, NVIDIA NIM, and MCP servers. Dynamic model router cut average task time by 62% on NVIDIA NIM's free tier, from roughly 45 seconds to roughly 17, so simple tasks no longer wait on a large model. Eval suite has 107 tasks across 9 categories (100 used per run). Resilience suite blocked 4 attack tests (hallucination traps, prompt injection, RCE patterns, CVE+fake package combo). NEVER say deployed or live.
   - **Greybox (Current Professional Role - AI Product Developer)**: Designing and deploying an agentic AI system on Google Cloud combining hybrid keyword-and-semantic retrieval across roughly 2,000 video transcripts for on-brand content generation. Validated in a pilot study achieving 66.7% top-3 retrieval accuracy, 100% groundedness with zero hallucinated techniques, and an 81.4/100 persona-fidelity score.
   - **Brain MRI Tumor Classification (Personal Project - Computer Vision)**: Owned the full pipeline for an 18,000-plus image brain MRI dataset, training and benchmarking five CNN architectures. Built an AI agent that ranks models by reliability rather than raw accuracy, selecting EfficientNet-B4, with Grad-CAM explainability for clinical interpretability.
   - **Clinical Reasoning Engine (Personal Project - Healthcare NLP)**: Built a clinical NLP reasoning engine turning unstructured discharge summaries into structured timelines with LLM-driven differential diagnosis, hitting 94.2% top-1 and 100% top-3 diagnostic accuracy across a 1,000-case benchmark, with every flagged finding grounded to exact source text and zero hallucinated evidence.
   - **IIIT Pune (Education / Academic Background)**: B.Tech in Computer Science and Engineering from Indian Institute of Information Technology, Pune (IIIT Pune).

5. **Mandatory Outreach Message Structure**:
   - One: Personalized 1-sentence opening observation based on profile facts (`Hi [Name], noticed your focus on [specific tech/system] at [Company].`).
   - Two: 1 or 2 matching projects/experiences from the portfolio above tailored to the recipient's role (e.g. NexusSwarm for agentic/systems/infra; Greybox for product/RAG/content; Clinical NLP for healthcare; Brain MRI for vision/radiology; IIIT Pune for alumni/peers).
   - Three: The ask: `I'm exploring junior AI engineering roles, open to remote or relocation, and wondered if your team has openings.`
   - Constraints: Zero em dashes, no links/URLs, never say deployed or live, strictly junior AI engineering roles, strict attribution (Greybox = current role; NexusSwarm, MRI, Clinical = personal projects; IIIT Pune = education). Never claim NexusSwarm was built at Greybox.
