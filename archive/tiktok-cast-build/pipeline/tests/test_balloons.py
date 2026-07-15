# pipeline/tests/test_balloons.py
from pipeline.build_balloons import aggregate, to_iso

def desc(vid, account, names_main):
    return {"video_id": vid, "account": account, "upload_date": "2025-01-06",
            "cast": [{"name": n, "is_main": True} for n in names_main]}

def test_aggregate_counts_and_sides():
    posts = [desc("1", "democrats", ["Trump"]),          # opp air for Trump
             desc("2", "whitehouse", ["Donald Trump"]),  # own air (alias resolves)
             desc("3", "whitehouse", ["Donald Trump"])]
    out, _ = aggregate(posts, stage2={})
    trump = next(p for p in out["people"] if p["slug"] == "donald-trump")
    assert trump["totals"] == {"posts": 3, "own": 2, "opp": 1,
                               "oppShare": 1/3, "ownRegister": None, "oppRegister": None}
    assert trump["weekly"] == [{"w": "2025-01-06", "own": 2, "opp": 1}]
    assert out["stage2"] == "partial"

def test_stage2_registers_enrich():
    posts = [desc("2", "whitehouse", ["Donald Trump"])]
    s2 = {("2", "Donald Trump"): -3}
    out, _ = aggregate(posts, stage2=s2)
    trump = out["people"][0]
    assert trump["totals"]["ownRegister"] == -3
    assert out["stage2"] == "full"

def test_to_iso_compact():
    assert to_iso("20260702") == "2026-07-02"

def test_to_iso_already_iso():
    assert to_iso("2026-07-02") == "2026-07-02"

def test_to_iso_empty():
    assert to_iso("") == ""
