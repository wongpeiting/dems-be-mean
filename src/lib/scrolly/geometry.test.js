import { describe, it, expect } from 'vitest';
import { makeWidthScale, ribbonPath, resample, lerpPoints, interpolateFlow } from './geometry.js';

describe('makeWidthScale', () => {
	it('maps domain to range via sqrt (thickness ∝ sqrt(value))', () => {
		const s = makeWidthScale({ domain: [0, 100], range: [0, 40] });
		expect(s(0)).toBeCloseTo(0);
		expect(s(100)).toBeCloseTo(40);
		// sqrt: value 25 → sqrt(25)/sqrt(100) = 0.5 → 20px
		expect(s(25)).toBeCloseTo(20);
	});
	it('clamps out-of-domain values', () => {
		const s = makeWidthScale({ domain: [0, 100], range: [2, 40] });
		expect(s(-50)).toBeCloseTo(2);
		expect(s(9999)).toBeCloseTo(40);
	});
});

describe('ribbonPath', () => {
	it('returns an SVG path string starting with M', () => {
		const d = ribbonPath([[0, 0], [10, 0], [10, 10]]);
		expect(d.startsWith('M')).toBe(true);
		expect(d.length).toBeGreaterThan(3);
	});
	it('handles empty and single-point input without throwing', () => {
		expect(ribbonPath([])).toBe('');
		expect(ribbonPath([[5, 5]])).toBe('');
	});
});

describe('resample', () => {
	it('returns exactly n points', () => {
		const out = resample([[0, 0], [10, 0]], 5);
		expect(out.length).toBe(5);
	});
	it('preserves endpoints', () => {
		const out = resample([[0, 0], [4, 0], [10, 0]], 7);
		expect(out[0]).toEqual([0, 0]);
		expect(out[out.length - 1]).toEqual([10, 0]);
	});
	it('spaces points evenly by arc length on a straight line', () => {
		const out = resample([[0, 0], [10, 0]], 3);
		expect(out[1][0]).toBeCloseTo(5); // midpoint at half the arc length
	});
});

describe('lerpPoints', () => {
	const a = [[0, 0], [10, 10]];
	const b = [[100, 0], [110, 10]];
	it('t=0 returns a, t=1 returns b', () => {
		expect(lerpPoints(a, b, 0)).toEqual(a);
		expect(lerpPoints(a, b, 1)).toEqual(b);
	});
	it('t=0.5 returns per-point midpoints', () => {
		expect(lerpPoints(a, b, 0.5)).toEqual([[50, 0], [60, 10]]);
	});
	it('throws on unequal length', () => {
		expect(() => lerpPoints([[0, 0]], b, 0.5)).toThrow();
	});
});

describe('interpolateFlow', () => {
	const project = ([lng, lat]) => [lng * 2, lat * 2]; // fake projection
	const flow = {
		schematic: [[0, 0], [0, 100]],
		geo: [[50, 0], [50, 100]] // projects to [100,0]..[100,200]
	};
	it('t=0 matches the schematic layout', () => {
		const out = interpolateFlow(flow, project, 0, 8);
		expect(out[0][0]).toBeCloseTo(0);
		expect(out[out.length - 1][0]).toBeCloseTo(0);
	});
	it('t=1 matches the projected geo route', () => {
		const out = interpolateFlow(flow, project, 1, 8);
		expect(out[0][0]).toBeCloseTo(100);
		expect(out[out.length - 1][0]).toBeCloseTo(100);
	});
});
