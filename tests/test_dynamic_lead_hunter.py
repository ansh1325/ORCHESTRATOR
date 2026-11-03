"""
Unit & Integration Tests for JARVIS Dynamic Lead Hunter & Autonomous Sourcing Strategist
Chief Systems Architect: Ansh Tiwari
"""

import csv
import json
import pytest
from pathlib import Path

from core.dynamic_lead_hunter import DynamicLeadHunter, LeadStrategy, dynamic_lead_hunter
from core.mcp_server import MCPServer


def test_strategy_deduction_across_diverse_domains():
    hunter = DynamicLeadHunter()

    # Domain 1: Solar & Roofing Contractors
    strat_solar = hunter.deduce_strategy("find solar and roofing contractors in Texas")
    assert strat_solar.primary_channel == "LOCAL_DIRECTORIES_AND_MAPS"
    assert any(w in strat_solar.target_industry.lower() for w in ["solar", "home", "roof", "construction", "renewable", "energy", "contractor"])
    assert len(strat_solar.search_queries) >= 1
    assert any("Maps" in s or "Yelp" in s or "BBB" in s or "HomeAdvisor" in s for s in strat_solar.recommended_sources)

    # Domain 2: Private Dental Practices
    strat_dental = hunter.deduce_strategy("scrape dental clinic practice owners")
    assert strat_dental.primary_channel == "HEALTHCARE_DIRECTORIES_AND_REGISTRIES"
    assert "dental" in strat_dental.target_industry.lower() or "health" in strat_dental.target_industry.lower()

    # Domain 3: Law Firms & Immigration Attorneys
    strat_legal = hunter.deduce_strategy("find managing partners of immigration law firms")
    assert strat_legal.primary_channel == "LEGAL_BAR_DIRECTORIES"
    assert "law" in strat_legal.target_industry.lower() or "legal" in strat_legal.target_industry.lower()

    # Domain 4: Shopify DTC E-Commerce Brands
    strat_ecom = hunter.deduce_strategy("find high-growth Shopify ecommerce clothing brands")
    assert strat_ecom.primary_channel == "ECOMMERCE_COMMUNITIES_AND_STORE_INDEXES"
    assert "ecom" in strat_ecom.target_industry.lower() or "commerce" in strat_ecom.target_industry.lower() or "retail" in strat_ecom.target_industry.lower() or "clothing" in strat_ecom.target_industry.lower()

    # Domain 5: Modern SaaS & Dev Tools
    strat_saas = hunter.deduce_strategy("find CTOs scaling Next.js microservices")
    assert strat_saas.primary_channel in ["TECH_ECOSYSTEMS_AND_COMMUNITIES", "B2B_SOCIAL_GRAPHS_AND_DIRECTORIES", "B2B_SOCIAL_GRAPHS"]
    assert "tech" in strat_saas.target_industry.lower() or "saas" in strat_saas.target_industry.lower() or "software" in strat_saas.target_industry.lower() or "dev" in strat_saas.target_industry.lower()


def test_autonomous_lead_harvest_and_dossier_generation(tmp_path):
    dest_csv = tmp_path / "solar_leads.csv"

    # Execute dynamic lead harvest for local contractors
    res = DynamicLeadHunter.harvest_leads_autonomously(
        directive="find commercial solar installers and contractors",
        target_count=10,
        dest_csv=dest_csv
    )

    assert "deduced_strategy" in res
    assert "execution_metrics" in res
    strat = res["deduced_strategy"]
    metrics = res["execution_metrics"]

    assert strat["primary_channel"] == "LOCAL_DIRECTORIES_AND_MAPS"
    assert metrics["verified_sendable"] >= 5
    assert dest_csv.exists()

    # Inspect CSV rows
    with open(dest_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) >= 5
        for r in reader:
            assert r["Website"].startswith("http")
            assert "@" in r["Email"]
            assert len(r["ProofOfNeed"]) > 10


def test_mcp_autonomous_lead_hunt_tool(tmp_path):
    mcp = MCPServer(workspace_path=tmp_path)
    tools = mcp.get_tool_definitions()
    tool_names = {t["name"] for t in tools}

    assert "autonomous_lead_hunt" in tool_names

    # Test JSON-RPC invocation
    rpc_res = mcp.handle_jsonrpc({
        "jsonrpc": "2.0",
        "id": "req-hunt-01",
        "method": "tools/call",
        "params": {
            "name": "autonomous_lead_hunt",
            "arguments": {
                "directive": "find private dental practices in Florida",
                "target_count": 5
            }
        }
    })

    assert "result" in rpc_res
    res_data = rpc_res["result"]
    assert "deduced_strategy" in res_data
    assert res_data["deduced_strategy"]["primary_channel"] == "HEALTHCARE_DIRECTORIES_AND_REGISTRIES"
    assert (tmp_path / "leads.csv").exists()
