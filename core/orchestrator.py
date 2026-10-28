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
            "artifacts": artifacts or []
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
        self.knowledge_base: Optional[KnowledgeBase] = None
        self.dag_plan: Optional[DAGPlan] = None
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

    def analyze_intent(self, vision: str, session_id: Optional[str] = None) -> IntentAnalysis:
        """Stage 1: Intent Analysis & Human Clarification Gate."""
        session = self.get_or_create_session(session_id, vision)
        v_lower = vision.lower()

        # Classify Track
        if any(w in v_lower for w in ["mail", "email", "gmail", "letter", "message", "write to", "send to"]):
            track_type = "communication_assistant"
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
        elif any(w in v_lower for w in ["business", "client", "acquisition", "agency", "freelance", "sales"]):
            track_type = "business_acquisition"
            extracted_goals = [
                "Establish a high-ticket B2B software engineering agency",
                "Acquire first 5 paying clients ($2,500 - $4,500/mo)",
                "Automate prospect scraping & personalized 3-sentence outreach"
            ]
            identified_constraints = [
                "High cold email conversion requirement",
                "Fast 7-day turnaround for client pilot projects",
                "Sandboxed verification of leads before outbound dispatch"
            ]
            missing_parameters = ["Target industry niche", "Pricing retainer model", "Outbound channel preference"]
            clarifications = [
                ClarificationQuestion(
                    id="target_niche",
                    question="Which industry niche should we target for immediate high-ticket client acquisition?",
                    why_needed="Focuses cold outreach copy on exact technical pain points and engineering bottlenecks.",
                    options=["Seed & Series A AI/SaaS Startups", "Healthcare & MedTech Platforms", "Fintech & Web3 Infrastructure"],
                    default_selection="Seed & Series A AI/SaaS Startups"
                ),
                ClarificationQuestion(
                    id="pricing_model",
                    question="What pricing and offer structure should we scaffold for your first 5 clients?",
                    why_needed="Ensures immediate cashflow while de-risking the engagement for prospective founders.",
                    options=["$2,500 Pilot Sprint + $4,500/mo Retainer", "Pure Equity & Rev-Share", "Hourly Billing ($150/hr)"],
                    default_selection="$2,500 Pilot Sprint + $4,500/mo Retainer"
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
                "outbound_angle": "Rapid 7-Day Sprint Delivery (Zero Hiring Overhead)"
            }
        else:
            track_type = "technical_software"
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
            raw_vision=vision,
            extracted_goals=extracted_goals,
            identified_constraints=identified_constraints,
            missing_parameters=missing_parameters,
            clarifications=clarifications,
            recommended_defaults=recommended_defaults
        )
        session.intent_analysis = analysis
        return analysis

    def compile_dag_and_synthesize_workers(self, session: SessionState) -> DAGPlan:
        """Stage 3: DAG Task Decomposition & Dynamic Worker Synthesis."""
        analysis = session.intent_analysis
        track = analysis.track_type if analysis else "technical_software"

        if track == "communication_assistant":
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
        elif track == "business_acquisition":
            nodes = [
                TaskNode(
                    id="task_biz_market_research",
                    title="Market Niche & Pricing Intelligence",
                    agent_type="MarketResearchAgent",
                    description="Analyze B2B target persona, contract values, and conversion levers.",
                    dependencies=[],
                    assigned_tools=["web_search", "file_write"]
                ),
                TaskNode(
                    id="task_biz_lead_scraping",
                    title="Lead Discovery & Syntax Verification",
                    agent_type="LeadScrapingAgent",
                    description="Scrape and validate decision-maker leads (CEO/CTO) with verified RFC-5322 emails.",
                    dependencies=["task_biz_market_research"],
                    assigned_tools=["verify_email_syntax", "file_write", "file_read"]
                ),
                TaskNode(
                    id="task_biz_cold_outreach",
                    title="High-Converting 3-Sentence Outreach Synthesis",
                    agent_type="OutreachAgent",
                    description="Synthesize ultra-short, high-converting cold email sequences tailored to engineering founders.",
                    dependencies=["task_biz_lead_scraping"],
                    assigned_tools=["file_write", "file_read"]
                ),
                TaskNode(
                    id="task_biz_collateral",
                    title="Agency Portfolio & Sprint Proposal Scaffolding",
                    agent_type="CollateralAgent",
                    description="Scaffold responsive portfolio landing page and pilot sprint contract.",
                    dependencies=["task_biz_cold_outreach"],
                    assigned_tools=["file_write", "send_mock_booking"]
                )
            ]
            plan = DAGPlan(
                session_id=session.session_id,
                title="Autonomous B2B Agency & Client Acquisition Pipeline",
                objective="Compile a turnkey client acquisition business for Ansh Tiwari with verified leads and high-converting outreach.",
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

    def get_subagent_spec(self, agent_type: str) -> SubAgentSpec:
        """Synthesizes dynamic sub-agent specifications with scoped system prompts."""
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
                spec = self.get_subagent_spec(node.agent_type)
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

            evaluator = EvaluatorGatekeeper(mcp=session.mcp)
            report = await evaluator.evaluate_deliverables(
                session_id=session_id,
                track_type=track_type,
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
                data={"summary": "All systems verified and operational."},
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

