import os
from pathlib import Path
from dataclasses import dataclass

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
HOME_DIR = Path.home()
USER_OUTREACH_DIR = HOME_DIR / "outreach"
LOCAL_DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
CHROME_PROFILE_DIR = BASE_DIR / "chrome_profile"
LOGS_DIR = BASE_DIR / "logs"

@dataclass
class OutreachConfig:
    # CSV file path - checks ~/outreach/contacts.csv first, fallback to ./data/contacts.csv
    contacts_csv: Path = (
        USER_OUTREACH_DIR / "contacts.csv"
        if (USER_OUTREACH_DIR / "contacts.csv").exists()
        else LOCAL_DATA_DIR / "contacts.csv"
    )
    
    # Message templates
    intro_template: Path = (
        USER_OUTREACH_DIR / "intro.txt"
        if (USER_OUTREACH_DIR / "intro.txt").exists()
        else TEMPLATES_DIR / "intro.txt"
    )
    followup_template: Path = (
        USER_OUTREACH_DIR / "followup.txt"
        if (USER_OUTREACH_DIR / "followup.txt").exists()
        else TEMPLATES_DIR / "followup.txt"
    )
    
    # Sequence delays & limits
    invite_wait_days: int = 3          # Step 2: Check connected if invited >= 3 days ago
    followup_wait_days: int = 5        # Step 3: Send follow-up if connected >= 5 days ago
    
    daily_invite_limit: int = 20       # Max new connection invites per daily run
    daily_message_limit: int = 20      # Shared cap for intro + follow-up messages
    
    # Anti-detection & Human behavior settings
    min_action_delay_secs: int = 15    # Delay between contacts (seconds)
    max_action_delay_secs: int = 25    # Max delay between contacts
    typing_delay_min: float = 0.04     # Keystroke delay min (seconds)
    typing_delay_max: float = 0.11     # Keystroke delay max (seconds)
    
    # Browser connection
    cdp_ports: tuple = (18800, 9222)   # Ports to check for running Chrome (Chrome CDP / remote debugging)
    headless: bool = False             # Must run headed for LinkedIn session persistence & stealth
    user_data_dir: Path = CHROME_PROFILE_DIR
    
    # Logging
    log_file: Path = LOGS_DIR / "outreach.log"

def ensure_directories():
    """Ensure all required local and user directories exist."""
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    USER_OUTREACH_DIR.mkdir(parents=True, exist_ok=True)

config = OutreachConfig()
