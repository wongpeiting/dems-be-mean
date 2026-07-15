<script>
	// Generic story graphic: everything comes from `config` (story.json) and the
	// loaded `basemap`. Nothing about any specific story lives here.
	import { fade } from 'svelte/transition';
	import GeoLayer from '$lib/scrolly/GeoLayer.svelte';
	import FlowMap from '$lib/scrolly/FlowMap.svelte';
	import Annotation from '$lib/scrolly/Annotation.svelte';
	import { buildProjection, setProjectionContext } from '$lib/scrolly/projection.js';
	import { buildFlows } from '$lib/scrolly/flows.js';

	let { config, basemap, progress = 0 } = $props();

	const colors = config.colors ?? {};

	// optionally drop regions from the drawn map (e.g. offshore territories)
	const exclude = new Set(config.excludeRegions ?? []);
	const features = basemap.features.filter((f) => {
		const name = f.properties?.NAME ?? f.properties?.name;
		return !exclude.has(name);
	});
	const drawn = { type: 'FeatureCollection', features };

	const flowData = buildFlows(config, drawn);
	const total = flowData.widthDomain[1];
	const tributaries = flowData.flows.filter((f) => f.kind === 'tributary');

	// zoom the map to just the places the story uses, so it frames the action
	const focusNames = new Set([...config.flows.map((f) => f.region), config.hub.region].filter(Boolean));
	const focus = { type: 'FeatureCollection', features: features.filter((f) => focusNames.has(f.properties?.NAME ?? f.properties?.name)) };
	const fitTo = focus.features.length ? focus : drawn;

	let width = $state(0);
	let height = $state(0);

	const isNarrow = $derived(width > 0 && width < 640);
	const labelSize = $derived(isNarrow ? 11 : 13);

	const projection = $derived(
		width > 0 && height > 0
			? buildProjection(drawn, [width, height], {
					fitTo,
					padding: [Math.round(height * 0.16), Math.round(width * 0.14), Math.round(height * 0.16), Math.round(width * 0.14)]
				})
			: null
	);
	setProjectionContext(() => projection);

	// Morph pacing: hold schematic, morph, hold map. Overridable from config.
	const pace = config.morph ?? { start: 0.2, span: 0.4 };
	const clamp01 = (v) => Math.max(0, Math.min(1, v));
	const t = $derived(clamp01((progress - pace.start) / pace.span));
	const mapOpacity = $derived(0.08 + 0.92 * t);
</script>

<div class="stage" style:background={colors.background ?? '#ffffff'}>
	<div class="frame" bind:clientWidth={width} bind:clientHeight={height}>
		{#if projection}
			<svg viewBox="0 0 {width} {height}" role="presentation">
				<GeoLayer {features} fill={colors.mapFill ?? '#e7e7ee'} stroke={colors.mapStroke ?? '#fff'} opacity={mapOpacity} />
				<FlowMap
					flows={flowData.flows}
					widthDomain={flowData.widthDomain}
					widthRange={[Math.max(3, width * 0.006), Math.max(20, width * 0.05)]}
					{t}
					color={colors.line ?? '#141414'}
					trunkColor={colors.trunk ?? colors.line ?? '#141414'}
				/>

				{#if config.title}
					<Annotation at={{ frac: [0.02, 0.05] }} text={config.title} dx={0} dy={0} dot={false} color={colors.text ?? '#1a1a1a'} size={isNarrow ? 16 : 20} />
				{/if}

				{#if t < 0.5}
					<g transition:fade={{ duration: 250 }}>
						{#each tributaries as f (f.id)}
							<Annotation at={{ frac: [f.schematic[0][0], 0.1] }} text="{f.label} {Math.round((f.value / total) * 100)}%" dx={0} dy={0} dot={false} align="middle" color={colors.text ?? '#1a1a1a'} size={labelSize} />
						{/each}
					</g>
				{:else}
					<g transition:fade={{ duration: 250 }}>
						{#each tributaries as f (f.id)}
							<Annotation at={{ lngLat: f.geo[0] }} text="{f.label} {Math.round((f.value / total) * 100)}%" dx={0} dy={-14} align="middle" color={colors.text ?? '#1a1a1a'} size={labelSize} />
						{/each}
					</g>
				{/if}

				{#if t > 0.7 && config.callout}
					<g transition:fade={{ duration: 300 }}>
						<Annotation at={{ lngLat: flowData.hub.point }} text={config.callout} dx={-16} dy={6} align="end" connector={true} color={colors.callout ?? '#c0392b'} dot={true} size={labelSize} />
					</g>
				{/if}
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
		padding: 1.5rem;
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
	}
</style>
