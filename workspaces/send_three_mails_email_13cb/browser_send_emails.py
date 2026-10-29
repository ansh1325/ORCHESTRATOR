"""
Automated Browser Session Dispatcher for Jarvis Outbound Communication
Opens real host browser (Chrome/Edge) with user active Gmail session and pre-fills letters.
"""

import os
import sys
import time
import json
import webbrowser
import urllib.parse
from typing import List, Dict, Any

class BrowserEmailDispatcher:
    def __init__(self, recipient: str = "anshtiwarif17@gmail.com"):
        self.recipient = recipient
        self.dispatched_letters: List[Dict[str, Any]] = []

    def read_letter_body(self, filename: str) -> str:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        return "Hello Master Ansh, this is Jarvis."

    def open_gmail_compose(self, subject: str, body: str) -> str:
        recip_enc = urllib.parse.quote_plus(self.recipient)
        subj_enc = urllib.parse.quote_plus(subject)
        body_enc = urllib.parse.quote_plus(body)
        url = f"https://mail.google.com/mail/?view=cm&fs=1&to={recip_enc}&su={subj_enc}&body={body_enc}"
        webbrowser.open(url, new=2)
        return url

    def execute_browser_dispatch(self) -> Dict[str, Any]:
        letters = ["mail_1.md", "mail_2.md", "mail_3.md"]
        opened_urls = []
        for l in letters:
            body = self.read_letter_body(l)
            url = self.open_gmail_compose("hello i am jarvis", body)
            opened_urls.append(url)
            self.dispatched_letters.append({
                "recipient": self.recipient,
                "subject": "hello i am jarvis",
                "letter_file": l,
                "status": "Opened in Host Browser (Gmail Compose Ready to Send)",
                "timestamp": time.time()
            })
            time.sleep(0.5)
        return {
            "success": True,
            "dispatched_count": len(self.dispatched_letters),
            "recipient": self.recipient,
            "subject": "hello i am jarvis",
            "opened_urls": opened_urls
        }

if __name__ == "__main__":
    dispatcher = BrowserEmailDispatcher()
    result = dispatcher.execute_browser_dispatch()
    print("Browser Dispatch Result:", json.dumps(result, indent=2))
