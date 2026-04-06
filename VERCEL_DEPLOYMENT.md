# 🚀 Deploy to Vercel (100% Free) - Complete Guide

## ⚠️ Important: Vercel Architecture

Vercel doesn't support long-running Python servers. Instead:
- **Frontend**: Static site (React built files)
- **Backend**: Serverless Python functions (`/api/*.py`)
- **Database**: External PostgreSQL (Neon.tech — Free)

---

## Step-by-Step Deployment

### Step 1: Create Free PostgreSQL Database on Neon

1. Go to **https://neon.tech**
2. Sign up with GitHub (free)
3. Click **"New Project"**
4. Name it: `resume-matcher-db`
5. Click **"Create"**
6. Copy the **Connection String** (looks like):
   ```
   postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/resume-db?sslmode=require
   ```
7. Keep this safe — you'll need it in Step 3

---

### Step 2: Push Code to GitHub

```bash
cd /home/arthas/Documents/GitHub/Resume-Chatbot

# Make sure everything is committed
git add .
git commit -m "Ready for Vercel deployment"

# Push to GitHub
git push origin main
```

---

### Step 3: Deploy to Vercel

#### Option A: Via Vercel Dashboard (Easiest)

1. Go to **https://vercel.com/new**
2. Sign in with GitHub
3. **Import** your `Resume-Chatbot` repository
4. Configure the project:

| Setting | Value |
|---------|-------|
| **Framework Preset** | Vite |
| **Root Directory** | `.` (root) |
| **Build Command** | `npm run vercel-build` |
| **Output Directory** | `dist` |
| **Install Command** | `npm install` |

5. **Add Environment Variables** (click "Environment Variables"):

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/resume-db?sslmode=require` |
| `GROQ_API_KEY` | Your Groq API key |
| `SERPAPI_KEY` | Your SerpAPI key |
| `CORS_ORIGINS` | `*` |
| `DEBUG` | `false` |

6. Click **"Deploy"**
7. Wait 2-3 minutes
8. **Done!** Your app is live at `https://your-project.vercel.app`

#### Option B: Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd /home/arthas/Documents/GitHub/Resume-Chatbot
vercel

# Set environment variables
vercel env add DATABASE_URL
vercel env add GROQ_API_KEY
vercel env add SERPAPI_KEY
vercel env add CORS_ORIGINS

# Deploy to production
vercel --prod
```

---

## How It Works

```
your-app.vercel.app
├── /                    → React frontend (static)
├── /resume              → React frontend (static)
├── /jobs                → React frontend (static)
├── /api/users           → api/index.py (serverless)
├── /api/resumes/upload  → api/index.py (serverless)
├── /api/jobs/scan       → api/index.py (serverless)
└── /api/health          → api/index.py (serverless)
```

All API requests go through `api/index.py` which routes them like FastAPI does.

---

## Environment Variables on Vercel

After deployment, add these in Vercel Dashboard → Settings → Environment Variables:

| Variable | Where to Get |
|----------|-------------|
| `DATABASE_URL` | Neon.tech (Step 1) |
| `GROQ_API_KEY` | https://console.groq.com |
| `SERPAPI_KEY` | https://serpapi.com |
| `CORS_ORIGINS` | `*` (or your custom domain) |

---

## Limitations (Free Tier)

| Limit | Value | Impact |
|-------|-------|--------|
| Serverless timeout | 10 seconds | Job scans may timeout if many jobs |
| Database | External (Neon) | Free tier: 0.5GB storage |
| Serverless invocations | 100k/month | Plenty for personal use |
| Bandwidth | 100GB/month | Plenty |
| Builds | Unlimited | No limit |

---

## Troubleshooting

### "API timeout" on job scan
- Vercel has a 10s limit for serverless functions
- The app will scan fewer jobs to stay within limit
- Solution: Reduce `max_results` to 5-10

### "Database connection error"
- Verify `DATABASE_URL` is correct in Vercel env vars
- Check Neon.tech project is active
- Test connection string locally first

### "CORS error"
- Set `CORS_ORIGINS` to `*` in Vercel env vars
- Or set to your exact Vercel URL

### Frontend shows but API doesn't work
- Check `api/index.py` exists in your repo
- Verify `vercel.json` routes are correct
- Check Vercel build logs for Python errors

---

## Custom Domain (Optional)

1. Vercel Dashboard → Your Project → Settings → Domains
2. Add your domain
3. Follow DNS configuration steps
4. Free SSL automatically applied

---

## Cost: $0/month

| Service | Cost |
|---------|------|
| Vercel Frontend | Free |
| Vercel API (100k invocations) | Free |
| Neon PostgreSQL (0.5GB) | Free |
| Groq API | Free tier |
| SerpAPI | Free (100 searches/month) |
| **Total** | **$0** |
