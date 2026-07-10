<script>
	let {
		title = 'Panel',
		content
	} = $props();
</script>

<section class="panel">
	<h2 class="title">{title}</h2>
	<div class="content">
		{@render content()}
	</div>
</section>

<style>
	.panel {
		border: 1px solid #e5e5e5;
		border-radius: 0.5rem;
		overflow: hidden;
		background: white;
		box-shadow: 0 2px 8px rgb(0 0 0 / 0.06);
	}

	.title {
		margin: 0;
		padding: 0.75rem 1.25rem;
		background: #f7f7f7;
		border-bottom: 1px solid #e5e5e5;
		font-size: 1rem;
		font-weight: 600;
	}

	.content {
		padding: 1.25rem;
	}
</style>
