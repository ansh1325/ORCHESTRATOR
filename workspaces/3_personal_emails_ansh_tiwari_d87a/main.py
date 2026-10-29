import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from email_service import send_email
from mangum import Mangum

app = FastAPI()

CREDENTIALS_PATH = Path(__file__).parent / "credentials.json"
EMAIL_BODIES_PATH = Path(__file__).parent / "email_bodies.json"


def load_email_bodies():
    """Load a list of email bodies from ``email_bodies.json``.

    The JSON file must contain an array of strings.
    """
    try:
        with open(EMAIL_BODIES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("email_bodies.json must contain a JSON array of strings")
            return data
    except Exception as exc:
        raise RuntimeError(f"Failed to load email bodies: {exc}")


class CampaignRequest(BaseModel):
    to: EmailStr


@app.post("/send_campaign")
async def send_campaign(request: CampaignRequest):
    """Send three campaign emails to the supplied address.

    The function cycles through the bodies defined in ``email_bodies.json``
    and sends each one using the SendGrid helper defined in ``email_service``.
    """
    bodies = load_email_bodies()
    subject = "hello i am jarvis"
    for i in range(3):
        body = bodies[i % len(bodies)]
        try:
            send_email(to=request.to, subject=subject, body=body)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
    return {"status": "sent", "emails_sent": 3}

# AWS Lambda entry point – Mangum adapts the ASGI app to the Lambda proxy integration
handler = Mangum(app)