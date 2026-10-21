"""
Connections Outreach Pipeline:
Handles 1st-degree connection retrieval, regional filtering, role-archetype messaging,
and 4-5 day follow-up lifecycle.
"""

import os
import shutil
import logging
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable

from .config import config, USER_OUTREACH_DIR, LOCAL_DATA_DIR
from .browser_engine import BrowserEngine
from .region_filter import classify_location
from .ai_generator import nim_generator
from .company_researcher import company_researcher
from .outreach_memory import outreach_memory, normalize_linkedin_url
from .connections_actions import (
    scrape_connections_list,
    inspect_connection_location,
    extract_profile_about,
    send_connection_dm,
    check_connection_reply,
    is_academic_or_student,
)

logger = logging.getLogger("outreach.connections_pipeline")

CONNECTIONS_CSV_PATH = (
    USER_OUTREACH_DIR / "connections.csv"
    if (USER_OUTREACH_DIR / "connections.csv").exists()
    else LOCAL_DATA_DIR / "connections.csv"
)

CONNECTIONS_SCHEMA = [
    "Full Name", "First Name", "Last Name", "Title", "Company", "Headline",
    "About", "Location", "Region Tier", "LinkedIn URL", "Status", "Sent Date", "Followup Date", "Notes"
]

class ConnectionsPipeline:
    """
    Manages end-to-end outreach to existing 1st-degree connections.
    """

    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or CONNECTIONS_CSV_PATH
        self.backups_dir = self.csv_path.parent / "backups"
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.sender_profile = {
            "name": "Shaurya Sharma",
            "headline": "Junior AI Engineer / Artificial Intelligence Product Developer at GreyBox Technologies",
            "role": "Junior AI Engineer",
        }
        self._ensure_csv()
        outreach_memory.sync_from_csv(self.csv_path)

    def _ensure_csv(self):
        """Initializes connections.csv if it does not already exist."""
        if not self.csv_path.exists():
            df = pd.DataFrame(columns=CONNECTIONS_SCHEMA)
            df.to_csv(self.csv_path, index=False, encoding="utf-8")
            logger.info(f"Initialized new connections CRM at: {self.csv_path}")

    def _backup(self):
        """Creates a timestamped backup before modifying the file."""
        if self.csv_path.exists() and self.csv_path.stat().st_size > 0:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            bak_file = self.backups_dir / f"connections_{ts}.bak"
            shutil.copy2(self.csv_path, bak_file)

    def load_df(self) -> pd.DataFrame:
        """Loads connections dataframe."""
        self._ensure_csv()
        df = pd.read_csv(self.csv_path, dtype=str).fillna("")
        for col in CONNECTIONS_SCHEMA:
            if col not in df.columns:
                df[col] = ""
        return df

    def save_df(self, df: pd.DataFrame):
        """Atomically saves dataframe with backup."""
        self._backup()
        df.to_csv(self.csv_path, index=False, encoding="utf-8")

    def scrape_and_index(
        self,
        max_count: int = 50,
        resolve_locations: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Drives Playwright to scrape 1st-degree connections and applies regional classification.
        """
        def log(msg: str):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)

        log(f"Starting connections scraper (Target: up to {max_count} cards)...")
        engine = BrowserEngine(headless=config.headless)
        try:
            context, page = engine.start()
        except Exception as e:
            err = f"Failed to start browser: {e}"
            log(f"[ERROR] {err}")
            return {"error": err, "count": 0}

        try:
            df = self.load_df()
            existing_urls = set(df["LinkedIn URL"].dropna().str.strip().tolist())
            log(f"Current database has {len(existing_urls)} known connections. Fetching next {max_count} new connections...")

            # 1. Scrape connection cards, skipping already known connections
            raw_connections = scrape_connections_list(
                page, engine, max_count=max_count, progress_callback=progress_callback, existing_urls=existing_urls
            )
            if not raw_connections:
                log("[WARNING] No new connection cards returned.")
                engine.close()
                return {"count": 0, "new": 0, "updated": 0}

            new_count = 0
            updated_count = 0

            for conn in raw_connections:
                url = conn["LinkedIn URL"]
                headline = conn.get("Headline", "")

                # 2. Inspect location on profile if explicitly requested and blank
                location = conn.get("Location", "")
                if resolve_locations and not location:
                    log(f"Inspecting profile location: {conn['Full Name']}...")
                    location = inspect_connection_location(page, engine, url)
                    conn["Location"] = location
                    engine.human_delay(1.5, 3)

                if location:
                    is_eligible, tier_label, normalized_region = classify_location(location)
                else:
                    is_el, t_label, norm_reg = classify_location(headline)
                    if is_el or norm_reg in ["india", "africa"]:
                        is_eligible, tier_label, normalized_region = is_el, t_label, norm_reg
                    else:
                        is_eligible, tier_label, normalized_region = False, "Unknown", "unknown"

                conn["Region Tier"] = tier_label

                is_acad, acad_reason = is_academic_or_student(conn)
                if is_acad:
                    status = "EXCLUDED_ACADEMIA"
                    conn["Notes"] = f"Academic/Student: {acad_reason}"
                elif normalized_region in ["india", "africa"]:
                    status = "REGION_EXCLUDED"
                elif is_eligible:
                    status = "FILTERED_ELIGIBLE"
                else:
                    status = "RETRIEVED"

                conn["Status"] = status

                if url in existing_urls:
                    # Update existing record fields without overriding sent dates
                    idx = df[df["LinkedIn URL"] == url].index[0]
                    if location:
                        df.at[idx, "Location"] = location
                        df.at[idx, "Region Tier"] = tier_label
                        if str(df.at[idx, "Status"]) in ["RETRIEVED", "QUEUED_LATER", "", "nan"]:
                            df.at[idx, "Status"] = status
                    updated_count += 1
                else:
                    new_row = {
                        "Full Name": conn.get("Full Name", ""),
                        "First Name": conn.get("First Name", ""),
                        "Last Name": conn.get("Last Name", ""),
                        "Title": conn.get("Title", ""),
                        "Company": conn.get("Company", ""),
                        "Headline": conn.get("Headline", ""),
                        "Location": location,
                        "Region Tier": tier_label,
                        "LinkedIn URL": url,
                        "Status": status,
                        "Sent Date": "",
                        "Followup Date": "",
                        "Notes": f"Scraped {datetime.now().strftime('%Y-%m-%d')}",
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    new_count += 1
                    existing_urls.add(url)

            self.save_df(df)
            log(f"[SUCCESS] Scraped {len(raw_connections)} connections. New: {new_count}, Updated: {updated_count}")
            engine.close()
            return {"count": len(raw_connections), "new": new_count, "updated": updated_count}
        except Exception as e:
            log(f"[ERROR] Connection scraping encountered error: {e}")
            engine.close()
            return {"error": str(e), "count": 0}

    def run_outreach_batch(
        self,
        max_messages: int = 15,
        dry_run: bool = False,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Executes daily batch for 1st-degree connections:
        Phase 1: Checks for 4-5d follow-ups on MSG_SENT (reply inspection + follow-up dispatch).
        Phase 2: Dispatches initial career openers to priority region leads.
        """
        def clean_ascii(s: str) -> str:
            if not s:
                return ""
            replacements = {
                "\u2011": "-",
                "\u2013": "-",
                "\u2014": "-",
                "\u2018": "'",
                "\u2019": "'",
                "\u201c": '"',
                "\u201d": '"',
                "\u2026": "...",
            }
            for orig, rep in replacements.items():
                s = s.replace(orig, rep)
            return "".join(c if ord(c) < 128 else "" for c in s)

        def log(msg: str):
            clean_msg = clean_ascii(str(msg))
            logger.info(clean_msg)
            if progress_callback:
                try:
                    progress_callback(clean_msg)
                except Exception:
                    pass

        stats = {
            "openers_sent": 0,
            "followups_sent": 0,
            "replies_detected": 0,
            "skipped_or_excluded": 0,
            "dry_run": dry_run,
        }

        df = self.load_df()
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")

        log(f"=== Starting 1st-Degree Connections Outreach Run (Dry Run: {dry_run}) ===")
        log(f"Daily Cap: Max {max_messages} Direct Messages")

        engine = BrowserEngine(headless=config.headless)
        try:
            context, page = engine.start()
        except Exception as e:
            err = f"Failed to start browser engine: {e}"
            log(f"[ERROR] {err}")
            return {"error": err, **stats}

        if not engine.check_logged_in(page):
            log("[WARNING] Not logged into LinkedIn. Please run login assistant first.")
            engine.close()
            return {"error": "Not logged in", **stats}

        log("[OK] LinkedIn session active.")

        # =========================================================================
        # PHASE 1: Process 4-5 Day Follow-Ups (MSG_SENT -> FOLLOWUP_SENT)
        # =========================================================================
        log("\n--- Phase 1: Checking Follow-ups on Previously Sent Messages (4-5 Days) ---")
        msg_sent_rows = df[df["Status"] == "MSG_SENT"].copy()
        log(f"Found {len(msg_sent_rows)} connections in MSG_SENT status.")

        for idx, row in msg_sent_rows.iterrows():
            if (stats["openers_sent"] + stats["followups_sent"]) >= max_messages:
                break

            sent_date_str = str(row.get("Sent Date", "")).strip()
            if not sent_date_str:
                continue

            try:
                sent_d = datetime.strptime(sent_date_str, "%Y-%m-%d").date()
                days_elapsed = (today - sent_d).days
            except Exception:
                continue

            if days_elapsed >= 4:
                name = row.get("Full Name", "Contact")
                url = row.get("LinkedIn URL", "")
                log(f"\n[Follow-Up Check] {name} ({url}) - {days_elapsed} days elapsed since first message.")

                # Check if prospect replied
                if check_connection_reply(page, engine, row.to_dict()):
                    log(f"[HALT] Prospect {name} has replied! Halting automation and marking REPLIED.")
                    df.at[idx, "Status"] = "REPLIED"
                    df.at[idx, "Notes"] = f"Replied on or before {today_str}"
                    stats["replies_detected"] += 1
                    outreach_memory.record_thread_detected(url, name, "Replied in chat thread", status="REPLIED")
                    self.save_df(df)
                    continue

                # Generate low-pressure follow-up
                followup_text = nim_generator.generate_connection_followup(row.to_dict(), self.sender_profile)
                log(f"Drafted follow-up text:\n{followup_text}")

                def on_followup_sent(contact_dict: Dict[str, Any], status_code: str, note_or_text: str):
                    if status_code == "MSG_SENT":
                        df.at[idx, "Status"] = "FOLLOWUP_SENT"
                        df.at[idx, "Followup Date"] = today_str
                    elif status_code == "REPLIED":
                        df.at[idx, "Status"] = "REPLIED"
                        df.at[idx, "Notes"] = f"Replied on or before {today_str}"
                    self.save_df(df)

                status_code, reason = send_connection_dm(
                    page,
                    engine,
                    row.to_dict(),
                    message_text=followup_text,
                    dry_run=dry_run,
                    on_sent_callback=on_followup_sent,
                )
                log(f"Result: {status_code} - {reason}")
                engine.cleanup_screenshots()

                if status_code in ["MSG_SENT", "FOLLOWUP_SENT"]:
                    stats["followups_sent"] += 1
                elif status_code == "REPLIED":
                    stats["replies_detected"] += 1

                if not dry_run and status_code in ["MSG_SENT", "FOLLOWUP_SENT"]:
                    engine.human_delay(15, 25)

        # =========================================================================
        # PHASE 2: Dispatch New Openers to Eligible Connections
        # =========================================================================
        remaining_budget = max_messages - (stats["openers_sent"] + stats["followups_sent"])
        log(f"\n--- Phase 2: Dispatching Initial Openers (Remaining Quota: {remaining_budget}) ---")

        eligible_rows = df[df["Status"].isin(["RETRIEVED", "FILTERED_ELIGIBLE", "QUEUED_LATER"])].copy()

        # Sort priority: Tier 1 (Europe) first, Tier 2, Tier 3, Tier 4, Tier 5 (Unverified/RETRIEVED)
        def sort_priority(tier: str) -> int:
            if "Tier 1" in tier: return 1
            if "Tier 2" in tier: return 2
            if "Tier 3" in tier: return 3
            if "Tier 4" in tier: return 4
            return 5

        eligible_rows["Priority"] = eligible_rows["Region Tier"].apply(sort_priority)
        eligible_rows = eligible_rows[eligible_rows["Priority"] <= 5].sort_values("Priority")
        log(f"Found {len(eligible_rows)} eligible priority leads.")

        for idx, row in eligible_rows.iterrows():
            if stats["openers_sent"] >= remaining_budget:
                break

            name = row.get("Full Name", "Contact")
            url = row.get("LinkedIn URL", "")
            region = row.get("Region Tier", "Unknown")
            title = row.get("Title", "")
            company = row.get("Company", "")

            # Safeguard 0: Check academic or student exclusion
            is_acad, acad_reason = is_academic_or_student(row.to_dict())
            if is_acad:
                log(f"[ACADEMIA EXCLUDED] Skipping {name} ({url}): {acad_reason}")
                df.at[idx, "Status"] = "EXCLUDED_ACADEMIA"
                df.at[idx, "Notes"] = f"Excluded academia: {acad_reason}"
                outreach_memory.record_thread_detected(url, name, acad_reason, status="EXCLUDED_ACADEMIA")
                self.save_df(df)
                stats["skipped_or_excluded"] += 1
                continue

            # Safeguard 1: Check persistent outreach memory first
            already_sent, prior_status = outreach_memory.is_already_contacted(url)
            if already_sent:
                log(f"[OUTREACH MEMORY] {name} ({url}) already recorded as {prior_status}. Updating CSV and skipping.")
                df.at[idx, "Status"] = prior_status
                self.save_df(df)
                stats["skipped_or_excluded"] += 1
                continue

            log(f"\n[Opener {stats['openers_sent'] + 1}/{remaining_budget}] {name} ({region}) - {title} @ {company}")

            # Define dynamic opener generator that runs AFTER About section is extracted from profile
            def generate_opener_with_about(c: Dict[str, Any]) -> str:
                comp = c.get("Company", company)
                hd = c.get("Headline", row.get("Headline", ""))
                ti = c.get("Title", title)
                c_intel = company_researcher.research_company(
                    company_name=comp,
                    headline_hint=hd,
                    title_hint=ti,
                )
                log(f"   [Intel] Industry: {c_intel.get('industry')} | AI Angle: {c_intel.get('ai_angle')}")
                draft = nim_generator.generate_connection_career_opener(
                    contact=c,
                    sender_profile=self.sender_profile,
                    company_intel=c_intel,
                )
                log(f"Drafted opener (tailored with profile About context):\n{draft}")
                return draft

            # Define immediate CSV commit callback
            def on_sent_callback(contact_dict: Dict[str, Any], status_code: str, note_or_text: str):
                df.at[idx, "Status"] = status_code
                if contact_dict.get("About"):
                    df.at[idx, "About"] = contact_dict["About"][:1000]
                if contact_dict.get("Location"):
                    df.at[idx, "Location"] = contact_dict["Location"]
                if contact_dict.get("Region Tier"):
                    df.at[idx, "Region Tier"] = contact_dict["Region Tier"]
                if status_code == "MSG_SENT":
                    df.at[idx, "Sent Date"] = today_str
                elif status_code == "REPLIED":
                    df.at[idx, "Notes"] = f"Replied on or before {today_str}"
                elif status_code in ["EXCLUDED_ACADEMIA", "REGION_EXCLUDED", "UNREACHABLE", "OVERLAY_FAILED"]:
                    df.at[idx, "Notes"] = note_or_text
                self.save_df(df)
                log(f"[STATE SAVED] Immediately committed {name} -> {status_code} to CSV.")

            try:
                status_code, reason = send_connection_dm(
                    page,
                    engine,
                    row.to_dict(),
                    dry_run=dry_run,
                    opener_generator=generate_opener_with_about,
                    on_sent_callback=on_sent_callback,
                )
            except Exception as loop_err:
                log(f"[ERROR] Exception during outreach to {name}: {loop_err}")
                status_code, reason = "ERROR", str(loop_err)

            log(f"Result: {status_code} - {reason}")

            # Zero-footprint screenshot cleanup after every message
            engine.cleanup_screenshots()

            if status_code == "MSG_SENT":
                stats["openers_sent"] += 1
                if not dry_run:
                    engine.human_delay(15, 25)
            elif status_code == "REPLIED":
                stats["replies_detected"] += 1
                engine.human_delay(2, 3)
            elif status_code in ["ALREADY_SENT", "UNREACHABLE", "OVERLAY_FAILED", "EXCLUDED_ACADEMIA", "REGION_EXCLUDED"]:
                stats["skipped_or_excluded"] += 1
                engine.human_delay(2, 3)

        self.save_df(df)
        engine.close()
        log(f"\n=== Connections Outreach Run Complete ===")
        log(f"Openers Sent: {stats['openers_sent']} | Follow-ups Sent: {stats['followups_sent']} | Replies Detected: {stats['replies_detected']}")
        return stats

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns connection counts grouped by status and region tier."""
        df = self.load_df()
        status_counts = df["Status"].value_counts().to_dict()
        tier_counts = df["Region Tier"].value_counts().to_dict()
        return {
            "total_connections": len(df),
            "by_status": status_counts,
            "by_region_tier": tier_counts,
            "csv_path": str(self.csv_path),
        }

connections_pipeline = ConnectionsPipeline()
