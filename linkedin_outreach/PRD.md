# Product Requirements Document (PRD)
## Autonomous LinkedIn Outreach & Multi-Agent Intelligence Engine

**Project:** `linkedin_outreach`  
**System Version:** 2.1.0  
**Author:** AI Engineering & Automation  
**Status:** In Production / Active Deployment  
**Repository Path:** `c:\New folder (2)\linkedin_outreach`

---

## 1. Executive Summary & Vision

### 1.1 Problem Statement
Modern B2B LinkedIn outreach and professional networking suffer from three major bottlenecks:
1. **Exorbitant Software Costs**: SaaS tools (Expandi, Waalaxy, PhantomBuster) charge $100–$300/month while operating on cloud proxies that frequently trigger LinkedIn automated security blocks.
2. **AI Slop & Generic Messaging**: AI outreach generators produce verbose, pitch-heavy messages loaded with AI fingerprints (em dashes, corporate buzzwords, formulaic openings), driving reply rates below 2% and prompting recipient spam reports.
3. **Existing Connection Neglect**: Most outreach tools focus exclusively on cold connections. Re-engaging existing 1st-degree connections for career opportunities (internships, remote work, international relocation) is done manually, without structured follow-ups, regional filtering, or role personalization.

### 1.2 Product Vision
The **Autonomous LinkedIn Outreach Engine** is a free, self-hosted, browser-backed automation system equipped with a **Custom Model Context Protocol (MCP) Server**. It serves two distinct, parallel operational pipelines:
1. **Cold Outreach Pipeline**: Dispatches targeted connection requests (<200-char notes) and multi-step intro/follow-up sequences to new prospects.
2. **Existing-Connections Career Outreach Extension**: Scrapes, filters, and messages existing 1st-degree connections for international internships, remote roles, and relocation opportunities—filtered by priority regions, personalized by role archetypes, and governed by automated 4–5 day follow-up logic.

The system reuses a single, stealth, authenticated Google Chrome profile (`chrome_profile/`) via Playwright, ensuring LinkedIn sees an authentic human session rather than API scraping.

---

## 2. User Personas & Target Audience

| Persona | Role & Objectives | Key Workflows & Features |
|---|---|---|
| **Shaurya — AI Engineer** | AI Product Developer seeking international internships, relocation opportunities, or high-impact remote engineering roles. | Existing-Connections Extension: filters foreign 1st-degree connections (UK, Europe, US, Singapore, Dubai), generates role-specific no-pitch openers, and tracks follow-ups. |
| **Founder / CTO** | Startup leader conducting customer discovery and technical partnership outreach. | Cold Outreach Pipeline: automated 3-step sequence, atomic CSV tracking, and 20/day safety caps. |
| **Growth Strategist** | Content creator building organic reach and engaging target audiences. | Cloud MCP feed publishing (`LINKEDIN_CREATE_LINKED_IN_POST`), thought leadership distribution, and profile health auditing. |

---

## 3. Core Value Propositions & Key Differentiators

1. **100% Free & Self-Hosted**: Zero subscription fees. Runs directly on the host machine using standard Python and Playwright.
2. **Single Stealth Session Persistence**: Operates through your authenticated Chrome user profile (`chrome_profile/`). Session cookies, 2FA tokens, and localStorage remain intact across runs, eliminating login prompts.
3. **Custom Model Context Protocol (MCP) Server**: Exposes local browser actions (`LINKEDIN_GET_CONNECTIONS`, `LINKEDIN_SEND_CONNECTION_MESSAGE`) alongside cloud API tools over standard MCP stdio, allowing any MCP-compliant client or agent to drive LinkedIn directly.
4. **Strict No-Pitch `li-dm` Philosophy**:
   - Invite notes capped strictly below 200 characters with visible character counts.
   - First messages are short (2–4 sentences), conversational, and offer value or ask genuine questions before making any request.
   - No immediate pitch, no unsolicited CV attachments, and no booking calendar links in the opener.
5. **Human Emulation & Anti-Detection Safety**:
   - Keystroke jitter (40ms – 110ms randomized delay per character).
   - Natural inter-action cooldowns (15s – 25s between profile visits).
   - Strict shared daily cap of 20 actions/day to preserve account health.
   - Immediate detection of LinkedIn weekly limit warnings or captcha checkpoints with non-destructive pause.

---

## 4. Functional Requirements: Cold Outreach Pipeline

### 4.1 Lead Management & CRM Persistence (FR-1)
- **FR-1.1**: Leads are stored in `~/outreach/contacts.csv` (fallback: `./data/contacts.csv`).
- **FR-1.2**: Schema:
  `First Name, Last Name, Full Name, Title, Company, Location, LinkedIn URL, LinkedIn Status, Invited Date, Connected Date, Notes`
- **FR-1.3**: Automatic timestamped backup (`./data/backups/contacts_YYYYMMDD_HHMMSS.bak`) before every write mutation.

### 4.2 Cold Sequence State Machine (FR-2)
```
(Blank) ──[Step 1: Invite Note]──────► INVITED
                                           │
              [3+ Days & Connected?]───────┤
                                           ▼
                                       MSG1_SENT (Step 2: Intro DM)
                                           │
              [5+ Days & No Reply?]────────┤
                                           ▼
                                       MSG2_SENT (Step 3: Follow-up)
                                           │
             [Recipient Replies at Any Point]
                                           ▼
                                       REPLIED (Sequence Halts)
```
- **FR-2.1 (Step 1 - New Invites)**: Find rows with blank `LinkedIn Status`. Navigate to profile, click *Connect*, attach personalized note (<200 chars), mark `INVITED`, record date. Limit: 20/day.
- **FR-2.2 (Step 2 - Acceptance Check & Intro DM)**: For `INVITED` leads where `today - Invited Date >= 3 days`: Navigate to profile. If connected and no prior message, type and send Intro DM. Mark `MSG1_SENT`.
- **FR-2.3 (Step 3 - Follow-up DM)**: For `MSG1_SENT` leads where `today - Connected Date >= 5 days`: Inspect thread. If no reply, dispatch follow-up. Mark `MSG2_SENT`.
- **FR-2.4 (Safety Reply Halt)**: If prospect has replied, set status to `REPLIED` and immediately stop automated messaging for that contact.

---

## 5. Functional Requirements: Existing-Connections Outreach Extension

### 5.1 Purpose & Scope (FR-3.1)
Target existing 1st-degree LinkedIn connections for career discovery, internships, remote engineering roles, or international relocation opportunities. This extension bypasses cold invites entirely and operates on established connections.

### 5.2 Retrieval: `LINKEDIN_GET_CONNECTIONS` (FR-3.2)
- **FR-3.2.1**: Playwright navigates to `https://www.linkedin.com/mynetwork/invite-connect/connections/`.
- **FR-3.2.2**: Scrapes connection cards: `Full Name`, `Title`, `Company`, `Headline`, `Location`, and `Profile URL`.
- **FR-3.2.3**: Writes extracted records to `~/outreach/connections.csv` (or `./data/connections.csv`), preserving existing status if the lead was previously recorded.
- **FR-3.2.4 (Sync Strategy)**:
  - *Full Initial Backfill*: On first execution, scrolls through the connections list to index established network contacts.
  - *Incremental Delta Sync*: On subsequent executions, parses only connections added since the last recorded sync date.

### 5.3 Location & Regional Filtering (FR-3.3)
- **FR-3.3.1 (Explicit Exclusion)**: Any connection whose resolved location is **India** is excluded from this job outreach workflow (domestic on-site is out of scope).
- **FR-3.3.2 (Priority Inclusions)**:
  1. **Tier 1 (Top Priority)**: Europe (United Kingdom, Ireland priority; Germany, Netherlands, France, Switzerland, Nordics).
  2. **Tier 2**: United States & Canada.
  3. **Tier 3**: Singapore.
  4. **Tier 4**: Middle East (Dubai / UAE specifically, Saudi Arabia, Qatar).
- **FR-3.3.3 (Backlog Preservation)**: Connections outside the target regions are preserved in the CRM with status `QUEUED_LATER` or `REGION_EXCLUDED`, ensuring no data loss while keeping the active outreach queue clean.

### 5.4 Role-Archetype & Deep Company Domain Personalization (FR-3.4)
- **FR-3.4.1 (Archetype Detection)**: Categorizes each contact into one of four role archetypes based on Title and Headline:
  - **Engineering Leadership**: VP of Eng, CTO, Head of AI, Engineering Manager. Angle: High-level technical perspective on agent reliability, architectures, and engineering internships/roles.
  - **Senior Technical IC**: Staff / Principal AI Engineer, Tech Lead, Senior Developer. Angle: Peer-to-peer technical exchange on production LLM/agent challenges and team openings.
  - **Product & Innovation**: VP of Product, Head of AI Product, Product Lead. Angle: Applied AI product workflows, product engineering, and collaborative roles.
  - **Talent & Recruitment**: Technical Recruiter, Head of Talent, People Partner. Angle: Direct inquiry regarding current or upcoming AI engineering openings and remote/relocation policies.
- **FR-3.4.2 (Deep Company Domain Intelligence Engine)**: Driven by `company_researcher.py` and NVIDIA Nemotron 3 Super (`nvidia/nemotron-3-super-120b-a12b`), automatically analyzes what the target organization actually builds before any outreach is drafted:
  - **Healthcare / Medical**: Identifies focus on clinical trial workflows, patient intelligence, or biomedical models; tailors Shaurya's angle to clinical document reasoning and HIPAA-compliant agent pipelines.
  - **Transportation / Mobility**: Identifies fleet dispatch, transit networks, or logistics platforms; tailors Shaurya's angle to dynamic routing optimization and autonomous dispatch intelligence.
  - **Cloud Infrastructure / DevOps**: Identifies observability, distributed systems, or developer tooling; tailors Shaurya's angle to telemetry agents and low-latency LLM orchestration.
  - **Fintech / Banking**: Identifies transaction fraud, payment networks, or regulatory reporting; tailors Shaurya's angle to audit automation and financial document reasoning.
  - **Persistent Local Caching**: Extracted profiles are cached locally in `./data/company_cache.json` to eliminate redundant lookups and accelerate execution.
- **FR-3.4.3 (Generation Standards)**: Reuses `ai_generator.py` with `nvidia/nemotron-3-super-120b-a12b` (1024 token reasoning buffer). Enforces strict `li-dm` rules:
  - Max 2 to 3 sentences. Conversational, peer-to-peer, respectful.
  - Zero em dashes (never use '—'), zero corporate slop words (*leverage*, *synergy*, *game-changer*).
  - Genuine, personalized opener connecting Shaurya's applied AI agent background to their specific domain without dropping a CV or pitching aggressively.

### 5.5 Multimodal Visual Browser Control via NVIDIA Nemotron 3.5 Super VL (FR-3.5)
- **FR-3.5.1 (Vision Model Tier)**: Employs `nvidia/nemotron-3.5-super-vl-120b-a12b` via NVIDIA NIM endpoint for visual GUI understanding.
- **FR-3.5.2 (Multimodal State Inspection - `visual_browser_inspect`)**: Analyzes live browser page state directly to visually detect unexpected modals, invitation weekly limits, 2FA checkpoints, or chat overlay visibility when DOM selectors fail.
- **FR-3.5.3 (Coordinate-Based Element Clicking - `visual_locate_element`)**: When LinkedIn's obfuscated or shadow DOM breaks standard CSS locators, Nemotron 3.5 Super VL visually identifies the exact center pixel coordinates `(x, y)` of the target UI element (e.g., *Message*, *Send*, *Dismiss*), enabling genuine human mouse clicks.

### 5.6 Ephemeral Screenshot Architecture & Storage Hygiene (FR-3.6)
- **FR-3.6.1 (In-Memory Processing)**: Playwright captures screenshots directly into RAM as PNG byte buffers (`page.screenshot(type="png")`) and encodes them directly to base64. Zero bytes are written to physical disk during standard visual analysis.
- **FR-3.6.2 (Guaranteed Post-Message Deletion)**: Immediately following every direct message attempt or visual inspection, the engine triggers `cleanup_screenshots()` in a strict `finally` block, unlinking any debug or temporary image files (*.png, *.jpg).
- **FR-3.6.3 (Zero Storage Pileup Guarantee)**: Disk storage never accumulates image artifacts across days or weeks of autonomous operation, maintaining drive health on space-constrained systems.

### 5.7 Message Dispatch: `LINKEDIN_SEND_CONNECTION_MESSAGE` (FR-3.7)
- **FR-3.7.1**: Navigates to the connection's profile URL.
- **FR-3.7.2**: Verifies 1st-degree connection status and clicks *Message* (falling back to visual coordinate clicking if needed).
- **FR-3.7.3**: Inspects existing chat history to ensure no active conversation is overridden.
- **FR-3.7.4**: Simulates human keystroke cadence, sends message, cleans up all screenshots, and transitions status to `MSG_SENT` with current timestamp.

### 5.8 Follow-Up Engine & State Machine (FR-3.8)
```
(Retrieved & Filtered) ──► MSG_SENT (Personalized First Opener)
                                │
          [4–5 Days & No Reply?]────────┤
                                        ▼
                                    FOLLOWUP_SENT (Single Value-Add Follow-Up)
                                        │
         [Recipient Replies at Any Point]
                                        ▼
                                    REPLIED (Sequence Halts Permanently)
```
- **FR-3.8.1 (4–5 Day Delay)**: Follow-up message is eligible only after 4 to 5 elapsed days with zero recipient response.
- **FR-3.8.2 (Thread Inspection)**: The engine reads the message thread DOM. If the contact has replied with even a single word, automated follow-up is immediately aborted and marked `REPLIED`.
- **FR-3.8.3 (Single Follow-Up Rule)**: Exactly one follow-up message is permitted. If no reply is received after `FOLLOWUP_SENT`, no further messages are sent.
- **FR-3.8.4 (Immediate Hygiene)**: Post-message screenshot deletion executes after each follow-up dispatch.

---

## 6. Custom MCP Server Specification

### 6.1 Architecture & Transport
- **Protocol**: Model Context Protocol (MCP) specification 2024-11-05.
- **Transport**: Standard I/O (stdio) JSON-RPC 2.0.
- **Entrypoint**: `python -m linkedin_outreach.mcp_server`
- **Compatibility**: Integrates seamlessly with any MCP client (Claude Desktop, Antigravity, Cursor, or standalone agentic frameworks).

### 6.2 Exposed Tool Definitions

| Tool Name | Parameters | Description |
|---|---|---|
| `LINKEDIN_GET_CONNECTIONS` | `limit` (int, default 50), `sync_mode` ("incremental" \| "full") | Scrapes 1st-degree connections from LinkedIn, resolves location and headline, and updates `connections.csv`. |
| `LINKEDIN_FILTER_CONNECTIONS` | `target_regions` (array), `exclude_regions` (array) | Filters stored connections based on regional priority criteria. |
| `LINKEDIN_GENERATE_CONNECTION_MSG` | `profile_url` (str), `archetype_override` (str) | Uses NVIDIA NIM Nemotron to draft a role-personalized, no-pitch opener for a connection. |
| `LINKEDIN_SEND_CONNECTION_MESSAGE` | `profile_url` (str), `message` (str), `dry_run` (bool) | Navigates to the connection's profile via Playwright and sends the message with human typing cadence. |
| `LINKEDIN_RUN_CONNECTIONS_OUTREACH`| `max_messages` (int, default 15), `dry_run` (bool) | Executes the full sequence: checks follow-ups (4-5d), inspects replies, and sends new openers up to daily cap. |
| `LINKEDIN_GET_PIPELINE_STATUS` | `pipeline` ("cold" \| "connections" \| "all") | Returns real-time queue counts across all stages. |

---

## 7. Operational Schedules & Anti-Detection Safety

### 7.1 Daily Safety Caps
- **Invites Ceiling**: Hard maximum of 20 connection requests per day (Cold pipeline).
- **Direct Messages Ceiling**: Shared hard maximum of 20 DMs per day across both pipelines combined (Cold intros + Cold follow-ups + Connection openers + Connection follow-ups).
- **Weekly Ceiling**: Maximum of 80 invites per rolling 7-day period to prevent LinkedIn algorithmic limits.

### 7.2 Scheduling Options
1. **Windows Task Scheduler**: Pre-configured task `LinkedInOutreachDaily` triggering `run_outreach.bat` at 9:00 AM every morning.
2. **Cron (macOS / Linux)**: Standard entry `0 9 * * * /path/to/run_outreach.bat`.
3. **Background Daemon**: `python -m linkedin_outreach.scheduler --time 09:00`.

---

## 8. Web Control Center & REST API

- **Port**: `http://127.0.0.1:8500`
- **Features**:
  - Combined metric counters for both Cold Leads and 1st-Degree Connections.
  - Interactive pipeline flowcharts with live stage counts.
  - Lead and Connection table managers with inline search, regional filtering, and export.
  - Template and prompt editor with live character counting.
  - Real-time Server-Sent Events (SSE) streaming console logs.

---

## 9. Non-Functional Requirements (NFR)

- **NFR-1 (Local Security)**: Session cookies and credentials remain 100% local inside `chrome_profile/`. No session data is transmitted externally.
- **NFR-2 (Self-Contained Runtime)**: Relies on standalone CPython (`runtime/`) with native binaries, avoiding permission errors on Windows.
- **NFR-3 (Atomic Storage)**: Every CSV write operation produces a `.bak` snapshot in `data/backups/`.
- **NFR-4 (Timeout Bounds)**: DOM selectors and page navigations enforce 10-second bounded timeouts with exponential backoff.

---

## 10. Phased Roadmap

- **Phase 1 (Complete)**: Cold invite Playwright pipeline, atomic CSV manager, CLI tools, Windows scheduler.
- **Phase 2 (Complete)**: FastAPI Web Control Center with SSE streaming and interactive diagram.
- **Phase 3 (Current)**: Custom Stdio MCP Server (`mcp_server.py`) exposing `LINKEDIN_GET_CONNECTIONS` and `LINKEDIN_SEND_CONNECTION_MESSAGE`.
- **Phase 4 (Current)**: Regional filtering engine (India exclusion; UK, EU, US, SG, Dubai priority) and role archetype generator.
- **Phase 5 (Next)**: Automated Sales Navigator lead import and inbound message classification.
