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
- **Inbox Sorting & Responses**: Route to `li-inbox`.
- **Content Repurposing**: Route to `li-repurpose`.
- **Analytics & Post Performance**: Route to `li-audit`.
