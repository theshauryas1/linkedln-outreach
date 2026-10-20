import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from .config import config, ensure_directories
from .pipeline import OutreachPipeline

logger = logging.getLogger("outreach.scheduler")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def run_daily_job(dry_run: bool = False):
    """Executes the daily outreach job."""
    logger.info(f"Triggering scheduled daily outreach at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    pipeline = OutreachPipeline()
    res = pipeline.run(
        invite_limit=config.daily_invite_limit,
        message_limit=config.daily_message_limit,
        dry_run=dry_run,
        progress_callback=lambda msg: logger.info(msg),
    )
    logger.info(f"Daily outreach finished with results: {res}")
    return res

def run_schedule_daemon(target_hour: int = 9, target_minute: int = 0, dry_run: bool = False):
    """
    Runs an internal daemon that checks every minute and triggers at the target time (default 09:00 AM).
    """
    ensure_directories()
    time_str = f"{target_hour:02d}:{target_minute:02d}"
    print("\n" + "=" * 65)
    print(f"  LINKEDIN OUTREACH SCHEDULER DAEMON ACTIVE")
    print(f"  Target Run Time: {time_str} Every Morning")
    print(f"  Dry Run: {dry_run}")
    print("=" * 65)
    print("  Keep this window open or run as a Windows background task.")
    print("  Press Ctrl+C to stop.\n")

    last_run_date = None

    while True:
        now = datetime.now()
        current_date = now.date()

        if now.hour == target_hour and now.minute == target_minute and last_run_date != current_date:
            logger.info(f"Time matched ({time_str})! Launching daily pipeline...")
            try:
                run_daily_job(dry_run=dry_run)
                last_run_date = current_date
            except Exception as e:
                logger.error(f"Error during scheduled execution: {e}")

        time.sleep(30)

def main():
    parser = argparse.ArgumentParser(description="LinkedIn Outreach Daily Scheduler")
    parser.add_argument("--now", action="store_true", help="Run the daily pipeline immediately once")
    parser.add_argument("--time", type=str, default="09:00", help="Target time in HH:MM format (default: 09:00)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions without sending")
    args = parser.parse_args()

    if args.now:
        run_daily_job(dry_run=args.dry_run)
    else:
        try:
            parts = args.time.split(":")
            h, m = int(parts[0]), int(parts[1])
        except Exception:
            h, m = 9, 0
        run_schedule_daemon(target_hour=h, target_minute=m, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
