"""Artifact contracts and schema definitions for HCS MovieForge."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ArtifactKind(StrEnum):
    IMAGE = "IMAGE"
    MASK = "MASK"
    CUTOUT = "CUTOUT"
    MESH_RAW = "MESH_RAW"
    MESH_RETOPO = "MESH_RETOPO"
    RIG = "RIG"
    ANIMATION = "ANIMATION"
    AUDIO_VOICE = "AUDIO_VOICE"
    AUDIO_MUSIC = "AUDIO_MUSIC"
    AUDIO_SFX = "AUDIO_SFX"
    VIDEO_CLIP = "VIDEO_CLIP"
    VIDEO_MASTER = "VIDEO_MASTER"
    TEXT_STORY = "TEXT_STORY"
    TEXT_SCREENPLAY = "TEXT_SCREENPLAY"
    STORYBOARD_FRAME = "STORYBOARD_FRAME"
    BLENDER_SCENE = "BLENDER_SCENE"
    REPORT = "REPORT"


class QAStatus(StrEnum):
    UNINSPECTED = "UNINSPECTED"
    PENDING = "PENDING"
    PASSED = "PASSED"
    FLAGGED = "FLAGGED"
    REJECTED = "REJECTED"


class ArtifactRecord(BaseModel):
    artifact_id: str
    project_id: str
    kind: ArtifactKind
    path: str
    relative_path: str
    size: int
    sha256: str
    mime: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    producer: str
    producer_version: str = "0.1.0"
    model_id: str | None = None
    model_revision: str | None = None
    source_artifacts: list[str] = Field(default_factory=list)
    recipe_fingerprint: str | None = None
    qa_status: QAStatus = QAStatus.UNINSPECTED
    canonical: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
