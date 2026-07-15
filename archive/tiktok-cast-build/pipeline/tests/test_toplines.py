# pipeline/tests/test_toplines.py
import statistics
from pipeline.build_toplines import era_of, toxicity_rows


# ── era_of ──────────────────────────────────────────────────────────────────

H2H = "2025-08-19"
ELECTION = "2024-11-06"


def test_era_dem_pre():
    assert era_of("democrats", "2024-11-05", H2H) == "dem_pre"


def test_era_dem_post():
    assert era_of("democrats", "2024-11-06", H2H) == "dem_post"


def test_era_dem_post_day_before_h2h():
    assert era_of("democrats", "2025-08-18", H2H) == "dem_post"


def test_era_headtohead_dem():
    assert era_of("democrats", "2025-08-19", H2H) == "headtohead"


def test_era_rep_always_headtohead():
    for acct in ("whitehouse", "republicans"):
        assert era_of(acct, "2024-01-01", H2H) == "headtohead"
        assert era_of(acct, "2023-05-15", H2H) == "headtohead"
        assert era_of(acct, "2026-01-01", H2H) == "headtohead"


# ── toxicity_rows ────────────────────────────────────────────────────────────

def test_toxicity_basic():
    posts = [
        {"account": "whitehouse", "era": "headtohead", "views": 1000, "function": "attack"},
        {"account": "whitehouse", "era": "headtohead", "views": 500,  "function": "attack"},
        {"account": "whitehouse", "era": "headtohead", "views": 200,  "function": "promote_leader"},
    ]
    rows = toxicity_rows(posts)
    assert len(rows) == 1
    r = rows[0]
    assert r["account"] == "whitehouse"
    assert r["era"] == "headtohead"
    assert r["attackMedian"] == statistics.median([1000, 500])
    assert r["otherMedian"] == statistics.median([200])
    assert r["n"] == 3
    assert r["pending"] is True  # n < 100


def test_toxicity_pending_false_at_100():
    posts = [
        {"account": "whitehouse", "era": "headtohead", "views": i * 100, "function": "attack"}
        for i in range(1, 101)
    ]
    rows = toxicity_rows(posts)
    assert rows[0]["pending"] is False


def test_toxicity_no_attack():
    """Group with no attack posts: attackMedian should be None."""
    posts = [
        {"account": "democrats", "era": "dem_pre", "views": 300, "function": "promote_policy"},
        {"account": "democrats", "era": "dem_pre", "views": 400, "function": "mobilize"},
    ]
    rows = toxicity_rows(posts)
    assert len(rows) == 1
    assert rows[0]["attackMedian"] is None
    assert rows[0]["otherMedian"] == statistics.median([300, 400])


def test_toxicity_no_other():
    """Group with only attack posts: otherMedian should be None."""
    posts = [
        {"account": "whitehouse", "era": "headtohead", "views": 800, "function": "attack"},
    ]
    rows = toxicity_rows(posts)
    assert rows[0]["otherMedian"] is None
    assert rows[0]["attackMedian"] == 800


def test_toxicity_groups_by_account_and_era():
    posts = [
        {"account": "whitehouse", "era": "headtohead", "views": 100, "function": "attack"},
        {"account": "democrats",  "era": "dem_pre",    "views": 200, "function": "attack"},
        {"account": "whitehouse", "era": "headtohead", "views": 300, "function": "promote_leader"},
    ]
    rows = toxicity_rows(posts)
    assert len(rows) == 2
    accounts = {r["account"] for r in rows}
    assert accounts == {"whitehouse", "democrats"}
