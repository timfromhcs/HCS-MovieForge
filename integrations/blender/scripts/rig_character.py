"""Blender headless: import GLB, normalize scale, gate humanoid suitability, rigify when viable.

TRELLIS-generated blobs are NOT humanoid; the script reports BLOCKED_NON_HUMANOID with
real measurements instead of fabricating a rig. Exit 0 on rigged, 2 on honest block.
"""

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
    p = argparse.ArgumentParser(description="Rigify a character GLB when humanoid.")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True, help="Output .blend path (written only when rigged)")
    p.add_argument("--evidence", required=True)
    args = p.parse_args(raw)
    args.input = os.path.abspath(args.input)
    args.output = os.path.abspath(args.output)
    args.evidence = os.path.abspath(args.evidence)
    return args


def main():
    args = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.preferences.addon_enable(module="rigify")
    bpy.ops.import_scene.gltf(filepath=args.input)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        with open(args.evidence, "w", encoding="utf-8") as f:
            json.dump({"status": "BLOCKED_NO_MESH", "input": args.input}, f, indent=2)
        print("[BLOCKED] no mesh in GLB")
        sys.exit(2)
    # Normalize: longest dimension -> 1.8m
    dims = [0.0, 0.0, 0.0]
    for o in meshes:
        for i in range(3):
            dims[i] = max(dims[i], float(o.dimensions[i]))
    longest = max(dims)
    if longest <= 0:
        with open(args.evidence, "w", encoding="utf-8") as f:
            json.dump({"status": "BLOCKED_DEGENERATE", "dims": dims}, f, indent=2)
        print("[BLOCKED] degenerate mesh")
        sys.exit(2)
    scale = 1.8 / longest
    for o in meshes:
        o.scale = (scale, scale, scale)
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(scale=True)
    dims_n = [0.0, 0.0, 0.0]
    for o in meshes:
        for i in range(3):
            dims_n[i] = max(dims_n[i], float(o.dimensions[i]))
    total_verts = sum(len(o.data.vertices) for o in meshes)
    height, width = dims_n[2], dims_n[0]
    humanoid = (height / max(width, 1e-6) > 1.6) and (total_verts >= 500) and (height > 1.2)
    evidence: dict = {
        "input": args.input,
        "normalized_dims_xyz": dims_n,
        "total_verts": total_verts,
        "height_width_ratio": height / max(width, 1e-6),
        "humanoid_gate": humanoid,
    }
    if not humanoid:
        evidence["status"] = "BLOCKED_NON_HUMANOID"
        with open(args.evidence, "w", encoding="utf-8") as f:
            json.dump(evidence, f, indent=2)
        print("[BLOCKED] mesh is not humanoid; no rig fabricated")
        sys.exit(2)
    try:
        bpy.ops.object.armature_human_metarig_add()
    except Exception as e:  # Rigify addon missing
        evidence["status"] = "BLOCKED_NO_RIGIFY"
        evidence["error"] = str(e)
        with open(args.evidence, "w", encoding="utf-8") as f:
            json.dump(evidence, f, indent=2)
        print(f"[BLOCKED] rigify unavailable: {e}")
        sys.exit(2)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=args.output)
    evidence["status"] = "RIGGED_METARIG"
    evidence["output"] = args.output
    with open(args.evidence, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)
    print("[PASS] metarig placed.")


if __name__ == "__main__":
    main()
