<script>
  import { onMount } from 'svelte';
  import { Spring } from 'svelte/motion';
  import * as d3 from 'd3';
  import Balloon from './Balloon.svelte';
  import { inflationAt } from '$lib/balloon.js';

  let { person, onopen } = $props();

  let section = $state(null);
  let t = $state(0);

  const totalPosts = person.weekly.reduce((s, w) => s + w.own + w.opp, 0);
  const rScale = d3.scaleSqrt().domain([0, totalPosts]).range([30, 140]);

  let springR = new Spring(30, { stiffness: 0.08, damping: 0.7 });

  const inf = $derived(inflationAt(person.weekly, t));
  const plump = $derived(0.78 + 0.37 * t);
  const currentWeek = $derived(
    person.weekly[Math.min(Math.floor(t * person.weekly.length), person.weekly.length - 1)]
  );
  const oppAirPct = $derived(inf.total > 0 ? Math.round((inf.opp / inf.total) * 100) : 0);

  $effect(() => {
    springR.set(rScale(inf.total));
  });

  function progressOf(isoDate) {
    const n = person.weekly.length;
    let idx = 0;
    for (let i = 0; i < n; i++) {
      if (person.weekly[i].w <= isoDate) idx = i;
      else break;
    }
    return idx / n;
  }

  // COPY: PT — annotation texts for editor review
  const annotations = [
    { at: progressOf('2024-11-06'), text: 'Election night. @democrats goes dark woke.' },
    { at: progressOf('2025-01-20'), text: 'Inauguration day.' },
    { at: progressOf('2025-08-19'), text: '@whitehouse joins TikTok.' },
    { at: progressOf('2026-02-01'), text: '@republicans launches.' },
  ];

  onMount(() => {
    let cleanup = () => {};
    import('gsap').then(({ gsap }) => {
      import('gsap/ScrollTrigger').then(({ ScrollTrigger }) => {
        gsap.registerPlugin(ScrollTrigger);
        const st = ScrollTrigger.create({
          trigger: section,
          start: 'top top',
          end: 'bottom bottom',
          scrub: 0.4,
          onUpdate: (self) => { t = self.progress; }
        });
        cleanup = () => st.kill();
      });
    });
    return () => cleanup();
  });
</script>

<section bind:this={section} class="hero-balloon">
  <div class="sticky-vp">
    <div class="ticker">
      {inf.total} posts · {oppAirPct}% opposition air ·
      {currentWeek?.w ?? ''}
    </div>

    <div class="balloon-wrap">
      <Balloon {person} r={springR.current} {plump} oppShare={inf.total > 0 ? inf.opp / inf.total : person.totals.oppShare} />
    </div>

    {#each annotations as ann}
      <div
        class="annotation"
        style="opacity:{Math.abs(t - ann.at) < 0.06 ? 1 : 0}"
      >
        {ann.text}
      </div>
    {/each}

    {#if t > 0.95}
      <button class="interior-btn" onclick={() => onopen?.()}>
        Look inside the balloon ▸
      </button>
    {/if}
  </div>
</section>

<style>
  .hero-balloon {
    height: 400vh;
    position: relative;
  }
  .sticky-vp {
    position: sticky;
    top: 0;
    height: 100vh;
    height: 100svh;
    overflow: hidden;
  }
  .balloon-wrap {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }
  .ticker {
    position: absolute;
    top: 16px;
    left: 0;
    right: 0;
    text-align: center;
    font-size: 13px;
    color: #444;
    z-index: 10;
    pointer-events: none;
  }
  .annotation {
    position: absolute;
    bottom: 80px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(0, 0, 0, 0.75);
    color: white;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 13px;
    text-align: center;
    transition: opacity 0.3s;
    pointer-events: none;
    max-width: 280px;
    white-space: normal;
  }
  @keyframes fade-in {
    from { opacity: 0; }
    to   { opacity: 1; }
  }
  .interior-btn {
    position: absolute;
    bottom: 40px;
    left: 50%;
    transform: translateX(-50%);
    min-height: 44px;
    padding: 0 20px;
    background: rgba(255, 255, 255, 0.9);
    border: none;
    border-radius: 22px;
    font-size: 15px;
    cursor: pointer;
    white-space: nowrap;
    z-index: 20;
    animation: fade-in 0.25s ease both;
  }
</style>
