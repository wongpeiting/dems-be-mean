"""
build_quiz.py — clip encoder + quiz.json builder.

Usage (once pipeline/picks.csv exists):
    python -m pipeline.build_quiz

Reads:  pipeline/picks.csv (columns: id, account, side, caption, track, tell, ...)
Writes: static/clips/{id}.mp4  — 2.5s muted loop, watermark cropped, 480px wide
        static/clips/{id}.webm — same, VP9
        static/clips/{id}.jpg  — poster frame at 1s
        src/lib/data/quiz.json — {rounds: [...], seeded: {}}

rounds_from_picks() is a pure function (no I/O); ffmpeg encode is in encode().
"""

import csv
import json
import subprocess
from pathlib import Path

from .config import VIDEOS, OUT_STATIC, OUT_DATA, PROJECT


# ---------------------------------------------------------------------------
# Pure function — unit-tested, no ffmpeg dependency
# ---------------------------------------------------------------------------

def rounds_from_picks(picks: list[dict]) -> list[dict]:
    """Convert a list of pick dicts (from picks.csv) into quiz round dicts.

    Each output round:
        {id, answer, account, caption, sound, tell, clip, poster}

    The `tell` field is normalised: the string "true" (case-insensitive) → True,
    anything else → False.
    """
    return [
        {
            "id": p["id"],
            "answer": p["side"],
            "account": p["account"],
            "caption": p["caption"],
            "sound": p["track"],
            "tell": str(p.get("tell", "")).lower() == "true",
            "clip": f"clips/{p['id']}",
            "poster": f"clips/{p['id']}.jpg",
        }
        for p in picks
    ]


# ---------------------------------------------------------------------------
# ffmpeg encode — not unit-tested (requires real video files)
# ---------------------------------------------------------------------------

def encode(src: Path, out_dir: Path, vid: str) -> None:
    """Encode one clip to mp4 + webm + jpg poster.

    Encoding spec:
    - Start offset: 0.5s (skips title-card freeze)
    - Duration: 2.5s, silent (-an)
    - Crop: 8% from edges to shave watermark (crop=iw*0.92:ih*0.92)
    - Scale: 480px wide, height auto
    """
    vf = "crop=iw*0.92:ih*0.92,scale=480:-2"
    base = ["ffmpeg", "-y", "-ss", "0.5", "-t", "2.5", "-i", str(src), "-an", "-vf", vf]

    # H.264 mp4 (broad compatibility)
    subprocess.run(
        base + ["-c:v", "libx264", "-crf", "28", "-preset", "slow",
                "-movflags", "+faststart", str(out_dir / f"{vid}.mp4")],
        check=True,
    )

    # VP9 webm (smaller, modern browsers)
    subprocess.run(
        base + ["-c:v", "libvpx-vp9", "-crf", "42", "-b:v", "0",
                str(out_dir / f"{vid}.webm")],
        check=True,
    )

    # Poster JPEG at 1s
    subprocess.run(
        ["ffmpeg", "-y", "-ss", "1", "-i", str(src),
         "-frames:v", "1", "-vf", vf, str(out_dir / f"{vid}.jpg")],
        check=True,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    picks_path = PROJECT / "pipeline" / "picks.csv"
    if not picks_path.exists():
        raise FileNotFoundError(
            f"{picks_path} not found. "
            "Curate picks from pipeline/out/quiz_candidates.csv into pipeline/picks.csv "
            "(columns: id,account,side,caption,track,tell,...) then re-run."
        )

    picks = list(csv.DictReader(open(picks_path)))

    out_dir = OUT_STATIC / "clips"
    out_dir.mkdir(parents=True, exist_ok=True)

    for p in picks:
        src = VIDEOS / p["account"] / f"{p['id']}.mp4"
        if not src.exists():
            src = VIDEOS / p["account"] / f"{p['id']}_carousel.mp4"
        encode(src, out_dir, p["id"])

    OUT_DATA.mkdir(parents=True, exist_ok=True)
    quiz = {"rounds": rounds_from_picks(picks), "seeded": {}}
    json.dump(quiz, open(OUT_DATA / "quiz.json", "w"), indent=1)
    print(f"{len(picks)} rounds encoded → {OUT_DATA / 'quiz.json'}")


if __name__ == "__main__":
    main()
