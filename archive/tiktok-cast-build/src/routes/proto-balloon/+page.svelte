<script>
  import * as d3 from 'd3';
  import { base } from '$app/paths';
  import balloons from '$lib/data/balloons.json';

  const REP = '#e0483d', BLUE = '#4d8be0';
  let people = balloons.people;
  let W = $state(0), H = $state(0);
  let hovered = $state(null);

  // Lay the cast out by post count using pack for x positions, then draw each
  // as a proper balloon: tapered latex body, face clipped INTO it, sheen, knot,
  // string. ry > rx so it reads as an inflated balloon, not a circle.
  let items = $derived.by(() => {
    if (W <= 0 || H <= 0) return [];
    const root = d3.hierarchy({ children: people })
      .sum((d) => d.totals?.posts ?? 0).sort((a, b) => b.value - a.value);
    d3.pack().size([W, H * 0.82]).padding(10)(root);
    return root.leaves().map((n) => ({ d: n.data, x: n.x, y: n.y + 6, rx: n.r * 0.92 }));
  });

  // balloon body path — rounded top, tapered to a knot at the bottom
  function balloonPath(rx, ry) {
    return `M0,${-ry}
      C${rx*1.15},${-ry} ${rx*1.2},${ry*0.32} ${rx*0.30},${ry*0.92}
      C${rx*0.13},${ry*1.02} ${-rx*0.13},${ry*1.02} ${-rx*0.30},${ry*0.92}
      C${-rx*1.2},${ry*0.32} ${-rx*1.15},${-ry} 0,${-ry} Z`;
  }
</script>

<main>
  <header>
    <p class="eyebrow">The cast · both parties' official TikTok, Nov 2024–now</p>
    <h1>Twelve people,<br />pumped full of <span class="hl">air</span>.</h1>
    <p class="dek">
      Each balloon is one politician, inflated by every video that stars them. Redder latex is
      <span class="own">air from their own side</span>; bluer is
      <span class="opp">their opponents blowing them up to knock them down</span>. Trump is swollen
      biggest — and he’s mostly full of enemy breath.
    </p>
  </header>

  <section class="stage" bind:clientWidth={W} bind:clientHeight={H}>
    {#if W > 0}
      <svg viewBox="0 0 {W} {H}" role="presentation">
        <defs>
          {#each items as it (it.d.slug)}
            {@const ry = it.rx * 1.28}
            <clipPath id="b-{it.d.slug}"><path d={balloonPath(it.rx, ry)} transform="translate({it.x},{it.y})" /></clipPath>
            <radialGradient id="sheen-{it.d.slug}" cx="0.34" cy="0.26" r="0.75">
              <stop offset="0%" stop-color="#fff" stop-opacity="0.55" />
              <stop offset="34%" stop-color="#fff" stop-opacity="0.10" />
              <stop offset="100%" stop-color="#000" stop-opacity="0.30" />
            </radialGradient>
          {/each}
        </defs>

        {#each items as it (it.d.slug)}
          {@const ry = it.rx * 1.28}
          {@const tint = it.d.totals.oppShare > 0.5 ? BLUE : REP}
          {@const knotY = it.y + ry}
          <g class="node" class:dim={hovered && hovered !== it.d.slug}
             onpointerenter={() => hovered = it.d.slug} onpointerleave={() => hovered = null} role="presentation">
            <!-- string -->
            <path d="M{it.x},{knotY} q {it.rx*0.5},{ry*0.5} {-it.rx*0.15},{ry*1.1}" fill="none" stroke="#8890a8" stroke-width="1.2" opacity="0.7" />
            <!-- knot -->
            <path d="M{it.x-3.5},{knotY} L{it.x+3.5},{knotY} L{it.x},{knotY+7} Z" fill={tint} />
            <!-- latex base tint -->
            <path d={balloonPath(it.rx, ry)} transform="translate({it.x},{it.y})" fill={tint} opacity="0.9" />
            <!-- face printed on / clipped into the latex, stretched to fill the taller body -->
            <image href="{base}/{it.d.face}" clip-path="url(#b-{it.d.slug})"
                   x={it.x - it.rx} y={it.y - ry} width={it.rx*2} height={ry*2}
                   preserveAspectRatio="none" opacity="0.92" />
            <!-- glossy sheen over everything -->
            <path d={balloonPath(it.rx, ry)} transform="translate({it.x},{it.y})" fill="url(#sheen-{it.d.slug})" />
            <path d={balloonPath(it.rx, ry)} transform="translate({it.x},{it.y})" fill="none" stroke={tint} stroke-width="1.5" opacity="0.8" />
            {#if it.rx > 30}
              <text class="nm" x={it.x} y={knotY + 22}>{it.d.name}</text>
              <text class="pct" x={it.x} y={knotY + 37}>{Math.round(it.d.totals.oppShare*100)}% enemy air</text>
            {/if}
          </g>
        {/each}
      </svg>
    {/if}
  </section>

  <footer>Balloon size = videos the person stars in · Colour = who’s inflating them · Data: stage-2 classification (partial)</footer>
</main>

<style>
  @import url('https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;500;700&display=swap');
  :global(body) { margin: 0; background: #0b0b10; }
  main {
    min-height: 100vh; background: radial-gradient(120% 80% at 50% -10%, #17172a 0%, #0b0b10 55%);
    color: #f2f2f5; font-family: 'Inter', system-ui, sans-serif;
    display: grid; grid-template-columns: 34% 1fr; grid-template-rows: 1fr auto;
    grid-template-areas: 'head stage' 'foot stage';
  }
  header { grid-area: head; padding: clamp(1.5rem, 4vw, 4rem); align-self: center; max-width: 40ch; }
  .eyebrow { font-size: .72rem; letter-spacing: .14em; text-transform: uppercase; color: #8a8aa0; margin: 0 0 1.4rem; }
  h1 { font-family: 'Anton', sans-serif; font-weight: 400; font-size: clamp(2.2rem, 4.2vw, 4rem);
       line-height: .98; margin: 0 0 1.3rem; text-transform: uppercase; }
  .hl { color: #ffd23e; }
  .dek { font-size: 1.02rem; line-height: 1.6; color: #c3c3d2; margin: 0; }
  .own { color: #ff6b60; font-weight: 600; } .opp { color: #6ba6ff; font-weight: 600; }
  .stage { grid-area: stage; min-width: 0; position: relative; }
  svg { display: block; width: 100%; height: 100%; }
  .node { transition: opacity .25s; cursor: pointer; }
  .node.dim { opacity: .26; }
  .nm { fill: #fff; font-size: 12px; font-weight: 700; text-anchor: middle; paint-order: stroke; stroke: #0b0b10; stroke-width: 3px; }
  .pct { fill: #b7b7c8; font-size: 10px; text-anchor: middle; paint-order: stroke; stroke: #0b0b10; stroke-width: 3px; }
  footer { grid-area: foot; padding: 1rem clamp(1.5rem, 4vw, 4rem) 2rem; font-size: .7rem; color: #77778c; max-width: 40ch; }

  @media (max-width: 820px) {
    main { grid-template-columns: 1fr; grid-template-rows: auto 1fr auto; grid-template-areas: 'head' 'stage' 'foot'; }
    header { padding: 1.5rem 1.25rem .5rem; max-width: none; }
    .stage { aspect-ratio: 1/1.15; height: auto; }
    footer { max-width: none; }
  }
</style>
