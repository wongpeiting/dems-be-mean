# Archived: tiktok-cast build

An interactive on the "dark woke" convergence of the two US parties' official
TikTok accounts. **Archived 2026-07-14 — abandoned.**

## Why it was shelved
- The balloon metaphor never read as balloons and the face-stretch wasn't convincing.
- The hero visualization lacked a sharp editorial point; the interlude charts were decorative.
- The emotion-cloud layer was slow and hidden behind a click instead of revealed by scrolling.

## What's worth keeping
- **The Python pipeline** (`tiktok-cast-build/pipeline/`) turns the upstream
  `all-of-pol-tiktok` classification into real analysis: `balloons.json`,
  `interior/*.json`, `toplines.json`. Re-run: `build_balloons`, `build_interior`,
  `build_toplines`.
- **The finding that actually lands:** the Democrats' official TikTok starred
  Donald Trump in **1,198 videos — more than their five biggest own-side figures
  combined (974).** The opposition made its enemy its main character.
- **The strongest visual direction** reached before shelving: an editorial
  circle-pack (faces clipped into circles) on a *built-up-by-own-side ↔
  torn-down-by-opponents* axis. See `tiktok-cast-build/src/routes/proto-pack/`.

## Full history
Everything, with complete commit history, is on the git branch **`build`**
(tip `6c51a6c`). Recover with `git checkout build`. This folder is a flat
snapshot for browsing without git.
