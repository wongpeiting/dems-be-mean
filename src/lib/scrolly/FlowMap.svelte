<script>
	// The signature layer: each flow is one stroked <path> whose width encodes its
	// value. Morphs between schematic (t=0) and geography (t=1) via the `t` prop.
	import { getProjectionContext } from '$lib/scrolly/projection.js';
	import { makeWidthScale, ribbonPath, interpolateFlow } from '$lib/scrolly/geometry.js';

	let {
		flows = [],
		widthDomain = [0, 1],
		widthRange = [3, 40],
		t = 1,
		color = '#141414',
		trunkColor = null,
		samples = 64
	} = $props();

	const getProjection = getProjectionContext();
	const proj = $derived(getProjection?.());

	const widthScale = $derived(makeWidthScale({ domain: widthDomain, range: widthRange }));

	// Denormalize each flow's schematic (0..1 fractions) into pixel space using the
	// current frame size, then morph. Kept in a derived so it recomputes on resize/scroll.
	const rendered = $derived.by(() => {
		if (!proj) return [];
		const W = proj.width;
		const H = proj.height;
		return flows.map((f) => {
			const pxFlow = { ...f, schematic: f.schematic.map(([fx, fy]) => [fx * W, fy * H]) };
			const points = interpolateFlow(pxFlow, proj.project, t, samples);
			return {
				id: f.id,
				kind: f.kind,
				d: ribbonPath(points),
				width: widthScale(f.value)
			};
		});
	});
</script>

{#if proj}
	<g class="flow-map">
		{#each rendered as f (f.id)}
			<path
				d={f.d}
				fill="none"
				stroke={f.kind === 'trunk' && trunkColor ? trunkColor : color}
				stroke-width={f.width}
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
		{/each}
	</g>
{/if}

<style>
	path {
		transition:
			stroke-width 0.4s ease,
			opacity 0.4s ease;
	}
</style>
