"""Golden motion test: metarig pose sheet must evaluate all 14 poses without NaN/crash."""

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image


def test_pose_sheet_golden(tmp_path):
    blender = shutil.which("blender") or "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe"
    assert Path(blender).exists()
    root = Path(__file__).resolve().parent.parent.parent
    script = root / "integrations" / "blender" / "scripts" / "pose_sheet.py"
    out = tmp_path / "pose_sheet.png"
    evidence = tmp_path / "pose_sheet.json"
    workdir = tmp_path / "poses"
    proc = subprocess.run(
        [
            blender,
            "-b",
            "--python",
            str(script),
            "--",
            "--output",
            str(out),
            "--evidence",
            str(evidence),
            "--workdir",
            str(workdir),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stderr[-1500:]
    data = json.loads(evidence.read_text())
    assert data["bone_count"] > 100
    assert len(data["poses"]) == 14
    assert all(p["rendered"] for p in data["poses"])
    tiles = [Image.open(p["file"]) for p in data["poses"]]
    cols, rows = 5, 3
    tw, th = tiles[0].size
    sheet = Image.new("RGB", (cols * tw, rows * th), (20, 20, 20))
    for i, tile in enumerate(tiles[: cols * rows]):
        sheet.paste(tile, ((i % cols) * tw, (i // cols) * th))
    sheet.save(out)
    assert out.stat().st_size > 50000
