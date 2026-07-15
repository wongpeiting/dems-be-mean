# sv

Everything you need to build a Svelte project, powered by [`sv`](https://github.com/sveltejs/cli).

## Creating a project

If you're seeing this, you've probably already done this step. Congrats!

```sh
# create a new project
npx sv create my-app
```

To recreate this project with the same configuration:

```sh
# recreate this project
npx sv@0.15.3 create --template minimal --no-types --add prettier --install npm class-svelte-starter
```

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```sh
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```sh
npm run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment.

---

## TikTok Cast

**What it is:** An interactive quiz and data story examining how both parties' official TikTok accounts have converged on the same crude, meme-brained register. Readers are shown clips stripped of party labels and asked to guess who posted them. The piece then reveals the structural patterns — profanity crossover, toxicity dividend, near-absent moderation — through scrollytelling charts, balloon glyphs, and a canvas interior field.

### Pipeline re-run (when full stage-2 LLM coverage lands)

Re-generate all JSON data assets with:

```sh
pipeline/.venv/bin/python -m pipeline.build_balloons
pipeline/.venv/bin/python -m pipeline.build_interior
pipeline/.venv/bin/python -m pipeline.build_toplines
```

Then `npm run build` to pick up new data.

### Quiz curation flow

`src/lib/data/quiz.json` is currently a **STUB** (placeholder rounds, no real clips). To produce real clips:

1. Run the curation script to produce candidates: `pipeline/.venv/bin/python -m pipeline.curate_quiz` — writes `pipeline/out/quiz_candidates.csv`.
2. **Human step (PT):** review the candidates CSV and save ~24 chosen rows as `pipeline/picks.csv` (same columns plus a `tell` bool column — set `tell=true` on every ~3rd row to flag the give-away clip in a sequence).
3. Encode clips and write real quiz.json: `pipeline/.venv/bin/python -m pipeline.build_quiz` (requires ffmpeg). This replaces the STUB.

**Note:** The OG image URL in `src/app.html` is a relative path (`/og.png`). It must be changed to an absolute `https://` URL before publishing, otherwise social-media preview cards will not load the image.

### Crowd backend

See `crowd/README.md` for Vercel serverless + Upstash Redis deploy instructions. Set `VITE_CROWD_URL` in `.env` after deploying.

### DEFERRED — requires human action

- **Copy passes** (PT): every draft copy block in `src/routes/+page.svelte`, `src/lib/components/BalloonPack.svelte`, and `src/lib/components/FeedOutro.svelte` is marked `<!-- COPY: PT -->`. Rewrite in-place.
- **og.png**: supply a 1200×630 social share image at `static/og.png`. Referenced in `src/app.html` OG/Twitter tags.
- **Real video clips**: fill `pipeline/picks.csv`, run `build_quiz` + `encode_clips`, replace SMPTE color-bar stubs under `static/clips/`.
- **Vercel deploy**: `npx vercel deploy --prod` (or `make github` once BASE_PATH is confirmed). See `crowd/README.md` for crowd backend.
- **Real-device QA**: quiz tap targets ≥44px, video autoplay muted with `playsinline` on iOS, hero scrub, interior pinch zoom, feed snap, localStorage persistence, offline crowd fallback.
- **Face-image rights confirmation**: portrait images in `static/faces/` were fetched as internal references. Confirm republication rights or swap to public-domain official portraits (same filenames, no code change needed).
- **Pilot seed**: deploy staging, send to ~10 classmates, verify Redis counters rise.
