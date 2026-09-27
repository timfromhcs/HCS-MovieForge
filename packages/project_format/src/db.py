"""Project database initialization, WAL management, and transactional tables."""

import sqlite3
from pathlib import Path

MIGRATION_V1 = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    path TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    mime TEXT NOT NULL,
    created_at TEXT NOT NULL,
    producer TEXT NOT NULL,
    producer_version TEXT NOT NULL,
    model_id TEXT,
    model_revision TEXT,
    source_artifacts TEXT,
    recipe_fingerprint TEXT,
    qa_status TEXT DEFAULT 'UNINSPECTED',
    canonical INTEGER DEFAULT 0,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    model_id TEXT,
    model_revision TEXT,
    input_artifact_ids TEXT,
    input_hashes TEXT,
    recipe_fingerprint TEXT,
    priority INTEGER DEFAULT 20,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 2,
    resource_estimate TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    parent_job TEXT,
    child_jobs TEXT,
    worker_id TEXT,
    output_artifact_ids TEXT,
    error TEXT,
    payload TEXT
);

CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_artifacts_kind ON artifacts(kind);
CREATE INDEX IF NOT EXISTS idx_artifacts_project ON artifacts(project_id);
"""

MIGRATION_V2 = """
CREATE TABLE IF NOT EXISTS characters (
    character_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    visual_style TEXT,
    reference_artifact_ids TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS locations (
    location_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    time_of_day TEXT,
    weather TEXT,
    reference_artifact_ids TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS props (
    prop_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    reference_artifact_ids TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS scenes (
    scene_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    scene_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    location_id TEXT,
    time_of_day TEXT,
    synopsis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shots (
    shot_id TEXT PRIMARY KEY,
    scene_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    shot_number INTEGER NOT NULL,
    camera_prompt TEXT,
    action_description TEXT,
    dialogue TEXT,
    character_ids TEXT,
    duration_sec REAL DEFAULT 3.0,
    status TEXT DEFAULT 'PLANNED',
    video_artifact_id TEXT,
    audio_artifact_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(scene_id) REFERENCES scenes(scene_id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE IF NOT EXISTS story_bible USING fts5(
    entity_id,
    entity_type,
    title,
    content,
    tags
);

CREATE INDEX IF NOT EXISTS idx_shots_scene ON shots(scene_id, shot_number);
"""


class ProjectDB:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        with self.get_connection() as conn:
            # Check current version
            conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_versions "
                "(version INTEGER PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
            )
            cursor = conn.execute("SELECT MAX(version) FROM schema_versions;")
            row = cursor.fetchone()
            curr_ver = row[0] or 0

            if curr_ver < 1:
                conn.executescript(MIGRATION_V1)
                conn.execute("INSERT INTO schema_versions (version) VALUES (1);")
            if curr_ver < 2:
                conn.executescript(MIGRATION_V2)
                conn.execute("INSERT INTO schema_versions (version) VALUES (2);")
            conn.commit()

    def check_integrity(self) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            return result[0] == "ok"
