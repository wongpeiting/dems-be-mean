# Archived: attention-river / scatter project

An interactive on how the TikTok cast + targets of attack shift over time across
@democrats (2022), @whitehouse (Aug 2025) and @republicans (Feb 2026), built on
the reusable scrolly flow-map kit. **Archived 2026-07-15 — abandoned.**

Went through several forms, none of which landed:
1. **Attention-pool beeswarm** — people as pools on a platformed↔attacked axis, ribbons from accounts, scroll = time. (Rejected: static snapshot, not travelled-through.)
2. **Vertical time-Sankey** (Hormuz-styled) — account→target streams flowing down through time, register colour, quarterly widths. (Closer, but not it.)
3. **Scatter** — every treatment a dot, x = register, y = time, colour = account.
4. **Face scatter** — dots replaced with subject face cutouts + account-colour rings; institutions as dots. (Final form; also rejected.)

## What's here
- `pipeline/attention.py` — aggregates `stage2_treatments.csv` into `attention.json`
  (monthly account→person flows) + `attention_points.json` (every treatment).
  Uses PT's authoritative `subject_aliases.json` for canonical-name merges.
- `pipeline/faces.py` — cuts circular face crops from the pol-face YouGov roster
  (roster-aware slug matching; ~55% of points get a face, the rest are institutions).
- `routes-attention/` — the Svelte routes (AttentionMap, VerticalFlow, Scatter).
- `data/`, `faces/` — the generated data + 148 face crops.

## Note
The reusable **flow-map kit** (`src/lib/scrolly/`, `src/routes/kit-demo/`) was kept
in the repo — only this project built on top of it was archived.

Full git history is on branch **`scrolly-kit`**. Recover with `git checkout scrolly-kit`.
