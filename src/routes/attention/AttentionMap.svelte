<script>
	// Attention-pool map: people are pools on a platformed(-3)↔attacked(+3) axis,
	// sized by how much attention they've received; each account feeds a ribbon
	// whose width = post volume and colour = register. Scroll = time.
	// Reuses the kit's ribbon geometry + width scale; layout is computed, not geographic.
	import { forceSimulation, forceX, forceY, forceCollide } from 'd3-force';
	import { scaleLinear } from 'd3-scale';
	import { max } from 'd3-array';
	import { makeWidthScale, ribbonPath } from '$lib/scrolly/geometry.js';
	import data from '$lib/data/attention.json';

	let { progress = 0 } = $props();

	let width = $state(0);
	let height = $state(0);

	const months = data.months;
	const firstMonth = Object.fromEntries(data.accounts.map((a) => [a.id, a.firstMonth]));
	const ACCOUNT_LABEL = { democrats: '@democrats', whitehouse: '@whitehouse', republicans: '@republicans' };

	// register → colour (cool worship … hot attack) and → x position
	const colorFor = scaleLinear().domain([-3, 0, 3]).range(['#3f86d6', '#8f8f9c', '#e0483d']).clamp(true);
	const maxTotal = max(data.people, (p) => p.total);

	// scroll → month index (hold ~8% at each end so the first/last states read)
	const monthIndex = $derived(Math.round(Math.max(0, Math.min(1, (progress - 0.08) / 0.84)) * (months.length - 1)));
	const currentMonth = $derived(months[monthIndex]);

	const xScale = $derived(scaleLinear().domain([-3, 3]).range([width * 0.14, width * 0.86]));
	const rScale = $derived(makeWidthScale({ domain: [0, maxTotal], range: [6, Math.min(width, height) * 0.115] }));
	const ribbonWidth = $derived(makeWidthScale({ domain: [0, maxTotal], range: [1, Math.min(width, height) * 0.12] }));

	// stable pool layout: fixed x by register, beeswarm y (sized by FINAL total so
	// spacing never shifts as pools grow over time)
	const poolPos = $derived.by(() => {
		if (width <= 0 || height <= 0) return {};
		const nodes = data.people.map((p) => ({ id: p.id, x: xScale(p.register), y: height * 0.46, r: rScale(p.total) + 6 }));
		const sim = forceSimulation(nodes)
			.force('x', forceX((d) => xScale(d.id ? data.people.find((p) => p.id === d.id).register : 0)).strength(0.5))
			.force('y', forceY(height * 0.46).strength(0.04))
			.force('collide', forceCollide((d) => d.r).strength(0.9))
			.stop();
		for (let i = 0; i < 260; i++) sim.tick();
		return Object.fromEntries(nodes.map((n) => [n.id, [n.x, n.y]]));
	});

	// account source positions along the bottom
	const accountPos = $derived.by(() => {
		const ids = data.accounts.map((a) => a.id);
		const y = height * 0.9;
		// shifted right so the bottom-left step card doesn't cover @democrats
		return Object.fromEntries(ids.map((id, i) => [id, [width * (0.4 + 0.2 * i), y]]));
	});

	// cumulative attention up to the current month
	const frame = $derived.by(() => {
		const perPerson = {}; // id → count
		const perRibbon = {}; // `${acct}|${person}` → {count, sumReg}
		for (const f of data.flows) {
			if (f.month > currentMonth) continue;
			perPerson[f.person] = (perPerson[f.person] ?? 0) + f.count;
			const k = `${f.account}|${f.person}`;
			const r = (perRibbon[k] ??= { count: 0, sumReg: 0, account: f.account, person: f.person });
			r.count += f.count;
			r.sumReg += f.sumReg;
		}
		const onlineAccounts = data.accounts.filter((a) => a.firstMonth <= currentMonth).map((a) => a.id);
		const ribbons = Object.values(perRibbon)
			.filter((r) => r.count > 0)
			.map((r) => {
				const from = accountPos[r.account];
				const to = poolPos[r.person];
				if (!from || !to) return null;
				const mid = [(from[0] + to[0]) / 2, (from[1] + to[1]) / 2 - Math.abs(from[0] - to[0]) * 0.12];
				return {
					id: `${r.account}|${r.person}`,
					d: ribbonPath([from, mid, to]),
					w: ribbonWidth(r.count),
					color: colorFor(r.sumReg / r.count),
					count: r.count
				};
			})
			.filter(Boolean)
			.sort((a, b) => b.count - a.count); // thick ribbons drawn first, thin on top
		const pools = data.people
			.filter((p) => perPerson[p.id] > 0)
			.map((p) => ({ id: p.id, name: p.name, at: poolPos[p.id], r: rScale(perPerson[p.id]), color: colorFor(p.register), n: perPerson[p.id] }));
		return { ribbons, pools, onlineAccounts };
	});
</script>

<div class="stage">
	<div class="frame" bind:clientWidth={width} bind:clientHeight={height}>
		{#if width > 0 && height > 0}
			<svg viewBox="0 0 {width} {height}" role="presentation">
				<!-- axis -->
				<line class="axis" x1={width * 0.08} x2={width * 0.92} y1={height * 0.14} y2={height * 0.14} />
				<text class="axlbl" x={width * 0.08} y={height * 0.14 - 8} text-anchor="start">◄ platformed by their own side</text>
				<text class="axlbl" x={width * 0.92} y={height * 0.14 - 8} text-anchor="end">attacked by opponents ►</text>

				<!-- ribbons (account → pool) -->
				<g class="ribbons">
					{#each frame.ribbons as r (r.id)}
						<path d={r.d} fill="none" stroke={r.color} stroke-width={r.w} stroke-linecap="round" opacity="0.62" />
					{/each}
				</g>

				<!-- pools -->
				<g class="pools">
					{#each frame.pools as p (p.id)}
						<circle cx={p.at[0]} cy={p.at[1]} r={p.r} fill={p.color} fill-opacity="0.9" stroke="#0b0b10" stroke-width="1.5" />
						{#if p.r > 16}
							<text class="pool-label" x={p.at[0]} y={p.at[1] + p.r + 13} text-anchor="middle">{p.name}</text>
						{/if}
					{/each}
				</g>

				<!-- account sources -->
				<g class="accounts">
					{#each data.accounts as a (a.id)}
						{@const online = frame.onlineAccounts.includes(a.id)}
						{@const pos = accountPos[a.id]}
						<g opacity={online ? 1 : 0.18}>
							<circle cx={pos[0]} cy={pos[1]} r="7" fill="#f2f2f5" stroke="#0b0b10" stroke-width="1.5" />
							<text class="acct-label" x={pos[0]} y={pos[1] + 22} text-anchor="middle">{ACCOUNT_LABEL[a.id]}</text>
						</g>
					{/each}
				</g>

				<text class="clock" x={width * 0.92} y={height * 0.94} text-anchor="end">{currentMonth}</text>
			</svg>
		{/if}
	</div>
</div>

<style>
	.stage {
		width: 100%;
		height: 100vh;
		box-sizing: border-box;
		display: flex;
		padding: 1.25rem;
		background: radial-gradient(120% 80% at 50% 0%, #17172a 0%, #0b0b10 60%);
	}
	.frame {
		flex: 1;
		min-height: 0;
		width: 100%;
	}
	svg {
		width: 100%;
		height: 100%;
		display: block;
		font-family: system-ui, sans-serif;
	}
	.axis {
		stroke: #33334a;
		stroke-width: 1;
	}
	.axlbl {
		fill: #8a8aa0;
		font-size: 12px;
		letter-spacing: 0.02em;
	}
	path {
		transition: stroke-width 0.4s ease;
	}
	circle {
		transition: r 0.4s ease;
	}
	.pool-label {
		fill: #fff;
		font-size: 12px;
		font-weight: 600;
		paint-order: stroke;
		stroke: #0b0b10;
		stroke-width: 3px;
	}
	.acct-label {
		fill: #e8e8f0;
		font-size: 12px;
		font-weight: 700;
	}
	.clock {
		fill: #b7b7c8;
		font-size: 22px;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
	}
</style>
