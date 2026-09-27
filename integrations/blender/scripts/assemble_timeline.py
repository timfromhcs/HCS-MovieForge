"""Blender headless script: Assemble video clips, image stills, and audio track on the VSE timeline and render a 1080p master."""

import argparse
import json
import os
import sys
import bpy


def parse_args():
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        raw_args = sys.argv[idx + 1:]
    else:
        raw_args = []

    parser = argparse.ArgumentParser(description="Assemble shots on Blender VSE timeline.")
    parser.add_argument("--clips", nargs="+", help="List of video/image files in playback order")
    parser.add_argument("--clips-json", help="Path to JSON file containing list of clip objects")
    parser.add_argument("--audio", help="Optional path to audio track (.wav, .mp3, .aac)")
    parser.add_argument("--output", required=True, help="Output master video path (.mp4)")
    parser.add_argument("--width", type=int, default=1920, help="Resolution width")
    parser.add_argument("--height", type=int, default=1080, help="Resolution height")
    parser.add_argument("--fps", type=int, default=24, help="Timeline framerate")
    parser.add_argument("--seconds-per-still", type=float, default=3.0, help="Duration for still images in seconds")
    args = parser.parse_args(raw_args)
    args.output = os.path.abspath(args.output)
    if args.audio:
        args.audio = os.path.abspath(args.audio)
    return args


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def main():
    args = parse_args()
    clear_scene()

    clips = []
    if args.clips_json and os.path.exists(args.clips_json):
        with open(args.clips_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                clips = data
            elif isinstance(data, dict):
                clips = data.get("clips", [])
    elif args.clips:
        clips = [{"path": os.path.abspath(c)} for c in args.clips]

    if not clips:
        print("[FAIL] No input clips specified.")
        sys.exit(1)

    scene = bpy.context.scene
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.fps = args.fps

    seq = scene.sequence_editor_create()

    current_frame = 1
    still_duration_frames = int(args.seconds_per_still * args.fps)

    strips_coll = getattr(seq, "strips", getattr(seq, "sequences", None))

    for i, clip in enumerate(clips):
        cpath = clip.get("path") if isinstance(clip, dict) else str(clip)
        if not os.path.exists(cpath):
            print(f"[WARN] Clip not found: {cpath}, skipping.")
            continue

        ext = os.path.splitext(cpath)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"]:
            # Image strip
            strip = strips_coll.new_image(
                name=f"Still_{i+1}",
                filepath=cpath,
                channel=1,
                frame_start=current_frame,
            )
            custom_frames = clip.get("frames") if isinstance(clip, dict) else None
            duration = custom_frames if custom_frames else still_duration_frames
            strip.frame_final_duration = duration
            current_frame += duration
        else:
            # Movie strip
            strip = strips_coll.new_movie(
                name=f"Movie_{i+1}",
                filepath=cpath,
                channel=1,
                frame_start=current_frame,
            )
            current_frame += strip.frame_final_duration

    # Add audio track if provided
    if args.audio and os.path.exists(args.audio):
        strips_coll.new_sound(
            name="AudioTrack",
            filepath=args.audio,
            channel=2,
            frame_start=1,
        )

    total_frames = max(current_frame - 1, 1)
    scene.frame_start = 1
    scene.frame_end = total_frames

    # Render frame sequence
    temp_dir = os.path.join(os.path.dirname(args.output), "timeline_frames_tmp")
    os.makedirs(temp_dir, exist_ok=True)
    frame_pattern = os.path.join(temp_dir, "frame_%04d.png")

    scene.render.filepath = os.path.join(temp_dir, "frame_")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    print(f"[INFO] Rendering VSE sequence: {total_frames} frames ({total_frames / args.fps:.2f}s) to PNG frames...")
    bpy.ops.render.render(animation=True)

    # Encode with FFmpeg
    import shutil
    import subprocess
    ffmpeg_exe = shutil.which("ffmpeg") or "ffmpeg"
    ffmpeg_cmd = [
        ffmpeg_exe,
        "-y",
        "-framerate", str(args.fps),
        "-i", os.path.join(temp_dir, "frame_%04d.png"),
    ]

    if args.audio and os.path.exists(args.audio):
        ffmpeg_cmd.extend(["-i", args.audio, "-c:a", "aac", "-b:a", "192k", "-shortest"])

    ffmpeg_cmd.extend([
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(args.fps),
        args.output,
    ])

    print(f"[INFO] Encoding final 1080p MP4 master with FFmpeg: {' '.join(ffmpeg_cmd)}")
    res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

    # Clean up temporary frames
    shutil.rmtree(temp_dir, ignore_errors=True)

    if res.returncode != 0 or not os.path.exists(args.output):
        print(f"[FAIL] FFmpeg encoding failed (code {res.returncode}): {res.stderr[-500:]}")
        sys.exit(1)

    print(f"[OK] Timeline assembly & 1080p master complete: {args.output}")


if __name__ == "__main__":
    main()
