<script>
	import Scroller from '$lib/components/Scroller.svelte';
	import Stage from './Stage.svelte';

	let index = $state(0);
	let progress = $state(0);
	let count = $state(0);
</script>

<section class="story">
	<Scroller top={0} bottom={1} bind:index bind:progress bind:count>
		{#snippet background()}
			<Stage {index} {progress} />
		{/snippet}

		{#snippet foreground()}
			<div class="step"><p>Scroll to walk through the map.</p></div>
			<div class="step"><p>The base geography holds while the story moves.</p></div>
			<div class="step"><p>Flows and annotations come next.</p></div>
		{/snippet}
	</Scroller>
</section>

<style>
	.story {
		max-width: none;
		font-family: system-ui, sans-serif;
	}
	.step {
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		pointer-events: none;
	}
	.step p {
		background: rgba(255, 255, 255, 0.92);
		border: 1px solid #e3e3ea;
		border-radius: 8px;
		padding: 0.9rem 1.1rem;
		max-width: 22rem;
		margin: 0;
		font-size: 1.05rem;
		line-height: 1.5;
		color: #1c1c22;
		box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08);
	}
</style>
