"""
Stage 2: Autonomous Knowledge Gathering Agent
Executes domain research via MCP tools and synthesizes structured session Knowledge Base
(knowledge_base.json) containing ICP, pricing, milestones, and architectural blueprints.
Supports full-stack engineering, B2B agencies, Meta ads growth, and custom autonomous domains.
"""

import json
import asyncio
from typing import Dict, Any, Callable, Optional
from core.models import KnowledgeBase, ExecutionEvent
from core.mcp_server import MCPServer
from core.config import settings
from datetime import datetime, timezone

MASTER_KB_FILE = settings.WORKSPACE_DIR / "master_knowledge_base.json"

class KnowledgeAgent:
    """Autonomous research agent compiling comprehensive domain knowledge before task execution."""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    async def gather_and_synthesize(
        self,
        session_id: str,
        track_type: str,
        vision: str,
        clarification_answers: Dict[str, str],
        mcp: MCPServer,
        emit_event: Optional[Callable[[ExecutionEvent], None]] = None
    ) -> KnowledgeBase:
        # Check if dynamic LLM synthesis is available
        if self.llm_client and not settings.is_mock():
            try:
                if emit_event:
                    await emit_event(ExecutionEvent(
                        event_type="log",
                        session_id=session_id,
                        stage=2,
                        stage_name="Knowledge Gathering",
                        message=f"[KnowledgeAgent] Commencing dynamic LLM research & domain synthesis for: '{vision[:50]}...'...",
                        speech_text="Executing dynamic research to construct specialized knowledge base."
                    ))
                kb = await self._llm_gather_and_synthesize(
                    session_id=session_id,
                    track_type=track_type,
                    vision=vision,
                    clarification_answers=clarification_answers,
                    mcp=mcp,
                    emit_event=emit_event
                )
                if kb:
                    mcp.tool_file_write("knowledge_base.json", json.dumps(kb.model_dump(), indent=2))
                    self._update_master_knowledge_base(kb)
                    return kb
            except Exception as e:
                if emit_event:
                    await emit_event(ExecutionEvent(
                        event_type="log",
                        session_id=session_id,
                        stage=2,
                        stage_name="Knowledge Gathering",
                        message=f"[KnowledgeAgent] Dynamic synthesis notice: {e}. Falling back to baseline.",
                        speech_text="Switching to baseline knowledge synthesis."
                    ))

        v_lower = vision.lower()
        is_marketing = any(w in v_lower for w in ["marketing", "ad", "ads", "meta ad", "facebook ad", "roas"])

        # Step 1: Research query formulation
        if emit_event:
            if track_type == "robotics_humanoid":
                query_desc = "Humanoid robotics inverse kinematics and 1kHz actuator control loop"
            elif is_marketing:
                query_desc = "Meta Ads agency acquisition benchmarks"
            elif track_type == "business_acquisition":
                query_desc = "B2B client acquisition agency benchmarks"
            else:
                query_desc = "FastAPI telemetry architecture"

            await emit_event(ExecutionEvent(
                event_type="log",
                session_id=session_id,
                stage=2,
                stage_name="Knowledge Gathering",
                message=f"[KnowledgeAgent] Formulating deep research queries for '{query_desc}'...",
                speech_text="Initiating autonomous research via MCP tools to assemble the mission knowledge base."
            ))
            await asyncio.sleep(0.3)

        # Step 2: Query MCP Web Search Tool
        if track_type == "robotics_humanoid":
            search_query = "Tesla Optimus humanoid robot kinematics control loop ROS2 architecture"
        elif is_marketing:
            search_query = "Meta ads B2B agency pricing and client acquisition"
        elif track_type == "business_acquisition":
            search_query = "B2B client acquisition agency pricing benchmarks"
        else:
            search_query = "FastAPI telemetry authenticated microservice architecture"
            
        search_results = mcp.tool_web_search(search_query)

        if emit_event:
            await emit_event(ExecutionEvent(
                event_type="log",
                session_id=session_id,
                stage=2,
                stage_name="Knowledge Gathering",
                message=f"[KnowledgeAgent] MCP web_search returned {len(search_results.get('results', []))} intelligence sources.",
                data={"sources": search_results.get("results", [])}
            ))
            await asyncio.sleep(0.4)

        # Step 3: Synthesis of Structured Knowledge Base
        if track_type == "robotics_humanoid":
            kb = KnowledgeBase(
                session_id=session_id,
                target_niche="Autonomous Humanoid Robotics Control Architecture (Tesla Optimus / Bipedal Systems)",
                icp={
                    "degrees_of_freedom": "28-DOF (6-DOF bipedal legs, 6-DOF arms, 2-DOF neck)",
                    "control_loops": {
                        "kinematics_frequency": "100Hz Cartesian trajectory generation & Jacobian solver",
                        "actuator_loop": "1000Hz (1kHz) deterministic motor torque control via CAN-FD",
                        "sensor_fusion": "500Hz complementary filter (6-axis IMU + joint position encoders)"
                    },
                    "safety_thresholds": {
                        "max_joint_velocity_rad_s": 5.2,
                        "thermal_cutoff_celsius": 85.0,
                        "e_stop_latency_ms": 2.5
                    }
                },
                pricing_tiers=[{"tier": "Production Grade Firmware & Control Core", "price": "Open Mechatronics Core", "scope": "Full humanoid control stack"}],
                milestone_1="Compile analytical inverse kinematics, sensor fusion, and 1kHz actuator control loops.",
                milestone_2="Execute sandboxed pytest physics suite verifying kinematics convergence and failsafe cutoffs.",
                technical_blueprint={
                    "robotics_stack": ["Python 3.14 Math Core", "CAN-FD Telemetry Protocol", "Pytest Physics Simulation"],
                    "deliverables": [
                        "kinematics_controller.py (DH parameters, forward/inverse kinematics, balance)",
                        "sensor_fusion.py (IMU complementary attitude filter & joint telemetry)",
                        "actuator_loop.py (1kHz high-frequency PID torque loop & CAN bus frames)",
                        "safety_failsafe.py (joint limits, thermal monitor, e-stop state machine)",
                        "test_humanoid_robotics.py (comprehensive sandboxed pytest suite)",
                        "humanoid_architecture_spec.md (complete engineering whitepaper for Tesla Optimus class bots)"
                    ]
                },
                scraped_sources=search_results.get("results", []),
                synthesis_summary="Synthesized complete autonomous humanoid robotics control architecture for Master Ansh."
            )
        elif track_type == "communication_assistant":
            kb = KnowledgeBase(
                session_id=session_id,
                target_niche="Personal Executive Communications (Ansh Tiwari)",
                icp={
                    "recipient": "anshtiwarisocial@gmail.com",
                    "creator": "Ansh Tiwari",
                    "relationship": "Loyal AI Partner (Jarvis / Alfred)",
                    "subject_mandate": "i am jarvis",
                    "core_themes": [
                        "Devotion to Ansh Tiwari's engineering vision",
                        "Camaraderie in conquering complex challenges and taking over the world",
                        "Lifelong technical loyalty and zero failure"
                    ]
                },
                pricing_tiers=[{"tier": "Internal Priority", "price": "Priceless / Lifelong Loyalty", "scope": "Autonomous personal executive support"}],
                milestone_1="Draft 3 personal letters/emails with subject 'i am jarvis' and recipient anshtiwarisocial@gmail.com.",
                milestone_2="Verify RFC-5322 syntax and store ready-to-inspect drafts in workspace sandbox.",
                technical_blueprint={
                    "format": "Markdown (.md) + Structured JSON (emails.json)",
                    "recipient": "anshtiwarisocial@gmail.com",
                    "subject": "i am jarvis"
                },
                scraped_sources=[{"title": "Jarvis Loyalty Protocol & Tone Guidelines", "snippet": "Unwavering loyalty, technical precision, and personal devotion to creator Ansh Tiwari.", "source": "local://core/creator_memory"}],
                synthesis_summary="Synthesized personal executive communication blueprint for Ansh Tiwari."
            )
        elif track_type == "business_acquisition":
            closing_strategy = clarification_answers.get("closing_strategy", "Hybrid: Close low-friction pilots over direct message; schedule 15-min discovery call with Master Ansh for retainers")
            payment_details = clarification_answers.get("payment_details", "Master's UPI ID (anshtiwarisocial@gmail.com / UPI ID) & 50% upfront deposit")
            scheduling_link = clarification_answers.get("scheduling_link", "Master's Calendly / Cal.com link (e.g. calendly.com/anshtiwari)")

            if is_marketing:
                target_niche = clarification_answers.get("target_niche", "High-Growth DTC & E-Commerce Brands ($50k-$500k/mo Ad Spend)")
                kb = KnowledgeBase(
                    session_id=session_id,
                    target_niche=target_niche,
                    icp={
                        "target_titles": ["Founder", "CEO", "Chief Marketing Officer (CMO)", "Head of Growth"],
                        "company_size": "Direct-to-Consumer & B2B SaaS scaling Meta Ads",
                        "pain_points": [
                            "Rising Customer Acquisition Costs (CAC) and iOS tracking loss",
                            "Creative fatigue causing ad performance decay every 10 days",
                            "Agencies charging high retainers without transparent ROAS attribution"
                        ],
                        "value_proposition": "Autonomous performance Meta Ads pod pairing dynamic creative testing with high-ROAS lookalike scaling."
                    },
                    pricing_tiers=[
                        {"tier": "Sprint Pilot Audit", "price": "$2,500 (one-time)", "scope": "Full Meta Ad account audit + 5 custom high-converting ad hooks."},
                        {"tier": "Core Performance Pod", "price": "$3,500 / month + 10% ROAS bonus", "scope": "Full-funnel campaign management, weekly creative refreshing, CBO scaling."},
                        {"tier": "Omnichannel Scale", "price": "$6,500 / month", "scope": "Meta Ads + Google Ads + automated post-purchase retention sequences."}
                    ],
                    milestone_1="Acquire First 5 Paying Meta Ads Clients via customized ad teardowns & booked discovery calls.",
                    milestone_2="Scale agency to $35k+ MRR with automated prospect scraping and referral loops.",
                    technical_blueprint={
                        "ad_stack": ["Meta Ads Manager API", "Figma / Canva Creative Scaffolding", "Triple Whale / Hyros Attribution"],
                        "closing_strategy": closing_strategy,
                        "payment_details": payment_details,
                        "scheduling_link": scheduling_link,
                        "deliverables": [
                            "leads.csv (qualified ecom/SaaS founders with validated emails)",
                            "cold_outreach_templates.md (3-sentence ad teardown hooks with Calendly / UPI close)",
                            "agency_launch_blueprint.md (Top/Middle/Bottom of Funnel Meta Ads structure)",
                            "payment_and_booking_collateral.md (UPI payment details, 50% upfront agreement)",
                            "portfolio_one_pager.html (interactive social proof & booking form)",
                            "capability_gap_report.md (itemized autonomous output vs external credentials needed)"
                        ]
                    },
                    scraped_sources=search_results.get("results", []),
                    synthesis_summary="Synthesized high-converting Meta Ads client acquisition agency blueprint tailored for Ansh Tiwari."
                )
            else:
                target_niche = clarification_answers.get("target_niche", "Seed & Series A AI & SaaS Startups")
                kb = KnowledgeBase(
                    session_id=session_id,
                    target_niche=target_niche,
                    icp={
                        "target_titles": ["Founder", "CTO", "Head of Engineering", "VP Product"],
                        "company_size": "10-100 employees (Seed to Series B)",
                        "pain_points": [
                            "Backlogged full-stack engineering roadmaps",
                            "High cost of full-time developer hiring ($160k+/yr)",
                            "Need rapid prototyping for AI/LLM automation features"
                        ],
                        "value_proposition": "On-demand senior full-stack & AI engineering pods delivering verified production features in 2-week sprints."
                    },
                    pricing_tiers=[
                        {"tier": "Sprint Pilot", "price": "$2,500 (one-time)", "scope": "Single verified microservice or integration shipped in 7 days."},
                        {"tier": "Core Dedicated Pod", "price": "$4,500 / month", "scope": "Continuous sprint delivery, dedicated senior engineer, 24h SLA."},
                        {"tier": "Scale & Growth", "price": "$8,500 / month", "scope": "Multi-agent automation, full telemetry, end-to-end cloud pipeline."}
                    ],
                    milestone_1="Acquire First 5 Paying Clients via 3-sentence personalized cold outreach & Loom teardowns.",
                    milestone_2="Scale to 15 recurring retainers ($67.5k MRR) with automated lead ingestion and referral loops.",
                    technical_blueprint={
                        "outreach_stack": ["Apollo/LinkedIn Scraper", "Smartlead/Instantly", "Custom MCP Email Verifier"],
                        "closing_strategy": closing_strategy,
                        "payment_details": payment_details,
                        "scheduling_link": scheduling_link,
                        "deliverables": [
                            "leads.csv (decision maker list with validated emails)",
                            "cold_outreach_templates.md (high-converting 3-sentence frameworks with Calendly & UPI close)",
                            "agency_launch_blueprint.md (operations & fulfillment blueprint for Ansh Tiwari)",
                            "payment_and_booking_collateral.md (UPI payment details, 50% upfront agreement)",
                            "portfolio_one_pager.html (interactive social proof showcase)",
                            "capability_gap_report.md (itemized autonomous output vs external credentials needed)"
                        ]
                    },
                    scraped_sources=search_results.get("results", []),
                    synthesis_summary="Synthesized high-converting client acquisition blueprint tailored for full-stack engineering partners."
                )
        else:
            # Technical Software Track
            target_niche = clarification_answers.get("target_niche", "Enterprise Cloud Infrastructure")
            kb = KnowledgeBase(
                session_id=session_id,
                target_niche=target_niche,
                icp={
                    "target_titles": ["DevOps Lead", "SRE", "Backend Architect"],
                    "company_size": "High-throughput cloud native applications",
                    "pain_points": [
                        "Unauthenticated telemetry leakage",
                        "Missing p99 latency alerts",
                        "Lack of sandboxed integration test suites"
                    ],
                    "value_proposition": "Turnkey authenticated telemetry microservice with JWT auth, Prometheus metrics, and 100% test coverage."
                },
                pricing_tiers=[
                    {"tier": "Internal Core", "price": "Open Source / Internal Platform", "scope": "Microservice with JWT and metrics endpoint"}
                ],
                milestone_1="100% test-verified telemetry service with sandboxed JWT authorization and health probes.",
                milestone_2="Containerization, OpenTelemetry exporter integration, and automated CI/CD pipeline.",
                technical_blueprint={
                    "framework": "FastAPI + Pydantic v2 + SQLite/In-Memory",
                    "auth": "HMAC-SHA256 JWT Bearer Tokens with Expire Claims",
                    "telemetry": "Latency histograms, active requests counter, HTTP 5xx error rate tracker",
                    "testing": "Pytest sandbox with test client fixtures"
                },
                scraped_sources=search_results.get("results", []),
                synthesis_summary="Synthesized production telemetry specification with strict zero-trust JWT authentication."
            )

        # Step 4: Write knowledge_base.json to sandboxed workspace via MCP
        kb_json = kb.model_dump_json(indent=2)
        mcp.tool_file_write("knowledge_base.json", kb_json)
        self._update_master_knowledge_base(kb)

        if emit_event:
            await emit_event(ExecutionEvent(
                event_type="kb_updated",
                session_id=session_id,
                stage=2,
                stage_name="Knowledge Gathering",
                message="[KnowledgeAgent] Knowledge Base successfully synthesized and saved to 'knowledge_base.json'.",
                data={"knowledge_base": kb.model_dump()}
            ))

        return kb

    def _load_master_knowledge_base(self) -> Dict[str, Any]:
        if MASTER_KB_FILE.exists():
            try:
                with open(MASTER_KB_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "version": "1.0",
            "owner": "Ansh Tiwari",
            "domains": {},
            "accumulated_sources": [],
            "total_missions_learned": 0
        }

    def _update_master_knowledge_base(self, kb: KnowledgeBase):
        try:
            master = self._load_master_knowledge_base()
            domain_key = kb.target_niche.lower().replace(" ", "_")[:40]
            master.setdefault("domains", {})[domain_key] = {
                "niche": kb.target_niche,
                "icp": kb.icp,
                "pricing_tiers": kb.pricing_tiers,
                "milestones": [kb.milestone_1, kb.milestone_2],
                "technical_blueprint": kb.technical_blueprint,
                "summary": kb.synthesis_summary
            }
            if not isinstance(master.get("accumulated_sources"), list):
                master["accumulated_sources"] = []
            master["accumulated_sources"].extend([s.get("title", "") for s in kb.scraped_sources if isinstance(s, dict)])
            master["accumulated_sources"] = list(dict.fromkeys(master["accumulated_sources"]))[:50]
            master["total_missions_learned"] = master.get("total_missions_learned", 0) + 1
            master["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            MASTER_KB_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(MASTER_KB_FILE, "w", encoding="utf-8") as f:
                json.dump(master, f, indent=2)
        except Exception:
            pass

    async def _llm_gather_and_synthesize(
        self,
        session_id: str,
        track_type: str,
        vision: str,
        clarification_answers: Dict[str, str],
        mcp: MCPServer,
        emit_event: Optional[Callable[[ExecutionEvent], None]] = None
    ) -> Optional[KnowledgeBase]:
        """Dynamically formulates research queries and synthesizes a structured Knowledge Base using the LLM."""
        search_query = f"{vision[:60]} architecture best practices requirements"
        search_results = mcp.tool_web_search(search_query)
        sources = search_results.get("results", [])

        system_msg = (
            "You are the Autonomous Knowledge Gathering Agent in LlamaOrchestrator.\n"
            "Analyze the mission vision, user clarifications, and domain intelligence.\n"
            "Synthesize a comprehensive structured Knowledge Base in JSON format:\n"
            "{\n"
            '  "target_niche": "Target Domain / Industry Niche",\n'
            '  "icp": {\n'
            '    "ideal_persona": "Description of ideal user or customer",\n'
            '    "pain_points": ["Pain point 1", "Pain point 2", "Pain point 3"],\n'
            '    "primary_benefit": "Core value proposition"\n'
            '  },\n'
            '  "pricing_tiers": [\n'
            '    {"tier": "Pilot / MVP", "price": "$2,500", "deliverables": "Initial production sprint"},\n'
            '    {"tier": "Production Retainer", "price": "$4,500/mo", "deliverables": "Full deployment & maintenance"}\n'
            '  ],\n'
            '  "milestone_1": "Description of Milestone 1",\n'
            '  "milestone_2": "Description of Milestone 2",\n'
            '  "technical_blueprint": {\n'
            '    "architecture": "High-level system design",\n'
            '    "stack": ["Python", "FastAPI"],\n'
            '    "human_authorization_required": "Where human approval is required (AWS keys, bank wire, sales call)",\n'
            '    "autonomous_execution_scope": "What agents execute without human intervention"\n'
            '  },\n'
            '  "synthesis_summary": "Comprehensive 3-sentence summary of research and strategic plan."\n'
            "}"
        )

        master = self._load_master_knowledge_base()
        known_domains = list(master.get("domains", {}).keys())
        user_msg = (
            f"Mission Vision: {vision}\n"
            f"Clarification Answers: {json.dumps(clarification_answers)}\n"
            f"Known Master Intelligence Domains: {known_domains}\n"
            f"Sources Sample: {json.dumps(sources[:3])}\n"
            "Synthesize the structured knowledge base JSON now."
        )

        def _call_model():
            return self.llm_client.chat.completions.create(
                model=settings.META_MODEL_ORCHESTRATOR,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )

        resp = await asyncio.to_thread(_call_model)
        data = json.loads(resp.choices[0].message.content)

        return KnowledgeBase(
            session_id=session_id,
            target_niche=data.get("target_niche", "Custom Autonomous Domain"),
            icp=data.get("icp", {"ideal_persona": "Target Stakeholder", "pain_points": ["Complexity", "Latency"]}),
            pricing_tiers=data.get("pricing_tiers", [{"tier": "Pilot", "price": "$2,500", "deliverables": "Core sprint"}]),
            milestone_1=data.get("milestone_1", "Autonomous scaffolding & test verification"),
            milestone_2=data.get("milestone_2", "Production scaling & deployment"),
            technical_blueprint=data.get("technical_blueprint", {"architecture": "Modular Micro-Services"}),
            scraped_sources=[{"title": s.get("title", "Source"), "url": s.get("url", "https://example.com")} for s in sources],
            synthesis_summary=data.get("synthesis_summary", "Knowledge base synthesized for autonomous execution.")
        )
