with open('jarvis_cli.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add help lines
old_help = '''        print(f"  {C.CYAN}hermes [skills|memory|learn]{C.RESET} Hermes Supercharger (44+ skills, tiered memory, self-learning)")'''
new_help = '''        print(f"  {C.CYAN}hermes [skills|memory|learn]{C.RESET} Hermes Supercharger (44+ skills, tiered memory, self-learning)")
        print(f"  {C.CYAN}reach <platform> <query>{C.RESET}  Agent-Reach Multi-Platform Engine (LinkedIn, Reddit, Twitter, YouTube, GitHub)")
        print(f"  {C.CYAN}reach leads <niche> [loc]{C.RESET} Harvest verified social leads bypassing login walls")'''
assert old_help in content, "old_help not found"
content = content.replace(old_help, new_help)

# 2. Add handle_reach_cmd before handle_browser_cmd
old_browser_cmd = '''    async def handle_browser_cmd(self, parts: list[str]):
        """Direct browser automation commands from terminal."""'''

new_reach_cmd = '''    def handle_reach_cmd(self, parts: list[str]):
        """
        Agent-Reach Multi-Platform Intelligence Interface.
        Queries LinkedIn, Twitter, Reddit, YouTube, GitHub, Instagram, etc. with zero API fees.
        """
        from core.agent_reach_powerup import AgentReachEngine
        if len(parts) < 2 or parts[1].lower() in ["help", "info"]:
            print(f"\\n{C.CYAN}{C.BOLD}🌐 [Agent-Reach // Multi-Platform Intelligence Engine]{C.RESET}")
            print("  Access public & walled-garden platforms without paid APIs or key limits.")
            print(f"  {C.CYAN}reach doctor{C.RESET}                   Inspect connectivity and health across 14 channels")
            print(f"  {C.CYAN}reach leads <niche> [location]{C.RESET} Harvest verified social leads via public syndication")
            print(f"  {C.CYAN}reach linkedin <query>{C.RESET}         Search LinkedIn jobs or public profiles")
            print(f"  {C.CYAN}reach reddit <query|r/sub>{C.RESET}    Search Reddit discussions or subreddit posts")
            print(f"  {C.CYAN}reach twitter <query>{C.RESET}          Search Twitter/X public posts and sentiment")
            print(f"  {C.CYAN}reach github <query>{C.RESET}           Search GitHub repositories and code")
            print(f"  {C.CYAN}reach youtube <query|url>{C.RESET}      Search YouTube videos or extract transcripts")
            print(f"  {C.CYAN}reach read <url>{C.RESET}               Universal markdown reader for any web page\\n")
            return

        sub = parts[1].lower()
        if sub in ["doctor", "health", "status", "diag"]:
            doc = AgentReachEngine.doctor()
            print(f"\\n{C.CYAN}{C.BOLD}🌐 [Agent-Reach System Health: {doc.get('overall_health')}]{C.RESET}")
            print(f"  • Total Channels Loaded: {C.GREEN}{doc.get('installed_channels')}{C.RESET}")
            print(f"  • Shared Browser Profile: {doc.get('shared_browser_profile')}")
            print(f"  • Profile Active: {C.GREEN if doc.get('profile_active') else C.YELLOW}{doc.get('profile_active')}{C.RESET}\\n")
            print(f"{C.BOLD}Platform Channel Registry:{C.RESET}")
            for ch, h in doc.get("channel_health", {}).items():
                status_str = f"{C.GREEN}ONLINE{C.RESET}" if h.get("available") else f"{C.RED}OFFLINE{C.RESET}"
                print(f"  • {ch:12}: {status_str} (Actions: {', '.join(h.get('actions', []))})")
            print()
            self.speak("Agent Reach diagnostics complete. All channels online.")

        elif sub in ["leads", "lead", "harvest"]:
            if len(parts) < 3:
                print(f"{C.RED}Usage: reach leads <niche> [location]{C.RESET}")
                return
            niche = parts[2]
            loc = parts[3] if len(parts) > 3 else None
            print(f"\\n{C.CYAN}[Agent-Reach]{C.RESET} Harvesting verified social leads for {C.YELLOW}{niche}{C.RESET} via Public-First Syndication...")
            leads = AgentReachEngine.search_linkedin_leads(niche, location=loc, limit=10)
            print(f"\\n{C.GREEN}✓ Harvested {len(leads)} Decision-Maker Leads (Zero Auth Wall):{C.RESET}")
            for idx, ld in enumerate(leads, start=1):
                print(f"  {idx}. {C.BOLD}{ld.get('name')}{C.RESET} - {ld.get('title')} @ {C.CYAN}{ld.get('company')}{C.RESET}")
                print(f"     Profile: {C.DIM}{ld.get('profile_url')}{C.RESET}")
            print()
            self.speak(f"Harvested {len(leads)} verified leads across public social syndication.")

        elif sub in AgentReachEngine.SUPPORTED_PLATFORMS:
            query = " ".join(parts[2:]) if len(parts) > 2 else "latest"
            print(f"\\n{C.CYAN}[Agent-Reach // {sub.upper()}]{C.RESET} Query: {C.YELLOW}{query}{C.RESET}")
            items = AgentReachEngine.universal_search(sub, query, limit=5)
            print(f"\\n{C.GREEN}✓ Retrieved {len(items)} Items from {sub.title()}:{C.RESET}")
            for idx, it in enumerate(items, start=1):
                title = it.get("title") or it.get("text", "")[:60] or "Result"
                url = it.get("url") or it.get("profile_url", "")
                author = f" (by {it.get('author')})" if it.get("author") else ""
                print(f"  {idx}. {C.BOLD}{title}{C.RESET}{author}")
                if url:
                    print(f"     URL: {C.DIM}{url}{C.RESET}")
            print()
            self.speak(f"Retrieved {len(items)} results from {sub.title()}.")

        elif sub in ["read", "fetch"]:
            if len(parts) < 3:
                print(f"{C.RED}Usage: reach read <url>{C.RESET}")
                return
            url = parts[2]
            print(f"\\n{C.CYAN}[Agent-Reach Reader]{C.RESET} Fetching clean text from: {C.YELLOW}{url}{C.RESET}")
            doc = AgentReachEngine.read_url_content(url)
            print(f"\\n{C.BOLD}{doc.get('title', 'Document')}{C.RESET}\\n")
            print(doc.get("content", "")[:1000])
            print(f"\\n{C.DIM}... [Content truncated for terminal preview]{C.RESET}\\n")

        else:
            query = " ".join(parts[1:])
            print(f"\\n{C.CYAN}[Agent-Reach Universal]{C.RESET} Querying across web & social: {C.YELLOW}{query}{C.RESET}")
            items = AgentReachEngine.universal_search("web", query, limit=5)
            for idx, it in enumerate(items, start=1):
                print(f"  {idx}. {it.get('title')} ({it.get('url')})")

    async def handle_browser_cmd(self, parts: list[str]):
        """Direct browser automation commands from terminal."""'''

assert old_browser_cmd in content, "old_browser_cmd not found"
content = content.replace(old_browser_cmd, new_reach_cmd)

# 3. Add directive handling in process_directive
old_reach_dir = '''        # REA (Reverse Engineer Anything) Engine
        if low.startswith("rea"):'''

new_reach_dir = '''        # Agent-Reach Multi-Platform Intelligence (LinkedIn, Reddit, Twitter, YouTube, GitHub)
        if low.startswith("reach ") or low == "reach":
            parts = line.split()
            self.handle_reach_cmd(parts)
            return True

        # REA (Reverse Engineer Anything) Engine
        if low.startswith("rea"):'''

assert old_reach_dir in content, "old_reach_dir not found"
content = content.replace(old_reach_dir, new_reach_dir)

# 4. Add reach step execution in execute_autonomous_step
old_step_exec = '''        elif mode == "browser":
            print(f"\\n{C.YELLOW}{C.BOLD}[Central Brain Router]{C.RESET} Directive classified as autonomous web/browser action.")
            await self.handle_autonomous_browse(goal, intent=step)
            return True'''

new_step_exec = '''        elif mode == "reach":
            print(f"\\n{C.YELLOW}{C.BOLD}[Central Brain Router]{C.RESET} Directive classified as Agent-Reach multi-platform intelligence.")
            from core.agent_reach_powerup import AgentReachEngine
            plat = step.get("platform", "web")
            q = step.get("query") or goal
            items = AgentReachEngine.universal_search(plat, q, limit=step.get("count", 5), location=step.get("location"))
            print(f"\\n{C.GREEN}✓ Retrieved {len(items)} records from {plat.title()} via Agent-Reach.{C.RESET}\\n")
            for idx, it in enumerate(items[:5], start=1):
                t = it.get("title") or it.get("name") or "Record"
                u = it.get("url") or it.get("profile_url") or ""
                print(f"  {idx}. {t} ({u})")
            print()
            return True
        elif mode == "browser":
            print(f"\\n{C.YELLOW}{C.BOLD}[Central Brain Router]{C.RESET} Directive classified as autonomous web/browser action.")
            await self.handle_autonomous_browse(goal, intent=step)
            return True'''

assert old_step_exec in content, "old_step_exec not found"
content = content.replace(old_step_exec, new_step_exec)

# 5. Add zero-model fallback in decompose_directive_cognitively
old_fb = '''        # Complex multi-step missions, business building, lead gen, and software swarms take highest precedence'''

new_fb = '''        # Agent-Reach social / platform intelligence intent (LinkedIn, Reddit, Twitter, Instagram, GitHub, YouTube)
        if any(plat in low for plat in ["linkedin", "reddit", "twitter", "x.com", "instagram", "github", "youtube", "bilibili"]) and any(w in low for w in ["find", "search", "scrape", "get", "harvest", "leads", "lead", "posts", "post", "jobs", "job", "tweets", "tweet", "videos"]):
            target_plat = "linkedin"
            for p in ["linkedin", "reddit", "twitter", "instagram", "github", "youtube", "bilibili"]:
                if p in low or (p == "twitter" and "x.com" in low):
                    target_plat = p
                    break
            return {
                "thought": f"Agent-Reach platform intelligence mission for {target_plat}",
                "steps": [{
                    "mode": "reach",
                    "platform": target_plat,
                    "query": line,
                    "goal": f"Retrieve intelligence from {target_plat.title()} via Agent-Reach"
                }]
            }

        # Complex multi-step missions, business building, lead gen, and software swarms take highest precedence'''

assert old_fb in content, "old_fb not found"
content = content.replace(old_fb, new_fb)

with open('jarvis_cli.py', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("jarvis_cli.py patched with Agent-Reach commands and cognitive routing!")

