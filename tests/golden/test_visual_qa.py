"""Golden visual QA: sample the real mini-film master, detect known-bad, build sheet."""

from pathlib import Path

from packages.validators.src.visual_qa import check_result, contact_sheet, frame_brightness, sample_frames


def test_minifilm_master_visual_qa(tmp_path):
    root = Path(__file__).resolve().parent.parent.parent
    master = root / "projects" / "minifilm_spark7" / "exports" / "spark7_final_master_1080p.mp4"
    assert master.exists()
    frames = sample_frames(master, tmp_path / "frames", count=3)
    assert len(frames) == 3
    verdict = check_result(frames)
    assert verdict["passed"], verdict["flagged"]
    assert all(frame_brightness(f) > 2.0 for f in frames)
    sheet = contact_sheet(frames, tmp_path / "contact.png")
    assert sheet.stat().st_size > 20000
