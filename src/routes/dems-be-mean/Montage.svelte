<script>
	import { fade } from 'svelte/transition';
	// Opening montage: @democrats troll-post frames are dealt onto a pile as you scroll.
	// Everything is driven by `progress` so the narration, its z-index and the cards stay
	// in lockstep: the B `lines` each own a 1/B slice of scroll; each line appears at its
	// slice start ON TOP of the whole pile, holds, then that slice's cards bury it. The
	// last line gets no cards, so it stays on top.
	let { imgs = [], progress = 0, lines = [] } = $props();
	const N = imgs.length;
	const B = Math.max(2, lines.length);

	const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
	const smooth = (e0, e1, x) => {
		const t = clamp((x - e0) / (e1 - e0), 0, 1);
		return t * t * (3 - 2 * t);
	};
	const easeOut = (t) => 1 - Math.pow(1 - t, 3); // fast fling, settle to rest
	function rng(seed) {
		return function () {
			seed |= 0;
			seed = (seed + 0x6d2b79f5) | 0;
			let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
			t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
			return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
		};
	}
	// Halton low-discrepancy sequence: successive points fill the gaps, so the FIRST
	// few cards spread across the screen instead of clustering.
	function halton(i, base) {
		let f = 1,
			r = 0;
		while (i > 0) {
			f /= base;
			r += f * (i % base);
			i = Math.floor(i / base);
		}
		return r;
	}

	// Cards are dealt in a BURST per narration beat. The B beats each own a 1/B slice of
	// the scroll; a card assigned to beat `bg` lands only in the LATTER part of that
	// slice (after a HOLD), so the line that appeared at the slice's start reads clean on
	// top first, then gets buried. The last beat gets no cards, so its line stays on top.
	const HOLD = 0.42;
	const nodes = imgs.map((src, i) => {
		const r = rng(i * 2654435761 + 1013904223);
		const jx = (r() - 0.5) * 6,
			jy = (r() - 0.5) * 6; // small jitter so it's not perfectly even
		const fx = clamp(7 + halton(i + 1, 2) * 86 + jx, 5, 95); // resting position (well-spread)
		// top and sides may bleed off the frame, but the BOTTOM must never clip: a card is
		// ~8.5vw wide → ~15vw tall, so cap the resting centre well above the bottom edge
		const fy = clamp(9 + halton(i + 1, 3) * 73 + jy, 6, 82);
		// fling in from a random direction, exiting the NEAREST edge — short, varied travel
		const ang = r() * Math.PI * 2;
		const dx = Math.cos(ang),
			dy = Math.sin(ang);
		const M = 16; // how far past the edge to start
		const tx = dx > 1e-3 ? (100 + M - fx) / dx : dx < -1e-3 ? (-M - fx) / dx : 1e9;
		const ty = dy > 1e-3 ? (100 + M - fy) / dy : dy < -1e-3 ? (-M - fy) / dy : 1e9;
		const t = Math.min(tx, ty);
		// spread cards across the first B-1 beats; reveal within each beat's back portion
		const frac = (i + 1) / N;
		const bg = Math.min(B - 2, Math.floor(frac * (B - 1)));
		const local = Math.min(1, frac * (B - 1) - bg);
		return {
			src,
			revealAt: (bg + HOLD + (1 - HOLD) * local) / B,
			fx,
			fy,
			ox: fx + dx * t,
			oy: fy + dy * t,
			rot: (r() - 0.5) * 40, // resting angle
			spin: (r() - 0.5) * 160, // extra spin during the throw
			z: i // newer cards land on top of older ones
		};
	});

	// active beat (and its text) from progress; z-index = the cards from all EARLIER
	// beats, so this line sits above them and gets buried only by its own beat's cards.
	const beat = $derived(clamp(Math.floor(progress * B), 0, B - 1));
	const caption = $derived(lines[beat] ?? '');
	const capZ = $derived(Math.min(N, Math.round((N * beat) / (B - 1))));
</script>

<div class="stage">
	<div class="field">
		{#each nodes as n (n.src)}
			{@const a = smooth(n.revealAt, n.revealAt + 0.06, progress)}
			{@const e = easeOut(a)}
			<div
				class="post"
				style:left="{n.ox + (n.fx - n.ox) * e}%"
				style:top="{n.oy + (n.fy - n.oy) * e}%"
				style:z-index={n.z}
				style:opacity={a > 0.001 ? 1 : 0}
				style:transform="translate(-50%,-50%) rotate({n.rot + n.spin * (1 - e)}deg)"
			>
				<img src="/{n.src}" alt="" loading="lazy" />
			</div>
		{/each}
	</div>
	<!-- narration, pinned to the centre of the (sticky) viewport, crossfading per beat -->
	{#key caption}
		<div class="caption" style:z-index={capZ} in:fade={{ duration: 350 }} out:fade={{ duration: 350 }}>
			<!-- eslint-disable-next-line svelte/no-at-html-tags -->
			<div class="cap-inner">{@html caption}</div>
		</div>
	{/key}
</div>

<style>
	.stage {
		position: sticky;
		top: 0;
		height: 100vh;
		overflow: hidden;
		background: #1a1d21;
	}
	.field {
		position: absolute;
		inset: 0;
	}
	/* uniform playing cards: same size, white border, rounded corners */
	.post {
		position: absolute;
		width: 8.5%;
		aspect-ratio: 9 / 16;
		box-sizing: border-box;
		padding: 4px;
		background: #f7f6f2;
		border-radius: 8px;
		box-shadow: 0 8px 22px rgba(0, 0, 0, 0.7);
		will-change: transform, left, top;
	}
	.post img {
		display: block;
		width: 100%;
		height: 100%;
		object-fit: cover;
		border-radius: 4px;
		filter: saturate(0.85) brightness(0.9);
	}
	.caption {
		position: absolute;
		inset: 0;
		z-index: 6; /* below the pile (cards use z 0..N) so posts bury each line as they land */
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 24px;
		pointer-events: none;
	}
	.cap-inner {
		/* fixed footprint (widest line + tallest step, the field-guide entry) so the box
		   never resizes between narration lines; text just recentres inside it */
		width: min(26em, calc(100vw - 48px));
		min-height: 11em;
		box-sizing: border-box;
		display: flex;
		align-items: center;
		justify-content: center;
		text-align: center;
		font-family: var(--serif);
		font-weight: 500;
		font-size: clamp(0.9rem, 1.7vw, 1.2rem);
		line-height: 1.45;
		color: #16181c;
		background: #fff;
		padding: 0.85rem 2.1rem;
		box-shadow: 0 8px 26px rgba(0, 0, 0, 0.45);
	}
	.cap-inner :global(em) {
		font-style: italic;
		color: inherit;
	}
	.cap-inner :global(.fg-wrap) {
		display: block;
	}
	.cap-inner :global(.fieldguide) {
		display: block;
		margin-top: 0.85em;
		padding: 0.7em 0.9em;
		background: #f5f2f4;
		font-family: var(--mono, ui-monospace, 'SFMono-Regular', Menlo, monospace);
		font-size: 0.78em;
		letter-spacing: 0.01em;
		line-height: 1.75;
		text-align: left;
		color: #3a3f47;
	}
	.cap-inner :global(.fieldguide b) {
		display: block;
		margin-bottom: 0.35em;
		font-weight: 700;
		color: #16181c;
	}
	@media (max-width: 620px) {
		.post {
			width: 22%;
		}
	}
</style>
