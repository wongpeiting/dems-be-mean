<script>
	// Demo background graphic: owns the single <svg> + the shared projection,
	// and renders the kit layers as direct children (so projection context flows
	// cleanly, with no snippet boundary between set and get).
	import GeoLayer from '$lib/scrolly/GeoLayer.svelte';
	import FlowMap from '$lib/scrolly/FlowMap.svelte';
	import Annotation from '$lib/scrolly/Annotation.svelte';
	import { buildProjection, setProjectionContext } from '$lib/scrolly/projection.js';
	import { buildFlows } from '$lib/scrolly/flows.js';
	import states from '$lib/data/us-states.json';

	let { index = 0, progress = 0 } = $props();

	// contiguous US only — drop AK/HI/PR so the map isn't zoomed out to nothing
	const OFFSHORE = new Set(['Alaska', 'Hawaii', 'Puerto Rico']);
	const features = states.features.filter((f) => !OFFSHORE.has(f.properties.NAME));
	const basemap = { type: 'FeatureCollection', features };

	// The friendly, non-coder data contract — this is all an author writes.
	const story = {
		basemap: 'us-states',
		unit: 'million tonnes',
		hub: { label: 'Gulf export', region: 'Louisiana' },
		flows: [
			{ label: 'Iowa', region: 'Iowa', value: 45 },
			{ label: 'Illinois', region: 'Illinois', value: 30 },
			{ label: 'Nebraska', region: 'Nebraska', value: 25 }
		]
	};
	const flowData = buildFlows(story, basemap);
	const total = flowData.widthDomain[1];
	const tributaries = flowData.flows.filter((f) => f.kind === 'tributary');

	// zoom the map to the corridor the story actually uses, so it frames the
	// action (and spreads the labels) instead of showing the whole country tiny
	const focusNames = new Set([...story.flows.map((f) => f.region), story.hub.region]);
	const focus = { type: 'FeatureCollection', features: features.filter((f) => focusNames.has(f.properties.NAME)) };

	let width = $state(0);
	let height = $state(0);

	const isNarrow = $derived(width > 0 && width < 640);
	const labelSize = $derived(isNarrow ? 11 : 13);

	const projection = $derived(
		width > 0 && height > 0
			? buildProjection(basemap, [width, height], {
					fitTo: focus,
					padding: [Math.round(height * 0.16), Math.round(width * 0.14), Math.round(height * 0.16), Math.round(width * 0.14)]
				})
			: null
	);
	setProjectionContext(() => projection);

	// Morph pacing: hold the schematic for the first fifth, morph to geography
	// over the next two-fifths, hold the map after. One number, edited here.
	const clamp01 = (v) => Math.max(0, Math.min(1, v));
	const t = $derived(clamp01((progress - 0.2) / 0.4));
	const mapOpacity = $derived(0.08 + 0.92 * t);
</script>

<div class="stage">
	<div class="frame" bind:clientWidth={width} bind:clientHeight={height}>
		{#if projection}
			<svg viewBox="0 0 {width} {height}" role="presentation">
				<GeoLayer {features} opacity={mapOpacity} />
				<FlowMap
					flows={flowData.flows}
					widthDomain={flowData.widthDomain}
					widthRange={[Math.max(3, width * 0.006), Math.max(20, width * 0.05)]}
					{t}
					trunkColor="#c0392b"
				/>

				<!-- persistent headline (frac anchor, top-left) -->
				<Annotation
					at={{ frac: [0.02, 0.05] }}
					text="Where the grain goes"
					dx={0}
					dy={0}
					dot={false}
					color="#1a1a1a"
					size={isNarrow ? 16 : 20}
				/>

				{#if t < 0.5}
					<!-- schematic mode: label each bar in place (frac anchors → proves frac mode) -->
					{#each tributaries as f (f.id)}
						<Annotation
							at={{ frac: [f.schematic[0][0], 0.1] }}
							text="{f.label} {Math.round((f.value / total) * 100)}%"
							dx={0}
							dy={0}
							dot={false}
							align="middle"
							color="#1a1a1a"
							size={labelSize}
						/>
					{/each}
				{:else}
					<!-- geographic mode: label each source on the map -->
					{#each tributaries as f (f.id)}
						<Annotation
							at={{ lngLat: f.geo[0] }}
							text="{f.label} {Math.round((f.value / total) * 100)}%"
							dx={0}
							dy={-14}
							align="middle"
							color="#1a1a1a"
							size={labelSize}
						/>
					{/each}
				{/if}

				{#if t > 0.7}
					<!-- the Hormuz homage: a red callout explaining the width encoding.
					     anchored to the LEFT of the trunk so it never runs off the frame. -->
					<Annotation
						at={{ lngLat: flowData.hub.point }}
						text={'Width of each line is that\nstate’s share of grain exports.'}
						dx={-16}
						dy={6}
						align="end"
						connector={true}
						color="#c0392b"
						dot={true}
						size={labelSize}
					/>
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
		background: #fbfbfd;
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
