import { Redis } from '@upstash/redis';
const redis = Redis.fromEnv();
export default async function handler(req, res) {
	res.setHeader('Access-Control-Allow-Origin', '*');
	res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=300');
	const ids = String(req.query.rounds || '').split(',').filter((s) => /^\d{5,25}$/.test(s)).slice(0, 64);
	if (!ids.length) return res.status(400).json({});
	const keys = ids.flatMap((id) => [`g:${id}:dem`, `g:${id}:rep`]);
	const vals = await redis.mget(...keys);
	const out = {};
	ids.forEach((id, i) => (out[id] = { dem: vals[i * 2] ?? 0, rep: vals[i * 2 + 1] ?? 0 }));
	return res.status(200).json(out);
}
