"""pipeline/build_interior.py

Builds per-subject interior layout data and thumbnail atlases for the
BalloonInterior canvas scene.

Usage:
    pipeline/.venv/bin/python -m pipeline.build_interior

Outputs (for Donald Trump):
    src/lib/data/interior/donald-trump.json
    static/atlas/donald-trump_0.jpg
    static/atlas/donald-trump_1.jpg
    ...
"""

import json
import math
import random
import subprocess
import tempfile
import concurrent.futures
from collections import Counter
from pathlib import Path

from PIL import Image

from .config import (
    DESC, VIDEOS, OUT_DATA, OUT_STATIC,
    ALL_ACCOUNTS, side_of, canonical_name, slugify, emotion_bucket,
)
from .build_balloons import load_stage2, post_meta, iter_posts, to_iso

# ── Atlas constants ────────────────────────────────────────────────────────────
THUMB = 96          # px per side
COLS = 16           # thumbnails per row
MAX_PER_SHEET = 256  # thumbnails per atlas JPEG
ATLAS_QUALITY = 72  # JPEG quality

# ── Subject to build ───────────────────────────────────────────────────────────
TARGET = "Donald Trump"


# ── Core logic ─────────────────────────────────────────────────────────────────

def load_dunks():
    """{video_id: dunk_line} from function_*.jsonl rows with has_dunk=True."""
    from .config import CLS
    dunks = {}
    for f in CLS.glob("function_*.jsonl"):
        for line in open(f, encoding="utf-8"):
            d = json.loads(line)
            if d.get("has_dunk"):
                dunks[str(d["video_id"])] = d.get("dunk_line", "")
    return dunks


def collect(posts, meta, s2, subject, dunk_map=None):
    """Build node list for *subject* from stage-1 posts + stage-2 data.

    Args:
        posts:    iterable of stage-1 post dicts (video_id, account, upload_date,
                  cast, emotions_signaled, central_claim, intended_effect, ...)
        meta:     {vid_str: (view_count_int, upload_date_str)}
        s2:       {(vid_str, canonical_subject_str): register_float_or_int}
        subject:  canonical name to filter on (e.g. "Donald Trump")
        dunk_map: optional {vid_str: dunk_line_str}

    Returns:
        List of node dicts, one per post where *subject* is main cast.
        Keys: id, account, side, date, views, emotion, color, register,
              claim, intent, dunk.
        (x, y added by layout(); ai, ax, ay added after atlases())
    """
    nodes = []
    for d in posts:
        cast = d.get("cast", [])
        # Check if subject appears as main cast
        is_main = any(
            canonical_name(c.get("name", "")) == subject and c.get("is_main")
            for c in cast
        )
        if not is_main:
            continue

        vid = str(d.get("video_id", ""))
        account = d.get("account", "")

        # Emotion: use first mapped emotion from emotions_signaled list
        emotions = d.get("emotions_signaled", [])
        bucket, color = ("Other", "#8d99ae")
        for e in emotions:
            b, c = emotion_bucket(e)
            if b != "Other":
                bucket, color = b, c
                break
        else:
            # All resolved to Other — use the first one's result
            if emotions:
                bucket, color = emotion_bucket(emotions[0])

        views, upload_date_raw = meta.get(vid, (0, d.get("upload_date", "")))

        register = s2.get((vid, subject))

        nodes.append({
            "id": vid,
            "account": account,
            "side": side_of(account),
            "date": to_iso(upload_date_raw),
            "views": views,
            "emotion": bucket,
            "color": color,
            "register": register,
            "claim": d.get("central_claim", ""),
            "intent": d.get("intended_effect", ""),
            "dunk": (dunk_map or {}).get(vid, ""),
        })

    return nodes


def layout(nodes):
    """Golden-angle ring of emotion-cluster centers + seeded jitter blob per cluster."""
    emotions = sorted({n["emotion"] for n in nodes})
    centers = {}
    for i, e in enumerate(emotions):
        a = i * 2.39996; r = 0.30
        centers[e] = (0.5 + r * math.cos(a), 0.5 + r * math.sin(a))
    rng = random.Random(34)
    out = []
    for n in sorted(nodes, key=lambda n: n["id"]):
        cx, cy = centers[n["emotion"]]
        rad = 0.16 * math.sqrt(rng.random()); ang = rng.random() * 6.28318
        out.append({**n, "x": round(min(1, max(0, cx + rad * math.cos(ang))), 4),
                         "y": round(min(1, max(0, cy + rad * math.sin(ang))), 4)})
    return out


def _default_ffmpeg(vid, account, tmpf):
    """Extract mid-point frame from video as JPEG to tmpf.

    Returns True on success, False on failure.
    """
    video_path = VIDEOS / account / f"{vid}.mp4"
    if not video_path.exists():
        return False

    try:
        # Get duration
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            capture_output=True, text=True, timeout=15
        )
        duration = float(probe.stdout.strip() or "10")
        mid = duration / 2

        result = subprocess.run(
            ["ffmpeg", "-y", "-ss", str(mid), "-i", str(video_path),
             "-vframes", "1", "-vf", f"scale={THUMB}:{THUMB}:force_original_aspect_ratio=increase,crop={THUMB}:{THUMB}",
             "-q:v", "2", str(tmpf)],
            capture_output=True, timeout=30
        )
        return result.returncode == 0 and Path(tmpf).exists()
    except Exception:
        return False


def atlases(nodes, out_dir, ffmpeg_fn=None):
    """Extract thumbnail frames and pack them into atlas sheets.

    Args:
        nodes:     list of node dicts (must have id, account keys)
        out_dir:   Path where atlas JPEGs will be written
        ffmpeg_fn: optional callable(vid, account, tmpf) -> bool, for testing

    Returns:
        (sheet_paths, nodes, skips) where nodes have 'atlas' and 'idx'
        keys added, and skips is the count of nodes with no extractable frame.
    """
    if ffmpeg_fn is None:
        ffmpeg_fn = _default_ffmpeg

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    n = len(nodes)
    # Map node index -> temp file path
    tmpdir = Path(tempfile.mkdtemp())
    tmp_paths = {i: tmpdir / f"_f_{nodes[i]['id']}.jpg" for i in range(n)}

    skips = 0
    ok_flags = [False] * n

    def extract_one(i):
        node = nodes[i]
        success = ffmpeg_fn(node["id"], node["account"], tmp_paths[i])
        return i, success

    # Parallel extraction
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(extract_one, i): i for i in range(n)}
        done_count = 0
        for future in concurrent.futures.as_completed(futures):
            i, success = future.result()
            ok_flags[i] = success
            done_count += 1
            if done_count % 100 == 0:
                print(f"  frame extraction: {done_count}/{n} done")

    # Remove failed nodes from the active list
    active = [i for i in range(n) if ok_flags[i]]
    skips = n - len(active)

    # Build sheets from active nodes
    sheet_paths = []
    # Assign atlas/idx before building (so updated_nodes reflects order)
    for sheet_num, sheet_start in enumerate(range(0, len(active), MAX_PER_SHEET)):
        sheet_indices = active[sheet_start: sheet_start + MAX_PER_SHEET]
        count = len(sheet_indices)
        rows = math.ceil(count / COLS)
        sheet_w = COLS * THUMB
        sheet_h = rows * THUMB
        sheet = Image.new("RGB", (sheet_w, sheet_h), (0, 0, 0))

        for pos, node_idx in enumerate(sheet_indices):
            nodes[node_idx]["atlas"] = sheet_num
            nodes[node_idx]["idx"] = pos

            row = pos // COLS
            col = pos % COLS
            try:
                thumb = Image.open(tmp_paths[node_idx]).convert("RGB")
                thumb = thumb.resize((THUMB, THUMB), Image.LANCZOS)
                sheet.paste(thumb, (col * THUMB, row * THUMB))
            except Exception:
                pass  # leave black square

            if (pos + 1) % 100 == 0:
                print(f"  sheet {sheet_num}: pasted {pos+1}/{count} frames")

        slug = slugify(TARGET)
        sheet_path = out_dir / f"{slug}_{sheet_num}.jpg"
        sheet.save(sheet_path, "JPEG", quality=ATLAS_QUALITY)
        sheet_paths.append(sheet_path)
        print(f"  atlas sheet {sheet_num}: {count} thumbs -> {sheet_path}")

    # Clean up temp files
    for tmpf in tmp_paths.values():
        try:
            tmpf.unlink(missing_ok=True)
        except Exception:
            pass
    try:
        tmpdir.rmdir()
    except Exception:
        pass

    return sheet_paths, nodes, skips


def main():
    print(f"Building interior for: {TARGET}")
    print("Loading metadata...")
    meta = post_meta()
    print(f"  {len(meta)} posts in meta")

    print("Loading stage-2 classifications...")
    s2 = load_stage2()
    print(f"  {len(s2)} stage-2 entries")

    print("Loading dunks...")
    dunk_map = load_dunks()
    print(f"  {len(dunk_map)} dunk entries")

    print("Collecting nodes...")
    posts = list(iter_posts(meta))
    nodes = layout(collect(posts, meta, s2, TARGET, dunk_map=dunk_map))
    print(f"  {len(nodes)} nodes for {TARGET}")

    # Build atlases
    print("Building thumbnail atlases...")
    atlas_dir = OUT_STATIC / "atlas"
    sheet_paths, nodes, skips = atlases(nodes, atlas_dir)
    print(f"  Skipped {skips} nodes (missing video or ffmpeg failure)")

    n_sheets = len(sheet_paths)
    total_bytes = sum(p.stat().st_size for p in sheet_paths)
    print(f"  {n_sheets} sheets, {total_bytes:,} bytes total")

    # Write JSON
    out_interior = OUT_DATA / "interior"
    out_interior.mkdir(parents=True, exist_ok=True)

    slug = slugify(TARGET)
    out_json = out_interior / f"{slug}.json"

    # Only include nodes that got atlas placement (have atlas key)
    placed_nodes = [n for n in nodes if "atlas" in n]

    # Annotate ai/ax/ay from atlas/idx, then strip atlas/idx
    for n in placed_nodes:
        ai = n.pop("atlas")
        idx = n.pop("idx")
        n["ai"] = ai
        n["ax"] = (idx % COLS) * THUMB
        n["ay"] = (idx // COLS) * THUMB

    # Emotion distribution — computed from placed nodes only
    emotion_counts = Counter(n["emotion"] for n in placed_nodes)
    print("Emotion distribution (placed nodes):")
    for emotion, count in sorted(emotion_counts.items(), key=lambda x: -x[1]):
        print(f"  {emotion}: {count}")

    output = {
        "slug": slug,
        "thumb": THUMB,
        "cols": COLS,
        "atlases": [f"atlas/{slug}_{i}.jpg" for i in range(n_sheets)],
        "nodes": placed_nodes,
    }

    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(output, fh, separators=(",", ":"))

    print(f"\nWrote {out_json}")
    print(f"  nodes: {len(placed_nodes)}")
    print(f"  emotions: {dict(emotion_counts)}")
    print(f"  sheets: {n_sheets}")
    print(f"  skips: {skips}")
    print(f"  atlas bytes: {total_bytes:,}")


if __name__ == "__main__":
    main()
