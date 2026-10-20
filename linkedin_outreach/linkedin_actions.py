import time
import logging
from typing import Tuple, Dict, Any, Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from .browser_engine import BrowserEngine

logger = logging.getLogger("outreach.actions")

def is_profile_connected(page: Page) -> bool:
    """Checks if the profile has an active Message button and no Connect/Pending."""
    try:
        # If Pending button is visible, still waiting
        if page.locator("button:has-text('Pending'), button[aria-label*='Pending']").first.is_visible(timeout=1500):
            return False

        # If primary Message button is visible on the profile top card
        msg_btn = page.locator("main section button:has-text('Message'), main section a:has-text('Message')").first
        if msg_btn.is_visible(timeout=2000):
            # Check if there is also a Connect button (sometimes shown for 2nd/3rd degree InMail)
            connect_btn = page.locator("main section button:has-text('Connect')").first
            if connect_btn.is_visible(timeout=1000):
                return False
            return True
        return False
    except Exception:
        return False

def check_for_replies_in_chat(page: Page, contact_name: str) -> bool:
    """
    Checks if there are incoming messages sent by the contact in the active chat overlay.
    """
    try:
        time.sleep(2)
        # Check message thread items
        events = page.locator("li.msg-s-message-list__event, div.msg-s-event-listitem")
        count = events.count()
        if count == 0:
            return False

        first_name = contact_name.split()[0].lower() if contact_name else ""

        # Scan message sender headers
        sender_elements = page.locator(".msg-s-message-group__name, .msg-s-event-listitem__profile-name")
        for i in range(sender_elements.count()):
            sender_text = sender_elements.nth(i).inner_text().strip().lower()
            if first_name and first_name in sender_text:
                return True
        return False
    except Exception as e:
        logger.debug(f"Error checking chat replies: {e}")
        return False

def send_connection_request(
    page: Page,
    engine: BrowserEngine,
    contact: Dict[str, Any],
    dry_run: bool = False,
) -> Tuple[str, str]:
    """
    Step 1: Visits LinkedIn profile and sends connection request without note.
    Returns: (STATUS_CODE, message)
    """
    url = contact.get("LinkedIn URL", "").strip()
    if not url:
        return "ERROR", "Missing LinkedIn URL"

    logger.info(f"Visiting profile: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=25000)
    engine.human_delay(2, 4)
    engine.human_scroll(page, distance=250)

    # 1. Check if already connected or pending
    if page.locator("button:has-text('Pending'), button[aria-label*='Pending']").first.is_visible(timeout=1500):
        return "INVITED", "Invite was already pending on LinkedIn"

    if is_profile_connected(page):
        return "ALREADY_CONNECTED", "Already connected with this contact"

    # 2. Look for Connect button
    connect_btn = page.locator(
        "main section button:has-text('Connect'), button[aria-label*='Invite'][aria-label*='to connect']"
    ).first

    found_connect = False
    if connect_btn.is_visible(timeout=2500):
        found_connect = True
    else:
        # Check under 'More' action dropdown
        more_btn = page.locator(
            "main section button:has-text('More'), main section button[aria-label='More actions']"
        ).first
        if more_btn.is_visible(timeout=2000):
            more_btn.click()
            time.sleep(1)
            # Find Connect inside dropdown
            dropdown_connect = page.locator(
                "div[role='menu'] div:has-text('Connect'), div[role='menu'] span:has-text('Connect')"
            ).first
            if dropdown_connect.is_visible(timeout=2000):
                connect_btn = dropdown_connect
                found_connect = True

    if not found_connect:
        return "FAILED", "Connect button not found (might require email or follow-only)"

    if dry_run:
        return "INVITED", "[DRY RUN] Would click Connect and Send without note"

    # 3. Click Connect
    connect_btn.click()
    time.sleep(1.5)

    # 4. Handle confirmation modal ('Send without a note' / 'Send')
    send_without_note = page.locator(
        "button:has-text('Send without a note'), button[aria-label='Send without a note']"
    ).first
    if send_without_note.is_visible(timeout=3000):
        send_without_note.click()
    else:
        # Check for direct 'Send' button
        send_btn = page.locator(
            "div[role='dialog'] button:has-text('Send'), button[aria-label='Send now']"
        ).first
        if send_btn.is_visible(timeout=2000):
            send_btn.click()

    time.sleep(2)

    # Check for invitation limit popup
    limit_warning = page.locator("text='invitation limit', text='reached your limit'").first
    if limit_warning.is_visible(timeout=1500):
        # Dismiss modal
        dismiss_btn = page.locator("button[aria-label='Dismiss'], button:has-text('Got it')").first
        if dismiss_btn.is_visible():
            dismiss_btn.click()
        return "LIMIT_REACHED", "LinkedIn weekly invitation limit reached"

    return "INVITED", "Connection request sent successfully"

def check_connected_and_send_intro(
    page: Page,
    engine: BrowserEngine,
    contact: Dict[str, Any],
    intro_text: str,
    dry_run: bool = False,
) -> Tuple[str, str]:
    """
    Step 2: Checks if contact accepted invite (INVITED 3d+). If accepted, sends intro message.
    """
    url = contact.get("LinkedIn URL", "").strip()
    if not url:
        return "ERROR", "Missing LinkedIn URL"

    logger.info(f"Checking acceptance for: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=25000)
    engine.human_delay(2, 4)

    # If still pending, keep as INVITED
    if page.locator("button:has-text('Pending'), button[aria-label*='Pending']").first.is_visible(timeout=2000):
        return "STILL_PENDING", "Invite is still pending acceptance"

    # Check if connected
    if not is_profile_connected(page):
        return "NOT_CONNECTED", "Profile does not show active connected state"

    # Contact is connected! Open Message dialog
    msg_btn = page.locator("main section button:has-text('Message'), main section a:has-text('Message')").first
    msg_btn.click()
    time.sleep(2)

    # Check for previous replies from contact
    contact_name = contact.get("Full Name") or contact.get("First Name", "")
    if check_for_replies_in_chat(page, contact_name):
        return "REPLIED", "Prospect already replied; stopping sequence"

    if dry_run:
        # Close message box if opened
        close_chat_overlay(page)
        return "MSG1_SENT", f"[DRY RUN] Would send intro message: {intro_text[:50]}..."

    # Type and send intro message
    success = type_and_send_message(page, engine, intro_text)
    close_chat_overlay(page)

    if success:
        engine.cleanup_screenshots()
        return "MSG1_SENT", "Intro message (MSG1) sent successfully"
    else:
        engine.cleanup_screenshots()
        return "FAILED", "Failed to type or send intro message"

def send_followup_message(
    page: Page,
    engine: BrowserEngine,
    contact: Dict[str, Any],
    followup_text: str,
    dry_run: bool = False,
) -> Tuple[str, str]:
    """
    Step 3: Checks if prospect replied (MSG1_SENT 5d+). If no reply, sends followup message.
    """
    url = contact.get("LinkedIn URL", "").strip()
    if not url:
        return "ERROR", "Missing LinkedIn URL"

    logger.info(f"Opening chat to check followup for: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=25000)
    engine.human_delay(2, 4)

    # Click Message button
    msg_btn = page.locator("main section button:has-text('Message'), main section a:has-text('Message')").first
    if not msg_btn.is_visible(timeout=4000):
        return "FAILED", "Message button not visible on profile"

    msg_btn.click()
    time.sleep(2)

    # Check if prospect replied
    contact_name = contact.get("Full Name") or contact.get("First Name", "")
    if check_for_replies_in_chat(page, contact_name):
        close_chat_overlay(page)
        return "REPLIED", "Prospect replied to previous message; sequence stopped"

    if dry_run:
        close_chat_overlay(page)
        return "MSG2_SENT", f"[DRY RUN] Would send follow-up message: {followup_text[:50]}..."

    # Type and send follow-up message
    success = type_and_send_message(page, engine, followup_text)
    close_chat_overlay(page)

    engine.cleanup_screenshots()
    if success:
        return "MSG2_SENT", "Follow-up message (MSG2) sent successfully"
    else:
        return "FAILED", "Failed to type or send follow-up message"

def type_and_send_message(page: Page, engine: BrowserEngine, text: str) -> bool:
    """Types message into LinkedIn chat overlay textbox and clicks send."""
    try:
        textbox = page.locator(
            "div.msg-form__contenteditable[role='textbox'], div[role='textbox'][contenteditable='true']"
        ).last
        if not textbox.is_visible(timeout=5000):
            return False

        engine.human_type(textbox, text)
        time.sleep(1)

        # Click send button
        send_btn = page.locator(
            "button.msg-form__send-button, button[type='submit']:has-text('Send')"
        ).last
        if send_btn.is_enabled(timeout=3000):
            send_btn.click()
            time.sleep(2)
            return True
        return False
    except Exception as e:
        logger.error(f"Error typing/sending message: {e}")
        return False

def close_chat_overlay(page: Page):
    """Closes any open messaging conversation bubble."""
    try:
        close_btn = page.locator(
            "button[data-control-name='overlay.close_conversation_window'], button:has-text('Close conversation')"
        ).first
        if close_btn.is_visible(timeout=1000):
            close_btn.click()
    except Exception:
        pass
