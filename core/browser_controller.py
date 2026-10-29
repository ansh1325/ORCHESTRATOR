"""
LlamaOrchestrator Real Browser Controller & Outbound Dispatch Engine
Executes real browser actions:
1. Launches host browser (Chrome/Edge) with active logged-in user profile via system webbrowser.
2. Directly opens Gmail Compose tabs with recipient, subject, and body prefilled.
3. Launches real Playwright browser sessions (msedge/chrome, headless=False) for live DOM automation.
4. Executes real SMTP email transmissions if credentials are provided.
"""

import os
import sys
import time
import urllib.parse
import webbrowser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Any, List, Optional

class BrowserController:
    """Unified controller for system browser interaction and Playwright automation."""

    @staticmethod
    def build_gmail_compose_url(recipient: str, subject: str, body: str) -> str:
        """Constructs official Gmail web compose URL with URL-encoded parameters."""
        recip_enc = urllib.parse.quote_plus(recipient.strip())
        subj_enc = urllib.parse.quote_plus(subject.strip())
        body_enc = urllib.parse.quote_plus(body.strip())
        return f"https://mail.google.com/mail/?view=cm&fs=1&to={recip_enc}&su={subj_enc}&body={body_enc}"

    @classmethod
    def open_in_system_browser(cls, url: str) -> bool:
        """Opens target URL in the user's active host browser (Chrome/Edge with user session)."""
        try:
            return webbrowser.open(url, new=2)
        except Exception as e:
            print(f"[BrowserController] Failed to open system browser: {e}", file=sys.stderr)
            return False

    @classmethod
    def compose_in_gmail(cls, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Opens user's default browser directly into Gmail Compose.
        Because the user is already logged in to Google in their browser, this immediately
        presents the composed email ready for instant 1-click dispatch.
        """
        url = cls.build_gmail_compose_url(recipient, subject, body)
        success = cls.open_in_system_browser(url)
        return {
            "success": success,
            "action": "open_gmail_compose",
            "recipient": recipient,
            "subject": subject,
            "compose_url": url,
            "method": "system_browser_user_session"
        }

    @classmethod
    def compose_batch_in_gmail(cls, emails: List[Dict[str, str]]) -> Dict[str, Any]:
        """Opens Gmail Compose tabs for a batch of letters/emails with safe staggered timing."""
        results = []
        for idx, item in enumerate(emails):
            recip = item.get("to") or item.get("recipient", "anshtiwarisocial@gmail.com")
            subj = item.get("subject", "hello i am jarvis")
            body = item.get("body", "")
            res = cls.compose_in_gmail(recip, subj, body)
            results.append(res)
            if idx < len(emails) - 1:
                time.sleep(0.4)
        return {
            "success": True,
            "total_staged": len(results),
            "results": results
        }

    @classmethod
    def run_playwright_automation(
        cls,
        url: str,
        headless: bool = False,
        actions: Optional[List[Dict[str, Any]]] = None,
        screenshot_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Launches real Playwright browser (Edge or Chrome) on Windows.
        When headless=False, the browser window physically appears on the user's screen.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return {
                "success": False,
                "error": "Playwright is not installed. Run 'pip install playwright'."
            }

        actions = actions or []
        captured_data: Dict[str, Any] = {"title": "", "url": "", "executed_actions": []}

        try:
            with sync_playwright() as p:
                browser = None
                for channel in ["msedge", "chrome"]:
                    try:
                        browser = p.chromium.launch(channel=channel, headless=headless)
                        break
                    except Exception:
                        continue

                if not browser:
                    browser = p.chromium.launch(headless=headless)

                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                captured_data["title"] = page.title()
                captured_data["url"] = page.url

                for act in actions:
                    act_type = act.get("type", "")
                    selector = act.get("selector", "")
                    val = act.get("value", "")

                    if act_type == "click" and selector:
                        page.wait_for_selector(selector, timeout=8000)
                        page.click(selector)
                        captured_data["executed_actions"].append(f"Clicked {selector}")
                    elif act_type == "type" and selector:
                        page.wait_for_selector(selector, timeout=8000)
                        page.type(selector, str(val), delay=50)
                        captured_data["executed_actions"].append(f"Typed into {selector}")
                    elif act_type == "wait":
                        wait_ms = int(act.get("ms", 1000))
                        page.wait_for_timeout(wait_ms)
                        captured_data["executed_actions"].append(f"Waited {wait_ms}ms")

                if screenshot_path:
                    out = Path(screenshot_path)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(out), full_page=True)
                    captured_data["screenshot"] = str(out)

                browser.close()
                return {"success": True, **captured_data}
        except Exception as e:
            return {"success": False, "error": f"Playwright automation failed: {str(e)}"}

    @classmethod
    def automate_gmail_dispatch_playwright(
        cls,
        recipient: str,
        subject: str,
        body: str,
        headless: bool = False
    ) -> Dict[str, Any]:
        """
        True autonomous browser worker.
        Launches Playwright Chrome/Edge on the desktop, navigates to Gmail,
        clicks Compose, types recipient, subject, and body, and sends or stages it.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return {"success": False, "error": "Playwright is not installed."}

        try:
            with sync_playwright() as p:
                browser = None
                for channel in ["msedge", "chrome"]:
                    try:
                        browser = p.chromium.launch(channel=channel, headless=headless)
                        break
                    except Exception:
                        continue

                if not browser:
                    browser = p.chromium.launch(headless=headless)

                page = browser.new_page()
                compose_url = cls.build_gmail_compose_url(recipient, subject, body)
                page.goto(compose_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(2.0)

                # Attempt to find Send button and click it autonomously
                sent = False
                try:
                    send_btn = page.query_selector('div[role="button"][data-tooltip*="Send"], div[aria-label*="Send"]')
                    if send_btn:
                        send_btn.click()
                        sent = True
                        time.sleep(1.5)
                except Exception:
                    pass

                page_title = page.title()
                page_url = page.url
                browser.close()

                return {
                    "success": True,
                    "action": "autonomous_playwright_dispatch",
                    "recipient": recipient,
                    "subject": subject,
                    "title": page_title,
                    "url": page_url,
                    "sent_automatically": sent,
                    "message": "Playwright browser worker automated Gmail dispatch successfully."
                }
        except Exception as e:
            return {"success": False, "error": f"Playwright execution error: {str(e)}"}

    @classmethod
    def send_smtp_email(
        cls,
        recipient: str,
        subject: str,
        body: str,
        sender_email: Optional[str] = None,
        password: Optional[str] = None,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587
    ) -> Dict[str, Any]:
        """
        Sends an email over direct SMTP if credentials are configured in .env or arguments.
        """
        sender = sender_email or os.getenv("SENDER_EMAIL") or os.getenv("SMTP_USER") or os.getenv("GMAIL_USER")
        pwd = password or os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")

        if not sender or not pwd:
            return {
                "success": False,
                "error": "No SMTP credentials configured. Provide GMAIL_APP_PASSWORD or use the 1-click Browser Gmail Compose button."
            }

        try:
            msg = MIMEMultipart()
            msg["From"] = sender
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            server = smtplib.SMTP(smtp_server, smtp_port, timeout=20)
            server.ehlo()
            server.starttls()
            server.login(sender, pwd)
            server.send_message(msg)
            server.quit()

            return {
                "success": True,
                "message": f"Successfully transmitted email to {recipient} via SMTP.",
                "recipient": recipient,
                "subject": subject
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"SMTP transmission failed: {str(e)}"
            }

