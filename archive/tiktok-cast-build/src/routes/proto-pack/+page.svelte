<script>
  import * as d3 from 'd3';
  import { base } from '$app/paths';
  import balloons from '$lib/data/balloons.json';

  const REP = '#e0483d', BLUE = '#4d8be0';
  const people = balloons.people;
  let W = $state(0), H = $state(0);
  let hovered = $state(null);

  // Beeswarm: x = share of a figure's videos posted by the OTHER side.
  // Left  = built up almost entirely by their own team (heroes).
  // Right = starred almost entirely by opponents tearing them down (targets).
  // Size  = total videos they star in. Trump is huge AND on the right.
  const maxPosts = d3.max(people, (p) => p.totals.posts);
  let nodes = $derived.by(() => {
    if (W <= 0 || H <= 0) return [];
    const padX = Math.max(80, W * 0.09);
    const x = d3.scaleLinear().domain([0, 1]).range([padX, W - padX]);
    const r = d3.scaleSqrt().domain([0, maxPosts]).range([16, Math.min(H, W) * 0.145]);
    const n = people.map((p) => ({
      d: p, r: r(p.totals.posts), tx: x(p.totals.oppShare), ty: H * 0.52
    }));
    const sim = d3.forceSimulation(n)
      .force('x', d3.forceX((d) => d.tx).strength(0.28))
      .force('y', d3.forceY((d) => d.ty).strength(0.06))
      .force('collide', d3.forceCollide((d) => d.r + 4).strength(0.95))
      .stop();
    for (let i = 0; i < 320; i++) sim.tick();
    return n;
  });

  function arcs(r, oppShare) {
    const C = 2 * Math.PI * r, own = 1 - oppShare;
    return { C, ownLen: own * C, oppLen: oppShare * C, oppOffset: -own * C };
  }
  const trump = $derived(nodes.find((n) => n.d.slug === 'donald-trump'));
</script>

<main>
  <header>
    <p class="eyebrow">Who stars in official party TikTok · Nov 2024 – now</p>
    <h1>The Democrats can’t stop making<br /><span class="hl">Trump</span> their main character.</h1>
    <p class="dek">
      Every face is a politician, sized by how many of the two parties’ videos they star in, and
      placed by <em>who</em> is putting them on screen — from figures
      <span class="own">their own side builds up</span> on the left, to those
      <span class="opp">the other side drags on</span> to knock them down, on the right.
    </p>
  </header>

  <section class="stage" bind:clientWidth={W} bind:clientHeight={H}>
    {#if W > 0}
      <svg viewBox="0 0 {W} {H}" role="presentation">
        <defs>
          <clipPath id="c" clipPathUnits="objectBoundingBox"><circle cx="0.5" cy="0.5" r="0.5" /></clipPath>
        </defs>

        <!-- axis -->
        <line x1={W*0.06} y1={H*0.9} x2={W*0.94} y2={H*0.9} class="axis" />
        <text x={W*0.06} y={H*0.94} class="axlbl" text-anchor="start">◄ built up by their own side</text>
        <text x={W*0.94} y={H*0.94} class="axlbl" text-anchor="end">dragged by the other side ►</text>

        {#each nodes as n (n.d.slug)}
          {@const a = arcs(n.r, n.d.totals.oppShare)}
          <g transform="translate({n.x},{n.y})" class="node" class:dim={hovered && hovered !== n.d.slug}
             onpointerenter={() => hovered = n.d.slug} onpointerleave={() => hovered = null} role="presentation">
            <circle r={n.r} class="halo" />
            <image href="{base}/{n.d.face}" x={-n.r} y={-n.r} width={n.r*2} height={n.r*2}
                   preserveAspectRatio="xMidYMid slice" clip-path="url(#c)" />
            <circle r={n.r} fill="none" stroke={REP} stroke-width={Math.max(2.5, n.r*0.08)}
                    stroke-dasharray="{a.ownLen} {a.C}" transform="rotate(-90)" />
            <circle r={n.r} fill="none" stroke={BLUE} stroke-width={Math.max(2.5, n.r*0.08)}
                    stroke-dasharray="{a.oppLen} {a.C}" stroke-dashoffset={a.oppOffset} transform="rotate(-90)" />
            {#if n.r > 30}
              <text class="nm" y={n.r + 15}>{n.d.name}</text>
              <text class="pct" y={n.r + 30}>{n.d.totals.posts} videos</text>
            {/if}
          </g>
        {/each}
      </svg>

      {#if trump}
        <div class="callout" style="left: {(trump.x/W)*100}%; top: {((trump.y - trump.r)/H)*100}%">
          <b>1,198</b> Democratic videos star Trump — more than their five biggest
          <span class="own">own-side</span> figures <b>combined</b> (974).
        </div>
      {/if}
    {/if}
  </section>

  <footer>Left–right = share of a figure’s videos posted by the opposing party · Size = total videos · Ring = <span class="own">own-side</span> vs <span class="opp">opponent</span> air · Stage-2 classification (partial)</footer>
</main>

<style>
  @import url('https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;500;600;700&display=swap');
  :global(body) { margin: 0; background: #0b0b10; }
  main {
    min-height: 100vh; background: radial-gradient(120% 80% at 50% -10%, #17172a 0%, #0b0b10 55%);
    color: #f2f2f5; font-family: 'Inter', system-ui, sans-serif;
    display: grid; grid-template-columns: 32% 1fr; grid-template-rows: 1fr auto;
    grid-template-areas: 'head stage' 'foot stage';
  }
  header { grid-area: head; padding: clamp(1.5rem, 3.5vw, 3.5rem); align-self: center; max-width: 42ch; }
  .eyebrow { font-size: .72rem; letter-spacing: .14em; text-transform: uppercase; color: #8a8aa0; margin: 0 0 1.3rem; }
  h1 { font-family: 'Anton', sans-serif; font-weight: 400; font-size: clamp(2.1rem, 3.6vw, 3.5rem);
       line-height: 1.0; margin: 0 0 1.2rem; text-transform: uppercase; }
  .hl { color: #ffd23e; }
  .dek { font-size: 1rem; line-height: 1.6; color: #c3c3d2; margin: 0; }
  .dek em { font-style: normal; color: #eaeaf2; font-weight: 600; }
  .own { color: #ff6b60; font-weight: 600; } .opp { color: #6ba6ff; font-weight: 600; }
  .stage { grid-area: stage; min-width: 0; position: relative; }
  svg { display: block; width: 100%; height: 100%; }
  .axis { stroke: #2a2a3a; stroke-width: 1; }
  .axlbl { fill: #7a7a90; font-size: 11px; letter-spacing: .02em; }
  .node { transition: opacity .25s; cursor: pointer; }
  .node.dim { opacity: .26; }
  .halo { fill: #000; opacity: .4; }
  .nm { fill: #fff; font-size: 12px; font-weight: 700; text-anchor: middle; paint-order: stroke; stroke: #0b0b10; stroke-width: 3.5px; }
  .pct { fill: #b7b7c8; font-size: 10px; text-anchor: middle; paint-order: stroke; stroke: #0b0b10; stroke-width: 3.5px; }
  .callout {
    position: absolute; transform: translate(-50%, -108%); width: 220px;
    background: rgba(14,14,22,.92); border: 1px solid #33334a; border-left: 3px solid #ffd23e;
    border-radius: 8px; padding: .6rem .7rem; font-size: .82rem; line-height: 1.45; color: #e8e8f0;
    box-shadow: 0 8px 30px rgba(0,0,0,.5); pointer-events: none;
  }
  .callout b { color: #ffd23e; }
  footer { grid-area: foot; padding: 1rem clamp(1.5rem,3.5vw,3.5rem) 1.75rem; font-size: .7rem; color: #77778c; max-width: 42ch; }

  @media (max-width: 820px) {
    main { grid-template-columns: 1fr; grid-template-rows: auto 1fr auto; grid-template-areas: 'head' 'stage' 'foot'; }
    header { padding: 1.4rem 1.25rem .4rem; max-width: none; }
    .stage { aspect-ratio: 1/1.25; height: auto; }
    .callout { width: 170px; font-size: .74rem; }
    footer { max-width: none; }
  }
</style>
