import json
from pipeline.curate_quiz import build_candidates

POSTS_HEADER = "id,account,url,title,description,upload_date,duration,view_count,like_count,comment_count,repost_count,tags,track,track_artist,is_photo_carousel,transcript\n"

def test_build_candidates_merges_sources(tmp_path):
    cluster = tmp_path / "cluster.csv"
    cluster.write_text(
        "id,account,x,y,cluster,title,description,upload_date,view_count,like_count,comment_count,track,post_type,is_restricted,transcript\n"
        "111,democrats,0,0,34,cap A,,2025-01-01,100,1,1,song A,video,False,\n"
        "222,whitehouse,0,0,12,cap B,,2025-01-02,200,1,1,song B,video,False,\n")
    desc = tmp_path / "desc" / "whitehouse"; desc.mkdir(parents=True)
    (desc / "222.json").write_text(json.dumps({
        "video_id": "222", "central_claim": "An absurd spectacle of X.",
        "intended_effect": "mock", "visual_action": ""}))
    (tmp_path / "desc" / "democrats").mkdir()
    rows = build_candidates(cluster, tmp_path / "desc", posts_dir=tmp_path)
    by_id = {r["id"]: r for r in rows}
    assert by_id["111"]["source"] == "cluster34"
    assert by_id["222"]["source"] == "absurd"
    assert by_id["111"]["side"] == "dem" and by_id["222"]["side"] == "rep"


def test_absurd_fallback_from_posts_csv(tmp_path):
    """Absurd-flagged video not in cluster CSV but present in posts CSV appears in output."""
    # Cluster CSV has only id "111"
    cluster = tmp_path / "cluster.csv"
    cluster.write_text(
        "id,account,x,y,cluster,title,description,upload_date,view_count,like_count,comment_count,track,post_type,is_restricted,transcript\n"
        "111,democrats,0,0,34,cap A,,2025-01-01,100,1,1,song A,video,False,\n"
    )

    # Posts CSV fixture for whitehouse with id "333"
    posts_csv = tmp_path / "whitehouse_posts.csv"
    posts_csv.write_text(
        POSTS_HEADER +
        "333,whitehouse,https://www.tiktok.com/@whitehouse/video/333,Cap W,,20250103,30,500,10,2,1,,track W,artist W,False,\n"
    )

    # Desc dir: "333.json" under whitehouse with absurd text
    desc = tmp_path / "desc" / "whitehouse"
    desc.mkdir(parents=True)
    (desc / "333.json").write_text(json.dumps({
        "video_id": "333",
        "central_claim": "An absurd stunt by the president.",
        "intended_effect": "mock",
        "visual_action": "",
        "manipulation_or_satire": "",
    }))
    (tmp_path / "desc" / "democrats").mkdir(parents=True)

    rows = build_candidates(cluster, tmp_path / "desc", posts_dir=tmp_path)
    by_id = {r["id"]: r for r in rows}

    assert "333" in by_id, "id 333 should appear via absurd fallback"
    assert by_id["333"]["source"] == "absurd"
    assert by_id["333"]["account"] == "whitehouse"


def test_must_include_adds_manual_row(tmp_path):
    """A must_include id not in cluster CSV but in posts CSV appears with source='manual'."""
    # Cluster CSV has id "111" only
    cluster = tmp_path / "cluster.csv"
    cluster.write_text(
        "id,account,x,y,cluster,title,description,upload_date,view_count,like_count,comment_count,track,post_type,is_restricted,transcript\n"
        "111,democrats,0,0,34,cap A,,2025-01-01,100,1,1,song A,video,False,\n"
    )

    # Posts CSV fixture for democrats with id "999"
    posts_csv = tmp_path / "democrats_posts.csv"
    posts_csv.write_text(
        POSTS_HEADER +
        "999,democrats,https://www.tiktok.com/@democrats/video/999,Cap D,,20250105,60,800,20,3,2,,track D,artist D,False,\n"
    )

    # Desc dir: no absurd hits
    desc = tmp_path / "desc" / "democrats"
    desc.mkdir(parents=True)

    # must_include.txt with id "999"
    must_include = tmp_path / "must_include.txt"
    must_include.write_text("# comment\n999\n")

    rows = build_candidates(
        cluster,
        tmp_path / "desc",
        must_include=must_include,
        posts_dir=tmp_path,
    )
    by_id = {r["id"]: r for r in rows}

    assert "999" in by_id, "id 999 should appear via must_include"
    assert by_id["999"]["source"] == "manual"
    assert by_id["999"]["account"] == "democrats"
