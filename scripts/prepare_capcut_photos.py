"""Reusable CapCut photo preparation through ffmpeg-skill helpers."""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
MOVEMENTS = {"ZOOM_IN", "ZOOM_OUT", "PAN_LEFT_ZOOM", "PAN_RIGHT_ZOOM"}
OUTPUT_RELATIVE = Path("09_PROJECT/CAPCUT_READY/KEN_BURNS_LIBRARY")
MARKERS = ("character_card", "branding", "logo", "_ia_", "ai_gen")
BLOCKED_DIRS = {"kling", "character_cards", "ui", "interface"}


@dataclass(frozen=True)
class Decision:
    source: str
    status: str
    asset_name: str = ""
    movement: str = ""
    subject: str = ""
    crop_notes: str = ""
    notes: str = ""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Prepare CapCut photo clips via ffmpeg-skill; visual decisions stay human-owned."
    )
    parser.add_argument("--episode", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--decisions", type=Path)
    parser.add_argument("--ffmpeg-skill-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def get_source(episode, source):
    return (source or episode / "04_IMAGES").resolve()


def mechanically_excluded(path, source):
    relative = path.relative_to(source)
    if {part.lower() for part in relative.parts[:-1]} & BLOCKED_DIRS:
        return "mechanical directory exclusion"
    if any(marker in path.name.lower() for marker in MARKERS):
        return "mechanical filename exclusion"
    return ""


def discover_images(source):
    if not source.is_dir():
        raise ValueError(f"Image source does not exist: {source}")
    result = []
    for path in sorted(source.rglob("*"), key=lambda item: str(item).lower()):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            result.append((path, mechanically_excluded(path, source)))
    return result


def load_decisions(path):
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("decisions", data)
    if not isinstance(items, list):
        raise ValueError("Decisions JSON must contain a decisions list.")
    decisions = {}
    for item in items:
        decision = Decision(
            source=item["source"],
            status=item["status"].upper(),
            asset_name=item.get("asset_name", ""),
            movement=item.get("movement", "").upper(),
            subject=item.get("subject", ""),
            crop_notes=item.get("crop_notes", ""),
            notes=item.get("notes", ""),
        )
        if decision.status not in {"INCLUDE", "EXCLUDE"}:
            raise ValueError(f"{decision.source}: status must be INCLUDE or EXCLUDE.")
        if decision.status == "INCLUDE":
            if decision.movement not in MOVEMENTS:
                raise ValueError(f"{decision.source}: unsupported movement.")
            if not all((decision.asset_name, decision.subject, decision.crop_notes)):
                raise ValueError(f"{decision.source}: asset_name, subject and crop_notes are required.")
        if decision.source in decisions:
            raise ValueError(f"Duplicate decision: {decision.source}")
        decisions[decision.source] = decision
    return decisions


def safe_name(value):
    value = re.sub(r"[^A-Za-z0-9]+", "_", value.upper()).strip("_")
    if not value:
        raise ValueError("asset_name must include letters or numbers.")
    return value[:72]


def build_plan(images, source, decisions):
    rows, index = [], 1
    for path, mechanical_reason in images:
        relative = path.relative_to(source).as_posix()
        base = {"index": "", "source_image": relative, "master_clip": "", "movement": "",
                "subject": "", "crop_notes": "", "notes": ""}
        if mechanical_reason:
            rows.append({**base, "status": "SKIPPED_NON_PHOTO", "notes": mechanical_reason})
            continue
        decision = decisions.get(relative)
        if decision is None:
            rows.append({**base, "status": "PENDING_VISUAL_REVIEW",
                         "notes": "Human visual decision required."})
            continue
        if decision.status == "EXCLUDE":
            rows.append({**base, "status": "SKIPPED_BAD_CROP",
                         "notes": decision.notes or "Excluded by visual review."})
            continue
        clip = f"{index:03d}_{safe_name(decision.asset_name)}__{decision.movement}.mp4"
        rows.append({**base, "index": f"{index:03d}", "master_clip": f"01_CLIPS/{clip}",
                     "movement": decision.movement, "status": "PLANNED",
                     "subject": decision.subject, "crop_notes": decision.crop_notes,
                     "notes": decision.notes})
        index += 1
    return rows


def skill_dir(value):
    if value:
        return value.expanduser().resolve()
    if os.environ.get("FFMPEG_SKILL_DIR"):
        return Path(os.environ["FFMPEG_SKILL_DIR"]).expanduser().resolve()
    return Path.home() / ".codex/skills/ffmpeg-skill"


def run_tool(script, arguments):
    subprocess.run([sys.executable, str(script), *arguments, "--json"], check=True)


def create_structure(root):
    paths = [root / "01_CLIPS", root / "02_CONTACT_SHEETS", root / "03_MANIFEST"]
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
    return paths


def write_manifest(path, rows, duration):
    fields = ["index", "source_image", "master_clip", "movement", "duration", "resolution",
              "fps", "status", "subject", "crop_notes", "notes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({**{field: "" for field in fields}, **row,
                             "duration": f"{duration:.3f}" if row["status"] == "PLANNED" else "",
                             "resolution": "1920x1080" if row["status"] == "PLANNED" else "",
                             "fps": "30" if row["status"] == "PLANNED" else ""})


def insert_arguments(image, clip, movement, duration):
    zoom = "out" if movement == "ZOOM_OUT" else "in"
    arguments = [str(image), "--duration", str(duration), "--width", "1920",
                 "--height", "1080", "--fps", "30", "--zoom", zoom,
                 "--zoom-amount", "1.08"]
    if movement == "PAN_LEFT_ZOOM":
        arguments.extend(["--pan", "left"])
    elif movement == "PAN_RIGHT_ZOOM":
        arguments.extend(["--pan", "right"])
    return [*arguments, "-o", str(clip), "--fast"]


def execute(rows, source, clips, sheets, tools, duration):
    scripts = tools / "scripts"
    insert, probe, look = (scripts / "insert.py", scripts / "probe.py", scripts / "look.py")
    if not all(path.is_file() for path in (insert, probe, look)):
        raise ValueError(f"ffmpeg-skill scripts unavailable under {scripts}")
    for row in rows:
        if row["status"] != "PLANNED":
            continue
        image, clip = source / row["source_image"], clips / Path(row["master_clip"]).name
        run_tool(probe, [str(image)])
        run_tool(insert, insert_arguments(image, clip, row["movement"], duration))
        run_tool(probe, [str(clip)])
        run_tool(look, [str(clip), "--tiles", "3x1", "--width", "1440", "--no-timecode",
                        "-o", str(sheets / f"{clip.stem}_contact.png")])


def main(argv=None):
    args = parse_args(argv)
    if args.duration <= 0:
        raise ValueError("--duration must be positive.")
    source = get_source(args.episode.resolve(), args.source)
    rows = build_plan(discover_images(source), source, load_decisions(args.decisions))
    planned = [row for row in rows if row["status"] == "PLANNED"]
    pending = [row for row in rows if row["status"] == "PENDING_VISUAL_REVIEW"]
    if args.dry_run:
        print(f"planned_clips={len(planned)}")
        print(f"pending_visual_review={len(pending)}")
        for row in planned:
            print(f"{row['index']} {row['source_image']} -> {row['master_clip']} ({row['movement']})")
        return 0
    if args.decisions is None or pending:
        raise ValueError("A complete --decisions file is required before rendering.")
    root = args.episode.resolve() / OUTPUT_RELATIVE
    clips, sheets, manifest = create_structure(root)
    execute(rows, source, clips, sheets, skill_dir(args.ffmpeg_skill_dir), args.duration)
    write_manifest(manifest / "clips_manifest.csv", rows, args.duration)
    (manifest / "README.md").write_text(
        "CAPCUT_READY photo B-roll library. Clips are 5 s, 1920x1080, 30 fps CFR, H.264, no audio. "
        "Human visual QA of every contact sheet remains required.\n", encoding="utf-8"
    )
    print(f"prepared={root}")
    print("Visual QA remains required before approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
