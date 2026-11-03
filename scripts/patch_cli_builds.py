path = 'D:/LlamaOrchestrator/jarvis_cli.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update print_help
help_target = """        print(f"  {C.CYAN}workflows{C.RESET}                View saved recurring workflows")"""
help_replacement = """        print(f"  {C.CYAN}builds [list]{C.RESET}             List all verified builds, constructed microservices & workspaces")
        print(f"  {C.CYAN}builds info <id>{C.RESET}          Inspect file breakdown, PRDs, and architecture of a build")
        print(f"  {C.CYAN}builds run <id> [file]{C.RESET}    Execute build entrypoint immediately in workspace sandbox")
        print(f"  {C.CYAN}builds test <id>{C.RESET}          Execute unit test suite for a specific build workspace")
        print(f"  {C.CYAN}builds open <id>{C.RESET}          Open workspace folder directly in Windows File Explorer")
        print(f"  {C.CYAN}builds clean{C.RESET}              Safely prune empty ghost folders without harming core data")
        print(f"  {C.CYAN}workflows{C.RESET}                View saved recurring workflows")"""

# 2. Add handle_builds_command implementation
builds_handler = '''    async def handle_builds_command(self, line: str) -> bool:
        """
        Manages, inspects, executes, and cleans JARVIS builds and workspaces.
        """
        from core.build_manager import build_manager

        clean_line = line.strip()
        low = clean_line.lower()

        # Handle natural language aliases
        if any(w in low for w in ["clean workspace", "clean workspaces", "cleanup workspace", "cleanup workspaces", "clean the workspace"]):
            subcmd = "clean"
            parts = ["builds", "clean"]
        elif low in ["list builds", "show builds", "get builds", "show workspaces", "list workspaces"]:
            subcmd = "list"
            parts = ["builds", "list"]
        elif low.startswith("run build "):
            subcmd = "run"
            parts = ["builds", "run"] + clean_line.split()[2:]
        elif low.startswith("test build "):
            subcmd = "test"
            parts = ["builds", "test"] + clean_line.split()[2:]
        elif low.startswith("open build ") or low.startswith("open workspace "):
            subcmd = "open"
            parts = ["builds", "open"] + clean_line.split()[2:]
        elif low.startswith("info build ") or low.startswith("build info "):
            subcmd = "info"
            parts = ["builds", "info"] + clean_line.split()[2:]
        else:
            parts = clean_line.split()
            subcmd = parts[1].lower() if len(parts) > 1 else "list"

        if subcmd in ["list", "all", "ls", "show"]:
            builds = build_manager.list_builds()
            print(f"\\n{C.BOLD}{C.CYAN}===================================================================================================={C.RESET}")
            print(f"{C.BOLD}{C.CYAN}                              JARVIS AUTONOMOUS BUILDS & WORKSPACES                                 {C.RESET}")
            print(f"{C.BOLD}{C.CYAN}===================================================================================================={C.RESET}")
            if not builds:
                print(f"  {C.DIM}No active builds found. Commands like 'build a fullstack app' will synthesize one.{C.RESET}\\n")
                return True

            print(f"{C.BOLD}{'ID':<28} | {'TITLE / PURPOSE':<30} | {'TRACK':<20} | {'FILES':<5} | {'STATUS'}{C.RESET}")
            print("-" * 100)
            for b in builds:
                st_color = C.GREEN if b.status == "CERTIFIED" else C.YELLOW
                print(f"{C.CYAN}{b.workspace_id:<28}{C.RESET} | {b.title:<30} | {b.track:<20} | {b.file_count:<5} | {st_color}{b.status}{C.RESET}")
            print("-" * 100)
            print(f"{C.DIM}Quick Commands:{C.RESET}")
            print(f"  {C.GREEN}builds run <id>{C.RESET}         Execute the build entrypoint directly")
            print(f"  {C.GREEN}builds info <id>{C.RESET}        View complete files, PRD, and architecture")
            print(f"  {C.GREEN}builds test <id>{C.RESET}        Execute unit test suite for this build")
            print(f"  {C.GREEN}builds open <id>{C.RESET}        Open build folder in Windows File Explorer")
            print(f"  {C.GREEN}builds clean{C.RESET}            Safely prune empty ghost directories\\n")
            return True

        elif subcmd in ["clean", "prune"]:
            res = build_manager.clean_workspaces(remove_empty_dirs=True, deduplicate_test_runs=True, dry_run=False)
            print(f"\\n{C.GREEN}✓ Workspace Clean Completed Successfully:{C.RESET}")
            print(f"  • Empty Ghost Directories Removed: {C.BOLD}{res['cleaned_empty_directories_count']}{C.RESET}")
            print(f"  • Duplicate Test Runs Pruned:      {C.BOLD}{res['pruned_duplicate_test_runs_count']}{C.RESET}")
            print(f"  • Active Verified Builds Retained: {C.BOLD}{res['active_preserved_builds_count']}{C.RESET}\\n")
            self.speak("Workspaces safely cleaned and organized, Master Ansh.")
            return True

        elif subcmd in ["open", "explore", "view"]:
            ws_id = parts[2] if len(parts) > 2 else "workspaces"
            res = build_manager.open_in_explorer(ws_id)
            if res.get("success"):
                print(f"\\n{C.GREEN}✓ Opened in File Explorer: {C.BOLD}{res.get('path')}{C.RESET}\\n")
            else:
                print(f"\\n{C.RED}✗ Error opening folder: {res.get('error')}{C.RESET}\\n")
            return True

        elif subcmd in ["info", "inspect"]:
            if len(parts) < 3:
                print(f"\\n{C.YELLOW}Usage: builds info <workspace_id>{C.RESET}\\n")
                return True
            ws_id = parts[2]
            b = build_manager.get_build(ws_id)
            if not b:
                print(f"\\n{C.RED}✗ Build '{ws_id}' not found.{C.RESET}\\n")
                return True

            print(f"\\n{C.BOLD}{C.CYAN}================================================================================{C.RESET}")
            print(f"{C.BOLD}BUILD DOSSIER: {b.title}{C.RESET} ({C.GREEN}{b.status}{C.RESET})")
            print(f"{C.BOLD}{C.CYAN}================================================================================{C.RESET}")
            print(f"  {C.BOLD}ID:{C.RESET}               {b.workspace_id}")
            print(f"  {C.BOLD}Track:{C.RESET}            {b.track}")
            print(f"  {C.BOLD}Directory:{C.RESET}        {b.absolute_path}")
            print(f"  {C.BOLD}Created / Mod:{C.RESET}    {b.created_at} / {b.modified_at}")
            print(f"  {C.BOLD}Total Size:{C.RESET}       {b.total_size_human} ({b.file_count} files)")
            print(f"  {C.BOLD}Primary Entry:{C.RESET}    {b.primary_entrypoint or 'None'}")
            print(f"  {C.BOLD}Run Command:{C.RESET}      {b.run_command or 'None'}")
            if b.documentation:
                print(f"  {C.BOLD}PRD / Summary:{C.RESET}    {b.documentation}")

            print(f"\\n{C.BOLD}Enclosed Artifacts:{C.RESET}")
            for a in b.artifacts:
                ep_tag = f" {C.GREEN}[ENTRYPOINT]{C.RESET}" if a.is_entrypoint else ""
                print(f"  • {a.relative_path:<35} ({a.size_human:>7}, {a.file_type}){ep_tag}")

            print(f"\\n{C.DIM}Execute now: {C.GREEN}builds run {b.workspace_id}{C.RESET} | {C.GREEN}builds open {b.workspace_id}{C.RESET}\\n")
            return True

        elif subcmd in ["run", "exec", "start"]:
            if len(parts) < 3:
                print(f"\\n{C.YELLOW}Usage: builds run <workspace_id> [entrypoint_file]{C.RESET}\\n")
                return True
            ws_id = parts[2]
            ep = parts[3] if len(parts) > 3 else None
            extra_args = parts[4:] if len(parts) > 4 else None

            print(f"\\n{C.CYAN}⚡ JARVIS Build Runner: Initializing execution for '{ws_id}'...{C.RESET}")
            self.speak(f"Executing build {ws_id}.")
            res = build_manager.run_build(workspace_id=ws_id, entrypoint=ep, args=extra_args)

            if res.get("success"):
                print(f"{C.GREEN}✓ Execution Completed Successfully (Exit 0 in {res.get('elapsed_sec')}s):{C.RESET}")
                if res.get("stdout"):
                    print(f"\\n{C.BOLD}--- [STDOUT] ---{C.RESET}\\n{res.get('stdout').strip()}")
                if res.get("stderr"):
                    print(f"\\n{C.YELLOW}--- [STDERR] ---{C.RESET}\\n{res.get('stderr').strip()}")
            else:
                print(f"{C.RED}✗ Execution Failed (Exit {res.get('exit_code')} in {res.get('elapsed_sec')}s):{C.RESET}")
                if res.get("error"):
                    print(f"Error: {res.get('error')}")
                if res.get("stderr"):
                    print(f"\\n{C.RED}--- [STDERR] ---{C.RESET}\\n{res.get('stderr').strip()}")
                if res.get("stdout"):
                    print(f"\\n{C.DIM}--- [STDOUT] ---{C.RESET}\\n{res.get('stdout').strip()}")
            print()
            return True

        elif subcmd in ["test"]:
            if len(parts) < 3:
                print(f"\\n{C.YELLOW}Usage: builds test <workspace_id>{C.RESET}\\n")
                return True
            ws_id = parts[2]
            print(f"\\n{C.CYAN}🧪 JARVIS Build Runner: Running test suite for '{ws_id}'...{C.RESET}")
            res = build_manager.test_build(workspace_id=ws_id)
            if res.get("success"):
                print(f"{C.GREEN}✓ All Tests Passed in {res.get('elapsed_sec')}s:{C.RESET}")
                print(res.get("output", "").strip())
            else:
                print(f"{C.RED}✗ Test Suite Failed:{C.RESET}")
                print(res.get("output", res.get("error", "")).strip())
            print()
            return True

        else:
            print(f"\\n{C.YELLOW}Unknown builds subcommand '{subcmd}'. Available: list, info, run, test, open, clean.{C.RESET}\\n")
            return True

'''

# 3. Add to process_directive
process_target = """        # Utility Subcommands
        if low.startswith("audit ") or low.startswith("inspect folder "):"""

process_replacement = """        # Builds & Workspaces Management Commands
        if (
            low in ["builds", "build", "workspaces", "workspace", "list builds", "show builds", "get builds", "list workspaces", "show workspaces"]
            or low.startswith(("builds ", "build ", "workspaces ", "workspace ", "run build ", "test build ", "open build ", "open workspace ", "clean workspace", "clean workspaces", "cleanup workspace", "cleanup workspaces", "clean up the workspace folder"))
        ):
            return await self.handle_builds_command(line)

        # Utility Subcommands
        if low.startswith("audit ") or low.startswith("inspect folder "):"""

text_norm = text.replace('\r\n', '\n')
help_target_norm = help_target.replace('\r\n', '\n')
help_rep_norm = help_replacement.replace('\r\n', '\n')
process_target_norm = process_target.replace('\r\n', '\n')
process_rep_norm = process_replacement.replace('\r\n', '\n')

if help_target_norm in text_norm and process_target_norm in text_norm:
    new_text = text_norm.replace(help_target_norm, help_rep_norm, 1)
    new_text = new_text.replace(process_target_norm, process_rep_norm, 1)
    
    # Insert builds_handler right before async def process_directive
    proc_def = "    async def process_directive(self, line: str) -> bool:"
    if proc_def in new_text:
        new_text = new_text.replace(proc_def, builds_handler + proc_def, 1)
        if '\r\n' in text:
            new_text = new_text.replace('\n', '\r\n')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("jarvis_cli.py patched with builds commands successfully!")
    else:
        print("process_directive definition not found!")
else:
    print("help_target or process_target not found!")

