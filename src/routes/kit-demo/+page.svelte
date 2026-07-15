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
			<div class="step">
				<p>Three states grow most of the grain that leaves through the Gulf. Here they are as a
					simple chart — each bar as wide as that state’s share.</p>
			</div>
			<div class="step">
				<p>Now watch where that grain actually comes from. The bars lift off and settle onto the
					map, at each state’s place.</p>
			</div>
			<div class="step">
				<p>The routes converge and pour south, merging into a single trunk bound for the export
					terminals on the Gulf coast.</p>
			</div>
			<div class="step">
				<p>The width never lies: the trunk is exactly as thick as the three tributaries combined.</p>
			</div>
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
