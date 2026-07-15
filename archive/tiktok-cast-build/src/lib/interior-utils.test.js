import { describe, it, expect } from 'vitest';
import { nearestNode, emotionCentroids, cullVisible } from './interior-utils.js';

describe('nearestNode', () => {
  const nodes = [
    { id: 'a', x: 0.1, y: 0.1 },
    { id: 'b', x: 0.5, y: 0.5 },
    { id: 'c', x: 0.9, y: 0.9 }
  ];

  it('finds the nearest node within radius', () => {
    const result = nearestNode(nodes, 0.12, 0.12, 0.1);
    expect(result).not.toBeNull();
    expect(result.id).toBe('a');
  });

  it('finds nearest even when multiple are in range', () => {
    const result = nearestNode(nodes, 0.48, 0.48, 0.1);
    expect(result).not.toBeNull();
    expect(result.id).toBe('b');
  });

  it('returns null when all nodes are outside maxDist', () => {
    // query point (0.3, 0.3): distance to 'a'=(0.1,0.1) is ~0.283, to 'b'=(0.5,0.5) is ~0.283
    // maxDist = 0.05 → none within range
    const result = nearestNode(nodes, 0.3, 0.3, 0.05);
    expect(result).toBeNull();
  });

  it('returns null for empty nodes array', () => {
    const result = nearestNode([], 0.5, 0.5, 1.0);
    expect(result).toBeNull();
  });

  describe('anisotropic (pixel-space) hit tests', () => {
    const W = 800;
    const H = 400;
    const kW = 1 * W; // 800
    const kH = 1 * H; // 400
    const node = { id: 'center', x: 0.5, y: 0.5 };

    it('finds node offset only in x on a wide canvas', () => {
      // 20px offset in x: dx = 20/800 * 800 = 20px; dy = 0 → d = 20 < 24
      const result = nearestNode([node], 0.5 + 20 / W, 0.5, 24, kW, kH);
      expect(result).not.toBeNull();
      expect(result.id).toBe('center');
    });

    it('misses node offset only in x beyond maxDistPx on a wide canvas', () => {
      // 30px offset in x: dx = 30/800 * 800 = 30px; dy = 0 → d = 30 > 24
      const result = nearestNode([node], 0.5 + 30 / W, 0.5, 24, kW, kH);
      expect(result).toBeNull();
    });
  });
});

describe('emotionCentroids', () => {
  it('computes correct centroid for two emotion clusters', () => {
    const nodes = [
      { emotion: 'Anger', x: 0.1, y: 0.2 },
      { emotion: 'Anger', x: 0.3, y: 0.4 },
      { emotion: 'Joy', x: 0.7, y: 0.8 },
      { emotion: 'Joy', x: 0.9, y: 0.6 }
    ];
    const centroids = emotionCentroids(nodes);

    expect(centroids instanceof Map).toBe(true);
    expect(centroids.has('Anger')).toBe(true);
    expect(centroids.has('Joy')).toBe(true);

    const anger = centroids.get('Anger');
    expect(anger.x).toBeCloseTo(0.2, 5);
    expect(anger.y).toBeCloseTo(0.3, 5);

    const joy = centroids.get('Joy');
    expect(joy.x).toBeCloseTo(0.8, 5);
    expect(joy.y).toBeCloseTo(0.7, 5);
  });

  it('handles a single node per group', () => {
    const nodes = [{ emotion: 'Fear', x: 0.42, y: 0.58 }];
    const centroids = emotionCentroids(nodes);
    const fear = centroids.get('Fear');
    expect(fear.x).toBeCloseTo(0.42, 5);
    expect(fear.y).toBeCloseTo(0.58, 5);
  });
});

describe('cullVisible', () => {
  // identity transform: applyX(v) = v * 1 + 0, applyY(v) = v * 1 + 0
  const identity = {
    k: 1,
    x: 0,
    y: 0,
    applyX: (v) => v,
    applyY: (v) => v
  };

  const W = 400;
  const H = 300;
  const margin = 50;

  const nodes = [
    { id: 'center', x: 0.5, y: 0.5 },   // screen: 200, 150 — inside
    { id: 'edge', x: 0.0, y: 0.0 },      // screen: 0, 0 — at border, inside margin
    { id: 'far-right', x: 1.5, y: 0.5 }, // screen: 600, 150 — outside W+margin=450
    { id: 'far-below', x: 0.5, y: 1.5 }  // screen: 200, 450 — outside H+margin=350
  ];

  it('passes nodes near center at identity transform', () => {
    const visible = cullVisible(nodes, identity, W, H, margin);
    const ids = visible.map((n) => n.id);
    expect(ids).toContain('center');
    expect(ids).toContain('edge');
  });

  it('excludes nodes far outside the viewport', () => {
    const visible = cullVisible(nodes, identity, W, H, margin);
    const ids = visible.map((n) => n.id);
    expect(ids).not.toContain('far-right');
    expect(ids).not.toContain('far-below');
  });

  it('respects zoom transform (panned + scaled)', () => {
    // zoom in 2x centered around top-left: everything shifts right/down
    const panned = {
      k: 2,
      x: 100,
      y: 100,
      applyX: (v) => v * 2 + 100,
      applyY: (v) => v * 2 + 100
    };
    // center node at data (0.5, 0.5) → screen (2*200+100, 2*150+100) = (500, 400)
    // W=400, H=300, margin=50 → visible range x:[-50,450], y:[-50,350]
    // 500 > 450 → outside x; 400 > 350 → outside y → excluded
    const visible = cullVisible([nodes[0]], panned, W, H, margin);
    expect(visible.length).toBe(0);
  });
});
