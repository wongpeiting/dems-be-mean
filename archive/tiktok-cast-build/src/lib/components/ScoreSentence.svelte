<script>
	import { scoreSentence } from '$lib/quiz.svelte.js';
	let { n, correct } = $props();
</script>

<p class="score" aria-live="polite">{scoreSentence(n, correct)}</p>

<style>
	.score {
		text-align: center;
		background: #fffcd9;
		padding: 6px 10px;
		border-radius: 6px;
		max-width: 390px;
		margin: 10px auto;
		font-size: 14px;
	}
</style>
