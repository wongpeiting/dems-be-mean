<script>
	// Demo background graphic: owns the single <svg> + the shared projection,
	// and renders the kit layers as direct children (so projection context flows
	// cleanly, with no snippet boundary between set and get).
	import GeoLayer from '$lib/scrolly/GeoLayer.svelte';
	import { buildProjection, setProjectionContext } from '$lib/scrolly/projection.js';
	import states from '$lib/data/us-states.json';

	let { index = 0, progress = 0 } = $props();

	// contiguous US only — drop AK/HI/PR so the map isn't zoomed out to nothing
	const OFFSHORE = new Set(['Alaska', 'Hawaii', 'Puerto Rico']);
	const features = states.features.filter((f) => !OFFSHORE.has(f.properties.NAME));
	const basemap = { type: 'FeatureCollection', features };

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
