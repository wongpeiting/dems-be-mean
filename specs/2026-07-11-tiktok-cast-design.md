# TikTok Cast — Design Spec
*2026-07-11 · Wong Pei Ting · spun off from `all-of-pol-tiktok` (stage-2 classification running)*

## Premise

A mobile-first Svelte + D3 scrollytelling interactive arguing that the Democrats' adoption of "dark woke" and the Trump White House's native trolling style have made the two parties' TikTok content nearly indistinguishable — and that TikTok moderates almost none of it. The reader discovers this by failing a guessing game, then explores *who* both machines are inflating: a cast of characters rendered as balloons, pumped up over time by their own side's hype and their opponents' mockery.

**Form:** one continuous scroll, one route. Quiz → interlude → hero balloon → inside the balloon → the reveal (balloon pack) → the feed. Mobile is the design target; desktop is the adaptation.

**Deadline: ~2 weeks.** Build scope: quiz + interlude + hero balloon + collapsed interior layer + pack reveal + feed outro. Anything that slips ships as designed-mockup in the writeup.

---

## Scene 0 — The Game

Modeled on NYT's "Trump Fridge vs Biden Fridge" (Oct 2020, John Keefe) — mechanics recovered from its unminified archived source.

**Editorial frame (~90 words, NYT-style stereotype→doubt pivot):** *"Trump strutting to his own walk-on music? Easy — White House. But a wig-edited JD Vance lip-syncing Radiohead's 'Creep'? … Are you sure?"* One clause plants the thesis before play.

**Mechanics:**
- One fixed module, not a scroll-quiz. A **muted 2–3s looping clip** inside a recreated TikTok UI shell — caption, sound bar with track name, emoji visible; handle/avatar/watermark redacted. The shell is deliberate: a TikTok's tells are semiotic layers (song, caption, emoji, edit style), not just pixels.
- Two pill buttons below, **order randomized per session**: 🔵 Democrats · 🔴 White House / GOP.
- Tap → border flashes answer color + one-line verdict + **live crowd bar** ("64% of readers got this wrong") → auto-advance after 1.5s. No Next button. ~4s per round.
- **No fixed round count.** Deep shuffled pool; reader quits by scrolling on. Score is a live prose sentence below the module, grammatical at any N ("You've guessed 6 times and got 3 right — a coin flip."). Persists via localStorage.
- Every guess POSTs immediately — partial play still feeds crowd stats.
- **Tap-the-tell (every 3rd round):** before the reveal — "Tap what made you think it's the Democrats." Tappable zones = video area, caption, sound title, emoji, or a "just vibes" chip; zone + coordinates logged. Yields the crowdsourced perceived-tells dataset: what readers *think* distinguishes the parties vs. what actually does. Rounds with rich `on_screen_text[]` are preferred for these.

**The pool:** Cluster 34 (the 401-post embedding-verified convergence zone) ∪ posts whose Stage-1 descriptions volunteer absurdity language ("absurd": 154 hits @democrats, 22 @whitehouse, 6 @republicans — itself a finding; note it is free-text, not a schema field). Candidate sheet ~60 → PT hand-picks ~24, balanced red/blue, curated for dark-woke snark. Confirmed candidates: @democrats' Vance-in-a-wig "Creep" edit (`7596097777050848567`), Vance Hannah Montana wig edit (`7621282572986813709`). To audit: the Schumer/Jeffries sombrero set — include only a restrained one (the famous ones carry recognition risk from news coverage); skip if all too notorious.

## Scene 1 — The Interlude

Prose + small charts. **Eras, not corpus averages** — three windows: ① @democrats pre-Nov 6 2024 (creator-native, celebratory) → ② post-Trump-win (the dark-woke turn) → ③ head-to-head (@whitehouse joins Sep 2025; @republicans Feb 2026). Attack share, crudeness, profanity, mechanism adoption each shown as *the turn* (before/after step-lines).

Charts:
1. **EraStepline** — attack share per era per account.
2. **ProfanityCrossover** — @democrats overtaking @republicans post-Feb 2025 (echoes WaPo's tone reporting, quantified per-post).
3. **ToxicityPays** — original HKS-style calc on our own data: scraped engagement metadata × our register/crudeness/profanity classifications → median views, attack vs. non-attack, per era per account (medians, not means — one 39M viral wrecks means). HKS Misinformation Review showed toxicity earns ~2.3% more engagement across political TikTok; nobody has shown it for the parties' own accounts. Original chart.
4. **The moderation void** — TikTok's GPPPA policy bans party accounts from ads/monetization but holds organic content to only baseline community guidelines; no elevated standard exists. In our corpus: 20 restrictions, one deletion, 5,637 posts. No major outlet has done this story; say so.

Scaffolding (researched, citable): term arc — AOC "cry more" (Jan 2025) → Guardian op-ed (Jan 30 2025, Rothpletz) → NYT christening (Apr 21 2025, Jack Crosbie, Styles) → Newsom's GCN institutionalization → Slate retrospective (Feb 2026). DNC on record at NOTUS: "it's all about dunks." WaPo Jul 2025 tone analysis. Critiques: GQ (Press-Reynolds), NY Mag (Barkan). Mechanism: HKS Misinformation Review (Biswas/Sabet/Lin 2025); audience capture (Bhogal); Postman.

## Scene 2 — Meet the Balloon (hero: Trump)

A limp, deflated balloon with Trump's face printed on it. **Scroll = time**, Nov 2024 → today, over ~4 viewport heights. Every post where he's a main character is a puff of air; the balloon swells and **the face stretches with the latex** (Alvin Chang distortion — the thesis made physical).

**Split-fill encoding (decided):** balloon size = main-character post count; fill split two-tone — **blue air** from @democrats/@dccc/etc. (mockery, negative register) vs **red air** from @whitehouse/@republicans (hero-worship). Register (−3…+3) drives shade intensity. Ticker shows post count + opponent-air %.

Pinned scroll-step annotations: election night, inauguration, the 39.2M-view TikTok-restricted "disgusting" post, @republicans' Feb 2026 launch.

Trump is the only defensible hero: #1 character in his opponents' feed (781 @democrats videos — more than double Harris) *and* his own side's hero-worship object. Inflated from both nozzles.

## Scene 3 — Inside the Balloon

Tap → camera dives in. Interior is **one collapsed zoomable layer** (emotion clouds and media clouds are the same field at different zoom depths, à la soot.com): every Trump post is a node, position-clustered by emotion (`emotions_signaled`), tinted by emotion color. Zoomed out = plumes of colored smoke; zoom in = actual post stills. Tap a post → tooltip card: central claim, intended effect, register chip, who posted, verbatim `dunk_line` if `has_dunk`, date, link. ✕ to surface.

Honesty note: `emotions_signaled` is post-level, not per-person — the plumes are "emotions of posts where X is a main character," and the copy says so.

## Scene 4 — The Reveal

Zoom out past the latex: the hero balloon shrinks into a **balloon-pack of the top ~12 cast members**, faces printed on every one, all split-filled. Header stat: "[N] people account for [X]% of everything both parties posted" (cast concentration — the face-card lineage). Guided scroll-highlights: Trump biggest and majority-blue (his enemies inflate him more than his friends) · Harris/Obama inflated almost purely by own-side platforming · Musk/Vance as mock-targets · Leavitt/Mamdani fresh balloons still being blown up (exact contrasts pending full stage-2 data). Then free-explore: tap any balloon → same interior treatment (data permitting; minimum = tooltip summary).

## Scene 5 — The Feed

No cliché kicker. The piece **dissolves into a simulated For You feed**: real posts from both sides, unlabeled, interleaved, scroll-snap, endless. After a few swipes a floating toggle appears: **"show me who posted these"** — tap, every clip tints red or blue. The reader has been inside the converged feed the whole time. Closing caption over the still-scrolling feed: *"170 million Americans watch this feed. You guessed right [n] of [m] times. TikTok doesn't guess at all — 20 restrictions, one deletion, 5,637 posts."* Methodology + credits.

Gratification is never withheld: every quiz round reveals instantly; Scene 5 is a reprise, not the result.

---

## Architecture

Base: **the-pudding/svelte-starter** (Svelte 5 runes, SvelteKit 2, d3 v7, ships production `Scrolly.svelte`). Existing repo scaffold (`sv` minimal template) gets the starter's helpers grafted in or is re-scaffolded — decide at build start. Static adapter, `docs/` is the GitHub Pages build target (spec lives in `specs/` for this reason).

Animation: **GSAP 3.13+ (fully free incl. ScrollTrigger/MorphSVG)** — ScrollTrigger `scrub` drives the hero balloon; `svelte/motion` Spring supplies latex overshoot. Convention: D3 does math, Svelte owns the DOM, GSAP animates; never let Svelte reactivity and GSAP contend for the same attribute; GSAP contexts mounted in `$effect`, killed on teardown.

| Component | Job |
|---|---|
| `QuizModule` | ClipCard (TikTok shell + muted loop) · randomized GuessButtons · RevealBar (answer + crowd %) · TellTap overlay every 3rd round |
| `ScoreSentence` | live prose score, any-N grammatical, localStorage |
| `EraStepline` / `ProfanityCrossover` / `ToxicityPays` | interlude charts |
| `HeroBalloon` | Scrolly + ScrollTrigger scrub, Nov 2024→today |
| `BalloonInterior` | canvas + d3-zoom semantic zoom field |
| `BalloonPack` | d3.pack + interpolateZoom reveal |
| `FeedOutro` | scroll-snap FYP + who-posted toggle |

State: one runes store (guesses, score, crowd cache).

**Backend (the only one):** one serverless function. `POST /guess {roundId, choice, tellZone?, xy?}` → KV increment; `GET /stats` → aggregate JSON cached 60s. Seeded with pilot-run data so crowd bars never read empty. (Live crowd stats decided over static-seeded.)

## Balloon rendering spec

- **Shape:** 3–4 hand-drawn balloon keyframe paths with identical command structure → `d3.interpolate(progress)`; Spring on progress = wobble; string sways on the same spring. No flubber needed (same topology).
- **Split-fill:** balloon path as clipPath over two stacked color fields; boundary height = own-side share, animated with time.
- **Face:** transparent PNG per politician on an **HTML layer above the SVG**, 3-slice vertical stretch via CSS transforms only (compositor, 60fps); radial highlight overlay for latex sheen. **Never `feDisplacementMap`** — Safari rasterizes SVG filters per frame; keep animated transforms out of SVG on mobile.
- **Puffs:** heavy post-weeks land as Spring scale-pulses — inflation reads as breaths.
- **Pack:** `d3.pack()` only computes `{x, y, r}`; draw balloon glyphs at those coords — standard practice, no library gap.

## Interior field spec

Single canvas, d3-zoom (pinch/drag). Below threshold `k`: soft emotion-tinted blobs (smoke). Above: `drawImage` from **pre-composited thumbnail atlases** (PixPlot pattern). Cluster positions computed offline in Python, shipped as JSON. Tooltip is an HTML overlay.
**Timeboxed fallback:** if canvas zoom fights us by day 12, tap-balloon opens a swipeable gallery sectioned by emotion. Less magic, same content, ships.

## Data pipeline (Python, upstream in all-of-pol-tiktok)

Stage-2 rollout: **already running** (launched 2026-07-11); balloons consume `stage2_treatments.csv` when it lands.

1. **Quiz curation:** Cluster 34 ∪ absurd-language grep → ~60-candidate sheet → PT picks ~24 → ffmpeg per clip: crop watermark, 2–3s loop, mute, 480px, h264+webm (~300KB) + poster jpg.
2. **Balloon aggregation:** treatments → weekly cumulative counts per (politician, side, register bucket) → `balloons.json`.
3. **Interlude notebook:** era-split toplines + ToxicityPays calc → `toplines.json`.
4. **Atlas build:** frame grabs → sprite sheets per balloon; emotion-cluster layout offline.
5. **Pilot seed:** classmates play staging; guesses seed crowd stats.

## Build order (2 weeks)

| Days | Work |
|---|---|
| 1–2 | scaffold, data contracts (JSON schemas), quiz curation sheet |
| 3–5 | quiz end-to-end: clips, shell, counter, crowd bars, tap-the-tell |
| 6–8 | hero balloon scrub scene |
| 9–10 | interlude charts + copy |
| 11–12 | interior field (timeboxed; fallback ready) |
| 13 | pack reveal + feed outro |
| 14 | real-iPhone Safari QA, pilot seeding, methodology note |

## Risks & mitigations

- **Stage-2 lands late / sparse for @democrats** → hero balloon runs on WH treatments + hand-coded Dem sheets (2,352 gold posts) as interim air supply.
- **Canvas zoom perf on mobile** → gallery fallback (above).
- **Clip weight** → lazy-load + unload offscreen videos via IntersectionObserver; posters first.
- **Recognition-risk quiz rounds** → curation pass screens for news-famous posts (sombrero rule).
- **Reflexivity backlash** (NYT fridge ate a classism critique) → methodology includes a "what this quiz can't tell you" section: what muted 3-second clips can't show, sampling choices, LLM classification limits.

## Key references

- NYT fridge quiz (archived + source-recovered mechanics) · Alvin Chang, "24 hours in an invisible epidemic" (Pudding, 2023) — parameterize vectors, don't pixel-warp · soot.com (zoom semantics) · Bostock zoomable circle packing · PixPlot (atlas + LOD architecture).
- Dark woke bibliography (full annotated list in project notes): Crosbie/NYT Apr 2025 · Rothpletz/Guardian Jan 2025 · Slate Feb 2026 · Knowles & Sidhom/WaPo Jul 2025 · Roarty/NOTUS Jun 2025 · Press-Reynolds/GQ · Barkan/NY Mag · Biswas et al./HKS Misinformation Review 2025 · Biswas et al./ICWSM 2025 · Bhogal audience capture · TikTok GPPPA policy pages.
