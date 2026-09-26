"""3D Mesh and GLTF/GLB validator verifying geometry, bounds, and scene graph."""

import json
import math
import struct
from pathlib import Path
from typing import Any


class MeshValidationResult:
    def __init__(
        self,
        is_valid: bool,
        errors: list[str],
        vertex_count: int = 0,
        face_count: int = 0,
        material_count: int = 0,
        texture_count: int = 0,
        bounding_box: dict[str, list[float]] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.is_valid = is_valid
        self.errors = errors
        self.vertex_count = vertex_count
        self.face_count = face_count
        self.material_count = material_count
        self.texture_count = texture_count
        self.bounding_box = bounding_box or {}
        self.metadata = metadata or {}


def validate_glb(glb_path: Path | str, min_size_bytes: int = 1024) -> MeshValidationResult:
    """Parses binary GLB file and validates structure, geometry counts, and finite coordinates."""
    path = Path(glb_path)
    errors = []

    if not path.is_file():
        return MeshValidationResult(False, [f"GLB file does not exist: {path}"])

    size = path.stat().st_size
    if size < min_size_bytes:
        return MeshValidationResult(
            False,
            [f"GLB file size too small ({size} bytes < minimum {min_size_bytes} bytes)"]
        )

    try:
        with open(path, "rb") as f:
            header = f.read(12)
            if len(header) < 12:
                return MeshValidationResult(False, ["Invalid GLB header: truncated file."])

            magic, version, length = struct.unpack("<4sII", header)
            if magic != b"glTF":
                return MeshValidationResult(
                    False,
                    [f"Invalid GLB magic bytes: expected 'glTF', got {magic!r}"]
                )

            if version != 2:
                errors.append(f"Unexpected glTF version: {version} (expected 2)")

            if length != size:
                errors.append(f"Header length {length} does not match file size {size}")

            # Read first chunk: JSON
            chunk_header = f.read(8)
            if len(chunk_header) < 8:
                return MeshValidationResult(False, ["Truncated chunk header in GLB."])

            chunk_len, chunk_type = struct.unpack("<II", chunk_header)
            if chunk_type != 0x4E4F534A:  # ASCII for "JSON"
                return MeshValidationResult(
                    False,
                    [f"First chunk must be JSON, got chunk type 0x{chunk_type:08X}"]
                )

            json_bytes = f.read(chunk_len)
            if len(json_bytes) < chunk_len:
                return MeshValidationResult(False, ["Truncated JSON chunk in GLB."])

            gltf_json = json.loads(json_bytes.decode("utf-8"))

        # Inspect meshes and primitives
        meshes = gltf_json.get("meshes", [])
        if not meshes:
            errors.append("GLB contains no meshes.")

        accessors = gltf_json.get("accessors", [])
        materials = gltf_json.get("materials", [])
        textures = gltf_json.get("textures", [])

        total_vertices = 0
        total_faces = 0
        bbox_min = [float("inf"), float("inf"), float("inf")]
        bbox_max = [float("-inf"), float("-inf"), float("-inf")]

        for mesh in meshes:
            primitives = mesh.get("primitives", [])
            if not primitives:
                errors.append(f"Mesh '{mesh.get('name', 'unnamed')}' has no primitives.")
            for prim in primitives:
                attrs = prim.get("attributes", {})
                pos_idx = attrs.get("POSITION")
                if pos_idx is None or pos_idx >= len(accessors):
                    errors.append("Primitive missing valid POSITION accessor.")
                    continue

                pos_accessor = accessors[pos_idx]
                v_count = pos_accessor.get("count", 0)
                if v_count <= 0:
                    errors.append(f"POSITION accessor has 0 vertices.")
                total_vertices += v_count

                # Check bounding coordinates min/max
                a_min = pos_accessor.get("min")
                a_max = pos_accessor.get("max")
                if not a_min or not a_max:
                    errors.append("POSITION accessor missing min/max bounding coordinates.")
                else:
                    for val in a_min + a_max:
                        if math.isnan(val) or math.isinf(val):
                            errors.append(f"Detected NaN or Inf in vertex coordinates: {val}")

                    for i in range(3):
                        if i < len(a_min) and i < len(a_max):
                            bbox_min[i] = min(bbox_min[i], a_min[i])
                            bbox_max[i] = max(bbox_max[i], a_max[i])

                indices_idx = prim.get("indices")
                if indices_idx is not None and indices_idx < len(accessors):
                    idx_accessor = accessors[indices_idx]
                    idx_count = idx_accessor.get("count", 0)
                    total_faces += idx_count // 3
                else:
                    total_faces += v_count // 3

                # Material index validation
                mat_idx = prim.get("material")
                if mat_idx is not None and mat_idx >= len(materials):
                    errors.append(f"Primitive references non-existent material index {mat_idx}.")

        if total_vertices == 0:
            errors.append("Mesh has zero total vertices.")

        bbox = {
            "min": bbox_min if bbox_min[0] != float("inf") else [0.0, 0.0, 0.0],
            "max": bbox_max if bbox_max[0] != float("-inf") else [0.0, 0.0, 0.0],
        }

        return MeshValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            vertex_count=total_vertices,
            face_count=total_faces,
            material_count=len(materials),
            texture_count=len(textures),
            bounding_box=bbox,
            metadata={"gltf_version": version, "file_size": size},
        )
    except Exception as e:
        return MeshValidationResult(
            is_valid=False,
            errors=[f"Failed to parse GLB: {e}"]
        )
