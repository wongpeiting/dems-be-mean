<script>
	// ModerationStat.svelte
	// Big-number block showing restrictions, deletions, and total posts.

	let { data } = $props();
</script>

<div class="moderation-stat">
	<p class="stat-line">
		{data.restricted.toLocaleString()} {data.restricted === 1 ? 'restriction' : 'restrictions'}
		·
		{data.deleted.toLocaleString()} {data.deleted === 1 ? 'deletion' : 'deletions'}
		·
		{data.total.toLocaleString()} posts
	</p>
</div>

<style>
	.moderation-stat {
		text-align: center;
		padding: 24px 12px;
		background: #f9f9f9;
		border-radius: 8px;
		margin: 16px 0;
	}
	.stat-line {
		font-size: 22px;
		font-weight: 800;
		line-height: 1.4;
		color: #111;
		margin: 0;
		letter-spacing: -0.01em;
	}
</style>
