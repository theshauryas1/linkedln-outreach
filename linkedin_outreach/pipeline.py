import logging
import time
from datetime import date
from typing import Dict, Any, Optional, Callable

from .config import config
from .csv_manager import CSVManager
from .templates_engine import template_engine
from .browser_engine import BrowserEngine
from .linkedin_actions import (
    send_connection_request,
    check_connected_and_send_intro,
    send_followup_message,
)

logger = logging.getLogger("outreach.pipeline")

class OutreachPipeline:
    """
    Executes the 3-step LinkedIn Outreach workflow according to the daily automation rules.
    """

    def __init__(self, csv_manager: Optional[CSVManager] = None):
        self.csv = csv_manager or CSVManager()
        self.engine: Optional[BrowserEngine] = None

    def run(
        self,
        invite_limit: int = 20,
        message_limit: int = 20,
        dry_run: bool = False,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the daily outreach sequence.
        """
        def log(msg: str):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)

        stats = {
            "invites_sent": 0,
            "intros_sent": 0,
            "followups_sent": 0,
            "replies_detected": 0,
            "skipped_or_failed": 0,
            "dry_run": dry_run,
        }

        today_str = date.today().strftime("%Y-%m-%d")
        log(f"=== Starting LinkedIn Outreach Run (Dry Run: {dry_run}) ===")
        log(f"Daily Limits: Max {invite_limit} Invites | Max {message_limit} Messages (Shared Cap)")

        self.engine = BrowserEngine(headless=config.headless)
        try:
            context, page = self.engine.start()
        except Exception as e:
            err = f"Failed to start browser engine: {e}"
            log(f"[ERROR] {err}")
            return {"error": err, **stats}

        # Verify LinkedIn Login
        log("Verifying LinkedIn session...")
        if not self.engine.check_logged_in(page):
            log("[WARNING] Not logged into LinkedIn. Launching login assistant...")
            logged_in = self.engine.interactive_login()
            if not logged_in:
                err = "Could not verify LinkedIn login. Please run 'python -m linkedin_outreach.cli login' first."
                log(f"[ABORT] {err}")
                self.engine.close()
                return {"error": err, **stats}

        log("[OK] LinkedIn session active.")

        # =========================================================================
        # STEP 1: Process Blank Rows -> Send Invites (Limit: invite_limit)
        # =========================================================================
        log("\n--- STEP 1: Sending Connection Requests for Blank Rows ---")
        uncontacted = self.csv.get_uncontacted(limit=invite_limit)
        log(f"Found {len(uncontacted)} uncontacted leads (Max {invite_limit}).")

        for contact in uncontacted:
            if stats["invites_sent"] >= invite_limit:
                break

            name = contact.get("Full Name") or f"{contact.get('First Name')} {contact.get('Last Name')}"
            url = contact.get("LinkedIn URL", "")
            idx = contact["_df_index"]

            log(f"\n[Invite {stats['invites_sent'] + 1}/{invite_limit}] {name} ({url})")

            status_code, reason = send_connection_request(page, self.engine, contact, dry_run=dry_run)
            log(f"Result: {status_code} - {reason}")

            if status_code in ("INVITED", "ALREADY_CONNECTED"):
                new_status = "INVITED" if status_code == "INVITED" else "CONNECTED"
                self.csv.update_row(
                    df_index=idx,
                    status=new_status,
                    invited_date=today_str,
                    notes=reason,
                )
                stats["invites_sent"] += 1
            elif status_code == "LIMIT_REACHED":
                log("[ALERT] LinkedIn weekly invite limit reached. Stopping Step 1.")
                break
            else:
                self.csv.update_row(df_index=idx, notes=f"Invite issue: {reason}")
                stats["skipped_or_failed"] += 1

            if not dry_run:
                self.engine.human_delay()

        # =========================================================================
        # STEP 2: Process INVITED 3d+ -> Check Acceptance & Send Intro Message
        # =========================================================================
        remaining_messages = message_limit - (stats["intros_sent"] + stats["followups_sent"])
        log(f"\n--- STEP 2: Checking Acceptances for INVITED (3d+) (Quota: {remaining_messages}) ---")

        pending_invites = self.csv.get_pending_invites(
            min_days=config.invite_wait_days,
            limit=remaining_messages,
        )
        log(f"Found {len(pending_invites)} contacts invited >= {config.invite_wait_days} days ago.")

        for contact in pending_invites:
            if stats["intros_sent"] + stats["followups_sent"] >= message_limit:
                log("Message quota reached. Ending message steps.")
                break

            name = contact.get("Full Name") or contact.get("First Name", "")
            idx = contact["_df_index"]
            days_ago = contact.get("_days_since_invited", 3)

            log(f"\n[Check Intro] {name} (Invited {days_ago} days ago)")
            intro_msg = template_engine.get_intro_message(contact)

            status_code, reason = check_connected_and_send_intro(
                page, self.engine, contact, intro_msg, dry_run=dry_run
            )
            log(f"Result: {status_code} - {reason}")

            if status_code == "MSG1_SENT":
                self.csv.update_row(
                    df_index=idx,
                    status="MSG1_SENT",
                    connected_date=today_str,
                    notes=reason,
                )
                stats["intros_sent"] += 1
            elif status_code == "REPLIED":
                self.csv.update_row(
                    df_index=idx,
                    status="REPLIED",
                    connected_date=today_str,
                    notes=reason,
                )
                stats["replies_detected"] += 1
            elif status_code == "STILL_PENDING":
                # Leave status as INVITED
                pass
            else:
                stats["skipped_or_failed"] += 1

            if not dry_run:
                self.engine.human_delay()

        # =========================================================================
        # STEP 3: Process MSG1_SENT 5d+ -> Check Reply & Send Followup Message
        # =========================================================================
        remaining_messages = message_limit - (stats["intros_sent"] + stats["followups_sent"])
        log(f"\n--- STEP 3: Checking Follow-ups for MSG1_SENT (5d+) (Quota: {remaining_messages}) ---")

        pending_followups = self.csv.get_pending_followups(
            min_days=config.followup_wait_days,
            limit=remaining_messages,
        )
        log(f"Found {len(pending_followups)} contacts messaged >= {config.followup_wait_days} days ago.")

        for contact in pending_followups:
            if stats["intros_sent"] + stats["followups_sent"] >= message_limit:
                break

            name = contact.get("Full Name") or contact.get("First Name", "")
            idx = contact["_df_index"]
            days_ago = contact.get("_days_since_connected", 5)

            log(f"\n[Followup] {name} (Connected/Messaged {days_ago} days ago)")
            followup_msg = template_engine.get_followup_message(contact)

            status_code, reason = send_followup_message(
                page, self.engine, contact, followup_msg, dry_run=dry_run
            )
            log(f"Result: {status_code} - {reason}")

            if status_code == "MSG2_SENT":
                self.csv.update_row(
                    df_index=idx,
                    status="MSG2_SENT",
                    notes=reason,
                )
                stats["followups_sent"] += 1
            elif status_code == "REPLIED":
                self.csv.update_row(
                    df_index=idx,
                    status="REPLIED",
                    notes=reason,
                )
                stats["replies_detected"] += 1
            else:
                stats["skipped_or_failed"] += 1

            if not dry_run:
                self.engine.human_delay()

        # Summary
        log("\n" + "=" * 55)
        log("  OUTREACH RUN COMPLETE")
        log("=" * 55)
        log(f"  New Invites Sent:      {stats['invites_sent']}")
        log(f"  Intro Messages (MSG1): {stats['intros_sent']}")
        log(f"  Follow-ups (MSG2):     {stats['followups_sent']}")
        log(f"  Replies Detected:      {stats['replies_detected']}")
        log(f"  Skipped / Issues:      {stats['skipped_or_failed']}")
        log("=" * 55)

        # Cleanup
        self.engine.close()
        return stats
