<script>
	import * as d3 from 'd3';
	import { fade } from 'svelte/transition';
	import payoff from '$lib/data/payoff.json';

	// The payoff for the word wall: the account's average register (meanness) over time,
	// which sits warm for years and then jumps after the November 2024 loss — and a second
	// beat that decomposes that meanness into its stage-2 ingredients (profanity, crudeness,
	// rage-bait, mockery). `step` picks the view, `progress` draws the line as you scroll.
	let { step = 0, progress = 0 } = $props();

	const months = payoff.months;
	const dates = months.map((m) => new Date(+m.slice(0, 4), +m.slice(5, 7) - 1, 1));
	const electionDate = payoff.electionIdx != null ? dates[payoff.electionIdx] : null;

	const INGREDIENTS = [
		{ key: 'profanity', label: 'profanity', color: '#ee6677' },
		{ key: 'crudeness', label: 'crudeness', color: '#cc8a3c' },
		{ key: 'ragebait', label: 'rage-bait', color: '#a8478c' },
		{ key: 'mockery', label: 'mockery', color: '#6a9fd8' }
	];
	const maxShare = Math.max(
		...INGREDIENTS.flatMap((g) => payoff.ingredients[g.key])
	);

	let W = $state(0);
	const H = 480;
	const M = { top: 28, right: 20, bottom: 42, left: 46 };

	const x = $derived(
		d3
			.scaleTime()
			.domain(d3.extent(dates))
			.range([M.left, Math.max(M.left + 1, W - M.right)])
	);
	const yMean = d3.scaleLinear().domain([-3, 3]).range([H - M.bottom, M.top]);
	const yShare = $derived(
		d3
			.scaleLinear()
			.domain([0, maxShare * 1.05])
			.range([H - M.bottom, M.top])
	);

	// draw the line up to the scroll position on the first beat; full once past it
	const shown = $derived(step > 0 ? months.length : Math.max(2, Math.round(progress * months.length)));

	const meanLine = $derived(
		d3
			.line()
			.x((_, i) => x(dates[i]))
			.y((v) => yMean(v))
			.curve(d3.curveMonotoneX)
	);
	const meanArea = $derived(
		d3
			.area()
			.x((_, i) => x(dates[i]))
			.y0(yMean(0))
			.y1((v) => yMean(v))
			.curve(d3.curveMonotoneX)
	);
	const ingLine = (key) =>
		d3
			.line()
			.x((_, i) => x(dates[i]))
			.y((v) => yShare(v))
			.curve(d3.curveMonotoneX)(payoff.ingredients[key].slice(0, shown));

	const meanSlice = $derived(payoff.meanness.slice(0, shown));
	const fmtYear = d3.timeFormat('%Y');
	const yearTicks = $derived(x.ticks ? x.ticks(d3.timeYear.every(1)) : []);
</script>

<div class="stage">
	<div class="chart" bind:clientWidth={W}>
		{#if W > 0}
			<svg viewBox="0 0 {W} {H}" width={W} height={H} role="presentation">
				<!-- y grid + labels -->
				{#if step === 0}
					{#each [-3, -2, -1, 0, 1, 2, 3] as t}
						<line class="grid" class:zero={t === 0} x1={M.left} x2={W - M.right} y1={yMean(t)} y2={yMean(t)} />
						<text class="ytick" x={M.left - 8} y={yMean(t)}>{t > 0 ? '+' + t : t}</text>
					{/each}
					<text class="axis-cap harsh" x={M.left - 8} y={yMean(3) - 14}>hostile →</text>
					<text class="axis-cap warm" x={M.left - 8} y={yMean(-3) + 20}>← friendly</text>
				{:else}
					{#each yShare.ticks(4) as t}
						<line class="grid" x1={M.left} x2={W - M.right} y1={yShare(t)} y2={yShare(t)} />
						<text class="ytick" x={M.left - 8} y={yShare(t)}>{Math.round(t * 100)}%</text>
					{/each}
				{/if}

				<!-- x year labels -->
				{#each yearTicks as d}
					<text class="xtick" x={x(d)} y={H - M.bottom + 20}>{fmtYear(d)}</text>
				{/each}

				<!-- election marker -->
				{#if electionDate}
					<line class="election" x1={x(electionDate)} x2={x(electionDate)} y1={M.top} y2={H - M.bottom} />
					<text class="election-lab" x={x(electionDate) + 6} y={M.top + 12}>Nov 2024 · the loss</text>
				{/if}

				{#if step === 0}
					<!-- meanness line -->
					<path class="mean-area" d={meanArea(meanSlice)} />
					<path class="mean-line" d={meanLine(meanSlice)} />
					{#if shown >= months.length}
						<circle class="mean-dot" cx={x(dates[dates.length - 1])} cy={yMean(payoff.meanness.at(-1))} r="4" />
					{/if}
				{:else}
					<!-- ingredients -->
					{#each INGREDIENTS as g (g.key)}
						<path class="ing-line" style:stroke={g.color} d={ingLine(g.key)} in:fade={{ duration: 300 }} />
					{/each}
				{/if}
			</svg>
		{/if}
	</div>

	{#if step > 0}
		<div class="legend" in:fade={{ duration: 300 }}>
			{#each INGREDIENTS as g (g.key)}
				<span><i style:background={g.color}></i>{g.label}</span>
			{/each}
		</div>
	{/if}
</div>

<style>
	.stage {
		position: sticky;
		top: 0;
		height: 100vh;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		background: #1a1d21;
	}
	.chart {
		width: min(920px, 92vw);
	}
	svg {
		display: block;
		width: 100%;
		height: auto;
		overflow: visible;
	}
	.grid {
		stroke: #2a2e34;
		stroke-width: 1;
	}
	.grid.zero {
		stroke: #4a4f57;
	}
	.ytick,
	.xtick {
		fill: var(--muted);
		font-family: var(--sans);
		font-size: 0.7rem;
	}
	.ytick {
		text-anchor: end;
		dominant-baseline: middle;
	}
	.xtick {
		text-anchor: middle;
	}
	.axis-cap {
		font-family: var(--sans);
		font-size: 0.62rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		text-anchor: end;
	}
	.axis-cap.harsh {
		fill: #a8478c;
	}
	.axis-cap.warm {
		fill: #6a9fd8;
	}
	.election {
		stroke: #e6e6e7;
		stroke-width: 1;
		stroke-dasharray: 3 3;
		opacity: 0.6;
	}
	.election-lab {
		fill: #e6e6e7;
		font-family: var(--sans);
		font-size: 0.68rem;
		font-weight: 600;
	}
	.mean-area {
		fill: #a8478c;
		opacity: 0.16;
	}
	.mean-line {
		fill: none;
		stroke: #a8478c;
		stroke-width: 2.5;
	}
	.mean-dot {
		fill: #a8478c;
	}
	.ing-line {
		fill: none;
		stroke-width: 2.2;
	}
	.legend {
		display: flex;
		gap: 1.1rem;
		margin-top: 1.1rem;
		font-family: var(--sans);
		font-size: 0.8rem;
		color: var(--muted);
	}
	.legend i {
		display: inline-block;
		width: 11px;
		height: 11px;
		border-radius: 2px;
		margin-right: 5px;
		vertical-align: -1px;
	}
</style>
