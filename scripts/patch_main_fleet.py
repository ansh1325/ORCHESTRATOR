from pathlib import Path

main_path = Path("D:/LlamaOrchestrator/main.py")
content = main_path.read_text(encoding="utf-8")

anchor = """@app.post("/api/builds/clean")
async def clean_workspaces_endpoint(req: dict = Body(default_factory=dict)):
    \"\"\"Safely prunes empty ghost directories and deduplicates test runs.\"\"\"
    dry_run = bool(req.get("dry_run", False))
    res = await asyncio.to_thread(build_manager.clean_workspaces, True, True, dry_run)
    return res"""

fleet_routes = """@app.post("/api/builds/clean")
async def clean_workspaces_endpoint(req: dict = Body(default_factory=dict)):
    \"\"\"Safely prunes empty ghost directories and deduplicates test runs.\"\"\"
    dry_run = bool(req.get("dry_run", False))
    res = await asyncio.to_thread(build_manager.clean_workspaces, True, True, dry_run)
    return res

# ==========================================
# Account Fleet & Cold Outreach Delivery Hub
# ==========================================
from core.account_fleet import account_fleet

@app.get("/api/fleet/summary")
async def get_fleet_summary(platform: str = "gmail"):
    \"\"\"Returns real-time fleet health, total accounts, quota limits, and capacity.\"\"\"
    return account_fleet.get_fleet_summary(platform=platform)

@app.post("/api/fleet/scale")
async def scale_fleet_topology_endpoint(req: dict = Body(default_factory=dict)):
    \"\"\"Scales fleet to 20 or up to 200 accounts with safe daily quota limits.\"\"\"
    count = int(req.get("target_count", 20))
    is_ws = bool(req.get("is_workspace", False))
    return account_fleet.scale_fleet_topology(target_account_count=count, is_workspace=is_ws)

@app.post("/api/fleet/verify")
async def verify_email_deliverability(req: dict = Body(default_factory=dict)):
    \"\"\"Verifies physical email sendability via RFC syntax, disposable checks, and live DNS MX resolution.\"\"\"
    email = req.get("email", "")
    if email:
        return account_fleet.validate_email_sendability(email)
    leads = req.get("leads", [])
    return account_fleet.filter_sendable_prospects(leads)

@app.get("/api/fleet/sequence")
async def get_outreach_sequence(niche: str = "Full-Stack Dev & AI Systems"):
    \"\"\"Returns the 8-touch human-engineered email follow-up sequence.\"\"\"
    return {"touches": account_fleet.generate_8_touch_sequence(company_niche=niche)}

@app.get("/api/fleet/notifications")
async def get_fleet_notifications():
    \"\"\"Returns executive briefings of high-intent lead replies and Calendly meeting bookings.\"\"\"
    return {"notifications": account_fleet.get_notifications()}"""

norm_c = content.replace("\r\n", "\n")
norm_anchor = anchor.replace("\r\n", "\n")
norm_routes = fleet_routes.replace("\r\n", "\n")

if norm_anchor in norm_c:
    new_c = norm_c.replace(norm_anchor, norm_routes, 1)
    if "\r\n" in content:
        new_c = new_c.replace("\n", "\r\n")
    main_path.write_text(new_c, encoding="utf-8")
    print("SUCCESSFULLY_PATCHED_MAIN_PY")
else:
    print("ANCHOR_NOT_FOUND")

