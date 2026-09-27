"""Unit tests for agent tool registry and master agent planning."""

import pytest
from pathlib import Path
from packages.project_format.src.db import ProjectDB
from engine.artifact_manager.manager import ArtifactManager
from agent.tools.registry import ToolRegistry


def test_tool_registry_initialization(tmp_path: Path):
    db_file = tmp_path / "test.db"
    db = ProjectDB(db_file)
    mgr = ArtifactManager(tmp_path, db)
    reg = ToolRegistry(tmp_path, db, mgr)

    tools = reg.list_tools()
    tool_names = [t["name"] for t in tools]
    assert "story.create_or_update" in tool_names
    assert "image.generate" in tool_names
    assert "asset.image_to_3d" in tool_names
    assert "voice.generate" in tool_names
    assert "speech.transcribe" in tool_names
    assert "blender.render_turntable" in tool_names
    assert "timeline.assemble" in tool_names
    assert "agent.inspect_image" in tool_names


def test_tool_registry_story_create(tmp_path: Path):
    db_file = tmp_path / "test.db"
    db = ProjectDB(db_file)
    mgr = ArtifactManager(tmp_path, db)
    reg = ToolRegistry(tmp_path, db, mgr)

    res = reg.execute(
        "story.create_or_update",
        project_id="test_p",
        title="Test Story",
        logline="A test logline.",
        characters=[{"name": "Hero", "description": "Protagonist"}],
        locations=[{"name": "Station", "description": "Platform"}],
        shots=[{"action": "Action 1", "camera_prompt": "Wide shot"}],
    )
    assert res["status"] == "ok"

    # Verify committed to SQLite DB
    with db.get_connection() as conn:
        chars = conn.execute("SELECT * FROM characters WHERE project_id = 'test_p';").fetchall()
        assert len(chars) == 1
        assert chars[0]["name"] == "Hero"

        shots = conn.execute("SELECT * FROM shots WHERE project_id = 'test_p';").fetchall()
        assert len(shots) == 1

        # Verify FTS5 story_bible search
        fts_res = conn.execute("SELECT * FROM story_bible WHERE story_bible MATCH 'Hero';").fetchall()
        assert len(fts_res) == 1
