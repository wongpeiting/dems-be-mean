<script>
	import * as d3 from 'd3';
	import { fade } from 'svelte/transition';
	import { base } from '$app/paths';
	import data from '$lib/data/tiktok.json';

	// The @democrats cast, packed as portrait circles. The scroll drives it as an
	// instrument: which people are on the board (`side`), what sizes them (`sizeBy`),
	// and who is singled out (`spotlight` one face, `emphasis` a set) all change per step.
	//   side     — 'all' | 'own' (Democrats) | 'opp' (their opposition)
	//   sizeBy   — 'main' (lead roles) | 'videos' (any appearance) | an emotion key
	//   colorBy  — 'party' | 'lean' (attack↔hype)
	let {
		account = 'Democrat',
		side = 'all',
		sizeBy = 'main',
		colorBy = 'lean',
		spotlight = null,
		emphasis = null,
		litParty = null, // 'opp' → keep the opposition bright and dim own side (or vice-versa)
		win = null // 'recent3' (last three months), { lo, hi } indices, or null = all time
	} = $props();

	const COLORS = { Republican: '#ee6677', Democrat: '#5b8dd6' };
	// the lean score is effectively categorical (values cluster at the ends / near zero),
	// so we label it rather than imply a continuous position
	const leanCat = (l) => ((l ?? 0) <= -0.3 ? 'att' : (l ?? 0) >= 0.3 ? 'hyp' : 'mix');
	const leanLabel = (l) => ({ att: 'Attacked', hyp: 'Hyped', mix: 'Mixed' })[leanCat(l)];
	const leanScale = d3
		.scaleLinear()
		.domain([-1, 0, 1])
		.range(['#a8478c', '#c9ccd2', '#e8863a'])
		.clamp(true);
	const emoColor = (e) => {
		const ATTACK = new Set(['mockery', 'contempt', 'outrage', 'anger', 'disgust', 'disapproval', 'ridicule', 'suspicion', 'fear', 'alarm', 'concern', 'sadness', 'urgency']);
		const HYPE = new Set(['pride', 'patriotism', 'admiration', 'triumph', 'inspiration', 'hope', 'celebration', 'confidence', 'strength', 'excitement', 'nostalgia', 'unity']);
		return ATTACK.has(e) ? '#a8478c' : HYPE.has(e) ? '#e8863a' : '#aeb4bd';
	};
	const faceColor = (p) => (colorBy === 'lean' ? leanScale(p.lean ?? 0) : (COLORS[p.party] ?? '#8a8e97'));

	const emoKeys = new Set(Array.isArray(data.emotions) ? data.emotions : []);
	const acctNode = $derived(data.children.find((c) => c.name === account));
	// small caption naming whose feed this is — stays correct when the slides flip account
	const acctHandles = $derived.by(() => {
		const handles = (acctNode?.accounts ?? []).map((a) => '@' + a);
		return handles.length ? handles.join(' + ') : '@' + account.toLowerCase();
	});
	const roster = $derived(acctNode?.children ?? []);
	const acctMonths = $derived(acctNode?.months ?? []);
	// resolve the window to concrete { lo, hi } indices into THIS account's months, so
	// 'recent3' means each account's own last three months
	// The window is set by the scroll step (the scrolly leads); the caption just reports it.
	const isRecent = $derived(!!win);
	const winRange = $derived.by(() => {
		if (!isRecent) return null;
		const n = acctMonths.length;
		return n >= 3 ? { lo: n - 3, hi: n - 1 } : { lo: 0, hi: Math.max(0, n - 1) };
	});

	// value that sizes a circle in the CURRENT step: a month window if set, else the metric
	const val = (d) => {
		if (winRange && acctMonths.length) {
			let s = 0;
			for (let i = winRange.lo; i <= winRange.hi; i++) s += d.monthly?.[acctMonths[i]] ?? 0;
			return s;
		}
		if (emoKeys.has(sizeBy)) return d.emotions?.[sizeBy] ?? 0;
		if (sizeBy === 'videos') return d.videos ?? 0;
		return d.main ?? 0; // lead roles
	};
	// stable reference metric (all-time lead roles) — fixes ONE absolute scale for the
	// whole component, so narrowing to a window genuinely shrinks circles instead of
	// re-inflating them to fill the space.
	const refVal = (d) => d.main ?? 0;

	// windowed appearance count for the tooltip (all we can window — main/emotions are all-time)
	const winCount = (d) => {
		if (!winRange || !acctMonths.length) return d.videos ?? 0;
		let s = 0;
		for (let i = winRange.lo; i <= winRange.hi; i++) s += d.monthly?.[acctMonths[i]] ?? 0;
		return s;
	};
	const MONS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
	const winLabel = $derived.by(() => {
		if (!winRange || !acctMonths.length) return '';
		const a = acctMonths[winRange.lo],
			b = acctMonths[winRange.hi];
		const mon = (m) => MONS[+m.slice(5, 7) - 1];
		return a.slice(0, 4) === b.slice(0, 4)
			? `${mon(a)}–${mon(b)} ${b.slice(0, 4)}`
			: `${mon(a)} ${a.slice(0, 4)} – ${mon(b)} ${b.slice(0, 4)}`;
	});

	let people = $derived.by(() => {
		let ppl = roster;
		if (side === 'own') ppl = ppl.filter((p) => p.party === account);
		else if (side === 'opp') ppl = ppl.filter((p) => p.party !== account);
		return ppl.filter((p) => val(p) > 0);
	});

	let chartW = $state(0);
	let chartH = $state(0);
	// Absolute sizing: a circle's radius ∝ √(its value), with ONE scale factor `k` fixed
	// by the full roster — never re-normalised to fill the space. So when a step narrows
	// the board (e.g. drops the opposition), the survivors keep their true size and the
	// cluster simply shrinks, instead of inflating to fake parity with Trump.
	const PAD = 0.6;
	const LABEL_RESERVE = 46; // top band kept clear for the account caption
	let leaves = $derived.by(() => {
		if (chartW <= 0 || chartH <= 0 || people.length === 0) return [];
		// enclosing-radius budget — fit within the width and the height BELOW the label
		const target = Math.min(chartW / 2, (chartH - LABEL_RESERVE) / 2) - 2;

		// reference cluster: the FULL roster at all-time scale, at unit radius
		const full = roster
			.filter((p) => refVal(p) > 0)
			.map((p) => ({ r: Math.sqrt(refVal(p)) }))
			.sort((a, b) => b.r - a.r);
		d3.packSiblings(full);
		const encFull = d3.packEnclose(full);
		const k = encFull && encFull.r > 0 ? target / encFull.r : 1;

		// pack the CURRENT subset with that same k (pad for a little breathing room)
		const nodes = people
			.map((p) => ({ d: p, draw: k * Math.sqrt(val(p)), r: k * Math.sqrt(val(p)) + PAD }))
			.sort((a, b) => b.r - a.r);
		d3.packSiblings(nodes);
		const enc = d3.packEnclose(nodes);
		const cx = chartW / 2 - (enc?.x ?? 0),
			cy = LABEL_RESERVE + (chartH - LABEL_RESERVE) / 2 - (enc?.y ?? 0);
		return nodes.map((n) => ({ d: n.d, x: n.x + cx, y: n.y + cy, r: n.draw }));
	});

	let hovered = $state(null);
	let tooltip = $state(null);
	let tipW = $state(236);
	let tipH = $state(240);
	function enter(node) {
		hovered = node.d.slug;
		tooltip = { x: node.x, y: node.y, r: node.r, person: node.d };
	}
	function leave() {
		hovered = null;
		tooltip = null;
	}
	let tipStyle = $derived.by(() => {
		if (!tooltip) return 'display:none';
		const { x, y, r } = tooltip;
		const w = tipW || 236,
			h = tipH || 240,
			m = 10;
		let left, top;
		if (y - r - h - m >= 8) {
			left = Math.max(w / 2 + 8, Math.min(chartW - w / 2 - 8, x));
			top = y - r - h - m;
		} else if (y + r + m + h <= chartH - 8) {
			left = Math.max(w / 2 + 8, Math.min(chartW - w / 2 - 8, x));
			top = y + r + m;
		} else {
			const roomRight = x + r + m + w <= chartW - 8;
			const cx = roomRight ? x + r + m + w / 2 : x - r - m - w / 2;
			left = Math.max(w / 2 + 8, Math.min(chartW - w / 2 - 8, cx));
			top = Math.max(8, Math.min(chartH - h - 8, y - h / 2));
		}
		return `left:${left}px; top:${top}px`;
	});

	// which faces are muted: a hover wins; else a spotlight isolates one; else an
	// emphasis set keeps a few bright and dims the rest.
	const emphasisSet = $derived(emphasis ? new Set(emphasis) : null);
	// litParty keeps one side bright: 'opp' = not the account's party, 'own' = the account's party
	const inLitParty = (d) =>
		litParty === 'opp' ? d.party !== account : litParty === 'own' ? d.party === account : false;
	const dimmed = (d) => {
		if (hovered) return hovered !== d.slug;
		if (spotlight) return spotlight !== d.slug;
		if (litParty) return !inLitParty(d);
		if (emphasisSet) return !emphasisSet.has(d.slug);
		return false;
	};
	const lit = (d) =>
		hovered === d.slug ||
		spotlight === d.slug ||
		(litParty && inLitParty(d)) ||
		emphasisSet?.has(d.slug);
</script>

<div class="stage">
	<div class="chart" bind:clientWidth={chartW} bind:clientHeight={chartH}>
		<div class="cast-label">
			<b>{acctHandles}</b>
			<span class="win-tag">{isRecent ? 'recent' : 'all-time'}</span>
			cast of characters
		</div>
		{#if chartW > 0 && chartH > 0}
			<svg width={chartW} height={chartH} viewBox="0 0 {chartW} {chartH}" role="presentation">
				<defs>
					<clipPath id="castClip" clipPathUnits="objectBoundingBox"
						><circle cx="0.5" cy="0.5" r="0.5" /></clipPath
					>
				</defs>
				{#each leaves as node (node.d.slug)}
					<g
						class="node"
						class:dim={dimmed(node.d)}
						class:on={lit(node.d)}
						style="transform: translate({node.x}px, {node.y}px)"
						onmouseenter={() => enter(node)}
						onmouseleave={leave}
						in:fade={{ duration: 260 }}
						out:fade={{ duration: 200 }}
						role="presentation"
					>
						<g class="bubble" style="transform: scale({node.r})">
							<circle class="ring" r="1" fill={faceColor(node.d)} />
							{#if node.d.img}
								<image
									href={base + node.d.img}
									x="-1"
									y="-1"
									width="2"
									height="2"
									preserveAspectRatio="xMidYMid slice"
									clip-path="url(#castClip)"
								/>
							{/if}
							<circle class="stroke" r="1" fill="none" stroke={faceColor(node.d)} />
						</g>
					</g>
				{/each}
			</svg>

			{#if tooltip}
				{@const p = tooltip.person}
				{@const emos = Object.entries(p.emotions ?? {}).slice(0, 6)}
				{@const emax = emos.length ? emos[0][1] : 1}
				<div class="tip" bind:clientWidth={tipW} bind:clientHeight={tipH} style={tipStyle}>
					<div class="tip-name">{p.name}</div>
					<div class="tip-meta">{p.party}{p.party !== 'Democrat' ? ' · opposition' : ' · own side'}</div>
					{#if isRecent}
						<div class="tip-big">
							appears in <b>{winCount(p)}</b> videos<span class="sub"> · {winLabel}</span>
						</div>
					{:else}
						<div class="tip-big">
							leads <b>{p.main}</b> videos<span class="sub"> · appears in {p.videos}</span>
						</div>
						<div class="tip-lean">
							<span class="lean-pill {leanCat(p.lean)}">{leanLabel(p.lean)}</span>
						</div>
						{#if emos.length}
							<div class="tip-section">emotions engineered</div>
							<div class="emo-bars">
								{#each emos as [e, n]}
									<div class="emo-row">
										<span>{e}</span>
										<div class="etrack">
											<div class="efill" style="width: {(n / emax) * 100}%; background: {emoColor(e)}"></div>
										</div>
										<b>{n}</b>
									</div>
								{/each}
							</div>
						{/if}
					{/if}
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	.stage {
		position: sticky;
		top: 0;
		height: 100vh;
		overflow: hidden;
		background: #1a1d21;
	}
	.chart {
		position: absolute;
		/* --chart-left lets the host push the circle graphic to one side so scroll cards
		   riding up the other side never sit on top of the faces */
		inset: 3vh 2vw 3vh var(--chart-left, 2vw);
	}
	.cast-label {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		text-align: center;
		font-family: var(--sans);
		font-size: 0.82rem;
		letter-spacing: 0.01em;
		color: #fff;
		opacity: 0.9;
		z-index: 3;
		pointer-events: none;
	}
	.win-tag {
		font-weight: 700;
		color: #fff;
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.3);
		border-radius: 999px;
		padding: 0.05em 0.5em;
		margin: 0 0.1em;
	}
	svg {
		display: block;
		width: 100%;
		height: 100%;
	}
	.node {
		transition:
			transform 700ms cubic-bezier(0.4, 0, 0.2, 1),
			opacity 300ms ease;
		cursor: pointer;
	}
	.bubble {
		transition: transform 700ms cubic-bezier(0.4, 0, 0.2, 1);
	}
	.node.dim {
		opacity: 0.7;
	}
	.ring {
		opacity: 0.3;
	}
	.stroke {
		stroke-width: 3;
		stroke-opacity: 1;
		vector-effect: non-scaling-stroke;
		transition: stroke 400ms ease;
	}
	.node.on .stroke {
		stroke-width: 5;
	}
	.tip {
		position: absolute;
		transform: translateX(-50%);
		width: 236px;
		background: #fff;
		color: #16181c;
		border-radius: 10px;
		padding: 0.6rem 0.75rem;
		box-shadow: 0 8px 26px rgba(0, 0, 0, 0.4);
		pointer-events: none;
		z-index: 5;
	}
	.tip-name {
		font-weight: 700;
		font-size: 0.95rem;
		line-height: 1.2;
	}
	.tip-meta {
		font-size: 0.72rem;
		color: #99a;
	}
	.tip-big {
		margin: 0.4rem 0 0.3rem;
		font-size: 0.9rem;
	}
	.tip-big b {
		font-size: 1.05rem;
	}
	.tip-big .sub {
		font-size: 0.68rem;
		color: #99a;
	}
	.tip-lean {
		margin: 0.4rem 0 0.2rem;
	}
	.lean-pill {
		display: inline-block;
		padding: 2px 9px;
		border-radius: 999px;
		font-size: 0.66rem;
		font-weight: 700;
		letter-spacing: 0.02em;
	}
	.lean-pill.att {
		background: rgba(168, 71, 140, 0.16);
		color: #a8478c;
	}
	.lean-pill.hyp {
		background: rgba(232, 134, 58, 0.16);
		color: #c96f22;
	}
	.lean-pill.mix {
		background: #eef0f3;
		color: #6b7076;
	}
	.tip-section {
		margin: 0.5rem 0 0.15rem;
		font-size: 0.6rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #aab;
	}
	.emo-row {
		display: grid;
		grid-template-columns: 5rem 1fr 1.5rem;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.7rem;
		margin-top: 0.15rem;
	}
	.emo-row span {
		color: #667;
		white-space: nowrap;
		text-transform: capitalize;
	}
	.emo-row b {
		text-align: right;
	}
	.etrack {
		height: 6px;
		background: #eef0f3;
		border-radius: 3px;
		overflow: hidden;
	}
	.efill {
		height: 100%;
		border-radius: 3px;
	}
</style>
