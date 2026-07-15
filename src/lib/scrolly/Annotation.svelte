<script>
	// A label/callout anchored at a geographic point, a pixel point, or a fraction
	// of the frame. Text gets a halo so it stays readable over ribbons. Multiline
	// via "\n". The page owns the <svg>; this renders a bare <g>.
	import { getProjectionContext } from '$lib/scrolly/projection.js';

	let {
		at, // one of { lngLat:[lng,lat] } | { xy:[x,y] } | { frac:[fx,fy] }
		text = '',
		dx = 8,
		dy = -8,
		connector = false,
		dot = true,
		color = '#141414',
		align = 'start',
		size = 13,
		opacity = 1
	} = $props();

	const getProjection = getProjectionContext();
	const proj = $derived(getProjection?.());

	const anchor = $derived.by(() => {
		if (!proj || !at) return null;
		if (Array.isArray(at.xy)) return at.xy;
		if (Array.isArray(at.lngLat)) return proj.project(at.lngLat);
		if (Array.isArray(at.frac)) return [at.frac[0] * proj.width, at.frac[1] * proj.height];
		return null;
	});

	const lines = $derived(String(text).split('\n'));
</script>

{#if anchor}
	{@const [ax, ay] = anchor}
	<g class="annotation" style:opacity>
		{#if connector}
			<line x1={ax} y1={ay} x2={ax + dx} y2={ay + dy} stroke={color} stroke-width="1" opacity="0.6" />
		{/if}
		{#if dot}
			<circle cx={ax} cy={ay} r="3" fill={color} />
		{/if}
		<text x={ax + dx} y={ay + dy} text-anchor={align} fill={color} style:font-size="{size}px">
			{#each lines as line, i (i)}
				<tspan x={ax + dx} dy={i === 0 ? 0 : '1.25em'}>{line}</tspan>
			{/each}
		</text>
	</g>
{/if}

<style>
	.annotation {
		transition: opacity 0.3s ease;
	}
	text {
		font-family: system-ui, sans-serif;
		font-weight: 600;
		paint-order: stroke;
		stroke: #fbfbfd;
		stroke-width: 3.5px;
		stroke-linejoin: round;
	}
</style>
