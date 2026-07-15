import csv, json, re, sys
from pathlib import Path
from .config import CLUSTER_CSV, DATA, DESC, OUT_WORK, ALL_ACCOUNTS, side_of

ABSURD = re.compile(r"absurd|surreal", re.I)
TEXT_FIELDS = ("central_claim", "intended_effect", "visual_action", "manipulation_or_satire")
FIELDNAMES = ["id", "account", "side", "upload_date", "view_count", "caption", "track", "central_claim", "source", "url"]

def _build_meta_lookup(posts_dir: Path) -> dict:
    """Build a dict keyed by string video id from all 6 account posts CSVs."""
    lookup = {}
    for account in ALL_ACCOUNTS:
        posts_csv = posts_dir / f"{account}_posts.csv"
        if not posts_csv.exists():
            continue
        with open(posts_csv, newline="") as f:
            for r in csv.DictReader(f):
                vid = str(r.get("id", "")).strip()
                if not vid:
                    continue
                lookup[vid] = {
                    "id": vid,
                    "account": account,
                    "side": side_of(account),
                    "upload_date": r.get("upload_date", ""),
                    "view_count": r.get("view_count", ""),
                    "caption": r.get("title", ""),
                    "track": r.get("track", ""),
                }
    return lookup

def build_candidates(
    cluster_csv: Path,
    desc_dir: Path,
    must_include: Path = None,
    posts_dir: Path = None,
) -> list[dict]:
    """
    Build candidate rows from cluster CSV, absurd descriptions, and must-include list.

    source values: cluster34 | absurd | both | manual, with +manual suffix when a must-include id
    also matched another source.
    """
    if posts_dir is None:
        posts_dir = DATA

    # Build metadata fallback from upstream posts CSVs
    meta_lookup = _build_meta_lookup(posts_dir)

    rows = {}
    with open(cluster_csv, newline="") as f:
        for r in csv.DictReader(f):
            if r["account"] not in ALL_ACCOUNTS: continue
            base = dict(id=r["id"], account=r["account"], side=side_of(r["account"]),
                        upload_date=r["upload_date"], view_count=r["view_count"],
                        caption=r["title"], track=r["track"], central_claim="", source="", url="")
            if r["cluster"] == "34":
                base["source"] = "cluster34"; rows[r["id"]] = base
            rows.setdefault(r["id"], base)  # keep metadata for absurd joins

    for account in ALL_ACCOUNTS:
        for f in (desc_dir / account).glob("*.json"):
            d = json.loads(f.read_text())
            text = " ".join(str(d.get(k, "")) for k in TEXT_FIELDS)
            if ABSURD.search(text):
                vid = str(d.get("video_id", f.stem))
                if vid in rows:
                    rows[vid]["source"] = "both" if rows[vid]["source"] == "cluster34" else "absurd"
                    rows[vid]["central_claim"] = d.get("central_claim", "")
                elif vid in meta_lookup:
                    # Absurd-flagged video not in cluster CSV — build from meta_lookup
                    meta = meta_lookup[vid]
                    rows[vid] = dict(
                        id=vid,
                        account=meta["account"],
                        side=meta["side"],
                        upload_date=meta["upload_date"],
                        view_count=meta["view_count"],
                        caption=meta["caption"],
                        track=meta["track"],
                        central_claim=d.get("central_claim", ""),
                        source="absurd",
                        url="",
                    )
                # else: not in cluster or meta_lookup — skip

    # Must-include
    if must_include is not None and must_include.exists():
        for line in must_include.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            vid = line
            if vid in rows:
                src = rows[vid]["source"]
                if not src.endswith("+manual"):
                    rows[vid]["source"] = (src + "+manual") if src else "manual"
            elif vid in meta_lookup:
                meta = meta_lookup[vid]
                rows[vid] = dict(
                    id=vid,
                    account=meta["account"],
                    side=meta["side"],
                    upload_date=meta["upload_date"],
                    view_count=meta["view_count"],
                    caption=meta["caption"],
                    track=meta["track"],
                    central_claim="",
                    source="manual",
                    url="",
                )
            else:
                print(f"WARNING: must-include id {vid!r} not found in meta_lookup — skipping", file=sys.stderr)

    return [r for r in rows.values() if r["source"]]

def main():
    OUT_WORK.mkdir(parents=True, exist_ok=True)
    rows = build_candidates(
        CLUSTER_CSV,
        DESC,
        must_include=Path(__file__).parent / "must_include.txt",
        posts_dir=DATA,
    )
    if not rows:
        raise SystemExit("No candidates found — check upstream paths in pipeline/config.py")
    for r in rows:
        r["url"] = f"https://www.tiktok.com/@{r['account']}/video/{r['id']}"
    out = OUT_WORK / "quiz_candidates.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} candidates -> {out}")

if __name__ == "__main__":
    main()
