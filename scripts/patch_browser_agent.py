path = 'D:/LlamaOrchestrator/core/browser_agent.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

target = """                    if parsed:
                        # Guard B: If media goal and not yet on video watch page, do not complete prematurely
                        if is_media_goal and parsed.get("action") in ["complete", "extract_content"] and not is_on_watch_page:
                            pass  # Fall through to click the actual video link
                        elif is_media_goal and ("/results" in current_url or "typed" in history_str) and parsed.get("action") == "click":
                            target_id = parsed.get("element_id")
                            clicked_el = next((e for e in elements if e.index == target_id), None)
                            if clicked_el and clicked_el.tag in ["input", "textarea"]:
                                pass  # Fall through to click the actual video link
                            else:
                                return parsed
                        else:
                            return parsed"""

replacement = """                    if parsed:
                        # Guard B: If media goal and not yet on video watch page, do not complete or extract prematurely
                        if is_media_goal and not is_on_watch_page and (parsed.get("action") in ["complete", "extract_content", "extract", "extract_text", "wait", "scroll"] or parsed.get("action") != "click"):
                            pass  # Fall through to click the actual video link
                        elif is_media_goal and ("/results" in current_url or "typed" in history_str) and parsed.get("action") == "click":
                            target_id = parsed.get("element_id")
                            clicked_el = next((e for e in elements if e.index == target_id), None)
                            if clicked_el and clicked_el.tag in ["input", "textarea"]:
                                pass  # Fall through to click the actual video link
                            else:
                                return parsed
                        else:
                            return parsed"""

text_norm = text.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')
replacement_norm = replacement.replace('\r\n', '\n')

if target_norm in text_norm:
    new_text = text_norm.replace(target_norm, replacement_norm, 1)
    if '\r\n' in text:
        new_text = new_text.replace('\n', '\r\n')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_text)
    print('Updated successfully!')
else:
    print('Target not found in text!')

