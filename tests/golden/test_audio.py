"""Golden audio test: real Piper TTS WAV generation + ffprobe/amplitude validation."""

import struct
import wave
from pathlib import Path

from integrations.piper.worker import PiperWorker
from packages.contracts.src.worker import WorkerRequest
from packages.validators.src.audio_validator import validate_audio


def _rms(wav_path: Path) -> float:
    with wave.open(str(wav_path), "rb") as wf:
        raw = wf.readframes(wf.getnframes())
    samples = struct.unpack(f"<{len(raw) // 2}h", raw)
    return (sum(s * s for s in samples) / len(samples)) ** 0.5 / 32768.0


def test_piper_golden_wav(tmp_path):
    worker = PiperWorker()
    out = tmp_path / "golden_dialogue.wav"
    req = WorkerRequest(
        job_id="job_golden_tts",
        project_id="golden",
        task_type="voice.generate",
        parameters={"text": "All systems nominal. Searching for track anomaly.", "output_wav": str(out)},
    )
    resp = worker.run(req)
    assert not resp.error, resp.error
    assert out.exists() and out.stat().st_size > 5000
    val = validate_audio(out, min_duration_sec=1.0)
    assert val.is_valid, val.errors
    assert _rms(out) > 0.01
    peak_ok = val.duration_sec < 30.0
    assert peak_ok


def test_music_generate_honestly_unavailable():
    from agent.tools.registry import ToolRegistry
    from engine.artifact_manager.manager import ArtifactManager
    from packages.project_format.src.db import ProjectDB

    root = Path(__file__).resolve().parent.parent.parent / "projects" / "minifilm_spark7"
    db = ProjectDB(root / "movieforge.db")
    reg = ToolRegistry(root, db, ArtifactManager(root, db))
    res = reg.execute("music.generate", project_id="minifilm_spark7", mood="tense")
    assert res["status"] == "error"
    assert res["error_class"] == "MISSING_DEPENDENCY"
