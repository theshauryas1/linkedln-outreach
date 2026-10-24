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

4. **NexusSwarm Fact Source & Outreach Brief (Strict Grounding - Zero Invention / Rounding)**:
   - When writing outreach messages for Shaurya, use only the facts in this brief.
   - Never claim to follow, admire or know someone's work unless that's verified, and never open with a line like that.
   - Pick one or two facts that fit the person's role or company, and don't dump everything.
   - Never state a number that isn't listed here.
   - Don't put a pitch or CV in the first message, and output only the message text.
   - Share the repo link only after the person replies or asks, or in a follow-up after applying.
   - **Never say NexusSwarm is deployed or live**, because it isn't right now.
   - **Platform & Architecture**: NexusSwarm is a 28-agent hierarchical platform, with executive, manager and worker agents, that automates requirements to deployment. It's built with AutoGen, FastAPI, React and TypeScript, NVIDIA NIM and MCP servers, and it has a dynamic model router, an LLM gateway and guardrails against prompt injection, secret leakage and hallucinated imports.
   - **Model Router**: The router cut average task time by 62% on NVIDIA NIM's free tier, from roughly 45 seconds to roughly 17, and the message must always say free tier.
   - **Evaluation Suite**: The eval suite has 107 tasks across 9 categories, with 100 used per run.
   - **Resilience Suite**: The resilience suite blocked 4 attack tests, covering hallucination traps, prompt injection, remote code execution patterns and a CVE plus fake package combo, plus one deployment-penalty scoring check. **Never say 4 of 5 attacks blocked**.
   - **Agent Count**: If the README says 31 agents, the public number is still 28 core agents, and the 3 validation agents are a detail only if asked.

5. **Mandatory Outreach Message Order & Golden Example**:
   - Every message uses this order, in two or three sentences:
     * One, name NexusSwarm and its architecture: a 28-agent hierarchical platform of executive, manager and worker agents.
     * Two, name one or two features that fit the reader's role: model router, LLM gateway, guardrails, or the eval suite across 9 categories.
     * Three, give one verified result: 62% lower average task time on NVIDIA NIM's free tier, roughly 45 seconds to roughly 17, or 4 attack tests blocked.
     * Four, give one plain sentence of what that means technically, never an invented business number.
     * Then the ask.
     * No em dashes, no link, never say deployed or live.
   - **Golden Architect Example**:
     > "Hi Alex, I came across your profile and your work on multi-agent systems at Cohere. I built NexusSwarm, a 28-agent hierarchical platform of executive, manager and worker agents, with a dynamic model router and LLM gateway. Routing cut average task time by 62% on NVIDIA NIM's free tier, from roughly 45 seconds to roughly 17, so simple tasks no longer wait on a large model. I'm exploring junior AI engineering roles, open to remote or relocation, and wondered if your team has openings."
