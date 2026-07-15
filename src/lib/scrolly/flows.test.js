import { describe, it, expect } from 'vitest';
import { buildFlows } from './flows.js';

// tiny basemap: two named square "states" + a hub square
const basemap = {
	type: 'FeatureCollection',
	features: [
		{ type: 'Feature', properties: { NAME: 'Iowa' }, geometry: { type: 'Polygon', coordinates: [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]] } },
		{ type: 'Feature', properties: { NAME: 'Ohio' }, geometry: { type: 'Polygon', coordinates: [[[4, 0], [6, 0], [6, 2], [4, 2], [4, 0]]] } },
		{ type: 'Feature', properties: { NAME: 'Texas' }, geometry: { type: 'Polygon', coordinates: [[[0, -6], [4, -6], [4, -4], [0, -4], [0, -6]]] } }
	]
};

const config = {
	unit: 'tonnes',
	hub: { label: 'Gulf', region: 'Texas' },
	flows: [
		{ label: 'Iowa', region: 'Iowa', value: 60 },
		{ label: 'Ohio', region: 'Ohio', value: 40 }
	]
};

describe('buildFlows', () => {
	it('produces one flow per input plus a trunk, with resolved geo + normalized schematic', () => {
		const out = buildFlows(config, basemap);
		const tribs = out.flows.filter((f) => f.kind === 'tributary');
		const trunks = out.flows.filter((f) => f.kind === 'trunk');
		expect(tribs.length).toBe(2);
		expect(trunks.length).toBe(1);
		// each flow carries geo lng/lat pairs and normalized schematic in [0,1]
		for (const f of out.flows) {
			expect(f.geo.length).toBeGreaterThanOrEqual(2);
			expect(f.schematic.every(([x, y]) => x >= 0 && x <= 1 && y >= 0 && y <= 1)).toBe(true);
		}
	});
	it("trunk value equals the sum of tributary values", () => {
		const out = buildFlows(config, basemap);
		const trunk = out.flows.find((f) => f.kind === 'trunk');
		expect(trunk.value).toBe(100);
		expect(out.widthDomain).toEqual([0, 100]);
	});
	it('accepts explicit [lng,lat] via `at`', () => {
		const out = buildFlows(
			{ hub: { label: 'H', at: [10, 10] }, flows: [{ label: 'A', at: [0, 0], value: 5 }] },
			basemap
		);
		expect(out.flows.find((f) => f.kind === 'tributary').geo[0]).toEqual([0, 0]);
	});
	it('throws a clear error naming the row when a region is not found', () => {
		const bad = { hub: { label: 'Gulf', region: 'Texas' }, flows: [{ label: 'Iowaa', region: 'Iowaa', value: 5 }] };
		expect(() => buildFlows(bad, basemap)).toThrow(/Iowaa/);
	});
	it('suggests the closest region name on a typo', () => {
		const bad = { hub: { label: 'Gulf', region: 'Texas' }, flows: [{ label: 'x', region: 'Iowaa', value: 5 }] };
		expect(() => buildFlows(bad, basemap)).toThrow(/Iowa/);
	});
	it('throws when value is missing or not positive', () => {
		const bad = { hub: { label: 'Gulf', region: 'Texas' }, flows: [{ label: 'Iowa', region: 'Iowa', value: -3 }] };
		expect(() => buildFlows(bad, basemap)).toThrow(/value/);
	});
	it('throws when a flow has neither region nor at', () => {
		const bad = { hub: { label: 'Gulf', region: 'Texas' }, flows: [{ label: 'Nowhere', value: 5 }] };
		expect(() => buildFlows(bad, basemap)).toThrow(/region.*at|location/i);
	});
});
