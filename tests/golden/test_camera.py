"""Golden camera test: apply orbit preset in headless Blender and verify render + evidence."""

import json
import shutil
import subprocess
from pathlib import Path


def test_camera_orbit_golden(tmp_path):
    blender = shutil.which("blender") or "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe"
    assert Path(blender).exists()
    root = Path(__file__).resolve().parent.parent.parent
    script = root / "integrations" / "blender" / "scripts" / "apply_cine.py"
    out = tmp_path / "cam_orbit.png"
    evidence = tmp_path / "cam_orbit.json"
    proc = subprocess.run(
        [
            blender,
            "-b",
            "--python",
            str(script),
            "--",
            "--module",
            "camera",
            "--preset",
            "orbit",
            "--output",
            str(out),
            "--evidence",
            str(evidence),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, proc.stderr[-1500:]
    assert out.exists() and out.stat().st_size > 10000
    data = json.loads(evidence.read_text())
    assert data["lens_mm"] == 35
