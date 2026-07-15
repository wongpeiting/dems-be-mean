import { base } from '$app/paths';
import usStates from '$lib/data/us-states.json';

// Built-in maps ship with the kit. Add your own here (one line) for a permanent
// map, or just drop a GeoJSON file in static/basemaps/ and name it in story.json.
const BUILTIN = {
	'us-states': usStates
};

export const builtinBasemaps = Object.keys(BUILTIN);

/**
 * Resolve a basemap name from story.json to a GeoJSON FeatureCollection.
 * - a built-in key (e.g. "us-states") → the bundled map
 * - anything else → fetched from static/basemaps/<name>.json (drop your file there)
 *
 * Every feature needs a name in `properties.NAME` (or `name`), because the story's
 * `region:` values are matched against those names.
 *
 * @param {string} name
 * @returns {Promise<object>} a GeoJSON FeatureCollection
 */
export async function loadBasemap(name) {
	if (BUILTIN[name]) return BUILTIN[name];
	const file = name.endsWith('.json') ? name : `${name}.json`;
	const res = await fetch(`${base}/basemaps/${file}`);
	if (!res.ok) {
		throw new Error(
			`Basemap '${name}' not found. Use a built-in (${builtinBasemaps.join(', ')}), ` +
				`or drop the GeoJSON at static/basemaps/${file}.`
		);
	}
	return res.json();
}
