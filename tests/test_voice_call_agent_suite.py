"""
Test Suite: JARVIS Autonomous Voice Calling Agent Engine
==========================================================
Verifies autonomous voice call dispatch, 5-dial retry cadences, objection handling,
automatic calendar booking, MCP server tool registration (66 tools total),
and Central Brain autonomous inference for high-ticket agency sales buildouts.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from core.voice_call_agent import VoiceCallAgentEngine, VoiceCallLead, VoiceAgentPersona, voice_call_engine
from core.mcp_server import MCPServer
from jarvis_cli import JarvisCLI


class TestVoiceCallAgent:
    def test_voice_call_doctor(self):
        """Verifies doctor diagnostics for telephony providers and calendar integration."""
        doc = voice_call_engine.doctor()
        assert doc["status"] == "ONLINE"
        assert "active_telephony_provider" in doc
        assert "calendly_booking_url" in doc
        assert "https://calendly.com/anshtiwari" in doc["calendly_booking_url"]
        assert doc["voice_calling_online"] is True
        assert doc.get("google_voice_supported") is True
        assert doc.get("whatsapp_calling_supported") is True
        assert "google_voice" in doc.get("supported_providers", [])
        assert "whatsapp" in doc.get("supported_providers", [])

    @pytest.mark.asyncio
    async def test_dispatch_single_call_google_voice(self):
        """Verifies outbound call dispatch via Google Voice Browser Bridge."""
        from core.browser_controller import BrowserController
        lead = VoiceCallLead(
            phone="+1 (555) 019-9201",
            name="Sarah Jenkins",
            company="Summit Logistics",
            niche="Logistics"
        )
        with patch.object(BrowserController, "open_in_system_browser", return_value=True) as mock_launch:
            res = await voice_call_engine.dispatch_single_call(lead, provider="google_voice")
            assert res["success"] is True
            assert res["provider"] == "google_voice"
            assert res["status"] == "initiated"
            assert "voice.google.com" in res["url"]
            assert "+15550199201" in res["phone"] or "5550199201" in res["phone"]
            assert res["browser_launched"] is True
            mock_launch.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_single_call_whatsapp(self):
        """Verifies outbound call dispatch via WhatsApp Web VoIP Bridge."""
        from core.browser_controller import BrowserController
        lead = VoiceCallLead(
            phone="+1 (555) 019-9202",
            name="Marcus Vance",
            company="BlueWater Solar",
            niche="Solar Energy"
        )
        with patch.object(BrowserController, "open_in_system_browser", return_value=True) as mock_launch:
            res = await voice_call_engine.dispatch_single_call(lead, provider="whatsapp")
            assert res["success"] is True
            assert res["provider"] == "whatsapp"
            assert res["status"] == "initiated"
            assert "web.whatsapp.com" in res["url"]
            assert "15550199202" in res["phone"]
            assert res["browser_launched"] is True
            mock_launch.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_single_call_simulation(self):
        """Verifies multi-turn conversational cold call simulation with objection handling and booking close."""
        lead = VoiceCallLead(
            phone="+1555019920",
            name="Dr. David Miller",
            company="Apex Dental Care",
            niche="Dental Clinics"
        )
        res = await voice_call_engine.dispatch_single_call(lead)
        assert res["success"] is True
        assert res["status"] == "BOOKED"
        assert res["booking_slot"] is not None
        assert lead.attempts == 1
        assert len(lead.transcript) >= 4
        assert "Thursday" in res["booking_slot"] or "PM" in res["booking_slot"]

    @pytest.mark.asyncio
    async def test_execute_cold_call_campaign(self, tmp_path):
        """Verifies high-velocity cold call campaign replicating $10k math (4 closes @ $2,500)."""
        engine = VoiceCallAgentEngine(workspace_dir=tmp_path)
        sample_leads = [
            {"phone": "+15550101", "name": "Sarah", "company": "Summit Logistics"},
            {"phone": "+15550102", "name": "Marcus", "company": "BlueWater Solar"},
            {"phone": "+15550103", "name": "Jake", "company": "Titan Construction"}
        ]
        res = await engine.execute_cold_call_campaign(
            niche="Logistics & Construction",
            total_leads_count=3,
            offer_price=2500,
            target_revenue=10000,
            leads_data=sample_leads
        )
        assert res["status"] == "COMPLETED"
        assert res["total_dials_executed"] >= 3
        assert res["calls_booked_count"] >= 1
        assert len(res["booked_discovery_calls"]) >= 1
        assert res["unit_price"] == "$2,500"
        assert "$10,000" in res["target_revenue"]

        # Verify saved in campaign ledger
        camps = engine.list_campaigns()
        assert len(camps) >= 1
        assert camps[0]["campaign_id"] == res["campaign_id"]


class TestMCPVoiceCallTools:
    def test_mcp_voice_call_tool_definitions(self, tmp_path):
        """Verifies all 4 voice calling tools are registered in MCP server (total 66 tools)."""
        server = MCPServer(workspace_path=tmp_path)
        defs = server.get_tool_definitions()
        names = {t["name"] for t in defs}

        assert len(defs) >= 66
        assert "voice_call_dispatch" in names
        assert "voice_call_campaign" in names
        assert "voice_call_doctor" in names
        assert "voice_call_list_campaigns" in names

    def test_mcp_voice_call_jsonrpc_workflow(self, tmp_path):
        """Verifies JSON-RPC dispatch for voice_call_doctor and voice_call_dispatch."""
        server = MCPServer(workspace_path=tmp_path)

        req_doc = {
            "jsonrpc": "2.0",
            "id": 301,
            "method": "tools/call",
            "params": {"name": "voice_call_doctor", "arguments": {}}
        }
        res_doc = server.handle_jsonrpc(req_doc)
        assert res_doc["id"] == 301
        assert res_doc["result"]["status"] == "ONLINE"

        req_call = {
            "jsonrpc": "2.0",
            "id": 302,
            "method": "tools/call",
            "params": {
                "name": "voice_call_dispatch",
                "arguments": {
                    "phone": "+1555018888",
                    "name": "Elena",
                    "company": "Premier Health",
                    "niche": "Healthcare"
                }
            }
        }
        res_call = server.handle_jsonrpc(req_call)
        assert res_call["id"] == 302
        assert res_call["result"]["success"] is True
        assert res_call["result"]["status"] == "BOOKED"


@pytest.mark.asyncio
class TestJarvisCLIVoiceCallAutonomousInference:
    async def test_autonomous_inference_from_post_description(self):
        """
        Verifies Central Brain infers the need for a Voice Calling Agent when given
        the action plan to sell 4 custom AI buildouts at $2500 each and dial leads.
        """
        cli = JarvisCLI()
        post_prompt = (
            "Claude Code build product, GitHub store source, Vercel deploy, Supabase database. "
            "Sell 4 custom AI buildouts at $2,500 each = $10,000. 300 cold calls = 2 booked calls. "
            "Dial 3000 leads 5 times to get your $10k in a week."
        )
        plan = await cli.decompose_directive_cognitively(post_prompt)
        steps = plan.get("steps", [])
        assert len(steps) >= 1
        # Check that call mode was inferred
        call_step = next((s for s in steps if s.get("mode") == "call"), None)
        assert call_step is not None, "Central Brain failed to autonomously infer the need for Voice Call Agent!"
        assert call_step.get("call_action") == "campaign" or "dial" in call_step.get("goal", "").lower()

    async def test_execute_autonomous_step_call_campaign(self):
        """Verifies execute_autonomous_step for mode 'call'."""
        cli = JarvisCLI()
        step = {
            "mode": "call",
            "niche": "Roofing Contractors",
            "count": 300,
            "call_action": "campaign",
            "price_per_close": 2500,
            "goal": "Dial 300 leads and book discovery calls"
        }
        with patch.object(voice_call_engine, "execute_cold_call_campaign") as mock_camp:
            mock_camp.return_value = {
                "status": "COMPLETED",
                "total_dials_executed": 300,
                "connected_conversations": 45,
                "calls_booked_count": 4,
                "booked_discovery_calls": [{"slot": "Friday 2 PM", "lead_name": "Marcus", "company": "Apex", "deal_value": "$2,500"}],
                "projected_closes": 2,
                "unit_price": "$2,500",
                "projected_revenue": "$5,000",
                "calendar_url": "https://calendly.com/anshtiwari"
            }
            ok = await cli.execute_autonomous_step(step, original_line="launch voice call campaign")
            assert ok is True
            mock_camp.assert_called_once()

    async def test_process_directive_call_doctor(self):
        """Verifies direct CLI process_directive routing for 'call doctor'."""
        cli = JarvisCLI()
        with patch.object(cli, "handle_call_cmd") as mock_cmd:
            ok = await cli.process_directive("call doctor")
            assert ok is True
            mock_cmd.assert_called_once()


    async def test_cli_dispatch_provider_flag(self):
        """Verifies CLI 'call dispatch' parses --provider flag properly."""
        cli = JarvisCLI()
        with patch.object(voice_call_engine, "dispatch_single_call", new_callable=AsyncMock) as mock_dispatch:
            mock_dispatch.return_value = {
                "success": True,
                "provider": "google_voice",
                "call_id": "call_test123",
                "status": "initiated",
                "url": "https://voice.google.com/u/0/calls?number=+15551234567",
                "phone": "+15551234567"
            }
            parts = ["call", "dispatch", "+15551234567", "Jake", "Titan", "Roofing", "--provider", "google_voice"]
            await cli.handle_call_cmd(parts)
            mock_dispatch.assert_called_once()
            args, kwargs = mock_dispatch.call_args
            assert kwargs.get("provider") == "google_voice"
