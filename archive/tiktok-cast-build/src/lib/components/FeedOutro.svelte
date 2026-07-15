<script>
  import { onDestroy, onMount, tick } from 'svelte';
  import { base } from '$app/paths';
  import { deterministicShuffle } from '$lib/pack-utils.js';

  let { rounds, moderation, quizN, quizCorrect } = $props();

  // Shuffled rounds — starts as unshuffled (SSR-safe), reshuffled in onMount
  let shuffledRounds = $state(rounds);
  let showToggle = $state(false);
  let tinted = $state(false);

  let feedEl = $state(null);
  let maxIndexSeen = $state(0);

  /** @type {IntersectionObserver | null} */
  let observer = null;

  const DEM_COLOR = 'rgba(85, 136, 213, 0.35)';
  const REP_COLOR = 'rgba(213, 86, 76, 0.35)';

  function overlayColor(answer) {
    return answer === 'dem' ? DEM_COLOR : REP_COLOR;
  }

  onMount(async () => {
    // Reshuffle on client only
    shuffledRounds = deterministicShuffle(rounds, 'feed-outro');

    // Wait for DOM to update after shuffle
    await tick();

    if (!feedEl) return;

    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const idx = Number(entry.target.dataset.index);
          const video = entry.target.querySelector('video');
          if (entry.isIntersecting) {
            if (video) video.play().catch(() => {});
            if (idx > maxIndexSeen) maxIndexSeen = idx;
            if (maxIndexSeen >= 2) showToggle = true;
          } else {
            if (video) video.pause();
          }
        });
      },
      { root: feedEl, threshold: 0.6 }
    );

    const cells = feedEl.querySelectorAll('[data-index]');
    cells.forEach((cell) => observer.observe(cell));
  });

  onDestroy(() => {
    if (observer) {
      observer.disconnect();
      observer = null;
    }
    // Pause all videos
    if (feedEl) {
      feedEl.querySelectorAll('video').forEach((v) => v.pause());
    }
  });
</script>

<section style="width:100%; height:100vh; height:100svh; position:relative;">
  <div
    bind:this={feedEl}
    style="height:100vh; height:100svh; overflow-y:auto; scroll-snap-type:y mandatory;"
  >
    {#each shuffledRounds as round, i (round.id)}
      <div
        data-index={i}
        style="scroll-snap-align:start; height:100vh; height:100svh; position:relative; overflow:hidden;"
      >
        <video
          src="{base}/{round.clip}.mp4"
          poster="{base}/{round.poster}"
          muted
          loop
          playsinline
          preload="none"
          style="width:100%; height:100%; object-fit:cover; display:block;"
        ></video>

        {#if tinted}
          <!-- Coloured overlay -->
          <div
            style="
              position:absolute;
              inset:0;
              background:{overlayColor(round.answer)};
              pointer-events:none;
            "
          ></div>

          <!-- Corner account tag -->
          <div
            style="
              position:absolute;
              bottom:16px;
              left:16px;
              background:rgba(0,0,0,0.55);
              color:#fff;
              font-size:13px;
              font-weight:600;
              padding:4px 10px;
              border-radius:6px;
              pointer-events:none;
            "
          >
            @{round.account}
          </div>
        {/if}
      </div>
    {/each}
  </div>

  {#if showToggle && !tinted}
    <button
      onclick={() => (tinted = true)}
      style="
        position:fixed;
        bottom:28px;
        left:50%;
        transform:translateX(-50%);
        min-height:44px;
        padding:10px 20px;
        background:#222;
        color:#fff;
        border:none;
        border-radius:24px;
        font-size:15px;
        font-weight:600;
        cursor:pointer;
        z-index:100;
        white-space:nowrap;
      "
    >
      show me who posted these
    </button>
  {/if}

  {#if tinted}
    <div
      style="
        position:fixed;
        bottom:0;
        left:0;
        right:0;
        padding:20px 16px 32px;
        background:rgba(0,0,0,0.78);
        color:#fff;
        font-size:15px;
        line-height:1.6;
        pointer-events:none;
        z-index:200;
      "
    >
      <!-- COPY: PT -->
      170 million Americans watch this feed. {#if quizN > 0}You guessed right {quizCorrect} of {quizN}. {/if}TikTok
      doesn't guess at all — {moderation.restricted} restrictions, {moderation.deleted} deletion,
      {moderation.total.toLocaleString()} posts.
    </div>
  {/if}
</section>
