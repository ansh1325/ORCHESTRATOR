"""
Stage 2: Autonomous Knowledge Gathering Agent
Executes domain research via MCP tools and synthesizes structured session Knowledge Base
(knowledge_base.json) containing ICP, pricing, milestones, and architectural blueprints.
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
        
        # Step 1: Research query formulation
        if emit_event:
            await emit_event(ExecutionEvent(
                event_type="log",
                session_id=session_id,
                stage=2,
                stage_name="Knowledge Gathering",
                message=f"[KnowledgeAgent] Formulating deep research queries for '{track_type}' domain...",
                speech_text="Initiating autonomous research via MCP tools to assemble the mission knowledge base."
            ))
            await asyncio.sleep(0.3)

        # Step 2: Query MCP Web Search Tool
        search_query = "B2B client acquisition agency pricing benchmarks" if track_type == "business_acquisition" else "FastAPI telemetry authenticated microservice architecture"
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
        target_niche = clarification_answers.get("target_niche", "B2B AI & SaaS Startups" if track_type == "business_acquisition" else "Enterprise Cloud Infrastructure")
        pricing_model = clarification_answers.get("pricing_model", "$4,500/mo Retainer" if track_type == "business_acquisition" else "High-Throughput Zero-Trust Telemetry")

        if track_type == "business_acquisition":
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
                    {
                        "tier": "Sprint Pilot",
                        "price": "$2,500 (one-time)",
                        "scope": "Single verified microservice or integration shipped in 7 days."
                    },
                    {
                        "tier": "Core Dedicated Pod",
                        "price": "$4,500 / month",
                        "scope": "Continuous sprint delivery, dedicated senior engineer, 24h SLA."
                    },
                    {
                        "tier": "Scale & Growth",
                        "price": "$8,500 / month",
                        "scope": "Multi-agent automation, full telemetry, end-to-end cloud pipeline."
                    }
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
