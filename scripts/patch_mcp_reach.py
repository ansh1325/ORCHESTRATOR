with open('core/mcp_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add tool implementations
old_tools_end = '''    def tool_browser_use_execute(self, task: str, max_steps: int = 15, headless: bool = False) -> dict[str, Any]:
        """
        Executes a dynamic browser automation objective using the official 'browser-use' engine.
        Uses Set-of-Marks visual perception and multi-step reasoning to accomplish complex web tasks
        without brittle hardcoded selectors.
        """
        from core.browser_use_engine import browser_use_engine
        return browser_use_engine.execute_task_sync(task=task, max_steps=max_steps, headless=headless)'''

new_tools = '''    def tool_browser_use_execute(self, task: str, max_steps: int = 15, headless: bool = False) -> dict[str, Any]:
        """
        Executes a dynamic browser automation objective using the official 'browser-use' engine.
        Uses Set-of-Marks visual perception and multi-step reasoning to accomplish complex web tasks
        without brittle hardcoded selectors.
        """
        from core.browser_use_engine import browser_use_engine
        return browser_use_engine.execute_task_sync(task=task, max_steps=max_steps, headless=headless)

    def tool_reach_universal_search(self, platform: str, query: str, limit: int = 5, location: str | None = None) -> list[dict[str, Any]]:
        """Agent-Reach Tool: Dispatches search across 14 platforms (linkedin, reddit, twitter, github, youtube, etc.) with zero API keys."""
        from core.agent_reach_powerup import AgentReachEngine
        return AgentReachEngine.universal_search(platform=platform, query=query, limit=limit, location=location)

    def tool_reach_harvest_leads(self, niche: str, location: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """Agent-Reach Tool: Harvests verified decision-makers via Public-First Scoped Syndication, bypassing platform login walls."""
        from core.agent_reach_powerup import AgentReachEngine
        return AgentReachEngine.search_linkedin_leads(niche=niche, location=location, limit=limit)

    def tool_reach_read_target(self, target_url: str) -> dict[str, Any]:
        """Agent-Reach Tool: Universal Markdown Reader for any webpage or social post."""
        from core.agent_reach_powerup import AgentReachEngine
        return AgentReachEngine.read_url_content(target_url=target_url)

    def tool_reach_doctor(self) -> dict[str, Any]:
        """Agent-Reach Tool: Inspects connectivity, channel health, and browser session status across all platforms."""
        from core.agent_reach_powerup import AgentReachEngine
        return AgentReachEngine.doctor()'''

assert old_tools_end in content, "old_tools_end not found!"
content = content.replace(old_tools_end, new_tools)

# 2. Add tool definitions
old_defs_end = '''            {"name": "browser_use_execute", "description": "Autonomous Vision-Action Web Agent powered by 'browser-use': dynamically navigates, operates, and solves tasks on any website without hardcoded selectors."}
        ]'''

new_defs = '''            {"name": "browser_use_execute", "description": "Autonomous Vision-Action Web Agent powered by 'browser-use': dynamically navigates, operates, and solves tasks on any website without hardcoded selectors."},
            {"name": "reach_universal_search", "description": "Agent-Reach: Dispatches search across 14 platforms (linkedin, reddit, twitter, github, youtube, etc.) with zero API keys."},
            {"name": "reach_harvest_leads", "description": "Agent-Reach: Harvests verified decision-makers via Public-First Scoped Syndication, bypassing platform login walls."},
            {"name": "reach_read_target", "description": "Agent-Reach: Universal Markdown Reader for any webpage or social post."},
            {"name": "reach_doctor", "description": "Agent-Reach: Inspects connectivity, channel health, and browser session status across all platforms."}
        ]'''

assert old_defs_end in content, "old_defs_end not found!"
content = content.replace(old_defs_end, new_defs)

# 3. Add JSON-RPC dispatch
old_dispatch_end = '''                elif tool_name == "browser_use_execute":
                    res = self.tool_browser_use_execute(
                        task=tool_args["task"],
                        max_steps=tool_args.get("max_steps", 15),
                        headless=tool_args.get("headless", False)
                    )
                else:'''

new_dispatch = '''                elif tool_name == "browser_use_execute":
                    res = self.tool_browser_use_execute(
                        task=tool_args["task"],
                        max_steps=tool_args.get("max_steps", 15),
                        headless=tool_args.get("headless", False)
                    )
                elif tool_name == "reach_universal_search":
                    res = self.tool_reach_universal_search(
                        platform=tool_args["platform"],
                        query=tool_args["query"],
                        limit=tool_args.get("limit", 5),
                        location=tool_args.get("location")
                    )
                elif tool_name == "reach_harvest_leads":
                    res = self.tool_reach_harvest_leads(
                        niche=tool_args["niche"],
                        location=tool_args.get("location"),
                        limit=tool_args.get("limit", 10)
                    )
                elif tool_name == "reach_read_target":
                    res = self.tool_reach_read_target(target_url=tool_args["target_url"])
                elif tool_name == "reach_doctor":
                    res = self.tool_reach_doctor()
                else:'''

assert old_dispatch_end in content, "old_dispatch_end not found!"
content = content.replace(old_dispatch_end, new_dispatch)

with open('core/mcp_server.py', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("core/mcp_server.py patched with Agent-Reach tools!")

