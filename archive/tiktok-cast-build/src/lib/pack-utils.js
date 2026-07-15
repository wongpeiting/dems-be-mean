/**
 * Pure helper utilities for pack visualisation.
 * No Svelte, no d3, SSR-safe.
 */

/**
 * Computes the share of total posts represented by the given people array.
 * @param {Array<{totals: {posts: number}}>} people
 * @param {number} total
 * @returns {number} clamped 0–1
 */
export function topShare(people, total) {
  if (!total || total <= 0) return 0;
  const sum = people.reduce((acc, p) => acc + (p.totals?.posts ?? 0), 0);
  return Math.min(1, Math.max(0, sum / total));
}

/**
 * Returns a deterministic, stable shuffle of arr using seedStr.
 * Same input + seed → same order. Does not mutate the original array.
 * Uses a simple string hash as a seed for a seeded Fisher-Yates shuffle.
 * @template T
 * @param {T[]} arr
 * @param {string} seedStr
 * @returns {T[]}
 */
export function deterministicShuffle(arr, seedStr) {
  // String hash → seed integer
  let seed = 0;
  for (let i = 0; i < seedStr.length; i++) {
    seed = (Math.imul(31, seed) + seedStr.charCodeAt(i)) | 0;
  }
  // Make positive
  seed = seed >>> 0;

  // Simple LCG random number generator seeded from above
  function lcg() {
    // LCG parameters from Numerical Recipes
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    return seed / 0x100000000;
  }

  const result = arr.slice();
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(lcg() * (i + 1));
    const tmp = result[i];
    result[i] = result[j];
    result[j] = tmp;
  }
  return result;
}
