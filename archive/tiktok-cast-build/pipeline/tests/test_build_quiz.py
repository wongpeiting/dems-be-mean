"""
Tests for pipeline.build_quiz.rounds_from_picks().

ffmpeg encoding is NOT tested here — it requires real video files and
a working ffmpeg installation. These tests cover only the pure data
transformation: CSV row dicts → quiz round dicts.
"""

import pytest
from pipeline.build_quiz import rounds_from_picks


def test_rounds_from_picks_basic():
    picks = [
        {
            "id": "111",
            "account": "democrats",
            "side": "dem",
            "caption": "so real",
            "track": "Creep",
            "tell": "true",
            "upload_date": "2025-01-01",
            "view_count": "9",
            "central_claim": "",
            "source": "absurd",
            "url": "",
        }
    ]
    rounds = rounds_from_picks(picks)
    assert len(rounds) == 1
    r = rounds[0]
    assert r == {
        "id": "111",
        "answer": "dem",
        "account": "democrats",
        "caption": "so real",
        "sound": "Creep",
        "tell": True,
        "clip": "clips/111",
        "poster": "clips/111.jpg",
    }


def test_rounds_from_picks_tell_false_when_missing():
    picks = [
        {
            "id": "222",
            "account": "whitehouse",
            "side": "rep",
            "caption": "caption",
            "track": "",
            "tell": "",
        }
    ]
    rounds = rounds_from_picks(picks)
    assert rounds[0]["tell"] is False


def test_rounds_from_picks_tell_case_insensitive():
    for val in ("True", "TRUE", "true"):
        picks = [{"id": "1", "account": "democrats", "side": "dem",
                  "caption": "", "track": "", "tell": val}]
        assert rounds_from_picks(picks)[0]["tell"] is True

    for val in ("false", "False", "0", "no", ""):
        picks = [{"id": "1", "account": "democrats", "side": "dem",
                  "caption": "", "track": "", "tell": val}]
        assert rounds_from_picks(picks)[0]["tell"] is False


def test_rounds_from_picks_clip_and_poster_paths():
    picks = [
        {"id": "9876543210", "account": "republicans", "side": "rep",
         "caption": "", "track": "", "tell": "false"}
    ]
    r = rounds_from_picks(picks)[0]
    assert r["clip"] == "clips/9876543210"
    assert r["poster"] == "clips/9876543210.jpg"


def test_rounds_from_picks_multiple_preserves_order():
    picks = [
        {"id": "aaa", "account": "democrats", "side": "dem", "caption": "A", "track": "T1", "tell": "true"},
        {"id": "bbb", "account": "whitehouse", "side": "rep", "caption": "B", "track": "T2", "tell": "false"},
        {"id": "ccc", "account": "democrats", "side": "dem", "caption": "C", "track": "T3", "tell": "true"},
    ]
    rounds = rounds_from_picks(picks)
    assert [r["id"] for r in rounds] == ["aaa", "bbb", "ccc"]
    assert rounds[1]["answer"] == "rep"
