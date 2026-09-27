"""Golden rig-gate test: TRELLIS blob GLB must be honestly BLOCKED, never fake-rigged."""

import json
import shutil
import subprocess
from pathlib import Path


def test_trellis_blob_blocked():
    blender = shutil.which("blender") or "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe"
    assert Path(blender).exists()
    root = Path(__file__).resolve().parent.parent.parent
    glb = root / "projects" / "minifilm_spark7" / "props" / "spark7_mesh.glb"
    assert glb.exists()
    script = root / "integrations" / "blender" / "scripts" / "rig_character.py"
    tmp = root / "runtime" / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    evidence = tmp / "rig_gate_evidence.json"
    proc = subprocess.run(
        [
            blender,
            "-b",
            "--python",
            str(script),
            "--",
            "--input",
            str(glb),
            "--output",
            str(tmp / "rig_gate.blend"),
            "--evidence",
            str(evidence),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 2, proc.stdout[-1500:] + proc.stderr[-1500:]
    data = json.loads(evidence.read_text())
    assert data["status"] == "BLOCKED_NON_HUMANOID"
    assert data["total_verts"] > 0
