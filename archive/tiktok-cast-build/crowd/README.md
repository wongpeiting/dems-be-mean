# tiktok-cast-crowd

Vercel serverless backend for crowd-sourced quiz stats, backed by Upstash Redis.

No `vercel.json` is needed — Vercel's zero-config detection picks up files in `api/` automatically.

## Deploy

1. **Link to a Vercel project** (create one if needed):

   ```bash
   npx vercel link
   ```

2. **Add the Upstash KV integration** in the Vercel dashboard:
   - Go to your project → Integrations → browse for **Upstash** (or **Vercel KV**).
   - Create a Redis database and connect it to this project.
   - Vercel will automatically inject `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` as environment variables.

3. **Deploy to production:**

   ```bash
   npx vercel deploy --prod
   ```

4. **Set the URL in the main site's `.env`:**

   ```
   VITE_CROWD_URL=https://your-deployment.vercel.app
   ```

## Smoke tests

Replace `$URL` with your production URL.

```bash
# POST a guess
curl -s -X POST "$URL/api/guess" \
  -H "content-type: application/json" \
  -d '{"roundId":"12345","choice":"dem"}' | jq .

# GET stats for a round
curl -s "$URL/api/stats?rounds=12345" | jq .
```

Expected responses:
- POST → `{"ok":true}`
- GET → `{"12345":{"dem":1,"rep":0}}`
