import os
import shutil
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

from .config import config, USER_OUTREACH_DIR

REQUIRED_COLUMNS = [
    "First Name",
    "Last Name",
    "Full Name",
    "Title",
    "Company",
    "Location",
    "LinkedIn URL",
    "LinkedIn Status",
    "Invited Date",
    "Connected Date",
    "Notes",
]

class CSVManager:
    """Manages the outreach CSV database with atomic saves and query helpers."""

    def __init__(self, filepath: Optional[Path] = None):
        self.filepath = filepath or config.contacts_csv
        self.ensure_file_exists()

    def ensure_file_exists(self):
        """Ensures the CSV file exists with proper columns."""
        if not self.filepath.exists():
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            df = pd.DataFrame(columns=REQUIRED_COLUMNS)
            df.to_csv(self.filepath, index=False)
        else:
            # Verify columns exist
            df = self.read()
            missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
            if missing:
                for c in missing:
                    df[c] = ""
                self._save(df)

    def read(self) -> pd.DataFrame:
        """Reads CSV safely, treating empty values as empty strings."""
        if not self.filepath.exists():
            self.ensure_file_exists()
        df = pd.read_csv(self.filepath, dtype=str).fillna("")
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df

    def _save(self, df: pd.DataFrame):
        """Atomic write to prevent file corruption during execution."""
        temp_file = self.filepath.with_suffix(".tmp")
        df.to_csv(temp_file, index=False)
        shutil.move(str(temp_file), str(self.filepath))

    def get_stats(self) -> Dict[str, int]:
        """Returns counts for all outreach stages."""
        df = self.read()
        statuses = df["LinkedIn Status"].str.strip().str.upper()
        
        total = len(df)
        blank = int((statuses == "").sum())
        invited = int((statuses == "INVITED").sum())
        msg1_sent = int((statuses == "MSG1_SENT").sum())
        msg2_sent = int((statuses == "MSG2_SENT").sum())
        replied = int((statuses == "REPLIED").sum())
        other = total - (blank + invited + msg1_sent + msg2_sent + replied)

        return {
            "total": total,
            "blank": blank,
            "invited": invited,
            "msg1_sent": msg1_sent,
            "msg2_sent": msg2_sent,
            "replied": replied,
            "other": other,
        }

    def get_uncontacted(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Step 1 candidate rows: LinkedIn Status is blank."""
        df = self.read()
        mask = df["LinkedIn Status"].str.strip() == ""
        candidates = df[mask].head(limit)
        results = []
        for idx, row in candidates.iterrows():
            d = row.to_dict()
            d["_df_index"] = idx
            results.append(d)
        return results

    def get_pending_invites(self, min_days: int = 3, limit: int = 20) -> List[Dict[str, Any]]:
        """Step 2 candidate rows: INVITED and Invited Date >= min_days ago."""
        df = self.read()
        mask = df["LinkedIn Status"].str.strip().str.upper() == "INVITED"
        candidates = df[mask]
        results = []
        today = date.today()

        for idx, row in candidates.iterrows():
            invited_date_str = str(row["Invited Date"]).strip()
            if not invited_date_str:
                continue
            try:
                inv_date = datetime.strptime(invited_date_str, "%Y-%m-%d").date()
                delta_days = (today - inv_date).days
                if delta_days >= min_days:
                    d = row.to_dict()
                    d["_df_index"] = idx
                    d["_days_since_invited"] = delta_days
                    results.append(d)
                    if len(results) >= limit:
                        break
            except ValueError:
                # If date format is invalid, keep for manual review
                continue

        return results

    def get_pending_followups(self, min_days: int = 5, limit: int = 20) -> List[Dict[str, Any]]:
        """Step 3 candidate rows: MSG1_SENT and Connected Date >= min_days ago."""
        df = self.read()
        mask = df["LinkedIn Status"].str.strip().str.upper() == "MSG1_SENT"
        candidates = df[mask]
        results = []
        today = date.today()

        for idx, row in candidates.iterrows():
            conn_date_str = str(row["Connected Date"]).strip()
            if not conn_date_str:
                # Fallback to Invited Date if Connected Date was blank
                conn_date_str = str(row["Invited Date"]).strip()
            if not conn_date_str:
                continue
            try:
                conn_date = datetime.strptime(conn_date_str, "%Y-%m-%d").date()
                delta_days = (today - conn_date).days
                if delta_days >= min_days:
                    d = row.to_dict()
                    d["_df_index"] = idx
                    d["_days_since_connected"] = delta_days
                    results.append(d)
                    if len(results) >= limit:
                        break
            except ValueError:
                continue

        return results

    def update_row(
        self,
        df_index: int,
        status: Optional[str] = None,
        invited_date: Optional[str] = None,
        connected_date: Optional[str] = None,
        notes: Optional[str] = None,
    ):
        """Updates a contact row and writes atomically to disk."""
        df = self.read()
        if df_index not in df.index:
            raise IndexError(f"Row index {df_index} not found in CSV.")

        if status is not None:
            df.at[df_index, "LinkedIn Status"] = status
        if invited_date is not None:
            df.at[df_index, "Invited Date"] = invited_date
        if connected_date is not None:
            df.at[df_index, "Connected Date"] = connected_date
        if notes is not None:
            existing = str(df.at[df_index, "Notes"]).strip()
            if existing and existing != notes:
                df.at[df_index, "Notes"] = f"{existing}; {notes}"
            else:
                df.at[df_index, "Notes"] = notes

        self._save(df)

    def add_contact(self, contact: Dict[str, str]):
        """Adds a new contact to the CSV."""
        df = self.read()
        new_row = {col: contact.get(col, "") for col in REQUIRED_COLUMNS}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        self._save(df)

def sync_to_user_home():
    """Copies current data and templates to ~/outreach for standard user outreach location."""
    USER_OUTREACH_DIR.mkdir(parents=True, exist_ok=True)
    home_csv = USER_OUTREACH_DIR / "contacts.csv"
    if not home_csv.exists() and config.contacts_csv.exists():
        shutil.copy(str(config.contacts_csv), str(home_csv))
    
    for tpl in ["intro.txt", "followup.txt"]:
        src = config.intro_template.parent / tpl
        dst = USER_OUTREACH_DIR / tpl
        if not dst.exists() and src.exists():
            shutil.copy(str(src), str(dst))
