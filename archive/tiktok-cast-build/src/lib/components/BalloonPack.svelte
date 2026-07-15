<script>
  import * as d3 from 'd3';
  import Balloon from './Balloon.svelte';
  import Scroller from './Scroller.svelte';
  import { topShare } from '$lib/pack-utils.js';

  const MODERATION_TOTAL = 5860;
  const OPP_SHARE_THRESHOLD = 0.2;

  let { people, onopen } = $props();

  let w = $state(0);
  let scrollIndex = $state(0);

  // Compute share stat for step 0 copy
  const share = $derived(topShare(people, MODERATION_TOTAL));
  const sharePercent = $derived(Math.round(share * 100));

  const trump = $derived(people.find(p => p.slug === 'donald-trump') ?? people[0]);
  const trumpOppPercent = $derived(Math.round((trump?.totals?.oppShare ?? 0) * 100));

  // People with oppShare < 0.2 (platformed, not attacked)
  const platformedGroup = $derived(people.filter((p) => p.totals.oppShare < OPP_SHARE_THRESHOLD));
  const platformedNames = $derived(
    platformedGroup.length > 0
      ? platformedGroup.length === 1
        ? platformedGroup[0].name
        : platformedGroup.length === 2
          ? platformedGroup.map((p) => p.name).join(' and ')
          : platformedGroup.slice(0, -1).map((p) => p.name).join(', ') + ', and ' + platformedGroup.at(-1).name
      : ''
  );

  // d3 pack layout — recomputed whenever width changes
  const nodes = $derived((() => {
    if (w === 0) return [];
    const h = w * 0.85;
    const root = d3
      .hierarchy({ children: people })
      .sum((d) => d.totals?.posts ?? 0);
    d3.pack().size([w, h]).padding(8)(root);
    return root.leaves();
  })());

  // Per-node opacity map based on scroll step
  const opacityMap = $derived(
    scrollIndex === 1
      ? Object.fromEntries(people.map((p) => [p.slug, p.slug === 'donald-trump' ? 1 : 0.25]))
      : scrollIndex === 2
        ? Object.fromEntries(
            people.map((p) => [p.slug, p.totals.oppShare < OPP_SHARE_THRESHOLD ? 1 : 0.25])
          )
        : Object.fromEntries(people.map((p) => [p.slug, 1]))
  );

  // Whether balloons are interactive
  const balloonsInteractive = $derived(scrollIndex === 3);
</script>

<div bind:clientWidth={w} style="width:100%">
  {#if w > 0}
    <Scroller bind:index={scrollIndex}>
      {#snippet background()}
        <div
          style="position:relative; width:{w}px; height:{w * 0.85}px; overflow:visible;"
        >
          {#each nodes as node (node.data.slug)}
            {@const person = node.data}
            <button
              class="balloon-btn"
              disabled={!balloonsInteractive}
              style="
                position:absolute;
                left:{node.x - node.r * 1.2}px;
                top:{node.y - node.r * 1.9}px;
                opacity:{opacityMap[person.slug]};
                transition:opacity 0.4s;
                pointer-events:{balloonsInteractive ? 'auto' : 'none'};
                cursor:{balloonsInteractive ? 'pointer' : 'default'};
              "
              onclick={() => { if (!balloonsInteractive) return; onopen(person.slug); }}
              aria-label="Open {person.name} profile"
            >
              <Balloon {person} r={node.r} labeled={node.r > 40} />
            </button>
          {/each}
        </div>
      {/snippet}

      {#snippet foreground()}
        <!-- Step 0: Header stat -->
        <!-- COPY: PT -->
        <div
          class="step-card"
          style="pointer-events:none; min-height:90svh; display:flex; align-items:flex-end; padding-bottom:32px;"
        >
          <div class="step-content">
            <p class="step-copy">
              These {people.length} people account for <strong>{sharePercent}%</strong> of everything
              both parties posted.
            </p>
          </div>
        </div>

        <!-- Step 1: Trump highlight -->
        <!-- COPY: PT -->
        <div
          class="step-card"
          style="pointer-events:none; min-height:90svh; display:flex; align-items:flex-end; padding-bottom:32px;"
        >
          <div class="step-content">
            <p class="step-copy">
              His opponents inflate him more than his own side does —
              <strong>{trumpOppPercent}%</strong> opposition air.
            </p>
          </div>
        </div>

        <!-- Step 2: Platformed, not attacked -->
        <!-- COPY: PT -->
        <div
          class="step-card"
          style="pointer-events:none; min-height:90svh; display:flex; align-items:flex-end; padding-bottom:32px;"
        >
          <div class="step-content">
            <p class="step-copy">
              {platformedNames} — these accounts get platformed, not attacked.
            </p>
          </div>
        </div>

        <!-- Step 3: Free explore -->
        <!-- COPY: PT -->
        <div
          class="step-card"
          style="pointer-events:none; min-height:90svh; display:flex; align-items:flex-end; padding-bottom:32px;"
        >
          <div class="step-content">
            <!-- COPY:PT — softened; full interior only exists for Trump -->
            <p class="step-copy">Tap any balloon for a quick look. Trump has the full breakdown.</p>
          </div>
        </div>
      {/snippet}
    </Scroller>
  {/if}
</div>

<style>
  .balloon-btn {
    background: none;
    border: none;
    padding: 0;
    margin: 0;
    display: inline-block;
  }

  .step-card {
    width: 100%;
    box-sizing: border-box;
  }

  .step-content {
    background: rgba(255, 255, 255, 0.88);
    border-radius: 10px;
    padding: 16px 18px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    margin: 0 16px;
    pointer-events: auto;
  }

  .step-copy {
    font-size: 16px;
    line-height: 1.55;
    color: #222;
    margin: 0;
  }
</style>
