<script>
	import dots from '$lib/data/payoff_dots.json';

	// Every @democrats post since the loss as one dot, grouped into four crudeness bands,
	// placed by view count on a log axis. The cloud shifts right as the posts get crueler;
	// a line marks each band's median. `shown` fades the dots in on scroll.
	let { shown = false, portrait = false } = $props();

	const W = 680;
	const PADL = 124; // room for the band labels
	const PADR = 20;
	const TOP = 48; // top lane parks the "Median view count" label in open space above band 1
	const XAX = 30; // bottom band for the view-count axis
	const BAND = 92;
	const R = 1.7;
	const H = TOP + dots.tiers.length * BAND + XAX;

	// broken axis: a LINEAR main zone (0–3M, where ~88% of posts sit) and, after a break,
	// a COMPRESSED LOG tail (3M–46M) so the viral outliers keep their real spread instead of
	// piling into one clump. The break marker signals the scale change.
	const CAP = 3_000_000;
	const MAXV = 46_000_000;
	const GAP = 20; // break gap
	const TAILW = 116; // tail-zone width
	const plotW = W - PADL - PADR;
	const MAINW = plotW - TAILW - GAP;
	const XBREAK = PADL + MAINW; // end of the linear zone (where 3M sits)
	const l3 = Math.log10(CAP);
	const lmax = Math.log10(MAXV);
	const xPos = (v) =>
		v <= CAP
			? PADL + (v / CAP) * MAINW
			: XBREAK + GAP + ((Math.log10(v) - l3) / (lmax - l3)) * TAILW;

	// proper beeswarm: within each band, dots stack symmetrically around the centre line,
	// column by column, so the shape swells where posts pile up. If a dense column would
	// overflow the band, all offsets scale down to fit (dots overlap → a darker centre).
	const layout = dots.tiers.map((t, ti) => {
		const cy = TOP + ti * BAND + BAND / 2;
		const halfH = BAND * 0.46;
		const xs = t.views.map((v, i) => {
			// TikTok rounds views (to the nearest 100K above 1M), which stacks many posts on
			// identical values. Spread each dot within that rounding uncertainty (±3%) so the
			// swarm reads as a cloud, not the rounding grid.
			const jv = ((i * 257 + ti * 89 + 13) % 100) / 100;
			return xPos(v * (1 + (jv - 0.5) * 0.06));
		});
		const colW = R * 2.05;
		const order = xs.map((x, i) => ({ x, i })).sort((a, b) => a.x - b.x);
		const colCount = new Map();
		const yoff = new Array(xs.length);
		for (const o of order) {
			const c = Math.round(o.x / colW);
			const k = colCount.get(c) || 0;
			colCount.set(c, k + 1);
			yoff[o.i] = (k % 2 === 1 ? 1 : -1) * Math.ceil(k / 2) * colW;
		}
		let maxOff = 1;
		for (const y of yoff) if (Math.abs(y) > maxOff) maxOff = Math.abs(y);
		const sc = maxOff > halfH ? halfH / maxOff : 1;
		const pts = xs.map((x, i) => ({ x, y: cy + yoff[i] * sc }));
		return { ...t, cy, medX: xPos(t.median), pts };
	});

	// dot colour ramps white (institutional) → coral red (crass) across the four bands
	const TIER_COLORS = ['#ffffff', '#f9ccd2', '#f499a4', '#ee6677'];

	// annotation: park "Median view count" in the empty top-right space over band 1 and run a
	// swoopy leader arrow from under the "M" down to the "370K" median label, arrowhead on the K
	const mx = layout[0].medX;
	// a plain straight arrow: the label sits up-and-right, one straight line runs down to a tip
	// just to the right of "370K".
	const anno = {
		tx: mx + 64, ty: 30, // "Median view count", anchored left, up-right of the median
		x1: mx + 58, y1: 34, // line start, at the label's left edge
		x2: mx + 16, y2: 45 // arrowhead tip, a gap to the right of the "K" in 370K
	};
	function arrowPoly(x1, y1, x2, y2, size = 6.5, spread = 0.55) {
		const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 1;
		const ux = dx / L, uy = dy / L;
		const bx = x2 - ux * size, by = y2 - uy * size;
		const px = -uy, py = ux, w = size * spread;
		return `${x2},${y2} ${bx + px * w},${by + py * w} ${bx - px * w},${by - py * w}`;
	}

	const ticks = [1000000, 2000000, 3000000];
	const tailTicks = [10000000, 40000000];
	const fmtTick = (n) => n / 1e6 + 'M';
	const fmtMed = (n) => (n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : Math.round(n / 1e3) + 'K');

	// ---- PORTRAIT (mobile): transposed — the four crudeness levels are COLUMNS across the top,
	// view count runs DOWN the y-axis (broken: linear 0–3M, then a compressed log tail).
	const Wp = 384;
	const PADTp = 70; // top band: column labels + medians
	const PADBp = 24;
	const LAXp = 42; // left band for the view-count axis
	const PADRp = 12;
	const GAPp = 16;
	const TAILHp = 130;
	const BANDp = 380; // main (linear) zone height
	const Hp = PADTp + BANDp + GAPp + TAILHp + PADBp;
	const YBREAKp = PADTp + BANDp;
	const yPos = (v) =>
		v <= CAP
			? PADTp + (v / CAP) * BANDp
			: YBREAKp + GAPp + ((Math.log10(v) - l3) / (lmax - l3)) * TAILHp;
	const bandW = (Wp - LAXp - PADRp) / dots.tiers.length;
	const layoutP = dots.tiers.map((t, ti) => {
		const cx = LAXp + ti * bandW + bandW / 2;
		const halfW = bandW * 0.42;
		const ys = t.views.map((v, i) => {
			const jv = ((i * 257 + ti * 89 + 13) % 100) / 100;
			return yPos(v * (1 + (jv - 0.5) * 0.06));
		});
		const rowW = R * 2.05;
		const order = ys.map((y, i) => ({ y, i })).sort((a, b) => a.y - b.y);
		const rowCount = new Map();
		const xoff = new Array(ys.length);
		for (const o of order) {
			const c = Math.round(o.y / rowW);
			const k = rowCount.get(c) || 0;
			rowCount.set(c, k + 1);
			xoff[o.i] = (k % 2 === 1 ? 1 : -1) * Math.ceil(k / 2) * rowW;
		}
		let maxOff = 1;
		for (const x of xoff) if (Math.abs(x) > maxOff) maxOff = Math.abs(x);
		const sc = maxOff > halfW ? halfW / maxOff : 1;
		const pts = ys.map((y, i) => ({ y, x: cx + xoff[i] * sc }));
		return { ...t, cx, halfW, medY: yPos(t.median), pts };
	});
</script>

{#if !portrait}
<svg viewBox="0 0 {W} {H}" width={W} height={H} role="presentation">
	<!-- main zone gridlines (linear 0–3M) -->
	{#each ticks as tk (tk)}
		<line class="sw-grid" x1={xPos(tk)} x2={xPos(tk)} y1={TOP} y2={H - XAX} />
		<text class="sw-xlab" x={xPos(tk)} y={H - XAX + 17} text-anchor="middle">{fmtTick(tk)}</text>
	{/each}
	<!-- axis break marker -->
	<line class="sw-break" x1={XBREAK + 5} y1={H - XAX - 5} x2={XBREAK + 11} y2={H - XAX + 5} />
	<line class="sw-break" x1={XBREAK + 10} y1={H - XAX - 5} x2={XBREAK + 16} y2={H - XAX + 5} />
	<!-- tail zone gridlines (compressed log 3M–46M) -->
	{#each tailTicks as tk (tk)}
		<line class="sw-grid" x1={xPos(tk)} x2={xPos(tk)} y1={TOP} y2={H - XAX} />
		<text class="sw-xlab" x={xPos(tk)} y={H - XAX + 17} text-anchor="middle">{fmtTick(tk)}</text>
	{/each}
	<text class="sw-axcap" x={W - PADR} y={H - XAX + 28} text-anchor="end">views</text>

	{#each layout as t, ti (t.k)}
		<text class="sw-label" x={PADL - 12} y={t.cy - 2} text-anchor="end">{t.label}</text>
		<text class="sw-desc" x={PADL - 12} y={t.cy + 10} text-anchor="end">{t.desc}</text>

		<g class="sw-dots" class:on={shown} style:transition-delay="{ti * 160}ms">
			{#each t.pts as p (p.x + '-' + p.y)}
				<circle cx={p.x} cy={p.y} r={R} fill={TIER_COLORS[ti]} />
			{/each}
		</g>

		<line class="sw-med" x1={t.medX} x2={t.medX} y1={t.cy - BAND * 0.44} y2={t.cy + BAND * 0.44} />
		<text class="sw-medlab" x={t.medX} y={t.cy - BAND * 0.44 - 3} text-anchor="middle">
			{fmtMed(t.median)}
		</text>
		{#if ti === 0}
			<text class="sw-anno" x={anno.tx} y={anno.ty} text-anchor="start">Median view count</text>
			<line class="sw-anno-l" x1={anno.x1} y1={anno.y1} x2={anno.x2} y2={anno.y2} />
			<polygon class="sw-anno-h" points={arrowPoly(anno.x1, anno.y1, anno.x2, anno.y2)} />
		{/if}
	{/each}
</svg>
{:else}
<!-- portrait / mobile: crudeness columns across the top, view count down the y-axis -->
<svg viewBox="0 0 {Wp} {Hp}" width={Wp} height={Hp} role="presentation">
	{#each ticks as tk (tk)}
		<line class="sw-grid" x1={LAXp} x2={Wp - PADRp} y1={yPos(tk)} y2={yPos(tk)} />
		<text class="sw-xlab" x={LAXp - 5} y={yPos(tk) + 3} text-anchor="end">{fmtTick(tk)}</text>
	{/each}
	<line class="sw-break" x1={LAXp - 6} y1={YBREAKp + 5} x2={LAXp + 4} y2={YBREAKp + 11} />
	<line class="sw-break" x1={LAXp - 6} y1={YBREAKp + 10} x2={LAXp + 4} y2={YBREAKp + 16} />
	{#each tailTicks as tk (tk)}
		<line class="sw-grid" x1={LAXp} x2={Wp - PADRp} y1={yPos(tk)} y2={yPos(tk)} />
		<text class="sw-xlab" x={LAXp - 5} y={yPos(tk) + 3} text-anchor="end">{fmtTick(tk)}</text>
	{/each}
	<text class="sw-axcap" x={LAXp - 5} y={PADTp - 8} text-anchor="end">views ↓</text>

	{#each layoutP as t, ti (t.k)}
		<text class="sw-label" x={t.cx} y="22" text-anchor="middle">{t.label}</text>
		<text class="sw-desc" x={t.cx} y="35" text-anchor="middle">{t.desc}</text>
		<text class="sw-medlab" x={t.cx} y="52" text-anchor="middle">{fmtMed(t.median)}</text>
		<g class="sw-dots" class:on={shown} style:transition-delay="{ti * 160}ms">
			{#each t.pts as p (p.x + '-' + p.y)}
				<circle cx={p.x} cy={p.y} r={R} fill={TIER_COLORS[ti]} />
			{/each}
		</g>
		<line class="sw-med" x1={t.cx - t.halfW} x2={t.cx + t.halfW} y1={t.medY} y2={t.medY} />
	{/each}
</svg>
{/if}

<style>
	svg {
		display: block;
		width: 100%;
		height: auto;
		overflow: visible;
	}
	.sw-grid {
		stroke: #2a2e34;
		stroke-width: 1;
	}
	.sw-break {
		stroke: #6b7076;
		stroke-width: 1.2;
	}
	.sw-xlab,
	.sw-axcap {
		fill: #8a8f96;
		font-family: var(--sans);
		font-size: 9px;
	}
	.sw-label {
		fill: #ffffff;
		font-family: var(--sans);
		font-weight: 700;
		font-size: 13px;
		dominant-baseline: middle;
	}
	.sw-desc {
		fill: #ffffff;
		font-family: var(--sans);
		font-size: 8.5px;
		dominant-baseline: middle;
	}
	.sw-dots {
		opacity: 0;
		transition: opacity 0.9s ease;
	}
	.sw-dots.on {
		opacity: 0.7;
	}
	.sw-dots circle {
		/* dots read as a density cloud; the median line sits on top */
	}
	.sw-med {
		stroke: #ffffff;
		stroke-width: 1.6;
	}
	.sw-anno {
		fill: #8a8f96;
		font-family: var(--sans);
		font-weight: 700;
		font-size: 9.5px;
	}
	.sw-anno-l {
		stroke: #8a8f96;
		stroke-width: 1.2;
	}
	.sw-anno-h {
		fill: #8a8f96;
	}
	.sw-medlab {
		fill: #ffffff;
		font-family: var(--sans);
		font-weight: 700;
		font-size: 8.5px;
	}
</style>
