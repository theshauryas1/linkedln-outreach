"""
Outreach Memory & Idempotency Module:
Guarantees that once a connection has been sent a message or an existing conversation is detected,
they are permanently remembered and NEVER messaged again, even if a run is cut abruptly,
crashes, or is interrupted mid-execution.
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd

from .config import LOCAL_DATA_DIR

logger = logging.getLogger("outreach.memory")

MEMORY_FILE_PATH = LOCAL_DATA_DIR / "sent_memory.json"

def normalize_linkedin_url(url: str) -> str:
    """Canonicalizes LinkedIn URLs for exact deduping."""
    if not url:
        return ""
    clean = url.strip().lower()
    clean = clean.split("?")[0].split("#")[0].rstrip("/")
    if clean.startswith("http://"):
        clean = "https://" + clean[7:]
    elif not clean.startswith("https://"):
        clean = "https://" + clean
    clean = clean.replace("https://www.linkedin.com", "https://linkedin.com")
    return clean

class OutreachMemory:
    """
    Persistent memory tracking all contacts who have been sent outreach messages
    or who already have active conversation threads.
    """

    def __init__(self, memory_file: Optional[Path] = None):
        self.file_path = memory_file or MEMORY_FILE_PATH
        self.data: Dict[str, Any] = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "sent_urls": {},
            "history": [],
        }
        self.load()

    def load(self):
        """Loads memory from disk, creating it if missing."""
        if not self.file_path.exists():
            self.save()
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, dict):
                    self.data["version"] = content.get("version", "1.0")
                    self.data["sent_urls"] = content.get("sent_urls", {})
                    self.data["history"] = content.get("history", [])
        except Exception as e:
            logger.warning(f"Error loading outreach memory file: {e}. Preserving in-memory state.")

    def save(self):
        """Atomically saves memory to disk to prevent corruption on abrupt cutoffs."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.data["last_updated"] = datetime.now().isoformat()
            temp_file = self.file_path.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            shutil.move(str(temp_file), str(self.file_path))
        except Exception as e:
            logger.error(f"Failed to persist outreach memory to disk: {e}")

    def is_already_contacted(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Returns (True, status) if this URL has already been messaged or has an active thread.
        Otherwise returns (False, None).
        """
        canonical = normalize_linkedin_url(url)
        if not canonical:
            return False, None
        
        record = self.data["sent_urls"].get(canonical)
        if record:
            status = record.get("status", "MSG_SENT")
            return True, status
        return False, None

    def record_sent(
        self,
        url: str,
        name: str,
        message_type: str,
        message_text: str,
        status: str = "MSG_SENT",
        source: str = "live_send",
    ):
        """
        Immediately writes a sent message event to memory and flushes atomically to disk.
        """
        canonical = normalize_linkedin_url(url)
        if not canonical:
            return

        now_iso = datetime.now().isoformat()
        snippet = message_text[:120].strip() if message_text else ""

        record = {
            "canonical_url": canonical,
            "raw_url": url,
            "name": name,
            "status": status,
            "message_type": message_type,
            "snippet": snippet,
            "timestamp": now_iso,
            "source": source,
        }

        self.data["sent_urls"][canonical] = record
        self.data["history"].append({
            "action": f"{message_type.upper()}_SENT",
            "url": canonical,
            "name": name,
            "timestamp": now_iso,
            "status": status,
        })
        self.save()
        logger.info(f"[OUTREACH MEMORY] Recorded {status} for {name} ({canonical})")

    def record_thread_detected(
        self,
        url: str,
        name: str,
        reason: str,
        status: str = "MSG_SENT",
    ):
        """
        Records that an active conversation was found on LinkedIn (e.g. sent prior or manually).
        Guarantees that subsequent runs will immediately skip this prospect.
        """
        canonical = normalize_linkedin_url(url)
        if not canonical:
            return

        now_iso = datetime.now().isoformat()
        record = {
            "canonical_url": canonical,
            "raw_url": url,
            "name": name,
            "status": status,
            "message_type": "existing_thread",
            "snippet": reason,
            "timestamp": now_iso,
            "source": "live_thread_dom",
        }
        self.data["sent_urls"][canonical] = record
        self.data["history"].append({
            "action": "THREAD_DETECTED_HALT",
            "url": canonical,
            "name": name,
            "timestamp": now_iso,
            "status": status,
            "reason": reason,
        })
        self.save()
        logger.info(f"[OUTREACH MEMORY] Thread detected on LinkedIn for {name}. Marked {status} and saved.")

    def sync_from_csv(self, csv_path: Path):
        """
        Ensures all connections marked as MSG_SENT, FOLLOWUP_SENT, or REPLIED in the CSV
        are registered in memory.
        """
        if not csv_path.exists():
            return

        try:
            df = pd.read_csv(csv_path, dtype=str).fillna("")
            updated = False
            for _, row in df.iterrows():
                status = str(row.get("Status", "")).strip().upper()
                url = str(row.get("LinkedIn URL", "")).strip()
                name = str(row.get("Full Name", "")).strip()
                sent_date = str(row.get("Sent Date", "")).strip()

                if status in ["MSG_SENT", "FOLLOWUP_SENT", "REPLIED"] and url:
                    canonical = normalize_linkedin_url(url)
                    if canonical not in self.data["sent_urls"]:
                        self.data["sent_urls"][canonical] = {
                            "canonical_url": canonical,
                            "raw_url": url,
                            "name": name,
                            "status": status,
                            "message_type": "csv_synced",
                            "snippet": f"Synced from CSV (Sent Date: {sent_date})",
                            "timestamp": datetime.now().isoformat(),
                            "source": "csv_sync",
                        }
                        updated = True
            if updated:
                self.save()
                logger.info(f"[OUTREACH MEMORY] Synced active statuses from CSV ({len(self.data['sent_urls'])} total records).")
        except Exception as e:
            logger.warning(f"Failed to sync memory from CSV: {e}")

outreach_memory = OutreachMemory()
