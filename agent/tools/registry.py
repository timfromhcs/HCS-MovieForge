"""Agent tool contracts, registry, and execution dispatcher."""

import os
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from engine.artifact_manager.manager import ArtifactManager
from integrations.blender.worker import BlenderWorker
from integrations.llama_cpp.worker import LlamaWorker
from integrations.piper.worker import PiperWorker
from integrations.stable_diffusion_cpp.worker import StableDiffusionWorker
from integrations.trellis_cpp.worker import TrellisWorker
from integrations.whisper_cpp.worker import WhisperWorker
from packages.contracts.src.artifact import ArtifactKind
from packages.contracts.src.worker import WorkerRequest
from packages.project_format.src.db import ProjectDB

_SQL_STORY_BIBLE_UPSERT = (
    "INSERT OR REPLACE INTO story_bible (entity_id, entity_type, title, content, tags) VALUES (?, ?, ?, ?, ?);"
)
_SQL_CHARACTER_UPSERT = (
    "INSERT OR REPLACE INTO characters "
    "(character_id, project_id, name, description, visual_style) VALUES (?, ?, ?, ?, ?);"
)
_SQL_LOCATION_UPSERT = (
    "INSERT OR REPLACE INTO locations "
    "(location_id, project_id, name, description, time_of_day, weather) "
    "VALUES (?, ?, ?, ?, ?, ?);"
)
_SQL_SCENE_UPSERT = (
    "INSERT OR REPLACE INTO scenes (scene_id, project_id, scene_number, title, synopsis) VALUES (?, ?, ?, ?, ?);"
)
_SQL_SHOT_UPSERT = (
    "INSERT OR REPLACE INTO shots "
    "(shot_id, scene_id, project_id, shot_number, camera_prompt, action_description, "
    "dialogue, duration_sec) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
)


class ToolRegistry:
    def __init__(self, project_root: Path | str, db: ProjectDB, artifact_mgr: ArtifactManager):
        self.project_root = Path(project_root).resolve()
        self.db = db
        self.artifact_mgr = artifact_mgr

        # Initialize backend workers
        self.sd_worker = StableDiffusionWorker()
        self.trellis_worker = TrellisWorker()
        self.llama_worker = LlamaWorker()
        self.whisper_worker = WhisperWorker()
        self.piper_worker = PiperWorker()
        self.blender_worker = BlenderWorker()

        self._tools: dict[str, dict[str, Any]] = {}
        self._register_default_tools()

    def register_tool(self, name: str, description: str, parameters: dict[str, Any], handler: Callable[..., Any]):
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
        }

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            }
            for t in self._tools.values()
        ]

    def execute(self, name: str, **kwargs) -> dict[str, Any]:
        if name not in self._tools:
            return {"status": "error", "message": f"Unknown tool: {name}"}
        try:
            return self._tools[name]["handler"](**kwargs)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _register_default_tools(self):
        # 1. story.create_or_update
        self.register_tool(
            name="story.create_or_update",
            description="Create or update story synopsis, logline, characters, locations, and shot list.",
            parameters={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "title": {"type": "string"},
                    "logline": {"type": "string"},
                    "characters": {"type": "array"},
                    "locations": {"type": "array"},
                    "shots": {"type": "array"},
                },
                "required": ["project_id", "title"],
            },
            handler=self._tool_story_create,
        )

        # 2. image.generate
        self.register_tool(
            name="image.generate",
            description="Generate a high-quality visual concept or reference image via Bonsai FLUX.2 Klein on Vulkan.",
            parameters={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "prompt": {"type": "string"},
                    "width": {"type": "integer", "default": 512},
                    "height": {"type": "integer", "default": 512},
                    "steps": {"type": "integer", "default": 4},
                    "output_filename": {"type": "string"},
                },
                "required": ["project_id", "prompt"],
            },
            handler=self._tool_image_generate,
        )

        # 3. asset.image_to_3d
        self.register_tool(
            name="asset.image_to_3d",
            description="Reconstruct an image into a 3D textured mesh GLB using TRELLIS.2.",
            parameters={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "image_path": {"type": "string"},
                    "output_filename": {"type": "string"},
                    "resolution": {"type": "integer", "default": 512},
                    "steps": {"type": "integer", "default": 1},
                },
                "required": ["project_id", "image_path"],
            },
            handler=self._tool_asset_image_to_3d,
        )

        # 4. voice.generate
        self.register_tool(
            name="voice.generate",
            description="Synthesize dialogue speech audio WAV from text using Piper neural TTS.",
            parameters={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "text": {"type": "string"},
                    "output_filename": {"type": "string"},
                    "speaker": {"type": "integer", "default": 0},
                },
                "required": ["project_id", "text"],
            },
            handler=self._tool_voice_generate,
        )

        # 5. speech.transcribe
        self.register_tool(
            name="speech.transcribe",
            description="Transcribe dialogue WAV audio using Whisper STT.",
            parameters={
                "type": "object",
                "properties": {
                    "audio_path": {"type": "string"},
                },
                "required": ["audio_path"],
            },
            handler=self._tool_speech_transcribe,
        )

        # 6. blender.render_turntable
        self.register_tool(
            name="blender.render_turntable",
            description="Render studio lighting turntable beauty shot of a GLB asset using Blender EEVEE.",
            parameters={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "glb_path": {"type": "string"},
                    "output_filename": {"type": "string"},
                    "width": {"type": "integer", "default": 1080},
                    "height": {"type": "integer", "default": 1080},
                },
                "required": ["project_id", "glb_path"],
            },
            handler=self._tool_blender_render_turntable,
        )

        # 7. timeline.assemble
        self.register_tool(
            name="timeline.assemble",
            description="Assemble shots and audio track into final 1080p MP4 master using Blender VSE and FFmpeg.",
            parameters={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "clips": {"type": "array", "items": {"type": "string"}},
                    "audio_path": {"type": "string"},
                    "output_filename": {"type": "string"},
                    "fps": {"type": "integer", "default": 24},
                    "seconds_per_still": {"type": "float", "default": 3.0},
                },
                "required": ["project_id", "clips"],
            },
            handler=self._tool_timeline_assemble,
        )

        # 8. camera.configure
        self.register_tool(
            name="camera.configure",
            description="Apply a validated camera preset and render proof still with Blender.",
            parameters={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "preset": {"type": "string"},
                    "lens_mm": {"type": "number"},
                    "output_filename": {"type": "string"},
                },
                "required": ["project_id", "preset"],
            },
            handler=self._tool_camera_configure,
        )

        # 9. lighting.configure
        self.register_tool(
            name="lighting.configure",
            description="Apply a validated lighting preset and render proof still with Blender.",
            parameters={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "preset": {"type": "string"},
                    "output_filename": {"type": "string"},
                },
                "required": ["project_id", "preset"],
            },
            handler=self._tool_lighting_configure,
        )

        # 10. fx.configure
        self.register_tool(
            name="fx.configure",
            description="Enable a deterministic Blender FX system and render proof still.",
            parameters={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "preset": {"type": "string"},
                    "output_filename": {"type": "string"},
                },
                "required": ["project_id", "preset"],
            },
            handler=self._tool_fx_configure,
        )

        # 11. motion.plan
        self.register_tool(
            name="motion.plan",
            description="Translate plain-text direction into structured editable motion steps.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                },
                "required": ["text"],
            },
            handler=self._tool_motion_plan,
        )

        # 12. lipsync.create (energy baseline; phoneme-exact path pending CosyVoice)
        self.register_tool(
            name="lipsync.create",
            description="Build jaw-open viseme timing from dialogue WAV energy and key it in Blender.",
            parameters={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "audio_path": {"type": "string"},
                    "output_filename": {"type": "string"},
                },
                "required": ["project_id", "audio_path"],
            },
            handler=self._tool_lipsync_create,
        )

        # 13b. storyboard.reorder (manual card reorder as versioned mutation)
        self.register_tool(
            name="storyboard.reorder",
            description="Move a shot to a new position inside its scene (renumbers siblings).",
            parameters={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "scene_id": {"type": "string"},
                    "shot_id": {"type": "string"},
                    "new_position": {"type": "integer", "minimum": 1},
                },
                "required": ["project_id", "scene_id", "shot_id", "new_position"],
            },
            handler=self._tool_storyboard_reorder,
        )

        # 13c. qa.movie (programmatic final gate over video + audio)
        self.register_tool(
            name="qa.movie",
            description="Run the programmatic final-movie QA gate (resolution/fps/durations).",
            parameters={
                "type": "object",
                "properties": {
                    "video_path": {"type": "string"},
                    "audio_path": {"type": "string"},
                    "width": {"type": "integer", "default": 1920},
                    "height": {"type": "integer", "default": 1080},
                    "fps": {"type": "integer", "default": 24},
                },
                "required": ["video_path"],
            },
            handler=self._tool_qa_movie,
        )

        # 13. music.generate (honest gate: EXPERIMENTAL until acestep.cpp staged)
        self.register_tool(
            name="music.generate",
            description="Generate music stems (UNAVAILABLE until ACE-Step runtime staged).",
            parameters={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "mood": {"type": "string"},
                    "tempo": {"type": "number"},
                },
                "required": ["project_id"],
            },
            handler=self._tool_music_generate,
        )

        # 8. agent.inspect_image
        self.register_tool(
            name="agent.inspect_image",
            description="Inspect and critique an image or rendered frame using Qwen3-VL 8B multimodal reasoning.",
            parameters={
                "type": "object",
                "properties": {
                    "image_path": {"type": "string"},
                    "prompt": {"type": "string"},
                },
                "required": ["image_path", "prompt"],
            },
            handler=self._tool_agent_inspect_image,
        )

    # ---------------- Tool Implementations ----------------

    def _tool_story_create(self, **kwargs) -> dict[str, Any]:
        project_id = kwargs["project_id"]
        title = kwargs["title"]
        logline = kwargs.get("logline", "")
        chars = kwargs.get("characters", [])
        locs = kwargs.get("locations", [])
        shots = kwargs.get("shots", [])

        with self.db.get_connection() as conn:
            # Update story bible with logline
            conn.execute(
                _SQL_STORY_BIBLE_UPSERT,
                ("story_synopsis", "story", title, logline, "main,logline"),
            )

            # Insert characters
            for c in chars:
                cid = c.get("id") or f"char_{c['name'].lower().replace(' ', '_')}"
                conn.execute(
                    _SQL_CHARACTER_UPSERT,
                    (cid, project_id, c["name"], c.get("description", ""), c.get("visual_style", "")),
                )
                char_content = f"{c.get('description', '')} | Style: {c.get('visual_style', '')}"
                conn.execute(
                    _SQL_STORY_BIBLE_UPSERT,
                    (cid, "character", c["name"], char_content, "character"),
                )

            # Insert locations
            for loc in locs:
                lid = loc.get("id") or f"loc_{loc['name'].lower().replace(' ', '_')}"
                conn.execute(
                    _SQL_LOCATION_UPSERT,
                    (
                        lid,
                        project_id,
                        loc["name"],
                        loc.get("description", ""),
                        loc.get("time_of_day", ""),
                        loc.get("weather", ""),
                    ),
                )
                loc_content = f"{loc.get('description', '')} | Weather: {loc.get('weather', '')}"
                conn.execute(
                    _SQL_STORY_BIBLE_UPSERT,
                    (lid, "location", loc["name"], loc_content, "location"),
                )

            # Insert scene 1 & shots
            conn.execute(
                _SQL_SCENE_UPSERT,
                (f"scene_{project_id}_1", project_id, 1, title, logline),
            )
            for idx, s in enumerate(shots, start=1):
                sid = f"shot_{project_id}_{idx}"
                conn.execute(
                    _SQL_SHOT_UPSERT,
                    (
                        sid,
                        f"scene_{project_id}_1",
                        project_id,
                        idx,
                        s.get("camera_prompt", ""),
                        s.get("action", ""),
                        s.get("dialogue", ""),
                        s.get("duration_sec", 3.0),
                    ),
                )
            conn.commit()

        msg = f"Story '{title}' committed: {len(chars)} characters, {len(locs)} locations, {len(shots)} shots."
        return {"status": "ok", "message": msg}

    def _tool_image_generate(self, **kwargs) -> dict[str, Any]:
        project_id = kwargs["project_id"]
        prompt = kwargs["prompt"]
        width = kwargs.get("width", 512)
        height = kwargs.get("height", 512)
        steps = kwargs.get("steps", 4)
        out_name = kwargs.get("output_filename") or f"gen_{os.urandom(4).hex()}.png"

        out_path = self.project_root / "images" / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)

        req = WorkerRequest(
            job_id=f"job_img_{os.urandom(4).hex()}",
            project_id=project_id,
            task_type="image.text_to_image",
            priority=20,
            parameters={
                "prompt": prompt,
                "output_image": str(out_path),
                "width": width,
                "height": height,
                "steps": steps,
            },
        )
        resp = self.sd_worker.run(req)
        if resp.error:
            return {"status": "error", "message": resp.error}

        # Register immutable artifact
        rec = self.artifact_mgr.register_artifact(
            project_id=project_id,
            kind=ArtifactKind.IMAGE,
            file_path=out_path,
            producer="stable-diffusion.cpp",
            producer_version="master-920",
            model_id="image.bonsai.flux2-klein.q2k",
            canonical=True,
            metadata={"prompt": prompt, "width": width, "height": height, "steps": steps},
        )
        return {
            "status": "ok",
            "artifact_id": rec.artifact_id,
            "path": str(out_path),
            "relative_path": rec.relative_path,
        }

    def _tool_asset_image_to_3d(self, **kwargs) -> dict[str, Any]:
        project_id = kwargs["project_id"]
        image_path = kwargs["image_path"]
        out_name = kwargs.get("output_filename") or f"mesh_{os.urandom(4).hex()}.glb"
        resolution = kwargs.get("resolution", 512)
        steps = kwargs.get("steps", 1)

        out_path = self.project_root / "props" / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)

        req = WorkerRequest(
            job_id=f"job_3d_{os.urandom(4).hex()}",
            project_id=project_id,
            task_type="3d.image_to_3d",
            priority=20,
            parameters={
                "image_path": str(image_path),
                "output_glb": str(out_path),
                "resolution": resolution,
                "steps": steps,
                "backend": "CPU",
                "box_uv": True,
                "no_texture": True,
            },
        )
        resp = self.trellis_worker.run(req)
        if resp.error:
            return {"status": "error", "message": resp.error}

        rec = self.artifact_mgr.register_artifact(
            project_id=project_id,
            kind=ArtifactKind.MESH_RAW,
            file_path=out_path,
            producer="trellis.cpp",
            producer_version="0.8.1",
            model_id="3d.trellis2.q4",
            canonical=True,
            metadata={"resolution": resolution, "steps": steps},
        )
        return {
            "status": "ok",
            "artifact_id": rec.artifact_id,
            "path": str(out_path),
            "relative_path": rec.relative_path,
        }

    def _tool_voice_generate(self, **kwargs) -> dict[str, Any]:
        project_id = kwargs["project_id"]
        text = kwargs["text"]
        out_name = kwargs.get("output_filename") or f"voice_{os.urandom(4).hex()}.wav"
        speaker = kwargs.get("speaker", 0)

        out_path = self.project_root / "audio" / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)

        req = WorkerRequest(
            job_id=f"job_voice_{os.urandom(4).hex()}",
            project_id=project_id,
            task_type="audio.synthesize_speech",
            priority=20,
            parameters={
                "text": text,
                "output_wav": str(out_path),
                "speaker": speaker,
            },
        )
        resp = self.piper_worker.run(req)
        if resp.error:
            return {"status": "error", "message": resp.error}

        rec = self.artifact_mgr.register_artifact(
            project_id=project_id,
            kind=ArtifactKind.AUDIO_VOICE,
            file_path=out_path,
            producer="piper",
            producer_version="1.8.0",
            model_id="voice.piper.en_lessac_medium",
            canonical=True,
            metadata={"text": text, "speaker": speaker},
        )
        return {
            "status": "ok",
            "artifact_id": rec.artifact_id,
            "path": str(out_path),
            "relative_path": rec.relative_path,
        }

    def _tool_speech_transcribe(self, **kwargs) -> dict[str, Any]:
        audio_path = kwargs["audio_path"]
        req = WorkerRequest(
            job_id=f"job_stt_{os.urandom(4).hex()}",
            project_id="transcribe",
            task_type="speech.transcribe",
            priority=20,
            parameters={"audio_file": str(audio_path)},
        )
        resp = self.whisper_worker.run(req)
        if resp.error:
            return {"status": "error", "message": resp.error}
        text = resp.artifacts[0].get("text", "") if resp.artifacts else ""
        return {"status": "ok", "transcript": text}

    def _tool_blender_render_turntable(self, **kwargs) -> dict[str, Any]:
        project_id = kwargs["project_id"]
        glb_path = kwargs["glb_path"]
        out_name = kwargs.get("output_filename") or f"render_{os.urandom(4).hex()}.png"
        width = kwargs.get("width", 1080)
        height = kwargs.get("height", 1080)

        out_path = self.project_root / "renders" / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)

        script = Path("integrations/blender/scripts/import_and_render_turntable.py").resolve()
        cmd = [
            self.blender_worker.blender_path,
            "-b",
            "--python",
            str(script),
            "--",
            "--input",
            str(Path(glb_path).resolve()),
            "--output",
            str(out_path.resolve()),
            "--width",
            str(width),
            "--height",
            str(height),
            "--frames",
            "1",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not out_path.exists():
            return {"status": "error", "message": f"Blender turntable failed: {res.stderr[-500:]}"}

        rec = self.artifact_mgr.register_artifact(
            project_id=project_id,
            kind=ArtifactKind.IMAGE,
            file_path=out_path,
            producer="blender",
            producer_version="5.1.2",
            canonical=True,
            metadata={"width": width, "height": height, "glb": str(glb_path)},
        )
        return {
            "status": "ok",
            "artifact_id": rec.artifact_id,
            "path": str(out_path),
            "relative_path": rec.relative_path,
        }

    def _tool_timeline_assemble(self, **kwargs) -> dict[str, Any]:
        project_id = kwargs["project_id"]
        clips = kwargs["clips"]
        audio_path = kwargs.get("audio_path")
        out_name = kwargs.get("output_filename") or f"final_master_{os.urandom(4).hex()}.mp4"
        fps = kwargs.get("fps", 24)
        duration_per_still = kwargs.get("seconds_per_still", 3.0)

        out_path = self.project_root / "exports" / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)

        script = Path("integrations/blender/scripts/assemble_timeline.py").resolve()
        cmd = [
            self.blender_worker.blender_path,
            "-b",
            "--python",
            str(script),
            "--",
            "--clips",
            *[str(Path(c).resolve()) for c in clips],
            "--output",
            str(out_path.resolve()),
            "--fps",
            str(fps),
            "--seconds-per-still",
            str(duration_per_still),
        ]
        if audio_path:
            cmd.extend(["--audio", str(Path(audio_path).resolve())])

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not out_path.exists():
            return {"status": "error", "message": f"Timeline assembly failed: {res.stderr[-500:]}"}

        rec = self.artifact_mgr.register_artifact(
            project_id=project_id,
            kind=ArtifactKind.VIDEO_MASTER,
            file_path=out_path,
            producer="blender_vse_ffmpeg",
            producer_version="1.0.0",
            canonical=True,
            metadata={"fps": fps, "clips_count": len(clips)},
        )
        return {
            "status": "ok",
            "artifact_id": rec.artifact_id,
            "path": str(out_path),
            "relative_path": rec.relative_path,
        }

    def _tool_cine_render(self, project_id: str, module: str, preset: str, out_name: str | None) -> dict[str, Any]:
        from integrations.blender.cine import validate_camera_preset, validate_lighting_preset

        if module == "camera":
            ok, errors = validate_camera_preset(preset, {})
            if not ok:
                return {"status": "error", "message": f"camera preset invalid: {errors}"}
        elif module == "lighting":
            ok, errors = validate_lighting_preset(preset, {})
            if not ok:
                return {"status": "error", "message": f"lighting preset invalid: {errors}"}
        out_path = self.project_root / "renders" / (out_name or f"{module}_{preset}_{os.urandom(4).hex()}.png")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path = out_path.with_suffix(".json")
        script = Path("integrations/blender/scripts/apply_cine.py").resolve()
        cmd = [
            self.blender_worker.blender_path,
            "-b",
            "--python",
            str(script),
            "--",
            "--module",
            module,
            "--preset",
            preset,
            "--output",
            str(out_path.resolve()),
            "--evidence",
            str(evidence_path.resolve()),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if res.returncode != 0 or not out_path.exists():
            return {"status": "error", "message": f"cine {module}/{preset} failed: {res.stderr[-500:]}"}
        rec = self.artifact_mgr.register_artifact(
            project_id=project_id,
            kind=ArtifactKind.IMAGE,
            file_path=out_path,
            producer="blender_cine",
            producer_version="1.0.0",
            canonical=True,
            metadata={"module": module, "preset": preset},
        )
        return {"status": "ok", "artifact_id": rec.artifact_id, "path": str(out_path)}

    def _tool_camera_configure(self, **kwargs) -> dict[str, Any]:
        return self._tool_cine_render(kwargs["project_id"], "camera", kwargs["preset"], kwargs.get("output_filename"))

    def _tool_lighting_configure(self, **kwargs) -> dict[str, Any]:
        return self._tool_cine_render(kwargs["project_id"], "lighting", kwargs["preset"], kwargs.get("output_filename"))

    def _tool_fx_configure(self, **kwargs) -> dict[str, Any]:
        return self._tool_cine_render(kwargs["project_id"], "fx", kwargs["preset"], kwargs.get("output_filename"))

    def _tool_motion_plan(self, **kwargs) -> dict[str, Any]:
        from integrations.blender.cine import parse_motion_plan

        return {"status": "ok", "steps": parse_motion_plan(kwargs["text"])}

    def _tool_lipsync_create(self, **kwargs) -> dict[str, Any]:
        import json as _json

        from integrations.blender.lipsync import wav_to_visemes

        project_id = kwargs["project_id"]
        try:
            timeline = wav_to_visemes(kwargs["audio_path"])
        except Exception as e:
            return {"status": "error", "message": f"viseme analysis failed: {e}"}
        if not timeline:
            return {"status": "error", "message": "empty viseme timeline"}
        out_name = kwargs.get("output_filename") or f"lipsync_{os.urandom(4).hex()}.png"
        out_path = self.project_root / "renders" / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        vis_path = out_path.with_suffix(".visemes.json")
        ev_path = out_path.with_suffix(".evidence.json")
        with open(vis_path, "w", encoding="utf-8") as f:
            _json.dump(timeline, f, indent=2)
        script = Path("integrations/blender/scripts/lipsync_apply.py").resolve()
        cmd = [
            self.blender_worker.blender_path,
            "-b",
            "--python",
            str(script),
            "--",
            "--visemes",
            str(vis_path.resolve()),
            "--output",
            str(out_path.resolve()),
            "--evidence",
            str(ev_path.resolve()),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if res.returncode != 0 or not out_path.exists():
            return {"status": "error", "message": f"lipsync Blender pass failed: {res.stderr[-500:]}"}
        rec = self.artifact_mgr.register_artifact(
            project_id=project_id,
            kind=ArtifactKind.ANIMATION,
            file_path=out_path,
            producer="blender_lipsync_baseline",
            producer_version="1.0.0",
            canonical=True,
            metadata={"viseme_frames": len(timeline), "method": "rms_energy_baseline"},
        )
        return {"status": "ok", "artifact_id": rec.artifact_id, "path": str(out_path), "frames": len(timeline)}

    def _tool_storyboard_reorder(self, **kwargs) -> dict[str, Any]:
        project_id, scene_id, shot_id, pos = (
            kwargs["project_id"],
            kwargs["scene_id"],
            kwargs["shot_id"],
            int(kwargs["new_position"]),
        )
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT shot_id FROM shots WHERE project_id = ? AND scene_id = ? ORDER BY shot_number ASC",
                (project_id, scene_id),
            ).fetchall()
            order = [r["shot_id"] for r in rows]
            if shot_id not in order:
                return {"status": "error", "message": f"shot {shot_id} not in scene {scene_id}"}
            order.remove(shot_id)
            order.insert(max(0, min(pos - 1, len(order))), shot_id)
            for i, sid in enumerate(order, start=1):
                conn.execute("UPDATE shots SET shot_number = ? WHERE shot_id = ?", (i, sid))
            conn.commit()
        return {"status": "ok", "order": order}

    def _tool_qa_movie(self, **kwargs) -> dict[str, Any]:
        from packages.validators.src.movie_qa import qa_movie

        verdict = qa_movie(
            kwargs["video_path"],
            kwargs.get("audio_path"),
            kwargs.get("width", 1920),
            kwargs.get("height", 1080),
            kwargs.get("fps", 24),
        )
        return {"status": "ok" if verdict["passed"] else "error", **verdict}

    def _tool_music_generate(self, **kwargs) -> dict[str, Any]:
        return {
            "status": "error",
            "error_class": "MISSING_DEPENDENCY",
            "message": (
                "music.generate UNAVAILABLE: acestep.cpp runtime not staged (see integrations/acestep/STATUS.md)."
            ),
        }

    def _tool_agent_inspect_image(self, **kwargs) -> dict[str, Any]:
        image_path = kwargs["image_path"]
        prompt = kwargs["prompt"]

        req = WorkerRequest(
            job_id=f"job_inspect_{os.urandom(4).hex()}",
            project_id="qa_inspection",
            task_type="agent.inspect_image",
            priority=10,
            parameters={
                "prompt": prompt,
                "image_file": str(image_path),
            },
        )
        resp = self.llama_worker.run(req)
        if resp.error:
            return {"status": "error", "message": resp.error}
        text = resp.artifacts[0].get("text", "") if resp.artifacts else ""
        return {"status": "ok", "analysis": text}
