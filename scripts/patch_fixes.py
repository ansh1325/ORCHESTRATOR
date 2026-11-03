# Fix 1: core/browser_agent.py
agent_path = 'D:/LlamaOrchestrator/core/browser_agent.py'
with open(agent_path, 'r', encoding='utf-8') as f:
    agent_text = f.read()

# In browser_agent.py, after `if "action" in parsed:`
agent_target = '''                if "action" in parsed:
                    # Guard A: Never allow the LLM to type imperative commands or meta-prompts into search bars'''

agent_replacement = '''                if "action" in parsed:
                    if parsed.get("action") == "click":
                        target_id = parsed.get("element_id")
                        clicked_el = next((e for e in elements if e.index == target_id), None)
                        if clicked_el and any(g in (clicked_el.text + " " + clicked_el.aria_label).lower() for g in ["guest", "continue as guest", "use without account"]):
                            if "guest" not in str(parsed.get("reason", "")).lower():
                                parsed["reason"] = f"Bypass obstacle via guest button ({parsed.get('reason', '')})"
                    # Guard A: Never allow the LLM to type imperative commands or meta-prompts into search bars'''

agent_text_norm = agent_text.replace('\r\n', '\n')
agent_target_norm = agent_target.replace('\r\n', '\n')
agent_rep_norm = agent_replacement.replace('\r\n', '\n')

if agent_target_norm in agent_text_norm:
    new_agent_text = agent_text_norm.replace(agent_target_norm, agent_rep_norm, 1)
    if '\r\n' in agent_text:
        new_agent_text = new_agent_text.replace('\n', '\r\n')
    with open(agent_path, 'w', encoding='utf-8') as f:
        f.write(new_agent_text)
    print("Browser agent patched successfully!")
else:
    print("Browser agent target not found!")

# Fix 2: jarvis_cli.py
cli_path = 'D:/LlamaOrchestrator/jarvis_cli.py'
with open(cli_path, 'r', encoding='utf-8') as f:
    cli_text = f.read()

cli_target = '''                # Consolidate consecutive operations targeting same recipient into single batch step
                consolidated: list[dict[str, Any]] = []'''

cli_replacement = '''                for s in raw_steps:
                    if s.get("recipient") or any(w in str(s.get("goal", "")).lower() for w in ["mail", "email"]):
                        s["sub_action"] = "email"

                # Consolidate consecutive operations targeting same recipient into single batch step
                consolidated: list[dict[str, Any]] = []'''

cli_target_2 = '''                for s in consolidated:
                    step_text = f"{s.get('goal', '')} {s.get('body_instruction', '')}".lower()'''

cli_replacement_2 = '''                for s in consolidated:
                    step_text = f"{s.get('goal', '')} {s.get('body_instruction', '')}".lower()
                    if s.get("recipient") or any(w in step_text for w in ["mail", "email"]):
                        s["sub_action"] = "email"'''

cli_text_norm = cli_text.replace('\r\n', '\n')
cli_target_norm = cli_target.replace('\r\n', '\n')
cli_rep_norm = cli_replacement.replace('\r\n', '\n')

cli_target_2_norm = cli_target_2.replace('\r\n', '\n')
cli_rep_2_norm = cli_replacement_2.replace('\r\n', '\n')

if cli_target_norm in cli_text_norm and cli_target_2_norm in cli_text_norm:
    new_cli_text = cli_text_norm.replace(cli_target_norm, cli_rep_norm, 1)
    new_cli_text = new_cli_text.replace(cli_target_2_norm, cli_rep_2_norm, 1)
    if '\r\n' in cli_text:
        new_cli_text = new_cli_text.replace('\n', '\r\n')
    with open(cli_path, 'w', encoding='utf-8') as f:
        f.write(new_cli_text)
    print("Jarvis CLI patched successfully!")
else:
    print("Jarvis CLI target not found!")

