from pathlib import Path

# 1. Update core/mcp_server.py
mcp_file = Path("D:/LlamaOrchestrator/core/mcp_server.py")
mcp_text = mcp_file.read_text(encoding="utf-8")

mcp_tool_target = """    def tool_verify_email_syntax(self, email: str) -> dict[str, Any]:
        \"\"\"Validates cold outreach lead email formatting.\"\"\"
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"
        valid = bool(re.match(pattern, email.strip()))
        return {
            "email": email,
            "valid": valid,
            "reason": "Valid RFC-5322 structure" if valid else "Malformed email address"
        }"""

mcp_tool_replacement = """    def tool_verify_email_syntax(self, email: str) -> dict[str, Any]:
        \"\"\"Validates cold outreach lead email formatting.\"\"\"
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"
        valid = bool(re.match(pattern, email.strip()))
        return {
            "email": email,
            "valid": valid,
            "reason": "Valid RFC-5322 structure" if valid else "Malformed email address"
        }

    def tool_verify_lead_data(
        self,
        email: str,
        website: str = "",
        name: str = "",
        company: str = "",
        proof_of_need: str = ""
    ) -> dict[str, Any]:
        \"\"\"
        Pre-Storage Lead Verification Tool:
        Audits lead data before saving:
        1. RFC-5322 syntax regex check.
        2. Disposable / temporary email domain blocklist check.
        3. Real-time DNS MX (Mail Exchange) record resolution.
        4. Domain A-record resolution to prevent NXDOMAIN errors.
        5. Contact completeness and proof-of-need integrity.
        \"\"\"
        from core.lead_verifier import RealLeadVerifier
        audit = RealLeadVerifier.verify_lead_record({
            "Name": name,
            "Email": email,
            "Company": company,
            "Website": website,
            "ProofOfNeed": proof_of_need
        })
        return audit"""

mcp_spec_target = """            {"name": "verify_email_syntax", "description": "Validate syntax of outbound sales lead emails."},"""
mcp_spec_replacement = """            {"name": "verify_email_syntax", "description": "Validate syntax of outbound sales lead emails."},
            {"name": "verify_lead_data", "description": "Pre-storage lead verification: Checks RFC syntax, disposable domains, DNS MX, and domain A-record to prevent NXDOMAIN."},"""

mcp_dispatch_target = """                elif tool_name == "verify_email_syntax":
                    res = self.tool_verify_email_syntax(tool_args["email"])"""
mcp_dispatch_replacement = """                elif tool_name == "verify_email_syntax":
                    res = self.tool_verify_email_syntax(tool_args["email"])
                elif tool_name == "verify_lead_data":
                    res = self.tool_verify_lead_data(
                        email=tool_args.get("email", ""),
                        website=tool_args.get("website", ""),
                        name=tool_args.get("name", ""),
                        company=tool_args.get("company", ""),
                        proof_of_need=tool_args.get("proof_of_need", "")
                    )"""

norm_mcp = mcp_text.replace("\r\n", "\n")
norm_mcp_tool_target = mcp_tool_target.replace("\r\n", "\n")
norm_mcp_tool_rep = mcp_tool_replacement.replace("\r\n", "\n")
norm_mcp_spec_target = mcp_spec_target.replace("\r\n", "\n")
norm_mcp_spec_rep = mcp_spec_replacement.replace("\r\n", "\n")
norm_mcp_disp_target = mcp_dispatch_target.replace("\r\n", "\n")
norm_mcp_disp_rep = mcp_dispatch_replacement.replace("\r\n", "\n")

if norm_mcp_tool_target in norm_mcp and norm_mcp_spec_target in norm_mcp and norm_mcp_disp_target in norm_mcp:
    norm_mcp = norm_mcp.replace(norm_mcp_tool_target, norm_mcp_tool_rep, 1)
    norm_mcp = norm_mcp.replace(norm_mcp_spec_target, norm_mcp_spec_rep, 1)
    norm_mcp = norm_mcp.replace(norm_mcp_disp_target, norm_mcp_disp_rep, 1)
    if "\r\n" in mcp_text:
        norm_mcp = norm_mcp.replace("\n", "\r\n")
    mcp_file.write_text(norm_mcp, encoding="utf-8")
    print("SUCCESSFULLY_PATCHED_MCP_SERVER")
else:
    print("FAILED_TO_PATCH_MCP_SERVER")

# 2. Update core/worker.py to use RealLeadVerifier in DAG execution
worker_file = Path("D:/LlamaOrchestrator/core/worker.py")
worker_text = worker_file.read_text(encoding="utf-8")

worker_target = """        elif "lead" in tid or "scraping" in tid:
            leads_data = (
                "Name,Email,Company,Role,Status,Verified,ProofOfNeed,ObservedSignal,Website\\n"
                "Guillermo Rauch,guillermo@vercel.com,Vercel,CEO and Founder,Qualified,Yes (DNS-Verified),Optimizing edge rendering and cold-start latency for Next.js,High,https://vercel.com\\n"
                "Paul Copplestone,paul@supabase.com,Supabase,CEO and Co-Founder,Qualified,Yes (DNS-Verified),Refactoring microservices for sub-15ms latency on read-replicas,High,https://supabase.com\\n"
                "Karri Saarinen,karri@linear.app,Linear,CEO and Co-Founder,Qualified,Yes (DNS-Verified),Real-time synchronization and GraphQL client cache invalidation,High,https://linear.app\\n"
                "James Hawkins,james@posthog.com,PostHog,CEO and Co-Founder,Qualified,Yes (DNS-Verified),Event ingestion pipeline migration to ClickHouse cluster,High,https://posthog.com\\n"
                "Peer Richelsen,peer@cal.com,Cal.com,Co-CEO and Founder,Qualified,Yes (DNS-Verified),Full-stack scheduling engine optimization and Webhook delivery,High,https://cal.com\\n"
                "Patrick Collison,patrick@stripe.com,Stripe,CEO and Co-Founder,Qualified,Yes (DNS-Verified),Developer dashboard API response optimization (<200ms TTFB),High,https://stripe.com\\n"
            )
            self.mcp.tool_file_write("leads.csv", leads_data)
            artifacts.append("leads.csv")
            self.mcp.tool_file_write("campaigns/cold_email/leads.csv", leads_data)
            artifacts.append("campaigns/cold_email/leads.csv")"""

worker_replacement = """        elif "lead" in tid or "scraping" in tid:
            from core.lead_verifier import RealLeadVerifier
            # Autonomous Pre-Storage Verified Lead Generation
            verified_leads = RealLeadVerifier.generate_verified_leads(count=50)
            audit_res = RealLeadVerifier.audit_and_filter_leads_before_storage(
                [v.to_dict() for v in verified_leads],
                dest_csv=self.mcp.workspace_dir / "leads.csv"
            )
            dest_content = (self.mcp.workspace_dir / "leads.csv").read_text(encoding="utf-8")
            self.mcp.tool_file_write("leads.csv", dest_content)
            artifacts.append("leads.csv")
            self.mcp.tool_file_write("campaigns/cold_email/leads.csv", dest_content)
            artifacts.append("campaigns/cold_email/leads.csv")"""

norm_worker = worker_text.replace("\r\n", "\n")
norm_worker_target = worker_target.replace("\r\n", "\n")
norm_worker_rep = worker_replacement.replace("\r\n", "\n")

if norm_worker_target in norm_worker:
    norm_worker = norm_worker.replace(norm_worker_target, norm_worker_rep, 1)
    if "\r\n" in worker_text:
        norm_worker = norm_worker.replace("\n", "\r\n")
    worker_file.write_text(norm_worker, encoding="utf-8")
    print("SUCCESSFULLY_PATCHED_WORKER")
else:
    print("FAILED_TO_PATCH_WORKER")

