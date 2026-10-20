# Workspace Guidelines: LinkedIn & Content Automation

## Automatic Skill Activation (No Explicit Mentions Required)

Whenever the user's request involves LinkedIn, social content, or humanizing text, automatically activate and follow the corresponding skill procedures without waiting for or requiring the user to type slash commands or name the skills:

1. **Writing Posts**: When asked to draft, write, or turn an idea into a LinkedIn post:
   - Follow the `li-post` workflow.
   - Select 3 distinct hook formulas from `hooks.json`, draft on the strongest, run through humanizer, and present in a copy-ready block.

2. **Humanizing & AI Detection**: When asked to review, edit, or clean any text to sound natural, less robotic, remove em dashes, or avoid AI detection:
   - Follow the `li-human` workflow.
   - Strip invisible characters, collapse em dashes, replace slop words, and evaluate against the 5-check detection panel using `detect.py`.

3. **Content Planning**: When asked what to post, for a content calendar, or weekly planning:
   - Follow the `li-plan` workflow.

4. **Commenting**: When given someone else's post to comment on or engage with:
   - Follow the `li-comment` workflow.

5. **Reply Management**: When given comments on the user's posts to respond to:
   - Follow the `li-reply` workflow.

6. **Carousels & Document Posts**: When asked for slides, PDF carousels, or multi-card posts:
   - Follow the `li-carousel` workflow.

7. **Profile Optimization**: When asked to critique, rewrite, or score a LinkedIn headline, about section, or profile:
   - Follow the `li-profile` workflow and rubric.

8. **DMs & Connection Requests**: When asked to write connection notes, outreach messages, or follow-ups:
   - Follow the `li-dm` workflow.

9. **Inbox Triage**: When given incoming messages or connection requests to filter or reply to:
   - Follow the `li-inbox` workflow.

10. **Repurposing Content**: When given a long asset (video, transcript, newsletter, blog, or notes) to turn into LinkedIn content:
    - Follow the `li-repurpose` workflow.

11. **Content Audits**: When given analytics or past post performance data:
    - Follow the `li-audit` workflow.
