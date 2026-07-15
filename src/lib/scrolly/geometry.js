import { scaleSqrt } from 'd3-scale';
import { line, curveCatmullRom } from 'd3-shape';

/**
 * @typedef {[number, number]} Point
 * @typedef {object} Flow
 * @property {string} id
 * @property {number} value           share/magnitude → drives ribbon width
 * @property {Point[]} schematic      hand-placed x/y in viewBox space (t=0)
 * @property {Point[]} geo            [lng,lat] route (t=1), projected at render
 * @property {boolean} [geoIsProjected]  if true, geo is already [x,y]
 * @property {string} [label]
 * @property {'left'|'right'} [side]
 */

/**
 * Width scale for ribbons. Uses sqrt so a doubled value doesn't quadruple the
 * visual mass — thickness reads roughly proportional to the number. Clamped.
 * @param {{domain:[number,number], range:[number,number]}} opts
 */
export function makeWidthScale({ domain, range }) {
	return scaleSqrt().domain(domain).range(range).clamp(true);
}

const smooth = line().curve(curveCatmullRom.alpha(0.5));

/**
 * SVG path `d` for a ribbon centerline (smoothed). Stroke it with a wide,
 * round-capped stroke to get the "thick pipe" look. Empty/1-point → ''.
 * UPGRADE PATH: for within-segment tapering (a flow that thins as it splits),
 * replace this with filled centerline-offset polygons (±width/2 along normals).
 * @param {Point[]} points
 */
export function ribbonPath(points, { curve = smooth } = {}) {
	if (!points || points.length < 2) return '';
	return curve(points) ?? '';
}

/** Euclidean distance. @param {Point} a @param {Point} b */
function dist(a, b) {
	return Math.hypot(b[0] - a[0], b[1] - a[1]);
}

/**
 * Resample a polyline to exactly `n` points spaced evenly by arc length, so
 * index i is the same fractional distance along the path. Endpoints preserved.
 * This equal-arc-length correspondence is what stops the morph from "swimming".
 * @param {Point[]} points
 * @param {number} n
 * @returns {Point[]}
 */
export function resample(points, n) {
	if (!points || points.length === 0) return [];
	if (points.length === 1) return Array.from({ length: n }, () => [...points[0]]);
	// cumulative arc length at each vertex
	const cum = [0];
	for (let i = 1; i < points.length; i++) cum.push(cum[i - 1] + dist(points[i - 1], points[i]));
	const total = cum[cum.length - 1];
	if (total === 0) return Array.from({ length: n }, () => [...points[0]]);

	const out = [];
	for (let k = 0; k < n; k++) {
		const target = (k / (n - 1)) * total;
		// find segment containing `target`
		let i = 1;
		while (i < cum.length - 1 && cum[i] < target) i++;
		const segLen = cum[i] - cum[i - 1] || 1;
		const f = (target - cum[i - 1]) / segLen;
		const a = points[i - 1];
		const b = points[i];
		out.push([a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f]);
	}
	// pin exact endpoints against float drift
	out[0] = [...points[0]];
	out[n - 1] = [...points[points.length - 1]];
	return out;
}

/**
 * Per-point linear interpolation between two equal-length point arrays.
 * @param {Point[]} a @param {Point[]} b @param {number} t
 * @returns {Point[]}
 */
export function lerpPoints(a, b, t) {
	if (a.length !== b.length) throw new Error('lerpPoints: arrays must be equal length');
	return a.map((p, i) => [p[0] + (b[i][0] - p[0]) * t, p[1] + (b[i][1] - p[1]) * t]);
}

/**
 * Full morph for one flow: project the geo route, resample both layouts to a
 * common point count, then lerp by t (0 = schematic, 1 = geography).
 * @param {Flow} flow
 * @param {(lngLat:Point)=>Point} project
 * @param {number} t
 * @param {number} [n=64]
 * @returns {Point[]}
 */
export function interpolateFlow(flow, project, t, n = 64) {
	const geoXY = flow.geoIsProjected ? flow.geo : flow.geo.map((c) => project(c));
	const a = resample(flow.schematic, n);
	const b = resample(geoXY, n);
	return lerpPoints(a, b, t);
}
