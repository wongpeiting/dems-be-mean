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

	let width = $state(0);
	let height = $state(0);

	const projection = $derived(
		width > 0 && height > 0
			? buildProjection(basemap, [width, height], { padding: [24, 24, 24, 24] })
			: null
	);
	setProjectionContext(() => projection);
</script>

<div class="stage">
	<div class="frame" bind:clientWidth={width} bind:clientHeight={height}>
		{#if projection}
			<svg viewBox="0 0 {width} {height}" role="presentation">
				<GeoLayer {features} />
				<FlowMap
					flows={flowData.flows}
					widthDomain={flowData.widthDomain}
					widthRange={[Math.max(3, width * 0.006), Math.max(20, width * 0.05)]}
					t={1}
					trunkColor="#c0392b"
				/>

				<!-- % label at each source -->
				{#each tributaries as f (f.id)}
					<Annotation
						at={{ lngLat: f.geo[0] }}
						text="{f.label} {Math.round((f.value / total) * 100)}%"
						dx={10}
						dy={-12}
						color="#1a1a1a"
					/>
				{/each}

				<!-- the Hormuz homage: a red callout explaining the width encoding -->
				<Annotation
					at={{ lngLat: flowData.hub.point }}
					text={'Width of each line is that\nstate’s share of grain exports.'}
					dx={18}
					dy={8}
					connector={true}
					color="#c0392b"
					dot={true}
				/>
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
