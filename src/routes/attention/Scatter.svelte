<script>
	// Every treatment as a FACE cutout of its subject (canvas, so thousands render).
	// x = register (platformed ◄…► attacked); y = time; the ring around each face =
	// which account posted. Institutions with no headshot fall back to a coloured dot.
	import { base } from '$app/paths';
	import { scaleLinear } from 'd3-scale';
	import { onMount } from 'svelte';
	import points from '$lib/data/attention_points.json';
	import meta from '$lib/data/attention.json';
	import manifest from '$lib/data/faces_manifest.json';

	const HEIGHT = 4200;
	const FACE = 26;
	const ACCT_COLOR = { democrats: '#3a76c2', whitehouse: '#e0a13c', republicans: '#c0392b' };
	const ACCT_LABEL = { democrats: '@democrats', whitehouse: '@whitehouse', republicans: '@republicans' };
	const legend = ['democrats', 'whitehouse', 'republicans'];

	const ms = (d) => Date.UTC(+d.slice(0, 4), +d.slice(4, 6) - 1, +d.slice(6, 8));
	const times = points.map((p) => ms(p.d));
	const minT = Math.min(...times);
	const maxT = Math.max(...times);
	const yScale = scaleLinear().domain([minT, maxT]).range([80, HEIGHT - 40]);
	const jitter = (i) => {
		const v = Math.sin(i * 12.9898) * 43758.5453;
		return (v - Math.floor(v) - 0.5) * 0.82;
	};

	// per-point base data (stable)
	const pdata = points.map((p, i) => ({ r: p.r, a: p.a, face: manifest[p.s] || null, jx: jitter(i), t: ms(p.d) }));

	let width = $state(0);
	let canvasEl;
	const sprites = {}; // file → circular offscreen canvas
	let loaded = $state(0);
	let total = 0;
	const dpr = () => Math.min(1.5, typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1);

	const xScale = $derived(scaleLinear().domain([-3.5, 3.5]).range([width * 0.08, width * 0.92]));

	function makeSprite(img) {
		const d = dpr();
		const S = FACE * d;
		const c = document.createElement('canvas');
		c.width = S; c.height = S;
		const g = c.getContext('2d');
		g.beginPath(); g.arc(S / 2, S / 2, S / 2, 0, Math.PI * 2); g.clip();
		g.drawImage(img, 0, 0, S, S);
		return c;
	}

	function draw() {
		if (!canvasEl || width <= 0) return;
		const d = dpr();
		canvasEl.width = width * d; canvasEl.height = HEIGHT * d;
		canvasEl.style.width = width + 'px'; canvasEl.style.height = HEIGHT + 'px';
		const g = canvasEl.getContext('2d');
		g.setTransform(d, 0, 0, d, 0, 0);
		g.clearRect(0, 0, width, HEIGHT);
		const xs = xScale;
		for (const p of pdata) {
			const x = xs(p.r + p.jx);
			const y = yScale(p.t);
			const col = ACCT_COLOR[p.a];
			const spr = p.face ? sprites[p.face] : null;
			if (spr) {
				g.beginPath(); g.arc(x, y, FACE / 2 + 1.6, 0, Math.PI * 2); g.fillStyle = col; g.fill();
				g.drawImage(spr, x - FACE / 2, y - FACE / 2, FACE, FACE);
			} else {
				g.globalAlpha = 0.7; g.beginPath(); g.arc(x, y, 3.4, 0, Math.PI * 2); g.fillStyle = col; g.fill(); g.globalAlpha = 1;
			}
		}
	}

	onMount(() => {
		const files = [...new Set(Object.values(manifest))];
		total = files.length;
		files.forEach((f) => {
			const img = new Image();
			img.onload = () => { sprites[f] = makeSprite(img); loaded++; };
			img.onerror = () => { loaded++; };
			img.src = `${base}/${f}`;
		});
	});

	// redraw on width change, and once all faces are ready
	const ready = $derived(total > 0 && loaded >= total);
	$effect(() => { width; ready; draw(); });

	// overlay reference layer
	const years = [2022, 2023, 2024, 2025, 2026].map((y) => ({ y, py: yScale(Date.UTC(y, 0, 1)) })).filter((t) => t.py >= 70 && t.py <= HEIGHT);
	const eras = [
		{ id: 'whitehouse', text: 'Aug 2025 — the White House joins. A dense amber band pours in on the left: their own side, worshipped.' },
		{ id: 'republicans', text: 'Feb 2026 — the Republicans arrive; red fills in on both sides.' }
	].map((e) => {
		const m = meta.accounts.find((a) => a.id === e.id).firstMonth;
		return { ...e, py: yScale(Date.UTC(+m.slice(0, 4), +m.slice(5, 7) - 1, 1)) };
	});
</script>

<div class="scatter" bind:clientWidth={width} style="height:{HEIGHT}px">
	<canvas bind:this={canvasEl}></canvas>
	{#if width > 0}
		<svg class="overlay" {width} height={HEIGHT} viewBox="0 0 {width} {HEIGHT}" role="presentation">
			<text class="axlbl" x={width * 0.08} y="40" text-anchor="start">◄ platformed by their own side</text>
			<text class="axlbl" x={width * 0.92} y="40" text-anchor="end">attacked by opponents ►</text>
			<line class="axis" x1={xScale(0)} x2={xScale(0)} y1="52" y2={HEIGHT - 20} />
			<g transform="translate({width / 2 - 170}, 16)">
				{#each legend as id, i (id)}
					<circle cx={i * 130} cy="0" r="5" fill={ACCT_COLOR[id]} />
					<text class="leg" x={i * 130 + 10} y="4">{ACCT_LABEL[id]}</text>
				{/each}
			</g>
			{#each years as t (t.y)}
				<line class="tick" x1="0" x2={width} y1={t.py} y2={t.py} />
				<text class="tick-label" x="10" y={t.py - 6}>{t.y}</text>
			{/each}
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
		position: relative;
		width: 100%;
		background: #faf9f6;
	}
	canvas, .overlay {
		position: absolute;
		top: 0;
		left: 0;
	}
	.overlay {
		pointer-events: none;
	}
	.axis { stroke: #ddd8cd; stroke-width: 1; }
	.axlbl { fill: #8a8578; font: 600 12px system-ui, sans-serif; }
	.leg { fill: #444; font: 600 12px system-ui, sans-serif; }
	.tick { stroke: #eceae3; stroke-width: 1; }
	.tick-label { fill: #b3ac9e; font: 700 13px system-ui, sans-serif; }
	.era-rule { stroke: #cf3b34; stroke-width: 1; }
	.era { margin: 0; font: italic 500 14px/1.4 Georgia, serif; color: #cf3b34; }
</style>
