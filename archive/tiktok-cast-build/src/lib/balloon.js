// src/lib/balloon.js

/**
 * SVG path for a balloon of radius r, inflated to `plump` (0..1).
 * The balloon body uses a cubic bezier approximating a circle, then narrows
 * to a knot at the bottom.
 */
export function balloonPath(r, plump) {
  const w = r * plump;          // horizontal radius
  const h = r * 1.3 * plump;    // vertical radius (taller than wide)
  const k = r * 0.25 * plump;   // bezier handle factor
  const knotY = r * 1.1 * plump;
  const knotW = r * 0.08;

  // Top arc (circle-ish) using 4-point cubic approximation
  // Start at bottom of balloon body, go counter-clockwise
  return [
    `M 0 ${-h + k}`,
    `C ${-k} ${-h}  ${-w} ${-k}  ${-w} 0`,
    `C ${-w} ${k}   ${-k} ${h}   0 ${h}`,
    `C ${k} ${h}    ${w} ${k}    ${w} 0`,
    `C ${w} ${-k}   ${k} ${-h}   0 ${-h + k}`,
    // Knot
    `L ${knotW} ${knotY - r * 0.05}`,
    `Q 0 ${knotY + r * 0.08} ${-knotW} ${knotY - r * 0.05}`,
    `Z`
  ].join(' ');
}

/**
 * Accumulate weekly posts up to (but not including) week Math.floor(t * n).
 * t=0 → 0 weeks, t=0.5 of 2 weeks → 1 week, t=1 → all weeks.
 */
export function inflationAt(weekly, t) {
  const n = weekly.length;
  const upTo = Math.floor(t * n);
  let own = 0, opp = 0;
  for (let i = 0; i < upTo; i++) {
    own += weekly[i].own;
    opp += weekly[i].opp;
  }
  return { own, opp, total: own + opp };
}
