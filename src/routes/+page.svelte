<script>
	import { base } from '$app/paths';
</script>

<main>
	<h1>Scrollytelling flow-map kit</h1>
	<p>
		A small Svelte kit for NYT-style scrollytelling flow maps — a sticky map that reveals as you
		scroll, with lines whose width is your number. You write data; the kit draws it.
	</p>
	<p><a href="{base}/kit-demo">See the demo →</a></p>
	<p class="src">Docs: <code>src/lib/scrolly/README.md</code></p>
</main>

<style>
	main {
		max-width: 34rem;
		margin: 0 auto;
		padding: 4rem 1.5rem;
		font-family: system-ui, sans-serif;
		color: #1c1c22;
		line-height: 1.55;
	}
	h1 {
		font-size: 1.9rem;
		margin: 0 0 1rem;
	}
	a {
		color: #c0392b;
		font-weight: 600;
	}
	.src {
		color: #6b7280;
		font-size: 0.9rem;
	}
</style>
