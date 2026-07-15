// src/lib/crowd.test.js
import { describe, it, expect, vi, afterEach } from 'vitest';
import { fetchStats, postGuess } from './crowd.js';

const realFetch = global.fetch;

describe('crowd client', () => {
	afterEach(() => {
		global.fetch = realFetch;
		vi.unstubAllGlobals?.();
	});
	it('falls back to seeded stats when no URL configured', async () => {
		const seeded = { '111': { dem: 60, rep: 40 } };
		expect(await fetchStats(['111'], seeded, '')).toEqual(seeded);
	});
	it('postGuess is a no-op without URL', () => {
		global.fetch = vi.fn();
		postGuess({ roundId: '1', choice: 'dem' }, '');
		expect(global.fetch).not.toHaveBeenCalled();
	});
	it('falls back on fetch failure', async () => {
		global.fetch = vi.fn().mockRejectedValue(new Error('down'));
		const seeded = { '111': { dem: 1, rep: 1 } };
		expect(await fetchStats(['111'], seeded, 'https://x.example')).toEqual(seeded);
	});
});
