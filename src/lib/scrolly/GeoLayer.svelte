<script>
	// Draws GeoJSON features (land / coastlines) using the shared projection.
	// Renders bare <path> elements — the page owns the enclosing <svg>.
	import { getProjectionContext } from '$lib/scrolly/projection.js';

	let {
		features = [],
		fill = '#e7e7ee',
		stroke = '#ffffff',
		strokeWidth = 0.75,
		opacity = 1
	} = $props();

	const getProjection = getProjectionContext();
	const proj = $derived(getProjection?.());
</script>

{#if proj}
	<g class="geo-layer" style:opacity>
		{#each features as feature, i (i)}
			<path d={proj.path(feature)} {fill} {stroke} stroke-width={strokeWidth} />
		{/each}
	</g>
{/if}

<style>
	.geo-layer {
		transition: opacity 0.5s ease;
	}
</style>
