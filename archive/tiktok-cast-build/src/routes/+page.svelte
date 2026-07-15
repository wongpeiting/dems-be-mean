<script>
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import QuizModule from '$lib/components/QuizModule.svelte';
	import quizData from '$lib/data/quiz.json';
	import toplines from '$lib/data/toplines.json';
	import EraStepline from '$lib/components/charts/EraStepline.svelte';
	import ProfanityCrossover from '$lib/components/charts/ProfanityCrossover.svelte';
	import ToxicityPays from '$lib/components/charts/ToxicityPays.svelte';
	import ModerationStat from '$lib/components/charts/ModerationStat.svelte';
	import HeroBalloon from '$lib/components/HeroBalloon.svelte';
	import balloons from '$lib/data/balloons.json';
	import BalloonInterior from '$lib/components/BalloonInterior.svelte';
	import interior from '$lib/data/interior/donald-trump.json';
	import BalloonPack from '$lib/components/BalloonPack.svelte';
	import FeedOutro from '$lib/components/FeedOutro.svelte';

	let quizState = $state(null);
	let mounted = $state(false);
	let interiorOpen = $state(false);
	let summarySlug = $state(null);

	const summaryPerson = $derived(
		summarySlug ? balloons.people.find((p) => p.slug === summarySlug) ?? null : null
	);

	onMount(() => {
		mounted = true;
	});
</script>

<main>
	<header class="intro">
		<h1>Can You Tell Who Posted This?</h1>
		<!-- COPY: PT -->
		<p>
			Trump strutting into a party to his own walk-on music? Easy — that's the White House's TikTok.
			But a wig-edited JD Vance lip-syncing Radiohead's "Creep"? Careful. Since losing in 2024, the
			Democrats' official accounts have gone what the internet calls dark woke — as crude,
			meme-brained and merciless as anything the other side posts. We pulled clips from both parties'
			official TikTok accounts and stripped the names off. See if you can tell who posted what. Most
			people can't.
		</p>
	</header>

	<section class="quiz-section">
		{#if browser && mounted}
			<QuizModule rounds={quizData.rounds} seeded={quizData.seeded} bind:quiz={quizState} />
		{:else}
			<p class="loading">Loading quiz…</p>
		{/if}
	</section>

	<section class="interlude">
		<!-- COPY: PT -->
		<p>
			The Democrats did not just lose the 2024 election — they changed their entire register. Before
			November, their TikTok was protest signs and policy clips. After inauguration day, posting
			volume held steady, but the tone shifted hard: by the time the White House entered the ring in
			August 2025, the Democrats were matching Republicans video for video, meme for meme. Dem posting
			across the three eras shows a sustained, deliberate escalation.
		</p>

		<EraStepline data={toplines.eras} />

		<!-- COPY: PT -->
		<p>
			Meanwhile the profanity rate crossed a threshold that once would have been unthinkable for
			official party communications. From August 2025, Democrats were swearing at least as often as
			Republicans — the first month both sides had data and Democrats led. TikTok's moderation
			apparatus has barely stirred: just 24 restrictions and 1 deletion out of 5,860 posts scraped.
			The platform is not policing this race to the bottom.
		</p>

		<ProfanityCrossover data={toplines.profanityByMonth} />

		<!-- COPY:PT — era changed to dem_pre: only era where attackMedian > otherMedian with n≥10 (dem_pre: 43,250 vs 32,200, n=634). WH headtohead: 992,800 vs 994,200 — essentially tied. -->
		<p>
			The platform rewards it — at least on the Democratic side. Before the 2024 election,
			the Democrats' attack posts earned a median 43,250 views against 32,200 for everything
			else: a 34% gap. Once the White House entered TikTok, that advantage disappeared —
			attack and non-attack posts performed almost identically, at roughly a million views
			each. The Democrats' own pre-election playbook is the clearest evidence that going
			after someone pays.
		</p>

		<ToxicityPays data={toplines.toxicityPays} era="dem_pre" />

		<ModerationStat data={toplines.moderation} />
	</section>

	<HeroBalloon person={balloons.people[0]} onopen={() => (interiorOpen = true)} />

	{#if browser && mounted}
		<BalloonPack
			people={balloons.people}
			onopen={(slug) => {
				if (slug === 'donald-trump') {
					interiorOpen = true;
				} else {
					summarySlug = slug;
				}
			}}
		/>
	{/if}
</main>

{#if browser && interiorOpen}
	<BalloonInterior data={interior} onclose={() => (interiorOpen = false)} />
{/if}

{#if browser && summaryPerson}
	<!-- COPY:PT — Balloon summary card for non-Trump taps. Softening note: step 3 copy says 'Tap any balloon' which is fulfilled here. -->
	<div class="balloon-summary-overlay" role="dialog" aria-modal="true" aria-label="{summaryPerson.name} summary">
		<div class="balloon-summary-card">
			<button class="balloon-summary-close" onclick={() => (summarySlug = null)} aria-label="Close">✕</button>
			{#if summaryPerson.face}
				<img class="balloon-summary-face" src="/{summaryPerson.face}" alt={summaryPerson.name} />
			{/if}
			<h3 class="balloon-summary-name">{summaryPerson.name}</h3>
			<p class="balloon-summary-stat">
				{summaryPerson.totals.posts} posts · {Math.round(summaryPerson.totals.oppShare * 100)}% opposition air
			</p>
			{#if summaryPerson.totals.ownRegister !== null || summaryPerson.totals.oppRegister !== null}
				<p class="balloon-summary-register">
					{#if summaryPerson.totals.ownRegister !== null}own register: {summaryPerson.totals.ownRegister.toFixed(1)}{/if}
					{#if summaryPerson.totals.ownRegister !== null && summaryPerson.totals.oppRegister !== null}&nbsp;·&nbsp;{/if}
					{#if summaryPerson.totals.oppRegister !== null}opp register: {summaryPerson.totals.oppRegister.toFixed(1)}{/if}
				</p>
			{/if}
		</div>
	</div>
{/if}

{#if browser && mounted}
	<FeedOutro
		rounds={quizData.rounds}
		moderation={toplines.moderation}
		quizN={quizState?.n ?? 0}
		quizCorrect={quizState?.correct ?? 0}
	/>
{/if}

<details class="methodology">
	<summary>Methodology</summary>
	<!-- COPY: PT — one paragraph stub covering: LLM classification approach, stage-2 partial coverage disclosure, quiz sampling method, what clips can't show, face-image rights pending -->
	<p>
		Posts were classified using a large language model pipeline (stage-1 batch, stage-2 partial
		coverage). The quiz draws a stratified sample from head-to-head era clips; classification may
		misattribute ambiguous content. Video clips show framing and tone only — they cannot show reach,
		targeting, or paid promotion. Face images are used under fair-use editorial doctrine; rights
		status pending legal review.
	</p>
	<!-- Credits -->
	<p class="credits">
		Data: TikTok public API scrape · Analysis: Wong Pei Ting · Built with SvelteKit, D3, Vitest
	</p>
</details>

<style>
	main {
		max-width: 390px;
		margin: 0 auto;
		padding: 16px 12px 48px;
		font-family:
			system-ui,
			-apple-system,
			sans-serif;
	}
	.intro {
		margin-bottom: 24px;
	}
	h1 {
		font-size: 22px;
		font-weight: 800;
		margin: 0 0 12px;
		line-height: 1.2;
	}
	p {
		font-size: 15px;
		line-height: 1.6;
		margin: 0;
		color: #333;
	}
	.quiz-section {
		margin-top: 16px;
	}
	.loading {
		text-align: center;
		color: #666;
		padding: 24px 0;
	}
	.interlude {
		margin-top: 32px;
		border-top: 1px solid #e0e0e0;
		padding-top: 24px;
	}
	.interlude p {
		font-size: 15px;
		line-height: 1.6;
		color: #333;
		margin: 0 0 20px;
	}
	.methodology {
		margin-top: 32px;
		border-top: 1px solid #e0e0e0;
		padding-top: 16px;
		font-size: 14px;
		color: #555;
	}
	.methodology summary {
		cursor: pointer;
		font-weight: 600;
	}
	.credits {
		margin-top: 8px;
		font-size: 12px;
		color: #888;
	}
	.balloon-summary-overlay {
		position: fixed;
		inset: 0;
		z-index: 1200;
		display: flex;
		align-items: flex-end;
		justify-content: center;
		background: rgba(0, 0, 0, 0.45);
	}
	.balloon-summary-card {
		position: relative;
		width: 100%;
		max-width: 390px;
		background: #fff;
		border-radius: 16px 16px 0 0;
		padding: 24px 20px env(safe-area-inset-bottom, 16px);
		box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.2);
	}
	.balloon-summary-close {
		position: absolute;
		top: 12px;
		right: 12px;
		min-width: 44px;
		min-height: 44px;
		background: none;
		border: none;
		font-size: 18px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #333;
	}
	.balloon-summary-face {
		width: 64px;
		height: 64px;
		object-fit: cover;
		border-radius: 50%;
		display: block;
		margin: 0 auto 12px;
	}
	.balloon-summary-name {
		font-size: 18px;
		font-weight: 700;
		text-align: center;
		margin: 0 0 6px;
	}
	.balloon-summary-stat {
		font-size: 14px;
		color: #555;
		text-align: center;
		margin: 0 0 4px;
	}
	.balloon-summary-register {
		font-size: 12px;
		color: #888;
		text-align: center;
		margin: 0;
	}
</style>
