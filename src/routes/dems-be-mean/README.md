# `dems-be-mean` — the "field heats up over time" hero

An essential-words-style scattered word field, retooled to carry one argument:
the @democrats TikTok account's dunk vocabulary **got meaner in kind** after the
2024 loss, while **Trump crowded out every other target**. Scroll runs a clock;
the field ignites cool→hot in real time order.

## Files

| File | Role |
|---|---|
| `+page.svelte` | Header, the `<Scroller>` wiring, scroll captions, closing methodology. Owns the **playhead remap** (`KF_P`/`KF_T`). |
| `HeatField.svelte` | The sticky graphic: the word field, HUD date, the two gauges, now-line + loss marker. Takes `data` + `progress` (the playhead). |
| `$lib/data/dunk_hero.json` | Generated data (52 words + 53 monthly rows). Regenerate, don't hand-edit. |

## What each visual channel means (all grounded, nothing decorative)

It's a scatterplot of **meanness over time**:

- **x-position (left→right)** = **chronological order**. Words are spread *evenly
  by rank* of their median usage date (`xr`), earliest at left. Rank (not raw date)
  so the field fills the width instead of clumping on the right, where ~2/3 of the
  distinctive words are post-loss. Left→right is honest as ordering, not as linear
  calendar distance.
- **y-position (bottom→top)** = **meanness**. Each word's score is the mean
  `register` (harshness, −3 warm … +3 contemptuous) of the dunk lines that use it.
  Because an all-dunks corpus clusters at the harsh end, y is spread by **rank of
  that score** (`yr`) — harsher words ride higher. Ordering is honest; absolute
  spacing is not.
- **size** = how often the word appears (`√count`).
- **colour** = none. Words are a uniform off-white; the meanness signal lives on
  the y-axis, not in colour.
- **ignite order** = same as x (rank/time); words stay hidden until the now-line
  (the scroll clock) reaches their x, then fade in.
- **gauges** = separate, account-level monthly rates from `monthly_series.csv` —
  `attack_share` and `trump_main_share` — as a **3-month trailing average** so a
  tiny-n month (e.g. Dec 2024, n=19) doesn't spike a gauge to a misleading 100%.

## Two honest liberties (pacing & spread, never the ordering)

- **Both axes are ranks, not raw values.** Raw dates clump right and raw register
  clumps high, so each axis is spread by *rank*. This preserves ordering
  (earlier-is-left, harsher-is-higher) while making the field legible. Absolute
  pixel distance ≠ absolute months or register points.
- **Caption pacing is tuned to the rank axis.** Only ~1/3 of the words are
  pre-loss, so the pre-loss caption steps are short and the post-loss ones tall
  (`vh` per step in `+page.svelte`) — that keeps each caption aligned with the part
  of the timeline on screen. A lead-in step lets the vocabulary rise on its own
  before the first caption box appears.

## Regenerate the data

The generator lives with the upstream analysis (it needs the raw corpus):

```
python3 ../../../../all-of-pol-tiktok/party_accounts/data/analysis/pudding_words/build_hero.py
```

It writes `dunk_hero.json` straight into `$lib/data/` (and a `hero_data.js`/JSON
copy beside the standalone prototype). Word-selection knobs: `POST_N`, `PRE_N`,
`MIN_COUNT`. The profanity glow list is `PROFANE` (auditable, edit inline).

## What it shows / doesn't show

Distinctiveness describes **this account in this dataset**, not Democrats in
general. The corpus is already filtered to dunks, so the piece shows how the
dunking **changed in kind** (institutional → personal/profane), not that the
account only started dunking. Dunk extraction and register calls are model
judgments over Stage-1 video descriptions, adjudicated by the author.
