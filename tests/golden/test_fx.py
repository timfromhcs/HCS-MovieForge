"""Golden FX test: rain particle preset must render without crash or missing nodes."""

import json
import shutil
import subprocess
from pathlib import Path


def test_fx_rain_golden(tmp_path):
    blender = shutil.which("blender") or "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe"
    assert Path(blender).exists()
    root = Path(__file__).resolve().parent.parent.parent
    script = root / "integrations" / "blender" / "scripts" / "apply_cine.py"
    out = tmp_path / "fx_rain.png"
    evidence = tmp_path / "fx_rain.json"
    proc = subprocess.run(
        [
            blender,
            "-b",
            "--python",
            str(script),
            "--",
            "--module",
            "fx",
            "--preset",
            "rain",
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
    assert data["particle_count"] == 1000
