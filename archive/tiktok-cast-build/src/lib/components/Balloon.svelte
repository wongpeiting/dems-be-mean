<script>
  import { balloonPath } from '$lib/balloon.js';
  import { base } from '$app/paths';
  import { nextUid } from '$lib/uid.js';
  import * as d3 from 'd3';

  let { person, r, plump = 1, labeled = false, oppShare = person.totals.oppShare } = $props();

  const uid = nextUid();

  const totalHeight = $derived(r * 1.9 + r * 1.1); // = r * 3.0
  const topOfBalloon = $derived(-r * 1.9);

  // $derived expressions return strings directly (NOT functions/arrow functions)
  const ownColor = $derived(
    person.totals.ownRegister !== null && person.totals.oppRegister !== null
      ? d3.interpolateRgb('#d5564c', '#aa1100')(Math.min(Math.abs(person.totals.ownRegister) / 3, 1))
      : '#d5564c'
  );
  const oppColor = $derived(
    person.totals.ownRegister !== null && person.totals.oppRegister !== null
      ? d3.interpolateRgb('#5588d5', '#1144cc')(Math.min(Math.abs(person.totals.oppRegister) / 3, 1))
      : '#5588d5'
  );
</script>

<div style="position:relative; width:{r*2.4}px; height:{r*3.2}px; display:inline-block">
  <svg
    width={r * 2.4}
    height={r * 3.2}
    viewBox="{-r * 1.2} {-r * 1.9} {r * 2.4} {r * 3.2}"
  >
    <defs>
      <clipPath id="clip-{person.slug}-{uid}">
        <path d={balloonPath(r, plump)} />
      </clipPath>
    </defs>

    <!-- Filled balloon body, clipped -->
    <g clip-path="url(#clip-{person.slug}-{uid})">
      <!-- opp (blue) on top -->
      <rect
        x={-r}
        y={topOfBalloon}
        width={r * 2}
        height={totalHeight * oppShare}
        fill={oppColor}
      />
      <!-- own (red) below -->
      <rect
        x={-r}
        y={topOfBalloon + totalHeight * oppShare}
        width={r * 2}
        height={totalHeight * (1 - oppShare)}
        fill={ownColor}
      />
    </g>

    <!-- Balloon outline -->
    <path d={balloonPath(r, plump)} fill="none" stroke="#222" stroke-width="1.5" />

    <!-- Highlight ellipse (latex sheen) -->
    <ellipse
      cx={-r * 0.3}
      cy={-r * 1.3}
      rx={r * 0.18}
      ry={r * 0.28}
      fill="white"
      opacity="0.25"
    />

    <!-- String -->
    <path
      d="M 0 {r * 1.1 * plump} Q {r * 0.15} {r * 1.6 * plump} 0 {r * 2.0 * plump}"
      stroke="#555"
      fill="none"
      stroke-width="1"
    />
  </svg>

  <!-- Face overlay -->
  <img
    src="{base}/{person.face}"
    alt={person.name}
    onerror={(e) => e.currentTarget.style.display = 'none'}
    style="position:absolute; left:50%; top:50%; transform:translate(-50%,-55%) scale({0.5 + plump * 0.55},{0.35 + plump * 0.85}); will-change:transform; pointer-events:none; width:{r * 1.4}px; height:{r * 1.4}px; object-fit:contain;"
  />

  {#if labeled}
    <svg
      style="position:absolute; left:0; top:0; pointer-events:none; overflow:visible;"
      width={r * 2.4}
      height={r * 3.2}
      viewBox="{-r * 1.2} {-r * 1.9} {r * 2.4} {r * 3.2}"
    >
      <text
        x="0"
        y={r * 2.4}
        text-anchor="middle"
        font-size="11"
        fill="#222"
      >{person.name}</text>
      <text
        x="0"
        y={r * 2.4 + 14}
        text-anchor="middle"
        font-size="11"
        fill="#222"
      >{Math.round(oppShare * 100)}% opponent air</text>
    </svg>
  {/if}
</div>
