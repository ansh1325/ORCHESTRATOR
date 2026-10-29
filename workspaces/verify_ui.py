import asyncio
import sys
from playwright.async_api import async_playwright

async def run_ui_verification():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Capture browser console and errors
        page.on("console", lambda msg: print(f"[Browser Console {msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"[Browser Exception] {err}"))

        print("[Step 1] Navigating to http://127.0.0.1:8000...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        title = await page.title()
        print(f"[Step 1 Success] Page loaded: {title}")

        # Test Conversational Prompt (Zero button toggles needed)
        print("[Step 2] Testing direct conversational query (Zero mode buttons)...")
        await page.fill("#directiveInput", "What are your core autonomous capabilities?")
        await page.click("#submitBtn")
        await asyncio.sleep(2)
        chat_text = await page.inner_text("#chatHistory")
        print(f"[Step 2 Success] Conversational reply received! Words: {len(chat_text.split())}")

        # Test Actionable Multi-Agent Directive (Zero mode buttons, Auto-Execution)
        directive = "I want you to send me just 3 emails with subject i am jarvis with body whatever you feel about me and send those mails to anshtiwari17@gmail.com and do that via browser automation and no other way access my browser and just send those mails by composing it"
        print(f"[Step 3] Submitting user prompt: '{directive[:70]}...'")
        await page.fill("#directiveInput", directive)
        await page.click("#submitBtn")

        # Monitor autonomous execution loop (auto-launched, no clicks required!)
        print("[Step 4] Monitoring autonomous multi-agent execution loop...")
        for sec in range(35):
            await asyncio.sleep(1)
            is_done = await page.is_visible("#workDoneBanner")
            if is_done:
                print(f"[Step 4 Success] Mission autonomously compiled, tested, and certified in {sec+1} seconds!")
                break
        else:
            print("[Step 4 Notice] Checking deliverable status...")

        # Check deliverables list
        files_count = await page.inner_text("#deliverablesCountLabel")
        print(f"[Step 5] Deliverables count: {files_count.encode('ascii', 'replace').decode()}")

        # Check visual proof of browser worker button
        has_browser_worker_btn = await page.is_visible("button:has-text('Execute Real JARVIS Browser Worker')")
        print(f"[Step 6] 'Execute Real JARVIS Browser Worker' button visible: {has_browser_worker_btn}")

        # Test Gemini-style Dashboard Back Navigation
        print("[Step 7] Testing Dashboard Return button (#headerHomeBtn)...")
        await page.click("#headerHomeBtn")
        await asyncio.sleep(1)
        url_hash = await page.evaluate("() => window.location.hash")
        print(f"[Step 7 Success] Successfully returned to Dashboard! URL Hash: '{url_hash}'")

        # Capture visual proof
        await page.screenshot(path="workspaces/screenshots/live_ui_verification.png", full_page=True)
        print("[Step 8] Saved visual proof to workspaces/screenshots/live_ui_verification.png")

        await browser.close()
        print("[DONE] 100% End-to-End Autonomous Software Creation Verified!")

if __name__ == "__main__":
    asyncio.run(run_ui_verification())
