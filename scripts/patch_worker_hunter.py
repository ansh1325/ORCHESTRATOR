from pathlib import Path

worker_file = Path("D:/LlamaOrchestrator/core/worker.py")
text = worker_file.read_text(encoding="utf-8")

target = """        elif "lead" in tid or "scraping" in tid:
            from core.lead_verifier import RealLeadVerifier
            # Autonomous Pre-Storage Verified Lead Generation
            verified_leads = RealLeadVerifier.generate_verified_leads(count=50)
            audit_res = RealLeadVerifier.audit_and_filter_leads_before_storage(
                [v.to_dict() for v in verified_leads],
                dest_csv=self.mcp.workspace_path / "leads.csv"
            )
            dest_content = (self.mcp.workspace_path / "leads.csv").read_text(encoding="utf-8")
            self.mcp.tool_file_write("leads.csv", dest_content)
            artifacts.append("leads.csv")
            self.mcp.tool_file_write("campaigns/cold_email/leads.csv", dest_content)
            artifacts.append("campaigns/cold_email/leads.csv")"""

rep = """        elif "lead" in tid or "scraping" in tid:
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

norm_text = text.replace('\r\n', '\n')
norm_target = target.replace('\r\n', '\n')
norm_rep = rep.replace('\r\n', '\n')

if norm_target in norm_text:
    new_text = norm_text.replace(norm_target, norm_rep, 1)
    if '\r\n' in text:
        new_text = new_text.replace('\n', '\r\n')
    worker_file.write_text(new_text, encoding="utf-8")
    print("SUCCESS_WORKER_HUNTER")
else:
    print("TARGET_NOT_FOUND")

