"""Blender headless script: import GLB, set up studio light + turntable, render EEVEE."""

import argparse
import math
import sys

import bpy
import mathutils


def parse_args():
    # Everything after '--' is user arguments
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        raw_args = sys.argv[idx + 1 :]
    else:
        raw_args = []

    parser = argparse.ArgumentParser(description="Render 3D asset turntable in Blender EEVEE.")
    parser.add_argument("--input", required=True, help="Path to input GLTF/GLB file")
    parser.add_argument("--output", required=True, help="Output image or video path")
    parser.add_argument("--width", type=int, default=1080, help="Render width in pixels")
    parser.add_argument("--height", type=int, default=1080, help="Render height in pixels")
    parser.add_argument("--frames", type=int, default=1, help="Number of turntable frames (1 = single beauty shot)")
    args = parser.parse_args(raw_args)
    import os

    args.input = os.path.abspath(args.input)
    args.output = os.path.abspath(args.output)
    return args


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def setup_lighting():
    # Key light
    key_data = bpy.data.lights.new(name="KeyLight", type="SUN")
    key_data.energy = 3.5
    key_data.color = (1.0, 0.98, 0.95)
    key_obj = bpy.data.objects.new(name="KeyLight", object_data=key_data)
    key_obj.rotation_euler = (math.radians(45), math.radians(20), math.radians(30))
    bpy.context.collection.objects.link(key_obj)

    # Fill light
    fill_data = bpy.data.lights.new(name="FillLight", type="SUN")
    fill_data.energy = 1.5
    fill_data.color = (0.85, 0.9, 1.0)
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
    fill_obj.rotation_euler = (math.radians(60), math.radians(-30), math.radians(-120))
    bpy.context.collection.objects.link(fill_obj)

    # Rim light
    rim_data = bpy.data.lights.new(name="RimLight", type="SUN")
    rim_data.energy = 2.0
    rim_data.color = (1.0, 0.95, 0.9)
    rim_obj = bpy.data.objects.new(name="RimLight", object_data=rim_data)
    rim_obj.rotation_euler = (math.radians(-30), math.radians(10), math.radians(150))
    bpy.context.collection.objects.link(rim_obj)


def setup_camera(target_center, target_radius, frames=1):
    cam_data = bpy.data.cameras.new(name="TurntableCamera")
    cam_data.lens = 50.0
    cam_data.clip_start = 0.1
    cam_data.clip_end = 1000.0

    cam_obj = bpy.data.objects.new(name="TurntableCamera", object_data=cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # Position camera based on bounding radius
    distance = max(target_radius * 2.8, 1.5)
    cam_height = target_radius * 0.8
    cam_obj.location = (target_center[0], target_center[1] - distance, target_center[2] + cam_height)

    # Create empty at target center for camera tracking
    target_empty = bpy.data.objects.new(name="TargetEmpty", object_data=None)
    target_empty.location = target_center
    bpy.context.collection.objects.link(target_empty)

    track = cam_obj.constraints.new(type="TRACK_TO")
    track.target = target_empty
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"

    # Turntable orbit animation if frames > 1
    if frames > 1:
        # Parent camera to empty and rotate empty
        cam_obj.parent = target_empty
        target_empty.rotation_euler = (0, 0, 0)
        target_empty.keyframe_insert(data_path="rotation_euler", frame=1)
        target_empty.rotation_euler = (0, 0, math.radians(360))
        target_empty.keyframe_insert(data_path="rotation_euler", frame=frames + 1)

        # Set linear interpolation
        if target_empty.animation_data and target_empty.animation_data.action:
            for fcurve in target_empty.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = "LINEAR"


def main():
    args = parse_args()
    clear_scene()

    # Import GLB
    bpy.ops.import_scene.gltf(filepath=args.input)

    # Calculate bounding box across all imported mesh objects
    imported_meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not imported_meshes:
        print("[FAIL] No meshes imported from GLB.")
        sys.exit(1)

    min_coord = [float("inf")] * 3
    max_coord = [float("-inf")] * 3

    for obj in imported_meshes:
        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ mathutils.Vector(corner)
            for i in range(3):
                min_coord[i] = min(min_coord[i], world_corner[i])
                max_coord[i] = max(max_coord[i], world_corner[i])

    center = [(min_coord[i] + max_coord[i]) / 2.0 for i in range(3)]
    radius = max((max_coord[i] - min_coord[i]) / 2.0 for i in range(3))
    if radius <= 0:
        radius = 1.0

    setup_lighting()
    setup_camera(center, radius, frames=args.frames)

    # Render configuration
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"

    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True

    if args.frames > 1:
        scene.frame_start = 1
        scene.frame_end = args.frames
        scene.render.filepath = args.output
        if args.output.endswith((".mp4", ".mov", ".mkv")):
            scene.render.image_settings.file_format = "FFMPEG"
            scene.render.ffmpeg.format = "MPEG4"
            scene.render.ffmpeg.codec = "H264"
            scene.render.ffmpeg.constant_rate_factor = "HIGH"
        bpy.ops.render.render(animation=True)
    else:
        scene.frame_current = 1
        scene.render.filepath = args.output
        scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)

    print(f"[OK] Render successfully completed to {args.output}")


if __name__ == "__main__":
    main()
