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

        # Switch to Swarm Mode
        await page.click("#swarmModeBtn")
        print("[Step 2] Switched to Multi-Agent Swarm Builder mode.")

        # Directive
        directive = "Build an authenticated telemetry microservice with JWT auth and SQLite metrics storage"
        await page.fill("#directiveInput", directive)
        print(f"[Step 3] Submitting directive: '{directive}'")
        await page.click("#submitBtn")

        # Wait for Deploy button
        print("[Step 4] Waiting for Architecture Clarification Gate...")
        deploy_btn = await page.wait_for_selector("button:has-text('Deploy Autonomous Swarm')", timeout=15000)
        if not deploy_btn:
            print("ERROR: Deploy button not found!")
            sys.exit(1)
        
        print("[Step 4 Success] Clicking 'Deploy Autonomous Swarm'...")
        await deploy_btn.click()

        # Monitor execution loop
        print("[Step 5] Waiting for autonomous completion banner...")
        for sec in range(35):
            await asyncio.sleep(1)
            is_done = await page.is_visible("#workDoneBanner")
            if is_done:
                print(f"[Step 5 Success] Mission Certified in {sec+1} seconds!")
                break
        else:
            print("[Step 5 Notice] Reached 35s, checking deliverable status...")

        # Check deliverables list
        files_count = await page.inner_text("#deliverablesCountLabel")
        print(f"[Step 6] Deliverables label: {files_count.encode('ascii', 'replace').decode()}")

        # Capture visual proof
        await page.screenshot(path="workspaces/screenshots/live_ui_verification.png", full_page=True)
        print("[Step 7] Saved screenshot: workspaces/screenshots/live_ui_verification.png")

        await browser.close()
        print("[DONE] Autonomous UI Verification Finished.")

if __name__ == "__main__":
    asyncio.run(run_ui_verification())
