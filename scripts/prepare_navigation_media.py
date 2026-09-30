#!/usr/bin/env python3
"""Build course-focused web copies with timed failure highlights.

Requires ffmpeg and ffprobe on PATH. Originals in NavigationVid are preserved.
Run from any directory: python3 scripts/prepare_navigation_media.py
Rebuild a subset: python3 scripts/prepare_navigation_media.py --only full-clockwise
The supplied 5x/15x playback speed is preserved; full-clockwise loses its final 0.8s.
"""

import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import struct
import subprocess
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "static/media/NavigationVid"
VIDEOS = ROOT / "static/media/navigation"
POSTERS = ROOT / "static/images/navigation"
CLIPS = (
    ("FullSequenceClock5X.mp4", "full-clockwise", "Full-sequence", "Clockwise", 5),
    ("ForcingClock5X.mp4", "forcing-clockwise", "Diffusion Forcing", "Clockwise", 5),
    ("ReRollClock5X.mp4", "reroll-clockwise", "Diffusion ReRoll", "Clockwise", 5),
    ("FullSequenceCounter5X.mp4", "full-counterclockwise", "Full-sequence", "Counterclockwise", 5),
    ("ForcingCounter5X.mp4", "forcing-counterclockwise", "Diffusion Forcing", "Counterclockwise", 5),
    ("ReRollCounter5X.mp4", "reroll-counterclockwise", "Diffusion ReRoll", "Counterclockwise", 5),
    ("15XNavVid(ReRoll).mp4", "reroll-15x", "Diffusion ReRoll", "Example", 15),
)

# Coordinates refer to the cropped 960x372 web frame. Rings mark the failure
# locations, rather than tracking the robot after contact. Colors follow the
# updated overview: blue for clockwise and red for counterclockwise.
# Each ring remains visible until the final frame, including the shared player's
# held end frame. The forcing counterclockwise run has two separate contacts.
FAILURE_CIRCLES = {
    "full-clockwise": [(1.6, 132, 93, 46, "#315cff")],
    "forcing-clockwise": [(2.5, 190, 64, 48, "#315cff")],
    "full-counterclockwise": [(10.5, 595, 122, 47, "#ff3038")],
    "forcing-counterclockwise": [
        (8.55, 770, 161, 50, "#ff3038"),
        (11.9, 420, 177, 50, "#ff3038"),
    ],
}
TRIM_END_SECONDS = {"full-clockwise": 0.8}
RING_STROKE = 5


def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path),
    ]))


def write_ring(path, radius, color):
    """Write a small antialiased RGBA ring using only Python's standard library."""
    margin = math.ceil(radius + RING_STROKE / 2 + 1)
    size = margin * 2 + 1
    rgb = bytes.fromhex(color.lstrip("#"))
    rows = []
    for y in range(size):
        row = bytearray([0])  # PNG scanline with no filter.
        for x in range(size):
            distance = abs(math.hypot(x - margin, y - margin) - radius)
            coverage = max(0, min(1, RING_STROKE / 2 + 0.5 - distance))
            row.extend(rgb + bytes([round(255 * coverage)]))
        rows.append(row)

    def chunk(kind, data):
        return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data))

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!2I5B", size, size, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"".join(rows)))
        + chunk(b"IEND", b"")
    )
    return margin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", choices=[clip[1] for clip in CLIPS],
                        help="Rebuild selected clips, preserving other outputs and manifest entries.")
    args = parser.parse_args()
    VIDEOS.mkdir(parents=True, exist_ok=True)
    POSTERS.mkdir(parents=True, exist_ok=True)
    manifest_path = VIDEOS / "manifest.json"
    previous = {Path(entry["video"]).stem: entry for entry in json.loads(manifest_path.read_text())} if manifest_path.exists() else {}
    if args.only:
        missing = [slug for _, slug, *_ in CLIPS if slug not in args.only and slug not in previous]
        if missing:
            parser.error("First build all clips to initialize the manifest; missing: " + ", ".join(missing))
    manifest = []
    for filename, slug, method, direction, speed in CLIPS:
        if args.only and slug not in args.only:
            manifest.append(previous[slug])
            continue
        original = SOURCE / filename
        original_probe = probe(original)
        original_video = next(s for s in original_probe["streams"] if s["codec_type"] == "video")
        if (original_video["width"], original_video["height"]) != (1280, 720):
            raise ValueError(f"Recheck crop for changed source dimensions: {original}")
        # The fixed-camera course lies entirely between y=96 and y=592.
        # Keep the full width and reduce distracting foreground outside its boundary.
        # The 15x example uses a moving camera and must retain the full frame.
        crop = [0, 96, 1280, 496] if speed == 5 else None
        filters = "crop=1280:496:0:96,scale=960:372" if crop else "scale=960:540"
        trim_seconds = TRIM_END_SECONDS.get(slug, 0)
        trim_frames = Fraction(str(trim_seconds)) * Fraction(original_video["r_frame_rate"])
        if trim_frames.denominator != 1:
            raise ValueError(f"Trim must be an exact frame count: {slug}")
        expected_frames = int(original_video["nb_frames"]) - int(trim_frames)
        if expected_frames <= 0:
            raise ValueError(f"Trim exceeds the clip length: {slug}")
        if trim_frames:
            filters = f"trim=end_frame={expected_frames},setpts=PTS-STARTPTS," + filters
        circles = FAILURE_CIRCLES.get(slug, [])
        output = VIDEOS / f"{slug}.mp4"
        with tempfile.TemporaryDirectory(prefix="navigation-rings-") as temporary:
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(original)]
            if circles:
                graph = [f"[0:v:0]{filters}[base]"]
                base = "base"
                for index, (start, x, y, radius, color) in enumerate(circles):
                    ring_path = Path(temporary) / f"ring-{index}.png"
                    margin = write_ring(ring_path, radius, color)
                    command.extend(["-i", str(ring_path)])
                    result = f"marked{index}"
                    graph.append(f"[{base}][{index + 1}:v]overlay={x - margin}:{y - margin}:"
                                 f"enable='gte(t,{start})':eof_action=repeat[{result}]")
                    base = result
                command.extend(["-filter_complex_threads", "2", "-filter_complex", ";".join(graph), "-map", f"[{base}]"])
            else:
                command.extend(["-map", "0:v:0", "-vf", filters])
            command.extend([
                "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-threads", "2",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
            ])
            subprocess.run(command, check=True)
        poster = POSTERS / f"{slug}.jpg"
        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "0.2",
            "-i", str(output), "-frames:v", "1", "-q:v", "2", str(poster),
        ], check=True)
        output_probe = probe(output)
        output_video = next(s for s in output_probe["streams"] if s["codec_type"] == "video")
        # Preserve every frame except the explicitly requested endpoint trim.
        # There is no speed conversion: the 5x/15x speed is already baked in.
        if int(output_video["nb_frames"]) != expected_frames:
            raise ValueError(f"Unexpected frame count change in {output}")
        if output_video["r_frame_rate"] != original_video["r_frame_rate"]:
            raise ValueError(f"Unexpected frame rate change in {output}")
        entry = {
            "source": str(original.relative_to(ROOT)),
            "video": str(output.relative_to(ROOT)),
            "poster": str(poster.relative_to(ROOT)),
            "method": method, "direction": direction, "source_playback_speed": speed,
            "crop_xywh": crop, "width": output_video["width"], "height": output_video["height"],
            "duration_seconds": float(output_probe["format"]["duration"]),
            "frame_count": int(output_video["nb_frames"]),
            "frame_rate": output_video["r_frame_rate"],
            "size_bytes": int(output_probe["format"]["size"]),
            "audio": False,
            "trim_end_seconds": trim_seconds,
            "trim_end_frames": int(trim_frames),
            "failure_annotations": [
                {"shape": "circle", "center_xy": [x, y], "radius_pixels": radius,
                 "stroke_pixels": RING_STROKE, "color": color,
                 "start_seconds": start, "end_seconds": float(output_video["duration"])}
                for start, x, y, radius, color in circles
            ],
        }
        manifest.append(entry)
        print(f"{slug}: {entry['duration_seconds']:.3f}s; {entry['size_bytes']:,} bytes", flush=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
