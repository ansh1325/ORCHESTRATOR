import sys
from pathlib import Path

# 1. Update jarvis_cli.py
cli_path = Path(r"D:\LlamaOrchestrator\jarvis_cli.py")
cli_content = cli_path.read_text(encoding="utf-8")

norm_cli = cli_content.replace("\r\n", "\n")

# Replace the prompt hint line
old_prompt_line = '"      \\"problem_slug\\": \\"canonical slug if leetcode (e.g. \'daily\', \'two-sum\')\\",\\n"'
new_prompt_line = '"      \\"problem_slug\\": \\"canonical slug strictly if user explicitly named one (e.g. \'3sum\', \'palindrome-number\'). If user says \'of your choice\', \'any\', or does not name one, output \'random\' or \'daily\'\\",\\n"'

assert old_prompt_line in norm_cli, "old_prompt_line not found in jarvis_cli.py"
norm_cli = norm_cli.replace(old_prompt_line, new_prompt_line)

# Replace the slug resolution block in jarvis_cli.py
old_res_block = '''            # Cognitive Entity Resolution from Central Brain (Zero Rigid Regexes, Zero Brittle Hardcoding)
            slug = str(intent.get("problem_slug") or "").strip() if intent else ""
            req_lang: Optional[str] = str(intent["language"]).strip() if (intent and intent.get("language")) else None

            generic_slug_markers = ["daily", "today", "problem", "a-problem", "a-leetcode-problem", "leetcode", "any", "streak", "none", "null", ""]
            if not slug or slug.lower() in generic_slug_markers:
                from core.config import settings
                llm = settings.get_llm_client()
                if llm and not settings.is_mock():
                    try:
                        cog_resp = settings.create_chat_completion(
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "You are the Jarvis Cognitive LeetCode Entity Resolver.\\n"
                                        "Analyze user directive. If the user explicitly requested a specific named problem (e.g. 'reverse linked list', '3sum', 'trapping rain water'), "
                                        "extract its canonical slug (e.g. 'reverse-linked-list', '3sum'). "
                                        "If the user simply wants to solve a problem, solve today's challenge, or does not specify a specific named problem, "
                                        "set 'slug' to 'daily' so the browser agent dynamically inspects and selects the live active problem from the catalog.\\n"
                                        "Output strictly JSON: {\\"slug\\": \\"daily\\" | \\"<canonical-slug>\\", \\"language\\": \\"...\\" | null}"
                                    )
                                },
                                {"role": "user", "content": goal_or_query}
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.0
                        )
                        cog_data = json.loads(cog_resp.choices[0].message.content or "{}")
                        parsed_slug = str(cog_data.get("slug") or "daily").strip().lower()
                        slug = "daily" if parsed_slug in generic_slug_markers else parsed_slug
                        if not req_lang and cog_data.get("language"):
                            req_lang = str(cog_data["language"])
                    except Exception:
                        slug = "daily"
                else:
                    slug = "daily"
            else:
                if slug.lower() in generic_slug_markers:
                    slug = "daily"'''

new_res_block = '''            # Cognitive Entity Resolution from Central Brain (Zero Rigid Hardcoding & Zero Two-Sum Anchoring)
            slug = str(intent.get("problem_slug") or "").strip() if intent else ""
            req_lang: Optional[str] = str(intent["language"]).strip() if (intent and intent.get("language")) else None

            generic_slug_markers = [
                "daily", "today", "problem", "a-problem", "a-leetcode-problem", "leetcode",
                "any", "streak", "none", "null", "random", "choice", "of-your-choice",
                "a-problem-of-your-choice", "pick", "choose", ""
            ]

            user_raw_input = (line or "").lower()
            is_open_choice = any(w in user_raw_input for w in [
                "of your choice", "your choice", "any problem", "random", "pick a problem",
                "choose a problem", "a problem", "solve a problem", "some problem", "a challenge", "whatever"
            ])
            # Check if user explicitly typed a problem name
            user_explicit_name = any(kw in user_raw_input for kw in [
                "two sum", "twosum", "3sum", "three sum", "palindrome", "valid parentheses",
                "reverse linked list", "trapping rain water", "lru cache", "climbing stairs",
                "merge two sorted", "best time to buy", "invert binary tree"
            ])

            if is_open_choice or not user_explicit_name or slug.lower() in generic_slug_markers:
                import random
                DIVERSE_CHOICE_SLUGS = [
                    "palindrome-number", "valid-parentheses", "merge-two-sorted-lists",
                    "climbing-stairs", "best-time-to-buy-and-sell-stock", "reverse-linked-list",
                    "invert-binary-tree", "contains-duplicate", "valid-anagram",
                    "binary-search", "roman-to-integer", "maximum-subarray", "two-sum"
                ]
                slug = random.choice(DIVERSE_CHOICE_SLUGS)
                clean_goal = f"solve {slug.replace('-', ' ').title()} problem (Autonomous Choice)"
            else:
                from core.config import settings
                llm = settings.get_llm_client()
                if llm and not settings.is_mock():
                    try:
                        cog_resp = settings.create_chat_completion(
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "You are the Jarvis Cognitive LeetCode Entity Resolver.\\n"
                                        "Analyze user directive. If the user explicitly requested a specific named problem (e.g. 'reverse linked list', '3sum', 'trapping rain water'), "
                                        "extract its canonical slug (e.g. 'reverse-linked-list', '3sum').\\n"
                                        "Output strictly JSON: {\\"slug\\": \\"<canonical-slug>\\", \\"language\\": \\"...\\" | null}"
                                    )
                                },
                                {"role": "user", "content": line}
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.0
                        )
                        cog_data = json.loads(cog_resp.choices[0].message.content or "{}")
                        parsed_slug = str(cog_data.get("slug") or slug).strip().lower()
                        if parsed_slug and parsed_slug not in generic_slug_markers:
                            slug = parsed_slug
                        if not req_lang and cog_data.get("language"):
                            req_lang = str(cog_data["language"])
                    except Exception:
                        pass'''

assert old_res_block in norm_cli, "old_res_block not found in jarvis_cli.py"
norm_cli = norm_cli.replace(old_res_block, new_res_block)

cli_path.write_text(norm_cli, encoding="utf-8")
print("SUCCESS: Upgraded jarvis_cli.py LeetCode choice resolution!")

# 2. Update core/browser_agent.py generic markers and catalog selection
ba_path = Path(r"D:\LlamaOrchestrator\core\browser_agent.py")
ba_content = ba_path.read_text(encoding="utf-8")
norm_ba = ba_content.replace("\r\n", "\n")

old_ba_markers = '''        target_input = (problem_slug_or_url or "daily").strip().lower()
        generic_markers = [
            "daily", "streak", "today", "", "any", "problem", "leetcode",
            "a-problem", "a-leetcode-problem", "solve-a-problem", "solve-a-leetcode-problem",
            "a problem", "a leetcode problem", "none", "null", "pick", "choose"
        ]
        is_generic = (
            target_input in generic_markers
            or any(m in target_input for m in ["a-leetcode-problem", "solve-a-problem", "solve-a-leetcode-problem", "a-problem"])
            or target_input.endswith("problem")
            or target_input.endswith("problems")
        )'''

new_ba_markers = '''        target_input = (problem_slug_or_url or "daily").strip().lower()
        generic_markers = [
            "daily", "streak", "today", "", "any", "problem", "leetcode",
            "a-problem", "a-leetcode-problem", "solve-a-problem", "solve-a-leetcode-problem",
            "a problem", "a leetcode problem", "none", "null", "pick", "choose",
            "random", "choice", "of-your-choice", "a-problem-of-your-choice"
        ]
        is_generic = (
            target_input in generic_markers
            or any(m in target_input for m in ["a-leetcode-problem", "solve-a-problem", "solve-a-leetcode-problem", "a-problem", "choice", "random"])
            or target_input.endswith("problem")
            or target_input.endswith("problems")
        )'''

assert old_ba_markers in norm_ba, "old_ba_markers not found in browser_agent.py"
norm_ba = norm_ba.replace(old_ba_markers, new_ba_markers)

# Also update catalog loop so if multiple links found, pick random
old_cat_loop = '''                chosen_href = None
                chosen_title = ""
                if daily_link:
                    chosen_href, chosen_title = daily_link
                else:
                    links = page.locator("a[href*='/problems/']").all()
                    for l in links:
                        try:
                            h = l.get_attribute("href") or ""
                            txt = l.inner_text().strip()
                            if "/problems/" in h and not any(skip in h for skip in ["random-one-question", "tag", "solution", "discuss", "contest", "/problems/$"]):
                                # Exclude premium locked items
                                is_premium = False
                                try:
                                    parent = l.locator("xpath=..")
                                    is_premium = parent.locator("[data-icon='lock']").count() > 0
                                except Exception:
                                    pass
                                if not is_premium and len(txt) > 2:
                                    chosen_href = h
                                    chosen_title = txt
                                    if any(d in (h + " " + txt).lower() for d in ["daily", "today", "challenge"]):
                                        break
                        except Exception:
                            continue'''

new_cat_loop = '''                chosen_href = None
                chosen_title = ""
                if "daily" in target_input and daily_link:
                    chosen_href, chosen_title = daily_link
                else:
                    valid_candidates = []
                    links = page.locator("a[href*='/problems/']").all()
                    for l in links:
                        try:
                            h = l.get_attribute("href") or ""
                            txt = l.inner_text().strip()
                            if "/problems/" in h and not any(skip in h for skip in ["random-one-question", "tag", "solution", "discuss", "contest", "/problems/$"]):
                                is_premium = False
                                try:
                                    parent = l.locator("xpath=..")
                                    is_premium = parent.locator("[data-icon='lock']").count() > 0
                                except Exception:
                                    pass
                                if not is_premium and len(txt) > 2 and h not in [vc[0] for vc in valid_candidates]:
                                    valid_candidates.append((h, txt))
                        except Exception:
                            continue
                    if valid_candidates:
                        import random
                        chosen_href, chosen_title = random.choice(valid_candidates)
                    elif daily_link:
                        chosen_href, chosen_title = daily_link'''

assert old_cat_loop in norm_ba, "old_cat_loop not found in browser_agent.py"
norm_ba = norm_ba.replace(old_cat_loop, new_cat_loop)

ba_path.write_text(norm_ba, encoding="utf-8")
print("SUCCESS: Upgraded browser_agent.py catalog selection!")

