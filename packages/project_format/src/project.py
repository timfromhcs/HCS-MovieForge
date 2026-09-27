"""Project format structure, directory initialization, and validation."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

PROJECT_DIRECTORIES = [
    "story",
    "characters",
    "locations",
    "props",
    "scenes",
    "shots",
    "storyboards",
    "motion",
    "camera",
    "lighting",
    "fx",
    "audio",
    "renders",
    "exports",
    "logs",
    ".movieforge/events",
    ".movieforge/snapshots",
    ".movieforge/recovery",
    ".movieforge/locks",
    ".movieforge/trash",
]


class ProjectManifest(BaseModel):
    name: str
    project_id: str
    version: str = "0.1.0"
    created_at: str
    updated_at: str
    target_resolution: tuple[int, int] = (1920, 1080)
    target_fps: int = 24
    audio_sample_rate: int = 48000
    description: str = ""
    author: str = ""
    settings: dict[str, Any] = Field(default_factory=dict)


def init_project_structure(project_root: Path, manifest: ProjectManifest) -> None:
    """Creates the full project directory layout and initial manifest."""
    project_root = Path(project_root)
    project_root.mkdir(parents=True, exist_ok=True)

    for d in PROJECT_DIRECTORIES:
        (project_root / d).mkdir(parents=True, exist_ok=True)

    # Write manifest.json
    manifest_path = project_root / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest.model_dump_json(indent=2))

    # Write project.toml
    toml_path = project_root / "project.toml"
    with open(toml_path, "w", encoding="utf-8") as f:
        f.write(
            f"[project]\n"
            f'name = "{manifest.name}"\n'
            f'id = "{manifest.project_id}"\n'
            f'version = "{manifest.version}"\n\n'
            f"[media]\n"
            f"width = {manifest.target_resolution[0]}\n"
            f"height = {manifest.target_resolution[1]}\n"
            f"fps = {manifest.target_fps}\n"
            f"sample_rate = {manifest.audio_sample_rate}\n"
        )


def validate_project_structure(project_root: Path) -> tuple[bool, list[str]]:
    """Checks whether the directory conforms to the canonical project format."""
    project_root = Path(project_root)
    errors = []

    if not project_root.exists() or not project_root.is_dir():
        return False, [f"Project path does not exist or is not a directory: {project_root}"]

    if not (project_root / "manifest.json").exists():
        errors.append("Missing manifest.json")
    if not (project_root / "project.toml").exists():
        errors.append("Missing project.toml")

    for d in PROJECT_DIRECTORIES:
        if not (project_root / d).exists():
            errors.append(f"Missing required project directory: {d}")

    return len(errors) == 0, errors
