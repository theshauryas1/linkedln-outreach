import re
from pathlib import Path
from typing import Dict, Any, Optional

from .config import config

class TemplateEngine:
    """Renders message templates with contact variables and checks character limits."""

    def __init__(self, intro_path: Optional[Path] = None, followup_path: Optional[Path] = None):
        self.intro_path = intro_path or config.intro_template
        self.followup_path = followup_path or config.followup_template

    def load_template(self, template_path: Path) -> str:
        """Loads template text from disk."""
        if not template_path.exists():
            return ""
        return template_path.read_text(encoding="utf-8").strip()

    def render(self, template_text: str, contact: Dict[str, Any]) -> str:
        """
        Replaces variables like {First Name}, {Company}, {Title}, {Location}.
        Handles case insensitivity, spaces, and missing fields.
        """
        first_name = (contact.get("First Name") or "").strip()
        last_name = (contact.get("Last Name") or "").strip()
        full_name = (contact.get("Full Name") or f"{first_name} {last_name}").strip()
        company = (contact.get("Company") or "").strip()
        title = (contact.get("Title") or "").strip()
        location = (contact.get("Location") or "").strip()

        from .composio_linkedin import composio_linkedin
        sender_vars = composio_linkedin.get_sender_variables()

        # Variable mapping
        vars_map = {
            "first name": first_name or "there",
            "firstname": first_name or "there",
            "last name": last_name,
            "lastname": last_name,
            "full name": full_name or "there",
            "fullname": full_name or "there",
            "company": company or "your company",
            "title": title or "your role",
            "location": location,
            "sender name": sender_vars["sender_name"],
            "sender first name": sender_vars["sender_first_name"],
            "sender headline": sender_vars["sender_headline"],
            "sender company": sender_vars["sender_company"],
            "sender profile": sender_vars["sender_profile_url"],
        }

        rendered = template_text

        def replace_var(match):
            key = match.group(1).strip().lower()
            return vars_map.get(key, match.group(0))

        # Matches {First Name}, { Company }, etc.
        rendered = re.sub(r"\{\s*([^}]+)\s*\}", replace_var, rendered)

        # Remove robotic AI punctuation (e.g. em dashes, unnecessary quotation blocks)
        rendered = rendered.replace("—", "-").replace("–", "-")
        # Collapse multiple spaces or multiple blank lines
        rendered = re.sub(r"[ \t]+", " ", rendered)
        rendered = re.sub(r"\n{3,}", "\n\n", rendered)

        return rendered.strip()

    def get_intro_message(self, contact: Dict[str, Any]) -> str:
        """Returns rendered intro message for contact."""
        text = self.load_template(self.intro_path)
        return self.render(text, contact)

    def get_followup_message(self, contact: Dict[str, Any]) -> str:
        """Returns rendered followup message for contact."""
        text = self.load_template(self.followup_path)
        return self.render(text, contact)

template_engine = TemplateEngine()
