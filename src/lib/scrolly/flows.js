import { geoCentroid } from 'd3-geo';

/**
 * TRANSLATABLE DATA CONTRACT — the friendly input a non-coder writes.
 *
 * @typedef {object} StoryConfig
 * @property {string} [basemap]  informational label for which map you're using
 * @property {string} [unit]     what `value` counts (e.g. "million tonnes") — shown in labels
 * @property {LocationSpec} hub  the single destination every flow converges into
 * @property {FlowSpec[]} flows  the sources
 *
 * @typedef {object} FlowSpec
 * @property {string} label      the name shown on the ribbon (required)
 * @property {number} value      a POSITIVE number — the only thing that sets width (required)
 * @property {string} [region]   a place name that must match the basemap; the kit finds its center
 * @property {[number,number]} [at]  OR explicit [lng, lat] if you already have coordinates
 * @property {string} [date]     optional "YYYY" or "YYYY-MM" for time-ordered stories
 *
 * @typedef {{label?:string, region?:string, at?:[number,number]}} LocationSpec
 */

const isNum = (v) => typeof v === 'number' && Number.isFinite(v);

/** case-insensitive lookup of a basemap feature by NAME/name property */
function featureByName(basemap, name) {
	const key = String(name).trim().toLowerCase();
	return basemap.features.find((f) => {
		const n = f.properties?.NAME ?? f.properties?.name ?? f.properties?.Name;
		return n && String(n).toLowerCase() === key;
	});
}

/** cheap "did you mean" — substring match, else first few available names */
function suggest(basemap, name) {
	const q = String(name).trim().toLowerCase();
	const names = basemap.features
		.map((f) => f.properties?.NAME ?? f.properties?.name ?? f.properties?.Name)
		.filter(Boolean);
	const near = names.find((n) => n.toLowerCase().includes(q) || q.includes(n.toLowerCase()));
	if (near) return `Did you mean '${near}'?`;
	return `Available names include: ${names.slice(0, 6).join(', ')}${names.length > 6 ? '…' : ''}`;
}

/** resolve one location spec → [lng, lat], with a clear error if it can't. */
function resolvePoint(spec, basemap, where) {
	if (Array.isArray(spec?.at) && spec.at.length === 2 && spec.at.every(isNum)) return spec.at;
	if (spec?.region) {
		const feat = featureByName(basemap, spec.region);
		if (!feat) throw new Error(`${where}: region '${spec.region}' not found in basemap. ${suggest(basemap, spec.region)}`);
		return geoCentroid(feat);
	}
	throw new Error(`${where}: needs a location — give it a "region" name or an "at": [lng, lat].`);
}

/** point a fraction f of the way from a to b (in lng/lat space) */
const lerp2 = (a, b, f) => [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f];

/**
 * Turn the friendly StoryConfig into technical flows the FlowMap can draw:
 * resolves geography, auto-routes each source→confluence→hub, auto-lays-out the
 * schematic bars, and adds the merged trunk. The author never writes coordinates.
 *
 * @param {StoryConfig} config
 * @param {object} basemap  the GeoJSON FeatureCollection being drawn
 * @returns {{flows:object[], hub:object, widthDomain:[number,number], unit:string|undefined}}
 */
export function buildFlows(config, basemap) {
	if (!config || !Array.isArray(config.flows) || config.flows.length === 0)
		throw new Error('buildFlows: config.flows must be a non-empty array.');
	if (!config.hub) throw new Error('buildFlows: config.hub (the destination) is required.');

	const hubPoint = resolvePoint(config.hub, basemap, `hub '${config.hub.label ?? ''}'`);

	// resolve + validate each source
	const sources = config.flows.map((spec, i) => {
		const where = `Flow '${spec.label ?? `#${i + 1}`}'`;
		if (!isNum(spec.value) || spec.value <= 0)
			throw new Error(`${where}: value must be a positive number, got ${JSON.stringify(spec.value)}.`);
		return { spec, where, point: resolvePoint(spec, basemap, where) };
	});

	// order for the schematic bar layout: by date if every flow has one, else by value desc
	const allDated = sources.every((s) => s.spec.date);
	const ordered = [...sources].sort((a, b) =>
		allDated ? String(a.spec.date).localeCompare(String(b.spec.date)) : b.spec.value - a.spec.value
	);

	// confluence: where tributaries meet before the trunk — 55% of the way from
	// the sources' average position toward the hub.
	const avg = sources
		.reduce((acc, s) => [acc[0] + s.point[0], acc[1] + s.point[1]], [0, 0])
		.map((v) => v / sources.length);
	const confluence = lerp2(avg, hubPoint, 0.55);

	const total = sources.reduce((sum, s) => sum + s.spec.value, 0);
	const n = ordered.length;

	// schematic x positions evenly spread across the middle band (normalized 0..1)
	const xAt = (k) => (n === 1 ? 0.5 : 0.18 + (0.64 * k) / (n - 1));

	const tributaries = ordered.map((s, k) => ({
		id: s.spec.label ?? `flow-${k}`,
		kind: 'tributary',
		label: s.spec.label,
		value: s.spec.value,
		date: s.spec.date ?? null,
		// geo: source → confluence (the trunk carries it the rest of the way)
		geo: [s.point, lerp2(s.point, confluence, 0.6), confluence],
		// schematic: a vertical bar in the upper band
		schematic: [[xAt(k), 0.16], [xAt(k), 0.66]]
	}));

	const trunk = {
		id: 'trunk',
		kind: 'trunk',
		label: config.hub.label ?? 'Total',
		value: total,
		date: null,
		geo: [confluence, lerp2(confluence, hubPoint, 0.5), hubPoint],
		schematic: [[0.5, 0.66], [0.5, 0.9]]
	};

	return {
		flows: [...tributaries, trunk],
		hub: { label: config.hub.label, point: hubPoint },
		widthDomain: [0, total],
		unit: config.unit
	};
}
