<script>
	let {
		index = 0,
		count = 1,
		colors = ['#1d3557', '#457b9d', '#2a9d8f', '#e9c46a', '#e76f51', '#9b5de5']
	} = $props();

	const color = $derived(colors[index % colors.length]);
</script>

<div class="background" style:background-color={color}>
	<p class="label">
		<span class="current">{index + 1}</span>
		<span class="divider">of</span>
		<span class="total">{count}</span>
	</p>
</div>

<style>
	.background {
		display: grid;
		place-items: center;
		min-height: 100vh;
		padding: 2rem;
	}

	.label {
		margin: 0;
		display: flex;
		align-items: baseline;
		gap: 0.35rem;
		color: white;
		font-family: system-ui, sans-serif;
		font-weight: 600;
		line-height: 1;
	}

	.current {
		font-size: clamp(3rem, 12vw, 6rem);
		letter-spacing: -0.04em;
	}

	.divider {
		font-size: clamp(1rem, 3vw, 1.5rem);
		font-weight: 400;
		opacity: 0.75;
		text-transform: lowercase;
	}

	.total {
		font-size: clamp(1.75rem, 6vw, 3rem);
		opacity: 0.9;
	}
</style>
