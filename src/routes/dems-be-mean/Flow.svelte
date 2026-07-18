<script>
	import { sankey as d3sankey, sankeyLinkHorizontal } from 'd3-sankey';
	import { fade } from 'svelte/transition';
	import data from '$lib/data/tiktok.json';

	// A three-column Sankey of one account's output: every post flows from the account,
	// into the person it makes its MAIN CHARACTER, and out into the EMOTION it evokes.
	// Toggle the account to watch the same faces run through opposite emotional machines —
	// @democrats render Trump in mockery; @GOP render him in pride.
	let { account = $bindable('Democrat'), topChars = 7, topEmos = 8 } = $props();

	const ACCTS = { Democrat: '@democrats', Republican: '@GOP' };

	// emotion register: attack (tearing down) vs hype (building up) vs neutral. Same
	// families as the cast pack, so colour reads consistently across the piece.
	const ATTACK = new Set(['mockery', 'contempt', 'outrage', 'anger', 'disgust', 'disapproval', 'ridicule', 'suspicion', 'fear', 'alarm', 'concern', 'urgency', 'sadness', 'derision', 'scorn', 'condemnation', 'schadenfreude', 'criticism', 'indignation']);
	const HYPE = new Set(['pride', 'patriotism', 'admiration', 'triumph', 'inspiration', 'hope', 'celebration', 'confidence', 'strength', 'excitement', 'nostalgia', 'unity', 'optimism', 'joy', 'empowerment', 'warmth', 'enthusiasm', 'affection', 'positivity', 'support', 'hype', 'love', 'gratitude']);
	const classify = (e) => (ATTACK.has(e) ? 'attack' : HYPE.has(e) ? 'hype' : 'neutral');
	const CLS_COLOR = { attack: '#EE6677', hype: '#2f9e6a', neutral: '#8a8f96' };

	const OTHER_CHARS = 'Everyone else';
	const OTHER_EMOS = 'other emotions';

	// Build the sankey graph for an account: nodes (account | characters | emotions) and
	// links. Left→char width is the post count (`main`); char→emotion splits that count by
	// the character's own emotion mix, so every column's widths sum to the same total.
	function buildGraph(acct) {
		const people = data.children.find((c) => c.name === acct).children.filter((p) => (p.main ?? 0) > 0);
		const ranked = [...people].sort((a, b) => b.main - a.main);
		const lead = ranked.slice(0, topChars);
		const rest = ranked.slice(topChars);

		// character rows: the top faces, then everyone else folded into one
		const chars = lead.map((p) => ({ name: p.name, main: p.main, emotions: p.emotions ?? {} }));
		if (rest.length) {
			const emo = {};
			let main = 0;
			for (const p of rest) {
				main += p.main;
				for (const [e, v] of Object.entries(p.emotions ?? {})) emo[e] = (emo[e] || 0) + v;
			}
			chars.push({ name: OTHER_CHARS, main, emotions: emo, bucket: true });
		}

		// each character contributes main-weighted flow into emotions (their mix, scaled to
		// their post count). collect per-emotion totals to pick the columns worth naming.
		const emoTotals = {};
		const charFlows = chars.map((c) => {
			const tot = Object.values(c.emotions).reduce((s, v) => s + v, 0);
			const flows = {};
			if (tot > 0) {
				for (const [e, v] of Object.entries(c.emotions)) {
					const w = (v / tot) * c.main;
					flows[e] = w;
					emoTotals[e] = (emoTotals[e] || 0) + w;
				}
			} else {
				flows[OTHER_EMOS] = c.main;
				emoTotals[OTHER_EMOS] = (emoTotals[OTHER_EMOS] || 0) + c.main;
			}
			return { char: c, flows };
		});

		const topE = Object.entries(emoTotals)
			.filter(([e]) => e !== OTHER_EMOS)
			.sort((a, b) => b[1] - a[1])
			.slice(0, topEmos)
			.map(([e]) => e);
		const keepE = new Set(topE);

		// assemble node list: [account, ...characters, ...emotions(+other)]
		const nodes = [{ name: ACCTS[acct], kind: 'account' }];
		const charIdx = {};
		chars.forEach((c) => {
			charIdx[c.name] = nodes.length;
			nodes.push({ name: c.name, kind: 'char', bucket: c.bucket });
		});
		const emoIdx = {};
		const emoOrder = [...topE];
		if (Object.keys(emoTotals).some((e) => e === OTHER_EMOS || !keepE.has(e))) emoOrder.push(OTHER_EMOS);
		emoOrder.forEach((e) => {
			emoIdx[e] = nodes.length;
			nodes.push({ name: e, kind: 'emo', cls: e === OTHER_EMOS ? 'neutral' : classify(e) });
		});

		// links
		const links = [];
		for (const c of chars) links.push({ source: 0, target: charIdx[c.name], value: c.main });
		for (const { char, flows } of charFlows) {
			const merged = {};
			for (const [e, w] of Object.entries(flows)) {
				const key = keepE.has(e) ? e : OTHER_EMOS;
				merged[key] = (merged[key] || 0) + w;
			}
			for (const [e, w] of Object.entries(merged)) {
				links.push({ source: charIdx[char.name], target: emoIdx[e], value: w });
			}
		}
		return { nodes, links };
	}

	// dimensions
	let cw = $state(0);
	const H = 540;
	const M = { top: 14, right: 150, bottom: 14, left: 150 };

	let laid = $derived.by(() => {
		if (cw <= 0) return null;
		const g = buildGraph(account);
		const layout = d3sankey()
			.nodeWidth(14)
			.nodePadding(14)
			.extent([
				[M.left, M.top],
				[cw - M.right, H - M.bottom]
			]);
		return layout({
			nodes: g.nodes.map((d) => ({ ...d })),
			links: g.links.map((d) => ({ ...d }))
		});
	});
	const linkPath = sankeyLinkHorizontal();

	const fmt = (n) => Math.round(n).toLocaleString();
	let hover = $state(null); // a link or node key

	const nodeColor = (n) =>
		n.kind === 'account'
			? '#e6e6e7'
			: n.kind === 'emo'
				? CLS_COLOR[n.cls]
				: n.name === 'Donald Trump'
					? '#EE6677'
					: n.bucket
						? '#565b63'
						: '#9aa0a8';
	// links tint by the emotion they feed (char→emo); account→char stay neutral grey
	const linkColor = (l) => (l.target.kind === 'emo' ? CLS_COLOR[l.target.cls] : '#4a4f57');
</script>

<div class="wrap">
	<div class="toggle" role="group" aria-label="account">
		{#each Object.entries(ACCTS) as [key, label]}
			<button class:on={account === key} onclick={() => (account = key)}>{label}</button>
		{/each}
	</div>

	<div class="chart" bind:clientWidth={cw}>
		{#if laid}
			<svg viewBox="0 0 {cw} {H}" width={cw} height={H} role="presentation">
				<!-- links first, marks on top -->
				<g>
					{#each laid.links as l (l.source.name + '→' + l.target.name)}
						<path
							class="link"
							class:mute={hover && hover !== l.source.name && hover !== l.target.name}
							d={linkPath(l)}
							stroke={linkColor(l)}
							stroke-width={Math.max(1, l.width)}
							onmouseenter={() => (hover = l.target.name)}
							onmouseleave={() => (hover = null)}
							role="presentation"
						/>
					{/each}
				</g>
				<!-- nodes -->
				<g>
					{#each laid.nodes as n (n.name)}
						<rect
							class="node"
							class:mute={hover && hover !== n.name}
							x={n.x0}
							y={n.y0}
							width={n.x1 - n.x0}
							height={Math.max(1, n.y1 - n.y0)}
							fill={nodeColor(n)}
							onmouseenter={() => (hover = n.name)}
							onmouseleave={() => (hover = null)}
							role="presentation"
						/>
						<text
							class="label"
							class:mute={hover && hover !== n.name}
							class:strong={n.name === 'Donald Trump'}
							x={n.kind === 'emo' ? n.x1 + 8 : n.kind === 'account' ? n.x0 - 8 : n.x1 + 8}
							y={(n.y0 + n.y1) / 2}
							text-anchor={n.kind === 'account' ? 'end' : 'start'}
							dominant-baseline="middle"
						>
							{n.name}<tspan class="cnt"> {fmt(n.value)}</tspan>
						</text>
					{/each}
				</g>
			</svg>
		{/if}
	</div>

	<div class="key">
		<span><i style="background:#EE6677"></i> attack emotions</span>
		<span><i style="background:#2f9e6a"></i> hype emotions</span>
		<span><i style="background:#8a8f96"></i> neutral</span>
	</div>
</div>

<style>
	.wrap {
		width: 100%;
	}
	.toggle {
		display: flex;
		gap: 6px;
		justify-content: center;
		margin: 0 0 0.9rem;
	}
	.toggle button {
		font-family: var(--sans);
		font-size: 0.9rem;
		font-weight: 600;
		letter-spacing: 0.01em;
		color: var(--muted);
		background: transparent;
		border: 1px solid #3a3f47;
		border-radius: 999px;
		padding: 0.32rem 0.95rem;
		cursor: pointer;
		transition:
			color 160ms ease,
			background 160ms ease,
			border-color 160ms ease;
	}
	.toggle button:hover {
		color: var(--ink);
		border-color: #565b63;
	}
	.toggle button.on {
		color: #16181c;
		background: var(--ink);
		border-color: var(--ink);
	}
	.chart {
		width: 100%;
	}
	svg {
		display: block;
		width: 100%;
		height: auto;
	}
	.link {
		fill: none;
		stroke-opacity: 0.34;
		transition: stroke-opacity 160ms ease;
		cursor: pointer;
	}
	.link:hover {
		stroke-opacity: 0.6;
	}
	.link.mute {
		stroke-opacity: 0.07;
	}
	.node {
		transition: opacity 160ms ease;
		cursor: pointer;
	}
	.node.mute {
		opacity: 0.28;
	}
	.label {
		font-family: var(--sans);
		font-size: 0.82rem;
		fill: var(--ink);
		pointer-events: none;
		transition: opacity 160ms ease;
	}
	.label.strong {
		font-weight: 700;
	}
	.label.mute {
		opacity: 0.24;
	}
	.label .cnt {
		fill: var(--muted);
		font-size: 0.74rem;
	}
	.key {
		display: flex;
		gap: 1.2rem;
		justify-content: center;
		margin: 1rem 0 0;
		font-family: var(--sans);
		font-size: 0.78rem;
		color: var(--muted);
	}
	.key i {
		display: inline-block;
		width: 11px;
		height: 11px;
		border-radius: 2px;
		margin-right: 5px;
		vertical-align: -1px;
	}
	@media (max-width: 620px) {
		.label {
			font-size: 0.7rem;
		}
	}
</style>
