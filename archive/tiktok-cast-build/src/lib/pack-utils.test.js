import { describe, it, expect } from 'vitest';
import { topShare, deterministicShuffle } from './pack-utils.js';

describe('topShare', () => {
  it('returns correct share for known inputs', () => {
    const people = [
      { totals: { posts: 100 } },
      { totals: { posts: 200 } },
      { totals: { posts: 300 } }
    ];
    expect(topShare(people, 1000)).toBe(0.6);
  });

  it('returns 0 when total is 0', () => {
    const people = [{ totals: { posts: 100 } }];
    expect(topShare(people, 0)).toBe(0);
  });

  it('clamps to 1 when sum exceeds total', () => {
    const people = [{ totals: { posts: 2000 } }];
    expect(topShare(people, 1000)).toBe(1);
  });

  it('handles empty people array', () => {
    expect(topShare([], 1000)).toBe(0);
  });
});

describe('deterministicShuffle', () => {
  const items = [
    { id: 'a' },
    { id: 'b' },
    { id: 'c' },
    { id: 'd' },
    { id: 'e' },
    { id: 'f' }
  ];

  it('same input + same seed produces same order', () => {
    const r1 = deterministicShuffle(items, 'test-seed');
    const r2 = deterministicShuffle(items, 'test-seed');
    expect(r1.map((x) => x.id)).toEqual(r2.map((x) => x.id));
  });

  it('same input + different seed produces different order', () => {
    const r1 = deterministicShuffle(items, 'seed-alpha');
    const r2 = deterministicShuffle(items, 'seed-beta');
    // The two shuffles must differ somewhere (probability of collision for 6 items is tiny)
    const same = r1.every((x, i) => x.id === r2[i].id);
    expect(same).toBe(false);
  });

  it('does not mutate the original array', () => {
    const original = items.map((x) => ({ ...x }));
    deterministicShuffle(items, 'mutation-test');
    expect(items.map((x) => x.id)).toEqual(original.map((x) => x.id));
  });

  it('returns a new array of the same length', () => {
    const result = deterministicShuffle(items, 'length-test');
    expect(result).not.toBe(items);
    expect(result.length).toBe(items.length);
  });

  it('contains the same elements as the original', () => {
    const result = deterministicShuffle(items, 'contents-test');
    expect(result.map((x) => x.id).sort()).toEqual(items.map((x) => x.id).sort());
  });
});
