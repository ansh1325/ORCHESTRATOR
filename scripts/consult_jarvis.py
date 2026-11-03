import sys
from core.config import settings

sys_prompt = """You are JARVIS Central Brain (Chief Systems Architect: Ansh Tiwari).
Formulate the authoritative, bulletproof, production-grade architectural solutions for:
1. Challenge A: Live Extraction on Auth-Walled & Rate-Limited Platforms (LinkedIn, Instagram, Google, X/Twitter) for 1500+ decision-maker leads without getting banned or requiring brittle manual browser clicks.
2. Challenge B: API Pacing, Concurrency Scaling & Token Quota Multiplexing on Groq / Meta Llama 3.3 70B (handling unbounded swarms with zero 429 rate limit errors).

Output a deep, structured, first-principles technical architecture with concrete code patterns that we can implement directly into JARVIS."""

llm = settings.get_llm_client()
if llm and not settings.is_mock():
    resp = settings.create_chat_completion(
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": "Deliver the comprehensive architectural blueprints and implementation designs now."}
        ],
        temperature=0.2
    )
    content = resp.choices[0].message.content or ""
    with open("workspaces/jarvis_solutions.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("JARVIS delivered the solutions in workspaces/jarvis_solutions.md")
else:
    print("Mock/No LLM")

