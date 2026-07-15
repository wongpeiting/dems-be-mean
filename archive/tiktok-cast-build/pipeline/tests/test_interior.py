# pipeline/tests/test_interior.py
import json, math, tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

from pipeline.build_interior import collect, atlases, layout, THUMB, COLS, MAX_PER_SHEET


def _make_posts(n=3):
    """Minimal stage-1 post dicts with Trump as main cast."""
    posts = []
    for i in range(n):
        posts.append({
            "video_id": str(1000 + i),
            "account": "whitehouse",
            "upload_date": "2025-01-06",
            "cast": [{"name": "Donald Trump", "is_main": True}],
            "emotions_signaled": ["Pride", "Strength"],
            "central_claim": "Test claim",
            "intended_effect": "Test effect",
        })
    return posts


def _make_meta(posts):
    """post_meta() stub — {vid: (views, date)}."""
    return {str(p["video_id"]): (10000 * (i + 1), p["upload_date"])
            for i, p in enumerate(posts)}


def _make_s2(posts):
    """load_stage2() stub — a couple of nodes get register values."""
    return {("1000", "Donald Trump"): -3, ("1001", "Donald Trump"): 2}


def test_collect_returns_nodes():
    posts = _make_posts(3)
    meta = _make_meta(posts)
    s2 = _make_s2(posts)
    nodes = collect(posts, meta, s2, "Donald Trump")

    assert len(nodes) == 3
    required = {"id", "account", "side", "date", "views",
                "emotion", "color", "register", "claim", "intent", "dunk"}
    for n in nodes:
        assert required <= set(n.keys()), f"missing keys: {required - set(n.keys())}"


def test_collect_fields_correct():
    posts = _make_posts(3)
    meta = _make_meta(posts)
    s2 = _make_s2(posts)
    nodes = collect(posts, meta, s2, "Donald Trump")

    n0 = next(n for n in nodes if n["id"] == "1000")
    assert n0["account"] == "whitehouse"
    assert n0["side"] == "rep"
    assert n0["date"] == "2025-01-06"
    assert n0["views"] == 10000
    assert n0["emotion"] == "Pride"
    assert n0["color"].startswith("#")
    assert n0["register"] == -3
    assert n0["claim"] == "Test claim"
    assert n0["intent"] == "Test effect"
    assert n0["dunk"] == ""

    n2 = next(n for n in nodes if n["id"] == "1002")
    assert n2["register"] is None


def test_collect_skips_non_trump():
    """Posts where Trump is NOT main cast must not produce nodes."""
    posts = [
        {"video_id": "999", "account": "democrats", "upload_date": "2025-01-06",
         "cast": [{"name": "Kamala Harris", "is_main": True}],
         "emotions_signaled": ["hope"],
         "central_claim": "", "intended_effect": ""},
    ]
    meta = {"999": (500, "2025-01-06")}
    nodes = collect(posts, meta, {}, "Donald Trump")
    assert nodes == []


def test_collect_dunk_map():
    """Nodes get dunk_line from dunk_map when present."""
    posts = _make_posts(2)
    meta = _make_meta(posts)
    dunk_map = {"1000": "Next..."}
    nodes = collect(posts, meta, {}, "Donald Trump", dunk_map=dunk_map)
    n0 = next(n for n in nodes if n["id"] == "1000")
    n1 = next(n for n in nodes if n["id"] == "1001")
    assert n0["dunk"] == "Next..."
    assert n1["dunk"] == ""


def _make_atlas_nodes(n=3):
    """Node dicts in the shape collect() produces, for atlases() tests."""
    return [
        {
            "id": str(i), "account": "whitehouse", "side": "rep",
            "date": "2025-01-06", "views": 1000,
            "emotion": "Pride", "color": "#e4572e", "register": None,
            "claim": "Test claim", "intent": "Test effect", "dunk": "",
        }
        for i in range(n)
    ]


def test_atlases_creates_sheets(tmp_path):
    """atlases() should produce ceil(n/MAX_PER_SHEET) JPEGs with correct width."""
    nodes = _make_atlas_nodes(3)

    out_atlas = tmp_path / "atlas"
    out_atlas.mkdir()

    # Stub: ffmpeg writes a solid-color JPEG to the temp path
    def fake_ffmpeg(vid, account, tmpf):
        img = Image.new("RGB", (96, 96), color=(200, 100, 50))
        img.save(tmpf, "JPEG", quality=72)
        return True

    sheet_paths, updated, skips = atlases(nodes, out_atlas, ffmpeg_fn=fake_ffmpeg)

    assert skips == 0
    assert len(sheet_paths) == math.ceil(len(nodes) / MAX_PER_SHEET)
    # Every node should have atlas + idx keys added
    for n in updated:
        assert "atlas" in n
        assert "idx" in n

    # Each sheet should be a valid image of width COLS*THUMB
    for sp in sheet_paths:
        img = Image.open(sp)
        assert img.width == COLS * THUMB
        # height should be ceil(count_in_sheet / COLS) * THUMB
        assert img.height > 0


def test_atlases_max_per_sheet(tmp_path):
    """When nodes > MAX_PER_SHEET, multiple sheets are created."""
    n_nodes = MAX_PER_SHEET + 1
    nodes = [
        {
            "id": str(i), "account": "whitehouse", "side": "rep",
            "date": "2025-01-06", "views": 1,
            "emotion": "Hype", "color": "#2a9d8f", "register": None,
            "claim": "", "intent": "", "dunk": "",
        }
        for i in range(n_nodes)
    ]

    out_atlas = tmp_path / "atlas"
    out_atlas.mkdir()

    def fake_ffmpeg(vid, account, tmpf):
        img = Image.new("RGB", (96, 96), color=(50, 100, 200))
        img.save(tmpf, "JPEG", quality=72)
        return True

    sheet_paths, updated, skips = atlases(nodes, out_atlas, ffmpeg_fn=fake_ffmpeg)
    assert skips == 0
    assert len(sheet_paths) == 2
    assert updated[0]["atlas"] == 0
    assert updated[MAX_PER_SHEET]["atlas"] == 1


def test_layout_clusters_by_emotion_and_is_deterministic():
    nodes = [{"id": str(i), "emotion": "Pride" if i < 5 else "Anger"} for i in range(10)]
    a, b = layout(list(nodes)), layout(list(nodes))
    assert a == b                                    # deterministic (seeded)
    assert all(0 <= n["x"] <= 1 and 0 <= n["y"] <= 1 for n in a)
    import statistics
    pride = [n["x"] for n in a if n["emotion"] == "Pride"]
    anger = [n["x"] for n in a if n["emotion"] == "Anger"]
    assert abs(statistics.mean(pride) - statistics.mean(anger)) > 0.15  # separated clusters


def test_node_contract(tmp_path):
    """Final node dict (after atlas annotation) must have exactly the 16-key contract."""
    posts = _make_posts(2)
    meta = _make_meta(posts)
    s2 = _make_s2(posts)

    # collect -> layout -> atlases -> annotate ai/ax/ay
    raw_nodes = collect(posts, meta, s2, "Donald Trump")
    laid_out = layout(raw_nodes)

    out_atlas = tmp_path / "atlas"
    out_atlas.mkdir()

    def fake_ffmpeg(vid, account, tmpf):
        img = Image.new("RGB", (96, 96), color=(200, 100, 50))
        img.save(tmpf, "JPEG", quality=72)
        return True

    sheet_paths, updated_nodes, skips = atlases(laid_out, out_atlas, ffmpeg_fn=fake_ffmpeg)
    assert skips == 0

    placed = [n for n in updated_nodes if "atlas" in n]
    for n in placed:
        ai = n.pop("atlas")
        idx = n.pop("idx")
        n["ai"] = ai
        n["ax"] = (idx % COLS) * THUMB
        n["ay"] = (idx // COLS) * THUMB

    EXPECTED_KEYS = sorted(['id', 'x', 'y', 'emotion', 'color', 'account', 'side',
                            'ai', 'ax', 'ay', 'claim', 'intent', 'register',
                            'dunk', 'date', 'views'])
    for n in placed:
        assert sorted(n.keys()) == EXPECTED_KEYS, (
            f"key mismatch: got {sorted(n.keys())}, want {EXPECTED_KEYS}"
        )
        assert len(n["date"]) == 10, f"date not ISO: {n['date']!r}"
