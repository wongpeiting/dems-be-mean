<script>
	// EraStepline.svelte
	// NOTE: The toxicityPays data has only 3 rows and uses medians (not attack-share %),
	// so a step-line per account group across eras would be misleading. Instead this
	// renders a grouped bar chart of post COUNTS from `eras`. It shows that dem posting
	// volume was high pre-election (1,868), dipped post-election (1,004), and climbed
	// again in head-to-head (1,942 dem / 1,046 rep) — providing volume context rather
	// than attack shares.

	import * as d3 from 'd3';

	let { data, pending = false } = $props();

	// Container width via bind:clientWidth
	let width = $state(0);
	const height = 220;
	const margin = { top: 16, right: 12, bottom: 40, left: 46 };

	const DEM_COLOR = '#5588d5';
	const REP_COLOR = '#d5564c';

	const ERA_LABELS = {
		dem_pre: 'Pre',
		dem_post: 'Post',
		headtohead: 'H2H'
	};

	const eraKeys = ['dem_pre', 'dem_post', 'headtohead'];
	const sides = ['dem', 'rep'];

	// Flat rows: { era, side, count }
	const rows = $derived(
		eraKeys.flatMap((era) =>
			sides.map((side) => ({
				era,
				side,
				count: data[era]?.[side]?.count ?? 0
			}))
		)
	);

	const innerW = $derived(width - margin.left - margin.right);
	const innerH = $derived(height - margin.top - margin.bottom);

	const xScale = $derived(
		d3
			.scaleBand()
			.domain(eraKeys)
			.range([0, innerW])
			.padding(0.25)
	);

	const xSub = $derived(
		d3.scaleBand().domain(sides).range([0, xScale.bandwidth()]).padding(0.05)
	);

	const yMax = $derived(d3.max(rows, (d) => d.count) ?? 0);
	const yScale = $derived(
		d3.scaleLinear().domain([0, yMax * 1.1]).range([innerH, 0]).nice()
	);

	const yTicks = $derived(yScale.ticks(4));

	function barColor(side) {
		if (pending) return '#999';
		return side === 'dem' ? DEM_COLOR : REP_COLOR;
	}
</script>

<div class="era-stepline" bind:clientWidth={width}>
	<p class="chart-title">Posts per era</p>
	{#if width > 0}
		<svg {width} {height}>
			<g transform={`translate(${margin.left},${margin.top})`}>
				<!-- Y gridlines + ticks -->
				{#each yTicks as tick}
					<line
						x1={0}
						x2={innerW}
						y1={yScale(tick)}
						y2={yScale(tick)}
						stroke="#e8e8e8"
						stroke-width={1}
					/>
					<text
						x={-6}
						y={yScale(tick)}
						text-anchor="end"
						dominant-baseline="middle"
						font-size={10}
						fill="#666"
					>{tick.toLocaleString()}</text>
				{/each}

				<!-- Bars -->
				{#each eraKeys as era}
					{#each sides as side}
						{@const count = data[era]?.[side]?.count ?? 0}
						{@const x = xScale(era) + xSub(side)}
						{@const barW = xSub.bandwidth()}
						{@const barH = innerH - yScale(count)}
						{@const y = yScale(count)}
						{#if count > 0}
							<rect
								x={x}
								y={y}
								width={barW}
								height={barH}
								fill={barColor(side)}
								rx={2}
							/>
						{/if}
					{/each}
				{/each}

				<!-- X axis labels -->
				{#each eraKeys as era}
					<text
						x={xScale(era) + xScale.bandwidth() / 2}
						y={innerH + 14}
						text-anchor="middle"
						font-size={9}
						fill="#444"
					>{ERA_LABELS[era]}</text>
				{/each}

				<!-- Legend -->
				<rect x={innerW - 80} y={-2} width={10} height={10} fill={DEM_COLOR} rx={1} />
				<text x={innerW - 67} y={7} font-size={10} fill="#444">Dems</text>
				<rect x={innerW - 40} y={-2} width={10} height={10} fill={REP_COLOR} rx={1} />
				<text x={innerW - 27} y={7} font-size={10} fill="#444">Rep</text>

				<!-- Axis baseline -->
				<line x1={0} x2={innerW} y1={innerH} y2={innerH} stroke="#ccc" stroke-width={1} />
			</g>
		</svg>
	{/if}
	{#if pending}
		<p class="pending-note">awaiting classification</p>
	{/if}
</div>

<style>
	.era-stepline {
		width: 100%;
	}
	.chart-title {
		margin: 0 0 8px 0;
		font-size: 12px;
		font-weight: 600;
		color: #333;
	}
	svg {
		display: block;
		overflow: visible;
	}
	.pending-note {
		font-size: 11px;
		color: #999;
		text-align: center;
		margin: 4px 0 0;
	}
</style>
