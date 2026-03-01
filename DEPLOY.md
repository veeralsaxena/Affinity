# 🚀 RelAItion — Deployment Guide

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────┐
│  Vercel (FREE)  │────▶│  Railway (FREE)  │────▶│ PostgreSQL│
│  Next.js Front  │     │  FastAPI Backend  │     │ (Railway) │
└─────────────────┘     │  + Playwright     │     └───────────┘
                        │  + LangGraph      │     ┌───────────┐
                        │                   │────▶│   Redis   │
                        └──────────────────┘     │ (Railway) │
                                                  └───────────┘
```

---

## Step 1 · Deploy Backend on Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **"New Project"** → **"Deploy from GitHub Repo"**
3. Select the `Affinity` repo, set the **root directory** to `backend`
4. Railway will auto-detect the `Dockerfile` and `railway.toml`

### Add Services
5. Click **"+ New"** → **"Database"** → **PostgreSQL** (Railway provisions it free)
6. Click **"+ New"** → **"Database"** → **Redis** (Railway provisions it free)

### Set Environment Variables
7. Go to your **backend service** → **Variables** tab and add:

| Variable | Value |
|---|---|
| `DATABASE_URL` | *Auto-copied from Railway PostgreSQL* |
| `REDIS_URL` | *Auto-copied from Railway Redis* |
| `GEMINI_API_KEY` | Your Gemini API key |
| `JWT_SECRET` | A random 32+ character string |

> **Tip:** Railway auto-injects `DATABASE_URL` and `REDIS_URL` if you link the services.

8. Click **Deploy** — Railway builds the Docker image and starts the server
9. Note the generated URL (e.g. `https://affinity-backend-production.up.railway.app`)

---

## Step 2 · Deploy Frontend on Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click **"Add New Project"** → Import the `Affinity` repo
3. Set **Root Directory** to `frontend`
4. Vercel auto-detects Next.js — no extra config needed

### Set Environment Variables
5. Go to **Settings** → **Environment Variables** and add:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://your-railway-backend-url.up.railway.app` |

6. Click **Deploy** — Vercel builds and deploys in ~60 seconds
7. Your live URL is ready (e.g. `https://affinity.vercel.app`)

---

## Step 3 · Verify

1. Open your Vercel URL in a browser
2. Sign up for an account
3. Upload a WhatsApp chat export
4. Watch the AI pipeline analyze it in real-time!

---

## Notes

- **WhatsApp Automation**: The Playwright browser automation requires a desktop context (headed browser). It works locally but **not** on Railway's serverless containers. For the hackathon demo, run WhatsApp automation locally and use the cloud deployment for the rest of the pipeline.
- **Free Tier Limits**: Railway gives $5 free credit/month. More than enough for a hackathon.
- **Custom Domain**: Both Vercel and Railway support free custom domains if wanted.
