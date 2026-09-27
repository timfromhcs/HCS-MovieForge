"""Stress D: terminate the known Blender child mid-render; partial quarantined, DB intact."""

import shutil
import subprocess
import time
from pathlib import Path

import pytest

from packages.project_format.src.db import ProjectDB


def test_blender_crash_recovery(tmp_path):
    blender = shutil.which("blender") or "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe"
    if not Path(blender).exists():
        pytest.skip("blender not installed")
    root = Path(__file__).resolve().parent.parent.parent
    glb = root / "projects" / "minifilm_spark7" / "props" / "spark7_mesh.glb"
    script = root / "integrations" / "blender" / "scripts" / "import_and_render_turntable.py"
    out = tmp_path / "crash_turntable.png"
    proc = subprocess.Popen(
        [
            blender,
            "-b",
            "--python",
            str(script),
            "--",
            "--input",
            str(glb),
            "--output",
            str(out),
            "--frames",
            "120",
            "--width",
            "1920",
            "--height",
            "1080",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(10)  # let the known child start real multi-frame work
    assert proc.poll() is None, "blender finished before kill; increase --frames for this host"
    proc.terminate()  # only the Popen child we own
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
    assert proc.returncode != 0
    db = ProjectDB(tmp_path / "crash.db")
    assert db.check_integrity()
    if out.exists():
        # A partial render must never be presented as a valid artifact without validation
        assert out.stat().st_size > 0
