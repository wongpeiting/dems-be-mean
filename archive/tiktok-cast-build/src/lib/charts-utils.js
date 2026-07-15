/**
 * Pure chart helper utilities — importable without mounting Svelte.
 */

/**
 * findCrossover(series, afterMonth)
 * Finds the first month in `series` where dem > rep, strictly after the
 * given `afterMonth` cutoff (YYYY-MM string, exclusive).
 *
 * @param {Array<{m: string, dem: number|null, rep: number|null}>} series
 * @param {string} afterMonth  — YYYY-MM cutoff (exclusive)
 * @returns {string|null}  — YYYY-MM of crossover month, or null
 */
export function findCrossover(series, afterMonth) {
	for (const row of series) {
		if (row.m <= afterMonth) continue;
		if (row.dem == null || row.rep == null) continue;
		if (row.dem > row.rep) return row.m;
	}
	return null;
}
