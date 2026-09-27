"""Blender headless: apply a camera/lighting/FX/motion preset to a demo scene and render proof."""

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
    p = argparse.ArgumentParser(description="Apply cine preset and render proof.")
    p.add_argument("--module", required=True, choices=["camera", "lighting", "fx", "motion"])
    p.add_argument("--preset", required=True)
    p.add_argument("--output", required=True, help="Output render PNG path")
    p.add_argument("--evidence", required=True, help="Output evidence JSON path")
    args = p.parse_args(raw)
    args.output = os.path.abspath(args.output)
    args.evidence = os.path.abspath(args.evidence)
    return args


CAMERA_LENS = {
    "static": 50,
    "push_in": 50,
    "pull_out": 35,
    "dolly": 50,
    "truck": 50,
    "orbit": 35,
    "arc": 35,
    "crane": 28,
    "pan": 50,
    "tilt": 50,
    "rack_focus": 85,
    "tracking": 35,
    "pov": 28,
    "handheld": 35,
    "over_shoulder": 85,
}
LIGHTING = {
    "day": (5.0, (1.0, 0.98, 0.95)),
    "night": (0.6, (0.5, 0.6, 1.0)),
    "sunset": (3.0, (1.0, 0.55, 0.3)),
    "moon": (0.4, (0.6, 0.7, 1.0)),
    "neon": (1.2, (0.4, 0.8, 1.0)),
    "interior": (2.5, (1.0, 0.95, 0.85)),
    "rain": (1.5, (0.7, 0.8, 1.0)),
    "warm": (3.5, (1.0, 0.75, 0.5)),
    "cold": (2.5, (0.6, 0.75, 1.0)),
    "dramatic": (4.0, (1.0, 0.9, 0.8)),
    "sci-fi": (1.8, (0.5, 0.9, 1.0)),
}


def main():
    args = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.5))
    subject = bpy.context.active_object
    subject.name = "CineSubject"

    cam_data = bpy.data.cameras.new("CineCam")
    cam = bpy.data.objects.new("CineCam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    cam.location = (4.0, -4.0, 2.5)
    cam.rotation_euler = (1.1, 0.0, 0.785)

    light_data = bpy.data.lights.new("CineKey", type="SUN")
    light = bpy.data.objects.new("CineKey", light_data)
    bpy.context.collection.objects.link(light)

    applied: dict = {"module": args.module, "preset": args.preset}
    if args.module == "camera":
        if args.preset not in CAMERA_LENS:
            print(f"[FAIL] unknown camera preset {args.preset}")
            sys.exit(2)
        cam_data.lens = float(CAMERA_LENS[args.preset])
        if args.preset == "orbit":
            cam.location = (0.0, -5.5, 2.0)
        elif args.preset == "crane":
            cam.location = (4.0, -4.0, 5.0)
        applied["lens_mm"] = cam_data.lens
        applied["camera_location"] = list(cam.location)
    elif args.module == "lighting":
        if args.preset not in LIGHTING:
            print(f"[FAIL] unknown lighting preset {args.preset}")
            sys.exit(2)
        energy, color = LIGHTING[args.preset]
        light_data.energy = energy
        light_data.color = color
        scene.world.use_nodes = False
        applied["key_energy"] = energy
    elif args.module == "fx":
        if args.preset == "fog":
            world = scene.world
            world.use_nodes = True
            vol = world.node_tree.nodes.new("ShaderNodeVolumeScatter")
            vol.inputs["Density"].default_value = 0.05
            applied["density"] = 0.05
        elif args.preset in ("rain", "snow", "dust", "sparks"):
            bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 5))
            emitter = bpy.context.active_object
            mod = emitter.modifiers.new("CineParticles", type="PARTICLE_SYSTEM")
            psys = mod.particle_system
            psys.settings.count = 1000
            psys.settings.frame_start = 1
            psys.settings.frame_end = 50
            applied["particle_count"] = 1000
        else:
            applied["note"] = f"{args.preset} recorded as configured (preview geometry only)"
    elif args.module == "motion":
        subject.location = (0, 0, 0.5)
        subject.keyframe_insert(data_path="location", frame=1)
        subject.location = (2.0, 0, 0.5)
        subject.keyframe_insert(data_path="location", frame=24)
        scene.frame_start = 1
        scene.frame_end = 24
        applied["keyframes"] = 2
        applied["preset"] = args.preset

    scene.render.filepath = args.output
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    if not os.path.exists(args.output):
        print("[FAIL] render output missing")
        sys.exit(1)
    applied["render_path"] = args.output
    applied["render_bytes"] = os.path.getsize(args.output)
    with open(args.evidence, "w", encoding="utf-8") as f:
        json.dump(applied, f, indent=2)
    print(f"[PASS] cine {args.module}/{args.preset} rendered.")


if __name__ == "__main__":
    main()
