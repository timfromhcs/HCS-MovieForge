"""Unit tests for the energy-baseline viseme analysis (synthetic WAV, no backend)."""

import math
import struct
import wave

from integrations.blender.lipsync import wav_to_visemes


def _write_tone(path, seconds=1.0, freq=220.0, rate=22050, amplitude=0.5):
    frames = []
    for i in range(int(seconds * rate)):
        sample = int(amplitude * 32767 * math.sin(2 * math.pi * freq * i / rate))
        frames.append(struct.pack("<h", sample))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"".join(frames))


def test_tone_produces_open_visemes(tmp_path):
    wav = tmp_path / "tone.wav"
    _write_tone(wav)
    vis = wav_to_visemes(wav, frame_ms=100)
    assert len(vis) == 10
    assert any(v["viseme"] == "OPEN" for v in vis)
    assert all(0.0 <= v["jaw_open"] <= 1.0 for v in vis)


def test_silence_produces_sil(tmp_path):
    wav = tmp_path / "sil.wav"
    with wave.open(str(wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(b"\x00" * 22050 * 2)
    vis = wav_to_visemes(wav, frame_ms=100)
    assert vis and all(v["viseme"] == "SIL" for v in vis)


def test_missing_file_raises(tmp_path):
    try:
        wav_to_visemes(tmp_path / "nope.wav")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("expected FileNotFoundError")
