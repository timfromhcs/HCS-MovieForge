"""Blender headless: drive a jaw cube from a viseme timeline JSON and render proof."""

import argparse
import json
import os
import sys

import bpy


def parse_args():
    if "--" in sys.argv:
        raw = sys.argv[sys.argv.index("--") + 1 :]
    else:
        raw = []
    p = argparse.ArgumentParser(description="Apply viseme timeline to jaw proxy.")
    p.add_argument("--visemes", required=True, help="Viseme timeline JSON path")
    p.add_argument("--output", required=True, help="Proof render PNG path")
    p.add_argument("--evidence", required=True)
    p.add_argument("--fps", type=int, default=24)
    args = p.parse_args(raw)
    for attr in ("visemes", "output", "evidence"):
        setattr(args, attr, os.path.abspath(getattr(args, attr)))
    return args


def main():
    args = parse_args()
    with open(args.visemes, encoding="utf-8") as f:
        timeline = json.load(f)
    if not timeline:
        print("[FAIL] empty viseme timeline")
        sys.exit(1)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 360
    scene.render.fps = args.fps
    bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 0, 0.6))
    jaw = bpy.context.active_object
    jaw.name = "JawProxy"
    bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0, 0, 1.6))
    head = bpy.context.active_object
    head.name = "HeadProxy"
    cam_data = bpy.data.cameras.new("LipCam")
    cam = bpy.data.objects.new("LipCam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    cam.location = (2.5, -2.5, 1.5)

    cam.rotation_euler = (1.1, 0.0, 0.785)
    sun = bpy.data.lights.new("LipSun", type="SUN")
    sun.energy = 3.0
    bpy.context.collection.objects.link(bpy.data.objects.new("LipSun", sun))
    last_frame = 1
    for entry in timeline:
        frame = max(1, int(entry["t_sec"] * args.fps) + 1)
        jaw.scale = (1.0, 1.0, max(0.15, 1.0 - 0.85 * float(entry["jaw_open"])))
        jaw.keyframe_insert(data_path="scale", frame=frame)
        last_frame = max(last_frame, frame)
    scene.frame_start = 1
    scene.frame_end = last_frame
    mid = timeline[len(timeline) // 2]
    scene.frame_set(max(1, int(mid["t_sec"] * args.fps) + 1))
    scene.render.filepath = args.output
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    if not os.path.exists(args.output):
        print("[FAIL] lipsync proof render missing")
        sys.exit(1)
    evidence = {
        "frames": len(timeline),
        "last_frame": last_frame,
        "mid_viseme": mid["viseme"],
        "render": args.output,
    }
    with open(args.evidence, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)
    print(f"[PASS] lipsync: {len(timeline)} viseme frames keyed.")


if __name__ == "__main__":
    main()
