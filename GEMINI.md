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

4. **NexusSwarm Fact Source (Strict Grounding - Zero Invention / Rounding)**:
   - Use ONLY these verified facts; never invent, round up, or infer others:
     * **Platform**: 28-agent multi-agent platform on AutoGen, FastAPI, React and NVIDIA NIM.
     * **Architecture**: Executive/manager/worker hierarchy automating software and AI engineering from requirements through deployment.
     * **Model Router**: A dynamic model router cut average task time by 62% on NIM's free tier by routing tasks to right-sized models instead of one large model.
     * **Guardrails**: Includes guardrails against prompt injection, secret leakage and hallucinated imports.
     * **Evaluation**: Evaluated with a 100-task, 9-category benchmark suite and a resilience test report where 4 of 5 attack tests were blocked.
