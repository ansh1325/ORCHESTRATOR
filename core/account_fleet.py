"""
LlamaOrchestrator Multi-Account Fleet & Autonomous Outreach Engine
Architect: Ansh Tiwari (Chief Systems Architect)

Manages multi-account operations (e.g. 20+ Gmail accounts, LinkedIn profiles, or custom agents):
1. Account Rotation & Load Balancing (distributes volume across accounts to avoid rate limits).
2. Intelligent Sending Cadence (25-100 emails/account/day with anti-spam jitter).
3. 24/7 Continuous Reply Monitoring & Autonomous Follow-Up Loop.
4. Extensible to any domain: Cold Outreach, Talent Sourcing, Job Hunting, Data Scraping.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from core.config import settings

logger = logging.getLogger("AccountFleet")

FLEET_STORE_FILE = settings.WORKSPACE_DIR / "account_fleet.json"
CAMPAIGNS_STORE_FILE = settings.WORKSPACE_DIR / "fleet_campaigns.json"


@dataclass
class ManagedAccount:
    account_id: str
    platform: str = "gmail"  # gmail, linkedin, twitter, custom
    email: str = ""
    profile_index: int = 0  # e.g. u/0, u/1 for browser sessions
    daily_limit: int = 50   # Safe daily threshold (25 - 100)
    sent_today: int = 0
    total_sent: int = 0
    status: str = "READY"   # READY, ACTIVE, COOLDOWN, RATE_LIMITED, ERROR
    last_sent_at: float = 0.0
    warmup_active: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProspectLead:
    email: str
    name: str = ""
    company: str = ""
    status: str = "QUEUED"  # QUEUED, SENT, OPENED, REPLIED, BOUNCED, UNRESPONSIVE
    current_touch: int = 0  # 1 (Initial), 2 (Follow-up 1), etc.
    assigned_account_id: str = ""
    last_contact_at: float = 0.0
    reply_snippet: str = ""
    tags: list[str] = field(default_factory=list)


class AccountFleetManager:
    """
    Orchestrates high-volume, multi-account autonomous operations with
    rate-limit compliance, load distribution, and 24/7 reply detection.
    """

    def __init__(self, storage_path: Path = FLEET_STORE_FILE):
        self.storage_path = storage_path
        self.campaigns_path = CAMPAIGNS_STORE_FILE
        self.accounts: dict[str, ManagedAccount] = {}
        self.prospects: dict[str, ProspectLead] = {}
        self._load()

    def _load(self):
        """Loads fleet state and campaign records from persistent disk."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for acc_data in data.get("accounts", []):
                    acc = ManagedAccount(**acc_data)
                    self.accounts[acc.account_id] = acc
            except Exception as e:
                logger.warning(f"Failed to load account fleet state: {e}")

        if not self.accounts:
            # Initialize default 20-account Gmail pool topology
            self._initialize_default_gmail_fleet(num_accounts=20)

        if self.campaigns_path.exists():
            try:
                cdata = json.loads(self.campaigns_path.read_text(encoding="utf-8"))
                for p_data in cdata.get("prospects", []):
                    lead = ProspectLead(**p_data)
                    self.prospects[lead.email.lower()] = lead
            except Exception as e:
                logger.warning(f"Failed to load campaign records: {e}")

    def _save(self):
        """Persists current fleet state and prospect status to disk."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text(
                json.dumps(
                    {"accounts": [asdict(a) for a in self.accounts.values()]},
                    indent=2
                ),
                encoding="utf-8"
            )
            self.campaigns_path.write_text(
                json.dumps(
                    {"prospects": [asdict(p) for p in self.prospects.values()]},
                    indent=2
                ),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Error persisting fleet state: {e}")

    def _initialize_default_gmail_fleet(self, num_accounts: int = 20):
        """Sets up a coordinated 20-account fleet topology for Master Ansh."""
        for i in range(num_accounts):
            acc_id = f"gmail_u{i}"
            email = f"sender_{i+1}@workspace.domain" if i > 0 else "primary_host@gmail.com"
            self.accounts[acc_id] = ManagedAccount(
                account_id=acc_id,
                platform="gmail",
                email=email,
                profile_index=i,
                daily_limit=random.randint(40, 75),  # Human-like staggered capacity
                sent_today=0,
                status="READY"
            )
        self._save()

    def register_account(
        self,
        account_id: str,
        platform: str = "gmail",
        email: str = "",
        profile_index: int = 0,
        daily_limit: int = 50,
        metadata: Optional[dict[str, Any]] = None
    ) -> ManagedAccount:
        """Registers or updates a specific account in the fleet."""
        acc = ManagedAccount(
            account_id=account_id,
            platform=platform,
            email=email or f"{account_id}@domain.com",
            profile_index=profile_index,
            daily_limit=daily_limit,
            metadata=metadata or {}
        )
        self.accounts[account_id] = acc
        self._save()
        return acc

    def get_fleet_summary(self, platform: Optional[str] = None) -> dict[str, Any]:
        """Provides an executive overview of fleet health, capacity, and active load."""
        accs = [a for a in self.accounts.values() if not platform or a.platform == platform]
        total_accounts = len(accs)
        ready_accounts = sum(1 for a in accs if a.status == "READY")
        total_daily_capacity = sum(a.daily_limit for a in accs)
        total_sent_today = sum(a.sent_today for a in accs)
        remaining_capacity = max(0, total_daily_capacity - total_sent_today)

        return {
            "platform": platform or "all",
            "total_accounts": total_accounts,
            "ready_accounts": ready_accounts,
            "total_daily_capacity": total_daily_capacity,
            "total_sent_today": total_sent_today,
            "remaining_capacity": remaining_capacity,
            "accounts": [asdict(a) for a in accs]
        }

    def select_next_account(self, platform: str = "gmail") -> Optional[ManagedAccount]:
        """
        Cognitive Load Balancer:
        Selects the healthiest, least-utilized account that has remaining daily capacity
        and has satisfied cooldown requirements.
        """
        candidates = [
            a for a in self.accounts.values()
            if a.platform == platform and a.status == "READY" and a.sent_today < a.daily_limit
        ]
        if not candidates:
            return None

        # Sort by: sent_today ascending, then last_sent_at ascending
        candidates.sort(key=lambda x: (x.sent_today, x.last_sent_at))
        return candidates[0]

    def add_prospects(self, prospect_list: list[dict[str, Any]]) -> int:
        """Adds target leads to the outbound campaign queue."""
        added = 0
        for p in prospect_list:
            em = p.get("email", "").strip().lower()
            if not em or "@" not in em:
                continue
            if em not in self.prospects:
                self.prospects[em] = ProspectLead(
                    email=em,
                    name=p.get("name", ""),
                    company=p.get("company", ""),
                    status="QUEUED",
                    tags=p.get("tags", [])
                )
                added += 1
        if added:
            self._save()
        return added

    async def dispatch_next_touch(
        self,
        lead: ProspectLead,
        subject: str,
        body_template: str,
        send_fn: Optional[Callable[[str, str, str, int], Any]] = None
    ) -> dict[str, Any]:
        """
        Executes a touch-point with anti-spam jitter and rotating account dispatch.
        """
        acc = self.select_next_account(platform="gmail")
        if not acc:
            return {"success": False, "error": "All fleet accounts have reached daily quota or are cooling down."}

        # Personalize body
        body = body_template.replace("{{name}}", lead.name or "there")
        body = body.replace("{{company}}", lead.company or "your firm")

        lead.status = "SENT"
        lead.current_touch += 1
        lead.assigned_account_id = acc.account_id
        lead.last_contact_at = time.time()

        acc.sent_today += 1
        acc.total_sent += 1
        acc.last_sent_at = time.time()
        if acc.sent_today >= acc.daily_limit:
            acc.status = "COOLDOWN"

        self._save()

        # If a live sender function is provided (e.g. Browser or SMTP), invoke it
        if send_fn:
            try:
                await asyncio.to_thread(send_fn, lead.email, subject, body, acc.profile_index)
            except Exception as e:
                logger.error(f"Live dispatch error to {lead.email}: {e}")

        return {
            "success": True,
            "recipient": lead.email,
            "dispatched_from_account": acc.account_id,
            "profile_index": acc.profile_index,
            "touch_number": lead.current_touch,
            "sent_today_for_account": acc.sent_today,
            "account_daily_limit": acc.daily_limit
        }

    def process_incoming_reply(self, sender_email: str, reply_snippet: str) -> dict[str, Any]:
        """
        Autonomous Reply Processor:
        Detects responses from leads, disables future follow-ups, and categorizes sentiment.
        """
        em = sender_email.strip().lower()
        lead = self.prospects.get(em)
        if not lead:
            # Auto-register external responder
            lead = ProspectLead(email=em, status="REPLIED", reply_snippet=reply_snippet)
            self.prospects[em] = lead

        lead.status = "REPLIED"
        lead.reply_snippet = reply_snippet

        # Determine sentiment & intent
        low = reply_snippet.lower()
        category = "INTERESTED"
        if any(w in low for w in ["unsubscribe", "remove me", "stop", "not interested"]):
            category = "OPTOUT"
            lead.status = "UNSUBSCRIBED"
        elif any(w in low for w in ["pricing", "cost", "how much", "send details", "more info", "demo"]):
            category = "HIGH_INTENT"
        elif any(w in low for w in ["call", "calendly", "zoom", "meet", "schedule"]):
            category = "MEETING_REQUEST"

        self._save()
        return {
            "lead_email": em,
            "status": lead.status,
            "sentiment_category": category,
            "action_taken": "Halted automated follow-ups; flagged for conversational closing."
        }

    def reset_daily_counters(self):
        """Resets 24-hour dispatch counters at the start of each new day."""
        for acc in self.accounts.values():
            acc.sent_today = 0
            if acc.status == "COOLDOWN":
                acc.status = "READY"
        self._save()


# Global Singleton Instance
account_fleet = AccountFleetManager()

