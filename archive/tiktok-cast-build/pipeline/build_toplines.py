"""build_toplines.py — produce src/lib/data/toplines.json.

Toplines keys:
  eras            — per era (dem_pre / dem_post / headtohead) per side:
                    post counts and date ranges from the 6 posts CSVs
  profanityByMonth — list of {m, dem, rep} where value = share of that
                    side's posts in that month that had ≥1 profanity hit;
                    null for sides with 0 posts that month
  toxicityPays    — rows built by joining function_*.jsonl with post_meta()
                    views and era_of(); pending:true when n < 100
  moderation      — {restricted, deleted, total}

Re-run when full stage-2 data lands:
  python -m pipeline.build_balloons
  python -m pipeline.build_interior
  python -m pipeline.build_toplines
"""

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

from .config import (
    ALL_ACCOUNTS, CLS, CLUSTER_CSV, DATA, DEM_ACCOUNTS, ELECTION,
    OUT_DATA, REP_ACCOUNTS, side_of,
)
from .build_balloons import post_meta, to_iso


# ── era helpers ──────────────────────────────────────────────────────────────

def era_of(account: str, iso_date: str, h2h_start: str) -> str:
    """Return era label for a post.

    Rep accounts are always 'headtohead' (they didn't exist before h2h era).
    Dem accounts:
      iso_date < ELECTION   → 'dem_pre'
      iso_date < h2h_start  → 'dem_post'
      else                  → 'headtohead'
    """
    if account in REP_ACCOUNTS:
        return "headtohead"
    if iso_date < ELECTION:
        return "dem_pre"
    if iso_date < h2h_start:
        return "dem_post"
    return "headtohead"


# ── toxicity ─────────────────────────────────────────────────────────────────

def toxicity_rows(posts: list[dict]) -> list[dict]:
    """Compute attack-vs-other view-count medians grouped by (account, era).

    posts: list of dicts with keys: account, era, views, function
    Output rows: {account, era, attackMedian, otherMedian, n, pending}
    pending = True when n (total classified posts in group) < 100
    """
    groups: dict[tuple, dict] = defaultdict(lambda: {"attack": [], "other": []})
    for p in posts:
        key = (p["account"], p["era"])
        if p["function"] == "attack":
            groups[key]["attack"].append(p["views"])
        else:
            groups[key]["other"].append(p["views"])

    rows = []
    for (account, era), g in groups.items():
        n = len(g["attack"]) + len(g["other"])
        rows.append({
            "account": account,
            "era": era,
            "attackMedian": statistics.median(g["attack"]) if g["attack"] else None,
            "otherMedian": statistics.median(g["other"]) if g["other"] else None,
            "n": n,
            "pending": n < 100,
        })
    return rows


# ── h2h_start ────────────────────────────────────────────────────────────────

def get_h2h_start() -> str:
    """Min upload_date in whitehouse_posts.csv (via to_iso)."""
    dates = []
    with open(DATA / "whitehouse_posts.csv", newline="") as f:
        for r in csv.DictReader(f):
            d = to_iso(r["upload_date"])
            if d:
                dates.append(d)
    return min(dates)


# ── era counts ───────────────────────────────────────────────────────────────

def build_eras(h2h_start: str) -> dict:
    """Per era key per side: post counts and date ranges from the 6 posts CSVs."""
    # Structure: eras[era][side] = {count, min_date, max_date}
    buckets: dict[str, dict[str, dict]] = {
        "dem_pre":     {"dem": {"count": 0, "min": "", "max": ""},
                        "rep": {"count": 0, "min": "", "max": ""}},
        "dem_post":    {"dem": {"count": 0, "min": "", "max": ""},
                        "rep": {"count": 0, "min": "", "max": ""}},
        "headtohead":  {"dem": {"count": 0, "min": "", "max": ""},
                        "rep": {"count": 0, "min": "", "max": ""}},
    }
    for account in ALL_ACCOUNTS:
        side = side_of(account)
        with open(DATA / f"{account}_posts.csv", newline="") as f:
            for r in csv.DictReader(f):
                d = to_iso(r["upload_date"])
                if not d:
                    continue
                era = era_of(account, d, h2h_start)
                b = buckets[era][side]
                b["count"] += 1
                if not b["min"] or d < b["min"]:
                    b["min"] = d
                if d > b["max"]:
                    b["max"] = d

    # Clean up empty sides (count 0 → omit min/max)
    out = {}
    for era, sides in buckets.items():
        out[era] = {}
        for side, b in sides.items():
            if b["count"] == 0:
                out[era][side] = {"count": 0}
            else:
                out[era][side] = {"count": b["count"], "min": b["min"], "max": b["max"]}
    return out


# ── profanity by month ───────────────────────────────────────────────────────

def build_profanity_by_month() -> list[dict]:
    """List of {m, dem, rep} where value = share of that side's posts with ≥1 hit.

    Months where a side has 0 posts → null for that side.
    """
    # Collect profanity video_ids per side
    profanity_ids: dict[str, set] = {"dem": set(), "rep": set()}
    for account in ALL_ACCOUNTS:
        side = side_of(account)
        p = CLS / f"profanity_{account}.jsonl"
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                profanity_ids[side].add(str(d["video_id"]))

    # Monthly post totals and profanity counts per side
    monthly_total: dict[str, dict[str, int]] = defaultdict(lambda: {"dem": 0, "rep": 0})
    monthly_hit: dict[str, dict[str, int]] = defaultdict(lambda: {"dem": 0, "rep": 0})

    for account in ALL_ACCOUNTS:
        side = side_of(account)
        with open(DATA / f"{account}_posts.csv", newline="") as f:
            for r in csv.DictReader(f):
                d = to_iso(r["upload_date"])
                if not d:
                    continue
                m = d[:7]
                monthly_total[m][side] += 1
                if str(r["id"]) in profanity_ids[side]:
                    monthly_hit[m][side] += 1

    rows = []
    for m in sorted(monthly_total.keys()):
        t = monthly_total[m]
        h = monthly_hit[m]
        dem_share = h["dem"] / t["dem"] if t["dem"] > 0 else None
        rep_share = h["rep"] / t["rep"] if t["rep"] > 0 else None
        rows.append({"m": m, "dem": dem_share, "rep": rep_share})
    return rows


# ── toxicity pays (real data) ─────────────────────────────────────────────────

def build_toxicity_pays(meta: dict, h2h_start: str) -> list[dict]:
    """Build toxicity_rows from function_*.jsonl joined with post_meta() views and era_of.

    meta: {id: (views, iso_date)} from post_meta()
    """
    posts = []
    for account in ALL_ACCOUNTS:
        p = CLS / f"function_{account}.jsonl"
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                vid = str(d["video_id"])
                func = d.get("function", "")
                if vid not in meta:
                    continue
                views, iso_date = meta[vid]
                era = era_of(account, iso_date, h2h_start)
                posts.append({
                    "account": account,
                    "era": era,
                    "views": views,
                    "function": func,
                })
    return toxicity_rows(posts)


# ── moderation ───────────────────────────────────────────────────────────────

def build_moderation() -> dict:
    """Count restricted posts in cluster_data.csv, total posts, and one known deletion."""
    account_set = set(ALL_ACCOUNTS)
    restricted = 0
    with open(CLUSTER_CSV, newline="") as f:
        for r in csv.DictReader(f):
            if r.get("account") not in account_set:
                continue
            val = r.get("is_restricted", "").strip().lower()
            if val in ("true", "1", "yes"):
                restricted += 1

    total = 0
    for account in ALL_ACCOUNTS:
        with open(DATA / f"{account}_posts.csv", newline="") as f:
            total += sum(1 for _ in csv.DictReader(f))

    return {
        "restricted": restricted,
        "deleted": 1,  # single known deletion per upstream FINDINGS.md
        "total": total,
    }


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    h2h_start = get_h2h_start()
    print(f"h2h_start: {h2h_start}")

    meta = post_meta()

    eras = build_eras(h2h_start)
    profanity_by_month = build_profanity_by_month()
    toxicity_pays = build_toxicity_pays(meta, h2h_start)
    moderation = build_moderation()

    toplines = {
        "eras": eras,
        "profanityByMonth": profanity_by_month,
        "toxicityPays": toxicity_pays,
        "moderation": moderation,
    }

    OUT_DATA.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DATA / "toplines.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(toplines, fh, indent=1)

    print(f"Written: {out_path}")
    print(f"eras: { {e: {s: eras[e][s]['count'] for s in eras[e]} for e in eras} }")
    print(f"profanityByMonth: {len(profanity_by_month)} months, "
          f"first={profanity_by_month[0]['m']}, last={profanity_by_month[-1]['m']}")
    print(f"toxicityPays: {len(toxicity_pays)} rows")
    wh_h2h = next((r for r in toxicity_pays
                   if r["account"] == "whitehouse" and r["era"] == "headtohead"), None)
    if wh_h2h:
        print(f"WH headtohead: attackMedian={wh_h2h['attackMedian']}, "
              f"otherMedian={wh_h2h['otherMedian']}, n={wh_h2h['n']}, "
              f"pending={wh_h2h['pending']}")
    print(f"moderation: {moderation}")


if __name__ == "__main__":
    main()
