import csv, json, datetime, statistics
from collections import defaultdict
from .config import (DESC, CLS, DATA, OUT_DATA, OUT_STATIC, OUT_WORK, PROJECT,
                     ALL_ACCOUNTS, PARTY, side_of, canonical_name, slugify)

TOP_N = 12

def week_start(date_str):
    d = datetime.date.fromisoformat(date_str[:10])
    return (d - datetime.timedelta(days=d.weekday())).isoformat()

def to_iso(s: str) -> str:
    """Normalize date strings to 'YYYY-MM-DD' ISO format.
    Accepts '2026-07-02', '20260702', or datetime-ish strings.
    Returns '' for unparseable input.
    """
    if not s:
        return ""
    s = str(s).strip()
    if len(s) >= 10 and s[4] == "-":
        return s[:10]
    if len(s) >= 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return ""

def load_stage2():
    """(video_id, canonical subject) -> register, from all function_*.jsonl."""
    reg = {}
    for f in CLS.glob("function_*.jsonl"):
        for line in open(f, encoding="utf-8"):
            d = json.loads(line)
            for t in d.get("treatments", []):
                reg[(str(d["video_id"]), canonical_name(t["subject"]))] = t["register"]
    return reg

def post_meta():
    """{id: (view_count, upload_date)} from all posts CSVs. Also used by build_interior."""
    meta = {}
    for account in ALL_ACCOUNTS:
        with open(DATA / f"{account}_posts.csv", newline="") as f:
            for r in csv.DictReader(f):
                meta[str(r["id"])] = (int(r["view_count"] or 0), to_iso(r["upload_date"]))
    return meta

def iter_posts(meta=None):
    """Stage-1 descriptions with account + upload_date attached."""
    meta = meta or post_meta()
    for account in ALL_ACCOUNTS:
        for f in (DESC / account).glob("*.json"):
            d = json.loads(f.read_text())
            vid = str(d.get("video_id", f.stem))
            d["video_id"], d["account"] = vid, account
            d["upload_date"] = meta.get(vid, (0, "2025-01-01"))[1]
            yield d

def aggregate(posts, stage2):
    people = defaultdict(lambda: {"own": 0, "opp": 0,
                                  "weekly": defaultdict(lambda: {"own": 0, "opp": 0}),
                                  "own_regs": [], "opp_regs": []})
    unknown = defaultdict(int)
    pairs = covered = 0
    for d in posts:
        poster = side_of(d["account"])
        wk = week_start(d["upload_date"])
        for c in d.get("cast", []):
            if not c.get("is_main"):
                continue
            name = canonical_name(c["name"])
            if name not in PARTY:
                unknown[name] += 1
                continue
            air = "own" if poster == PARTY[name] else "opp"
            p = people[name]
            p[air] += 1
            p["weekly"][wk][air] += 1
            pairs += 1
            reg = stage2.get((str(d["video_id"]), name))
            if reg is not None:
                covered += 1
                p[f"{air}_regs"].append(reg)
    out_people = []
    for name, p in people.items():
        total = p["own"] + p["opp"]
        out_people.append({
            "slug": slugify(name), "name": name, "face": f"faces/{slugify(name)}.png",
            "totals": {"posts": total, "own": p["own"], "opp": p["opp"],
                       "oppShare": p["opp"] / total if total else 0,
                       "ownRegister": statistics.mean(p["own_regs"]) if p["own_regs"] else None,
                       "oppRegister": statistics.mean(p["opp_regs"]) if p["opp_regs"] else None},
            "weekly": [{"w": w, **v} for w, v in sorted(p["weekly"].items())]})
    out_people.sort(key=lambda x: -x["totals"]["posts"])
    result = {"generated": datetime.date.today().isoformat(),
              "stage2": "full" if pairs and covered / pairs >= 0.9 else "partial",
              "people": out_people[:TOP_N]}
    unknown_sorted = dict(sorted(unknown.items(), key=lambda kv: -kv[1])[:40])
    return result, unknown_sorted

def cut_faces(people):
    """pol-face watchlist/{slug}/01.jpg -> static/faces/{slug}.png via rembg.

    RIGHTS NOTE: YouGov portraits were fetched as internal face-ID references.
    Before publish, confirm rights or swap sources (official congressional /
    White House portraits are public domain) — flagged in Task 14 methodology.
    """
    from rembg import remove
    from .config import WATCHLIST
    out = OUT_STATIC / "faces"; out.mkdir(parents=True, exist_ok=True)
    for p in people:
        src = WATCHLIST / p["slug"] / "01.jpg"
        if not src.exists():
            print(f"WARN no headshot: {src}")
            continue
        try:
            (out / f"{p['slug']}.png").write_bytes(remove(src.read_bytes()))
        except Exception as e:
            print(f"WARN rembg failed for {p['slug']}: {e}")

def main():
    out, unknown = aggregate(iter_posts(), load_stage2())
    OUT_WORK.mkdir(parents=True, exist_ok=True)
    (OUT_WORK / "unknown_party.txt").write_text(
        "\n".join(f"{v}\t{k}" for k, v in unknown.items()))
    cut_faces(out["people"])
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    with open(OUT_DATA / "balloons.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"stage2={out['stage2']}, top: "
          + ", ".join(f"{p['name']}({p['totals']['posts']})" for p in out["people"][:5]))

if __name__ == "__main__":
    main()
