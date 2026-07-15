<script>
	// ProfanityCrossover.svelte
	// Monthly dem/rep profanity rate lines. Nulls create gaps via d3.line().defined().
	// GOP series-start marker: first month where rep is non-null (2025-08).

	import * as d3 from 'd3';

	let { data } = $props();

	let width = $state(0);
	const height = 220;
	const margin = { top: 16, right: 12, bottom: 36, left: 40 };

	const DEM_COLOR = '#5588d5';
	const REP_COLOR = '#d5564c';

	// Parse months to Date objects for d3 time scale
	const parsed = $derived(
		data.map((d) => ({
			date: new Date(d.m + '-01'),
			dem: d.dem,
			rep: d.rep,
			m: d.m
		}))
	);

	const innerW = $derived(width - margin.left - margin.right);
	const innerH = $derived(height - margin.top - margin.bottom);

	const xScale = $derived(
		d3
			.scaleTime()
			.domain(d3.extent(parsed, (d) => d.date))
			.range([0, innerW])
	);

	const allVals = $derived(
		parsed.flatMap((d) => [d.dem, d.rep]).filter((v) => v != null).map((v) => v * 100)
	);
	const yMax = $derived(d3.max(allVals) ?? 20);
	const yScale = $derived(
		d3.scaleLinear().domain([0, yMax * 1.1]).range([innerH, 0]).nice()
	);

	// d3 line generators with defined() for null gaps
	const demLine = $derived(
		d3
			.line()
			.x((d) => xScale(d.date))
			.y((d) => yScale(d.dem * 100))
			.defined((d) => d.dem != null)
	);

	const repLine = $derived(
		d3
			.line()
			.x((d) => xScale(d.date))
			.y((d) => yScale(d.rep * 100))
			.defined((d) => d.rep != null)
	);

	// GOP series-start marker: first month where rep is non-null
	const seriesStartRow = $derived(
		parsed.find((d) => d.rep != null) || null
	);

	// Y ticks as % values
	const yTicksRaw = $derived(yScale.ticks(4));

	// X ticks: yearly
	const xTicks = $derived(
		xScale.ticks(d3.timeYear.every(1))
	);
</script>

<div class="profanity-crossover" bind:clientWidth={width}>
	<p class="chart-title">% of posts with profanity, monthly</p>
	{#if width > 0}
		<svg {width} {height}>
			<g transform={`translate(${margin.left},${margin.top})`}>
				<!-- Gridlines -->
				{#each yTicksRaw as tick}
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
					>{tick.toFixed(0)}%</text>
				{/each}

				<!-- Dem line -->
				<path
					d={demLine(parsed)}
					fill="none"
					stroke={DEM_COLOR}
					stroke-width={2}
					stroke-linejoin="round"
					stroke-linecap="round"
				/>

				<!-- Rep line -->
				<path
					d={repLine(parsed)}
					fill="none"
					stroke={REP_COLOR}
					stroke-width={2}
					stroke-linejoin="round"
					stroke-linecap="round"
				/>

				<!-- GOP series-start marker -->
				{#if seriesStartRow}
					{@const cx = xScale(seriesStartRow.date)}
					{@const cy = yScale(seriesStartRow.rep * 100)}
					<circle cx={cx} cy={cy} r={5} fill={REP_COLOR} stroke="#fff" stroke-width={1.5} />
					<line
						x1={cx}
						x2={cx}
						y1={0}
						y2={innerH}
						stroke="#aaa"
						stroke-width={1}
						stroke-dasharray="3,3"
					/>
					<text
						x={cx + 5}
						y={cy - 8}
						font-size={9}
						fill={REP_COLOR}
						font-weight="600"
					>GOP series begins</text>
				{/if}

				<!-- X axis ticks -->
				{#each xTicks as tick}
					<text
						x={xScale(tick)}
						y={innerH + 14}
						text-anchor="middle"
						font-size={9}
						fill="#666"
					>{tick.getFullYear()}</text>
				{/each}

				<!-- Legend -->
				<rect x={0} y={-2} width={10} height={3} fill={DEM_COLOR} rx={1} />
				<text x={14} y={5} font-size={10} fill="#444">Dems</text>
				<rect x={52} y={-2} width={10} height={3} fill={REP_COLOR} rx={1} />
				<text x={66} y={5} font-size={10} fill="#444">Rep/WH</text>

				<!-- Axis baseline -->
				<line x1={0} x2={innerW} y1={innerH} y2={innerH} stroke="#ccc" stroke-width={1} />
			</g>
		</svg>
	{/if}
</div>

<style>
	.profanity-crossover {
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
</style>
