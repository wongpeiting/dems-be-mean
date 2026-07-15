// Reusable render-and-screenshot harness — the definition of "done" for every
// kit task. Loads a route in headless Chromium at desktop + mobile widths,
// screenshots three scroll positions each, into .screenshots/.
//
//   node scripts/shoot.mjs <url> [label]
//   e.g. node scripts/shoot.mjs http://localhost:5173/kit-demo demo
//
// Chromium is already cached by the local Playwright install.
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';

const url = process.argv[2] || 'http://localhost:5173/kit-demo';
const label = process.argv[3] || 'shot';
const OUT = '.screenshots';
mkdirSync(OUT, { recursive: true });

const VIEWPORTS = [
	{ name: 'desk', width: 1280, height: 800 },
	{ name: 'mob', width: 390, height: 844 }
];
const POSITIONS = [0.0, 0.5, 1.0];

const browser = await chromium.launch();
const errors = [];
for (const vp of VIEWPORTS) {
	const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 1.5 });
	page.on('pageerror', (e) => errors.push(`${vp.name}: ${e.message}`));
	page.on('console', (m) => m.type() === 'error' && errors.push(`${vp.name} console: ${m.text()}`));
	await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
	await page.waitForTimeout(600);
	for (const [i, frac] of POSITIONS.entries()) {
		await page.evaluate((f) => window.scrollTo(0, document.body.scrollHeight * f), frac);
		await page.waitForTimeout(500);
		await page.screenshot({ path: `${OUT}/${label}-${vp.name}-${i}.png` });
	}
	await page.close();
}
await browser.close();
console.log(`wrote ${VIEWPORTS.length * POSITIONS.length} shots to ${OUT}/ (${label}-*)`);
console.log(errors.length ? 'PAGE ERRORS:\n' + errors.slice(0, 12).join('\n') : 'no page errors');
