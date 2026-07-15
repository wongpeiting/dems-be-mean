// src/lib/quiz.test.js
import { describe, it, expect } from 'vitest';
import { scoreSentence, QuizState } from './quiz.svelte.js';

const rounds = [
	{ id: '1', answer: 'dem', tell: false },
	{ id: '2', answer: 'rep', tell: true }
];

describe('scoreSentence', () => {
	it('handles zero', () => expect(scoreSentence(0, 0)).toBe('Tap a side to start guessing.'));
	it('singular', () => expect(scoreSentence(1, 1)).toBe('You’ve guessed once and got it right.'));
	it('coin flip note', () =>
		expect(scoreSentence(6, 3)).toBe('You’ve guessed 6 times and got 3 right — a coin flip.'));
	it('above chance', () =>
		expect(scoreSentence(8, 7)).toBe('You’ve guessed 8 times and got 7 right — better than most.'));
});

describe('QuizState', () => {
	const mem = () => {
		const m = {};
		return { getItem: (k) => m[k] ?? null, setItem: (k, v) => (m[k] = v) };
	};
	it('records guesses and score', () => {
		const q = new QuizState(rounds, mem());
		const r = q.guess('dem');
		expect(r).toEqual({ correct: true, answer: 'dem' });
		expect(q.n).toBe(1); expect(q.correct).toBe(1);
		expect(q.current.id).toBe('2');
	});
	it('tell round blocks reveal until zone logged', () => {
		const q = new QuizState(rounds, mem());
		q.guess('dem');
		q.pick('rep'); // pick on a tell round stores choice, sets tellPending
		expect(q.tellPending).toBe(true);
		q.logTell('sound');
		expect(q.tellPending).toBe(false);
		expect(q.n).toBe(2);
	});
	it('persists across instances', () => {
		const s = mem();
		new QuizState(rounds, s).guess('rep');
		expect(new QuizState(rounds, s).n).toBe(1);
	});

	// Fix 1: guess() on a tell round must return null and not corrupt state
	it('guess() on a tell round returns null and leaves state unchanged', () => {
		const q = new QuizState(rounds, mem());
		q.guess('dem'); // advance to round 2 (tell round)
		expect(q.current.tell).toBe(true);
		const nBefore = q.n;
		const result = q.guess('rep');
		expect(result).toBe(null);
		expect(q.n).toBe(nBefore);
		expect(q.tellPending).toBe(false);
		// pick + logTell still work after the blocked guess
		q.pick('rep');
		expect(q.tellPending).toBe(true);
		const tell = q.logTell('sound');
		expect(tell).toMatchObject({ answer: 'rep', tellZone: 'sound' });
	});

	// Fix 2: #save() wrapped in try/catch — throwing storage must not crash
	it('throwing storage does not crash constructor or guess()', () => {
		const badStorage = {
			getItem: () => null,
			setItem: () => { throw new Error('QuotaExceededError'); }
		};
		expect(() => {
			const q = new QuizState(rounds, badStorage);
			q.guess('dem'); // triggers #save inside #commit
			expect(q.n).toBe(1); // state updated in memory
		}).not.toThrow();
	});

	// Fix 3: corrupted JSON in storage falls back to fresh state
	it('corrupted storage falls back to fresh state', () => {
		const corruptStorage = {
			getItem: () => '"{corrupt"',
			setItem: () => {}
		};
		const q = new QuizState(rounds, corruptStorage);
		expect(q.n).toBe(0);
		expect(q.current?.id).toBe('1'); // round index reset to 0
	});
});

// Fix 4: scoreSentence rate gap — above a coin flip variant
describe('scoreSentence rate gap', () => {
	it('returns above-a-coin-flip for rate between 0.6 and 0.75', () => {
		expect(scoreSentence(10, 7)).toBe('You’ve guessed 10 times and got 7 right — above a coin flip.');
	});
});
