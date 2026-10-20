"""
LinkedIn DOM Actions for Existing 1st-Degree Connections:
1. Scraping 1st-degree connections list (/mynetwork/invite-connect/connections/).
2. Inspecting profile location on top card.
3. Extracting About section for deep context.
4. Sending direct messages with live chat thread verification to prevent duplicate sends.
5. Checking message threads for replies.
"""

import re
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from .browser_engine import BrowserEngine
from .region_filter import classify_location
from .outreach_memory import outreach_memory

logger = logging.getLogger("outreach.connections_actions")

def is_academic_or_student(contact: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Checks if a contact is a professor, faculty member, teacher, student, PhD candidate,
    or affiliated with academia/educational roles.
    Returns (True, reason) if excluded, (False, "") if eligible.
    """
    headline = str(contact.get("Headline", "")).lower()
    title = str(contact.get("Title", "")).lower()
    company = str(contact.get("Company", "")).lower()
    about = str(contact.get("About", "")).lower()

    text_to_check = f"{headline} | {title} | {company}"

    # 1. Direct professor / faculty keywords
    faculty_keywords = [
        "professor", "prof.", "asst. professor", "assistant professor",
        "assoc. professor", "associate professor", "adjunct professor", "adjunct",
        "lecturer", "senior lecturer", "faculty", "dean", "instructor", "academician",
        "schoolteacher", "postdoc", "postdoctoral", "teaching assistant", "research assistant",
    ]
    for kw in faculty_keywords:
        if kw in text_to_check:
            return True, f"Academic faculty role detected: '{kw}'"

    # 2. Student keywords
    student_keywords = [
        "phd student", "ph.d. student", "phd candidate", "ph.d candidate", "ph.d. candidate",
        "doctoral student", "doctoral candidate", "master student", "master's student",
        "masters student", "bachelor student", "bachelor's student", "bachelors student",
        "undergraduate", "graduate student", "student at", "studying at", "student @",
        "intern at", "intern @", "internship",
    ]
    for kw in student_keywords:
        if kw in text_to_check:
            return True, f"Student role detected: '{kw}'"

    # 3. Check for standalone 'student' in title or headline
    words = set(re.findall(r"\b[a-z]+\b", f"{headline} {title}"))
    if "student" in words:
        return True, "Role is identified as student"

    # 4. Check if company is an educational institution and role is academic
    academic_institutions = ["university", "college", "school of", "hochschule", "universität", "universite", "universita"]
    if any(inst in company for inst in academic_institutions):
        academic_roles = ["phd", "researcher", "scholar", "fellow", "candidate", "trainee", "faculty", "lecturer", "assistant", "student"]
        if any(role in text_to_check for role in academic_roles):
            return True, f"Academic institution '{company}' with role in '{title or headline}'"

    # 5. Check About text if available
    if about:
        for kw in [
            "i am a phd student", "i am a student", "current phd student",
            "phd candidate at", "professor at", "assistant professor at",
            "associate professor at", "postdoctoral researcher at", "postdoc at"
        ]:
            if kw in about:
                return True, f"About section indicates academic/student: '{kw}'"

    return False, ""

CONNECTIONS_URL = "https://www.linkedin.com/mynetwork/invite-connect/connections/"

def scrape_connections_list(
    page: Page,
    engine: BrowserEngine,
    max_count: int = 50,
    progress_callback: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Navigates to the LinkedIn 1st-degree connections page and scrapes connection cards.
    Extracts: Full Name, Headline, Profile URL, Location, Title, Company.
    """
    def log(msg: str):
        logger.info(msg)
        if progress_callback:
            progress_callback(msg)

    log(f"Navigating to LinkedIn connections page: {CONNECTIONS_URL}")
    page.goto(CONNECTIONS_URL, wait_until="domcontentloaded", timeout=30000)
    engine.human_delay(2, 4)

    # Check for login redirect
    if "login" in page.url or "checkpoint" in page.url:
        log("[ERROR] Not logged in or checkpoint encountered.")
        return []

    def clean_bmp(s: str) -> str:
        if not s:
            return ""
        return "".join(c for c in s if ord(c) < 65536).strip()

    scraped: List[Dict[str, Any]] = []
    seen_urls = set()
    scroll_attempts = 0
    max_scrolls = max(8, (max_count // 5) + 3)

    while len(scraped) < max_count and scroll_attempts < max_scrolls:
        # Check both modern LinkedIn structure and legacy .mn-connection-card
        legacy_cards = page.locator(".mn-connection-card, li.mn-connection-card")
        if legacy_cards.count() > 0:
            for i in range(legacy_cards.count()):
                if len(scraped) >= max_count:
                    break
                try:
                    card = legacy_cards.nth(i)
                    link_el = card.locator("a[href*='/in/']").first
                    if not link_el.is_visible(timeout=500):
                        continue
                    raw_url = (link_el.get_attribute("href") or "").split("?")[0].strip()
                    if not raw_url.startswith("http"):
                        raw_url = f"https://www.linkedin.com{raw_url}"
                    if raw_url in seen_urls:
                        continue

                    name_el = card.locator(".mn-connection-card__name, span.mn-connection-card__name").first
                    full_name = clean_bmp(name_el.inner_text().strip() if name_el.is_visible(timeout=500) else link_el.inner_text().strip().split("\n")[0])
                    headline_el = card.locator(".mn-connection-card__occupation").first
                    headline = clean_bmp(headline_el.inner_text().strip() if headline_el.is_visible(timeout=500) else "")

                    parts = full_name.split()
                    first_name = parts[0] if parts else ""
                    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

                    title = headline
                    company = ""
                    for sep in [" at ", " @ ", " | "]:
                        if sep in headline:
                            title, company = headline.split(sep, 1)
                            break

                    scraped.append({
                        "Full Name": full_name,
                        "First Name": first_name,
                        "Last Name": last_name,
                        "Headline": headline,
                        "Title": title.strip(),
                        "Company": company.strip(),
                        "Location": "",
                        "LinkedIn URL": raw_url,
                        "Status": "RETRIEVED",
                    })
                    seen_urls.add(raw_url)
                except Exception:
                    continue
        else:
            # Modern LinkedIn DOM: Parse all connection profile links in the main viewport
            profile_links = page.locator("main a[href*='/in/']")
            for i in range(profile_links.count()):
                if len(scraped) >= max_count:
                    break
                try:
                    link_el = profile_links.nth(i)
                    raw_href = (link_el.get_attribute("href") or "").split("?")[0].strip()
                    if not raw_href or ("linkedin.com/in/" not in raw_href and not raw_href.startswith("/in/")):
                        continue
                    if not raw_href.startswith("http"):
                        raw_href = f"https://www.linkedin.com{raw_href}"
                    if raw_href in seen_urls:
                        continue

                    raw_txt = clean_bmp(link_el.inner_text().strip())
                    if not raw_txt:
                        continue

                    lines = [l.strip() for l in raw_txt.split("\n") if l.strip()]
                    if not lines:
                        continue

                    full_name = lines[0]
                    headline = " ".join(lines[1:]) if len(lines) > 1 else ""

                    parts = full_name.split()
                    first_name = parts[0] if parts else ""
                    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

                    title = headline
                    company = ""
                    for sep in [" at ", " @ ", " | "]:
                        if sep in headline:
                            title, company = headline.split(sep, 1)
                            break

                    scraped.append({
                        "Full Name": full_name,
                        "First Name": first_name,
                        "Last Name": last_name,
                        "Headline": headline,
                        "Title": title.strip(),
                        "Company": company.strip(),
                        "Location": "",
                        "LinkedIn URL": raw_href,
                        "Status": "RETRIEVED",
                    })
                    seen_urls.add(raw_href)
                except Exception:
                    continue

        log(f"Connections scraped so far: {len(scraped)} / {max_count}")
        if len(scraped) >= max_count:
            break

        # Scroll the main container to trigger lazy loading of the next batch of connection cards
        page.evaluate("""() => {
            const m = document.querySelector('main');
            if (m) {
                m.scrollTop = m.scrollHeight;
            } else {
                window.scrollBy(0, 1200);
            }
        }""")
        engine.human_delay(1.5, 2.5)
        scroll_attempts += 1

    log(f"Scraping complete. Retrieved {len(scraped)} 1st-degree connections.")
    return scraped

def extract_top_card_location(page: Page) -> str:
    """Extracts location string from top card of currently open profile."""
    try:
        loc = page.evaluate("""() => {
            const ci = document.querySelector("a[href*='contact-info']");
            if (ci && ci.parentElement) {
                const parentText = ci.parentElement.innerText || '';
                const parts = parentText.split('\\n').map(p => p.trim()).filter(Boolean);
                for (const part of parts) {
                    if (part.includes(',') && !part.includes('Contact info') && !part.includes('connections') && !part.includes('followers')) {
                        return part;
                    }
                }
            }
            return "";
        }""")
        if loc:
            return loc.strip()

        loc_el = page.locator("main section .text-body-small.inline.t-black--light.break-words").first
        if loc_el.is_visible(timeout=800):
            return loc_el.inner_text().strip()

        alt_loc = page.locator("main section span[class*='location'], .top-card__subline-item").first
        if alt_loc.is_visible(timeout=800):
            return alt_loc.inner_text().strip()
    except Exception:
        pass
    return ""

def inspect_connection_location(
    page: Page,
    engine: BrowserEngine,
    profile_url: str,
) -> str:
    """
    Visits a connection profile and extracts their location from the top-card.
    """
    try:
        page.goto(profile_url, wait_until="domcontentloaded", timeout=25000)
        engine.human_delay(1.5, 3)
        return extract_top_card_location(page)
    except Exception as e:
        logger.debug(f"Failed to inspect location for {profile_url}: {e}")
        return ""

def extract_profile_about(page: Page) -> str:
    """
    Extracts the 'About' section from the LinkedIn profile DOM, expanding 'see more' if truncated.
    """
    try:
        # Scroll down slightly to trigger lazy-loaded sections render
        page.evaluate("window.scrollBy(0, 450)")
        time.sleep(0.8)

        sections = page.locator("main section")
        for i in range(sections.count()):
            sec = sections.nth(i)
            # Check if this section header or first line is About
            header_loc = sec.locator("h2, .pv-profile-section__card-heading").first
            header_text = header_loc.inner_text().strip().lower() if header_loc.count() > 0 else ""
            lines = [l.strip() for l in sec.inner_text().split("\n") if l.strip()]
            first_line = lines[0].lower() if lines else ""

            if "about" in header_text or first_line == "about":
                # Expand see more if button present
                see_more = sec.locator(
                    "button.inline-show-more-text__button, button:has-text('see more'), button:has-text('...more')"
                ).first
                if see_more.is_visible(timeout=800):
                    try:
                        see_more.click()
                        time.sleep(0.4)
                    except Exception:
                        pass

                full_text = sec.inner_text().strip()
                if full_text.lower().startswith("about"):
                    body = full_text[5:].strip()
                else:
                    body = full_text

                for trail in ["...see more", "...less", "see less", "see more"]:
                    if body.lower().endswith(trail):
                        body = body[:-len(trail)].strip()

                clean_body = " ".join(body.split())
                return clean_body[:1200]
    except Exception as e:
        logger.debug(f"Failed to extract About section: {e}")
    return ""

def close_chat_overlay(page: Page):
    """Cleanly closes conversation overlay if open to avoid stacking windows."""
    close_selectors = [
        "button[data-control-name='overlay.close_conversation_window']",
        "button.msg-overlay-bubble-header__control--close",
        "button[aria-label*='Close your conversation']",
        "button[aria-label*='Close conversation']",
        "button.msg-overlay-bubble-header__control:has(svg[data-test-icon='close-small'])",
    ]
    for sel in close_selectors:
        close_btn = page.locator(sel).first
        if close_btn.is_visible(timeout=1000):
            try:
                close_btn.click()
                time.sleep(0.5)
                break
            except Exception:
                pass

def send_connection_dm(
    page: Page,
    engine: BrowserEngine,
    contact: Dict[str, Any],
    message_text: str = "",
    dry_run: bool = False,
    opener_generator: Optional[Any] = None,
    on_sent_callback: Optional[Any] = None,
) -> Tuple[str, str]:
    """
    Navigates to an existing 1st-degree connection profile, extracts About section context,
    checks existing chat thread history to prevent duplicate sends, and sends direct message.
    Immediately commits to persistent outreach memory so abrupt terminations never re-message.
    """
    url = contact.get("LinkedIn URL", "").strip()
    name = contact.get("Full Name", "Contact")
    if not url:
        return "ERROR", "Missing LinkedIn URL"

    # Step 0: Check persistent outreach memory first
    already_sent, prior_status = outreach_memory.is_already_contacted(url)
    if already_sent:
        logger.info(f"[OUTREACH MEMORY] Skipping {name} - already recorded as {prior_status}.")
        return "ALREADY_SENT", f"Contact already recorded in outreach memory ({prior_status})"

    try:
        logger.info(f"Visiting connection profile: {name} ({url})")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
        except Exception as nav_err:
            logger.warning(f"Initial navigation to {url} timed out: {nav_err}. Retrying with commit wait...")
            try:
                page.goto(url, wait_until="commit", timeout=20000)
            except Exception as nav_err2:
                logger.error(f"Failed to navigate to {name} ({url}): {nav_err2}")
                return "ERROR", f"Navigation to profile timed out: {nav_err2}"
        engine.human_delay(2, 3)

        # 1. Read the About section to get deep profile context
        about_text = extract_profile_about(page)
        if about_text:
            contact["About"] = about_text
            logger.info(f"[PROFILE CONTEXT] Read About section for {name} ({len(about_text)} chars)")
        else:
            logger.info(f"[PROFILE CONTEXT] No About section found for {name}.")

        # Check if candidate is academic or student based on full profile + About context
        is_acad, acad_reason = is_academic_or_student(contact)
        if is_acad:
            logger.info(f"[EXCLUDED ACADEMIA] {name} is excluded: {acad_reason}")
            outreach_memory.record_thread_detected(url, name, f"Academia excluded: {acad_reason}", status="EXCLUDED_ACADEMIA")
            if on_sent_callback:
                on_sent_callback(contact, "EXCLUDED_ACADEMIA", acad_reason)
            return "EXCLUDED_ACADEMIA", f"Candidate excluded due to academic/student role: {acad_reason}"

        # Check / extract location if blank and verify regional eligibility
        loc = contact.get("Location", "").strip()
        if not loc:
            loc = extract_top_card_location(page)
            if loc:
                contact["Location"] = loc
                is_eligible, tier_label, norm_reg = classify_location(loc)
                contact["Region Tier"] = tier_label
                if norm_reg in ["india", "africa"]:
                    logger.info(f"[REGION EXCLUDED] {name} is located in {loc}. Skipping.")
                    outreach_memory.record_thread_detected(url, name, f"Region excluded: {loc}", status="REGION_EXCLUDED")
                    if on_sent_callback:
                        on_sent_callback(contact, "REGION_EXCLUDED", f"Region excluded: {loc}")
                    return "REGION_EXCLUDED", f"Candidate excluded due to region: {loc}"

        # 2. Click Message button on top card
        msg_btn = page.locator("main section button:has-text('Message'), main section a:has-text('Message')").first
        if not msg_btn.is_visible(timeout=3000):
            # Fallback to secondary actions
            more_btn = page.locator("main section button:has-text('More')").first
            if more_btn.is_visible(timeout=1500):
                more_btn.click()
                time.sleep(1)
                msg_btn = page.locator("div[role='menu'] div:has-text('Message')").first

        if not msg_btn.is_visible(timeout=2000):
            # Multimodal Visual Browser Control fallback via Nemotron VL
            logger.info("DOM Message button not visible. Trying multimodal visual element location...")
            clicked = engine.visual_locate_and_click(page, "Message button on profile")
            if not clicked:
                return "ERROR", "Message button not visible (Not a 1st-degree connection or blocked)"

        if msg_btn.is_visible(timeout=1000):
            msg_btn.click()
        engine.human_delay(2, 3)

        # 3. Check chat overlay presence
        chat_box = page.locator(
            "div[role='textbox'][aria-label*='Write a message'], "
            "div.msg-form__contenteditable, "
            "div[contenteditable='true'][role='textbox'], "
            "div.msg-overlay-conversation-bubble div[contenteditable='true']"
        ).first

        if not chat_box.is_visible(timeout=3000):
            if msg_btn.is_visible(timeout=1000):
                msg_btn.click()
                time.sleep(2)

        if not chat_box.is_visible(timeout=3000):
            if dry_run:
                logger.info(f"[DRY RUN] Would send to {name}:\n{message_text}")
                return "MSG_SENT", "[DRY RUN] Simulated message (overlay not opened in dry-run)"
            return "ERROR", "Message textarea overlay did not open"

        # 4. CRITICAL SAFEGUARD: Live thread history inspection
        # If there are ANY message bubbles in the thread, NEVER send an opener again!
        time.sleep(0.5)
        msg_items = page.locator(
            ".msg-s-message-list-item, .msg-s-event-listitem, .msg-s-message-group, .msg-s-event-listitem__message-bubble"
        )
        if msg_items.count() > 0:
            first_name = contact.get("First Name", "").lower()
            sender_elements = page.locator(".msg-s-message-group__name, .msg-s-event-listitem__profile-name")
            prospect_replied = False
            for i in range(sender_elements.count()):
                sender_text = sender_elements.nth(i).inner_text().strip().lower()
                if first_name and first_name in sender_text:
                    prospect_replied = True
                    break

            close_chat_overlay(page)
            if prospect_replied:
                outreach_memory.record_thread_detected(url, name, "Prospect reply detected in chat thread", status="REPLIED")
                if on_sent_callback:
                    on_sent_callback(contact, "REPLIED", "Prospect reply detected in chat thread")
                return "REPLIED", f"Prospect {name} has already replied in chat thread. Sequence halted."
            else:
                outreach_memory.record_thread_detected(url, name, "Existing message history in chat thread", status="MSG_SENT")
                if on_sent_callback:
                    on_sent_callback(contact, "MSG_SENT", "Existing message history detected in thread")
                return "ALREADY_SENT", f"Active message thread already exists on LinkedIn for {name}. Halting to prevent duplicate send."

        # 5. Generate message if generator provided (now enriched with About context)
        if not message_text and opener_generator:
            message_text = opener_generator(contact)

        if dry_run:
            logger.info(f"[DRY RUN] Would send to {name} (Enriched with About context):\n{message_text}")
            close_chat_overlay(page)
            return "MSG_SENT", "[DRY RUN] Simulated connection message delivery"

        # 6. Focus chat box safely without viewport scroll error
        try:
            chat_box.focus(timeout=2000)
        except Exception:
            try:
                chat_box.click(force=True, timeout=1500)
            except Exception:
                page.evaluate("() => { const el = document.querySelector('div.msg-form__contenteditable'); if(el) el.focus(); }")

        time.sleep(0.3)
        engine.type_like_human(page, chat_box, message_text)
        engine.human_delay(1, 2)

        # 7. Click Send
        send_selectors = [
            "button.msg-form__send-button",
            "button.msg-form__send-btn",
            "form.msg-form button[type='submit']",
            "button[type='submit']:has-text('Send')",
            "footer button:has-text('Send')",
        ]
        sent_clicked = False
        for sel in send_selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=1000) and not btn.is_disabled():
                    try:
                        btn.click(force=True, timeout=2500)
                        sent_clicked = True
                        break
                    except Exception:
                        btn.evaluate("b => b.click()")
                        sent_clicked = True
                        break
            except Exception:
                continue

        if not sent_clicked:
            # Fallback: ensure input event is dispatched to enable Send button, then click
            page.evaluate("""() => {
                const box = document.querySelector('div.msg-form__contenteditable');
                if (box) {
                    box.dispatchEvent(new Event('input', { bubbles: true }));
                    box.dispatchEvent(new Event('change', { bubbles: true }));
                }
                const btn = document.querySelector('button.msg-form__send-button, form.msg-form button[type="submit"]');
                if (btn) {
                    btn.removeAttribute('disabled');
                    btn.click();
                }
            }""")
            time.sleep(1)

        # Verify delivery: check if message input cleared
        time.sleep(1.5)
        box_has_text = page.evaluate("""() => {
            const el = document.querySelector('div.msg-form__contenteditable');
            return el && el.innerText && el.innerText.trim().length > 0;
        }""")
        if box_has_text:
            # If text is still present, force click send button or submit form
            page.evaluate("""() => {
                const btn = document.querySelector('button.msg-form__send-button');
                if (btn) {
                    btn.removeAttribute('disabled');
                    btn.click();
                } else {
                    const form = document.querySelector('form.msg-form');
                    if (form) form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
                }
            }""")
            time.sleep(2)

        # 8. IMMEDIATE COMMIT TO PERSISTENT MEMORY
        outreach_memory.record_sent(url, name, "opener", message_text, status="MSG_SENT")
        if on_sent_callback:
            on_sent_callback(contact, "MSG_SENT", message_text)

        engine.human_delay(2, 3)
        close_chat_overlay(page)

        logger.info(f"[SUCCESS] Message delivered to connection {name}.")
        return "MSG_SENT", "Message sent successfully to 1st-degree connection"
    finally:
        # Crucial hygiene requirement: purge all screenshot files after every message attempt
        engine.cleanup_screenshots()

def check_connection_reply(
    page: Page,
    engine: BrowserEngine,
    contact: Dict[str, Any],
) -> bool:
    """
    Visits profile, opens chat, and verifies if the prospect has replied.
    """
    url = contact.get("LinkedIn URL", "").strip()
    first_name = contact.get("First Name", "").lower()
    if not url:
        return False

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        engine.human_delay(1.5, 3)

        msg_btn = page.locator("main section button:has-text('Message')").first
        if not msg_btn.is_visible(timeout=3000):
            return False

        msg_btn.click()
        engine.human_delay(2, 3)

        sender_elements = page.locator(".msg-s-message-group__name, .msg-s-event-listitem__profile-name")
        for i in range(sender_elements.count()):
            sender_text = sender_elements.nth(i).inner_text().strip().lower()
            if first_name and first_name in sender_text:
                close_chat_overlay(page)
                return True

        close_chat_overlay(page)
        return False
    finally:
        engine.cleanup_screenshots()
