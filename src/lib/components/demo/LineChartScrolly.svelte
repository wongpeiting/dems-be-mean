<script>
	import Scroller from '$lib/components/Scroller.svelte';
	import Background from '$lib/components/demo/VizBackground.svelte';

	let index = $state(0);
	let offset = $state(0);
	let progress = $state(0);
	let count = $state(0);
</script>

<section class="demo scroller-demo">
	<Scroller top={0} bottom={1} debugger={true} bind:index bind:offset bind:progress bind:count>
		{#snippet background()}
			<Background {index} {count} />
		{/snippet}

		{#snippet foreground()}
			<div class="step">This is the first step.</div>
			<div class="step">This is the second step.</div>
			<div class="step">This is the third step.</div>
			<div class="step">This is the fourth step.</div>
			<div class="step">This is the fifth step.</div>
		{/snippet}
	</Scroller>
</section>

<style>
	.scroller-demo {
		max-width: none;
	}

	.step {
		height: 100vh;
	}
</style>
