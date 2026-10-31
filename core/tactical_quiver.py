"""
LlamaOrchestrator Tactical Quiver & Cognitive Discretion Engine
Chief Systems Architect: Ansh Tiwari

"Just like an arrow given to a warrior archer — but first making the warrior
capable of understanding when to shoot this arrow and when not to use a nuke to blow off a door."

Implements the Cognitive Escalation Hierarchy & Tactical Tool Discretion:
- Tier 1: Direct Cognition & Deep Q&A (Chain-of-Thought, architecture, socratic reasoning — zero unnecessary tools).
- Tier 2: Standard Operations (Browsers, official APIs, standard file I/O).
- Tier 3: Autonomous Synthesis (Dynamic software maker, account fleet, recursive sub-DAGs).
- Tier 4: Heavy Tactical Arrow — REA (Reverse Engineer Anything: binaries, ASAR, network captures, zero-day audits).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from core.config import settings

logger = logging.getLogger("TacticalQuiver")


class ToolTier(str, Enum):
    TIER_1_COGNITIVE = "Tier 1: Direct Cognition & Socratic Reasoning"
    TIER_2_STANDARD = "Tier 2: Standard Operations (Browser / API / Files)"
    TIER_3_SYNTHETIC = "Tier 3: Autonomous Synthesis (Software Builder / Fleet)"
    TIER_4_TACTICAL_REA = "Tier 4: Heavy Tactical Arrow (Reverse Engineering Anything)"


@dataclass
class TacticalDecision:
    tier: ToolTier
    recommended_tools: list[str]
    tactical_rationale: str
    is_rea_appropriate: bool
    escalation_explanation: str
    suggested_action: str


class TacticalDiscretionEngine:
    """
    Cognitive Gatekeeper & Discretion Engine.
    Ensures JARVIS comprehends requirements with profound nuance and selects
    the exact right tool tier without over-escalating or using disproportionate force.
    """

    REA_EXTENSIONS = {".exe", ".dll", ".so", ".bin", ".dylib", ".asar", ".pcap", ".har", ".class", ".apk"}

    @classmethod
    def evaluate_directive(cls, directive: str, context: Optional[dict[str, Any]] = None) -> TacticalDecision:
        """
        Evaluates a user prompt or swarm task to determine the optimal tool tier
        with strict tactical discretion.
        """
        low = directive.lower().strip()

        # 1. Check for Heavy Tactical Arrow (Tier 4: REA)
        # ONLY appropriate when dealing with compiled binaries, ASAR electron packages, or raw packet captures
        has_rea_extension = any(ext in low for ext in cls.REA_EXTENSIONS)
        has_rea_keywords = any(kw in low for kw in [
            "reverse engineer", "decompile", "disassemble", "unpack asar",
            "pcap", "ghidra", "hopper", "ida pro", "crack binary", "analyze dll", "binary symbols"
        ])

        # Strict Negative Constraint: If it's a simple Q&A, conceptual query, or has an official API, REA is FORBIDDEN
        is_pure_question = (
            low.startswith(("what is", "why", "how does", "explain", "who is", "tell me about", "can you clarify"))
            and not any(act in low for act in ["decompile", "reverse engineer", "inspect binary", "disassemble"])
        )

        if (has_rea_extension or has_rea_keywords) and not is_pure_question:
            # Valid Tier 4 Application
            target_match = re.search(r'[\w\-/\\]+\.(?:exe|dll|so|asar|pcap|har|bin)', directive, re.IGNORECASE)
            target = target_match.group(0) if target_match else "target binary/capture"
            return TacticalDecision(
                tier=ToolTier.TIER_4_TACTICAL_REA,
                recommended_tools=["rea_inspect_binary", "rea_unpack_electron", "rea_analyze_traffic", "rea_clone_client"],
                tactical_rationale=f"Target '{target}' is a closed artifact without source code. Heavy tactical reverse-engineering is mathematically justified.",
                is_rea_appropriate=True,
                escalation_explanation="Decompilation and binary symbol extraction required to penetrate opaque binary/protocol boundaries.",
                suggested_action=f"Deploy REA MCP tools to inspect {target} and extract empirical telemetry."
            )

        # 2. Check for Synthetic Systems (Tier 3: Dynamic Software / Fleet)
        if any(kw in low for kw in ["fleet", "20 accounts", "20 gmail", "rate limit outreach", "build system", "system build", "self-constructing"]):
            return TacticalDecision(
                tier=ToolTier.TIER_3_SYNTHETIC,
                recommended_tools=["account_fleet", "dynamic_system_builder", "recursive_subdag"],
                tactical_rationale="Task requires persistent multi-worker topologies or new software construction.",
                is_rea_appropriate=False,
                escalation_explanation="Standard tools insufficient for multi-account load balancing or tool creation; requires Tier 3 Autonomous Synthesis.",
                suggested_action="Invoke AccountFleetManager or DynamicSystemBuilder with sandboxed verification."
            )

        # 3. Check for Standard Operations (Tier 2: Browser, Files, HTTP)
        if any(kw in low for kw in ["browse", "youtube", "play", "website", "leetcode", "search", "download", "export", "file", "email", "mail"]):
            return TacticalDecision(
                tier=ToolTier.TIER_2_STANDARD,
                recommended_tools=["browser_agent", "file_read", "file_write", "http_request"],
                tactical_rationale="Objective can be resolved via standard DOM perception, HTTP dispatch, or workspace file operations.",
                is_rea_appropriate=False,
                escalation_explanation="Proportionate force: Browser DOM interaction and standard protocols solve this with 100% precision. Heavy reverse engineering is unnecessary.",
                suggested_action="Route to Autonomous Browser Agent or Standard MCP file tools."
            )

        # 4. Pure Cognition & Architectural Q&A (Tier 1)
        return TacticalDecision(
            tier=ToolTier.TIER_1_COGNITIVE,
            recommended_tools=["central_brain_cot", "creator_memory"],
            tactical_rationale="Objective is conceptual, strategic, or architectural. Direct intelligence delivers immediate clarity.",
            is_rea_appropriate=False,
            escalation_explanation="Proportionate force: Zero external tools needed. Direct Chain-of-Thought reasoning is the most efficient and elegant response.",
            suggested_action="Provide structured, highly articulate response via Central Brain with Chain-of-Thought."
        )

    @classmethod
    def format_tactical_briefing(cls, decision: TacticalDecision) -> str:
        """Formats an executive briefing explaining why a specific tool tier was chosen."""
        return (
            f"🎯 [Tactical Discretion Protocol]\n"
            f"  • Selected Weaponry: {decision.tier.value}\n"
            f"  • Proportionate Rationale: {decision.tactical_rationale}\n"
            f"  • Escalation Audit: {decision.escalation_explanation}\n"
            f"  • Recommended Tools: {', '.join(decision.recommended_tools)}"
        )


# Global Singleton Instance
tactical_quiver = TacticalDiscretionEngine()

