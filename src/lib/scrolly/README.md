# Scrollytelling flow-map kit

A small kit for building NYT-style scrollytelling flow maps in Svelte — a sticky
map that reveals as the reader scrolls, with **thick "pipe" lines whose width is
your number** (share, tonnes, dollars, people), tributaries merging into a trunk.
Modelled on NYT's "The Choking of Hormuz."

Everything is plain SVG (no Mapbox / WebGL), so it's light and crisp on phones.

## You only write data. The kit draws it.

You do **not** write any coordinates or code for the shapes. You describe your
story as a small object and hand it to `buildFlows`. Here is the whole contract:

```js
const story = {
  basemap: 'us-states',                 // which map you're drawing
  unit: 'million tonnes',               // what the numbers count (for labels)
  hub:  { label: 'Gulf export', region: 'Louisiana' },   // the ONE destination
  flows: [
    { label: 'Iowa',     region: 'Iowa',     value: 45 },
    { label: 'Illinois', region: 'Illinois', value: 30 },
    { label: 'Nebraska', region: 'Nebraska', value: 25 }
  ]
};
```

### The three rules that make your data work

1. **`value` — required, a positive number.** This is the *only* thing that sets
   how thick a line is. Bigger number = thicker line. It can be anything you can
   count.
2. **A location — required, one of two easy forms.**
   - `"region": "Iowa"` — a place **name that must exactly match a place in your
     basemap**. The kit finds its centre for you. *(Case doesn't matter.)*
   - or `"at": [longitude, latitude]` — if you already have coordinates.
3. **`date` — optional, `"YYYY"` or `"YYYY-MM"`.** Only needed if your story
   reveals flows over time; it orders them. Leave it out for a plain "where it all
   goes" map.

Plus **`label`** (the name shown) and one **`hub`** (the single place everything
flows into — give it a `region` or `at`, same as a flow).

### If something's wrong, it tells you exactly what

`buildFlows` checks your data and throws a plain-English error naming the row:

- `Flow 'Iowaa': region 'Iowaa' not found in basemap. Did you mean 'Iowa'?`
- `Flow 'Corn belt': value must be a positive number, got "lots".`
- `Flow 'Nowhere': needs a location — give it a "region" name or an "at": [lng, lat].`

## Wiring it up (once)

`buildFlows(story, basemap)` returns `{ flows, hub, widthDomain, unit }`. Feed
`flows` + `widthDomain` to `<FlowMap>`, and drive its `t` from the scroller:

```svelte
<script>
  import Scroller from '$lib/components/Scroller.svelte';
  import { buildProjection, setProjectionContext } from '$lib/scrolly/projection.js';
  import { buildFlows } from '$lib/scrolly/flows.js';
  import GeoLayer from '$lib/scrolly/GeoLayer.svelte';
  import FlowMap from '$lib/scrolly/FlowMap.svelte';
  import Annotation from '$lib/scrolly/Annotation.svelte';
  // ... build projection from your basemap, set it into context, then render
  //     <GeoLayer>, <FlowMap t={t}>, <Annotation> inside one <svg>.
</script>
```

See `src/routes/kit-demo/` for a complete, working example (`Stage.svelte` is the
graphic, `+page.svelte` is the scroll steps). Copy that folder, swap in your
`story`, and change the step text.

## The pieces

| Import | What it does |
|---|---|
| `flows.js` → `buildFlows(story, basemap)` | Turns your friendly data into drawable flows. Validates it. **Start here.** |
| `projection.js` → `buildProjection(map, [w,h], {fitTo})` | One shared map projection so lines + coastlines + labels line up. `fitTo` zooms to a subset (e.g. just the states in your story) so the map frames the action on mobile. |
| `GeoLayer.svelte` | Draws the basemap (coastlines / land). |
| `FlowMap.svelte` | The signature lines. `t` (0→1) morphs from a schematic bar chart to the geographic map — drive it from the scroller's `progress`. |
| `Annotation.svelte` | A label or callout anchored to a place (`{lngLat}`), a pixel (`{xy}`), or a fraction of the frame (`{frac}`). |
| `Scroller.svelte` (in `components/`) | The scroll engine. Pins the graphic, tracks `progress`/`index`. Not part of this folder but it's what you bind to. |

## How the width lines actually merge

Each line is one SVG stroke whose width = your value — that's why the look is
free and honest (the width *is* the number). Tributaries "merge" because the kit
adds a **trunk** whose value is the sum of the flows, running from where they meet
to the hub. If you ever need a single line that *tapers* as it splits (rare), see
the note in `geometry.js` about switching to filled ribbons.
