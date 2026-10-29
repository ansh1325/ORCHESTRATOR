"""
SMTP Transport Script for Direct Email Dispatch
Transmits outbound emails if SMTP credentials are provided in .env
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_emails_smtp(recipient: str = "anshtiwarisocial@gmail.com"):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    sender_email = os.getenv("SENDER_EMAIL") or os.getenv("GMAIL_USER")
    password = os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")

    if not sender_email or not password:
        print("[SMTP Relay] Notice: SENDER_EMAIL or GMAIL_APP_PASSWORD not set in environment.")
        print("[SMTP Relay] Recommendation: Use 1-Click Browser Gmail Compose to transmit with your active browser session.")
        return False

    letters = ["mail_1.md", "mail_2.md", "mail_3.md"]
    for l in letters:
        body = "Hello from Jarvis."
        if os.path.exists(l):
            with open(l, "r", encoding="utf-8") as f:
                body = f.read()
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Subject"] = "hello i am jarvis"
        msg.attach(MIMEText(body, "plain", "utf-8"))
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
        print(f"[SMTP Relay] Sent {l} to {recipient}")
    return True

if __name__ == "__main__":
    send_emails_smtp()
