"""Baseline lip-sync analysis: WAV amplitude envelope mapped to jaw-open visemes.

This is an energy baseline, NOT phoneme-exact synthesis. It provides a real,
verified audio -> viseme-timing -> Blender-parameter path for persistent 3D
characters until a phoneme backend (CosyVoice/Whisper-timestamps) is certified.
Output visemes: SIL (silence), OPEN (vowel-like energy), MID, CLOSED (consonant dip).
"""

from __future__ import annotations

import math
import wave
from pathlib import Path


def wav_to_visemes(wav_path: Path | str, frame_ms: int = 100) -> list[dict]:
    """Computes per-frame RMS energy and maps it to viseme labels with open amounts."""
    path = Path(wav_path)
    if not path.is_file():
        raise FileNotFoundError(f"lipsync source missing: {path}")
    with wave.open(str(path), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    if sampwidth != 2:
        raise ValueError(f"lipsync baseline needs 16-bit PCM, got {sampwidth * 8}-bit")
    import struct

    total = len(raw) // (sampwidth * n_channels)
    channel0 = struct.unpack(f"<{total * n_channels}h", raw)[::n_channels]
    peak = max(1, max(abs(s) for s in channel0))
    per_frame = max(1, int(framerate * frame_ms / 1000))
    visemes: list[dict] = []
    for start in range(0, total, per_frame):
        chunk = channel0[start : start + per_frame]
        rms = math.sqrt(sum(s * s for s in chunk) / len(chunk)) / peak
        if rms < 0.02:
            label, open_amount = "SIL", 0.0
        elif rms < 0.10:
            label, open_amount = "CLOSED", 0.15
        elif rms < 0.30:
            label, open_amount = "MID", 0.5
        else:
            label, open_amount = "OPEN", min(1.0, rms * 2.0)
        visemes.append(
            {
                "t_sec": round(start / framerate, 3),
                "rms": round(rms, 4),
                "viseme": label,
                "jaw_open": round(open_amount, 3),
            }
        )
    return visemes
