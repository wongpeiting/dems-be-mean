import { describe, it, expect } from 'vitest';
import { buildProjection } from './projection.js';

// a small box of the world to fit
const box = {
	type: 'FeatureCollection',
	features: [
		{
			type: 'Feature',
			geometry: { type: 'Polygon', coordinates: [[[-10, -10], [10, -10], [10, 10], [-10, 10], [-10, -10]]] }
		}
	]
};

describe('buildProjection', () => {
	it('projects fitted geometry inside [0,w] x [0,h]', () => {
		const { project } = buildProjection(box, [200, 200]);
		const [x, y] = project([0, 0]); // center of the box → near center of the frame
		expect(x).toBeGreaterThanOrEqual(0);
		expect(x).toBeLessThanOrEqual(200);
		expect(y).toBeGreaterThanOrEqual(0);
		expect(y).toBeLessThanOrEqual(200);
	});
	it('is deterministic for the same inputs', () => {
		const a = buildProjection(box, [300, 150]).project([5, 5]);
		const b = buildProjection(box, [300, 150]).project([5, 5]);
		expect(a).toEqual(b);
	});
	it('path() returns an SVG path string for a feature', () => {
		const { path } = buildProjection(box, [200, 200]);
		const d = path(box.features[0]);
		expect(d.startsWith('M')).toBe(true);
	});
});
