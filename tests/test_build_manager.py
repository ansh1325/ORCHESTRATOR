"""
Unit tests for JARVIS Build & Workspace Management Engine.
Chief Systems Architect: Ansh Tiwari
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from main import app
from core.build_manager import BuildManager, BuildWorkspace, BuildArtifact
from jarvis_cli import JarvisCLI

def test_build_manager_list_and_inspect():
    bm = BuildManager()
    builds = bm.list_builds()
    assert isinstance(builds, list)
    assert len(builds) > 0
    
    first = builds[0]
    assert isinstance(first, BuildWorkspace)
    assert first.workspace_id != ""
    assert first.file_count > 0
    assert len(first.artifacts) > 0
    assert first.absolute_path != ""

def test_build_manager_get_build():
    bm = BuildManager()
    builds = bm.list_builds()
    assert len(builds) > 0
    target_id = builds[0].workspace_id
    
    b = bm.get_build(target_id)
    assert b is not None
    assert b.workspace_id == target_id
    assert b.file_count == builds[0].file_count

def test_build_manager_run_build(tmp_path):
    # Create a dummy build in a temp workspace root
    bm = BuildManager(workspace_root=tmp_path)
    build_dir = tmp_path / "test_microservice"
    build_dir.mkdir(parents=True)
    script_file = build_dir / "main.py"
    script_file.write_text("print('HELLO_FROM_JARVIS_BUILD')", encoding="utf-8")
    
    b = bm.get_build("test_microservice")
    assert b is not None
    assert b.primary_entrypoint == "main.py"
    
    res = bm.run_build("test_microservice")
    assert res["success"] is True, f"run_build failed: {res}"
    assert res["exit_code"] == 0
    assert "HELLO_FROM_JARVIS_BUILD" in res["stdout"]

def test_build_manager_clean_workspaces(tmp_path):
    bm = BuildManager(workspace_root=tmp_path)
    # Create empty ghost dir
    empty_dir = tmp_path / "ghost_session_1234"
    empty_dir.mkdir(parents=True)
    
    # Create non-empty dir
    real_dir = tmp_path / "real_service"
    real_dir.mkdir(parents=True)
    (real_dir / "service.py").write_text("x = 1", encoding="utf-8")
    
    # Dry run
    dry_res = bm.clean_workspaces(dry_run=True)
    assert dry_res["cleaned_empty_directories_count"] == 1
    assert empty_dir.exists()
    
    # Real run
    clean_res = bm.clean_workspaces(dry_run=False)
    assert clean_res["cleaned_empty_directories_count"] == 1
    assert not empty_dir.exists()
    assert real_dir.exists()

def test_build_manager_open_in_explorer():
    bm = BuildManager()
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value = None
        res = bm.open_in_explorer("workspaces")
        assert res["success"] is True
        assert mock_popen.called

def test_fastapi_build_endpoints():
    client = TestClient(app)
    
    # 1. GET /api/builds
    res_list = client.get("/api/builds")
    assert res_list.status_code == 200
    data = res_list.json()
    assert data["success"] is True
    assert data["count"] > 0
    
    # 2. GET /api/builds/{id}
    wid = data["builds"][0]["workspace_id"]
    res_info = client.get(f"/api/builds/{wid}")
    assert res_info.status_code == 200
    assert res_info.json()["success"] is True
    assert res_info.json()["build"]["workspace_id"] == wid
    
    # 3. POST /api/builds/clean (dry_run)
    res_clean = client.post("/api/builds/clean", json={"dry_run": True})
    assert res_clean.status_code == 200
    assert res_clean.json()["success"] is True

@pytest.mark.asyncio
async def test_jarvis_cli_builds_command():
    cli = JarvisCLI()
    cli.voice_enabled = False
    
    # Test builds list directive
    res_list = await cli.process_directive("builds list")
    assert res_list is True
    
    # Test clean workspaces directive
    with patch("core.build_manager.build_manager.clean_workspaces") as mock_clean:
        mock_clean.return_value = {
            "success": True,
            "cleaned_empty_directories_count": 0,
            "pruned_duplicate_test_runs_count": 0,
            "active_preserved_builds_count": 5
        }
        res_clean = await cli.process_directive("clean workspaces")
        assert res_clean is True
        assert mock_clean.called
