<script module>
	// unique gradient id per instance, so two charts on the page don't collide
	let _uid = 0;
</script>

<script>
	import payoff from '$lib/data/payoff.json';

	// a register-over-time chart on the 7-point scale (−3 hero-worship .. +3 hostile/taunting).
	// Data-driven: pass `vals` + `monthsList` for any account over its own timeline. `lineColor`
	// null → the gradient hero look; a colour → a solid line (for the faceted small-multiples).
	let {
		w = 300,
		h = 128,
		light = false,
		progress = 1,
		title = '',
		vals = payoff.meanness,
		monthsList = payoff.months,
		electionIdx = payoff.electionIdx,
		lineColor = null,
		showY = true,
		xEndpoints = false,
		allGrid = false,
		endAvatar = null,
		series = null // [{ vals, color }] → overlay multiple lines on one shared axis
	} = $props();
	const W = w;
	const H = h;
	const PAD = 8;
	const XAX = 15; // reserved band at the bottom for the time labels
	const LMARG = showY ? 78 : 10; // left band for the 7 register labels (only when shown)
	const B = H - PAD - XAX;
	const friendlyStop = light ? '#c2c6cc' : '#ffffff';
	const N = monthsList.length;
	const LO = -3;
	const HI = 3;
	const X = (i) => PAD + LMARG + (i / (N - 1)) * (W - 2 * PAD - LMARG);
	const Y = (v) => PAD + (1 - (v - LO) / (HI - LO)) * (B - PAD);
	const _u = _uid++;
	const gid = `sparkgrad-${_u}`;
	const clipId = `sparkclip-${_u}`;
	const hasEl = electionIdx != null && electionIdx >= 0 && electionIdx < N;
	const elX = hasEl ? X(electionIdx) : 0;

	const REG = [
		{ v: 3, name: 'hostile' },
		{ v: 2, name: 'mocking' },
		{ v: 1, name: 'critical' },
		{ v: 0, name: 'neutral' },
		{ v: -1, name: 'warm' },
		{ v: -2, name: 'admiring' },
		{ v: -3, name: 'hero-worship' }
	];

	// reveal: draw up to a FRACTIONAL leading edge so the tip glides smoothly between
	// months instead of snapping from data point to data point. (Each series' drawn range
	// is contiguous, so we can interpolate the last segment safely.)
	const edge = $derived(Math.min(N - 1, Math.max(1, progress * (N - 1))));
	const iE = $derived(Math.floor(edge));
	const tE = $derived(edge - iE);
	const lead = $derived.by(() => {
		const v0 = vals[iE];
		if (v0 == null) return null;
		const j = Math.min(iE + 1, N - 1);
		const v1 = vals[j];
		const x = X(iE) + (X(j) - X(iE)) * tE;
		const y = Y(v1 == null ? v0 : v0 + (v1 - v0) * tE);
		return { x, y };
	});
	const whole = $derived(
		vals.slice(0, iE + 1).map((v, i) => `${X(i).toFixed(1)},${Y(v).toFixed(1)}`)
	);
	const line = $derived(
		'M' + whole.join(' L ') + (lead ? ` L${lead.x.toFixed(1)},${lead.y.toFixed(1)}` : '')
	);
	const area = $derived(
		`M${X(0).toFixed(1)},${Y(0).toFixed(1)} L` +
			whole.join(' L ') +
			(lead ? ` L${lead.x.toFixed(1)},${lead.y.toFixed(1)}` : '') +
			` L${(lead ? lead.x : X(iE)).toFixed(1)},${Y(0).toFixed(1)} Z`
	);
	const end = $derived(lead);

	// overlay mode: build a revealed line path for each series on the shared axis, skipping
	// leading nulls (so @whitehouse/@republicans lines only appear once the playhead reaches
	// their first active month).
	const seriesLines = $derived.by(() => {
		if (!series) return null;
		return series.map((s) => {
			const v = s.vals;
			const pts = [];
			for (let i = 0; i <= iE; i++) if (v[i] != null) pts.push(`${X(i).toFixed(1)},${Y(v[i]).toFixed(1)}`);
			let endPt = null;
			const v0 = v[iE];
			if (v0 != null) {
				const j = Math.min(iE + 1, N - 1);
				const v1 = v[j];
				endPt = { x: X(iE) + (X(j) - X(iE)) * tE, y: Y(v1 == null ? v0 : v0 + (v1 - v0) * tE) };
			}
			const d = pts.length
				? 'M' + pts.join(' L ') + (endPt ? ` L${endPt.x.toFixed(1)},${endPt.y.toFixed(1)}` : '')
				: '';
			return { d, color: s.color, end: endPt };
		});
	});

	// x-axis: for a long span, year labels every 2 years; for a short one, the start & end month
	const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
	const fmtMon = (m) => `${MON[+m.slice(5, 7) - 1]} ${m.slice(0, 4)}`;
	const xticks = [];
	if (!xEndpoints && N >= 25) {
		const yrs = monthsList.map((m) => +m.slice(0, 4));
		for (let y = yrs[0]; y <= yrs[yrs.length - 1]; y += 2) {
			const idx = monthsList.indexOf(`${y}-01`);
			if (idx >= 0) xticks.push({ label: '' + y, x: X(idx), anchor: 'middle' });
		}
	} else {
		xticks.push({ label: fmtMon(monthsList[0]), x: X(0), anchor: 'start' });
		xticks.push({ label: fmtMon(monthsList[N - 1]), x: X(N - 1), anchor: 'end' });
	}
</script>

<div class="mean-spark" class:light>
	{#if title}<div class="cap">{title}</div>{/if}
	<svg viewBox="0 0 {W} {H}" width={W} height={H} role="presentation">
		<defs>
			<linearGradient id={gid} gradientUnits="userSpaceOnUse" x1="0" y1={PAD} x2="0" y2={B}>
				<stop offset="0" stop-color={lineColor ?? '#a8478c'} />
				<stop offset="1" stop-color={friendlyStop} />
			</linearGradient>
		</defs>

		{#each REG as t (t.v)}
			{#if allGrid || t.v === 0}
				<line class="grid" class:zero={t.v === 0} x1={PAD + LMARG} x2={W - PAD} y1={Y(t.v)} y2={Y(t.v)} />
			{/if}
			{#if showY}
				<text class="reg-lab" x={PAD + LMARG - 7} y={Y(t.v) + 3} text-anchor="end">
					<tspan class="reg-num">{t.v > 0 ? '+' + t.v : t.v}</tspan>&#8194;{t.name}
				</text>
			{/if}
		{/each}

		{#if hasEl}
			<line class="el" x1={elX} x2={elX} y1={PAD} y2={B} />
			<text class="el-lab" x={elX - 5} y={PAD + 9} text-anchor="end">Trump wins election</text>
		{/if}

		{#if series}
			{#each seriesLines as sl, i (i)}
				<path class="line" d={sl.d} stroke={sl.color} />
				{#if sl.end}
					<circle class="end-dot" cx={sl.end.x} cy={sl.end.y} r="3" fill={sl.color} />
				{/if}
			{/each}
		{:else}
			<path class="area" d={area} fill="url(#{gid})" />
			<path class="line" d={line} stroke="url(#{gid})" />
			{#if end}
				{#if endAvatar}
					<clipPath id={clipId}><circle cx={end.x} cy={end.y} r="11.5" /></clipPath>
					<circle cx={end.x} cy={end.y} r="13" fill="#16181c" stroke={lineColor ?? '#a8478c'} stroke-width="2" />
					<image
						href={endAvatar}
						x={end.x - 11.5}
						y={end.y - 11.5}
						width="23"
						height="23"
						clip-path="url(#{clipId})"
						preserveAspectRatio="xMidYMid slice"
					/>
				{:else}
					<circle class="end-dot" cx={end.x} cy={end.y} r="3.2" fill={lineColor ?? '#a8478c'} />
				{/if}
			{/if}
		{/if}

		{#each xticks as t (t.label)}
			<text class="x-lab" x={t.x} y={H - 3} text-anchor={t.anchor}>{t.label}</text>
		{/each}
	</svg>
</div>

<style>
	.cap {
		font-family: var(--sans);
		font-size: 0.82rem;
		font-weight: 700;
		letter-spacing: 0.01em;
		color: var(--ink);
		margin-bottom: 6px;
	}
	svg {
		display: block;
		overflow: visible;
	}
	.grid {
		stroke: #2f333a;
		stroke-width: 1;
	}
	.grid.zero {
		stroke: #565b63;
	}
	.reg-lab {
		fill: #ffffff;
		font-family: var(--sans);
		font-size: 8.5px;
		font-weight: 700;
		dominant-baseline: middle;
	}
	.reg-lab .reg-num {
		fill: #ffffff;
		font-weight: 700;
	}
	.el {
		stroke: rgba(255, 255, 255, 0.55);
		stroke-width: 1;
	}
	.area {
		opacity: 0.15;
	}
	.line {
		fill: none;
		stroke-width: 1.8;
		stroke-linejoin: round;
	}
	.el-lab {
		fill: #9aa0a6;
		font-family: var(--sans);
		font-size: 8.5px;
		letter-spacing: 0.02em;
	}
	.x-lab {
		fill: #8a8f96;
		font-family: var(--sans);
		font-size: 8.5px;
	}
	/* light theme — chart on a white card */
	.mean-spark.light .cap {
		color: #16181c;
	}
	.mean-spark.light .grid {
		stroke: #e2e5e9;
	}
	.mean-spark.light .grid.zero {
		stroke: #c2c6cc;
	}
	.mean-spark.light .reg-lab {
		fill: #6b7076;
	}
	.mean-spark.light .reg-lab .reg-num {
		fill: #16181c;
	}
	.mean-spark.light .x-lab,
	.mean-spark.light .el-lab {
		fill: #6b7076;
	}
	.mean-spark.light .el {
		stroke: #b4b8be;
		opacity: 0.8;
	}
</style>
