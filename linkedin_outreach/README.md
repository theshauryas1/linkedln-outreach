# Automated LinkedIn Outreach Agent (Free & Browser-Based)

A free, 100% open automation system for LinkedIn outreach, built to replace costly SaaS tools ($100–$300/mo) using real Chrome browser automation, a spreadsheet/CSV CRM, and scheduled daily runs.

---

## 🏗 System Architecture & Rules

```
CRON (9:00 AM Daily)
       │
       ▼
Read CSV (contacts.csv)
       │
       ├─► STEP 1: BLANK rows ───────► Send Invite ────► INVITED (Limit: 20/day)
       │
       ├─► STEP 2: INVITED (3d+) ────► Send Intro ─────► MSG1_SENT (Limit: 20/day shared)
       │
       └─► STEP 3: MSG1_SENT (5d+) ──► Send Follow-up ─► MSG2_SENT
       │
       └─► ANY STEP: Reply Detected ──────────────────► REPLIED (Sequence halts)
       │
       ▼
Write CSV (Atomic state persistence)
```

### Required Columns in `contacts.csv`
```csv
First Name,Last Name,Full Name,Title,Company,Location,LinkedIn URL,LinkedIn Status,Invited Date,Connected Date,Notes
```

| Status | Meaning & Next Action |
|---|---|
| `(blank)` | Not yet contacted — will receive invite on next run (Step 1) |
| `INVITED` | Invite sent — waiting for acceptance (checked after 3+ days in Step 2) |
| `MSG1_SENT` | Intro message sent after acceptance — waiting 5+ days for follow-up (Step 3) |
| `MSG2_SENT` | Follow-up message sent |
| `REPLIED` | Prospect replied — sequence halts immediately so you take over by hand |

---

## 🚀 Quick Start Guide

### 1. Launch the Web Control Center (Recommended)
Open a terminal in the project directory and run:
```bash
python -m linkedin_outreach.cli serve --port 8500
```
Open **[http://127.0.0.1:8500](http://127.0.0.1:8500)** in your browser. You will see:
- Real-time pipeline metrics (Total, Blank, Invited, MSG1, MSG2, Replied).
- Interactive architecture flowchart with live counts.
- Lead manager (view, filter, search, add, delete).
- Message template editor with live preview and character counter.
- Live streaming activity console.

---

### 2. Connect Your LinkedIn Session (One-Time Setup)
You only do this once. Your session cookies and storage will be saved permanently in `chrome_profile/`.

Via Web Dashboard: Click **"Connect LinkedIn"** at the top right.  
Via Terminal:
```bash
python -m linkedin_outreach.cli login
```
A Google Chrome window opens. Sign in to your LinkedIn account. Once you reach your LinkedIn feed, the assistant verifies your session and saves it.

---

### 3. Test With 3 Contacts Live (Step 6)
Before letting it run automatically, verify everything works with 3 contacts:
```bash
# Dry run test (simulates without sending)
python -m linkedin_outreach.cli test --dry-run

# Live test (sends 3 real connection requests)
python -m linkedin_outreach.cli test
```

---

### 4. Run the Daily Batch Manually
```bash
# Full daily run (20 invites + 20 messages limit)
python -m linkedin_outreach.cli run

# Or with custom limits:
python -m linkedin_outreach.cli run --invites 15 --messages 15
```

---

### 5. Automated 9:00 AM Daily Run

#### On Windows (Windows Task Scheduler):
Run PowerShell as Administrator:
```powershell
powershell -ExecutionPolicy Bypass -File .\schedule_windows.ps1
```
This registers a scheduled task `LinkedInOutreachDaily` that triggers every morning at 9:00 AM via `run_outreach.bat`.

#### On Mac / Linux (Cron):
Add this line to your crontab (`crontab -e`):
```cron
0 9 * * * /path/to/linkedin_outreach/run_outreach.sh
```

#### Standalone Background Daemon:
```bash
python -m linkedin_outreach.scheduler --time 09:00
```

---

## ✍ Message Sequence Templates & Humanizer

The system includes pre-configured, de-slopped templates evaluated by the `li-human` 5-check detection panel:

### Preset 1: Creative & Design Research
**Intro (Step 2 - Sent after connection accepted):**
> Hi {First Name}, nice to meet you. I'm doing some research in the creative sector and looking for professionals like you to give me a bit of feedback. It's very quick, just a few questions every now and then, either a short form or a 10-minute call. Let me know. Thanks in advance.

**Follow-up (Step 3 - Sent 5 days later):**
> Hi {First Name}, just checking in case my last message got lost - no worries if now isn't a good time. Still looking for a few creative professionals to share some quick thoughts on my research. Totally informal, no pressure. Would you be open to it? Thanks again.

### Preset 2: AI Engineering & Multi-Agent Systems (Shaurya Sharma)
**Intro (Step 2):**
> Hi {First Name}, nice to connect with you. I'm an AI engineer building agentic systems and multi-agent workflows, and I've been following {Company}'s engineering work. I'm currently gathering perspectives from engineering leaders on multi-agent reliability and retrieval challenges in production. Would you be open to sharing a quick thought or a brief 10-minute chat? Thanks in advance.

**Follow-up (Step 3):**
> Hi {First Name}, just checking back in case my note was buried. No worries at all if you're slammed right now. Still curious to hear your take on agentic engineering challenges at {Company} whenever you have a moment. Totally informal and low-pressure. Thanks again.

---

## 🛡 Anti-Detection & Safety Guardrails
- **Daily Quotas**: Strict limit of 20 invites and 20 messages per day.
- **Human Typing**: Simulates keystroke delays (40ms–110ms with variance).
- **Randomized Delays**: 15–25 seconds between profile visits.
- **Stealth Flags**: `--disable-blink-features=AutomationControlled` prevents bot detection.
- **Limit Detection**: Automatically detects LinkedIn weekly limit warnings or checkpoints and gracefully pauses.
