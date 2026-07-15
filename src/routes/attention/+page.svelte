<script>
	import Scroller from '$lib/components/Scroller.svelte';
	import AttentionMap from './AttentionMap.svelte';

	let index = $state(0);
	let progress = $state(0);
	let count = $state(0);

	const steps = [
		'For three years, @democrats had political TikTok to itself. Watch where its attention pooled.',
		'Its own stars gathered on the left — Kamala Harris, Obama, Walz — platformed and adored.',
		'On the right, a wall of targets: Musk, the Republican Party, Mike Johnson — attacked in post after post.',
		'August 2025: the White House arrives, pouring cool, worshipful attention into Trump from the other side.',
		'February 2026: the Republicans join. Trump is now the biggest pool of all — fed hot by his enemies, cool by his own.'
	];
</script>

<section class="story">
	<Scroller top={0} bottom={1} bind:index bind:progress bind:count>
		{#snippet background()}
			<AttentionMap {progress} />
		{/snippet}
		{#snippet foreground()}
			{#each steps as step (step)}
				<div class="step"><p>{step}</p></div>
			{/each}
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
		align-items: flex-end;
		justify-content: flex-start;
		padding: 0 0 8vh 4vw;
		box-sizing: border-box;
		pointer-events: none;
	}
	.step p {
		background: rgba(14, 14, 22, 0.9);
		border: 1px solid #33334a;
		border-radius: 10px;
		padding: 1rem 1.15rem;
		max-width: 22rem;
		margin: 0;
		font-size: 1.02rem;
		line-height: 1.5;
		color: #ececf4;
		box-shadow: 0 6px 22px rgba(0, 0, 0, 0.5);
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
