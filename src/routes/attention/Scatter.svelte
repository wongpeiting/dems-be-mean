<script>
	// Every treatment as one dot — no aggregation. Time runs top(2022)→bottom(2026);
	// x = register (platformed ◄ … ► attacked); colour = register. Same editorial
	// vertical-flow style as the Hormuz piece. The reader scrolls the page through time.
	import { scaleLinear } from 'd3-scale';
	import points from '$lib/data/attention_points.json';
	import meta from '$lib/data/attention.json';

	const HEIGHT = 3800;
	const colorFor = scaleLinear().domain([-3, -1, 0, 1, 3]).range(['#2f6690', '#7ba6c9', '#c7c3b8', '#e08a5b', '#cf3b34']).clamp(true);

	// time → y
	const ms = (d) => Date.UTC(+d.slice(0, 4), +d.slice(4, 6) - 1, +d.slice(6, 8));
	const times = points.map((p) => ms(p.d));
	const minT = Math.min(...times);
	const maxT = Math.max(...times);
	const yScale = scaleLinear().domain([minT, maxT]).range([70, HEIGHT - 40]);

	// deterministic jitter so dots don't reflow on resize
	const jitter = (i) => {
		const v = Math.sin(i * 12.9898) * 43758.5453;
		return (v - Math.floor(v) - 0.5) * 0.82; // ±0.41 register units
	};

	let width = $state(0);
	const xScale = $derived(scaleLinear().domain([-3.5, 3.5]).range([width * 0.08, width * 0.92]));

	const dots = $derived.by(() => {
		if (width <= 0) return [];
		return points.map((p, i) => ({
			x: xScale(p.r + jitter(i)),
			y: yScale(ms(p.d)),
			c: colorFor(p.r)
		}));
	});

	// year ticks
	const years = [2022, 2023, 2024, 2025, 2026].map((y) => ({ y, py: yScale(Date.UTC(y, 0, 1)) })).filter((t) => t.py >= 60 && t.py <= HEIGHT);
	// account-arrival annotations
	const eras = [
		{ id: 'whitehouse', text: 'Aug 2025 — the White House joins. A dense cool band pours in on the left: Trump, worshipped.' },
		{ id: 'republicans', text: 'Feb 2026 — the Republicans arrive. The cloud thickens on both sides at once.' }
	].map((e) => {
		const m = meta.accounts.find((a) => a.id === e.id).firstMonth;
		return { ...e, py: yScale(Date.UTC(+m.slice(0, 4), +m.slice(5, 7) - 1, 1)) };
	});
</script>

<div class="scatter" bind:clientWidth={width}>
	{#if width > 0}
		<svg {width} height={HEIGHT} viewBox="0 0 {width} {HEIGHT}" role="presentation">
			<!-- axis labels (top) -->
			<text class="axlbl" x={width * 0.08} y="34" text-anchor="start">◄ platformed by their own side</text>
			<text class="axlbl" x={width * 0.92} y="34" text-anchor="end">attacked by opponents ►</text>
			<line class="axis" x1={xScale(0)} x2={xScale(0)} y1="46" y2={HEIGHT - 20} />

			<!-- year gridlines -->
			{#each years as t (t.y)}
				<line class="tick" x1="0" x2={width} y1={t.py} y2={t.py} />
				<text class="tick-label" x="10" y={t.py - 6}>{t.y}</text>
			{/each}

			<!-- every treatment -->
			{#each dots as d, i (i)}
				<circle cx={d.x} cy={d.y} r="2.6" fill={d.c} fill-opacity="0.5" />
			{/each}

			<!-- account-arrival annotations -->
			{#each eras as e (e.id)}
				<line class="era-rule" x1={width * 0.6} x2={width * 0.97} y1={e.py} y2={e.py} />
				<foreignObject x={width * 0.6} y={e.py + 6} width={width * 0.37} height="90">
					<p class="era">{e.text}</p>
				</foreignObject>
			{/each}
		</svg>
	{/if}
</div>

<style>
	.scatter {
		width: 100%;
		background: #faf9f6;
	}
	svg {
		display: block;
		width: 100%;
	}
	.axis {
		stroke: #ddd8cd;
		stroke-width: 1;
	}
	.axlbl {
		fill: #8a8578;
		font: 600 12px system-ui, sans-serif;
	}
	.tick {
		stroke: #eceae3;
		stroke-width: 1;
	}
	.tick-label {
		fill: #b3ac9e;
		font: 700 13px system-ui, sans-serif;
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
