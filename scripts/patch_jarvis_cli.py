import re
from pathlib import Path

cli_path = Path("D:/LlamaOrchestrator/jarvis_cli.py")
content = cli_path.read_text(encoding="utf-8")

old_needle = """        elif sub in ["replies", "check_replies", "responses"]:
            print(f"\\n{C.CYAN}{C.BOLD}📬 [Fleet Autonomous Reply Monitor]{C.RESET} Scanning inboxes across accounts...")
            res = account_fleet.process_incoming_reply("prospect_cio@enterprise.com", "Sounds interesting, what is your pricing and can we talk next Tuesday?")
            print(f"  • Lead Identified: {C.GREEN}{res.get('lead_email')}{C.RESET}")
            print(f"  • Sentiment Category: {C.YELLOW}{res.get('sentiment_category')}{C.RESET}")
            print(f"  • Action Taken: {C.CYAN}{res.get('action_taken')}{C.RESET}\\n")
            self.speak("Inboxes scanned. High-intent prospect response identified and flagged.")

        elif sub == "dispatch":"""

addition = """        elif sub == "scale":
            count = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 20
            is_ws = (len(parts) > 3 and parts[3].lower() in ["workspace", "custom", "true"])
            print(f"\\n{C.CYAN}{C.BOLD}⚡ [Scaling Account Fleet Topology]{C.RESET} Target Node Count: {count}...")
            res = account_fleet.scale_fleet_topology(target_account_count=count, is_workspace=is_ws)
            print(f"  • Total Fleet Accounts: {C.GREEN}{res['total_accounts']}{C.RESET}")
            print(f"  • Configuration Mode: {C.YELLOW}{res['account_type']}{C.RESET}")
            print(f"  • Safe Rate Limit / Account: {C.CYAN}{res['daily_capacity_per_account']}{C.RESET}")
            print(f"  • Total Fleet Daily Capacity: {C.GREEN}{res['total_daily_fleet_capacity']}{C.RESET}")
            print(f"  • Deliverability Shield: {C.GREEN}{res['primary_inbox_deliverability_score']}{C.RESET}\\n")
            self.speak(f"Account fleet scaled to {res['total_accounts']} nodes.")

        elif sub == "verify":
            target = parts[2] if len(parts) > 2 else "workspaces/leads.csv"
            print(f"\\n{C.CYAN}{C.BOLD}🛡️  [Email Deliverability & MX Verification Engine]{C.RESET}")
            if "@" in target:
                res = account_fleet.validate_email_sendability(target)
                status_col = C.GREEN if res["sendable"] else C.RED
                print(f"  • Target: {target}")
                print(f"  • Deliverability Status: {status_col}{'VERIFIED SENDABLE' if res['sendable'] else 'REJECTED'}{C.RESET}")
                print(f"  • Reason / MX Proof: {res['reason']}")
                if res.get("mx_servers"):
                    print(f"  • Active Mail Exchangers: {', '.join(res['mx_servers'][:3])}\\n")
            else:
                p_file = Path(target)
                if not p_file.exists():
                    p_file = Path("workspaces") / target
                if p_file.exists():
                    import csv
                    with open(p_file, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        leads = [{"email": r["Email"], "name": r.get("Name", ""), "company": r.get("Company", "")} for r in reader if "Email" in r]
                    audit = account_fleet.filter_sendable_prospects(leads)
                    print(f"  • Total Leads Audited: {audit['total_evaluated']}")
                    print(f"  • Sendable (Clean & Active MX): {C.GREEN}{audit['sendable_count']}{C.RESET}")
                    print(f"  • Bouncing / Disposable Rejected: {C.RED}{audit['rejected_count']}{C.RESET}\\n")
                else:
                    print(f"  {C.RED}File not found: {target}{C.RESET}\\n")

        elif sub == "sequence":
            niche = " ".join(parts[2:]) if len(parts) > 2 else "Full-Stack Dev & AI Systems"
            touches = account_fleet.generate_8_touch_sequence(company_niche=niche)
            print(f"\\n{C.CYAN}{C.BOLD}📅 [8-Touch Human-Engineered Outreach Sequence]{C.RESET}")
            print(f"  Target Focus: {niche} | Delivery Target: 98%+ Primary Folder Placement\\n")
            for t in touches:
                print(f"  {C.YELLOW}Touch {t['touch']} (Day {t['day_offset']}): {t['strategy']}{C.RESET}")
                print(f"    Subject: {C.BOLD}{t['subject']}{C.RESET}")
                print(f"    Body ({len(t['body'].split())} words):\\n    {t['body'].replace(chr(10), chr(10)+'    ')}\\n")

        elif sub == "close":
            if len(parts) < 4:
                print(f"{C.RED}Usage: fleet close <email> <reply snippet text>{C.RESET}")
                return
            em = parts[2]
            snippet = " ".join(parts[3:])
            briefing = account_fleet.synthesize_autonomous_reply(em, snippet)
            print(f"\\n{C.CYAN}{C.BOLD}🤝 [Autonomous Conversational Closer & Executive Briefing]{C.RESET}")
            print(f"  • Prospect: {briefing['lead_email']} ({briefing['lead_company']})")
            print(f"  • Detected Sentiment: {C.YELLOW}{briefing['sentiment_category']}{C.RESET}")
            print(f"  • Incoming Snippet: \\\"{briefing['incoming_reply']}\\\"")
            print(f"  • Synthesized Closer Response:\\n    {C.GREEN}{briefing['automated_response']}{C.RESET}")
            print(f"  • Human Intervention Required: {C.RED if briefing['requires_human_intervention'] else C.GREEN}{briefing['requires_human_intervention']}{C.RESET}\\n")
            self.speak("Autonomous reply generated driving prospect to 15-minute Calendly booking.")

        elif sub in ["notify", "notifications"]:
            notifs = account_fleet.get_notifications()
            print(f"\\n{C.CYAN}{C.BOLD}🔔 [Executive Lead Notifications & Meeting Bookings ({len(notifs)})]{C.RESET}")
            for n in notifs[:10]:
                urgent = C.RED if n.get("requires_human_intervention") else C.GREEN
                print(f"  • [{n.get('timestamp')}] {n.get('lead_email')} ({n.get('sentiment_category')}) - Action: {urgent}{'HUMAN CALL ESCALATED' if n.get('requires_human_intervention') else 'AUTONOMOUS'}{C.RESET}")
                print(f"    Snippet: \\\"{n.get('incoming_reply')}\\\"")
                print(f"    Booking Link: {n.get('booking_link')}\\n")

        elif sub == "dispatch":"""

norm_c = content.replace("\r\n", "\n")
norm_needle = old_needle.replace("\r\n", "\n")
norm_add = (old_needle.split('        elif sub == "dispatch":')[0] + addition).replace("\r\n", "\n")

if norm_needle in norm_c:
    new_c = norm_c.replace(norm_needle, norm_add, 1)
    if "\r\n" in content:
        new_c = new_c.replace("\n", "\r\n")
    cli_path.write_text(new_c, encoding="utf-8")
    print("SUCCESSFULLY_PATCHED_JARVIS_CLI")
else:
    print("NEEDLE_NOT_FOUND")

