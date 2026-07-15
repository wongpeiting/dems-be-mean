<script>
	import VerticalFlow from './VerticalFlow.svelte';
</script>

<article>
	<header>
		<h1>The attention river</h1>
		<p class="dek">
			Every stream is one account's attention on one person — its width the number of videos that
			quarter, its colour how they're portrayed, from <span class="cool">worship</span> to
			<span class="hot">attack</span>. Scroll down to travel from 2022 to today, and watch new
			streams join as each account comes online.
		</p>
	</header>

	<VerticalFlow />

	<footer>
		<p>Source: Stage-2 classification of @democrats, @whitehouse and @republicans TikTok, 2022–2026.</p>
	</footer>
</article>

<style>
	:global(body) {
		margin: 0;
		background: #faf9f6;
	}
	article {
		font-family: system-ui, sans-serif;
		color: #1c1c22;
	}
	header {
		max-width: 40rem;
		margin: 0 auto;
		padding: 4rem 1.5rem 2rem;
		text-align: center;
	}
	h1 {
		font: 700 2.6rem/1.05 Georgia, serif;
		margin: 0 0 1rem;
	}
	.dek {
		font-size: 1.05rem;
		line-height: 1.6;
		color: #3a3a42;
		margin: 0;
	}
	.cool {
		color: #2f6690;
		font-weight: 600;
	}
	.hot {
		color: #cf3b34;
		font-weight: 600;
	}
	footer {
		max-width: 40rem;
		margin: 0 auto;
		padding: 2rem 1.5rem 5rem;
		color: #8a8578;
		font-size: 0.8rem;
	}
</style>
