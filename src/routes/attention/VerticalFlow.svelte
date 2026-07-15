<script>
	// A tall vertical time-Sankey, Hormuz-styled: time runs top(2022)→bottom(2026),
	// each stream is one account→target attention flow, width = that quarter's volume
	// (non-additive), colour = register (cool worship … hot attack). Streams enter as
	// tributaries at their first quarter. The reader scrolls the page down through it.
	import { stack, stackOffsetSilhouette, stackOrderNone, area, curveBasis } from 'd3-shape';
	import { scaleLinear } from 'd3-scale';
	import data from '$lib/data/attention.json';

	const N_STREAMS = 14;
	const PER_QUARTER = 150; // px of height per quarter

	const ACCT = { democrats: '@democrats', whitehouse: '@whitehouse', republicans: '@republicans' };
	const quarterOf = (m) => {
		const [y, mo] = m.split('-').map(Number);
		return `${y}-Q${Math.floor((mo - 1) / 3) + 1}`;
	};
	// register → colour (cool worship … hot attack)
	const colorFor = scaleLinear().domain([-3, -1, 0, 1, 3]).range(['#2f6690', '#7ba6c9', '#b9b9c2', '#e08a5b', '#cf3b34']).clamp(true);

	// aggregate monthly flows → per (account,person) stream, per quarter
	const streamMap = {};
	for (const f of data.flows) {
		const key = `${f.account}|${f.person}`;
		const q = quarterOf(f.month);
		const s = (streamMap[key] ??= { account: f.account, person: f.person, byQ: {}, total: 0, sumReg: 0 });
		s.byQ[q] = (s.byQ[q] || 0) + f.count;
		s.total += f.count;
		s.sumReg += f.sumReg;
	}
	// top N streams, ordered by register (cool→hot) so the river runs worship-left → attack-right
	const streams = Object.entries(streamMap)
		.map(([key, s]) => ({ key, ...s, reg: s.sumReg / s.total }))
		.sort((a, b) => b.total - a.total)
		.slice(0, N_STREAMS)
		.sort((a, b) => a.reg - b.reg);

	const quarters = [...new Set(streams.flatMap((s) => Object.keys(s.byQ)))].sort();
	const qIndex = Object.fromEntries(quarters.map((q, i) => [q, i]));

	// series rows (one per quarter) → d3.stack (silhouette = centred streamgraph)
	const rows = quarters.map((q) => {
		const row = { q };
		for (const s of streams) row[s.key] = s.byQ[q] || 0;
		return row;
	});
	const stacked = stack().keys(streams.map((s) => s.key)).order(stackOrderNone).offset(stackOffsetSilhouette)(rows);

	const height = quarters.length * PER_QUARTER;
	let width = $state(0);

	const yOf = (i) => (i / (quarters.length - 1)) * (height - 2 * PER_QUARTER) + PER_QUARTER;
	const halfMax = Math.max(...stacked.flat().flatMap((d) => [Math.abs(d[0]), Math.abs(d[1])]));
	const xScale = $derived(scaleLinear().domain([-halfMax, halfMax]).range([width * 0.14, width * 0.86]));

	const areaGen = $derived(
		area()
			.y((d) => yOf(qIndex[d.data.q]))
			.x0((d) => xScale(d[0]))
			.x1((d) => xScale(d[1]))
			.curve(curveBasis)
	);

	// one label per stream at its WIDEST quarter (so labels spread out in time),
	// then a vertical dodge so they never overlap
	const labels = $derived.by(() => {
		if (width <= 0) return [];
		const raw = stacked
			.map((layer, li) => {
				const s = streams[li];
				let bestI = -1, bestW = 0;
				layer.forEach((d, i) => {
					const w = Math.abs(d[1] - d[0]);
					if (w > bestW) { bestW = w; bestI = i; }
				});
				if (bestI < 0 || bestW <= 0) return null;
				const d = layer[bestI];
				return {
					key: s.key,
					x: (xScale(d[0]) + xScale(d[1])) / 2,
					y: yOf(bestI),
					text: `${s.person} · ${ACCT[s.account]}`,
					color: colorFor(s.reg)
				};
			})
			.filter(Boolean)
			.sort((a, b) => a.y - b.y);
		const MIN = 22;
		for (let i = 1; i < raw.length; i++) {
			if (raw[i].y - raw[i - 1].y < MIN) raw[i].y = raw[i - 1].y + MIN;
		}
		return raw;
	});

	// time gridlines + era annotations placed at their quarter
	const eras = [
		{ q: quarterOf(data.accounts.find((a) => a.id === 'democrats').firstMonth), text: '2022 — @democrats has political TikTok to itself. Its attention already runs hot: attacks on the right, its own stars adored on the left.' },
		{ q: quarterOf(data.accounts.find((a) => a.id === 'whitehouse').firstMonth), text: 'Aug 2025 — the White House arrives and a cool worship-stream pours into Trump, even as the Democrats keep hammering him.' },
		{ q: quarterOf(data.accounts.find((a) => a.id === 'republicans').firstMonth), text: 'Feb 2026 — the Republicans join. Trump is now fed from both temperatures at once.' }
	].map((e) => ({ ...e, y: yOf(qIndex[e.q] ?? 0) }));
	const yearTicks = $derived(quarters.map((q, i) => ({ q, i, y: yOf(i) })).filter((t) => t.q.endsWith('Q1')));
</script>

<div class="flow" bind:clientWidth={width}>
	{#if width > 0}
		<svg {width} {height} viewBox="0 0 {width} {height}" role="presentation">
			<!-- year ticks -->
			{#each yearTicks as t (t.q)}
				<line class="tick" x1="0" x2={width} y1={t.y} y2={t.y} />
				<text class="tick-label" x="10" y={t.y - 6}>{t.q.slice(0, 4)}</text>
			{/each}

			<!-- streams -->
			{#each stacked as layer, li (streams[li].key)}
				<path d={areaGen(layer)} fill={colorFor(streams[li].reg)} fill-opacity="0.88" />
			{/each}

			<!-- stream labels at entry -->
			{#each labels as l (l.key)}
				<text class="stream-label" x={l.x} y={l.y} text-anchor="middle">{l.text}</text>
			{/each}

			<!-- era word-annotations -->
			{#each eras as e (e.q)}
				<line class="era-rule" x1={width * 0.62} x2={width * 0.96} y1={e.y} y2={e.y} />
				<foreignObject x={width * 0.62} y={e.y + 8} width={width * 0.34} height="130">
					<p class="era">{e.text}</p>
				</foreignObject>
			{/each}
		</svg>
	{/if}
</div>

<style>
	.flow {
		width: 100%;
		background: #faf9f6;
	}
	svg {
		display: block;
		width: 100%;
	}
	.tick {
		stroke: #e7e4dd;
		stroke-width: 1;
	}
	.tick-label {
		fill: #b3ac9e;
		font: 700 13px system-ui, sans-serif;
	}
	path {
		transition: fill-opacity 0.2s;
	}
	.stream-label {
		fill: #1a1a1a;
		font: 600 12px system-ui, sans-serif;
		paint-order: stroke;
		stroke: #faf9f6;
		stroke-width: 3px;
	}
	.era-rule {
		stroke: #cf3b34;
		stroke-width: 1;
	}
	.era {
		margin: 0;
		font: italic 500 14px/1.4 Georgia, serif;
		color: #cf3b34;
	}
</style>
