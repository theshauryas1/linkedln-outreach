import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(r"c:\New folder (2)")))
from linkedin_outreach.browser_engine import BrowserEngine

def main():
    engine = BrowserEngine(headless=False)
    try:
        ctx, page = engine.start()
        page.goto("https://www.linkedin.com/mynetwork/invite-connect/connections/", wait_until="domcontentloaded")
        time.sleep(3)
        
        for s in range(5):
            res = page.evaluate("""() => {
                const m = document.querySelector('main');
                if (m) {
                    m.scrollTop = m.scrollHeight;
                    return { scrollTop: m.scrollTop, scrollHeight: m.scrollHeight, links: m.querySelectorAll("a[href*='/in/']").length };
                }
                return null;
            }""")
            print(f"Scroll {s+1}:", res)
            time.sleep(2)
            
    finally:
        engine.close()

if __name__ == "__main__":
    main()
