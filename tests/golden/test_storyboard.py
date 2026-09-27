"""Golden storyboard test: reorder shots in a scratch project DB without breaking order."""

from agent.tools.registry import ToolRegistry
from engine.artifact_manager.manager import ArtifactManager
from packages.project_format.src.db import ProjectDB


def test_storyboard_reorder_golden(tmp_path):
    db = ProjectDB(tmp_path / "story.db")
    reg = ToolRegistry(tmp_path, db, ArtifactManager(tmp_path, db))
    res = reg.execute(
        "story.create_or_update",
        project_id="sb1",
        title="Board",
        logline="log",
        characters=[],
        locations=[],
        shots=[
            {"action": "a", "camera_prompt": "wide", "duration_sec": 2.0},
            {"action": "b", "camera_prompt": "close", "duration_sec": 2.0},
            {"action": "c", "camera_prompt": "aerial", "duration_sec": 2.0},
        ],
    )
    assert res["status"] == "ok"
    scene_id = "scene_sb1_1"
    first = "shot_sb1_1"
    moved = reg.execute("storyboard.reorder", project_id="sb1", scene_id=scene_id, shot_id=first, new_position=3)
    assert moved["status"] == "ok"
    assert moved["order"] == ["shot_sb1_2", "shot_sb1_3", "shot_sb1_1"]
    bad = reg.execute("storyboard.reorder", project_id="sb1", scene_id=scene_id, shot_id="nope", new_position=1)
    assert bad["status"] == "error"
