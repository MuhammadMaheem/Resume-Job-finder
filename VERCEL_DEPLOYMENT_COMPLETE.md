# ✅ Complete Vercel + Neon Deployment Guide (FIXED)

## 🔧 Issues Fixed

1. ✅ **api/requirements.txt** - Added psycopg connection pooling libraries
2. ✅ **api/config.py** - Auto-detects VERCEL_URL for CORS
3. ✅ **api/database.py** - Adds connection pooling for Neon serverless
4. ✅ **vercel.json** - Updated Python runtime 3.11 + cache headers

---

## 📋 Step 1: Neon Database Setup (5 minutes)

### 1.1 Create Neon Database
1. Go to **https://neon.tech**
2. Sign up with GitHub (completely FREE)
3. Click **"Create New Project"**
4. Name: `resume-matcher-db`
5. Region: Pick closest to you
6. Click **"Create Project"**

### 1.2 Copy Connection String
1. Click on your project
2. Go to **"Connection strings"**
3. Copy the **PostgreSQL** connection string (starts with `postgresql://`)
   ```
   postgresql://user:password@ep-xxx.regxxx.aws.neon.tech/resume_db?sslmode=require
   ```
4. ⚠️ **Save this securely** - you'll need it in next step

---

## 📋 Step 2: GitHub Setup

### 2.1 Initialize Git (if not already done)
```bash
cd /home/arthas/Documents/GitHub/Resume-Chatbot

# Check if git repo exists
git status

# If not, initialize
git init
git add .
git commit -m "Initial commit - ready for Vercel deployment"
```

### 2.2 Push to GitHub
```bash
# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/Resume-Chatbot.git

# Push to main branch
git branch -M main
git push -u origin main
```

---

## 📋 Step 3: Vercel Deployment (10 minutes)

### 3.1 Import Project to Vercel
1. Go to **https://vercel.com/new**
2. Click **"Select Repository"**
3. Search and select `Resume-Chatbot`
4. Click **"Import"**

### 3.2 Configure Project Settings
1. **Root Directory**: Leave as `.` (root)
2. **Build Command**: `npm run vercel-build`
3. **Output Directory**: `dist`
4. **Install Command**: `npm install`

### 3.3 Add Environment Variables ⚠️ CRITICAL

Click **"Add Environment Variable"** and add these 5 variables:

| Variable | Value | Required |
|----------|-------|----------|
| `GROQ_API_KEY` | Your Groq API key from https://console.groq.com | ✅ Yes |
| `SERPAPI_KEY` | Your SerpAPI key from https://serpapi.com | ✅ Yes |
| `DATABASE_URL` | Your Neon PostgreSQL connection string (from Step 1) | ✅ Yes |
| `DEBUG` | `false` | ✅ Yes |
| `PYTHON_RUNTIME` | `python3.11` | ✅ Yes |

**Example DATABASE_URL:**
```
postgresql://user:password@ep-xxx.regxxx.aws.neon.tech/resume_db?sslmode=require
```

### 3.4 Deploy
1. Click **"Deploy"**
2. Wait 2-3 minutes for build to complete
3. ✅ Done! Your app is now live

---

## ✅ Post-Deployment Verification

### Test Your Deployment

```bash
# Test health endpoint
curl https://your-project.vercel.app/api/health

# Expected response:
# {"status":"ok","app":"Resume Job Matcher AI"}
```

### Frontend API Configuration

The frontend automatically routes to `/api/*` which maps to your serverless functions.

**Verify in browser console:**
```javascript
// Open DevTools > Console and run:
fetch('/api/health').then(r => r.json()).then(console.log)
// Should show: {status: "ok", app: "Resume Job Matcher AI"}
```

---

## 🚀 Frontend Environment Setup

Update your `.env` file for Vercel build:

```env
# .env (local development)
VITE_API_URL=http://localhost:8000

# For Vercel (auto-resolved)
# Frontend proxy automatically routes /api/* to serverless functions
```

Your `vite.config.ts` is already configured to:
- Use `/api` proxy during local dev (to `http://localhost:8000`)
- Use relative `/api` paths in production (which route to Vercel serverless)

---

## 🔗 Database Connection Pooling

Neon + Vercel Serverless automatically handles:
- ✅ Connection pooling (up to 15 connections)
- ✅ Automatic idle timeout (5 minutes)
- ✅ SSL/TLS encryption by default
- ✅ Free tier includes 1000 connection hours/month

**No additional configuration needed!**

---

## 📱 Frontend Deployment

The React app is deployed to Vercel's CDN:
- ✅ Auto-rebuilds on git push
- ✅ Automatic HTTPS
- ✅ Global CDN edge caching
- ✅ Automatic Gzip compression

---

## 🆘 Troubleshooting

### Build Fails with Python Error
```bash
# Check Python version (Vercel uses 3.11 by default)
# vercel.json is set to python3.11
# If error persists, check requirements.txt for syntax errors
```

### Database Connection Timeout
```
Error: connection timeout
```
Solution:
1. Verify `DATABASE_URL` is correct (copy from Neon again)
2. Check it includes `?sslmode=require` at the end
3. Wait 30 seconds for Vercel to propagate env vars

### API Routes Return 404
1. Check `/api/health` endpoint returns `{"status":"ok"}`
2. Verify `vercel.json` routes are correct
3. Clear browser cache (Ctrl+Shift+Del)

### CORS Errors
- ✅ Already fixed in `api/config.py`
- Auto-detects `VERCEL_URL` environment variable
- No manual CORS configuration needed

---

## 📊 Monitoring & Logs

### View Deployment Logs
1. Go to your Vercel project dashboard
2. Click **"Deployments"**
3. Click the latest deployment
4. View **"Logs"**

### View Function Logs
1. Go to **"Functions"**
2. Click `/api/index.py`
3. View real-time execution logs

---

## ♻️ Continuous Deployment

After setup, deployment is automatic:
```bash
# Just commit and push
git add .
git commit -m "Fix: Update resume parsing logic"
git push origin main

# Vercel automatically: ✅ Rebuilds ✅ Runs tests ✅ Deploys
# Check deployment status in Vercel dashboard
```

---

## 🎉 Success Checklist

- [ ] Neon database created and connection string copied
- [ ] GitHub repository created and code pushed
- [ ] Vercel project imported
- [ ] All 5 environment variables set in Vercel dashboard
- [ ] Deployment completed successfully
- [ ] `/api/health` endpoint responds with `{"status":"ok"}`
- [ ] Frontend loads and makes API calls successfully
- [ ] Database is storing/retrieving data

---

## 📞 Support

If you encounter issues:
1. Check Vercel deployment logs
2. Verify all environment variables are set
3. Test API endpoint: `https://your-project.vercel.app/api/health`
4. Check browser DevTools Network tab for API calls

---

## 🔐 Production Security Checklist

- ✅ `DEBUG=false` in production
- ✅ HTTPS enabled (Vercel default)
- ✅ SSL/TLS for database (Neon default)
- ✅ Connection pooling for query efficiency
- ✅ Environment variables not in code
- ✅ CORS configured for your domain

Your Resume Chatbot is now **production-ready on Vercel + Neon** 🎉
