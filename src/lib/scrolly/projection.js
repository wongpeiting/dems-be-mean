import { geoMercator, geoEqualEarth, geoPath } from 'd3-geo';
import { setContext, getContext } from 'svelte';

const KEY = Symbol('scrolly-projection');

const MAKERS = { mercator: geoMercator, equalEarth: geoEqualEarth };

/**
 * Build one fitted projection that every layer shares, so coastlines, ribbons
 * and labels register exactly.
 * @param {object} geojson  a GeoJSON Feature/FeatureCollection to fit
 * @param {[number,number]} size  [width, height] of the viewBox
 * @param {object} [opts]
 * @param {'mercator'|'equalEarth'} [opts.type='mercator']
 * @param {[number,number,number,number]} [opts.padding]  [top,right,bottom,left] px inset
 * @returns {{project:(lngLat:[number,number])=>[number,number], path:(f:object)=>string, projection:import('d3-geo').GeoProjection, width:number, height:number}}
 */
export function buildProjection(geojson, [width, height], opts = {}) {
	const { type = 'mercator', padding } = opts;
	const projection = (MAKERS[type] ?? geoMercator)();
	if (padding) {
		const [t, r, b, l] = padding;
		projection.fitExtent([[l, t], [width - r, height - b]], geojson);
	} else {
		projection.fitSize([width, height], geojson);
	}
	const pathGen = geoPath(projection);
	return {
		projection,
		width,
		height,
		project: (lngLat) => projection(lngLat),
		path: (feature) => pathGen(feature) ?? ''
	};
}

/**
 * Share the current projection via context. Pass a GETTER so reactivity flows:
 * `setProjectionContext(() => currentProjection)`.
 * @param {() => ReturnType<typeof buildProjection>} getter
 */
export function setProjectionContext(getter) {
	setContext(KEY, getter);
}

/** @returns {() => ReturnType<typeof buildProjection>} the getter set by the page */
export function getProjectionContext() {
	return getContext(KEY);
}
