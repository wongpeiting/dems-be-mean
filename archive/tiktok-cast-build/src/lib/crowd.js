const CONFIGURED = import.meta.env?.VITE_CROWD_URL || '';

export function postGuess(payload, url = CONFIGURED) {
	if (!url) return;
	fetch(`${url}/api/guess`, {
		method: 'POST',
		headers: { 'content-type': 'application/json' },
		body: JSON.stringify(payload),
		keepalive: true
	}).catch(() => {});
}

export async function fetchStats(roundIds, seeded, url = CONFIGURED) {
	if (!url) return seeded;
	try {
		const ctrl = new AbortController();
		const t = setTimeout(() => ctrl.abort(), 2500);
		const res = await fetch(`${url}/api/stats?rounds=${roundIds.join(',')}`, { signal: ctrl.signal });
		clearTimeout(t);
		if (!res.ok) return seeded;
		const live = await res.json();
		return { ...seeded, ...live };
	} catch {
		return seeded;
	}
}
