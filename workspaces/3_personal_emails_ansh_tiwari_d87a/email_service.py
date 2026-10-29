import json
from pathlib import Path
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

CREDENTIALS_PATH = Path(__file__).parent / "credentials.json"


def _load_api_key() -> str:
    """Read the SendGrid API key from ``credentials.json``.

    The JSON file is expected to have a top‑level key ``sendgrid_api_key``.
    """
    try:
        with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            api_key = data.get("sendgrid_api_key")
            if not api_key:
                raise ValueError("'sendgrid_api_key' not found in credentials.json")
            return api_key
    except Exception as exc:
        raise RuntimeError(f"Unable to load SendGrid API key: {exc}")


def send_email(to: str, subject: str, body: str) -> None:
    """Send a single email via SendGrid.

    Parameters
    ----------
    to: str
        Recipient email address.
    subject: str
        Email subject line.
    body: str
        Plain‑text body of the email.
    """
    api_key = _load_api_key()
    message = Mail(
        from_email="no-reply@example.com",
        to_emails=to,
        subject=subject,
        plain_text_content=body,
    )
    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        if response.status_code >= 400:
            raise RuntimeError(f"SendGrid returned error {response.status_code}: {response.body}")
    except Exception as exc:
        raise RuntimeError(f"Failed to send email: {exc}")