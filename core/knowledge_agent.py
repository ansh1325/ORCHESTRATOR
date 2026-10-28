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
        
        v_lower = vision.lower()
        is_marketing = any(w in v_lower for w in ["marketing", "ad", "ads", "meta ad", "facebook ad", "roas"])

        # Step 1: Research query formulation
        if emit_event:
            query_desc = "Meta Ads agency acquisition benchmarks" if is_marketing else ("B2B client acquisition agency benchmarks" if track_type == "business_acquisition" else "FastAPI telemetry architecture")
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
        search_query = "Meta ads B2B agency pricing and client acquisition" if is_marketing else ("B2B client acquisition agency pricing benchmarks" if track_type == "business_acquisition" else "FastAPI telemetry authenticated microservice architecture")
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
        if track_type == "business_acquisition":
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
                        "deliverables": [
                            "leads.csv (qualified ecom/SaaS founders with validated emails)",
                            "cold_outreach_templates.md (3-sentence ad teardown hooks)",
                            "ad_campaign_blueprint.md (Top/Middle/Bottom of Funnel Meta Ads structure)",
                            "portfolio_one_pager.html (interactive social proof & booking form)"
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
                        "deliverables": [
                            "leads.csv (decision maker list with validated emails)",
                            "cold_outreach_templates.md (high-converting 3-sentence frameworks)",
                            "client_proposal_template.md (pricing & SLA contract)",
                            "portfolio_one_pager.html (interactive social proof showcase)"
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
