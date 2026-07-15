<script>
	import Scroller from '$lib/components/Scroller.svelte';
	import Stage from './Stage.svelte';
	import { loadBasemap } from '$lib/scrolly/basemaps.js';
	import config from './story.json';

	let index = $state(0);
	let progress = $state(0);
	let count = $state(0);

	// load the map named in the config (built-in, or a file dropped in static/basemaps/)
	let basemap = $state(null);
	let error = $state(null);
	$effect(() => {
		loadBasemap(config.basemap)
			.then((b) => (basemap = b))
			.catch((e) => (error = e.message));
	});
</script>

{#if error}
	<p class="error">{error}</p>
{:else if basemap}
	<section class="story">
		<Scroller top={0} bottom={1} bind:index bind:progress bind:count>
			{#snippet background()}
				<Stage {config} {basemap} {progress} />
			{/snippet}

			{#snippet foreground()}
				{#each config.steps as step (step)}
					<div class="step"><p>{step}</p></div>
				{/each}
			{/snippet}
		</Scroller>
	</section>
{/if}

<style>
	.story {
		max-width: none;
		font-family: system-ui, sans-serif;
	}
	.step {
		height: 100vh;
		display: flex;
		align-items: flex-end;
		justify-content: flex-start;
		padding: 0 0 8vh 4vw;
		box-sizing: border-box;
		pointer-events: none;
	}
	.step p {
		background: rgba(255, 255, 255, 0.94);
		border: 1px solid #e3e3ea;
		border-radius: 10px;
		padding: 1rem 1.15rem;
		max-width: 20rem;
		margin: 0;
		font-size: 1.02rem;
		line-height: 1.5;
		color: #1c1c22;
		box-shadow: 0 6px 22px rgba(0, 0, 0, 0.1);
	}
	.error {
		max-width: 34rem;
		margin: 4rem auto;
		padding: 1rem 1.25rem;
		font-family: system-ui, sans-serif;
		color: #b91c1c;
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 8px;
	}
	@media (max-width: 640px) {
		.step {
			padding: 0 1rem 6vh;
			justify-content: center;
		}
		.step p {
			max-width: none;
		}
	}
</style>
