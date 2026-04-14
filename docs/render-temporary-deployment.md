# Temporary Use of Render Instead of AWS EC2

## Context

AWS account is temporarily inaccessible. We are using Render's free tier to get the MVP live. When the AWS account is recovered, migration is a clean swap — see [Migrating Back to EC2](#migrating-back-to-ec2) below.

## What Changed in the Sprint Plan

- **Task 3.3 replaced entirely** — skip Dockerfile SSH/Caddy/EC2 steps. Render handles all of that automatically from the existing `Dockerfile`.
- **Task 3.4 stays the same** — just use the Render URL (`https://pickle-playbook.onrender.com`) instead of an EC2 IP.

## Deployment Steps We Followed

**Step 1** — Go to [render.com](https://render.com) and sign up with GitHub.

**Step 2** — Create a new Web Service:
- Click "New" → "Web Service"
- Connect the `pickle-playbook` GitHub repo
- Render auto-detects the `Dockerfile`

**Step 3** — Configure the service:
- Name: `pickle-playbook` (this is what appears in the public hostname)
- Region: Oregon (closest to Santa Clara)
- Instance type: Free
- Environment variables:
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `ANTHROPIC_API_KEY`
  - `OPENAI_API_KEY`

**Step 4** — Deploy. Render builds from the `Dockerfile` automatically. Service URL: `https://pickle-playbook.onrender.com`

**Step 5** — Update Vercel: set `VITE_API_URL=https://pickle-playbook.onrender.com` and redeploy.

## Cold Start Warm-Up (Free Tier Behavior)

Render's free tier spins down after 15 minutes of inactivity, causing 10-30 second cold starts. To hide the cold start latency, fire a silent prefetch to `/health` when the app loads — before the user clicks "Analyze":

```js
// App.jsx or main entry point
useEffect(() => {
  fetch(`${import.meta.env.VITE_API_URL}/health`).catch(() => {});
}, []);
```

This triggers the container wake-up during page load while the user is dragging players around, not when they click the button. The sprint plan already has a skeleton loader on the analyze endpoint, so the UX degrades gracefully if the warm-up doesn't finish in time.

## Migrating Back to EC2

When the AWS account is recovered, migration is:

1. Deploy the same `Dockerfile` to an EC2 instance (or use the existing `docker-compose.pickle.yml`)
2. Set the same four environment variables on the instance
3. Update `VITE_API_URL` in Vercel to the EC2 address
4. Redeploy the Vercel frontend
5. Delete the Render service

No code changes required — the `Dockerfile`, `caddy/pickle.caddyfile`, and `docker-compose.pickle.yml` are already wired for EC2/Caddy deployment.
