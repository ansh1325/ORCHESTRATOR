# -*- coding: utf-8 -*-
"""
AgentFactory – utility for creating sub‑agents at runtime.

Jarvis needs to spin up new workers (lead scraper, email sender, follow‑up
scheduler) without manual intervention. This tiny helper wraps the
Antigravity `define_subagent` and `invoke_subagent` tools so the orchestrator
can decide *when* to create an agent and *what* capabilities it should have.
"""

from typing import Dict, Any

# The Antigravity tool wrappers are injected into the execution environment.
# They are available as top‑level functions when this file runs inside the
# LlamaOrchestrator process.

def _define_subagent(payload: Dict[str, Any]) -> Any:
    """Call the `define_subagent` tool.
    The function exists only to keep the module import‑friendly – the real
    tool is provided by the host environment.
    """
    from functions import define_subagent
    return define_subagent(payload)


def _invoke_subagent(payload: Dict[str, Any]) -> Any:
    """Call the `invoke_subagent` tool and return the conversation ID.
    """
    from functions import invoke_subagent
    result = invoke_subagent(payload)
    # The tool returns a dict that includes "ConversationId" – the ID we use
    # later with `send_message`.
    return result.get("ConversationId")


class AgentFactory:
    """Factory for dynamic sub‑agents.

    Example usage::

        scraper_id = AgentFactory.create(
            name="lead_scraper",
            role="Lead Scraper Agent",
            prompt="Gather 1500 full‑stack dev leads...",
            tools={"mcp": True, "subagents": False, "write": True},
        )
    """

    @staticmethod
    def _definition(name: str, role: str, prompt: str, tools: Dict[str, bool]) -> Dict[str, Any]:
        return {
            "Name": name,
            "Description": f"Dynamic agent for {role}",
            "SystemPrompt": prompt,
            "EnableMCPTools": tools.get("mcp", False),
            "EnableSubagentTools": tools.get("subagents", False),
            "EnableWriteTools": tools.get("write", False),
        }

    @staticmethod
    def create(name: str, role: str, prompt: str, tools: Dict[str, bool]) -> str:
        """Define (if not already defined) and invoke a sub‑agent.

        Returns the conversation ID of the running sub‑agent, which can be
        used with `send_message` to give it further instructions.
        """
        # 1️⃣ Define the sub‑agent type – safe to call multiple times; the
        #    system ignores duplicate definitions.
        _define_subagent(AgentFactory._definition(name, role, prompt, tools))

        # 2️⃣ Invoke an instance of that type. Use a branched workspace so the
        #    sub‑agent can create files without affecting the main repo.
        payload = {
            "Model": "inherit",
            "Prompt": prompt,
            "Role": role,
            "TypeName": name,
            "Workspace": "branch",
        }
        return _invoke_subagent(payload)

# End of file

