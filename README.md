# Dems Be Mean

After the 2024 loss, the Democratic National Committee's official TikTok account (@democrats) abandoned its institutional voice for the language of the reply guy: casual profanity, appearance jabs and a feed increasingly organised around attacking Donald Trump. This piece measures that transformation and the engagement it brought. Access it here: https://wongpeiting.github.io/dems-be-mean/

## Story arc

1. **Doomscroll opening**: A wall of @democrats TikTok clips recreates the experience of scrolling through the account and establishes its post-2024 tone, as a lead-in to the topic.
2. **The insult primer**: Readers type an insult (or use a randomiser) to calibrate what the piece considers "mean" before encountering the analysis.
3. **The word wall** (`HeatField.svelte`): Every distinctive insult and put-down is plotted by time and hostility. As readers scroll, the vocabulary unfolds alongside live counters tracking the share of attack posts and how often Donald Trump is the target.
4. **The Mean-o-meter** (`MeanSpark.svelte`): A running measure of the account's register, from −3 (hero-worship) to +3 (hostility), showing how @democrats changed over time and how it compares with @whitehouse and @republicans.
5. **The cast** (`CastPack.svelte`): A circle-pack visualisation reveals who dominates the account's attention, mapping its recurring heroes, villains and supporting characters.
6. **The payoff** (`PayoffSwarm.svelte`): A beeswarm chart shows median views increasing with each rung of crudeness, asking whether meanness is rewarded with attention.

## Data & methodology

The analysis covers every TikTok post by @democrats through July 9, 2026, with @whitehouse and @republicans as comparisons. In total, about 3,800 videos across three accounts were collapsed into a single dataset to understand which words define the account, when its tone turned, who it targets, and whether cruelty is rewarded with views. This is not possible without **signals2text**, a tool I'm developing that makes video analysable at scale. 

I developed *signals2text* after I found through my prior projects that it's not easy to get LLM to understand TikTok posts due to the many layers of signals, including captions, the text burned onto the screen, the spoken audio, emotional register, music, the visuals, meme formats, pop culture references, and face identification. These different layers tend to get lost in translation if they are not first turned into structured, queryable text, and treated as data that hold equal weight. As such, I created a pipeline that first gets an LLM (Gemini 2.5 Pro, in my case) to describe the intent and visual action in any TikTok post by watching the video along with all of the cleaned and prepared data streams. 

<img width="1102" height="621" alt="Image" src="https://github.com/user-attachments/assets/9ee59069-674b-463e-ae4e-d524b36779fc" /><img width="1102" height="629" alt="Image" src="https://github.com/user-attachments/assets/83dc9e9f-aa0a-4d6c-8abe-d9b3c0e051cd" />

Only after that is done did I pass the content through an LLM classifier that would label or sort each post according to the categories being studied, so a phenomenon can be counted, tracked over time, and charted. 

<img width="693" height="527" alt="Image" src="https://github.com/user-attachments/assets/d441ed65-7f17-4fc2-80da-3df8f3d79559" />

The ability to read the output of the LLM's Stage 1 descriptions (its interpretation after considering all embedded signals) made it easier for me to trust the LLM model's classification, given the auditability of its understanding versus how a human would interpret the same specimen of a TikTok post.

The end-to-end pipeline — transcription, OCR, and the LLM classification passes — will be published in a separate repository in time to come.

## Tech

- **[SvelteKit](https://kit.svelte.dev/)** (Svelte 5 runes) with `adapter-static` and **D3**
- A reusable `Scroller` component that pins a sticky graphic while step text drives a single `progress` (0 to 1) value.

### Key components

| File | Role |
|------|------|
| `HeatField.svelte` | The scrolling word wall + live HUD |
| `MeanSpark.svelte` | The Mean-o-meter register-over-time chart |
| `CastPack.svelte` | The circle-pack of subjects |
| `PayoffSwarm.svelte` | The crudeness-vs-views beeswarm (landscape + mobile-portrait) |
| `Montage.svelte` | The archived opening montage |

## Run it locally

```sh
npm install
npm run dev
```

Then open **http://localhost:5173/dems-be-mean**.

```sh
npm run build     # static build into ./build
npm run preview   # serve the production build
```
