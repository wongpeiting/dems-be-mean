<script>
	let {
		title = 'Card title',
		description = 'A short description goes here.',
		accent = '#457b9d'
	} = $props();
</script>

<article class="card" style:--accent={accent}>
	<h2 class="title">{title}</h2>
	<p class="description">{description}</p>
</article>

<style>
	.card {
		padding: 1.25rem 1.5rem;
		border: 1px solid #e5e5e5;
		border-top: 4px solid var(--accent);
		border-radius: 0.5rem;
		background: white;
		box-shadow: 0 2px 8px rgb(0 0 0 / 0.06);
	}

	.title {
		margin: 0 0 0.5rem;
		font-size: 1.25rem;
		line-height: 1.2;
	}

	.description {
		margin: 0;
		color: #555;
		line-height: 1.5;
	}
</style>
