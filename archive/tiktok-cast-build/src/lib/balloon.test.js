// src/lib/balloon.test.js
import { describe, it, expect } from 'vitest';
import { balloonPath, inflationAt } from './balloon.js';

describe('balloonPath', () => {
  it('returns a string starting with M', () => {
    expect(balloonPath(50, 1)).toMatch(/^M/);
  });
  it('uses plump to vary path', () => {
    expect(balloonPath(50, 0.5)).not.toBe(balloonPath(50, 1));
  });
});

describe('inflationAt', () => {
  const weekly = [
    { own: 2, opp: 3 },
    { own: 1, opp: 4 },
  ];
  it('returns zero at t=0', () => {
    const r = inflationAt(weekly, 0);
    expect(r.total).toBe(0);
    expect(r.own).toBe(0);
    expect(r.opp).toBe(0);
  });
  it('returns first week at t=0.5', () => {
    const r = inflationAt(weekly, 0.5);
    expect(r.own).toBe(2);
    expect(r.opp).toBe(3);
    expect(r.total).toBe(5);
  });
  it('returns all weeks at t=1', () => {
    const r = inflationAt(weekly, 1);
    expect(r.own).toBe(3);
    expect(r.opp).toBe(7);
    expect(r.total).toBe(10);
  });
});
