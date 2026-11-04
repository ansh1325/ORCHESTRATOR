"""
Test Suite: Sales Psychology & Consultative Discovery Framework
Verifies that JARVIS, KnowledgeAgent, VoiceCallAgent, and AccountFleet
strictly enforce the Value-Before-Price Discovery Protocol.

Guarantees:
1. Zero upfront price disclosure on cold email Touch 1.
2. Zero premature pricing on phone call turns 1-2.
3. Consultative Price Shield deflection when prospect asks about price.
4. Structured sales_discovery_playbook across all synthesized Knowledge Bases.
"""

import pytest
import re
from core.models import KnowledgeBase
from core.knowledge_agent import KnowledgeAgent, synthesize_sales_discovery_playbook
from core.voice_call_agent import VoiceAgentPersona, VoiceCallAgentEngine, VoiceCallLead
from core.account_fleet import AccountFleetManager, account_fleet


class TestSalesPsychologyAndPriceProtection:

    def test_synthesize_sales_discovery_playbook_structure(self):
        """Verifies structure of the consultative sales discovery playbook."""
        playbook = synthesize_sales_discovery_playbook(
            niche="Autonomous Drone Delivery",
            pain_points=["manual route dispatch errors", "compliance delays"],
            offer_title="Autonomous Route Engine"
        )
        assert playbook["doctrine"] == "Consultative Value-First Discovery (Zero Upfront Price Dropping)"
        assert "STRICT_PRICE_SHIELD" in playbook["price_protection_rule"]["mandate"]
        assert "Never volunteer or blurt out pricing" in playbook["core_maxim"]
        assert "deflect" in playbook["objection_handling_matrix"]["how_much_is_it"].lower()
        assert len(playbook["cold_discovery_sequence"]) == 4

        # Verify Touch 1 directive
        assert "Zero price tags in Touch 1" in playbook["price_protection_rule"]["early_touch_directive"]

    def test_voice_agent_persona_system_prompt_rules(self):
        """Verifies voice agent system prompt enforces Price Protection Rule."""
        persona = VoiceAgentPersona(creator_name="Ansh Tiwari")
        prompt = persona.synthesize_system_prompt(
            niche="Autonomous Drone Delivery",
            prospect_name="Dr. Marcus Vance",
            company="Apex Healthcare"
        )
        # Must NOT push a flat price in mission objective or rule 3
        assert "flat $2,500 one-time investment" not in prompt
        assert "STRICT PRICE PROTECTION RULE" in prompt
        assert "NEVER volunteer or blurt out price" in prompt
        assert "PRICE SHIELD" in prompt
        assert "Every system is engineered custom" in prompt

    @pytest.mark.asyncio
    async def test_simulated_call_has_zero_early_price_disclosure(self, tmp_path):
        """Verifies cold call simulation turns 1 and 2 contain zero dollar prices."""
        engine = VoiceCallAgentEngine(workspace_dir=tmp_path)
        lead = VoiceCallLead(
            phone="+1555019999",
            name="Dr. Marcus Vance",
            company="Apex Healthcare",
            niche="Autonomous Drone Delivery"
        )
        res = await engine.dispatch_single_call(lead)
        assert res["success"] is True
        assert res["status"] == "BOOKED"
        assert len(lead.transcript) >= 4

        # Turn 1 and Turn 2 from JARVIS must have zero dollar signs or pricing
        jarvis_turns = [t["text"] for t in lead.transcript if "JARVIS" in t["speaker"]]
        assert len(jarvis_turns) >= 2

        turn_1 = jarvis_turns[0]
        turn_2 = jarvis_turns[1]

        assert "$" not in turn_1, f"Turn 1 disclosed pricing: {turn_1}"
        assert "$2,500" not in turn_1
        assert "$" not in turn_2, f"Turn 2 disclosed pricing: {turn_2}"
        assert "$2,500" not in turn_2

        # Verify discovery call booked
        assert "Thursday 2:00 PM EST" in res["booking_slot"] or "PM" in res["booking_slot"]

    def test_account_fleet_touch_1_zero_pricing(self):
        """Verifies cold email Touch 1 contains zero price tags."""
        seq = AccountFleetManager.generate_8_touch_sequence(
            company_niche="Autonomous Robotics & AI Pipelines",
            custom_offer="$2,500 14-day production sprint",
            founder_name="Ansh Tiwari"
        )
        touch_1 = seq[0]
        assert touch_1["touch"] == 1
        body_1 = touch_1["body"]
        assert "$" not in body_1, f"Touch 1 contained price tag: {body_1}"
        assert "$2,500" not in body_1
        assert any(phrase in body_1 for phrase in ["2-minute Loom", "2-minute video", "2‑minute video", "2-minute breakdown", "2‑minute"]), f"Expected 2-minute breakdown in Touch 1, got: {body_1}"

        # Touch 3 introduces the structured sprint
        touch_3 = seq[2]
        assert touch_3["touch"] == 3
        assert "$2,500 14-day production sprint" in touch_3["body"]

    def test_account_fleet_price_inquiry_reply(self, tmp_path):
        """Verifies inbound price inquiry is handled consultatively."""
        fleet = AccountFleetManager(storage_path=tmp_path / "fleet_test.json")
        briefing = fleet.synthesize_autonomous_reply(
            "founder@apexhealth.com",
            "What are your rates and pricing structure?",
            booking_link="https://calendly.com/anshtiwari"
        )
        assert briefing["sentiment_category"] == "PRICE_OBJECTION"
        reply = briefing["automated_response"]
        assert "$2,500" in reply or "discovery" in reply.lower() or "custom" in reply.lower()
        assert "https://calendly.com/anshtiwari" in reply

    def test_knowledge_base_has_sales_discovery_playbook(self):
        """Verifies KnowledgeBase model stores sales_discovery_playbook."""
        playbook = synthesize_sales_discovery_playbook("AI Automation")
        kb = KnowledgeBase(
            session_id="test_sess",
            target_niche="AI Automation",
            icp={"ideal_persona": "CTO"},
            pricing_tiers=[{"tier": "Pilot", "price": "$2,500"}],
            milestone_1="Scaffolding",
            milestone_2="Delivery",
            technical_blueprint={"stack": ["Python"]},
            scraped_sources=[],
            synthesis_summary="Test KB summary",
            sales_discovery_playbook=playbook
        )
        assert kb.sales_discovery_playbook is not None
        assert kb.sales_discovery_playbook["doctrine"] == "Consultative Value-First Discovery (Zero Upfront Price Dropping)"

    @pytest.mark.asyncio
    async def test_cognitive_call_reply_live_reasoning(self):
        """Verifies generate_cognitive_call_reply dynamically adapts to prospect input."""
        engine = VoiceCallAgentEngine()
        lead = VoiceCallLead(
            phone="+1555019999",
            name="Dr. Marcus Vance",
            company="Apex Healthcare",
            niche="Autonomous Drone Delivery"
        )
        persona = VoiceAgentPersona()
        history = [{"speaker": "JARVIS (Voice Agent)", "text": "Did I catch you at an okay time?"}]

        # Test Case 1: Price Inquiry -> Must deflect with Price Shield (Zero price quote)
        price_reply = await engine.generate_cognitive_call_reply(
            lead=lead,
            prospect_utterance="What is your pricing? I need to know the cost right now.",
            conversation_history=history,
            persona=persona
        )
        assert "$" not in price_reply
        assert "$2,500" not in price_reply
        assert "Thursday" in price_reply or "demo" in price_reply.lower() or "prototype" in price_reply.lower()

        # Test Case 2: In-House Software -> Must validate and clarify integration bridge
        software_reply = await engine.generate_cognitive_call_reply(
            lead=lead,
            prospect_utterance="We already have fleet management software in place.",
            conversation_history=history,
            persona=persona
        )
        assert any(w in software_reply.lower() for w in ["integrate", "system", "disrupt", "bridge", "replacement", "software"])

        # Test Case 3: Agreement -> Must confirm booking
        confirm_reply = await engine.generate_cognitive_call_reply(
            lead=lead,
            prospect_utterance="Thursday at 2 PM works for me. Send the invite.",
            conversation_history=history,
            persona=persona
        )
        assert "Thursday" in confirm_reply or "invite" in confirm_reply.lower() or "calendar" in confirm_reply.lower()
