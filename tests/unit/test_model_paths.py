"""Unit tests for portable model-lock path resolution (Windows <-> Linux)."""

from pathlib import Path

from engine.model_manager.manager import ModelManager


def test_resolve_relative_posix(tmp_path: Path) -> None:
    mgr = ModelManager(models_dir=tmp_path / "models")
    expected = tmp_path / "models" / "stt_whisper_base" / "ggml-base.bin"
    assert mgr.resolve_locked_path("stt_whisper_base/ggml-base.bin") == expected


def test_resolve_legacy_windows_absolute(tmp_path: Path) -> None:
    mgr = ModelManager(models_dir=tmp_path / "models")
    legacy = r"E:\AiMovieMaker\models\stt_whisper_base\ggml-base.bin"
    assert mgr.resolve_locked_path(legacy) == tmp_path / "models" / "stt_whisper_base" / "ggml-base.bin"


def test_resolve_legacy_windows_backslash_relative(tmp_path: Path) -> None:
    mgr = ModelManager(models_dir=tmp_path / "models")
    legacy = r"models\image_bonsai_flux2-klein_q2k\bonsai-flux2-klein-ternary-q2_k.gguf"
    expected = tmp_path / "models" / "image_bonsai_flux2-klein_q2k" / "bonsai-flux2-klein-ternary-q2_k.gguf"
    assert mgr.resolve_locked_path(legacy) == expected


def test_resolve_nested_posix(tmp_path: Path) -> None:
    mgr = ModelManager(models_dir=tmp_path / "models")
    stored = "vae_flux2_dev/split_files/vae/flux2-vae.safetensors"
    expected = tmp_path / "models" / "vae_flux2_dev" / "split_files" / "vae" / "flux2-vae.safetensors"
    assert mgr.resolve_locked_path(stored) == expected


def test_resolve_posix_with_models_prefix(tmp_path: Path) -> None:
    mgr = ModelManager(models_dir=tmp_path / "models")
    expected = tmp_path / "models" / "stt_whisper_base" / "ggml-base.bin"
    assert mgr.resolve_locked_path("models/stt_whisper_base/ggml-base.bin") == expected
