import asyncio
import json
import logging
import queue
import threading
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import config, ensure_directories
from .csv_manager import CSVManager
from .templates_engine import template_engine
from .pipeline import OutreachPipeline
from .browser_engine import BrowserEngine

ensure_directories()

app = FastAPI(title="LinkedIn Outreach Agent Control Center")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# In-memory log stream queue
log_queue = queue.Queue(maxsize=1000)
pipeline_running = False
current_pipeline_thread = None

class QueueHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            log_queue.put_nowait({"time": record.asctime if hasattr(record, "asctime") else "", "msg": msg, "level": record.levelname})
        except Exception:
            pass

logger = logging.getLogger("outreach")
logger.setLevel(logging.INFO)
q_handler = QueueHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
q_handler.setFormatter(formatter)
logger.addHandler(q_handler)

def emit_log(msg: str, level: str = "INFO"):
    logger.info(msg)
    try:
        log_queue.put_nowait({"time": "", "msg": msg, "level": level})
    except Exception:
        pass

class RunRequest(BaseModel):
    invites: int = 20
    messages: int = 20
    dry_run: bool = False

class TemplatesUpdate(BaseModel):
    intro: str
    followup: str

class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    title: str = ""
    company: str = ""
    location: str = ""
    linkedin_url: str
    notes: str = ""

@app.get("/", response_class=HTMLResponse)
def index():
    html_file = STATIC_DIR / "index.html"
    return html_file.read_text(encoding="utf-8")

@app.get("/api/status")
def get_status():
    from .composio_linkedin import composio_linkedin
    csv_mgr = CSVManager()
    stats = csv_mgr.get_stats()
    return {
        "stats": stats,
        "is_running": pipeline_running,
        "csv_path": str(csv_mgr.filepath),
        "composio_profile": composio_linkedin.get_profile(),
    }

@app.get("/api/composio/profile")
def get_composio_profile():
    from .composio_linkedin import composio_linkedin
    return composio_linkedin.get_profile()

@app.get("/api/contacts")
def get_contacts():
    csv_mgr = CSVManager()
    df = csv_mgr.read()
    contacts = []
    for idx, row in df.iterrows():
        d = row.to_dict()
        d["id"] = int(idx)
        contacts.append(d)
    return contacts

@app.post("/api/contacts")
def add_contact(payload: ContactCreate):
    csv_mgr = CSVManager()
    full_name = f"{payload.first_name} {payload.last_name}".strip()
    contact_dict = {
        "First Name": payload.first_name,
        "Last Name": payload.last_name,
        "Full Name": full_name,
        "Title": payload.title,
        "Company": payload.company,
        "Location": payload.location,
        "LinkedIn URL": payload.linkedin_url,
        "LinkedIn Status": "",
        "Invited Date": "",
        "Connected Date": "",
        "Notes": payload.notes,
    }
    csv_mgr.add_contact(contact_dict)
    emit_log(f"Added lead: {full_name} ({payload.linkedin_url})")
    return {"success": True, "message": "Lead added successfully"}

@app.delete("/api/contacts/{contact_id}")
def delete_contact(contact_id: int):
    csv_mgr = CSVManager()
    df = csv_mgr.read()
    if contact_id not in df.index:
        raise HTTPException(status_code=404, detail="Lead not found")
    name = df.at[contact_id, "Full Name"]
    df = df.drop(index=contact_id).reset_index(drop=True)
    csv_mgr._save(df)
    emit_log(f"Deleted lead #{contact_id}: {name}")
    return {"success": True}

@app.get("/api/templates")
def get_templates():
    intro = template_engine.load_template(config.intro_template)
    followup = template_engine.load_template(config.followup_template)
    return {"intro": intro, "followup": followup}

@app.post("/api/templates")
def save_templates(payload: TemplatesUpdate):
    config.intro_template.write_text(payload.intro, encoding="utf-8")
    config.followup_template.write_text(payload.followup, encoding="utf-8")
    emit_log("Updated outreach message templates successfully.")
    return {"success": True}

def _run_pipeline_worker(invites: int, messages: int, dry_run: bool):
    global pipeline_running
    pipeline_running = True
    try:
        pipeline = OutreachPipeline()
        pipeline.run(
            invite_limit=invites,
            message_limit=messages,
            dry_run=dry_run,
            progress_callback=lambda m: emit_log(m),
        )
    except Exception as e:
        emit_log(f"Pipeline error: {e}", level="ERROR")
    finally:
        pipeline_running = False

@app.post("/api/pipeline/run")
def trigger_pipeline(payload: RunRequest, background_tasks: BackgroundTasks):
    global pipeline_running
    if pipeline_running:
        raise HTTPException(status_code=400, detail="Pipeline is already running.")

    threading.Thread(
        target=_run_pipeline_worker,
        args=(payload.invites, payload.messages, payload.dry_run),
        daemon=True,
    ).start()

    emit_log(f"Triggered outreach run (Invites: {payload.invites}, Messages: {payload.messages}, Dry Run: {payload.dry_run})")
    return {"success": True, "message": "Outreach pipeline started"}

def _run_login_worker():
    global pipeline_running
    pipeline_running = True
    try:
        emit_log("Opening Chrome for LinkedIn authentication...")
        engine = BrowserEngine(headless=False)
        engine.start()
        success = engine.interactive_login()
        if success:
            emit_log("LinkedIn authentication confirmed and session saved!", level="SUCCESS")
        else:
            emit_log("LinkedIn login incomplete or timed out.", level="WARNING")
        engine.close()
    except Exception as e:
        emit_log(f"Login assistant error: {e}", level="ERROR")
    finally:
        pipeline_running = False

@app.post("/api/browser/login")
def trigger_login():
    global pipeline_running
    if pipeline_running:
        raise HTTPException(status_code=400, detail="A browser session is already active.")

    threading.Thread(target=_run_login_worker, daemon=True).start()
    return {"success": True, "message": "Login assistant launched in Chrome"}

@app.get("/api/logs/stream")
async def stream_logs():
    async def event_generator():
        while True:
            try:
                # Non-blocking get
                log_item = log_queue.get_nowait()
                data = json.dumps(log_item)
                yield f"data: {data}\n\n"
            except queue.Empty:
                await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
