"""Unit tests for continuity, movie-QA gates, and known-bad frame detection."""

from PIL import Image

from packages.validators.src.continuity import check_continuity
from packages.validators.src.movie_qa import check_shot_media
from packages.validators.src.visual_qa import detect_known_bad, histogram_distance


def test_continuity_pass_and_violation():
    shots = [
        {"shot_id": "s1", "wardrobe": "yellow jacket", "time_of_day": "night"},
        {
            "shot_id": "s2",
            "inherits_from_shot": "s1",
            "wardrobe": "yellow jacket",
            "time_of_day": "night",
            "continuity_constraints": {"wardrobe": "yellow jacket", "time_of_day": "night"},
        },
    ]
    res = check_continuity(shots)
    assert res["passed"] and res["checked"] == 2
    shots[1]["wardrobe"] = "red jacket"
    res = check_continuity(shots)
    assert not res["passed"] and res["violations"][0]["key"] == "wardrobe"


def test_shot_media_missing_zero(tmp_path):
    real = tmp_path / "clip.mp4"
    real.write_bytes(b"data")
    shots = [{"shot_id": "s1", "video_artifact": "a1"}]
    assert check_shot_media(shots, {"a1": real})["passed"]
    res = check_shot_media(shots, {})
    assert not res["passed"] and res["missing_media"] == 1


def test_known_bad_detection(tmp_path):
    black = tmp_path / "black.png"
    Image.new("RGB", (64, 64), (0, 0, 0)).save(black)
    assert "fully_black" in detect_known_bad(black)
    white = tmp_path / "white.png"
    Image.new("RGB", (64, 64), (255, 255, 255)).save(white)
    assert "fully_white" in detect_known_bad(white)
    normal = tmp_path / "normal.png"
    Image.new("RGB", (64, 64), (120, 30, 200)).save(normal)
    assert detect_known_bad(normal) == []
    assert histogram_distance(normal, normal) == 0.0
    assert 0.0 < histogram_distance(black, white) <= 1.0
    assert "undecodable" in detect_known_bad(tmp_path / "missing.png")[0]
