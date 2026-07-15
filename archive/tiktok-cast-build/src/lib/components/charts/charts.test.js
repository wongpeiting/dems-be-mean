// src/lib/components/charts/charts.test.js
import { describe, it, expect } from 'vitest';
import { findCrossover } from '../../charts-utils.js';

const SAMPLE = [
	{ m: '2025-01', dem: 0.01, rep: null },
	{ m: '2025-02', dem: 0.02, rep: null },
	{ m: '2025-03', dem: 0.05, rep: 0.08 }, // rep > dem, no crossover yet
	{ m: '2025-04', dem: 0.09, rep: 0.06 }, // dem > rep — crossover
	{ m: '2025-05', dem: 0.03, rep: 0.07 }
];

describe('findCrossover', () => {
	it('finds the first month where dem > rep after the cutoff', () => {
		expect(findCrossover(SAMPLE, '2025-01')).toBe('2025-04');
	});

	it('returns null when dem never exceeds rep after the cutoff', () => {
		const noFlip = [
			{ m: '2025-02', dem: 0.01, rep: 0.05 },
			{ m: '2025-03', dem: 0.02, rep: 0.06 }
		];
		expect(findCrossover(noFlip, '2025-01')).toBe(null);
	});

	it('skips null values when looking for crossover', () => {
		const withNulls = [
			{ m: '2025-02', dem: 0.05, rep: null }, // null rep — skip
			{ m: '2025-03', dem: null, rep: 0.03 }, // null dem — skip
			{ m: '2025-04', dem: 0.07, rep: 0.04 } // first valid crossover
		];
		expect(findCrossover(withNulls, '2025-01')).toBe('2025-04');
	});

	it('returns null when series is entirely before the cutoff', () => {
		expect(findCrossover(SAMPLE, '2026-01')).toBe(null);
	});

	it('finds real crossover month 2025-08 from toplines data shape', () => {
		const real = [
			{ m: '2025-07', dem: 0.0797872340425532, rep: null },
			{ m: '2025-08', dem: 0.08955223880597014, rep: 0.08333333333333333 },
			{ m: '2025-09', dem: 0.025210084033613446, rep: 0.08181818181818182 }
		];
		expect(findCrossover(real, '2025-01')).toBe('2025-08');
	});

	it('handles an empty series gracefully', () => {
		expect(findCrossover([], '2025-01')).toBe(null);
	});
});
