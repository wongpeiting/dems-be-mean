# TikTok Cast Interactive — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the mobile-first quiz + balloon scrollytelling interactive per `specs/2026-07-11-tiktok-cast-design.md`, on data that exists today, with contracts that absorb the full stage-2 classification (landing ~midday 2026-07-12) via pipeline re-run only.

**Architecture:** A Python pipeline (`pipeline/`) reads the upstream `all-of-pol-tiktok` repo and emits JSON contracts into `src/lib/data/` plus media into `static/`. The SvelteKit site (existing scaffold: Svelte 5 runes forced, adapter-static, d3 v7, runes `Scroller.svelte` with `progress`/`index` bindables) renders six scenes off those contracts. One external mini-project (`crowd/`, Vercel + Upstash Redis) serves live crowd stats; the site degrades to seeded stats without it.

**Tech Stack:** SvelteKit 2 / Svelte 5 (runes), d3 v7, GSAP 3.13 (ScrollTrigger, free tier), svelte/motion Spring, vitest; Python 3.11+ (pandas, Pillow, rembg), ffmpeg; Vercel serverless + @upstash/redis.

## Global Constraints

- Mobile-first: design target is a 390×844 viewport; desktop is an adaptation. Test every scene at that size.
- `docs/` is the GitHub Pages build output (`make github`). Never put source docs there; specs/plans live in `specs/`.
- No `feDisplacementMap`, no animated transforms *inside* SVG on scroll paths — face stretch is CSS transforms on HTML layers only (Safari perf).
- All pipeline scripts must run correctly when stage-2 data is partial: enrich rows that exist, mark the rest `"pending": true`. Re-running the pipeline after tomorrow's data drop is the only upgrade step.
- Upstream repo root: `/Users/wongpeiting/Desktop/CU/python-work/all-of-pol-tiktok/party_accounts` (read-only from this project).
- Accounts → sides: dem = `democrats, dccc, senatedems, senatedemshq`; rep = `whitehouse, republicans`.
- Election anchor: `2024-11-06`. Head-to-head era starts at @whitehouse's first post date (compute from data, do not hardcode).
- Git commits: NEVER add Co-Authored-By tags.
- D3 does math, Svelte owns the DOM, GSAP animates; never let Svelte reactivity and GSAP write the same attribute.

## Upstream data map (verified 2026-07-11)

| Data | Path (under upstream root) | Notes |
|---|---|---|
| Posts metadata | `data/{account}_posts.csv` | cols: `id,account,url,title,description,upload_date,duration,view_count,like_count,comment_count,repost_count,tags,track,track_artist,is_photo_carousel,transcript` |
| Stage-1 descriptions | `data/descriptions/gemini_v2/{account}/{video_id}.json` | keys: `video_id, visual_action, cast[], on_screen_text[], spoken_summary, emojis_present[], audio_music, editing_pacing, is_manipulated, manipulation_or_satire, emotions_signaled[], cultural_references[], central_claim, intended_effect, uncertainty_flags[]`; cast item: `{name, kind, how_identified, role_in_post, is_main, evidence}` |
| Stage-2 function | `data/classification/function_{account}.jsonl` | keys: `account, video_id, function, treatments[], peak_subject, peak_register, peak_side, peak_rationale, peak_autofixed, crudeness, crudeness_evidence, attention_mechanisms, function_confidence, treatments_confidence, function_rationale, production_style, has_dunk, dunk_line`; treatment: `{subject, side, register, is_main_character, is_peak, evidence}`. WH ~816 rows now; full corpus + regenerated `stage2_classification.csv` / `stage2_treatments.csv` land ~2026-07-12 midday |
| Profanity | `data/classification/profanity_{account}.jsonl` | exact words + source + strong tier |
| Embedding clusters | `data/embeddings_gemini/cluster_data.csv` | cols: `id,account,x,y,cluster,title,description,upload_date,view_count,like_count,comment_count,track,post_type,is_restricted,transcript` — Cluster 34 = convergence zone; `is_restricted` feeds moderation stat |
| Videos | `videos/{account}/{id}.mp4` | carousels end `_carousel.mp4` |

## Data contracts (produced by pipeline, consumed by site)

- `src/lib/data/quiz.json` — `{rounds: [{id, answer: "dem"|"rep", account, caption, sound, clip, poster, tell: bool}], seeded: {roundId: {dem, rep}}}`
- `src/lib/data/balloons.json` — `{generated, stage2: "partial"|"full", people: [{slug, name, face, totals: {posts, own, opp, oppShare, ownRegister|null, oppRegister|null}, weekly: [{w: "YYYY-MM-DD", own, opp}]}]}` (sorted by posts desc, top 12; registers null until stage-2 covers that person)
- `src/lib/data/interior/{slug}.json` — `{slug, thumb: 96, cols: 16, atlases: ["atlas/{slug}_0.jpg"], nodes: [{id, x, y, emotion, color, account, side, ai, ax, ay, claim, intent, register|null, dunk, date, views}]}` (x,y in 0–1)
- `src/lib/data/toplines.json` — `{eras: {...}, profanityByMonth: [...], toxicityPays: [{account, era, attackMedian, otherMedian, n, pending}], moderation: {restricted, deleted, total}}`
- `static/clips/{id}.mp4|.webm|.jpg`, `static/atlas/{slug}_{n}.jpg`, `static/faces/{slug}.png`

---

### Task 1: Project plumbing — deps, test runners, pipeline skeleton

**Files:**
- Modify: `package.json` (add gsap, vitest)
- Create: `vitest.config.js`, `pipeline/requirements.txt`, `pipeline/config.py`, `pipeline/tests/test_config.py`, `.env.example`
- Modify: `svelte.config.js` (base path), `Makefile` (BASE_PATH)

**Interfaces:**
- Produces: `pipeline.config` module (paths, `DEM_ACCOUNTS`, `REP_ACCOUNTS`, `side_of(account)`, `EMOTION_MAP`, `ALIASES`, `slugify(name)`); `npm test` and `pytest pipeline/tests` both green.

- [ ] **Step 1: Install JS deps**

```bash
npm install gsap && npm install -D vitest @vitest/browser jsdom
```

- [ ] **Step 2: Create `vitest.config.js`**

```js
import { defineConfig } from 'vitest/config';
export default defineConfig({
	test: { include: ['src/**/*.test.js'], environment: 'jsdom' }
});
```

Add to `package.json` scripts: `"test": "vitest run"`.

- [ ] **Step 3: Create `pipeline/requirements.txt` and venv**

```
pandas>=2.0
Pillow>=10.0
rembg>=2.0
pytest>=8.0
```

```bash
python3 -m venv pipeline/.venv && pipeline/.venv/bin/pip install -r pipeline/requirements.txt
```

Add `pipeline/.venv/` and `pipeline/out/` to `.gitignore`.

- [ ] **Step 4: Write failing test `pipeline/tests/test_config.py`**

```python
from pipeline.config import side_of, slugify, canonical_name

def test_side_of():
    assert side_of("democrats") == "dem"
    assert side_of("dccc") == "dem"
    assert side_of("whitehouse") == "rep"
    assert side_of("republicans") == "rep"

def test_slugify():
    assert slugify("Donald Trump") == "donald-trump"
    assert slugify("Alexandria Ocasio-Cortez") == "alexandria-ocasio-cortez"

def test_alias_resolution():
    assert canonical_name("Trump") == "Donald Trump"
    assert canonical_name("President Donald Trump") == "Donald Trump"
    assert canonical_name("JD Vance") == "JD Vance"
    assert canonical_name("J.D. Vance") == "JD Vance"
```

- [ ] **Step 5: Run to verify it fails**

Run: `cd /Users/wongpeiting/Desktop/CU/python-work/tiktok-cast && pipeline/.venv/bin/pytest pipeline/tests/test_config.py -v` — Expected: FAIL (module not found). Add empty `pipeline/__init__.py` and `pipeline/tests/__init__.py`.

- [ ] **Step 6: Implement `pipeline/config.py`**

```python
import re
from pathlib import Path

UPSTREAM = Path("/Users/wongpeiting/Desktop/CU/python-work/all-of-pol-tiktok/party_accounts")
DATA = UPSTREAM / "data"
DESC = DATA / "descriptions" / "gemini_v2"
CLS = DATA / "classification"
VIDEOS = UPSTREAM / "videos"
CLUSTER_CSV = DATA / "embeddings_gemini" / "cluster_data.csv"

PROJECT = Path(__file__).resolve().parents[1]
OUT_DATA = PROJECT / "src" / "lib" / "data"
OUT_STATIC = PROJECT / "static"
OUT_WORK = PROJECT / "pipeline" / "out"

DEM_ACCOUNTS = {"democrats", "dccc", "senatedems", "senatedemshq"}
REP_ACCOUNTS = {"whitehouse", "republicans"}
ALL_ACCOUNTS = sorted(DEM_ACCOUNTS | REP_ACCOUNTS)
ELECTION = "2024-11-06"

def side_of(account: str) -> str:
    if account in DEM_ACCOUNTS: return "dem"
    if account in REP_ACCOUNTS: return "rep"
    raise ValueError(account)

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

# Free-text cast names -> canonical. Extend as pipeline logs unknowns.
ALIASES = {
    "trump": "Donald Trump", "donald j. trump": "Donald Trump",
    "president trump": "Donald Trump", "president donald trump": "Donald Trump",
    "j.d. vance": "JD Vance", "vice president jd vance": "JD Vance",
    "kamala harris": "Kamala Harris", "vice president kamala harris": "Kamala Harris",
    "elon musk": "Elon Musk", "hakeem jeffries": "Hakeem Jeffries",
    "chuck schumer": "Chuck Schumer", "barack obama": "Barack Obama",
    "joe biden": "Joe Biden", "president joe biden": "Joe Biden",
    "gavin newsom": "Gavin Newsom", "karoline leavitt": "Karoline Leavitt",
    "pete hegseth": "Pete Hegseth", "zohran mamdani": "Zohran Mamdani",
    "alexandria ocasio-cortez": "Alexandria Ocasio-Cortez", "aoc": "Alexandria Ocasio-Cortez",
}
def canonical_name(name: str) -> str:
    return ALIASES.get(name.strip().lower(), name.strip())

# Canonical emotion buckets -> hex (smoke palette). Stage-1 emotions map in.
EMOTION_MAP = {
    "pride": ("Pride", "#e4572e"), "patriotism": ("Pride", "#e4572e"),
    "anger": ("Anger", "#c1121f"), "outrage": ("Anger", "#c1121f"), "rage": ("Anger", "#c1121f"),
    "mockery": ("Mockery", "#7b2cbf"), "ridicule": ("Mockery", "#7b2cbf"),
    "contempt": ("Mockery", "#7b2cbf"), "humor": ("Humor", "#f4a261"),
    "amusement": ("Humor", "#f4a261"), "fear": ("Alarm", "#264653"),
    "alarm": ("Alarm", "#264653"), "urgency": ("Alarm", "#264653"),
    "inspiration": ("Hype", "#2a9d8f"), "strength": ("Hype", "#2a9d8f"),
    "triumph": ("Hype", "#2a9d8f"), "excitement": ("Hype", "#2a9d8f"),
    "nostalgia": ("Warmth", "#e9c46a"), "hope": ("Warmth", "#e9c46a"),
}
def emotion_bucket(label: str) -> tuple[str, str]:
    return EMOTION_MAP.get(label.strip().lower(), ("Other", "#8d99ae"))
```

- [ ] **Step 7: Run tests, verify pass**

Run: `pipeline/.venv/bin/pytest pipeline/tests/test_config.py -v` — Expected: 3 PASS.

- [ ] **Step 8: Base path + env**

In `svelte.config.js` add inside `kit`: `paths: { base: process.env.BASE_PATH || '' }`. In `Makefile`, change build line to `BASE_PATH=/tiktok-cast npm run build` (confirm repo name with `git remote -v` first; if no remote yet, leave a Makefile comment to set it at deploy). Create `.env.example`:

```
VITE_CROWD_URL=
```

- [ ] **Step 9: Verify build & commit**

Run: `npm run build` — Expected: exits 0. Then:

```bash
git add -A && git commit -m "chore: deps, vitest, pipeline skeleton, base path"
```

---

### Task 2: Quiz curation script → candidates sheet for PT

**Files:**
- Create: `pipeline/curate_quiz.py`, `pipeline/tests/test_curate.py`

**Interfaces:**
- Consumes: `pipeline.config` paths.
- Produces: `pipeline/out/quiz_candidates.csv` with columns `id, account, side, upload_date, view_count, caption, track, central_claim, source (cluster34|absurd|both), url` — PT edits this into `pipeline/picks.csv` (same columns + `tell` bool, keep ~24 rows).

- [ ] **Step 1: Write failing test**

```python
# pipeline/tests/test_curate.py
import json
from pipeline.curate_quiz import build_candidates

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
    rows = build_candidates(cluster, tmp_path / "desc")
    by_id = {r["id"]: r for r in rows}
    assert by_id["111"]["source"] == "cluster34"
    assert by_id["222"]["source"] == "absurd"
    assert by_id["111"]["side"] == "dem" and by_id["222"]["side"] == "rep"
```

- [ ] **Step 2: Run, verify FAIL** — `pipeline/.venv/bin/pytest pipeline/tests/test_curate.py -v` → import error.

- [ ] **Step 3: Implement `pipeline/curate_quiz.py`**

```python
import csv, json, re
from pathlib import Path
from .config import CLUSTER_CSV, DESC, OUT_WORK, ALL_ACCOUNTS, side_of

ABSURD = re.compile(r"absurd|surreal", re.I)
TEXT_FIELDS = ("central_claim", "intended_effect", "visual_action", "manipulation_or_satire")

def build_candidates(cluster_csv: Path, desc_dir: Path) -> list[dict]:
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
    return [r for r in rows.values() if r["source"]]

def main():
    OUT_WORK.mkdir(parents=True, exist_ok=True)
    rows = build_candidates(CLUSTER_CSV, DESC)
    for r in rows:
        r["url"] = f"https://www.tiktok.com/@{r['account']}/video/{r['id']}"
    out = OUT_WORK / "quiz_candidates.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} candidates -> {out}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests, verify PASS** — `pipeline/.venv/bin/pytest pipeline/tests/test_curate.py -v`.

- [ ] **Step 5: Run for real, sanity-check**

Run: `pipeline/.venv/bin/python -m pipeline.curate_quiz` — Expected: several hundred candidates. Spot-check that `7596097777050848567` (Vance "Creep") appears; grep the sheet for `sombrero` candidates for PT's ambiguity audit. **Hand off `quiz_candidates.csv` to PT; PT saves ~24 rows as `pipeline/picks.csv` adding a `tell` column (true on ~every 3rd).**

- [ ] **Step 6: Commit** — `git add pipeline && git commit -m "feat: quiz candidate curation script"`

---

### Task 3: Clip encoder + quiz.json builder

**Files:**
- Create: `pipeline/build_quiz.py`, `pipeline/tests/test_build_quiz.py`

**Interfaces:**
- Consumes: `pipeline/picks.csv` (from Task 2), upstream `videos/{account}/{id}.mp4`.
- Produces: `static/clips/{id}.mp4/.webm/.jpg`; `src/lib/data/quiz.json` per the contract above. `seeded` starts as `{}` (filled by pilot in Task 10).

- [ ] **Step 1: Write failing test (JSON assembly only — ffmpeg is not unit-tested)**

```python
# pipeline/tests/test_build_quiz.py
from pipeline.build_quiz import rounds_from_picks

def test_rounds_from_picks():
    picks = [{"id": "111", "account": "democrats", "side": "dem", "caption": "so real",
              "track": "Creep", "tell": "true", "upload_date": "2025-01-01",
              "view_count": "9", "central_claim": "", "source": "absurd", "url": ""}]
    rounds = rounds_from_picks(picks)
    r = rounds[0]
    assert r == {"id": "111", "answer": "dem", "account": "democrats",
                 "caption": "so real", "sound": "Creep", "tell": True,
                 "clip": "clips/111", "poster": "clips/111.jpg"}
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement `pipeline/build_quiz.py`**

```python
import csv, json, subprocess
from .config import VIDEOS, OUT_STATIC, OUT_DATA, PROJECT

def rounds_from_picks(picks: list[dict]) -> list[dict]:
    return [{"id": p["id"], "answer": p["side"], "account": p["account"],
             "caption": p["caption"], "sound": p["track"],
             "tell": str(p.get("tell", "")).lower() == "true",
             "clip": f"clips/{p['id']}", "poster": f"clips/{p['id']}.jpg"} for p in picks]

def encode(src, out_dir, vid):
    # 2.5s loop from t=0.5, muted, watermark shaved via 8% crop, 480px wide
    vf = "crop=iw*0.92:ih*0.92,scale=480:-2"
    base = ["ffmpeg", "-y", "-ss", "0.5", "-t", "2.5", "-i", str(src), "-an", "-vf", vf]
    subprocess.run(base + ["-c:v", "libx264", "-crf", "28", "-preset", "slow",
                           "-movflags", "+faststart", str(out_dir / f"{vid}.mp4")], check=True)
    subprocess.run(base + ["-c:v", "libvpx-vp9", "-crf", "42", "-b:v", "0",
                           str(out_dir / f"{vid}.webm")], check=True)
    subprocess.run(["ffmpeg", "-y", "-ss", "1", "-i", str(src), "-frames:v", "1",
                    "-vf", vf, str(out_dir / f"{vid}.jpg")], check=True)

def main():
    picks = list(csv.DictReader(open(PROJECT / "pipeline" / "picks.csv")))
    out_dir = OUT_STATIC / "clips"; out_dir.mkdir(parents=True, exist_ok=True)
    for p in picks:
        src = VIDEOS / p["account"] / f"{p['id']}.mp4"
        if not src.exists():
            src = VIDEOS / p["account"] / f"{p['id']}_carousel.mp4"
        encode(src, out_dir, p["id"])
    (OUT_DATA).mkdir(parents=True, exist_ok=True)
    json.dump({"rounds": rounds_from_picks(picks), "seeded": {}},
              open(OUT_DATA / "quiz.json", "w"), indent=1)
    print(f"{len(picks)} rounds encoded")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests, verify PASS.**

- [ ] **Step 5: Run for real once `picks.csv` exists; eyeball 3 clips in QuickTime (watermark gone, loop reads). Check total `static/clips` weight < 15 MB; raise crf if not.**

- [ ] **Step 6: Commit** — `git commit -am "feat: quiz clip encoder + quiz.json"`

---

### Task 4: balloons.json builder (stage-1 counts now, stage-2 enrichment when present)

**Files:**
- Create: `pipeline/build_balloons.py`, `pipeline/tests/test_balloons.py`

**Interfaces:**
- Consumes: Stage-1 descriptions (cast/is_main), `function_{account}.jsonl` (registers), YouGov headshots at `/Users/wongpeiting/Desktop/CU/python-work/pol-face/watchlist/{slug}/01.jpg` (background cut with rembg → `static/faces/{slug}.png`; rights check before publish, see Task 14).
- Produces: `src/lib/data/balloons.json` per contract. **Core drop-in-later mechanism:** counts come from Stage-1 (complete today); `ownRegister/oppRegister` come from stage-2 treatments and are `null` where absent; `stage2` field says `"partial"` until >90% of posts have stage-2 rows.

- [ ] **Step 1: Write failing test**

```python
# pipeline/tests/test_balloons.py
from pipeline.build_balloons import aggregate

def desc(vid, account, names_main):
    return {"video_id": vid, "account": account, "upload_date": "2025-01-06",
            "cast": [{"name": n, "is_main": True} for n in names_main]}

def test_aggregate_counts_and_sides():
    posts = [desc("1", "democrats", ["Trump"]),          # opp air for Trump
             desc("2", "whitehouse", ["Donald Trump"]),  # own air (alias resolves)
             desc("3", "whitehouse", ["Donald Trump"])]
    out = aggregate(posts, stage2={})
    trump = next(p for p in out["people"] if p["slug"] == "donald-trump")
    assert trump["totals"] == {"posts": 3, "own": 2, "opp": 1,
                               "oppShare": 1/3, "ownRegister": None, "oppRegister": None}
    assert trump["weekly"] == [{"w": "2025-01-06", "own": 2, "opp": 1}]

def test_stage2_registers_enrich():
    posts = [desc("2", "whitehouse", ["Donald Trump"])]
    s2 = {("2", "Donald Trump"): -3}
    out = aggregate(posts, stage2=s2)
    trump = out["people"][0]
    assert trump["totals"]["ownRegister"] == -3
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement `pipeline/build_balloons.py`**

First add to `config.py` (own-vs-opp needs the subject's party — a poster-side count alone can't say who is hyping and who is mocking). Party AND faces both come from the pol-face YouGov roster (385 people, kebab-case slugs matching our `slugify`, one headshot at `watchlist/{slug}/01.jpg`):

```python
import csv as _csv
WATCHLIST = Path("/Users/wongpeiting/Desktop/CU/python-work/pol-face/watchlist")

def _load_party():
    """Subject party from pol-face YouGov roster.csv (name,slug,party R/D) + extras."""
    party = {}
    with open(WATCHLIST / "roster.csv", newline="") as f:
        for r in _csv.DictReader(f):
            party[r["name"]] = "rep" if r["party"] == "R" else "dem"
    party.update({"Elon Musk": "rep", "Karoline Leavitt": "rep"})  # extend via unknown_party.txt
    return party

PARTY = _load_party()
```

(Adjust `test_config.py` accordingly: add `from pipeline.config import PARTY; assert PARTY["Donald Trump"] == "rep"` — it reads the real roster, which is fine for this repo-local integration test.)

Then `pipeline/build_balloons.py`:

```python
import csv, json, datetime, statistics
from collections import defaultdict
from .config import (DESC, CLS, DATA, OUT_DATA, OUT_STATIC, OUT_WORK, PROJECT,
                     ALL_ACCOUNTS, PARTY, side_of, canonical_name, slugify)

TOP_N = 12

def week_start(date_str):
    d = datetime.date.fromisoformat(date_str[:10])
    return (d - datetime.timedelta(days=d.weekday())).isoformat()

def load_stage2():
    """(video_id, canonical subject) -> register, from all function_*.jsonl."""
    reg = {}
    for f in CLS.glob("function_*.jsonl"):
        for line in open(f):
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
                meta[str(r["id"])] = (int(r["view_count"] or 0), r["upload_date"])
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
    return {"generated": datetime.date.today().isoformat(),
            "stage2": "full" if pairs and covered / pairs >= 0.9 else "partial",
            "people": out_people[:TOP_N],
            "_unknown": dict(sorted(unknown.items(), key=lambda kv: -kv[1])[:40])}

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
        if src.exists():
            (out / f"{p['slug']}.png").write_bytes(remove(src.read_bytes()))
        else:
            print(f"WARN no headshot: {src}")

def main():
    out = aggregate(iter_posts(), load_stage2())
    unknown = out.pop("_unknown")
    OUT_WORK.mkdir(parents=True, exist_ok=True)
    (OUT_WORK / "unknown_party.txt").write_text(
        "\n".join(f"{v}\t{k}" for k, v in unknown.items()))
    cut_faces(out["people"])
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(OUT_DATA / "balloons.json", "w"), indent=1)
    print(f"stage2={out['stage2']}, top: "
          + ", ".join(f"{p['name']}({p['totals']['posts']})" for p in out["people"][:5]))

if __name__ == "__main__":
    main()
```

The Step-1 test pins the semantic: democrats posting Trump = `opp` air; whitehouse posting Trump = `own` (its `desc()` fixtures flow through `aggregate(iter([...]), stage2)` — pass the fixture list directly, `aggregate` takes any iterable). Note the test's expected weekly `w` is `"2025-01-06"`, a Monday. High-count names in `unknown_party.txt` get added to `PARTY`/`ALIASES`, then re-run.

- [ ] **Step 4: Run tests, verify PASS** (against the final clean implementation).

- [ ] **Step 5: Run for real** — `pipeline/.venv/bin/python -m pipeline.build_balloons`. Expected: `balloons.json` with Trump top, `stage2: "partial"`. Check `pipeline/out/unknown_party.txt` and extend PARTY/ALIASES for any high-count names, re-run.

- [ ] **Step 6: Commit** — `git commit -am "feat: balloons.json aggregation with stage-2 enrichment hook"`

---

### Task 5: Interior field data + thumbnail atlases (hero: donald-trump)

**Files:**
- Create: `pipeline/build_interior.py`, `pipeline/tests/test_interior.py`

**Interfaces:**
- Consumes: Stage-1 descriptions (emotions_signaled, central_claim, intended_effect), posts CSVs (views/date), stage-2 (register, dunk_line) when present, `videos/` for frames.
- Produces: `src/lib/data/interior/donald-trump.json` + `static/atlas/donald-trump_{n}.jpg` (16-col sheets of 96px thumbs, ≤256/sheet).

- [ ] **Step 1: Write failing test (layout determinism + emotion clustering)**

```python
# pipeline/tests/test_interior.py
from pipeline.build_interior import layout

def test_layout_clusters_by_emotion_and_is_deterministic():
    nodes = [{"id": str(i), "emotion": "Pride" if i < 5 else "Anger"} for i in range(10)]
    a, b = layout(list(nodes)), layout(list(nodes))
    assert a == b                                    # deterministic (seeded)
    assert all(0 <= n["x"] <= 1 and 0 <= n["y"] <= 1 for n in a)
    import statistics
    pride = [n["x"] for n in a if n["emotion"] == "Pride"]
    anger = [n["x"] for n in a if n["emotion"] == "Anger"]
    assert abs(statistics.mean(pride) - statistics.mean(anger)) > 0.15  # separated clusters
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement `pipeline/build_interior.py`**

```python
import json, math, random, subprocess
from collections import Counter
from PIL import Image
from .config import (DESC, CLS, OUT_DATA, OUT_STATIC, VIDEOS, ALL_ACCOUNTS,
                     side_of, canonical_name, emotion_bucket)

THUMB, COLS, PER_SHEET = 96, 16, 256

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

def collect(slug="donald-trump", name="Donald Trump"):
    meta = {}  # id -> (views, date) built from posts CSVs (same join helper as Task 4)
    from .build_balloons import load_stage2, post_meta
    meta = post_meta(); s2 = load_stage2()
    dunks = {}
    for f in CLS.glob("function_*.jsonl"):
        for line in open(f):
            d = json.loads(line)
            if d.get("has_dunk"): dunks[str(d["video_id"])] = d.get("dunk_line", "")
    nodes = []
    for account in ALL_ACCOUNTS:
        for f in (DESC / account).glob("*.json"):
            d = json.loads(f.read_text())
            if not any(canonical_name(c["name"]) == name and c.get("is_main")
                       for c in d.get("cast", [])): continue
            vid = str(d.get("video_id", f.stem))
            emo_raw = (d.get("emotions_signaled") or ["Other"])[0]
            bucket, color = emotion_bucket(emo_raw)
            views, date = meta.get(vid, (0, ""))
            nodes.append({"id": vid, "emotion": bucket, "color": color,
                          "account": account, "side": side_of(account),
                          "claim": d.get("central_claim", ""), "intent": d.get("intended_effect", ""),
                          "register": s2.get((vid, name)), "dunk": dunks.get(vid, ""),
                          "date": date, "views": views, "_src": account})
    return nodes

def atlases(nodes, slug):
    out_dir = OUT_STATIC / "atlas"; out_dir.mkdir(parents=True, exist_ok=True)
    sheets = []
    for s in range(0, len(nodes), PER_SHEET):
        chunk = nodes[s:s + PER_SHEET]
        rows = math.ceil(len(chunk) / COLS)
        sheet = Image.new("RGB", (COLS * THUMB, rows * THUMB), "#111")
        for i, n in enumerate(chunk):
            src = VIDEOS / n["_src"] / f"{n['id']}.mp4"
            if not src.exists(): src = VIDEOS / n["_src"] / f"{n['id']}_carousel.mp4"
            tmp = OUT_STATIC / "atlas" / "_f.jpg"
            subprocess.run(["ffmpeg", "-y", "-ss", "1", "-i", str(src), "-frames:v", "1",
                            "-vf", f"scale={THUMB}:{THUMB}:force_original_aspect_ratio=increase,crop={THUMB}:{THUMB}",
                            str(tmp)], check=True, capture_output=True)
            sheet.paste(Image.open(tmp), ((i % COLS) * THUMB, (i // COLS) * THUMB))
            n.update(ai=len(sheets), ax=i % COLS, ay=i // COLS)
        p = out_dir / f"{slug}_{len(sheets)}.jpg"; sheet.save(p, quality=72); sheets.append(p.name)
    tmp.unlink(missing_ok=True)
    return sheets

def main(slug="donald-trump", name="Donald Trump"):
    nodes = layout(collect(slug, name))
    sheets = atlases(nodes, slug)
    for n in nodes: n.pop("_src")
    out = OUT_DATA / "interior"; out.mkdir(parents=True, exist_ok=True)
    json.dump({"slug": slug, "thumb": THUMB, "cols": COLS,
               "atlases": [f"atlas/{s}" for s in sheets], "nodes": nodes},
              open(out / f"{slug}.json", "w"))
    print(f"{len(nodes)} nodes, {len(sheets)} sheets")

if __name__ == "__main__":
    main()
```

(Requires `post_meta()` helper exported from `build_balloons.py`: `{id: (view_count:int, upload_date:str)}` from all posts CSVs — add it there with a 3-line test.)

- [ ] **Step 4: Run tests, verify PASS.**

- [ ] **Step 5: Run for real; open one atlas jpg, confirm thumbs legible. Node count should be several hundred (Trump-main posts across accounts).**

- [ ] **Step 6: Commit** — `git commit -am "feat: interior emotion layout + thumbnail atlases"`

---

### Task 6: toplines.json (eras, profanity crossover, toxicity-pays, moderation)

**Files:**
- Create: `pipeline/build_toplines.py`, `pipeline/tests/test_toplines.py`

**Interfaces:**
- Consumes: posts CSVs, `cluster_data.csv` (is_restricted), `profanity_*.jsonl`, `function_*.jsonl`.
- Produces: `src/lib/data/toplines.json` per contract. Toxicity rows have `pending: true` when an account/era has <100 classified posts; site renders those greyed with an "awaiting classification" note.

- [ ] **Step 1: Write failing test**

```python
# pipeline/tests/test_toplines.py
from pipeline.build_toplines import era_of, toxicity_rows

def test_era_of():
    assert era_of("democrats", "2024-10-01", h2h_start="2025-09-01") == "dem_pre"
    assert era_of("democrats", "2025-01-01", h2h_start="2025-09-01") == "dem_post"
    assert era_of("democrats", "2025-10-01", h2h_start="2025-09-01") == "headtohead"
    assert era_of("whitehouse", "2025-10-01", h2h_start="2025-09-01") == "headtohead"

def test_toxicity_medians_and_pending():
    posts = [{"account": "whitehouse", "era": "headtohead", "views": v,
              "function": "attack" if v > 50 else "promote_leader"}
             for v in [10, 20, 30, 100, 200, 300]] * 20  # 120 rows -> not pending
    rows = toxicity_rows(posts)
    wh = next(r for r in rows if r["account"] == "whitehouse")
    assert wh["attackMedian"] == 200 and wh["otherMedian"] == 20 and wh["pending"] is False
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement** — `era_of(account, date, h2h_start)` (dem accounts: `< ELECTION` → `dem_pre`, `< h2h_start` → `dem_post`, else `headtohead`; rep accounts always `headtohead` — they didn't exist before); `h2h_start` = min upload_date in `whitehouse_posts.csv`. Profanity: per month per side, share of posts with ≥1 strong profanity (`profanityByMonth`). Moderation: `restricted` = count of `is_restricted` truthy in cluster_data for the 6 accounts; `deleted: 1` (hardcode with comment citing FINDINGS.md); `total` = row count across the 6 posts CSVs. Toxicity: join `function_*.jsonl` on posts views; `attack` vs all other functions; medians via `statistics.median`; group by (account, era); `pending = n < 100`. Emit JSON.

- [ ] **Step 4: Run tests, verify PASS.**

- [ ] **Step 5: Run for real; sanity-check** — dem_pre attack data will be pending (no stage-2 yet) — correct; WH headtohead should have real medians. **After tomorrow's stage-2 drop: re-run `build_balloons`, `build_interior`, `build_toplines` — that is the entire upgrade.** Note the re-run command trio in `pipeline/README.md` (create it, 5 lines).

- [ ] **Step 6: Commit** — `git commit -am "feat: era toplines with pending markers"`

---

### Task 7: Crowd stats backend (`crowd/`) + site client with fallback

**Files:**
- Create: `crowd/package.json`, `crowd/vercel.json`, `crowd/api/guess.js`, `crowd/api/stats.js`
- Create: `src/lib/crowd.js`, `src/lib/crowd.test.js`

**Interfaces:**
- Produces: `POST {url}/api/guess {roundId, choice: "dem"|"rep", tellZone?}` → `{ok}`; `GET {url}/api/stats?rounds=a,b,c` → `{a: {dem, rep}, ...}`. Site: `postGuess(payload)` (fire-and-forget, no-op if unconfigured), `fetchStats(roundIds, seeded)` → stats map, falling back to `seeded` on timeout/absence.

- [ ] **Step 1: Write failing client test**

```js
// src/lib/crowd.test.js
import { describe, it, expect, vi } from 'vitest';
import { fetchStats, postGuess } from './crowd.js';

describe('crowd client', () => {
	it('falls back to seeded stats when no URL configured', async () => {
		const seeded = { '111': { dem: 60, rep: 40 } };
		expect(await fetchStats(['111'], seeded, '')).toEqual(seeded);
	});
	it('postGuess is a no-op without URL', () => {
		global.fetch = vi.fn();
		postGuess({ roundId: '1', choice: 'dem' }, '');
		expect(global.fetch).not.toHaveBeenCalled();
	});
	it('falls back on fetch failure', async () => {
		global.fetch = vi.fn().mockRejectedValue(new Error('down'));
		const seeded = { '111': { dem: 1, rep: 1 } };
		expect(await fetchStats(['111'], seeded, 'https://x.example')).toEqual(seeded);
	});
});
```

- [ ] **Step 2: Run `npm test`, verify FAIL.**

- [ ] **Step 3: Implement `src/lib/crowd.js`**

```js
const CONFIGURED = import.meta.env?.VITE_CROWD_URL || '';

export function postGuess(payload, url = CONFIGURED) {
	if (!url) return;
	fetch(`${url}/api/guess`, {
		method: 'POST',
		headers: { 'content-type': 'application/json' },
		body: JSON.stringify(payload),
		keepalive: true
	}).catch(() => {});
}

export async function fetchStats(roundIds, seeded, url = CONFIGURED) {
	if (!url) return seeded;
	try {
		const ctrl = new AbortController();
		const t = setTimeout(() => ctrl.abort(), 2500);
		const res = await fetch(`${url}/api/stats?rounds=${roundIds.join(',')}`, { signal: ctrl.signal });
		clearTimeout(t);
		if (!res.ok) return seeded;
		const live = await res.json();
		return { ...seeded, ...live };
	} catch {
		return seeded;
	}
}
```

- [ ] **Step 4: Run `npm test`, verify PASS.**

- [ ] **Step 5: Build the backend**

`crowd/package.json`: `{"name":"tiktok-cast-crowd","type":"module","dependencies":{"@upstash/redis":"^1.34.0"}}`. `crowd/api/guess.js`:

```js
import { Redis } from '@upstash/redis';
const redis = Redis.fromEnv();
const ZONES = new Set(['video', 'caption', 'sound', 'emoji', 'vibes']);
export default async function handler(req, res) {
	res.setHeader('Access-Control-Allow-Origin', '*');
	res.setHeader('Access-Control-Allow-Headers', 'content-type');
	if (req.method === 'OPTIONS') return res.status(204).end();
	if (req.method !== 'POST') return res.status(405).end();
	const { roundId, choice, tellZone } = req.body ?? {};
	if (!/^\d{5,25}$/.test(String(roundId)) || !['dem', 'rep'].includes(choice))
		return res.status(400).json({ ok: false });
	await redis.incr(`g:${roundId}:${choice}`);
	if (tellZone && ZONES.has(tellZone)) await redis.incr(`t:${roundId}:${tellZone}`);
	return res.status(200).json({ ok: true });
}
```

`crowd/api/stats.js`:

```js
import { Redis } from '@upstash/redis';
const redis = Redis.fromEnv();
export default async function handler(req, res) {
	res.setHeader('Access-Control-Allow-Origin', '*');
	res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=300');
	const ids = String(req.query.rounds || '').split(',').filter((s) => /^\d{5,25}$/.test(s)).slice(0, 64);
	if (!ids.length) return res.status(400).json({});
	const keys = ids.flatMap((id) => [`g:${id}:dem`, `g:${id}:rep`]);
	const vals = await redis.mget(...keys);
	const out = {};
	ids.forEach((id, i) => (out[id] = { dem: vals[i * 2] ?? 0, rep: vals[i * 2 + 1] ?? 0 }));
	return res.status(200).json(out);
}
```

Deploy: `cd crowd && npx vercel deploy --prod` after `npx vercel link` and adding a Vercel KV/Upstash integration (env vars auto-injected). Smoke test with curl POST + GET. Put the prod URL in `.env` as `VITE_CROWD_URL`.

- [ ] **Step 6: Commit** — `git add crowd src/lib/crowd.* && git commit -m "feat: crowd stats backend + client with seeded fallback"`

---

### Task 8: Quiz state + score sentence (TDD) 

**Files:**
- Create: `src/lib/quiz.svelte.js`, `src/lib/quiz.test.js`

**Interfaces:**
- Produces: `scoreSentence(n, correct)` pure fn; `class QuizState` — `constructor(rounds, storage?)`, `.current` (round or null when exhausted), `.guess(choice)` → `{correct, answer}` records + persists, `.n`, `.correct`, `.buttonOrder` (['dem','rep'] shuffled once, persisted), `.tellPending` (true when current round has `tell` and no zone logged), `.logTell(zone)`. Used by Task 9 UI and Scene 5 callback.

- [ ] **Step 1: Write failing tests**

```js
// src/lib/quiz.test.js
import { describe, it, expect } from 'vitest';
import { scoreSentence, QuizState } from './quiz.svelte.js';

const rounds = [
	{ id: '1', answer: 'dem', tell: false },
	{ id: '2', answer: 'rep', tell: true }
];

describe('scoreSentence', () => {
	it('handles zero', () => expect(scoreSentence(0, 0)).toBe('Tap a side to start guessing.'));
	it('singular', () => expect(scoreSentence(1, 1)).toBe('You’ve guessed once and got it right.'));
	it('coin flip note', () =>
		expect(scoreSentence(6, 3)).toBe('You’ve guessed 6 times and got 3 right — a coin flip.'));
	it('above chance', () =>
		expect(scoreSentence(8, 7)).toBe('You’ve guessed 8 times and got 7 right — better than most.'));
});

describe('QuizState', () => {
	const mem = () => {
		const m = {};
		return { getItem: (k) => m[k] ?? null, setItem: (k, v) => (m[k] = v) };
	};
	it('records guesses and score', () => {
		const q = new QuizState(rounds, mem());
		const r = q.guess('dem');
		expect(r).toEqual({ correct: true, answer: 'dem' });
		expect(q.n).toBe(1); expect(q.correct).toBe(1);
		expect(q.current.id).toBe('2');
	});
	it('tell round blocks reveal until zone logged', () => {
		const q = new QuizState(rounds, mem());
		q.guess('dem');
		q.pick('rep'); // pick on a tell round stores choice, sets tellPending
		expect(q.tellPending).toBe(true);
		q.logTell('sound');
		expect(q.tellPending).toBe(false);
		expect(q.n).toBe(2);
	});
	it('persists across instances', () => {
		const s = mem();
		new QuizState(rounds, s).guess('rep');
		expect(new QuizState(rounds, s).n).toBe(1);
	});
});
```

- [ ] **Step 2: Run `npm test`, verify FAIL.**

- [ ] **Step 3: Implement `src/lib/quiz.svelte.js`**

```js
export function scoreSentence(n, correct) {
	if (n === 0) return 'Tap a side to start guessing.';
	if (n === 1) return `You’ve guessed once and got it ${correct ? 'right' : 'wrong'}.`;
	const base = `You’ve guessed ${n} times and got ${correct} right`;
	const rate = correct / n;
	if (rate >= 0.75) return `${base} — better than most.`;
	if (rate >= 0.4 && rate <= 0.6) return `${base} — a coin flip.`;
	if (rate < 0.4) return `${base} — worse than a coin flip.`;
	return `${base}.`;
}

const KEY = 'tiktok-cast-quiz-v1';

export class QuizState {
	i = $state(0);
	guesses = $state([]);
	tellPending = $state(false);
	#pendingChoice = null;

	constructor(rounds, storage = globalThis.localStorage) {
		this.rounds = rounds;
		this.storage = storage;
		const saved = storage?.getItem(KEY);
		if (saved) {
			const s = JSON.parse(saved);
			this.i = s.i; this.guesses = s.guesses; this.buttonOrder = s.buttonOrder;
		}
		this.buttonOrder ??= Math.random() < 0.5 ? ['dem', 'rep'] : ['rep', 'dem'];
		this.#save();
	}
	get current() { return this.rounds[this.i] ?? null; }
	get n() { return this.guesses.length; }
	get correct() { return this.guesses.filter((g) => g.correct).length; }

	pick(choice) {
		if (!this.current) return null;
		if (this.current.tell) { this.#pendingChoice = choice; this.tellPending = true; return null; }
		return this.#commit(choice);
	}
	guess(choice) { return this.pick(choice) ?? this.#commit(this.#drain()); }
	logTell(zone) {
		if (!this.tellPending) return null;
		this.tellPending = false;
		const r = this.#commit(this.#pendingChoice);
		return { ...r, tellZone: zone };
	}
	#drain() { const c = this.#pendingChoice; this.#pendingChoice = null; this.tellPending = false; return c; }
	#commit(choice) {
		const round = this.current;
		const correct = choice === round.answer;
		this.guesses = [...this.guesses, { id: round.id, choice, correct }];
		this.i += 1;
		this.#save();
		return { correct, answer: round.answer };
	}
	#save() {
		this.storage?.setItem(KEY, JSON.stringify({ i: this.i, guesses: this.guesses, buttonOrder: this.buttonOrder }));
	}
}
```

Note: `.svelte.js` extension makes `$state` runes legal in a plain module; vitest resolves it through the Svelte plugin — add `svelte()` plugin from `@sveltejs/vite-plugin-svelte` to `vitest.config.js` plugins array (it's already a dependency).

- [ ] **Step 4: Run `npm test`, verify PASS. Adjust `guess()` helper if the tell-flow test demands (test is the contract).**

- [ ] **Step 5: Commit** — `git commit -am "feat: quiz state machine + score sentence"`

---

### Task 9: Quiz UI — ClipCard shell, buttons, reveal, tell-tap

**Files:**
- Create: `src/lib/components/QuizModule.svelte`, `src/lib/components/ClipCard.svelte`, `src/lib/components/ScoreSentence.svelte`
- Modify: `src/routes/+page.svelte` (mount quiz section)

**Interfaces:**
- Consumes: `quiz.json`, `QuizState`, `postGuess/fetchStats`.
- Produces: `<QuizModule {rounds} {seeded} onDone(score)>`; exposes bindable `quiz` (QuizState) for Scene 5 callback.

- [ ] **Step 1: ClipCard — the TikTok shell**

```svelte
<!-- src/lib/components/ClipCard.svelte -->
<script>
	import { base } from '$app/paths';
	let { round, revealed = false, onzone = null } = $props();
	const zones = [
		['video', ''], ['caption', 'the caption'], ['sound', 'the sound'], ['vibes', 'just vibes']
	];
</script>

<figure class="card" class:revealed>
	<video src="{base}/{round.clip}.mp4" poster="{base}/{round.poster}" autoplay muted loop playsinline
		onclick={() => onzone?.('video')}></video>
	<figcaption>
		<p class="caption" onclick={() => onzone?.('caption')}>{round.caption}</p>
		<p class="sound" onclick={() => onzone?.('sound')}>♫ {round.sound || 'original sound'}</p>
	</figcaption>
	{#if onzone}
		<button class="vibes" onclick={() => onzone('vibes')}>it’s just the vibes</button>
	{/if}
</figure>

<style>
	.card { position: relative; width: min(100%, 390px); aspect-ratio: 9/14; margin: 0 auto;
		border: 6px solid #222; border-radius: 12px; overflow: hidden; background: #000;
		transition: border-color 0.3s; }
	.card.revealed { border-color: var(--reveal, #222); }
	video { width: 100%; height: 100%; object-fit: cover; }
	figcaption { position: absolute; bottom: 0; left: 0; right: 0; padding: 10px 12px;
		background: linear-gradient(transparent, rgba(0,0,0,0.75)); color: #fff; }
	.caption { font-size: 14px; margin: 0 0 4px; }
	.sound { font-size: 12px; opacity: 0.85; margin: 0; }
	.vibes { position: absolute; top: 8px; right: 8px; font-size: 12px; padding: 4px 8px;
		border-radius: 999px; background: rgba(255,255,255,0.85); border: none; }
</style>
```

- [ ] **Step 2: QuizModule — state machine wiring**

```svelte
<!-- src/lib/components/QuizModule.svelte -->
<script>
	import ClipCard from './ClipCard.svelte';
	import { QuizState, scoreSentence } from '$lib/quiz.svelte.js';
	import { postGuess, fetchStats } from '$lib/crowd.js';
	let { rounds, seeded = {}, quiz = $bindable() } = $props();

	quiz = new QuizState(rounds);
	let phase = $state('guess'); // guess | tell | revealed
	let lastResult = $state(null);
	let stats = $state(seeded);
	$effect(() => { fetchStats(rounds.map((r) => r.id), seeded).then((s) => (stats = s)); });

	const LABELS = { dem: '🔵 Democrats', rep: '🔴 White House / GOP' };
	const VERDICTS_Y = ['Correct.', 'You got this one.', 'Right — this time.'];
	const VERDICTS_N = ['Nope.', 'Wrong side.', 'Gotcha.'];

	function crowdWrong(id, answer) {
		const s = stats[id]; if (!s) return null;
		const total = s.dem + s.rep; if (total < 20) return null;
		return Math.round((100 * s[answer === 'dem' ? 'rep' : 'dem']) / total);
	}
	function tap(choice) {
		if (phase !== 'guess' || !quiz.current) return;
		const roundId = quiz.current.id;
		const res = quiz.pick(choice);
		if (quiz.tellPending) { phase = 'tell'; return; }
		reveal(roundId, res, choice);
	}
	function zone(z) {
		if (phase !== 'tell') return;
		const roundId = rounds[quiz.i].id;
		const res = quiz.logTell(z);
		reveal(roundId, res, res ? rounds[quiz.i - 1] && quiz.guesses.at(-1).choice : null, z);
	}
	function reveal(roundId, res, choice, tellZone) {
		lastResult = { ...res, roundId, verdict: (res.correct ? VERDICTS_Y : VERDICTS_N)[quiz.n % 3],
			wrongPct: crowdWrong(roundId, res.answer) };
		postGuess({ roundId, choice, tellZone });
		phase = 'revealed';
		setTimeout(() => { lastResult = null; phase = 'guess'; }, 1500);
	}
	const shownRound = $derived(phase === 'revealed'
		? rounds.find((r) => r.id === lastResult.roundId) : quiz.current);
</script>

{#if shownRound}
	<div class="quiz" style:--reveal={lastResult ? (lastResult.answer === 'dem' ? '#5588d5' : '#d5564c') : null}>
		{#if phase === 'tell'}<p class="prompt">Before we tell you — tap the thing that gave it away.</p>{/if}
		<ClipCard round={shownRound} revealed={phase === 'revealed'}
			onzone={phase === 'tell' ? zone : null} />
		{#if phase === 'revealed'}
			<p class="verdict">{lastResult.verdict} It’s from <b>@{shownRound.account}</b>.
				{#if lastResult.wrongPct !== null}{lastResult.wrongPct}% of readers got this wrong.{/if}</p>
		{:else if phase === 'guess'}
			<div class="buttons">
				{#each quiz.buttonOrder as side}
					<button class={side} onclick={() => tap(side)}>{LABELS[side]}</button>
				{/each}
			</div>
		{/if}
	</div>
{:else}
	<p class="done">That’s every clip we prepared. {scoreSentence(quiz.n, quiz.correct)}</p>
{/if}
<p class="score" aria-live="polite">{scoreSentence(quiz.n, quiz.correct)}</p>

<style>
	.buttons { display: flex; gap: 10px; justify-content: center; margin-top: 12px; }
	button { flex: 1; max-width: 190px; padding: 14px 8px; border: none; border-radius: 22px;
		color: #fff; font-weight: 700; font-size: 15px; }
	button.dem { background: #5588d5; } button.rep { background: #d5564c; }
	.verdict, .prompt { text-align: center; min-height: 44px; margin-top: 12px; }
	.score { text-align: center; background: #fffcd9; padding: 6px 10px; border-radius: 6px;
		max-width: 390px; margin: 10px auto; }
</style>
```

- [ ] **Step 3: Mount in `+page.svelte`** — replace demo content with intro copy block (draft below, PT rewrites) + `<QuizModule rounds={quiz.rounds} seeded={quiz.seeded} bind:quiz={quizState} />`. Draft intro (~90 words): "Trump strutting into a party to his own walk-on music? Easy — that's the White House's TikTok. But a wig-edited JD Vance lip-syncing Radiohead's 'Creep'? Careful. Since losing in 2024, the Democrats' official accounts have gone what the internet calls dark woke — as crude, meme-brained and merciless as anything the other side posts. We pulled clips from both parties' official TikTok accounts and stripped the names off. See if you can tell who posted what. Most people can't."

- [ ] **Step 4: Verify in browser** — `npm run dev -- --open`, phone-size viewport: clip loops muted, buttons randomized (clear localStorage, reload twice), reveal border flashes right color, auto-advance ~1.5s, score sentence updates, tell round interrupts every marked round, done state at pool end. Fix until true.

- [ ] **Step 5: Commit** — `git commit -am "feat: quiz module with TikTok shell, tell-tap, crowd reveal"`

---

### Task 10: Interlude charts (EraStepline, ProfanityCrossover, ToxicityPays, moderation stat)

**Files:**
- Create: `src/lib/components/charts/EraStepline.svelte`, `ProfanityCrossover.svelte`, `ToxicityPays.svelte`
- Modify: `src/routes/+page.svelte`

**Interfaces:**
- Consumes: `toplines.json`.
- Produces: three self-contained SVG chart components, each `{ data }` prop, 390px-first, with a `pending` visual state (grey bars + "awaiting classification" note).

- [ ] **Step 1: Build the three components.** Shared pattern — d3 scales, plain Svelte-rendered SVG (no d3 DOM mutation), `width` via `bind:clientWidth`, height 220. `EraStepline`: x = three eras (band), y = attack share %, one step-line per account group, grey + note when `pending`. `ProfanityCrossover`: monthly line per side from `profanityByMonth`, annotate crossover month (first month dem > rep after 2025-01: compute in component). `ToxicityPays`: paired horizontal bars (attackMedian vs otherMedian) per account within selected era; format views with `d3.format('.2s')`. Each ~60 lines; follow the axis/label idiom in `src/lib/components/demo/LineChartScrolly.svelte`.

- [ ] **Step 2: Mount in page with interlude copy slots.** Draft copy marks each stat's source and a bracketed `[pending full classification]` tag where `pending: true`; the moderation stat renders as a big-number block: "20 restrictions · 1 deletion · 5,637 posts".

- [ ] **Step 3: Verify at 390px** — charts legible, no horizontal scroll, pending states readable.

- [ ] **Step 4: Commit** — `git commit -am "feat: interlude era charts with pending states"`

---

### Task 11: Balloon glyph + HeroBalloon scroll scene

**Files:**
- Create: `src/lib/balloon.js`, `src/lib/balloon.test.js`, `src/lib/components/Balloon.svelte`, `src/lib/components/HeroBalloon.svelte`
- Modify: `src/routes/+page.svelte`

**Interfaces:**
- Consumes: `balloons.json` (hero = `people[0]`, expected donald-trump), `static/faces/donald-trump.png`, GSAP ScrollTrigger, `svelte/motion` Spring.
- Produces: `balloonPath(r, plump)` pure fn; `<Balloon person r plump face />` glyph reused by Task 13's pack; `<HeroBalloon person />` 400vh scrub scene.

- [ ] **Step 1: Write failing test for the path generator**

```js
// src/lib/balloon.test.js
import { describe, it, expect } from 'vitest';
import { balloonPath, inflationAt } from './balloon.js';

describe('balloonPath', () => {
	it('returns a closed path scaled by r', () => {
		const p = balloonPath(100, 1);
		expect(p).toMatch(/^M /); expect(p).toMatch(/Z$/);
		expect(balloonPath(50, 1)).not.toBe(p);
	});
});
describe('inflationAt', () => {
	const weekly = [ { w: '2024-11-04', own: 2, opp: 3 }, { w: '2024-11-11', own: 1, opp: 4 } ];
	it('cumulates to progress point', () => {
		expect(inflationAt(weekly, 0)).toEqual({ own: 0, opp: 0, total: 0 });
		expect(inflationAt(weekly, 0.5)).toEqual({ own: 2, opp: 3, total: 5 });
		expect(inflationAt(weekly, 1)).toEqual({ own: 3, opp: 7, total: 10 });
	});
});
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement `src/lib/balloon.js`**

```js
export function balloonPath(r, plump = 1) {
	// teardrop balloon centered at 0,0; plump 0.75 limp -> 1.15 overinflated
	const w = r * 0.82 * plump;
	const h = r * (1.9 - plump * 0.75);
	const knot = r * 0.08;
	return [
		`M 0 ${-h}`,
		`C ${w} ${-h}, ${w * 1.05} ${h * 0.25}, ${knot} ${h}`,
		`L ${-knot} ${h}`,
		`C ${-w * 1.05} ${h * 0.25}, ${-w} ${-h}, 0 ${-h}`,
		'Z'
	].join(' ');
}

export function inflationAt(weekly, t) {
	const upto = Math.floor(t * weekly.length);
	let own = 0, opp = 0;
	for (let i = 0; i < upto; i++) { own += weekly[i].own; opp += weekly[i].opp; }
	return { own, opp, total: own + opp };
}
```

- [ ] **Step 4: Run tests, verify PASS.**

- [ ] **Step 5: Build `Balloon.svelte`** — props `{ person, r, plump = 1, labeled = false }`. SVG group: `<clipPath id="clip-{person.slug}"><path d={balloonPath(r, plump)}/></clipPath>`; inside the clip two `<rect>`s — red bottom (own share height) and blue top (opp share) using `person.totals.oppShare`; balloon outline path stroke #222; ellipse highlight top-left, 0.25 opacity white (latex sheen); string: quadratic path below knot. **Face is an HTML `<img>` sibling absolutely positioned over the SVG center** (parent has `position: relative`), `style:transform: translate(-50%,-55%) scale({0.5 + plump * 0.55}, {0.35 + plump * 0.85})` — vertical stretch outpaces horizontal as it inflates; `will-change: transform`. Register shading: if `ownRegister/oppRegister` non-null, deepen rect colors via `d3.interpolateRgb` toward saturated ends by |register|/3; else flat colors (partial-data state, no code change later).

- [ ] **Step 6: Build `HeroBalloon.svelte`** — a `400vh` section; sticky inner viewport (`position: sticky; top: 0; height: 100svh`). In `onMount`: `gsap.registerPlugin(ScrollTrigger); const st = ScrollTrigger.create({ trigger: section, start: 'top top', end: 'bottom bottom', scrub: 0.4, onUpdate: (self) => (t = self.progress) });` return `() => st.kill()`. `t` is `$state`; derived: `const inf = $derived(inflationAt(person.weekly, t))`, `r = $derived(rScale(Math.sqrt(inf.total)))`, `plump = $derived(0.78 + 0.37 * t)`; Spring wraps `r` (`import { Spring } from 'svelte/motion'`) so weekly jumps read as puffs. Ticker div: date at `t` (index into weekly), post count, opp-air %. Annotations: array `[{at: progressOf('2024-11-06'), text: 'Election night...'}, inauguration, the 39.2M restricted post, republicans launch 2026-02]` — `progressOf(date)` = index of week / weeks.length; render as absolutely-positioned caption cards fading in within ±0.06 of `t`. GSAP owns nothing Svelte renders — it only feeds `t`.

- [ ] **Step 7: Verify in browser at 390px** — limp balloon at scene top, inflates on scroll with face stretching, split-fill boundary moves, annotations appear at beats, 60fps-ish on device emulation (Performance panel: no layout thrash; transforms only).

- [ ] **Step 8: Commit** — `git commit -am "feat: balloon glyph + hero scroll-scrub inflation scene"`

---

### Task 12: BalloonInterior — canvas semantic-zoom field + tooltip

**Files:**
- Create: `src/lib/components/BalloonInterior.svelte`, `src/lib/components/TooltipCard.svelte`
- Modify: `src/routes/+page.svelte`, `src/lib/components/HeroBalloon.svelte` (enter button)

**Interfaces:**
- Consumes: `interior/donald-trump.json`, atlas jpgs, d3-zoom.
- Produces: `<BalloonInterior data onclose />` full-screen overlay; opens from a "Look inside ▸" button after HeroBalloon completes (`t > 0.95`). **Fallback (timeboxed to 2 days):** if zoom perf fails on a real iPhone, `<InteriorGallery data />` — emotion-sectioned swipeable thumbnail rows using the same JSON.

- [ ] **Step 1: Build the canvas field.** Fixed-position overlay div; single `<canvas>` sized to `devicePixelRatio`; load atlas images into `Image[]`; `d3.zoom().scaleExtent([1, 8]).on('zoom', (e) => (transform = e.transform))` bound to the canvas selection; render loop via `requestAnimationFrame` gated on a dirty flag. Draw per node at `transform.apply([n.x * W, n.y * H])`: if `transform.k < 3` — `ctx.fillStyle = n.color; ctx.globalAlpha = 0.55; ctx.filter = 'blur(6px)'` circles r=10 (smoke plumes; set filter once per frame not per node); else — `ctx.drawImage(atlas[n.ai], n.ax * 96, n.ay * 96, 96, 96, x - s/2, y - s/2, s, s)` with `s = 14 * transform.k`, plus 2px side-colored border. Emotion labels: draw cluster names at centroid when `k < 3`.

- [ ] **Step 2: Tap → tooltip.** On `click`/`touchend` (no drag): invert transform, nearest node within 24px → `selected = node`; `<TooltipCard node onclose>` — bottom sheet (`position: fixed; bottom: 0`, max-height 55svh, scrollable): claim (bold), intent, register chip (colored −3…+3 or "unclassified" when null), `@account` + date + views (`d3.format('.2s')`), dunk line in quotes if present, link `https://www.tiktok.com/@{account}/video/{id}`.

- [ ] **Step 3: Wire open/close** — "Look inside the balloon ▸" button in HeroBalloon final state; ✕ closes overlay, `document.body.style.overflow` toggled.

- [ ] **Step 4: Verify on device emulation + a real iPhone via `npm run dev -- --host`** — pinch zoom smooth, blobs resolve to thumbnails at k≥3, tooltip data correct against a spot-checked JSON node. If jank is unfixable in the timebox: build `InteriorGallery` fallback and swap.

- [ ] **Step 5: Commit** — `git commit -am "feat: balloon interior semantic-zoom field with tooltip cards"`

---

### Task 13: BalloonPack reveal + FeedOutro

**Files:**
- Create: `src/lib/components/BalloonPack.svelte`, `src/lib/components/FeedOutro.svelte`
- Modify: `src/routes/+page.svelte`

**Interfaces:**
- Consumes: `balloons.json` (top 12), `Balloon.svelte`, existing `Scroller.svelte` (index binding), quiz score from `QuizState`, `toplines.json` moderation block, quiz clips for the feed.
- Produces: guided pack reveal + endless tinted feed ending.

- [ ] **Step 1: BalloonPack.** `d3.pack().size([w, h]).padding(6)` over `hierarchy({children: people})` sum = `totals.posts`; render `<Balloon>` per node at `{x, y, r}` (plump fixed 1.0; `labeled` shows name + oppShare% under each). Wrap in repo `Scroller` with 4 foreground steps: (1) all balloons enter (scale-in via Spring, staggered) + header stat "**{people.length} people** account for **{share}%** of everything both parties posted" (compute share = sum top-12 posts / total posts, passed via balloons.json `meta`); (2) highlight Trump (others dim to 0.25 opacity): "his enemies inflate him more than his friends do — {oppShare}% opposition air"; (3) highlight own-side-only balloons (oppShare < 0.2): platformed, not attacked; (4) free-explore hint. Tap any balloon → if `interior/{slug}.json` exists open BalloonInterior, else TooltipCard-style summary (totals + registers).

- [ ] **Step 2: FeedOutro.** Full-viewport section: `overflow-y: auto; scroll-snap-type: y mandatory` container of shuffled quiz-clip `<video>`s (each `scroll-snap-align: start; height: 100svh`), IntersectionObserver plays the visible one, pauses others. After the 3rd snap, float the toggle button "show me who posted these"; on tap set `tinted = true` → each cell gets an inset box-shadow + corner tag (`@democrats` blue / `@whitehouse` red). Closing caption fixed over feed once tinted: "170 million Americans watch this feed. You guessed right {quiz.correct} of {quiz.n} times. TikTok doesn't guess at all — {moderation.restricted} restrictions, {moderation.deleted} deletion, {moderation.total.toLocaleString()} posts." Then methodology `<details>` + credits (static copy slot; includes the "what this quiz can't tell you" paragraph and data-pending disclosures).

- [ ] **Step 3: Verify** — pack legible at 390px (12 balloons, faces visible), steps advance, feed snaps and autoplays muted, toggle tints, caption pulls live quiz numbers (play quiz first in same session).

- [ ] **Step 4: Commit** — `git commit -am "feat: balloon pack reveal + endless feed outro"`

---

### Task 14: Assembly, copy pass, QA, deploy

**Files:**
- Modify: `src/routes/+page.svelte` (final scene order + copy), `src/app.html` (meta/OG tags), `Makefile`
- Delete: `src/routes/demo/`, `src/lib/components/demo/`, `src/lib/data/regional-metrics.json`, `us-states.json`, `cities.json` (starter demo data)

- [ ] **Step 1: Final page order** — intro → QuizModule → interlude (copy + 3 charts + moderation block) → HeroBalloon → (interior via button) → BalloonPack → FeedOutro → methodology. Remove demo route/components; `npm run build` must stay green.

- [ ] **Step 2: Copy pass by PT** — every draft copy slot is marked `<!-- COPY: PT -->`; PT rewrites in-place. Bracketed pending stats resolve after tomorrow's pipeline re-run (`python -m pipeline.build_balloons && python -m pipeline.build_interior && python -m pipeline.build_toplines`).

- [ ] **Step 3: Run all tests** — `npm test && pipeline/.venv/bin/pytest pipeline/tests -v` — all green.

- [ ] **Step 3.5: Face rights check** — YouGov portraits currently on the balloons were fetched as internal face-ID references; confirm republication rights or swap to public-domain official portraits (congressional/White House) by replacing files in `static/faces/` — same filenames, no code change. Record the outcome in the methodology note.

- [ ] **Step 4: Device QA on a real iPhone** (`npm run dev -- --host`, phone on same wifi): quiz tap targets ≥44px, videos autoplay muted (iOS requires `playsinline muted` — verify), hero scrub smooth, interior pinch, feed snap, localStorage persistence across reload, offline crowd fallback (turn off wifi mid-quiz: seeded stats show, no errors).

- [ ] **Step 5: Pilot seed** — deploy staging (`make github` or `npx vercel`), send to ~10 classmates, verify Redis counters rise (`curl $VITE_CROWD_URL/api/stats?rounds=...`).

- [ ] **Step 6: Deploy** — `make github` (BASE_PATH set per Task 1). Verify live URL on phone. Commit.

---

## Self-review notes

- **Spec coverage:** Scene 0 → Tasks 2/3/8/9; Scene 1 → Tasks 6/10; Scene 2 → Tasks 4/11; Scene 3 → Tasks 5/12; Scene 4 → Task 13; Scene 5 → Task 13; crowd stats → Task 7; pipeline re-run upgrade → Tasks 4/5/6 (pending markers); methodology/reflexivity → Task 14. Sombrero audit + PT hand-pick → Task 2 Step 5. Faces/rembg → Task 4. Not in scope (spec allows): free-explore interiors for all 12 balloons (only slugs with generated JSON open the field; others get summary cards) — generate more interiors post-deadline by re-running `build_interior` per slug.
- **Known deviation:** balloon shape is parametric (`balloonPath(r, plump)`) rather than hand-drawn keyframes + d3.interpolate — same visual goal, no asset dependency; revisit only if the silhouette disappoints.
- **Type consistency check:** `quiz.json` fields (`id/answer/account/caption/sound/clip/poster/tell`) match ClipCard/QuizModule usage; `balloons.json` `totals/weekly` match `inflationAt`/Balloon props; `interior` node fields (`ai/ax/ay/x/y/color/claim/intent/register/dunk`) match canvas draw + TooltipCard; crowd API shapes match client. `QuizState.pick/guess/logTell` used consistently in Tasks 8/9.
