path = 'D:/LlamaOrchestrator/main.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

target = """@app.get("/api/workflows")
async def get_saved_workflows():"""

replacement = """# ==========================================
# BUILDS & WORKSPACES OPERATING HUB
# ==========================================
from core.build_manager import build_manager

@app.get("/api/builds")
async def list_jarvis_builds():
    \"\"\"Returns all active, indexed builds and constructed systems across workspaces.\"\"\"
    builds = build_manager.list_builds()
    return {"success": True, "count": len(builds), "builds": [b.to_dict() for b in builds]}

@app.get("/api/builds/{workspace_id:path}")
async def get_jarvis_build_info(workspace_id: str):
    \"\"\"Returns detailed information and file breakdown for a specific build.\"\"\"
    b = build_manager.get_build(workspace_id)
    if not b:
        raise HTTPException(status_code=404, detail=f"Build '{workspace_id}' not found.")
    return {"success": True, "build": b.to_dict()}

@app.post("/api/builds/{workspace_id:path}/run")
async def run_jarvis_build(workspace_id: str, req: dict = Body(default_factory=dict)):
    \"\"\"Executes a build in its sandboxed directory.\"\"\"
    entrypoint = req.get("entrypoint")
    args = req.get("args")
    timeout = int(req.get("timeout_sec", 60))
    res = await asyncio.to_thread(build_manager.run_build, workspace_id, entrypoint, args, timeout)
    return res

@app.post("/api/builds/{workspace_id:path}/test")
async def test_jarvis_build(workspace_id: str):
    \"\"\"Runs pytest unit tests for a specific build.\"\"\"
    res = await asyncio.to_thread(build_manager.test_build, workspace_id)
    return res

@app.post("/api/builds/{workspace_id:path}/open")
async def open_jarvis_build_folder(workspace_id: str):
    \"\"\"Opens the workspace directory in Windows File Explorer on the desktop.\"\"\"
    res = await asyncio.to_thread(build_manager.open_in_explorer, workspace_id)
    return res

@app.post("/api/builds/clean")
async def clean_workspaces_endpoint(req: dict = Body(default_factory=dict)):
    \"\"\"Safely prunes empty ghost directories and deduplicates test runs.\"\"\"
    dry_run = bool(req.get("dry_run", False))
    res = await asyncio.to_thread(build_manager.clean_workspaces, True, True, dry_run)
    return res

@app.get("/api/workflows")
async def get_saved_workflows():"""

text_norm = text.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')
rep_norm = replacement.replace('\r\n', '\n')

if target_norm in text_norm:
    new_text = text_norm.replace(target_norm, rep_norm, 1)
    if '\r\n' in text:
        new_text = new_text.replace('\n', '\r\n')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("main.py patched with build endpoints successfully!")
else:
    print("Target not found in main.py!")

