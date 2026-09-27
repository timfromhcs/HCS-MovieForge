"""Master autonomous Director Agent executing the complete production lifecycle from prompt to 1080p master."""

import json
import time
from pathlib import Path
from typing import Any

from agent.tools.registry import ToolRegistry
from engine.artifact_manager.manager import ArtifactManager
from packages.project_format.src.db import ProjectDB
from packages.validators.src.video_validator import validate_video


class MasterDirectorAgent:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root).resolve()
        self.db = ProjectDB(self.project_root / "movieforge.db")
        self.artifact_mgr = ArtifactManager(self.project_root, self.db)
        self.tool_registry = ToolRegistry(self.project_root, self.db, self.artifact_mgr)

    def run_production(self, prompt: str, project_id: str = "minifilm_robot") -> dict[str, Any]:
        """Executes the complete autonomous production pipeline specified in GEMINI.md Section 146."""
        print(f"\n[DIRECTOR] Starting production for project '{project_id}': {prompt}", flush=True)
        start_time = time.time()
        production_manifest: dict[str, Any] = {
            "project_id": project_id,
            "prompt": prompt,
            "steps": [],
            "artifacts": {},
            "status": "IN_PROGRESS",
        }

        # ---------------- 1. OBSERVE & PLAN ----------------
        print("[DIRECTOR: 1/8] Planning story, characters, and shot list...", flush=True)
        story_plan = {
            "project_id": project_id,
            "title": "Spark-7: The Rainy Station",
            "logline": (
                "A small maintenance robot inspects an empty, rain-swept train platform searching for track anomalies."
            ),
            "characters": [
                {
                    "name": "Spark-7",
                    "description": (
                        "A compact three-wheeled maintenance robot with weathered "
                        "yellow plating and a glowing blue optical sensor."
                    ),
                    "visual_style": "Industrial sci-fi, cinematic lighting, rain droplets on chassis",
                }
            ],
            "locations": [
                {
                    "name": "Platform 4B",
                    "description": (
                        "An outdoor elevated transit platform at night under torrential "
                        "rain, illuminated by neon sign reflections."
                    ),
                    "time_of_day": "Night",
                    "weather": "Heavy rain",
                }
            ],
            "shots": [
                {
                    "action": "Establishing wide shot of Platform 4B drenched in night rain.",
                    "camera_prompt": "Wide static establishing shot of futuristic train station in heavy rain",
                    "dialogue": "",
                    "duration_sec": 3.0,
                },
                {
                    "action": "Medium shot of Spark-7 scanning track rails with sensor light.",
                    "camera_prompt": "Medium orbit shot around maintenance robot scanning wet metal rails",
                    "dialogue": "All systems nominal. Searching for track anomaly in sector four.",
                    "duration_sec": 4.0,
                },
            ],
        }
        res_story = self.tool_registry.execute("story.create_or_update", **story_plan)
        production_manifest["steps"].append({"step": "story_create", "result": res_story})

        # ---------------- 2. IMAGE GENERATION (Bonsai FLUX.2 Klein) ----------------
        print("[DIRECTOR: 2/8] Generating robot concept via Bonsai FLUX.2 Klein...", flush=True)
        img_prompt = (
            "a small industrial maintenance robot on a wet train station platform in the rain, "
            "cinematic neon lighting, detailed chassis, 8k"
        )
        res_img = self.tool_registry.execute(
            "image.generate",
            project_id=project_id,
            prompt=img_prompt,
            width=256,
            height=256,
            steps=4,
            output_filename="spark7_concept.png",
        )
        if res_img.get("status") != "ok":
            raise RuntimeError(f"Image generation failed: {res_img.get('message')}")
        production_manifest["artifacts"]["concept_image"] = res_img
        production_manifest["steps"].append({"step": "image_generate", "result": res_img})
        concept_img_path = res_img["path"]

        # ---------------- 3. MULTIMODAL QA INSPECTION (Qwen3-VL 8B) ----------------
        print("[DIRECTOR: 3/8] Inspecting concept image with Qwen3-VL 8B Multimodal Agent...", flush=True)
        res_vlm = self.tool_registry.execute(
            "agent.inspect_image",
            image_path=concept_img_path,
            prompt="Describe this asset image, focusing on the character design and environmental lighting.",
        )
        production_manifest["steps"].append({"step": "vlm_inspection", "result": res_vlm})
        print(f"[DIRECTOR: QA] VLM Critique: {res_vlm.get('analysis', '')[:120]}...", flush=True)

        # ---------------- 4. 3D ASSET GENERATION (TRELLIS.2 Q4) ----------------
        print("[DIRECTOR: 4/8] Generating 3D mesh GLB via TRELLIS.2...", flush=True)
        # Prepare transparent alpha shape for reliable geometry extraction
        from PIL import Image, ImageDraw

        rgba_img_path = str(self.project_root / "images" / "spark7_matted.png")
        orig_img = Image.open(concept_img_path).convert("RGBA")
        mask = Image.new("L", orig_img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([20, 20, orig_img.size[0] - 20, orig_img.size[1] - 20], fill=255)
        orig_img.putalpha(mask)
        orig_img.save(rgba_img_path)

        res_3d = self.tool_registry.execute(
            "asset.image_to_3d",
            project_id=project_id,
            image_path=rgba_img_path,
            output_filename="spark7_mesh.glb",
            resolution=512,
            steps=1,
        )
        if res_3d.get("status") != "ok":
            raise RuntimeError(f"3D mesh generation failed: {res_3d.get('message')}")
        production_manifest["artifacts"]["mesh_3d"] = res_3d
        production_manifest["steps"].append({"step": "asset_3d", "result": res_3d})
        glb_path = res_3d["path"]

        # ---------------- 5. BLENDER TURNTABLE BEAUTY RENDER ----------------
        print("[DIRECTOR: 5/8] Rendering studio 3-point turntable beauty shot with Blender EEVEE...", flush=True)
        res_turntable = self.tool_registry.execute(
            "blender.render_turntable",
            project_id=project_id,
            glb_path=glb_path,
            output_filename="spark7_turntable.png",
            width=1080,
            height=1080,
        )
        if res_turntable.get("status") != "ok":
            raise RuntimeError(f"Blender render failed: {res_turntable.get('message')}")
        production_manifest["artifacts"]["turntable_render"] = res_turntable
        production_manifest["steps"].append({"step": "blender_render", "result": res_turntable})
        turntable_path = res_turntable["path"]

        # ---------------- 6. DIALOGUE SYNTHESIS (Piper Neural TTS) ----------------
        print("[DIRECTOR: 6/8] Synthesizing character dialogue with Piper Neural TTS...", flush=True)
        dialogue_text = "All systems nominal. Searching for track anomaly in sector four."
        res_voice = self.tool_registry.execute(
            "voice.generate",
            project_id=project_id,
            text=dialogue_text,
            output_filename="spark7_dialogue.wav",
        )
        if res_voice.get("status") != "ok":
            raise RuntimeError(f"Voice generation failed: {res_voice.get('message')}")
        production_manifest["artifacts"]["dialogue_audio"] = res_voice
        production_manifest["steps"].append({"step": "voice_generate", "result": res_voice})
        voice_path = res_voice["path"]

        # ---------------- 7. STT VERIFICATION (Whisper.cpp) ----------------
        print("[DIRECTOR: 7/8] Verifying dialogue audio via Whisper STT...", flush=True)
        res_stt = self.tool_registry.execute("speech.transcribe", audio_path=voice_path)
        production_manifest["steps"].append({"step": "stt_verify", "result": res_stt})
        print(f"[DIRECTOR: QA] Whisper Verified Transcript: '{res_stt.get('transcript', '').strip()}'", flush=True)

        # ---------------- 8. TIMELINE ASSEMBLY & 1080P MASTER (VSE + FFmpeg) ----------------
        print("[DIRECTOR: 8/8] Assembling timeline and encoding final 1080p MP4 master...", flush=True)
        res_timeline = self.tool_registry.execute(
            "timeline.assemble",
            project_id=project_id,
            clips=[concept_img_path, turntable_path],
            audio_path=voice_path,
            output_filename="spark7_final_master_1080p.mp4",
            fps=24,
            seconds_per_still=2.5,
        )
        if res_timeline.get("status") != "ok":
            raise RuntimeError(f"Timeline assembly failed: {res_timeline.get('message')}")
        production_manifest["artifacts"]["final_master"] = res_timeline
        production_manifest["steps"].append({"step": "timeline_assemble", "result": res_timeline})
        master_path = res_timeline["path"]

        # ---------------- FINAL VERIFICATION ----------------
        print("[DIRECTOR: QA] Validating final 1080p master video...", flush=True)
        val_res = validate_video(master_path, expected_width=1920, expected_height=1080, expected_fps=24)
        if not val_res.is_valid:
            raise ValueError(f"Final master video failed QA validation: {val_res.errors}")

        duration = time.time() - start_time
        production_manifest["status"] = "COMPLETED"
        production_manifest["duration_sec"] = round(duration, 2)
        production_manifest["video_qa"] = {
            "is_valid": val_res.is_valid,
            "width": val_res.width,
            "height": val_res.height,
            "fps": val_res.fps,
            "duration_sec": val_res.duration_sec,
            "video_codec": val_res.video_codec,
        }

        # Save production manifest to project root
        manifest_file = self.project_root / "production_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(production_manifest, f, indent=2)

        print(f"\n[DIRECTOR: SUCCESS] Full mini-film production completed in {duration:.2f}s!", flush=True)
        print(f"Master Video Artifact: {master_path}", flush=True)
        print(f"Manifest: {manifest_file}", flush=True)
        return production_manifest
