<script>
	import { base } from '$app/paths';
	let { round, revealed = false, onzone = null } = $props();
</script>

<figure class="card" class:revealed>
	<video
		src="{base}/{round.clip}.mp4"
		poster="{base}/{round.poster}"
		autoplay
		muted
		loop
		playsinline
		preload="none"
		onclick={() => onzone?.('video')}
	></video>
	<figcaption>
		<p class="caption" onclick={() => onzone?.('caption')}>{round.caption}</p>
		<p class="sound" onclick={() => onzone?.('sound')}>♫ {round.sound || 'original sound'}</p>
	</figcaption>
	{#if onzone}
		<button class="vibes" onclick={() => onzone('vibes')}>it's just the vibes</button>
	{/if}
</figure>

<style>
	.card {
		position: relative;
		width: min(100%, 390px);
		aspect-ratio: 9/14;
		margin: 0 auto;
		border: 6px solid #222;
		border-radius: 12px;
		overflow: hidden;
		background: #000;
		transition: border-color 0.3s;
	}
	.card.revealed {
		border-color: var(--reveal, #222);
	}
	video {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	figcaption {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		padding: 10px 12px;
		background: linear-gradient(transparent, rgba(0, 0, 0, 0.75));
		color: #fff;
	}
	.caption {
		font-size: 14px;
		margin: 0 0 4px;
	}
	.sound {
		font-size: 12px;
		opacity: 0.85;
		margin: 0;
	}
	.vibes {
		position: absolute;
		top: 8px;
		right: 8px;
		font-size: 12px;
		padding: 4px 8px;
		border-radius: 999px;
		background: rgba(255, 255, 255, 0.85);
		border: none;
		cursor: pointer;
		display: inline-flex;
		align-items: center;
		min-height: 44px;
	}
</style>
