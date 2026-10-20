---
name: linkedin-outreach
description: >-
  Automated browser-based LinkedIn outreach engine. Run daily connection invites,
  intro messages, follow-up messages, lead pipeline status tracking, CSV management,
  message template customization, and Web Control Center. Use whenever the user
  asks to run outreach, check leads, send invites, check pipeline status, launch
  the outreach dashboard, or test LinkedIn automation.
---

# linkedin-outreach

Full automated pipeline and control center for browser-based LinkedIn connection requests, intro messages, follow-ups, and lead status tracking.

## Python Interpreter & Execution Environment
A dedicated standalone Python environment is pre-configured and always available at:
```text
C:\New folder (2)\linkedin_outreach\.venv\Scripts\python.exe
```
When running outreach commands from PowerShell or cmd:
- **Option 1 (Recommended Batch File)**:
  ```powershell
  cd "C:\New folder (2)\linkedin_outreach"; .\run_outreach.bat
  ```
- **Option 2 (Direct Python)**:
  ```powershell
  cd "C:\New folder (2)"; & "C:\New folder (2)\linkedin_outreach\.venv\Scripts\python.exe" -m linkedin_outreach.cli status
  cd "C:\New folder (2)"; & "C:\New folder (2)\linkedin_outreach\.venv\Scripts\python.exe" -m linkedin_outreach.cli run --invites 15 --messages 15
  ```
- **Option 3 (Running li-human scripts)**:
  ```powershell
  & "C:\New folder (2)\linkedin_outreach\.venv\Scripts\python.exe" "C:\New folder (2)\linkedin-agent-skill\skills\li-human\humanize.py" "text to humanize"
  ```

## Core Capabilities & Commands

### 1. Check Pipeline Status
Displays real-time lead counts across all pipeline stages:
```bash
& "C:\New folder (2)\linkedin_outreach\.venv\Scripts\python.exe" -m linkedin_outreach.cli status
```

### 2. Run Daily Outreach Run
Executes the automated sequence for today:
```bash
# Standard daily batch (default 20 invites + 20 messages):
cd "C:\New folder (2)\linkedin_outreach"; .\run_outreach.bat

# Or with custom limits:
& "C:\New folder (2)\linkedin_outreach\.venv\Scripts\python.exe" -m linkedin_outreach.cli run --invites 15 --messages 15

# Dry-run (simulates actions without clicking or sending):
& "C:\New folder (2)\linkedin_outreach\.venv\Scripts\python.exe" -m linkedin_outreach.cli run --dry-run
```

### 3. Quick 3-Contact Test Run
Verifies Chrome session, selectors, and CSV updates on 3 contacts:
```bash
& "C:\New folder (2)\linkedin_outreach\.venv\Scripts\python.exe" -m linkedin_outreach.cli test
& "C:\New folder (2)\linkedin_outreach\.venv\Scripts\python.exe" -m linkedin_outreach.cli test --dry-run
```

### 4. Launch Web Control Center
Starts the FastAPI + modern web dashboard on port 8500:
```bash
& "C:\New folder (2)\linkedin_outreach\.venv\Scripts\python.exe" -m linkedin_outreach.cli serve --port 8500
```
Open **http://127.0.0.1:8500** to view live metrics, edit templates, inspect the lead table, and trigger runs.

### 5. Interactive LinkedIn Login / Session Connect
Launches Chrome headed for one-time login or cookie refresh:
```bash
& "C:\New folder (2)\linkedin_outreach\.venv\Scripts\python.exe" -m linkedin_outreach.cli login
```
Session cookies are permanently stored in `C:\New folder (2)\linkedin_outreach\chrome_profile\`.

---

## 3-Step Outreach Logic & State Machine

```
Read CSV (contacts.csv)
       │
       ├─► STEP 1: BLANK rows ───────► Send Invite ────► INVITED (Limit: 20/day)
       │
       ├─► STEP 2: INVITED (3d+) ────► Send Intro ─────► MSG1_SENT (Limit: 20/day shared)
       │
       ├─► STEP 3: MSG1_SENT (5d+) ──► Send Follow-up ─► MSG2_SENT
       │
       └─► ANY STEP: Reply Detected ──────────────────► REPLIED (Sequence halts)
```

| Status | Meaning & Automated Action |
|---|---|
| `(blank)` | New lead. Will receive connection request with intro note in Step 1. |
| `INVITED` | Invite pending. Checked after 3+ days. If accepted, sends Intro message -> transitions to `MSG1_SENT`. |
| `MSG1_SENT` | Intro sent. Checked after 5+ days. Sends follow-up message -> transitions to `MSG2_SENT`. |
| `MSG2_SENT` | Follow-up sent. Sequence completed, waiting for lead reply. |
| `REPLIED` | Prospect replied! Sequence stops immediately for this lead. |

---

## Data & File Locations

- **Leads Database**: `C:\New folder (2)\linkedin_outreach\data\contacts.csv` (and `~/outreach/contacts.csv`)
- **Intro Template**: `C:\New folder (2)\linkedin_outreach\templates\intro.txt`
- **Follow-up Template**: `C:\New folder (2)\linkedin_outreach\templates\followup.txt`
- **Browser Profile**: `C:\New folder (2)\linkedin_outreach\chrome_profile\`
- **OpenClaw Dedicated Browser**: Run `C:\New folder (2)\linkedin_outreach\start_openclaw_browser.bat` (Port 18800)
- **Composio Authenticated Profile**: Shaurya Sharma (`theshauryash@gmail.com`)
