from pathlib import Path

# 1. Update core/worker.py
worker_file = Path("D:/LlamaOrchestrator/core/worker.py")
worker_text = worker_file.read_text(encoding="utf-8")

worker_target = """        elif "lead" in tid or "scraping" in tid:
            from core.lead_verifier import RealLeadVerifier
            # Autonomous Pre-Storage Verified Lead Generation
            verified_leads = RealLeadVerifier.generate_verified_leads(count=50)
            target_csv = self.mcp.workspace_path / "leads.csv"
            audit_res = RealLeadVerifier.audit_and_filter_leads_before_storage(
                [v.to_dict() for v in verified_leads],
                dest_csv=target_csv
            )
            dest_content = target_csv.read_text(encoding="utf-8")
            self.mcp.tool_file_write("leads.csv", dest_content)
            artifacts.append("leads.csv")
            self.mcp.tool_file_write("campaigns/cold_email/leads.csv", dest_content)
            artifacts.append("campaigns/cold_email/leads.csv")"""

worker_replacement = """        elif "lead" in tid or "scraping" in tid:
            from core.dynamic_lead_hunter import dynamic_lead_hunter
            # Autonomous Domain-Agnostic Lead Hunting & Strategy Deduction
            directive_text = f"{task.description} {spec.system_prompt}"
            target_csv = self.mcp.workspace_path / "leads.csv"
            dossier = dynamic_lead_hunter.harvest_leads_autonomously(
                directive=directive_text,
                target_count=50,
                dest_csv=target_csv
            )
            dest_content = target_csv.read_text(encoding="utf-8")
            self.mcp.tool_file_write("leads.csv", dest_content)
            artifacts.append("leads.csv")
            self.mcp.tool_file_write("campaigns/cold_email/leads.csv", dest_content)
            artifacts.append("campaigns/cold_email/leads.csv")
            self.mcp.tool_file_write("lead_hunting_dossier.json", json.dumps(dossier, indent=2))
            artifacts.append("lead_hunting_dossier.json")"""

norm_w = worker_text.replace("\r\n", "\n")
norm_wt = worker_target.replace("\r\n", "\n")
norm_wr = worker_replacement.replace("\r\n", "\n")

if norm_wt in norm_w:
    norm_w = norm_w.replace(norm_wt, norm_wr, 1)
    if "\r\n" in worker_text:
        norm_w = norm_w.replace("\n", "\r\n")
    worker_file.write_text(norm_w, encoding="utf-8")
    print("SUCCESS_WORKER_HUNTER")
else:
    print("FAILED_WORKER_HUNTER")

# 2. Update core/mcp_server.py with tool_autonomous_lead_hunt
mcp_file = Path("D:/LlamaOrchestrator/core/mcp_server.py")
mcp_text = mcp_file.read_text(encoding="utf-8")

mcp_tool_target = """    def tool_verify_lead_data(
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

mcp_tool_rep = mcp_tool_target + """

    def tool_autonomous_lead_hunt(self, directive: str, target_count: int = 20) -> dict[str, Any]:
        \"\"\"
        Universal Autonomous Lead Hunter Tool:
        1. Analyzes directive and dynamically deduces optimal sourcing channels
           (Local Directories vs. Community Forums vs. B2B Social Graphs vs. Tech Ecosystems).
        2. Harvests entity candidates and extracts contact details.
        3. Pre-verifies physical sendability, live DNS MX, and domain resolution.
        4. Quarantines dead records and saves clean leads to leads.csv.
        5. Produces an Executive Sourcing Dossier explaining channel selection.
        \"\"\"
        from core.dynamic_lead_hunter import dynamic_lead_hunter
        target_csv = self.workspace_path / "leads.csv"
        return dynamic_lead_hunter.harvest_leads_autonomously(
            directive=directive,
            target_count=target_count,
            dest_csv=target_csv
        )"""

mcp_spec_target = """            {"name": "verify_lead_data", "description": "Pre-storage lead verification: Checks RFC syntax, disposable domains, DNS MX, and domain A-record to prevent NXDOMAIN."},"""
mcp_spec_rep = mcp_spec_target + """
            {"name": "autonomous_lead_hunt", "description": "Domain-agnostic lead discovery: deduces sourcing channels (forums, directories, social, job boards) and verifies physical sendability."},"""

mcp_disp_target = """                elif tool_name == "verify_lead_data":
                    res = self.tool_verify_lead_data(
                        email=tool_args.get("email", ""),
                        website=tool_args.get("website", ""),
                        name=tool_args.get("name", ""),
                        company=tool_args.get("company", ""),
                        proof_of_need=tool_args.get("proof_of_need", "")
                    )"""
mcp_disp_rep = mcp_disp_target + """
                elif tool_name == "autonomous_lead_hunt":
                    res = self.tool_autonomous_lead_hunt(
                        directive=tool_args.get("directive", "B2B tech leads"),
                        target_count=tool_args.get("target_count", 20)
                    )"""

norm_m = mcp_text.replace("\r\n", "\n")
norm_mt = mcp_tool_target.replace("\r\n", "\n")
norm_mr = mcp_tool_rep.replace("\r\n", "\n")
norm_st = mcp_spec_target.replace("\r\n", "\n")
norm_sr = mcp_spec_rep.replace("\r\n", "\n")
norm_dt = mcp_disp_target.replace("\r\n", "\n")
norm_dr = mcp_disp_rep.replace("\r\n", "\n")

if norm_mt in norm_m and norm_st in norm_m and norm_dt in norm_m:
    norm_m = norm_m.replace(norm_mt, norm_mr, 1)
    norm_m = norm_m.replace(norm_st, norm_sr, 1)
    norm_m = norm_m.replace(norm_dt, norm_dr, 1)
    if "\r\n" in mcp_text:
        norm_m = norm_m.replace("\n", "\r\n")
    mcp_file.write_text(norm_m, encoding="utf-8")
    print("SUCCESS_MCP_HUNTER")
else:
    print("FAILED_MCP_HUNTER")

# 3. Update jarvis_cli.py
cli_file = Path("D:/LlamaOrchestrator/jarvis_cli.py")
cli_text = cli_file.read_text(encoding="utf-8")

cli_route_target = """        # Autonomous Multi-Account Fleet Management (20 Inboxes, Anti-Spam Jitter, Reply Monitor)
        if low.startswith("fleet") or low in ["accounts", "fleet status", "fleet replies"]:"""

cli_route_rep = """        # Autonomous Lead Hunter & Domain-Agnostic Strategist
        if low.startswith("hunt ") or low.startswith("find leads ") or low.startswith("scrape leads "):
            directive = line.split(maxsplit=1)[1] if len(line.split()) > 1 else "B2B SaaS founders"
            self.handle_hunt_cmd(directive)
            return True

        # Autonomous Multi-Account Fleet Management (20 Inboxes, Anti-Spam Jitter, Reply Monitor)
        if low.startswith("fleet") or low in ["accounts", "fleet status", "fleet replies"]:"""

cli_method_target = """    def handle_fleet_cmd(self, parts: list[str]):"""

cli_method_rep = """    def handle_hunt_cmd(self, directive: str):
        \"\"\"Autonomously deduces lead sources (directories vs forums vs social media), harvests, and verifies deliverability.\"\"\"
        from core.dynamic_lead_hunter import dynamic_lead_hunter, DOSSIER_FILE
        print(f"\\n{C.CYAN}{C.BOLD}🎯 [Autonomous Lead Hunter & Strategic Sourcing Engine]{C.RESET}")
        print(f"  Directive: {C.YELLOW}{directive}{C.RESET}")
        self.speak("Analyzing directive. Dynamically deducing optimal lead sourcing channels and verifying deliverability.")

        res = dynamic_lead_hunter.harvest_leads_autonomously(directive=directive, target_count=20)
        strat = res["deduced_strategy"]
        metrics = res["execution_metrics"]

        print(f"\\n  {C.BOLD}1. Cognitive Strategy Deduction:{C.RESET}")
        print(f"  • Target Domain: {C.GREEN}{strat['target_industry']}{C.RESET}")
        print(f"  • Decision Maker Persona: {C.YELLOW}{strat['target_persona']}{C.RESET}")
        print(f"  • Selected Channel: {C.CYAN}{strat['primary_channel']}{C.RESET}")
        print(f"  • Channel Justification: {C.DIM}{strat['channel_justification']}{C.RESET}")
        print(f"  • Target Queries: {', '.join(strat['search_queries'][:2])}")

        print(f"\\n  {C.BOLD}2. Live Harvest & Pre-Storage Deliverability Metrics:{C.RESET}")
        print(f"  • Total Candidates Probed: {metrics['total_probed']}")
        print(f"  • 100% Verified Sendable (DNS & MX Live): {C.GREEN}{metrics['verified_sendable']}{C.RESET}")
        print(f"  • Quarantined / NXDOMAIN Rejected: {C.RED}{metrics['quarantined_invalid']}{C.RESET}")
        print(f"  • Deliverability Pass Rate: {C.GREEN}{metrics['deliverability_rate']}{C.RESET}")
        print(f"  • Verified CSV Output: {C.CYAN}{metrics['csv_deliverable']}{C.RESET}")
        print(f"  • Strategic Dossier: {C.DIM}{DOSSIER_FILE}{C.RESET}\\n")
        self.speak(f"Harvest complete. {metrics['verified_sendable']} verified leads saved to disk with live DNS and MX resolution.")

    def handle_fleet_cmd(self, parts: list[str]):"""

cli_help_target = """        print(f"  {C.CYAN}outreach <niche> [hook]{C.RESET}  Compile high-efficiency cold outreach system (<30c subject, <100w body, 4-stage follow-up)")"""
cli_help_rep = """        print(f"  {C.CYAN}hunt <directive>{C.RESET}         Autonomous Lead Hunter (Deduces channels: forums, directories, social, job boards; verifies DNS/MX)")
        print(f"  {C.CYAN}outreach <niche> [hook]{C.RESET}  Compile high-efficiency cold outreach system (<30c subject, <100w body, 4-stage follow-up)")"""

norm_c = cli_text.replace("\r\n", "\n")
norm_crt = cli_route_target.replace("\r\n", "\n")
norm_crr = cli_route_rep.replace("\r\n", "\n")
norm_cmt = cli_method_target.replace("\r\n", "\n")
norm_cmr = cli_method_rep.replace("\r\n", "\n")
norm_cht = cli_help_target.replace("\r\n", "\n")
norm_chr = cli_help_rep.replace("\r\n", "\n")

if norm_crt in norm_c and norm_cmt in norm_c and norm_cht in norm_c:
    norm_c = norm_c.replace(norm_crt, norm_crr, 1)
    norm_c = norm_c.replace(norm_cmt, norm_cmr, 1)
    norm_c = norm_c.replace(norm_cht, norm_chr, 1)
    if "\r\n" in cli_text:
        norm_c = norm_c.replace("\n", "\r\n")
    cli_file.write_text(norm_c, encoding="utf-8")
    print("SUCCESS_CLI_HUNTER")
else:
    print("FAILED_CLI_HUNTER")

