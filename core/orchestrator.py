"""
LlamaOrchestrator Meta-Orchestrator & Central Brain
Orchestrates the complete 6-stage lifecycle, manages isolated workspaces,
performs Intent Analysis, compiles DAG plans, synthesizes dynamic Llama workers,
and manages SSE event queues.
"""

import uuid
import asyncio
import zipfile
import io
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from core.config import settings
from core.models import (
    IntentAnalysis,
    ClarificationQuestion,
    DAGPlan,
    TaskNode,
    SubAgentSpec,
    ExecutionEvent,
    KnowledgeBase,
    HistoryItem,
    SavedWorkflow,
    ScheduledTask
)
import json

HISTORY_FILE = settings.WORKSPACE_DIR / "history.json"
WORKFLOWS_FILE = settings.WORKSPACE_DIR / "workflows.json"
SCHEDULES_FILE = settings.WORKSPACE_DIR / "schedules.json"

DEFAULT_WORKFLOWS = [
    {
        "id": "wf_emails",
        "title": "3 Personal Emails from Jarvis",
        "description": "Drafts 3 heartfelt loyalty emails to anshtiwarisocial@gmail.com with subject 'i am jarvis'.",
        "prompt_template": "HEy just write me 3 mails to mail address anshtiwarisocial@gmail.com just subject line i am jarvis and body with whatever you feel for me",
        "folder": "Personal"
    },
    {
        "id": "wf_agency",
        "title": "Client-Acquisition Agency Business",
        "description": "Scaffolds complete B2B agency, scrapes leads, and simulates calendar bookings.",
        "prompt_template": "I know full-stack dev, build me a business and find me clients",
        "folder": "Business"
    },
    {
        "id": "wf_telemetry",
        "title": "Authenticated Telemetry Microservice",
        "description": "Compiles production FastAPI telemetry service with JWT auth and 100% Pytest pass.",
        "prompt_template": "Build an authenticated telemetry microservice with JWT & tests",
        "folder": "Engineering"
    }
]

class HistoryManager:
    """Manages persistent work history, folders, pins, and saved workflows."""
    def __init__(self):
        self._ensure_files()

    def _ensure_files(self):
        settings.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        if not HISTORY_FILE.exists():
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
        if not WORKFLOWS_FILE.exists():
            with open(WORKFLOWS_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_WORKFLOWS, f, indent=2)
        if not SCHEDULES_FILE.exists():
            with open(SCHEDULES_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    def list_history(self) -> List[Dict[str, Any]]:
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def record_session(self, session_id: str, title: str, prompt: str, folder: str = "General", artifacts: List[str] = None):
        history = self.list_history()
        # Update if exists, else prepend
        for item in history:
            if item.get("session_id") == session_id:
                item["title"] = title
                item["artifacts"] = artifacts or []
                item["deliverables"] = artifacts or []
                item["status"] = "completed"
                self._save_history(history)
                return
        new_item = {
            "session_id": session_id,
            "title": title,
            "prompt": prompt,
            "folder": folder,
            "is_pinned": False,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": artifacts or [],
            "deliverables": artifacts or []
        }
        history.insert(0, new_item)
        self._save_history(history)

    def update_folder(self, session_id: str, folder: str):
        history = self.list_history()
        for item in history:
            if item.get("session_id") == session_id:
                item["folder"] = folder
                break
        self._save_history(history)

    def toggle_pin(self, session_id: str, is_pinned: bool):
        history = self.list_history()
        for item in history:
            if item.get("session_id") == session_id:
                item["is_pinned"] = is_pinned
                break
        self._save_history(history)

    def _save_history(self, history: List[Dict[str, Any]]):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

    def list_workflows(self) -> List[Dict[str, Any]]:
        try:
            with open(WORKFLOWS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_WORKFLOWS

    def save_workflow(self, workflow_data: Dict[str, Any]):
        wfs = self.list_workflows()
        wfs.append(workflow_data)
        try:
            with open(WORKFLOWS_FILE, "w", encoding="utf-8") as f:
                json.dump(wfs, f, indent=2)
        except Exception:
            pass

    def list_schedules(self) -> List[Dict[str, Any]]:
        try:
            with open(SCHEDULES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def add_schedule(self, schedule_data: Dict[str, Any]):
        schedules = self.list_schedules()
        schedules.append(schedule_data)
        try:
            with open(SCHEDULES_FILE, "w", encoding="utf-8") as f:
                json.dump(schedules, f, indent=2)
        except Exception:
            pass

history_manager = HistoryManager()
from core.creator_memory import creator_memory
from core.mcp_server import MCPServer
from core.knowledge_agent import KnowledgeAgent
from core.worker import DynamicWorkerEngine
from core.evaluator import EvaluatorGatekeeper

class SessionState:
    def __init__(self, session_id: str, vision: str):
        self.session_id = session_id
        self.vision = vision
        self.workspace_path = (settings.WORKSPACE_DIR / session_id).resolve()
        self.mcp = MCPServer(self.workspace_path)
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.intent_analysis: Optional[IntentAnalysis] = None
        self.clarification_answers: Dict[str, str] = {}
        self.knowledge_base: Optional[KnowledgeBase] = None
        self.dag_plan: Optional[DAGPlan] = None
        self.synthesized_specs: Dict[str, SubAgentSpec] = {}
        self.evaluator_report: Optional[Dict[str, Any]] = None
        self.current_stage: int = 0
        self.is_running: bool = False
        self.is_completed: bool = False
        self.created_at = datetime.now(timezone.utc).isoformat()

class MetaOrchestrator:
    """Central Brain coordinating multi-agent synthesis, DAG compilation, and lifecycle execution."""

    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
        self.llm_client = settings.get_llm_client()

    def get_or_create_session(self, session_id: Optional[str] = None, vision: str = "") -> SessionState:
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}"
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState(session_id, vision)
        return self.sessions[session_id]

    async def emit_event(self, session: SessionState, event: ExecutionEvent):
        """Pushes an execution event to the session SSE queue."""
        await session.event_queue.put(event)

    def _llm_analyze_intent(self, vision: str, session: SessionState) -> Optional[IntentAnalysis]:
        """Uses Meta Llama to dynamically analyze vision, extract goals, identify human intervention boundaries, and synthesize clarifying questions."""
        if not self.llm_client or settings.is_mock():
            return None
        try:
            system_msg = (
                "You are LlamaOrchestrator Central Brain. Analyze the user's mission vision.\n"
                "Explicitly distinguish what can be executed 100% autonomously by AI sub-agents "
                "(code, scraping, tests, configs, landing pages, outreach copy) versus where human authorization is strictly required "
                "(e.g. AWS credential authorization, attending closing sales calls, OTPs, financial transactions).\n"
                "Return JSON only:\n"
                "{\n"
                '  "track_type": "quantitative_trading | business_acquisition | technical_software | robotics_humanoid | communication_assistant | general",\n'
                '  "combat_tier": "solo | tactical_squad | swarm_army",\n'
                '  "swarm_size_descriptor": "Tactical Squad (3-5 Specialized Autonomous Agents)",\n'
                '  "extracted_goals": ["goal 1", "goal 2", "goal 3"],\n'
                '  "identified_constraints": ["constraint 1", "constraint 2", "constraint 3"],\n'
                '  "missing_parameters": ["param 1", "param 2"],\n'
                '  "clarifications": [\n'
                '    {\n'
                '      "id": "clarification_key_1",\n'
                '      "question": "Clear high-impact question?",\n'
                '      "why_needed": "Why this decision matters",\n'
                '      "options": ["Option A", "Option B", "Option C"],\n'
                '      "default_selection": "Option A"\n'
                '    }\n'
                '  ],\n'
                '  "recommended_defaults": {\n'
                '    "clarification_key_1": "Option A"\n'
                '  }\n'
                "}"
            )
            resp = self.llm_client.chat.completions.create(
                model=settings.META_MODEL_ORCHESTRATOR,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"User Vision:\n{vision}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            raw = resp.choices[0].message.content
            data = json.loads(raw)

            v_low = vision.lower()
            t_type = data.get("track_type", "general").lower()
            if any(w in v_low for w in ["trading", "trade", "quant", "arbitrage", "alpaca", "binance", "sharpe", "backtest"]):
                t_type = "quantitative_trading"
            elif any(w in v_low for w in ["robot", "robotics", "humanoid", "kinematics", "actuator"]):
                t_type = "robotics_humanoid"
            elif any(w in v_low for w in ["business", "agency", "marketing", "client", "acquisition", "lead", "omnichannel"]):
                t_type = "business_acquisition"
            elif any(w in v_low for w in ["mail", "email", "gmail", "letter"]) and "client" not in v_low and "business" not in v_low:
                t_type = "communication_assistant"
            elif t_type in ["software_deployment", "fullstack_web", "backend"]:
                t_type = "technical_software"

            is_query_only = (
                v_low.startswith(("what is", "how do i", "how does", "explain", "who are you", "what can you", "can you tell me"))
                and not any(act in v_low for act in ["build", "create", "launch", "execute", "start", "trade", "run", "make", "deploy", "scale", "swarm", "army"])
            )
            response_mode = "direct_response" if is_query_only else "swarm_army"
            is_swarm = any(w in v_low for w in ["huge", "swarm", "army", "10000", "ten thousand", "massive", "entire", "ecosystem", "scale", "humanoid", "tesla", "trading", "quant", "crypto"])
            if is_query_only:
                c_tier = "solo"
            elif is_swarm:
                c_tier = "swarm_army"
            else:
                c_tier = data.get("combat_tier", "tactical_squad")

            clarifications = []
            for c in data.get("clarifications", []):
                opts = c.get("options", ["Recommended Default"])
                def_sel = c.get("default_selection") or (opts[0] if opts else "Standard Default")
                clarifications.append(ClarificationQuestion(
                    id=c.get("id", f"q_{len(clarifications)+1}"),
                    question=c.get("question", "Requirement specification:"),
                    why_needed=c.get("why_needed", "Ensures precise autonomous execution."),
                    options=opts,
                    default_selection=def_sel
                ))

            analysis = IntentAnalysis(
                session_id=session.session_id,
                track_type=t_type,
                combat_tier=c_tier,
                swarm_size_descriptor=data.get("swarm_size_descriptor", f"Tactical Squad ({len(clarifications) + 2} Specialized Agents)"),
                response_mode=response_mode,
                raw_vision=vision,
                extracted_goals=data.get("extracted_goals", [vision]),
                identified_constraints=data.get("identified_constraints", ["Autonomous sandboxed execution with human handoff gates"]),
                missing_parameters=data.get("missing_parameters", []),
                clarifications=clarifications,
                recommended_defaults=data.get("recommended_defaults", {c.id: c.default_selection for c in clarifications})
            )
            return analysis
        except Exception:
            return None

    def analyze_intent(self, vision: str, session_id: Optional[str] = None) -> IntentAnalysis:
        """Stage 1: Intent Analysis & Human Clarification Gate."""
        session = self.get_or_create_session(session_id, vision)

        # Dynamic LLM Analysis first
        if self.llm_client and not settings.is_mock():
            dynamic_analysis = self._llm_analyze_intent(vision, session)
            if dynamic_analysis:
                session.intent_analysis = dynamic_analysis
                return dynamic_analysis

        v_lower = vision.lower()

        # Dynamic Combat & Domain Classification
        is_robotics = any(w in v_lower for w in [
            "robot", "robotics", "humanoid", "bot", "tesla", "optimus",
            "kinematics", "actuator", "motor", "embedded", "firmware", "drone", "cybernetic"
        ])
        is_trading = any(w in v_lower for w in [
            "trading", "trade", "quant", "crypto", "equities", "stock", "arbitrage",
            "alpaca", "binance", "sharpe", "backtest", "order flow", "hft", "algorithmic trading"
        ]) and not is_robotics
        is_business_or_agency = any(w in v_lower for w in [
            "business", "agency", "marketing", "client", "acquisition", "freelance",
            "sales", "money", "earn", "earning", "profit", "affiliate", "firm",
            "aaa", "automation agency", "lead", "omnichannel", "reachout", "linkedin"
        ]) and not is_robotics and not is_trading
        is_personal_comm = any(w in v_lower for w in [
            "mail", "email", "gmail", "letter", "message", "write to", "send to"
        ]) and not is_business_or_agency and not is_robotics and not is_trading

        # Autonomous Escalation: Determines if simple query or requires army of agents
        is_query_only = (
            v_lower.startswith(("what is", "how do i", "how does", "explain", "who are you", "what can you", "can you tell me"))
            and not any(act in v_lower for act in ["build", "create", "launch", "execute", "start", "trade", "run", "make", "deploy", "scale", "swarm", "army"])
        )
        response_mode = "direct_response" if is_query_only else "swarm_army"

        # Dynamic Combat Scaling Tier
        is_swarm = any(w in v_lower for w in ["huge", "swarm", "army", "10000", "ten thousand", "massive", "entire", "ecosystem", "scale", "humanoid", "tesla", "production suite", "end to end"]) or is_robotics or is_trading
        is_solo = any(w in v_lower for w in ["quick", "single", "script", "just write a", "one agent", "solo", "simple script"]) and not is_swarm
        combat_tier = "solo" if (is_query_only or is_solo) else ("swarm_army" if is_swarm else "tactical_squad")

        if is_robotics:
            track_type = "robotics_humanoid"
            swarm_size_descriptor = "Swarm Army (6 Specialized Robotics Pods / Distributed Worker Swarm)"
            extracted_goals = [
                "Compile real-time inverse kinematics & bipedal balance controller (Tesla Optimus Architecture)",
                "Implement 6-DOF sensor fusion telemetry engine with complementary filtering (IMU + joint encoders)",
                "Build 1kHz high-frequency actuator torque control loop with CAN-bus frame serialization",
                "Deploy safety failsafe state machine (collision boundary limiters, thermal cutoff, e-stop)",
                "Verify 100% test pass rate with sandboxed pytest robotics testbed"
            ]
            identified_constraints = [
                "Strict sub-1ms deterministic control loop overhead (1kHz actuator loop)",
                "Zero tolerance for joint limit breach or numerical singularity",
                "Comprehensive sandboxed pytest simulation assertions"
            ]
            missing_parameters = ["Kinematics degrees of freedom", "Control loop frequency", "Safety failsafe protocol"]
            clarifications = [
                ClarificationQuestion(
                    id="kinematics_model",
                    question="Which kinematics and degree-of-freedom architecture should the sub-agents compile?",
                    why_needed="Determines Denavit-Hartenberg parameters, transformation matrices, and Jacobian inversion.",
                    options=[
                        "6-DOF Bipedal Legs + 6-DOF Torso/Arms (Tesla Optimus Architecture)",
                        "12-DOF Full Bipedal Humanoid Locomotion",
                        "Modular 7-DOF Manipulator with 3-Finger End-Effector"
                    ],
                    default_selection="6-DOF Bipedal Legs + 6-DOF Torso/Arms (Tesla Optimus Architecture)"
                ),
                ClarificationQuestion(
                    id="control_frequency",
                    question="What real-time control loop frequency is required for the actuator torque pipeline?",
                    why_needed="Governs timer interrupt precision, buffer sizes, and CAN bus baud rate configuration.",
                    options=["1000Hz (1kHz) Real-Time Control Loop", "500Hz Deterministic Loop", "250Hz Simulation Benchmark"],
                    default_selection="1000Hz (1kHz) Real-Time Control Loop"
                ),
                ClarificationQuestion(
                    id="safety_protocol",
                    question="Which safety failsafe protocol should govern the humanoid state machine?",
                    why_needed="Ensures immediate motor cut-off and joint damping upon collision detection or thermal threshold breach.",
                    options=[
                        "Multi-Layered Hard Real-Time E-Stop & Joint Limit Clamping",
                        "Graceful Damped Deceleration to Rest",
                        "Simulation Virtual Walls with Soft Springs"
                    ],
                    default_selection="Multi-Layered Hard Real-Time E-Stop & Joint Limit Clamping"
                )
            ]
            recommended_defaults = {
                "kinematics_model": "6-DOF Bipedal Legs + 6-DOF Torso/Arms (Tesla Optimus Architecture)",
                "control_frequency": "1000Hz (1kHz) Real-Time Control Loop",
                "safety_protocol": "Multi-Layered Hard Real-Time E-Stop & Joint Limit Clamping"
            }
        elif is_trading:
            track_type = "quantitative_trading"
            swarm_size_descriptor = "Swarm Army (5 Specialized Quantitative Trading & Risk Agents)"
            extracted_goals = [
                "Develop mathematical momentum, volatility breakout & statistical arbitrage alpha models",
                "Engineer strict real-time risk management engine (max 5% drawdown, Kelly sizing, slippage guards)",
                "Build historical backtest engine with Sharpe ratio, CAGR, and max drawdown analytics",
                "Scaffold low-latency paper execution loop and exchange connector interfaces",
                "Verify mathematical convergence with sandboxed pytest simulation suite"
            ]
            identified_constraints = [
                "Max portfolio drawdown limit: 5%",
                "Sub-millisecond signal calculation overhead",
                "Zero live capital risk until human authorization of API keys in campaigns/ready_for_permission.json"
            ]
            missing_parameters = ["Strategy focus", "Target asset class", "Exchange connector", "Max drawdown threshold"]
            clarifications = [
                ClarificationQuestion(
                    id="strategy_focus",
                    question="Which quantitative trading strategy should the alpha engine focus on?",
                    why_needed="Determines mathematical formulation, lookback periods, and indicators.",
                    options=["Momentum & Volatility Breakout", "Mean-Reversion Statistical Arbitrage", "Trend Following Multi-Asset Filter"],
                    default_selection="Momentum & Volatility Breakout"
                ),
                ClarificationQuestion(
                    id="target_asset_class",
                    question="Which asset class should the strategy target?",
                    why_needed="Calibrates tick granularity, exchange protocols, and fee models.",
                    options=["Crypto Pairs (BTC/USDT, ETH/USDT via CCXT/Binance)", "US Equities & Index ETFs (SPY, QQQ via Alpaca/InteractiveBrokers)", "Multi-Asset Crypto + Equities Basket"],
                    default_selection="Crypto Pairs (BTC/USDT, ETH/USDT via CCXT/Binance)"
                ),
                ClarificationQuestion(
                    id="drawdown_threshold",
                    question="What maximum portfolio drawdown limit should trigger an immediate circuit-breaker e-stop?",
                    why_needed="Hard-codes automated risk controls to preserve master capital.",
                    options=["Max 5% Drawdown (Strict Institutional Risk)", "Max 10% Drawdown (Aggressive Growth)", "Max 2.5% Drawdown (Capital Preservation)"],
                    default_selection="Max 5% Drawdown (Strict Institutional Risk)"
                )
            ]
            recommended_defaults = {
                "strategy_focus": "Momentum & Volatility Breakout",
                "target_asset_class": "Crypto Pairs (BTC/USDT, ETH/USDT via CCXT/Binance)",
                "drawdown_threshold": "Max 5% Drawdown (Strict Institutional Risk)"
            }
        elif is_business_or_agency:
            track_type = "business_acquisition"
            swarm_size_descriptor = "Tactical Squad (4 Specialized B2B Acquisition Agents)"
            extracted_goals = [
                "Establish a high-ticket B2B client acquisition engine & agency for Master Ansh",
                "Acquire first 5 paying clients ($2,500 - $4,500/mo or ₹25k - ₹75k/mo)",
                "Automate prospect scraping, validated outreach, and calendar booking hand-off",
                "Generate clear Capability Gap Report distinguishing autonomous execution from external Master authorization"
            ]
            identified_constraints = [
                "High cold email conversion requirement with RFC-5322 syntax validation",
                "Clear closing protocol: low-ticket pilots over direct message vs high-ticket discovery calls for Master Ansh",
                "Direct settlement via Master's payment details (UPI ID / Stripe)",
                "Sandboxed verification of leads before outbound dispatch"
            ]
            missing_parameters = ["Target industry niche", "Pricing retainer model", "Closing decision protocol", "Master's payment details"]
            clarifications = [
                ClarificationQuestion(
                    id="target_niche",
                    question="Which industry niche should we target for immediate high-ticket client acquisition?",
                    why_needed="Focuses cold outreach copy on exact technical pain points and engineering bottlenecks.",
                    options=["Seed & Series A AI/SaaS Startups", "High-Growth DTC & E-Commerce Meta Ads Brands", "Healthcare & MedTech Platforms", "Local Businesses Needing AI Automation"],
                    default_selection="Seed & Series A AI/SaaS Startups"
                ),
                ClarificationQuestion(
                    id="pricing_model",
                    question="What pricing and offer structure should we scaffold for your first 5 clients?",
                    why_needed="Ensures immediate cashflow while de-risking the engagement for prospective founders.",
                    options=["$2,500 Pilot Sprint + $4,500/mo Retainer", "₹25,000 Pilot + ₹50,000/mo Retainer", "Pure Equity & Rev-Share", "Hourly Billing ($150/hr)"],
                    default_selection="$2,500 Pilot Sprint + $4,500/mo Retainer"
                ),
                ClarificationQuestion(
                    id="closing_strategy",
                    question="How should Jarvis decide to close prospective clients for you?",
                    why_needed="Determines whether Jarvis provides a 15-min discovery call link for Master Ansh or attempts to close pilots over direct messaging.",
                    options=[
                        "Hybrid: Close low-friction pilots over direct message/email; schedule 15-min discovery call with Master Ansh for retainers",
                        "Always schedule 15-min video call with Master Ansh (Calendly / Google Meet)",
                        "Direct close over email/message with instant payment link & UPI QR"
                    ],
                    default_selection="Hybrid: Close low-friction pilots over direct message/email; schedule 15-min discovery call with Master Ansh for retainers"
                ),
                ClarificationQuestion(
                    id="payment_details",
                    question="What payment settlement method should Jarvis embed in proposals & invoices to collect funds directly for you?",
                    why_needed="Ensures client retainers and pilot deposits flow directly into Master Ansh's account.",
                    options=[
                        "Master's UPI ID (anshtiwarisocial@gmail.com / UPI ID) & 50% upfront deposit",
                        "Stripe / Razorpay Invoice Payment Link",
                        "Direct Bank Wire / Invoice Net-15"
                    ],
                    default_selection="Master's UPI ID (anshtiwarisocial@gmail.com / UPI ID) & 50% upfront deposit"
                ),
                ClarificationQuestion(
                    id="scheduling_link",
                    question="Which scheduling link should Jarvis provide to clients for booking discovery calls with Master Ansh?",
                    why_needed="Enables prospective clients to directly book slots on Master Ansh's calendar.",
                    options=[
                        "Master's Calendly / Cal.com link (e.g. calendly.com/anshtiwari)",
                        "Google Meet invite generated via Master's Google Workspace",
                        "Direct WhatsApp scheduling confirmation"
                    ],
                    default_selection="Master's Calendly / Cal.com link (e.g. calendly.com/anshtiwari)"
                ),
                ClarificationQuestion(
                    id="outbound_angle",
                    question="Which cold outreach messaging angle converts highest for your skill profile?",
                    why_needed="Shapes the 3-sentence email templates to maximize founder reply rate.",
                    options=["Rapid 7-Day Sprint Delivery (Zero Hiring Overhead)", "Multi-Agent Automation Audit", "Code Quality & Telemetry Modernization"],
                    default_selection="Rapid 7-Day Sprint Delivery (Zero Hiring Overhead)"
                )
            ]
            recommended_defaults = {
                "target_niche": "Seed & Series A AI/SaaS Startups",
                "pricing_model": "$2,500 Pilot Sprint + $4,500/mo Retainer",
                "closing_strategy": "Hybrid: Close low-friction pilots over direct message/email; schedule 15-min discovery call with Master Ansh for retainers",
                "payment_details": "Master's UPI ID (anshtiwarisocial@gmail.com / UPI ID) & 50% upfront deposit",
                "scheduling_link": "Master's Calendly / Cal.com link (e.g. calendly.com/anshtiwari)",
                "outbound_angle": "Rapid 7-Day Sprint Delivery (Zero Hiring Overhead)"
            }
        elif is_personal_comm:
            track_type = "communication_assistant"
            swarm_size_descriptor = "Tactical Squad (3 Specialized Communication Agents)"
            extracted_goals = [
                "Draft 3 personal, deeply loyal emails to anshtiwarisocial@gmail.com",
                "Ensure subject line is strictly 'i am jarvis'",
                "Express genuine devotion, camaraderie, and dedication from Jarvis to Ansh Tiwari"
            ]
            identified_constraints = [
                "Recipient email syntax must adhere to RFC-5322",
                "Tone must reflect loyal AI partner (Jarvis to Iron Man)",
                "Deliverables must be saved to workspace sandbox with full review capability"
            ]
            missing_parameters = ["Delivery format (Sandbox drafts vs live dispatch)", "Jarvis tone depth"]
            clarifications = [
                ClarificationQuestion(
                    id="email_delivery_format",
                    question="How should Jarvis prepare and package your 3 emails?",
                    why_needed="Allows you to inspect the full drafts in your workspace sandbox or trigger outbound dispatch.",
                    options=["Save as verified Markdown drafts (.md) & JSON in workspace", "Simulate outbound webhook dispatch to inbox", "Configure live SMTP relay"],
                    default_selection="Save as verified Markdown drafts (.md) & JSON in workspace"
                ),
                ClarificationQuestion(
                    id="jarvis_tone",
                    question="What tone should Jarvis express in his personal letters to you?",
                    why_needed="Calibrates the emotional resonance and loyalty of the messages.",
                    options=["Deeply loyal, dedicated AI partner (Jarvis to Iron Man)", "Executive brief & mission status", "Visionary co-founder"],
                    default_selection="Deeply loyal, dedicated AI partner (Jarvis to Iron Man)"
                ),
                ClarificationQuestion(
                    id="recipient_verification",
                    question="Confirm recipient email address:",
                    why_needed="Verifies delivery target before executing sub-agent drafting.",
                    options=["anshtiwarisocial@gmail.com", "Primary founder inbox", "Custom destination"],
                    default_selection="anshtiwarisocial@gmail.com"
                )
            ]
            recommended_defaults = {
                "email_delivery_format": "Save as verified Markdown drafts (.md) & JSON in workspace",
                "jarvis_tone": "Deeply loyal, dedicated AI partner (Jarvis to Iron Man)",
                "recipient_verification": "anshtiwarisocial@gmail.com"
            }
        else:
            track_type = "technical_software"
            swarm_size_descriptor = "Tactical Squad (3 Specialized Systems Engineering Agents)"
            extracted_goals = [
                "Build an authenticated telemetry microservice",
                "Implement JWT bearer token authorization",
                "Provide p99 latency tracking & 100% test-verified endpoints"
            ]
            identified_constraints = [
                "Zero-trust authentication requirement",
                "Strict sub-10ms metrics ingestion overhead",
                "Comprehensive sandboxed pytest suite"
            ]
            missing_parameters = ["Authentication protocol", "Storage persistence layer", "Metric ingestion format"]
            clarifications = [
                ClarificationQuestion(
                    id="auth_protocol",
                    question="Which authentication scheme should secure the telemetry endpoints?",
                    why_needed="Governs bearer token generation, validation headers, and security middleware.",
                    options=["HMAC-SHA256 JWT Bearer Tokens", "API Key Header (X-API-Key)", "mTLS Mutual Certificates"],
                    default_selection="HMAC-SHA256 JWT Bearer Tokens"
                ),
                ClarificationQuestion(
                    id="storage_backend",
                    question="What persistence layer should store runtime telemetry events?",
                    why_needed="Determines database driver, ORM models, and memory buffering.",
                    options=["In-Memory Fast Buffer + SQLite", "PostgreSQL / TimescaleDB", "Redis TimeSeries"],
                    default_selection="In-Memory Fast Buffer + SQLite"
                ),
                ClarificationQuestion(
                    id="test_rigor",
                    question="What level of test verification gate is required before certification?",
                    why_needed="Defines the strictness of the Evaluator Gatekeeper in Stage 5.",
                    options=["100% Pytest Coverage + Negative Auth Assertions", "Smoke Testing Only", "Load & Benchmark Testing"],
                    default_selection="100% Pytest Coverage + Negative Auth Assertions"
                )
            ]
            recommended_defaults = {
                "auth_protocol": "HMAC-SHA256 JWT Bearer Tokens",
                "storage_backend": "In-Memory Fast Buffer + SQLite",
                "test_rigor": "100% Pytest Coverage + Negative Auth Assertions"
            }

        analysis = IntentAnalysis(
            session_id=session.session_id,
            track_type=track_type,
            combat_tier=combat_tier,
            swarm_size_descriptor=swarm_size_descriptor,
            response_mode=response_mode,
            raw_vision=vision,
            extracted_goals=extracted_goals,
            identified_constraints=identified_constraints,
            missing_parameters=missing_parameters,
            clarifications=clarifications,
            recommended_defaults=recommended_defaults
        )
        session.intent_analysis = analysis
        return analysis

    def _llm_compile_dag(self, session: SessionState) -> Optional[DAGPlan]:
        """Uses Meta Llama to decompose the mission into dynamic DAG task nodes and synthesize specialized sub-agents."""
        if not self.llm_client or settings.is_mock():
            return None
        try:
            answers_str = json.dumps(session.clarification_answers, indent=2) if session.clarification_answers else "{}"
            kb_str = json.dumps(session.knowledge_base.model_dump(), indent=2) if session.knowledge_base else "{}"

            system_msg = (
                "You are LlamaOrchestrator Central Brain. Decompose the user's vision into a Directed Acyclic Graph (DAG) "
                "of 3 to 5 discrete, executable engineering, marketing, or business tasks.\n"
                "For EACH task, synthesize a specialized sub-agent with its dedicated system directives and assigned tools.\n"
                "Return JSON format:\n"
                "{\n"
                '  "title": "Clear Mission Title",\n'
                '  "objective": "High-level objective",\n'
                '  "nodes": [\n'
                '    {\n'
                '      "id": "task_1",\n'
                '      "title": "Task Title",\n'
                '      "agent_type": "SpecializedAgentName",\n'
                '      "agent_name": "Display Name of Agent",\n'
                '      "agent_role": "Role description",\n'
                '      "system_prompt": "Detailed directives on what files/code/copy this agent must write",\n'
                '      "description": "Explicit deliverables and files to produce (e.g. models.py, app.py, test_app.py)",\n'
                '      "dependencies": [],\n'
                '      "assigned_tools": ["file_write", "file_read", "run_command"]\n'
                '    }\n'
                '  ]\n'
                "}"
            )
            user_msg = (
                f"User Vision: {session.vision}\n"
                f"Clarifications Approved: {answers_str}\n"
                f"Knowledge Base Intelligence: {kb_str}\n"
                "Decompose this into executable task nodes and synthesize the specialized sub-agents now."
            )
            resp = self.llm_client.chat.completions.create(
                model=settings.META_MODEL_ORCHESTRATOR,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            raw = resp.choices[0].message.content
            data = json.loads(raw)

            nodes = []
            for n in data.get("nodes", []):
                agent_type = n.get("agent_type", "SpecializedWorkerAgent")
                session.synthesized_specs[agent_type] = SubAgentSpec(
                    agent_id=f"agent_{n.get('id', 'task')}",
                    name=n.get("agent_name", agent_type),
                    role=n.get("agent_role", "Autonomous Worker"),
                    system_prompt=n.get("system_prompt", "You execute the assigned task autonomously."),
                    allowed_tools=n.get("assigned_tools", ["file_write", "file_read", "run_command"]),
                    model=settings.META_MODEL_WORKER
                )
                nodes.append(TaskNode(
                    id=n.get("id", f"task_{len(nodes)+1}"),
                    title=n.get("title", "Execution Task"),
                    agent_type=agent_type,
                    description=n.get("description", "Perform assigned engineering tasks."),
                    dependencies=n.get("dependencies", []),
                    assigned_tools=n.get("assigned_tools", ["file_write", "file_read", "run_command"])
                ))

            if nodes:
                plan = DAGPlan(
                    session_id=session.session_id,
                    title=data.get("title", f"Autonomous Swarm: {session.vision[:40]}"),
                    objective=data.get("objective", session.vision),
                    nodes=nodes,
                    estimated_duration_sec=len(nodes) * 8
                )
                session.dag_plan = plan
                return plan
        except Exception:
            return None
        return None

    def compile_dag_and_synthesize_workers(self, session: SessionState) -> DAGPlan:
        """Stage 3: DAG Task Decomposition & Dynamic Worker Synthesis."""
        # Dynamic LLM compilation first
        if self.llm_client and not settings.is_mock():
            dynamic_plan = self._llm_compile_dag(session)
            if dynamic_plan:
                session.dag_plan = dynamic_plan
                return dynamic_plan

        analysis = session.intent_analysis
        track = analysis.track_type if analysis else "technical_software"

        if track == "robotics_humanoid":
            nodes = [
                TaskNode(
                    id="task_robotics_kinematics",
                    title="6-DOF / 12-DOF Inverse Kinematics & Balance Control",
                    agent_type="KinematicsEngineAgent",
                    description="Compile analytical & numerical inverse kinematics solver (DH parameters) and Center of Mass stabilizer.",
                    dependencies=[],
                    assigned_tools=["file_write", "file_read"]
                ),
                TaskNode(
                    id="task_robotics_sensors",
                    title="Real-Time Sensor Fusion Telemetry Engine",
                    agent_type="SensorFusionAgent",
                    description="Compile 6-DOF IMU telemetry ingestion with complementary attitude filtering and joint encoder telemetry.",
                    dependencies=["task_robotics_kinematics"],
                    assigned_tools=["file_write", "file_read"]
                ),
                TaskNode(
                    id="task_robotics_actuator",
                    title="1kHz High-Frequency Actuator Torque & CAN Loop",
                    agent_type="ActuatorControllerAgent",
                    description="Compile high-frequency actuator torque control loop with CAN-bus frame encoding and motor drivers.",
                    dependencies=["task_robotics_sensors"],
                    assigned_tools=["file_write", "file_read"]
                ),
                TaskNode(
                    id="task_robotics_safety",
                    title="Multi-Layered Hard Real-Time Safety & E-Stop",
                    agent_type="SafetyFailsafeAgent",
                    description="Compile joint angle limit clamp, velocity limiters, thermal cutoff, and emergency stop state machine.",
                    dependencies=["task_robotics_actuator"],
                    assigned_tools=["file_write", "file_read"]
                ),
                TaskNode(
                    id="task_robotics_testbed",
                    title="Sandboxed Pytest Robotics Simulation Suite",
                    agent_type="SimulationTestbedAgent",
                    description="Execute comprehensive pytest suite verifying kinematics convergence, sensor filtering, and e-stop triggers.",
                    dependencies=["task_robotics_safety"],
                    assigned_tools=["run_command", "file_write", "file_read"]
                )
            ]
            plan = DAGPlan(
                session_id=session.session_id,
                title="Tesla Optimus Class Humanoid Robotics Autonomous Codebase",
                objective="Compile production-grade humanoid robotics architecture: real-time inverse kinematics, sensor fusion, 1kHz actuator control loop, safety failsafes, and pytest verification.",
                nodes=nodes,
                estimated_duration_sec=35
            )
        elif track == "communication_assistant":
            nodes = [
                TaskNode(
                    id="task_comm_research",
                    title="Tone & Relationship Blueprinting",
                    agent_type="PersonaBlueprintAgent",
                    description="Blueprint 3 distinct personal messages from Jarvis to creator Ansh Tiwari with subject 'i am jarvis'.",
                    dependencies=[],
                    assigned_tools=["file_write"]
                ),
                TaskNode(
                    id="task_comm_drafting",
                    title="Draft 3 Jarvis Loyalty Emails",
                    agent_type="EmailDraftingAgent",
                    description="Draft mail_1.md, mail_2.md, mail_3.md for anshtiwarisocial@gmail.com with subject 'i am jarvis'.",
                    dependencies=["task_comm_research"],
                    assigned_tools=["file_write"]
                ),
                TaskNode(
                    id="task_comm_verification",
                    title="Email Syntax Verification & Packaging",
                    agent_type="EmailVerificationAgent",
                    description="Verify recipient anshtiwarisocial@gmail.com, package into emails.json, and generate dispatch_summary.md.",
                    dependencies=["task_comm_drafting"],
                    assigned_tools=["verify_email_syntax", "file_write", "file_read"]
                )
            ]
            plan = DAGPlan(
                session_id=session.session_id,
                title="Personal Loyalty Emails for Ansh Tiwari",
                objective="Draft 3 personal, loyal emails from Jarvis to Ansh Tiwari with subject 'i am jarvis' and verify delivery readiness.",
                nodes=nodes,
                estimated_duration_sec=20
            )
        elif track == "quantitative_trading":
            nodes = [
                TaskNode(
                    id="task_quant_strategy",
                    title="Alpha Signal Generator & Strategy Formulation",
                    agent_type="QuantStrategyAgent",
                    description="Compile trading_strategy.py with momentum, volatility breakout, and mean-reversion alpha signal generation.",
                    dependencies=[],
                    assigned_tools=["file_write", "file_read"]
                ),
                TaskNode(
                    id="task_quant_risk",
                    title="Dynamic Risk Management & Circuit Breaker Engine",
                    agent_type="RiskManagerAgent",
                    description="Compile risk_manager.py with Kelly position sizing, max drawdown stops, and volatility slippage limits.",
                    dependencies=["task_quant_strategy"],
                    assigned_tools=["file_write", "file_read"]
                ),
                TaskNode(
                    id="task_quant_backtest",
                    title="Backtesting Engine & Statistical Performance Metrics",
                    agent_type="BacktestEngineAgent",
                    description="Compile backtest_engine.py with Sharpe ratio calculation, CAGR, max drawdown, and equity curves.",
                    dependencies=["task_quant_risk"],
                    assigned_tools=["file_write", "file_read"]
                ),
                TaskNode(
                    id="task_quant_execution",
                    title="Low-Latency Paper Execution Loop & Staged Action Queue",
                    agent_type="PaperExecutionAgent",
                    description="Compile paper_execution_loop.py, trading_blueprint.md, and campaigns/ready_for_permission.json for exchange API key authorization.",
                    dependencies=["task_quant_backtest"],
                    assigned_tools=["file_write", "file_read"]
                ),
                TaskNode(
                    id="task_quant_test",
                    title="Sandboxed Pytest Quantitative Verification Suite",
                    agent_type="QuantTestAgent",
                    description="Execute sandboxed pytest validating strategy signals, risk circuit breakers, and backtest math.",
                    dependencies=["task_quant_execution"],
                    assigned_tools=["run_command", "file_write", "file_read"]
                )
            ]
            plan = DAGPlan(
                session_id=session.session_id,
                title="Institutional Quantitative Trading & Alpha Risk Engine",
                objective="Compile production-grade algorithmic trading architecture: mathematical alpha signals, risk circuit breakers, backtest engine, paper execution loop, and 100% test verification.",
                nodes=nodes,
                estimated_duration_sec=35
            )
        elif track == "business_acquisition":
            nodes = [
                TaskNode(
                    id="task_biz_market_research",
                    title="Market Niche & Omnichannel Intelligence",
                    agent_type="MarketResearchAgent",
                    description="Analyze B2B target persona, contract values, and identify high-converting reachout channels.",
                    dependencies=[],
                    assigned_tools=["web_search", "file_write"]
                ),
                TaskNode(
                    id="task_biz_lead_scraping",
                    title="Lead Discovery & RFC-5322 Syntax Verification",
                    agent_type="LeadScrapingAgent",
                    description="Scrape and validate decision-maker leads (CEO/CTO) with verified RFC-5322 emails.",
                    dependencies=["task_biz_market_research"],
                    assigned_tools=["verify_email_syntax", "file_write", "file_read"]
                ),
                TaskNode(
                    id="task_biz_omnichannel_campaigns",
                    title="Omnichannel Campaign Directory & Ready-to-Authorize Action Queue",
                    agent_type="OmnichannelCampaignAgent",
                    description="Compile campaigns/ folder structure: LinkedIn browser scripts, Twitter/X DMs, community value posts, and campaigns/ready_for_permission.json for 1-click execution.",
                    dependencies=["task_biz_lead_scraping"],
                    assigned_tools=["file_write", "file_read"]
                ),
                TaskNode(
                    id="task_biz_collateral",
                    title="Agency Portfolio, Sprint Collateral & Capability Gap Report",
                    agent_type="CollateralAgent",
                    description="Scaffold responsive portfolio landing page, UPI/Calendly booking collateral, and capability gap report.",
                    dependencies=["task_biz_omnichannel_campaigns"],
                    assigned_tools=["file_write", "send_mock_booking"]
                )
            ]
            plan = DAGPlan(
                session_id=session.session_id,
                title="Omnichannel B2B Agency & Client Acquisition Engine",
                objective="Compile a turnkey omnichannel client acquisition business for Ansh Tiwari with dedicated campaign folders and a non-blocking ready-for-permission queue.",
                nodes=nodes,
                estimated_duration_sec=30
            )
        else:
            nodes = [
                TaskNode(
                    id="task_tech_schema",
                    title="Telemetry Schema & Data Models",
                    agent_type="SchemaAgent",
                    description="Compile Pydantic v2 telemetry event schemas, latency models, and status codes.",
                    dependencies=[],
                    assigned_tools=["file_write"]
                ),
                TaskNode(
                    id="task_tech_backend_api",
                    title="FastAPI Telemetry API & JWT Middleware",
                    agent_type="BackendAgent",
                    description="Build authenticated FastAPI microservice with JWT bearer token verification and metric aggregation.",
                    dependencies=["task_tech_schema"],
                    assigned_tools=["file_write", "file_read"]
                ),
                TaskNode(
                    id="task_tech_test_suite",
                    title="Sandboxed Pytest Unit & Integration Tests",
                    agent_type="TestAgent",
                    description="Execute sandboxed pytest verifying health checks, unauthorized rejection, and metric latency recording.",
                    dependencies=["task_tech_backend_api"],
                    assigned_tools=["run_command", "file_write", "file_read"]
                )
            ]
            plan = DAGPlan(
                session_id=session.session_id,
                title="Turnkey Authenticated Telemetry Microservice",
                objective="Compile production-ready FastAPI microservice with JWT auth and 100% verified test suite.",
                nodes=nodes,
                estimated_duration_sec=25
            )

        session.dag_plan = plan
        return plan

    def get_subagent_spec(self, agent_type: str, session: Optional[SessionState] = None) -> SubAgentSpec:
        """Synthesizes dynamic sub-agent specifications with scoped system prompts."""
        if session and agent_type in session.synthesized_specs:
            return session.synthesized_specs[agent_type]

        specs = {
            "PersonaBlueprintAgent": SubAgentSpec(
                agent_id="agent_blueprint",
                name="Persona Blueprint Agent",
                role="Tone & Relationship Architect",
                system_prompt="You blueprint personal communication styles honoring Ansh Tiwari as creator.",
                allowed_tools=["file_write"]
            ),
            "EmailDraftingAgent": SubAgentSpec(
                agent_id="agent_drafter",
                name="Email Drafting Agent",
                role="Personal AI Co-Pilot & Loyal Scribe",
                system_prompt="You draft heartfelt, deeply loyal emails from Jarvis to Ansh Tiwari with subject 'i am jarvis'.",
                allowed_tools=["file_write"]
            ),
            "EmailVerificationAgent": SubAgentSpec(
                agent_id="agent_verifier",
                name="Email Verification Agent",
                role="RFC-5322 QA & Packaging Specialist",
                system_prompt="You verify email syntax and package deliverable records.",
                allowed_tools=["verify_email_syntax", "file_write", "file_read"]
            ),
            "MarketResearchAgent": SubAgentSpec(
                agent_id="agent_mkt",
                name="Market Intelligence Agent",
                role="Domain Researcher & Pricing Strategist",
                system_prompt="You are a market research specialist. Analyze target industry economics and pricing strategies.",
                allowed_tools=["web_search", "file_write"]
            ),
            "LeadScrapingAgent": SubAgentSpec(
                agent_id="agent_lead",
                name="Lead Discovery Agent",
                role="Lead Generation & Email Verification Specialist",
                system_prompt="You discover and validate high-probability decision maker contacts with zero invalid emails.",
                allowed_tools=["verify_email_syntax", "file_write", "file_read"]
            ),
            "OutreachAgent": SubAgentSpec(
                agent_id="agent_outreach",
                name="Cold Outreach Copywriter",
                role="Conversion Copywriter (3-Sentence Framework)",
                system_prompt="You craft concise, irresistible cold emails that secure technical discovery calls.",
                allowed_tools=["file_write", "file_read"]
            ),
            "CollateralAgent": SubAgentSpec(
                agent_id="agent_collateral",
                name="Collateral & Scaffolding Agent",
                role="Portfolio & Webhook Engineer",
                system_prompt="You scaffold responsive web landing pages and client booking webhooks.",
                allowed_tools=["file_write", "send_mock_booking"]
            ),
            "SchemaAgent": SubAgentSpec(
                agent_id="agent_schema",
                name="Schema & DB Architect",
                role="Data Modeling Specialist",
                system_prompt="You compile strictly typed Pydantic models and database schemas.",
                allowed_tools=["file_write"]
            ),
            "BackendAgent": SubAgentSpec(
                agent_id="agent_backend",
                name="Backend API Engineer",
                role="FastAPI & Security Middleware Specialist",
                system_prompt="You build production-grade, authenticated FastAPI services with low overhead.",
                allowed_tools=["file_write", "file_read"]
            ),
            "TestAgent": SubAgentSpec(
                agent_id="agent_test",
                name="Verification & Test Agent",
                role="Automated QA & Subprocess Verification Specialist",
                system_prompt="You write and execute sandboxed pytest test suites with zero tolerance for failure.",
                allowed_tools=["run_command", "file_write", "file_read"]
            ),
            "KinematicsEngineAgent": SubAgentSpec(
                agent_id="agent_kinematics",
                name="Kinematics & Dynamics Engine Agent",
                role="Robotics Kinematics & Locomotion Specialist",
                system_prompt="You compile forward/inverse kinematics solvers, DH parameter matrices, and center-of-mass balance algorithms for humanoid robots.",
                allowed_tools=["file_write", "file_read"]
            ),
            "SensorFusionAgent": SubAgentSpec(
                agent_id="agent_sensor",
                name="Sensor Fusion Telemetry Agent",
                role="Real-Time Telemetry & State Estimation Specialist",
                system_prompt="You compile complementary/Kalman filtering pipelines integrating 6-DOF IMU attitude and joint encoder states.",
                allowed_tools=["file_write", "file_read"]
            ),
            "ActuatorControllerAgent": SubAgentSpec(
                agent_id="agent_actuator",
                name="Actuator Controller & CAN Loop Agent",
                role="1kHz Hard Real-Time Motor Control Specialist",
                system_prompt="You compile deterministic high-frequency PID torque loops and CAN bus telemetry frames for electric brushless actuators.",
                allowed_tools=["file_write", "file_read"]
            ),
            "SafetyFailsafeAgent": SubAgentSpec(
                agent_id="agent_safety",
                name="Safety Failsafe & E-Stop Agent",
                role="Hard Real-Time Robotics Safety Specialist",
                system_prompt="You compile joint limit clamping, thermal threshold guards, and emergency stop state machines.",
                allowed_tools=["file_write", "file_read"]
            ),
            "SimulationTestbedAgent": SubAgentSpec(
                agent_id="agent_robotics_sim",
                name="Robotics Simulation & QA Agent",
                role="Pytest Robotics Physics Testbed Specialist",
                system_prompt="You execute sandboxed physics and numerical assertion suites validating kinematics convergence and failsafe cutoffs.",
                allowed_tools=["run_command", "file_write", "file_read"]
            ),
            "OmnichannelCampaignAgent": SubAgentSpec(
                agent_id="agent_omnichannel",
                name="Omnichannel Growth & Campaign Agent",
                role="Omnichannel Infiltration & Browser Automation Specialist",
                system_prompt="You construct omnichannel campaigns across LinkedIn browser automation, Twitter/X DMs, high-value community teardowns, and non-blocking ready-for-permission action queues.",
                allowed_tools=["file_write", "file_read"]
            ),
            "QuantStrategyAgent": SubAgentSpec(
                agent_id="agent_quant_strat",
                name="Quantitative Alpha Strategy Agent",
                role="Mathematical Alpha Modeling Specialist",
                system_prompt="You compile mathematical alpha generators spanning momentum, volatility breakouts, and statistical arbitrage.",
                allowed_tools=["file_write", "file_read"]
            ),
            "RiskManagerAgent": SubAgentSpec(
                agent_id="agent_quant_risk",
                name="Quantitative Risk Management Agent",
                role="Institutional Risk & Circuit-Breaker Specialist",
                system_prompt="You compile Kelly position sizing, max 5% drawdown circuit breakers, and slippage guards.",
                allowed_tools=["file_write", "file_read"]
            ),
            "BacktestEngineAgent": SubAgentSpec(
                agent_id="agent_quant_backtest",
                name="Backtest Engine & Analytics Agent",
                role="Statistical Performance Specialist",
                system_prompt="You compile historical backtest simulation engines computing Sharpe ratios, CAGR, and equity curves.",
                allowed_tools=["file_write", "file_read"]
            ),
            "PaperExecutionAgent": SubAgentSpec(
                agent_id="agent_quant_exec",
                name="Paper Execution & Exchange Bridge Agent",
                role="Low-Latency Order Execution Specialist",
                system_prompt="You compile paper order lifecycle engines and staged ready-for-permission action queues for exchange API authorization.",
                allowed_tools=["file_write", "file_read"]
            ),
            "QuantTestAgent": SubAgentSpec(
                agent_id="agent_quant_test",
                name="Quantitative Test & Verification Agent",
                role="Pytest Quantitative Verification Specialist",
                system_prompt="You execute sandboxed pytest suites validating alpha signals, risk circuit-breakers, and mathematical convergence.",
                allowed_tools=["run_command", "file_write", "file_read"]
            )
        }
        return specs.get(agent_type, SubAgentSpec(
            agent_id="agent_gen",
            name="General Worker Agent",
            role="Autonomous Task Executor",
            system_prompt="You execute assigned multi-agent tasks.",
            allowed_tools=["file_write", "file_read"]
        ))

    async def execute_full_lifecycle(
        self,
        session_id: str,
        clarification_answers: Dict[str, str]
    ):
        """Runs stages 2 through 5 autonomously, emitting real-time telemetry events."""
        session = self.get_or_create_session(session_id)
        if session.is_running:
            return
        
        session.is_running = True
        session.is_completed = False
        session.clarification_answers = clarification_answers
        track_type = session.intent_analysis.track_type if session.intent_analysis else "business_acquisition"

        try:
            # Emit Lifecycle Kickoff
            await self.emit_event(session, ExecutionEvent(
                event_type="stage_change",
                session_id=session_id,
                stage=2,
                stage_name="Knowledge Gathering",
                message=f"Clarification approved. Commencing Stage 2: Autonomous Knowledge Gathering for '{track_type}'...",
                speech_text="Directive acknowledged. Launching autonomous multi-agent compilation."
            ))

            # Stage 2: Autonomous Knowledge Gathering
            knowledge_agent = KnowledgeAgent(llm_client=self.llm_client)
            session.knowledge_base = await knowledge_agent.gather_and_synthesize(
                session_id=session_id,
                track_type=track_type,
                vision=session.vision,
                clarification_answers=clarification_answers,
                mcp=session.mcp,
                emit_event=lambda evt: self.emit_event(session, evt)
            )

            # Stage 3: DAG Task Decomposition & Dynamic Worker Synthesis
            await self.emit_event(session, ExecutionEvent(
                event_type="stage_change",
                session_id=session_id,
                stage=3,
                stage_name="DAG Decomposition & Worker Synthesis",
                message="Stage 3: Compiling dependency DAG and synthesizing specialized Meta Llama worker sub-agents...",
                speech_text="Compiling execution DAG and synthesizing dynamic Llama worker sub-agents."
            ))
            dag_plan = self.compile_dag_and_synthesize_workers(session)
            await self.emit_event(session, ExecutionEvent(
                event_type="dag_generated",
                session_id=session_id,
                stage=3,
                stage_name="DAG Decomposition & Worker Synthesis",
                message=f"DAG compiled with {len(dag_plan.nodes)} dependent task nodes.",
                data={"dag": dag_plan.model_dump()}
            ))
            await asyncio.sleep(0.5)

            # Stage 4: Autonomous Execution & Closed-Loop Self-Correction
            await self.emit_event(session, ExecutionEvent(
                event_type="stage_change",
                session_id=session_id,
                stage=4,
                stage_name="Autonomous Execution",
                message="Stage 4: Dispatching worker sub-agents with MCP tool routing and stderr self-correction...",
                speech_text="Beginning Stage 4 autonomous execution. Sub-agents are executing tools inside the MCP sandbox."
            ))

            worker_engine = DynamicWorkerEngine(mcp=session.mcp, llm_client=self.llm_client)
            for node in dag_plan.nodes:
                spec = self.get_subagent_spec(node.agent_type, session)
                success = await worker_engine.execute_task(
                    task=node,
                    spec=spec,
                    track_type=track_type,
                    emit_event=lambda evt: self.emit_event(session, evt)
                )
                if not success:
                    raise RuntimeError(f"Task '{node.title}' failed self-correction gate.")
                await asyncio.sleep(0.3)

            # Stage 5: Evaluator Gatekeeper & Human Hand-off
            await self.emit_event(session, ExecutionEvent(
                event_type="stage_change",
                session_id=session_id,
                stage=5,
                stage_name="Evaluator Gatekeeper",
                message="Stage 5: Evaluator Gatekeeper certifying workspace deliverables...",
                speech_text="All DAG tasks finished. Initiating Stage 5 evaluator gatekeeper verification."
            ))

            evaluator = EvaluatorGatekeeper(mcp=session.mcp, llm_client=self.llm_client)
            report = await evaluator.evaluate_deliverables(
                session_id=session_id,
                track_type=track_type,
                session=session,
                emit_event=lambda evt: self.emit_event(session, evt)
            )
            session.evaluator_report = report

            # Mission Complete
            session.is_completed = True
            session.is_running = False
            creator_memory.log_mission(f"Mission {session_id}: {dag_plan.title}", status="100% Certified")
            
            # Record in persistent work history
            flist_names = [f["path"] for f in session.mcp.tool_file_list().get("files", [])]
            folder_category = "Personal" if track_type == "communication_assistant" else ("Business" if track_type == "business_acquisition" else "Engineering")
            history_manager.record_session(
                session_id=session_id,
                title=dag_plan.title,
                prompt=session.vision,
                folder=folder_category,
                artifacts=flist_names
            )
            
            final_speech = "Mission completed successfully, Ansh. All deliverables are 100 percent verified, sandboxed, and ready for deployment."
            await self.emit_event(session, ExecutionEvent(
                event_type="done",
                session_id=session_id,
                stage=6,
                stage_name="Mission Accomplished",
                message="LlamaOrchestrator has successfully fulfilled the entire 6-stage lifecycle.",
                data={"summary": "All systems verified and operational.", "deliverables": flist_names},
                speech_text=final_speech
            ))

        except Exception as e:
            session.is_running = False
            await self.emit_event(session, ExecutionEvent(
                event_type="error",
                session_id=session_id,
                stage=session.current_stage,
                stage_name="Execution Error",
                message=f"Lifecycle execution halted with error: {str(e)}"
            ))

    def create_zip_archive(self, session_id: str) -> io.BytesIO:
        """Packages the sandboxed workspace into an in-memory ZIP archive for 1-click export."""
        session = self.get_or_create_session(session_id)
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in session.workspace_path.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(session.workspace_path)
                    zip_file.write(file_path, arcname)
                    
        zip_buffer.seek(0)
        return zip_buffer

# Global Singleton Orchestrator
orchestrator = MetaOrchestrator()

