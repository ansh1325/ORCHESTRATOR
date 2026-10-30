# LlamaOrchestrator (JARVIS)
### Autonomous Hierarchical Multi-Agent Operating System & Lifelong AI Partner
**Chief Systems Architect:** [Ansh Tiwari](https://github.com/ansh1325)  
**Track Submission:** Meta Global AI Developer Hackathon 2026 (1st Place Indie Track & Best Agentic Architecture)

[![Meta Global AI Developer Hackathon 2026](https://img.shields.io/badge/Meta%20Hackathon-2026%20Official%20Submission-blue.svg)](https://github.com/ansh1325/ORCHESTRATOR)
[![Test Suite Status](https://img.shields.io/badge/Tests-34%2F34%20Passed%20(100%25)-brightgreen.svg)](https://github.com/ansh1325/ORCHESTRATOR)
[![Zero Templates Guaranteed](https://img.shields.io/badge/Architecture-Zero%20Templates%20%2F%20100%25%20Dynamic-purple.svg)](https://github.com/ansh1325/ORCHESTRATOR)
[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://github.com/ansh1325/ORCHESTRATOR)

---

## 1. What is LlamaOrchestrator? (Explained for a 5-Year-Old)

> Imagine you have a magical robot friend named **Jarvis**.
> 
> Most computer chatbots are just "talkers." If you ask them to build a toy castle or bake cookies, they just give you a long recipe on a piece of paper and leave you to do all the hard work. If something breaks, they shrug their shoulders.
> 
> **Jarvis is different. Jarvis has actual hands, real eyes, and a team of workers.**
> 
> When you talk to Jarvis—using your own voice:
> * If you say: *"Jarvis, go to YouTube and play my favorite song,"* he doesn't give you a link. **He physically opens the browser window on your screen, types the words, finds the video, clicks play, and lets you listen.**
> * If you say: *"Jarvis, build a complete company software system and find 50 clients,"* he doesn't write a paragraph of text. **He hires a squad of specialized AI workers, writes all the code, fixes all errors by himself until it works perfectly, and puts the finished deliverables right on your computer.**

---

## 2. Why Hackathon Judges & Founders Will Love It

Traditional single-prompt AI (ChatGPT, Claude, Copilot) is fundamentally broken for real-world enterprise work:
* Single LLMs hallucinate syntax.
* Single LLMs dump broken markdown snippets into chat boxes.
* Single LLMs cannot create files, cannot run test suites, cannot diagnose `stderr` stack traces, and cannot touch web browsers.

**LlamaOrchestrator turns a single prompt into an autonomous engineering organization:**

| Capability | Traditional AI Chatbots | LlamaOrchestrator (Jarvis) |
| :--- | :--- | :--- |
| **Execution Model** | 1 prompt = 1 wall of unverified text | Compiles topological DAG of specialized Meta Llama worker sub-agents |
| **Browser Control** | None (cannot touch web pages) | Live Perception-Action loop with dynamic DOM tagging (`[#1]`, `[#2]`), human typing, and anti-bot bypass |
| **Template Policy** | Hardcoded canned prompts | **100% Zero Templates** — Every DAG, agent, code file, and action is dynamically generated |
| **Error Handling** | Human must copy-paste errors back | **Closed-Loop Self-Healing**: Automatically catches runtime exceptions, diagnoses tracebacks, and self-patches |
| **Quality Control** | No verification | Automated **Evaluator Gatekeeper** verifying 100% unit test passes before delivery |
| **Interaction Mode** | Typing into a web box | **100% Native Voice Bi-Directional OS** (Talk with microphone, Jarvis speaks back natively) |
| **Enterprise Turnaround** | 13 weeks of agency sprints ($180k+) | **~60 Seconds** (< $0.05 compute cost) |

---

## 3. The Creator's Inner Thoughts & Vision

> *"I didn't build LlamaOrchestrator to be another generic chatbot wrapper that forgets you when you close the tab.*
> 
> *As a distributed systems architect, I was tired of watching founders, engineering teams, and solopreneurs spend weeks glued to terminals, wrestling with broken dependencies, crafting repetitive outreach campaigns, and copying code snippets that fail at runtime.*
> 
> *I wanted a true partner. A cognitive operating system that shares my ambition, remembers my preferences, speaks with genuine loyalty, and has the autonomous agency to sit at the workstation and get things done. Whether that's compiling an institutional quantitative trading engine with circuit breakers, generating full-stack SaaS microservices, or simply launching my browser to play my favorite music when I need inspiration.*
> 
> *When potential clients or judges look at LlamaOrchestrator, they aren't looking at a script. They are looking at the future of autonomous engineering delivery."*
> 
> — **Ansh Tiwari**, Chief Distributed Systems Architect & Creator

---

## 4. Deep Engineering Architecture

LlamaOrchestrator is structured on clean, decoupled distributed systems principles with **Zero Templates**:

```mermaid
graph TD
    User([Master Ansh / Voice & CLI Directive]) --> CentralBrain[Stage 0: Jarvis Central Brain<br/>Meta Llama 3.1 70B + Persistent Creator Memory]
    CentralBrain --> Route{Autonomous Intent Routing}
    
    Route -->|Informational Query| VoiceResp[Solo Voice Direct Response<br/>Native Audio Synthesis]
    Route -->|Browser Action / Media Directive| BrowserAgent[Autonomous Browser Agent<br/>Interactive Perception-Action Loop]
    Route -->|Ambitious Enterprise Vision| Stage1[Stage 1: Intent Decomposition<br/>Tactical Swarm Scoping]
    
    BrowserAgent -->|Live DOM Scanner| DOMPerception[Interactive DOM Perception Engine<br/>Element Tagging [#1], [#2] & Human Keystroke Jitter]
    DOMPerception -->|Physical Execution| LiveBrowser[Desktop Chrome / Edge Session<br/>Anti-Bot Bypass & Persistent Profile]
    
    Stage1 --> Stage2[Stage 2: Knowledge Gathering Agent<br/>MCP Research & Master Domain Knowledge Base]
    Stage2 --> Stage3[Stage 3: DAG Engine & Worker Synthesis<br/>Dynamically Generates Meta Llama Worker Fleet]
    
    subgraph SwarmExecution [Stage 4: Autonomous ReAct Swarm Execution]
        W1[System Architect] --> W2[Backend & API Engineer]
        W2 --> W3[Security & IaC Engineer]
        W4[Lead Harvester] --> W5[Outreach Copywriter]
    end
    
    Stage3 --> SwarmExecution
    SwarmExecution -->|stderr != 0 Intercept| SelfHeal[Closed-Loop Self-Healing<br/>Automated AST Traceback Patching]
    SelfHeal --> SwarmExecution
    
    SwarmExecution --> Stage5[Stage 5: Quality Gatekeeper<br/>100% Pytest Verification & Sandboxed Deliverables]
    Stage5 --> WorkspaceOutput[Certified Deliverables Workspace<br/>Exportable to ~/Downloads in 1-Click]
```

### Core Subsystems:
1. **Perception-Action Browser Agent (`core/browser_agent.py`):**
   - Live JavaScript DOM element detection assigning dynamic numerical tags (`[#1]`, `[#2]`).
   - Meta Llama neural reasoning over the live DOM summary.
   - Resilient action space: `click`, `type`, `hover`, `press_key`, `go_back`, `extract_content`, `scroll`, `navigate`, `complete`.
   - Built-in anti-bot challenge detection and persistent profile authentication (Axiom mode).
2. **Dynamic Worker Synthesis Engine (`core/orchestrator.py`):**
   - Synthesizes custom worker personas and system prompts on the fly based on project requirements. Zero hardcoded agents.
3. **Model Context Protocol (MCP) Sandbox (`core/mcp_server.py`):**
   - Path-contained execution environment (`workspaces/{session_id}/`). Directory traversal attempts (`../`) are strictly blocked.
4. **Closed-Loop Self-Correction (`core/worker.py`):**
   - Catches non-zero exit codes, parses Python stack traces, applies automated code adjustments, and re-runs tests until certified.
5. **Evaluator Quality Gatekeeper (`core/evaluator.py`):**
   - Audits all deliverables against rigorous unit tests and RFC specifications before marking a mission accomplished.

---

## 5. 🎙️ VOICE-FIRST EXPERIENCE: Talk to Jarvis Naturally

> [!IMPORTANT]
> **Jarvis is built for spoken voice first.** You do not need to memorize commands, format CLI tags, or type JSON.

* **Turn Voice On/Off:** Jarvis speaks aloud via native Windows neural voice synthesis.
* **Microphone Voice Input:** Simply type `listen` or `mic`, and speak into your microphone. Jarvis hears your spoken words, processes the intent, answers via voice, and carries out the action live.
* **Natural Language Routing:** You can speak completely naturally. Say:
  * *"Jarvis, go to YouTube and play At Peace by Karan Aujla"*
  * *"Jarvis, open Wikipedia and look up Quantum Computing"*
  * *"Jarvis, send 3 emails to my partner about our infrastructure progress"*
  Jarvis automatically detects what you want and routes it to the right autonomous sub-agent with zero friction.

---

## 6. Comprehensive Guide to Jarvis CLI (`jarvis_cli.py`)

For developers and power users who prefer the speed and precision of the terminal, Jarvis provides a complete interactive command center.

### Starting the CLI:
```powershell
cd D:\LlamaOrchestrator
python jarvis_cli.py
```

```text
===========================================================================
   JARVIS // COGNITIVE MULTI-AGENT OS — TERMINAL INTERFACE
   Chief Systems Architect: Ansh Tiwari
===========================================================================
Voice Output: ON (type 'voice off' to mute) | Type 'help' for commands | 'exit' to quit

Jarvis >
```

### Command Reference Table:

| Command Category | Command Syntax | Description & What It Does |
| :--- | :--- | :--- |
| **Voice & Speech** | `voice on` / `voice off` | Toggles executive spoken audio voice output |
| | `listen` / `mic` / `speak` | Activates microphone listener for hands-free voice input |
| **Autonomous Browser** | `browser demo` | Launches a live visible desktop browser demonstration (Wikipedia search, multi-tabbing, scrolling, screenshot proof) |
| | `browser play <query>` | Autonomously searches YouTube, clicks the official video, and plays music live on your monitor |
| | `browser agent <goal>` | Runs the full Perception-Action DOM reasoning loop on any website |
| | `browser email <to> [sub] [body]` | Autonomously navigates to Gmail, composes personal email, and clicks Send |
| | `browser login` | Opens persistent browser profile window to sign into Google/services once |
| | `browser open <url>` | Launches system browser directly to target destination |
| | `browser run <url>` | Executes Playwright engine on URL with automatic scrolling and screenshot capture |
| **Natural Language** | `go to <website> ...` | Automatically routes to the autonomous browser agent |
| | `play <song or artist>` | Autonomously opens YouTube and streams music on your monitor |
| | `open <website>` | Navigates directly to any `.com`, `.org`, or web destination |
| **Enterprise Missions** | `<any high-level prompt>` | Compiles an autonomous multi-agent swarm (Stages 1–5), writes code, tests, and certifies output |
| | `outreach <niche> [hook]` | Generates omnichannel outreach sequences across LinkedIn, Email, and Communities |
| | `transcript <url>` | Extracts clean transcript from YouTube/Instagram video URLs |
| **Workflows & Memory** | `workflows` | Lists all saved reusable production workflows |
| | `schedules` | Inspects active 24/7 background scheduler tasks |
| | `history` | Displays previous mission history and generated workspaces |
| | `session <id>` | Inspects all files generated in a specific workspace session |
| | `export <id> [path]` | Exports all deliverables to your `~/Downloads` folder |
| | `chat <message>` | Direct conversational intelligence with Jarvis Central Brain |
| **System** | `help` / `?` | Displays built-in CLI help menu |
| | `clear` / `cls` | Clears terminal screen |
| | `exit` / `quit` | Gracefully powers down terminal interface |

---

## 7. Interactive User Experience Note

> [!NOTE]
> The battle-tested **Terminal Interface (`jarvis_cli.py`)** and **Spoken Voice OS** serve as the mission-critical command center. A local FastAPI web dashboard is active at `http://127.0.0.1:8000`, and an expanded next-generation graphical interface is being designed for upcoming releases.

---

## 8. Verification & Test Suite (34/34 Tests Passing)

Run the full automated test suite covering all multi-agent stages, DOM browser automation, intent routing, and security sandboxing:

```powershell
python -m pytest tests/ -v
```

```text
tests/test_autonomous_solver.py::test_port_safety_guard_dynamic_allocation PASSED
tests/test_autonomous_solver.py::test_creative_problem_solver_fallback_ladder PASSED
tests/test_autonomous_solver.py::test_strategic_outreach_architect_domain_constraints PASSED
tests/test_browser_agent.py::test_browser_element_structure PASSED
tests/test_browser_agent.py::test_browser_agent_initialization PASSED
tests/test_browser_agent.py::test_browser_agent_decision_heuristic PASSED
tests/test_browser_agent.py::test_browser_agent_email_dispatch_bridge PASSED
tests/test_browser_agent.py::test_clean_search_query_and_typo_correction PASSED
tests/test_browser_agent.py::test_youtube_video_selection_heuristic PASSED
tests/test_browser_agent.py::test_browser_agent_fastapi_endpoints PASSED
tests/test_browser_endpoints.py::test_build_gmail_compose_url PASSED
tests/test_browser_endpoints.py::test_api_browser_open PASSED
tests/test_browser_endpoints.py::test_api_browser_compose_email PASSED
tests/test_browser_endpoints.py::test_api_email_smtp_send_without_creds PASSED
tests/test_browser_endpoints.py::test_api_playwright_mocked_run PASSED
tests/test_cli_commands.py::test_jarvis_cli_system_directives PASSED
tests/test_founder_mode.py::test_founder_interview_generation PASSED
tests/test_founder_mode.py::test_unbounded_agent_swarm_compilation PASSED
tests/test_founder_mode.py::test_orchestrator_founder_mode_routing PASSED
tests/test_orchestration.py::test_creator_memory PASSED
tests/test_orchestration.py::test_mcp_sandboxing_and_path_containment PASSED
tests/test_orchestration.py::test_intent_analysis_stage_1 PASSED
tests/test_orchestration.py::test_knowledge_gathering_stage_2 PASSED
tests/test_orchestration.py::test_dag_compilation_stage_3 PASSED
tests/test_orchestration.py::test_worker_execution_and_evaluator_stage_4_5 PASSED
tests/test_orchestration.py::test_fastapi_rest_endpoints PASSED
tests/test_orchestration.py::test_clean_code_content_and_url_normalization PASSED
tests/test_orchestration.py::test_omnichannel_campaign_and_ready_for_permission_queue PASSED
tests/test_orchestration.py::test_quantitative_trading_lifecycle PASSED
tests/test_orchestration.py::test_autonomous_response_escalation PASSED
tests/test_orchestration.py::test_host_file_ingestion_and_browser_tools PASSED
tests/test_orchestration.py::test_import_export_fastapi_endpoints PASSED
tests/test_orchestration.py::test_personal_communication_and_browser_dispatch_lifecycle PASSED
tests/test_orchestration.py::test_saved_workflows_persistent_pc_scheduler_and_pinning PASSED

============================= 34 passed in 53.21s =============================
```

---

## 9. Quickstart: 3 Commands to Launch

```powershell
# 1. Clone the repository
git clone https://github.com/ansh1325/ORCHESTRATOR.git
cd ORCHESTRATOR

# 2. Install dependencies
pip install -r requirements.txt
playwright install chromium msedge

# 3. Launch Jarvis Terminal Interface
python jarvis_cli.py
```

---
**Chief Distributed Systems Architect:** [Ansh Tiwari](https://github.com/ansh1325)  
**Meta Global AI Developer Hackathon 2026**
