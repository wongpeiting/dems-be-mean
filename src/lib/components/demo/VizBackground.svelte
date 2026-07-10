<script>
	import * as d3 from 'd3';
	import { fade } from 'svelte/transition';
	import dataset from '../../data/regional-metrics.json';

	let { index = 0, count = 1, data = dataset } = $props();

	// One entry per scroll step. Edit this array to change the story.
	const steps = [
		{ metric: 'revenue', highlight: null, annotation: null },
		{ metric: 'users', highlight: null, annotation: null },
		{ metric: 'satisfaction', highlight: null, annotation: null },
		{ metric: 'satisfaction', highlight: 'West', annotation: null },
		{
			metric: 'satisfaction',
			highlight: 'North',
			annotation: { region: 'North', year: 2023, text: 'Lorem ipsum' }
		}
	];

	const margin = { top: 30, right: 30, bottom: 40, left: 46 };
	const colors = { North: '#457b9d', South: '#e76f51', East: '#2a9d8f', West: '#e9c46a' };

	let width = $state(700);
	let height = $state(460);

	// clamp so the last step's state holds once the reader scrolls past it
	const step = $derived(steps[Math.min(index, steps.length - 1)]);
	const metric = $derived(step.metric);
	const highlight = $derived(step.highlight);
	const annotation = $derived(step.annotation);

	const years = $derived([...new Set(data.map((d) => d.year))].sort((a, b) => a - b));
	const regions = $derived([...new Set(data.map((d) => d.region))]);

	const xScale = $derived(
		d3
			.scalePoint()
			.domain(years)
			.range([margin.left, width - margin.right])
	);

	const yScale = $derived(
		d3
			.scaleLinear()
			.domain([0, d3.max(data, (d) => d[metric])])
			.nice()
			.range([height - margin.bottom, margin.top])
	);

	const line = $derived(
		d3
			.line()
			.x((d) => xScale(d.year))
			.y((d) => yScale(d[metric]))
	);

	function seriesFor(region) {
		return data.filter((d) => d.region === region).sort((a, b) => a.year - b.year);
	}

	const annotationPoint = $derived.by(() => {
		if (!annotation) return null;
		const row = data.find((d) => d.region === annotation.region && d.year === annotation.year);
		if (!row) return null;
		return { x: xScale(row.year), y: yScale(row[metric]) };
	});
</script>

<div class="background">
	<div class="chart" bind:clientWidth={width} bind:clientHeight={height}>
		<svg viewBox="0 0 {width} {height}" preserveAspectRatio="none">
			<!-- y axis -->
			{#each yScale.ticks(5) as tick (`${metric}-${tick}`)}
				<g
					class="tick"
					transform="translate(0,{yScale(tick)})"
					transition:fade={{ duration: 250 }}
				>
					<line x1={margin.left} x2={width - margin.right} />
					<text x={margin.left - 8} text-anchor="end" dominant-baseline="middle">{tick}</text>
				</g>
			{/each}

			<!-- x axis -->
			{#each years as year (`${metric}-${year}`)}
				<text
					x={xScale(year)}
					y={height - margin.bottom + 22}
					text-anchor="middle"
					transition:fade={{ duration: 250 }}
				>
					{year}
				</text>
			{/each}

			<!-- one line per region -->
			{#each regions as region (region)}
				<path
					d={line(seriesFor(region))}
					fill="none"
					stroke={colors[region]}
					stroke-width={highlight === region ? 4 : 2}
					opacity={highlight && highlight !== region ? 0.15 : 1}
				/>
			{/each}

			<!-- annotation, only rendered when the current step has one -->
			{#if annotationPoint}
				<g class="annotation" transform="translate({annotationPoint.x},{annotationPoint.y})">
					<circle r="5" stroke="white" stroke-width="2" />
					<text x="10" y="-10" stroke="white" stroke-width="3" paint-order="stroke fill">
						{annotation.text}
					</text>
				</g>
			{/if}
		</svg>
	</div>
</div>

<style>
	.background {
		display: flex;
		flex-direction: column;
		width: 100%;
		height: 100vh;
		box-sizing: border-box;
		font-family: system-ui, sans-serif;
        padding: 2rem;
	}

	.chart {
		flex: 1;
		width: 100%;
		min-height: 0;
	}

	svg {
		width: 100%;
		height: 100%;
		display: block;
	}

	path {
		transition:
			d 0.5s ease,
			opacity 0.4s ease,
			stroke-width 0.4s ease;
	}

	.tick line {
		stroke: #e2e2e2;
	}

	.tick text {
		font-size: 11px;
		fill: #666;
	}

	svg text {
		font-size: 11px;
		fill: #666;
	}

	.annotation circle {
		fill: #1d3557;
	}

	.annotation text {
		font-size: 13px;
		font-weight: 600;
		fill: #1d3557;
	}
</style>
