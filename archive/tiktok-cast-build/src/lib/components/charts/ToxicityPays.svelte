<script>
	// ToxicityPays.svelte
	// Paired horizontal bars per account: attackMedian (filled) vs otherMedian (outlined).
	// pending:true rows render grey + "awaiting classification" note.
	// Props: data (toxicityPays array), era (string, default "headtohead")

	import * as d3 from 'd3';

	let { data, era = 'headtohead' } = $props();

	let width = $state(0);
	const height = 220;
	const margin = { top: 16, right: 60, bottom: 32, left: 90 };

	const DEM_COLOR = '#5588d5';
	const REP_COLOR = '#d5564c';
	const PENDING_COLOR = '#999';

	function accountColor(account, pending) {
		if (pending) return PENDING_COLOR;
		return account === 'democrats' ? DEM_COLOR : REP_COLOR;
	}

	const MIN_N = 10;
	const allRows = $derived(data.filter((d) => d.era === era));
	const rows = $derived(allRows.filter((d) => d.n >= MIN_N));
	const suppressedCount = $derived(allRows.length - rows.length);

	const innerW = $derived(width - margin.left - margin.right);
	const innerH = $derived(height - margin.top - margin.bottom);

	const xMax = $derived(
		d3.max(rows, (d) => Math.max(d.attackMedian, d.otherMedian)) ?? 1
	);
	const xScale = $derived(
		d3.scaleLinear().domain([0, xMax * 1.05]).range([0, innerW]).nice()
	);

	// Band scale for accounts, each with two sub-bars
	const accounts = $derived(rows.map((d) => d.account));
	const yBand = $derived(
		d3.scaleBand().domain(accounts).range([0, innerH]).padding(0.3)
	);
	const subBand = $derived(
		d3.scaleBand().domain(['attack', 'other']).range([0, yBand.bandwidth()]).padding(0.05)
	);

	const fmt = d3.format('.2s');
	const xTicks = $derived(xScale.ticks(3));
</script>

<div class="toxicity-pays" bind:clientWidth={width}>
	<p class="chart-title">Median views: attack vs other posts</p>
	{#if width > 0}
		<svg {width} {height}>
			<g transform={`translate(${margin.left},${margin.top})`}>
				<!-- X gridlines -->
				{#each xTicks as tick}
					<line
						x1={xScale(tick)}
						x2={xScale(tick)}
						y1={0}
						y2={innerH}
						stroke="#e8e8e8"
						stroke-width={1}
					/>
					<text
						x={xScale(tick)}
						y={innerH + 14}
						text-anchor="middle"
						font-size={9}
						fill="#666"
					>{fmt(tick)}</text>
				{/each}

				<!-- Bars per account -->
				{#each rows as row}
					{@const color = accountColor(row.account, row.pending)}
					{@const yBase = yBand(row.account)}

					<!-- Account label -->
					<text
						x={-8}
						y={yBase + yBand.bandwidth() / 2}
						text-anchor="end"
						dominant-baseline="middle"
						font-size={10}
						fill={row.pending ? PENDING_COLOR : '#333'}
						font-weight={row.pending ? '400' : '600'}
					>{row.account}</text>

					<!-- Attack bar (filled) -->
					{@const attackY = yBase + subBand('attack')}
					{@const attackH = subBand.bandwidth()}
					{@const attackW = xScale(row.attackMedian)}
					<rect
						x={0}
						y={attackY}
						width={attackW}
						height={attackH}
						fill={color}
						rx={2}
						opacity={row.pending ? 0.5 : 1}
					/>
					<!-- Attack value label (inside if overflow) -->
					{@const attackLabel = fmt(row.attackMedian)}
					{#if attackW + 4 + 24 > innerW}
						<text
							x={attackW - 4}
							y={attackY + attackH / 2}
							text-anchor="end"
							dominant-baseline="middle"
							font-size={9}
							fill="white"
						>{attackLabel}</text>
					{:else}
						<text
							x={attackW + 4}
							y={attackY + attackH / 2}
							dominant-baseline="middle"
							font-size={9}
							fill={row.pending ? PENDING_COLOR : '#444'}
						>{attackLabel}</text>
					{/if}

					<!-- Other bar (outlined) -->
					{@const otherY = yBase + subBand('other')}
					{@const otherH = subBand.bandwidth()}
					{@const otherW = xScale(row.otherMedian)}
					<rect
						x={0}
						y={otherY}
						width={otherW}
						height={otherH}
						fill="none"
						stroke={color}
						stroke-width={1.5}
						rx={2}
						opacity={row.pending ? 0.5 : 1}
					/>
					<!-- Other value label (inside if overflow) -->
					{@const otherLabel = fmt(row.otherMedian)}
					{#if otherW + 4 + 24 > innerW}
						<text
							x={otherW - 4}
							y={otherY + otherH / 2}
							text-anchor="end"
							dominant-baseline="middle"
							font-size={9}
							fill="white"
						>{otherLabel}</text>
					{:else}
						<text
							x={otherW + 4}
							y={otherY + otherH / 2}
							dominant-baseline="middle"
							font-size={9}
							fill={row.pending ? PENDING_COLOR : '#444'}
						>{otherLabel}</text>
					{/if}

					<!-- Pending note -->
					{#if row.pending}
						<text
							x={0}
							y={yBase + yBand.bandwidth() + 2}
							font-size={8}
							fill={PENDING_COLOR}
							font-style="italic"
						>awaiting classification</text>
					{/if}
				{/each}

				<!-- Legend -->
				<rect x={0} y={innerH + 22} width={10} height={10} fill="#888" rx={1} />
				<text x={14} y={innerH + 30} font-size={9} fill="#444">attack posts</text>
				<rect x={80} y={innerH + 22} width={10} height={10} fill="none" stroke="#888" stroke-width={1.5} rx={1} />
				<text x={94} y={innerH + 30} font-size={9} fill="#444">other posts</text>

				<!-- Axis baseline -->
				<line x1={0} x2={innerW} y1={innerH} y2={innerH} stroke="#ccc" stroke-width={1} />
			</g>
		</svg>
	{/if}
	{#if suppressedCount > 0}
		<p class="suppressed-note">{suppressedCount} account{suppressedCount === 1 ? '' : 's'} hidden (too few classified posts)</p>
	{/if}
</div>

<style>
	.toxicity-pays {
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
	.suppressed-note {
		margin: 4px 0 0;
		font-size: 11px;
		color: #999;
		font-style: italic;
	}
</style>
