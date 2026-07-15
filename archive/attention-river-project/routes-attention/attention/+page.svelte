<script>
	import Scatter from './Scatter.svelte';
</script>

<article>
	<header>
		<h1>The attention cloud</h1>
		<p class="dek">
			Every dot is one moment a politician was cast in a video. Left to right is how they were
			treated — from <span class="cool">worshipped by their own side</span> to
			<span class="hot">attacked by opponents</span>. Colour is which account did the posting.
			Scroll down to travel from 2022 to today, and watch the White House and Republicans pile in.
		</p>
	</header>

	<Scatter />

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
