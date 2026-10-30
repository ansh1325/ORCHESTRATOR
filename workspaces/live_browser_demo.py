"""
Live Desktop Browser Action Demonstration for Ansh Tiwari.
Opens a visible browser window on your screen and performs interactive actions:
1. Launches visible Chrome / Edge browser on desktop
2. Navigates to Wikipedia
3. Types search query 'Artificial General Intelligence' with human-like keystroke delays
4. Submits search and navigates to the article
5. Smoothly scrolls down the page
6. Opens a second tab to Hacker News (news.ycombinator.com)
7. Scrolls through the top technology news
8. Switches back to the Wikipedia tab
9. Takes a screenshot proof and closes gracefully
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_live_demo():
    screenshot_dir = Path("workspaces/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    shot_path = screenshot_dir / "live_browser_demo.png"

    print("\n" + "="*60)
    print("  JARVIS // LIVE AUTONOMOUS BROWSER ACTION DEMO")
    print("="*60)
    print("Launching visible browser on your desktop monitor...")

    launch_args = [
        "--disable-blink-features=AutomationControlled",
        "--start-maximized"
    ]

    with sync_playwright() as p:
        browser = None
        for channel in ["msedge", "chrome"]:
            try:
                browser = p.chromium.launch(
                    channel=channel,
                    headless=False,
                    args=launch_args
                )
                print(f"✓ Successfully launched {channel.upper()} in visible mode.")
                break
            except Exception:
                continue

        if not browser:
            browser = p.chromium.launch(headless=False, args=launch_args)
            print("✓ Launched default Chromium in visible mode.")

        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Step 1: Navigate to Wikipedia
        print("\n[Action 1] Navigating to Wikipedia (https://www.wikipedia.org)...")
        page.goto("https://www.wikipedia.org", wait_until="domcontentloaded", timeout=30000)
        time.sleep(1.5)

        # Step 2: Locate search box and type with human-like delays
        search_query = "Artificial General Intelligence"
        print(f"[Action 2] Typing '{search_query}' into search field with human delays...")
        search_input = page.locator("#searchInput, input[name='search']").first
        search_input.click()
        for char in search_query:
            search_input.type(char, delay=45)

        time.sleep(1.0)

        # Step 3: Press Enter to submit search
        print("[Action 3] Submitting search and loading article...")
        page.keyboard.press("Enter")
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2.0)
        print(f"  • Landed on: {page.title()} ({page.url})")

        # Step 4: Smoothly scroll down the Wikipedia article
        print("[Action 4] Smooth scrolling down article to inspect headings...")
        for _ in range(4):
            page.mouse.wheel(0, 350)
            time.sleep(0.6)

        # Step 5: Open a second tab to Hacker News
        print("\n[Action 5] Opening a second tab to Hacker News (https://news.ycombinator.com)...")
        tab2 = context.new_page()
        tab2.goto("https://news.ycombinator.com", wait_until="domcontentloaded", timeout=30000)
        time.sleep(1.5)
        print(f"  • Tab 2 Title: {tab2.title()}")

        # Step 6: Scroll through top tech discussions on tab 2
        print("[Action 6] Scrolling through top technology discussions...")
        tab2.mouse.wheel(0, 400)
        time.sleep(1.2)

        # Step 7: Switch back to the original Wikipedia tab
        print("\n[Action 7] Switching active view back to Tab 1 (Wikipedia)...")
        page.bring_to_front()
        time.sleep(1.5)

        # Step 8: Capture visual proof screenshot
        print("[Action 8] Capturing full screenshot proof...")
        page.screenshot(path=str(shot_path))
        print(f"✓ Screenshot saved to: {shot_path}")

        print("\n[Complete] Keeping browser open for 4 seconds so you can view it...")
        time.sleep(4.0)

        browser.close()
        print("✓ Live browser demo completed successfully!\n")

if __name__ == "__main__":
    run_live_demo()
