"""
Unit tests for JARVIS Real Lead Sourcing and DNS Verification Engine.
Architect: Ansh Tiwari
"""

import csv
import pytest
from pathlib import Path
from core.lead_verifier import RealLeadVerifier, REAL_TECH_COMPANIES, VerifiedLead

def test_dns_verification_cache_and_resolution():
    verifier = RealLeadVerifier()
    # Test well-known resolvable domain
    ip = verifier.verify_domain_dns("stripe.com")
    assert ip is not None
    assert isinstance(ip, str)
    # Test cached lookup
    assert "stripe.com" in verifier._dns_cache
    cached_ip = verifier.verify_domain_dns("stripe.com")
    assert cached_ip == ip

def test_dns_verification_invalid_domain():
    verifier = RealLeadVerifier()
    ip = verifier.verify_domain_dns("invalid-fake-domain-nxdomain-99999.xyz")
    assert ip is None

def test_generate_verified_leads():
    verifier = RealLeadVerifier()
    leads = verifier.generate_verified_leads(count=50)
    assert len(leads) == 50
    for lead in leads:
        assert isinstance(lead, VerifiedLead)
        assert lead.Website.startswith("http")
        assert lead.DNS_IP != ""
        assert len(lead.ProofOfNeed) > 10
        assert lead.Verified == "Yes (DNS-Verified & Active)"
        assert lead.Status == "QUEUED"

def test_export_verified_leads(tmp_path):
    output_csv = tmp_path / "test_leads.csv"
    verifier = RealLeadVerifier()
    exported_path, count = verifier.export_verified_leads_to_csv(dest_filename=output_csv, count=20)
    assert Path(exported_path).exists()
    assert count == 20
    
    with open(exported_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 20
        for r in rows:
            assert "Website" in r
            assert "ProofOfNeed" in r
            assert "DNS_IP" in r
            assert r["Website"].startswith("http")
            assert r["DNS_IP"] != ""


def test_verify_lead_record_pipeline():
    verifier = RealLeadVerifier()
    
    # 1. Valid lead
    valid_lead = {
        "Name": "Patrick Collison",
        "Company": "Stripe",
        "Email": "patrick@stripe.com",
        "Website": "https://stripe.com",
        "ProofOfNeed": "Optimizing developer API gateway latency and microservice architecture"
    }
    audit1 = verifier.verify_lead_record(valid_lead)
    assert audit1["valid"] is True
    assert audit1["email_valid"] is True
    assert audit1["dns_valid"] is True
    assert audit1["lead"]["Status"] == "QUEUED"
    assert "DNS, MX & RFC-Verified" in audit1["lead"]["Verified"]

    # 2. Dead domain (NXDOMAIN)
    dead_lead = {
        "Name": "Ghost Founder",
        "Company": "DeadCorp",
        "Email": "ghost@nxdomain-fake-site-9999.xyz",
        "Website": "https://nxdomain-fake-site-9999.xyz",
        "ProofOfNeed": "Needs urgent fullstack engineering"
    }
    audit2 = verifier.verify_lead_record(dead_lead)
    assert audit2["valid"] is False
    assert audit2["dns_valid"] is False
    assert any("NXDOMAIN" in r for r in audit2["reasons"])

    # 3. Disposable email
    disp_lead = {
        "Name": "Spam User",
        "Company": "TempCo",
        "Email": "hacker@mailinator.com",
        "Website": "https://stripe.com",
        "ProofOfNeed": "Needs database migration"
    }
    audit3 = verifier.verify_lead_record(disp_lead)
    assert audit3["valid"] is False
    assert audit3["email_valid"] is False
    assert any("Disposable" in r for r in audit3["reasons"])


def test_audit_and_filter_leads_before_storage(tmp_path):
    dest_csv = tmp_path / "clean_leads.csv"
    quarantine_json = tmp_path / "quarantined.json"

    raw_batch = [
        {
            "Name": "Guillermo Rauch",
            "Company": "Vercel",
            "Email": "guillermo@vercel.com",
            "Website": "https://vercel.com",
            "ProofOfNeed": "Optimizing Next.js edge rendering cold start latency"
        },
        {
            "Name": "Bad Contact",
            "Company": "FakeCorp",
            "Email": "fake@tempmail.com",
            "Website": "https://nonexistent-nxdomain-99999.org",
            "ProofOfNeed": "Needs web development"
        }
    ]

    res = RealLeadVerifier.audit_and_filter_leads_before_storage(
        raw_batch,
        dest_csv=dest_csv,
        quarantine_file=quarantine_json
    )

    assert res["total_evaluated"] == 2
    assert res["valid_count"] == 1
    assert res["quarantined_count"] == 1
    assert dest_csv.exists()
    assert quarantine_json.exists()

    # Check that CSV ONLY contains the valid lead
    with open(dest_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        saved = list(reader)
        assert len(saved) == 1
        assert saved[0]["Email"] == "guillermo@vercel.com"


def test_mcp_server_lead_verification_tool(tmp_path):
    from core.mcp_server import MCPServer
    mcp = MCPServer(tmp_path)
    
    # 1. Direct tool call
    audit = mcp.tool_verify_lead_data(
        name="Paul Copplestone",
        email="paul@supabase.com",
        company="Supabase",
        website="https://supabase.com",
        proof_of_need="Refactoring microservices for sub-15ms latency"
    )
    assert audit["valid"] is True
    assert audit["dns_valid"] is True

    # 2. JSON-RPC tool call
    rpc_res = mcp.handle_jsonrpc({
        "jsonrpc": "2.0",
        "id": "req-verify-01",
        "method": "tools/call",
        "params": {
            "name": "verify_lead_data",
            "arguments": {
                "name": "Hacker",
                "email": "bad@mailinator.com",
                "company": "SpamCo",
                "website": "https://invalid-domain-nxdomain-test.com"
            }
        }
    })
    assert rpc_res["result"]["valid"] is False
