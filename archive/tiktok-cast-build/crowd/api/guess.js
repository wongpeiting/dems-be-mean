import { Redis } from '@upstash/redis';
const redis = Redis.fromEnv();
const ZONES = new Set(['video', 'caption', 'sound', 'emoji', 'vibes']);
export default async function handler(req, res) {
	res.setHeader('Access-Control-Allow-Origin', '*');
	res.setHeader('Access-Control-Allow-Headers', 'content-type');
	res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
	if (req.method === 'OPTIONS') return res.status(204).end();
	if (req.method !== 'POST') return res.status(405).end();
	const { roundId, choice, tellZone } = req.body ?? {};
	if (!/^\d{5,25}$/.test(String(roundId)) || !['dem', 'rep'].includes(choice))
		return res.status(400).json({ ok: false });
	await redis.incr(`g:${roundId}:${choice}`);
	if (tellZone && ZONES.has(tellZone)) await redis.incr(`t:${roundId}:${tellZone}`);
	return res.status(200).json({ ok: true });
}
