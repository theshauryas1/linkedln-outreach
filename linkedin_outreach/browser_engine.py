import asyncio
import os
import random
import time
import urllib.request
import json
import base64
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from playwright.sync_api import sync_playwright, BrowserContext, Page, Playwright

from .config import config

logger = logging.getLogger("outreach.browser")

class BrowserEngine:
    """
    Manages Chrome connection for LinkedIn automation.
    Supports:
    1. CDP connection (remote debugging on port 18800 or 9222)
    2. Real Google Chrome Persistent Context (preserves LinkedIn session cookies)
    3. Multimodal Visual Browser Control via NVIDIA Nemotron 3.5 Super VL
    """

    def __init__(self, headless: Optional[bool] = None, user_data_dir: Optional[Path] = None):
        self.headless = headless if headless is not None else config.headless
        self.user_data_dir = user_data_dir or config.user_data_dir
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_cdp: bool = False

    def _check_cdp_port(self, port: int) -> bool:
        """Checks if a Chrome DevTools Protocol endpoint is active on port."""
        try:
            url = f"http://127.0.0.1:{port}/json/version"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode())
                return "webSocketDebuggerUrl" in data or "Browser" in data
        except Exception:
            return False

    def _ensure_visible_chrome(self) -> bool:
        """Launches visible system Chrome with remote debugging on port 18800 if not already running."""
        for port in config.cdp_ports:
            if self._check_cdp_port(port):
                return True

        chrome_candidates = [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ]
        chrome_exe = next((p for p in chrome_candidates if p.exists()), None)
        if not chrome_exe:
            return False

        # Clear stale locks
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        for lock_name in ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket"]:
            lock_path = self.user_data_dir / lock_name
            if lock_path.exists():
                try:
                    lock_path.unlink(missing_ok=True)
                except Exception:
                    pass

        cmd = [
            str(chrome_exe),
            "--remote-debugging-port=18800",
            f"--user-data-dir={self.user_data_dir}",
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
            "https://www.linkedin.com/feed/"
        ]
        try:
            import subprocess
            subprocess.Popen(cmd)
            for _ in range(10):
                time.sleep(0.5)
                if self._check_cdp_port(18800):
                    logger.info("Auto-spawned visible Chrome with CDP on port 18800")
                    return True
        except Exception as e:
            logger.warning(f"Could not auto-spawn visible Chrome: {e}")
        return False

    def start(self) -> Tuple[BrowserContext, Page]:
        """Starts or attaches to Chrome browser session."""
        self.playwright = sync_playwright().start()

        # Ensure visible Chrome is active if not headless
        if not self.headless:
            self._ensure_visible_chrome()

        # 1. Check if Chrome is running with CDP on configured ports
        for port in config.cdp_ports:
            if self._check_cdp_port(port):
                try:
                    cdp_url = f"http://127.0.0.1:{port}"
                    browser = self.playwright.chromium.connect_over_cdp(cdp_url)
                    self.is_cdp = True
                    self.context = browser.contexts[0] if browser.contexts else browser.new_context()
                    pages = self.context.pages
                    self.page = pages[0] if pages else self.context.new_page()
                    logger.info(f"Connected over CDP on port {port} (Visible Chrome)")
                    return self.context, self.page
                except Exception as e:
                    logger.warning(f"CDP connection attempt failed on port {port}: {e}")

        # 2. Fallback: Launch real Chrome using persistent profile directory
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        # Clear stale lock files if any previous process crashed
        for lock_name in ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket"]:
            lock_path = self.user_data_dir / lock_name
            if lock_path.exists():
                try:
                    lock_path.unlink(missing_ok=True)
                except Exception:
                    pass

        chrome_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-infobars",
            "--start-maximized",
            "--test-type",
        ]

        # Use system Chrome if available, otherwise bundled chromium
        try:
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                channel="chrome",
                headless=self.headless,
                args=chrome_args,
                chromium_sandbox=True,
                ignore_default_args=["--no-sandbox"],
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            )
        except Exception:
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=self.headless,
                args=chrome_args,
                chromium_sandbox=True,
                ignore_default_args=["--no-sandbox"],
                viewport={"width": 1280, "height": 800},
            )

        pages = self.context.pages
        self.page = pages[0] if pages else self.context.new_page()
        return self.context, self.page

    def check_logged_in(self, page: Optional[Page] = None) -> bool:
        """Verifies if the current session is logged into LinkedIn."""
        p = page or self.page
        if not p:
            return False

        try:
            p.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=20000)
            self.human_delay(2, 4)

            # Check indicators of logged-in state
            current_url = p.url.lower()
            if "login" in current_url or "checkpoint" in current_url or "authwall" in current_url:
                return False

            selectors = [
                "#global-nav",
                "nav.global-nav",
                "div.feed-identity-module",
                "div.share-box-feed-entry__wrapper",
                "img.global-nav__me-photo",
                "a[href*='/in/']",
            ]
            for sel in selectors:
                if p.locator(sel).first.is_visible(timeout=3000):
                    return True
            return False
        except Exception:
            return False

    def interactive_login(self) -> bool:
        """Opens LinkedIn login page and waits for user to sign in."""
        if not self.context or not self.page:
            self.start()

        p = self.page
        p.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        print("\n" + "=" * 65)
        print("  LINKEDIN LOGIN ASSISTANT")
        print("=" * 65)
        print("  1. Please log in to your LinkedIn account in the Chrome window.")
        print("  2. Complete any 2FA/SMS code if prompted.")
        print("  3. Your session cookies will be permanently saved automatically.")
        print("=" * 65)

        # Wait until user reaches feed / logged in
        start_time = time.time()
        while time.time() - start_time < 300:  # 5 minutes timeout
            try:
                time.sleep(3)
                current_url = p.url.lower()
                if "/feed" in current_url or "/in/" in current_url or "/messaging" in current_url:
                    if self.check_logged_in(p):
                        print("\n[SUCCESS] LinkedIn Login confirmed! Session saved.")
                        return True
            except Exception:
                pass

        print("\n[TIMEOUT] Login waiting timed out after 5 minutes.")
        return False

    def human_delay(self, min_s: Optional[float] = None, max_s: Optional[float] = None):
        """Simulates human pause with random variance."""
        min_v = min_s if min_s is not None else config.min_action_delay_secs
        max_v = max_s if max_s is not None else config.max_action_delay_secs
        duration = random.uniform(min_v, max_v)
        time.sleep(duration)

    def human_type(self, locator, text: str):
        """Types text with natural human cadence without timing out or crashing on contenteditable divs."""
        try:
            locator.focus(timeout=3000)
            time.sleep(0.3)
            # Natural keystroke cadence: 15-25ms per character finishes 400-char text in ~7 seconds
            delay_ms = random.randint(15, 25)
            typing_timeout = max(30000, len(text) * 80 + 10000)
            locator.press_sequentially(text, delay=delay_ms, timeout=typing_timeout)
        except Exception as e:
            logger.warning(f"Native sequential typing fallback triggered: {e}")
            try:
                locator.focus(timeout=2000)
                locator.evaluate("(el, val) => { el.focus(); document.execCommand('insertText', false, val); }", text)
            except Exception:
                try:
                    locator.fill(text, timeout=3000)
                except Exception:
                    pass

        try:
            locator.dispatch_event("input")
        except Exception:
            pass

    def type_like_human(self, page_or_locator, locator_or_text, text: Optional[str] = None):
        """
        Flexible human typing wrapper supporting:
        - engine.type_like_human(locator, text)
        - engine.type_like_human(page, locator, text)
        """
        if text is not None:
            target = locator_or_text
            msg = text
        else:
            target = page_or_locator
            msg = locator_or_text
        self.human_type(target, msg)

    def human_scroll(self, page: Optional[Page] = None, distance: int = 350):
        """Scrolls naturally down the page to simulate reading."""
        p = page or self.page
        if not p:
            return
        steps = random.randint(3, 6)
        step_dist = distance // steps
        for _ in range(steps):
            p.mouse.wheel(0, step_dist + random.randint(-15, 25))
            time.sleep(random.uniform(0.1, 0.25))

    def capture_in_memory_screenshot_b64(self, page: Optional[Page] = None) -> str:
        """
        Captures screenshot directly in RAM as base64 string.
        Zero bytes are written to disk, preventing storage pileup.
        """
        p = page or self.page
        if not p:
            return ""
        try:
            png_bytes = p.screenshot(type="png", full_page=False)
            return base64.b64encode(png_bytes).decode("utf-8")
        except Exception:
            return ""

    def cleanup_screenshots(self, directory: Optional[Path] = None):
        """
        Strict hygiene: scans for and immediately removes any lingering or temporary screenshot
        files (*.png, *.jpg, *.jpeg) so storage never piles up.
        """
        target_dirs = [
            directory,
            Path("."),
            self.user_data_dir,
            Path("data"),
            Path("logs"),
        ]
        patterns = ["*screenshot*", "*snap*", "temp_*.png", "*.png", "*.jpg"]
        for d in target_dirs:
            if not d or not Path(d).exists():
                continue
            p_dir = Path(d)
            for pat in patterns:
                try:
                    for f in p_dir.glob(pat):
                        if f.is_file() and not f.name.endswith(".gitkeep"):
                            name_lower = f.name.lower()
                            if any(k in name_lower for k in ["screen", "snap", "temp", "view", "crop", "page", "modal"]):
                                try:
                                    f.unlink(missing_ok=True)
                                except Exception:
                                    pass
                except Exception:
                    pass

    def visual_browser_inspect(self, page: Optional[Page] = None, task_prompt: str = "") -> Dict[str, Any]:
        """
        Uses nvidia/nemotron-3.5-super-vl-120b-a12b for multimodal screen inspection.
        Takes in-memory screenshot (zero disk footprint) and returns structured analysis.
        Automatically guarantees immediate cleanup.
        """
        p = page or self.page
        b64 = self.capture_in_memory_screenshot_b64(p)
        if not b64:
            return {"detected": False, "state": "no_page", "description": "Failed to capture in-memory screenshot"}
        from .ai_generator import nim_generator
        result = nim_generator.visual_browser_inspect(b64, task_prompt)
        self.cleanup_screenshots()
        return result

    def visual_locate_and_click(self, page: Optional[Page] = None, element_description: str = "") -> bool:
        """
        Visually locates element coordinates (x, y) via Nemotron VL and performs a real human mouse click.
        Zero disk footprint.
        """
        p = page or self.page
        if not p:
            return False
        b64 = self.capture_in_memory_screenshot_b64(p)
        if not b64:
            return False
        from .ai_generator import nim_generator
        coords = nim_generator.visual_locate_element(b64, element_description)
        self.cleanup_screenshots()
        if coords and "x" in coords and "y" in coords:
            p.mouse.move(coords["x"], coords["y"])
            time.sleep(0.3)
            p.mouse.click(coords["x"], coords["y"])
            return True
        return False

    def close(self):
        """Closes browser session and guarantees full screenshot purge."""
        self.cleanup_screenshots()
        try:
            if self.context and not self.is_cdp:
                self.context.close()
        except Exception:
            pass
        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
        self.cleanup_screenshots()
