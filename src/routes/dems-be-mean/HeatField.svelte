<script>
	import { base } from '$app/paths';
	import { onMount, tick } from 'svelte';
	import worduse from '$lib/data/worduse.json';

	// `progress` (0→1) is the reveal playhead (clock). `highlight` is an array of
	// words to spotlight during the annotate phase (others dim); `annotating` fades
	// the HUD so the spotlight is the only thing to track.
	let { data, progress = 0, highlight = null, annotating = false, exploring = false } = $props();
	const hset = $derived(highlight && highlight.length ? new Set(highlight) : null);

	// explore act: hover a word → callout with its harshest line + inline clip
	let hovered = $state(null);
	$effect(() => {
		if (!exploring) hovered = null; // clear when leaving the explore act
	});
	// play the clip with sound; fall back to muted if the browser blocks audio autoplay
	function playWithSound(node) {
		node.muted = false;
		node.volume = 1;
		node.play().catch(() => {
			node.muted = true;
			node.play().catch(() => {});
		});
	}
	const fmt = (n) =>
		n == null
			? '—'
			: n >= 1e6
				? (n / 1e6).toFixed(1) + 'm'
				: n >= 1e3
					? Math.round(n / 1e3) + 'k'
					: '' + n;
	const clean = (s) => (s || '').replaceAll('_', ' ');

	const PADX = 8,
		PADY = 14; // % margins inside the stage

	const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
	const lerp = (a, b, t) => a + (b - a) * t;
	const smooth = (e0, e1, x) => {
		const t = clamp((x - e0) / (e1 - e0), 0, 1);
		return t * t * (3 - 2 * t);
	};
	// stable per-word pseudo-random in [0,1)
	function rnd(str, salt) {
		let h = 2166136261;
		const s = str + salt;
		for (let i = 0; i < s.length; i++) {
			h ^= s.charCodeAt(i);
			h = Math.imul(h, 16777619);
		}
		return ((h >>> 0) % 100000) / 100000;
	}
	const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
	const fmtMonth = (ym) => {
		const [y, m] = ym.split('-');
		return `${MON[+m - 1]} ${y}`;
	};

	const words = data.words; // pre-sorted by median date (= x-rank order)
	const nW = words.length;
	const months = data.months;
	// y from meanness RANK (yr, 0..1, 1 = meanest): harsher → top of the stage
	const yFor = (yr) => lerp(100 - PADY, PADY, clamp(yr, 0, 1));
	// colour follows the same axis: measured (bottom) neutral → inflammatory (top) red
	const yColor = (yr) => {
		const t = clamp(yr, 0, 1);
		const mild = [226, 227, 230],
			hot = [238, 92, 108];
		return `rgb(${Math.round(lerp(mild[0], hot[0], t))},${Math.round(lerp(mild[1], hot[1], t))},${Math.round(lerp(mild[2], hot[2], t))})`;
	};
	const lossXr = data.span.lossXr ?? 0.35;

	// 3-month trailing average so a tiny-n month doesn't spike the account-level gauges.
	const roll = (arr, k = 3) =>
		arr.map((_, i) => {
			const w = arr.slice(Math.max(0, i - k + 1), i + 1);
			return w.reduce((a, b) => a + b, 0) / w.length;
		});
	const attackS = roll(months.map((m) => m.attack));
	const trumpS = roll(months.map((m) => m.trump));

	// word nodes — x = chronological rank (even spread), y = meanness. x/y finalised
	// in layout() after fonts can be measured; ignite (revealAt) tracks x = rank.
	let nodes = $state(
		words.map((w) => ({
			word: w.word,
			revealAt: w.xr,
			xr: w.xr,
			yr: w.yr,
			color: yColor(w.yr),
			size: 13 + Math.sqrt(w.count) * 2.4,
			x: PADX + w.xr * (100 - 2 * PADX),
			y: yFor(w.yr),
			line: w.line, // harshest example dunk (explore act)
			clip: w.clip, // its local mp4 filename, or ""
			url: w.url, // tiktok link
			stats: w.stats // classification metadata (register, crudeness, function, tags, views…)
		}))
	);
	let els = [];
	let stageEl;
	let sf = $state(1); // font-size scale (shrinks the field on narrow screens)
	let mx = $state(PADX); // horizontal margin (also narrower on phones)

	// Both axes now carry data (x = time-rank, y = meanness), so we can't declump
	// freely. Keep y locked to the true meanness (+ a hair of jitter to break exact
	// ties) and resolve overlaps by nudging along x only — rank is ordinal, so small
	// horizontal shifts read fine while the vertical (meanness) stays honest.
	async function layout() {
		if (!stageEl) return;
		const r = stageEl.getBoundingClientRect();
		const W = r.width,
			H = r.height;
		if (!W || !H) return;
		sf = clamp(W / 1040, 0.5, 1);
		mx = W < 560 ? 5 : PADX;
		await tick();
		const N = nodes.map((n, i) => {
			const b = els[i]?.getBoundingClientRect();
			return {
				...n,
				wp: b ? (b.width / W) * 100 : 6,
				hp: b ? (b.height / H) * 100 : 4,
				x: mx + n.xr * (100 - 2 * mx),
				y: yFor(n.yr) + (rnd(n.word, 'y') - 0.5) * 2.4
			};
		});
		// Both axes are ordinal ranks (time, meanness), so small nudges on either read
		// fine. Separate each overlapping pair along the axis of *least* overlap — the
		// standard label-declutter move — so positions stay as close to true as possible.
		for (let it = 0; it < 120; it++) {
			for (let i = 0; i < N.length; i++)
				for (let j = i + 1; j < N.length; j++) {
					const a = N[i],
						c = N[j];
					const ox = (a.wp + c.wp) / 2 + 1 - Math.abs(a.x - c.x);
					const oy = (a.hp + c.hp) / 2 + 1.2 - Math.abs(a.y - c.y);
					if (ox <= 0 || oy <= 0) continue;
					if (ox < oy) {
						const dir = a.x === c.x ? (i % 2 ? 1 : -1) : a.x < c.x ? 1 : -1;
						const p = Math.min(ox, 4) / 2;
						a.x -= dir * p;
						c.x += dir * p;
					} else {
						const dir = a.y === c.y ? (i % 2 ? 1 : -1) : a.y < c.y ? 1 : -1;
						const p = Math.min(oy, 3) / 2;
						a.y -= dir * p;
						c.y += dir * p;
					}
				}
			for (const n of N) {
				n.x = clamp(n.x, mx, 100 - mx);
				n.y = clamp(n.y, PADY, 100 - PADY);
			}
		}
		nodes = N;
	}

	// --- reactive readout: playhead (rank) → the word at that rank → its month -----
	const wIdx = $derived(clamp(Math.round(progress * (nW - 1)), 0, nW - 1));
	const curMonthKey = $derived(words[wIdx].median.slice(0, 7));
	const mIdx = $derived(Math.max(0, months.findIndex((m) => m.month === curMonthKey)));
	const nowX = $derived(mx + progress * (100 - 2 * mx));
	const lossX = $derived(mx + lossXr * (100 - 2 * mx));
	const lossOpacity = $derived(smooth(lossXr - 0.1, lossXr, progress) * (1 - smooth(0.9, 1, progress)) * 0.9);
	const pct = (v) => Math.round(v * 100);

	onMount(() => {
		let done = false;
		const run = () => layout();
		run();
		if (document.fonts?.ready) document.fonts.ready.then(() => !done && run());
		const t = setTimeout(run, 400);
		const onResize = () => run();
		window.addEventListener('resize', onResize);
		return () => {
			done = true;
			clearTimeout(t);
			window.removeEventListener('resize', onResize);
		};
	});
</script>

<div class="stage" bind:this={stageEl}>
	<div class="field" class:annotating class:explore={exploring}>
		{#each nodes as n, i (n.word)}
			{@const a = smooth(n.revealAt - 0.05, n.revealAt + 0.02, progress)}
			{@const hi = hset ? hset.has(n.word) : null}
			{@const dim = exploring && hovered && hovered.word !== n.word}
			{@const op = hset ? (hi ? 1 : 0.08) : dim ? 0.22 : a}
			{@const sc = hset ? 1 : 0.84 + 0.16 * a}
			<span
				bind:this={els[i]}
				class="w"
				class:hi={hi === true}
				style:left="{n.x}%"
				style:top="{n.y}%"
				style:font-size="{(n.size * sf).toFixed(1)}px"
				style:color={n.color}
				style:opacity={op}
				style:transform="translate(-50%,-50%) scale({sc})"
				onmouseenter={() => exploring && (hovered = n)}
				onmouseleave={() => exploring && (hovered = null)}
				onclick={() => exploring && (hovered = hovered?.word === n.word ? null : n)}
				>{n.word}</span
			>
		{/each}
	</div>

	{#if exploring && hovered}
		{@const wu = worduse[hovered.word] || null}
		<div
			class="callout"
			class:left={hovered.x > 52}
			style:left="{hovered.x}%"
			style:top="50%"
		>
			{#if hovered.clip}
				<!-- svelte-ignore a11y_media_has_caption -->
				<video src="{base}/clips/{hovered.clip}" loop playsinline use:playWithSound></video>
			{/if}
			<div class="cl-count">
				<b>“{hovered.word}”</b> in {wu ? wu.n : 1}
				{(wu ? wu.n : 1) === 1 ? 'dunk' : 'dunks'}
			</div>
			<ul class="cl-lines">
				{#each (wu?.ex ?? [{ t: '', l: hovered.line }]) as e (e.l)}
					<li>{#if e.t}<span class="cl-t">{e.t}</span>{/if}“{e.l}”</li>
				{/each}
			</ul>
			{#if wu && wu.n > wu.ex.length}
				<div class="cl-more">…and {wu.n - wu.ex.length} more</div>
			{/if}
		</div>
	{/if}

	{#if exploring}
		<div class="explore-hint">
			<span class="eh-desktop">Hover any word to explore</span>
			<span class="eh-mobile">Tap any word to explore</span>
			<span class="hint-scroll">(or keep scrolling)</span>
		</div>
	{/if}

	<div class="lossmark" style:left="{lossX}%" style:opacity={lossOpacity}>
		<span class="tag">Trump wins election</span>
	</div>
	<div class="nowline" style:left="{nowX}%" style:opacity={progress > 0.01 && progress < 0.99 ? 0.9 : 0}></div>


	{#if !exploring}
	<div class="hud" class:annotating>
		<div class="date">{fmtMonth(curMonthKey)}</div>
		<div class="gauge g-mean">
			<div class="lab"><span>Share of posts that attack</span><span class="val">{pct(attackS[mIdx])}%</span></div>
			<div class="track"><div class="fill" style:width="{pct(attackS[mIdx])}%"></div></div>
		</div>
		<div class="gauge g-trump">
			<div class="lab"><span>Trump as target</span><span class="val">{pct(trumpS[mIdx])}%</span></div>
			<div class="track"><div class="fill" style:width="{pct(trumpS[mIdx])}%"></div></div>
		</div>
	</div>
	{/if}


</div>

<style>
	.stage {
		position: relative;
		height: 100vh;
		overflow: hidden;
		background-color: #1a1d21;
	}
	.field {
		position: absolute;
		inset: 0;
	}
	.w {
		position: absolute;
		z-index: 2; /* words sit above the election / now marker lines */
		font-family: var(--sans);
		font-weight: 700;
		white-space: nowrap;
		letter-spacing: -0.01em;
		color: var(--ink);
		transform: translate(-50%, -50%);
		text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
		pointer-events: none;
		will-change: opacity, transform;
	}
	/* transitions only while annotating, so the scroll reveal stays crisp */
	.field.annotating .w {
		transition:
			opacity 0.35s ease,
			transform 0.35s ease;
	}
	.w.hi {
		z-index: 4;
	}
	.field.explore .w {
		pointer-events: auto;
		cursor: pointer;
		transition: opacity 0.25s ease;
	}

	.callout {
		position: absolute;
		z-index: 20;
		display: flex;
		flex-direction: column;
		width: 320px;
		max-width: 48vw;
		max-height: calc(100dvh - 24px);
		background: #fff;
		color: #16181c;
		box-shadow: 0 14px 44px rgba(0, 0, 0, 0.6);
		overflow: hidden;
		pointer-events: none;
		transform: translate(20px, -50%);
	}
	.callout.left {
		transform: translate(calc(-100% - 20px), -50%);
	}
	.callout video {
		display: block;
		flex: 0 0 auto;
		width: 100%;
		height: auto;
		max-height: 200px;
		background: #000;
	}
	.callout .cl-count {
		flex: 0 0 auto;
		padding: 11px 15px 4px;
		font-family: var(--sans);
		font-size: 0.68rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #8a8f96;
	}
	.callout .cl-count b {
		font-family: var(--serif);
		font-size: 1rem;
		text-transform: none;
		letter-spacing: 0;
		color: #16181c;
	}
	.callout .cl-lines {
		flex: 1 1 auto;
		min-height: 0;
		overflow: hidden;
		list-style: none;
		margin: 0;
		padding: 4px 15px 6px;
		-webkit-mask-image: linear-gradient(#000 86%, transparent);
		mask-image: linear-gradient(#000 86%, transparent);
	}
	.callout .cl-lines li {
		font-family: var(--serif);
		font-style: italic;
		font-size: 0.86rem;
		line-height: 1.34;
		color: #33373d;
		padding: 5px 0;
		border-top: 1px solid #eceef1;
	}
	.callout .cl-lines li:first-child {
		border-top: 0;
	}
	.callout .cl-t {
		display: block;
		font-family: var(--sans);
		font-style: normal;
		font-size: 0.58rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: rgb(238, 92, 108);
		margin-bottom: 1px;
	}
	.callout .cl-more {
		flex: 0 0 auto;
		padding: 2px 15px 12px;
		font-family: var(--sans);
		font-size: 0.66rem;
		color: #8a8f96;
	}
	.explore-hint {
		position: absolute;
		top: 44px;
		left: 44px;
		z-index: 6;
		max-width: 230px;
		padding: 14px 19px;
		background: #fff;
		border: 1px solid rgba(0, 0, 0, 0.12);
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
		font-size: 0.95rem;
		line-height: 1.35;
		text-align: left;
		color: #a8478c;
		font-weight: 700;
		pointer-events: none;
		animation: hint-bob 2.4s ease-in-out infinite;
	}
	@keyframes hint-bob {
		0%,
		100% {
			transform: translateY(0);
		}
		50% {
			transform: translateY(-7px);
		}
	}
	.explore-hint .hint-scroll {
		display: block;
		margin-top: 4px;
		font-size: 0.78rem;
		font-weight: 400;
		letter-spacing: 0.02em;
		color: #a8478c;
	}
	.explore-hint .eh-mobile {
		display: none;
	}
	@media (hover: none) {
		.explore-hint .eh-desktop {
			display: none;
		}
		.explore-hint .eh-mobile {
			display: inline;
		}
	}
	@media (max-width: 640px) {
		.explore-hint {
			top: 24px;
			left: 20px;
			max-width: 150px;
			padding: 9px 12px;
			font-size: 0.8rem;
		}
		.explore-hint .hint-scroll {
			font-size: 0.64rem;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.explore-hint {
			animation: none;
		}
	}
	.nowline {
		position: absolute;
		z-index: 1;
		top: 0;
		bottom: 0;
		width: 1px;
		background: linear-gradient(to bottom, transparent, rgba(255, 255, 255, 0.28), transparent);
	}
	.lossmark {
		position: absolute;
		z-index: 1;
		top: 0;
		bottom: 0;
		width: 1px;
		background: rgba(255, 255, 255, 0.55);
	}
	.lossmark .tag {
		position: absolute;
		top: 6vh;
		left: 11px;
		font-size: 0.72rem;
		letter-spacing: 0.02em;
		color: rgba(255, 255, 255, 0.85);
		white-space: nowrap;
	}
	/* mobile: the HUD becomes a "life-bar" panel pinned across the top of the screen, and the
	   word wall is pushed down below it — so the date/gauges get dedicated space and the
	   scrolling words never collide with them */
	@media (max-width: 640px) {
		/* the caption already says "after Trump won the 2024 election" on mobile — drop the line */
		.lossmark {
			display: none;
		}
		.field {
			top: 118px;
		}
		/* while exploring the HUD is gone, so let the words reclaim the top band */
		.field.explore {
			top: 0;
		}
		.hud {
			left: 0;
			right: 0;
			top: 0;
			padding: 12px 16px 14px;
			background: #1a1d21;
			box-shadow: 0 7px 16px 7px #1a1d21; /* soft feather so words fade in below */
		}
		.hud .date {
			font-size: 1.15rem;
			margin-bottom: 8px;
		}
		.hud .gauge {
			width: auto; /* life bars span the full panel width */
			font-size: 0.72rem;
			margin-bottom: 7px;
		}
		.hud .gauge:last-child {
			margin-bottom: 0;
		}
		.gauge .track {
			height: 5px;
		}
	}
	.hud {
		position: absolute;
		left: 24px;
		top: 20px;
		z-index: 6;
		font-size: 0.72rem;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--muted);
		transition: opacity 0.4s ease;
	}
	.hud.annotating {
		opacity: 0.22;
	}
	.hud .date {
		font-family: var(--serif);
		font-weight: 700;
		font-size: 1.5rem;
		letter-spacing: 0;
		text-transform: none;
		color: var(--ink);
		margin-bottom: 14px;
	}
	.gauge {
		margin: 0 0 12px;
		width: min(230px, 42vw);
		text-transform: none;
		letter-spacing: 0.01em;
		font-size: 0.8rem;
	}
	.gauge .lab {
		display: flex;
		justify-content: space-between;
		margin-bottom: 4px;
	}
	.gauge .lab .val {
		color: var(--ink);
		font-weight: 700;
	}
	.gauge .track {
		height: 6px;
		border-radius: 3px;
		background: #2a2e34;
		overflow: hidden;
	}
	.gauge .fill {
		height: 100%;
		border-radius: 3px;
		transition: width 0.12s linear;
	}
	.g-mean .fill {
		background: #a8478c;
	}
	.g-trump .fill {
		background: #a8478c;
	}
	@media (prefers-reduced-motion: reduce) {
		.w {
			transition: none !important;
		}
	}
</style>
