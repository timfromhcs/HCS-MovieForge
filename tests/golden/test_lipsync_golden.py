"""Golden lipsync test: real dialogue WAV -> visemes -> Blender jaw keys -> proof render."""

import json
import shutil
import subprocess
from pathlib import Path

from integrations.blender.lipsync import wav_to_visemes


def test_lipsync_golden(tmp_path):
    root = Path(__file__).resolve().parent.parent.parent
    wav = root / "projects" / "minifilm_spark7" / "audio" / "spark7_dialogue.wav"
    assert wav.exists()
    timeline = wav_to_visemes(wav)
    assert len(timeline) > 10
    assert any(v["viseme"] == "OPEN" for v in timeline)
    vis_path = tmp_path / "timeline.visemes.json"
    vis_path.write_text(json.dumps(timeline), encoding="utf-8")
    blender = shutil.which("blender") or "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe"
    out = tmp_path / "lipsync_proof.png"
    evidence = tmp_path / "lipsync_evidence.json"
    script = root / "integrations" / "blender" / "scripts" / "lipsync_apply.py"
    proc = subprocess.run(
        [
            blender,
            "-b",
            "--python",
            str(script),
            "--",
            "--visemes",
            str(vis_path),
            "--output",
            str(out),
            "--evidence",
            str(evidence),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stderr[-1500:]
    data = json.loads(evidence.read_text())
    assert data["frames"] == len(timeline)
    assert out.stat().st_size > 5000
