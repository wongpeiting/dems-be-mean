/**
 * interior-utils.js — pure helpers for BalloonInterior canvas field
 */

/**
 * Find the nearest node (in normalized 0–1 data space) to the given (x, y).
 * @param {Array} nodes - array of nodes with .x and .y properties (0–1)
 * @param {number} x - normalized x (0–1)
 * @param {number} y - normalized y (0–1)
 * @param {number} maxDistPx - maximum pixel distance threshold
 * @param {number} kW - scale factor for x axis (transform.k * W), default 1
 * @param {number} kH - scale factor for y axis (transform.k * H), default 1
 * @returns {object|null} nearest node within maxDistPx, or null
 */
export function nearestNode(nodes, x, y, maxDistPx, kW = 1, kH = 1) {
  let best = null;
  let bestDist = maxDistPx;
  for (const n of nodes) {
    const dx = (n.x - x) * kW;
    const dy = (n.y - y) * kH;
    const d = Math.sqrt(dx * dx + dy * dy);
    if (d < bestDist) {
      bestDist = d;
      best = n;
    }
  }
  return best;
}

/**
 * Compute centroids for each emotion group.
 * @param {Array} nodes - array of nodes with .emotion, .x, .y
 * @returns {Map<string, {x: number, y: number}>} map from emotion to centroid
 */
export function emotionCentroids(nodes) {
  const groups = new Map();
  for (const n of nodes) {
    if (!groups.has(n.emotion)) {
      groups.set(n.emotion, { sumX: 0, sumY: 0, count: 0 });
    }
    const g = groups.get(n.emotion);
    g.sumX += n.x;
    g.sumY += n.y;
    g.count += 1;
  }
  const result = new Map();
  for (const [emotion, g] of groups) {
    result.set(emotion, { x: g.sumX / g.count, y: g.sumY / g.count });
  }
  return result;
}

/**
 * Cull nodes to only those visible in the current viewport (with margin).
 * @param {Array} nodes - array of nodes with .x, .y (0–1 normalized)
 * @param {object} transform - d3 zoom transform with .k, .x, .y and .applyX/.applyY methods
 * @param {number} w - canvas logical width
 * @param {number} h - canvas logical height
 * @param {number} margin - extra pixel buffer outside the viewport
 * @returns {Array} filtered nodes
 */
export function cullVisible(nodes, transform, w, h, margin) {
  return nodes.filter((n) => {
    const sx = transform.applyX(n.x * w);
    const sy = transform.applyY(n.y * h);
    return sx >= -margin && sx <= w + margin && sy >= -margin && sy <= h + margin;
  });
}
