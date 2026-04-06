# Deployment Guide - Resume Job Matcher AI

## 🚀 Option 1: Deploy to Render (Recommended - Free)

### Prerequisites
- GitHub account
- Groq API key (https://console.groq.com)
- SerpAPI key (https://serpapi.com)

### Step 1: Push Code to GitHub

```bash
cd /home/arthas/Documents/GitHub/Resume-Chatbot

# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Resume Job Matcher AI"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/resume-job-matcher.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy Backend to Render

1. Go to **https://render.com** and sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `resume-matcher-api`
   - **Region**: Oregon (or closest to you)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: **Free**

5. Add Environment Variables:
   ```
   GROQ_API_KEY = your_groq_api_key_here
   SERPAPI_KEY = your_serpapi_key_here
   CORS_ORIGINS = *
   DEBUG = false
   DATABASE_URL = sqlite:///./resume_chatbot.db
   ```

6. Click **"Create Web Service"**
7. Wait ~3 minutes for deployment
8. **Copy your backend URL** (e.g., `https://resume-matcher-api-xxx.onrender.com`)

### Step 3: Deploy Frontend to Render

1. Click **"New +"** → **"Static Site"**
2. Connect the same GitHub repository
3. Configure:
   - **Name**: `resume-matcher-frontend`
   - **Branch**: `main`
   - **Root Directory**: Leave blank
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
   - **Plan**: **Free**

4. Add Environment Variable:
   ```
   VITE_API_URL = https://your-backend-url.onrender.com
   ```
   *(Replace with your actual backend URL from Step 2)*

5. Click **"Create Static Site"**
6. Wait ~2 minutes for deployment
7. **Your app is live!** (e.g., `https://resume-matcher-frontend-xxx.onrender.com`)

---

## 🐳 Option 2: Deploy with Docker (Any VPS)

### Prerequisites
- VPS (DigitalOcean, AWS, GCP, etc.) with Docker installed
- Domain name (optional)

### Step 1: Clone Your Repo

```bash
git clone https://github.com/YOUR_USERNAME/resume-job-matcher.git
cd resume-job-matcher
```

### Step 2: Create Environment File

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

Edit `.env`:
```
GROQ_API_KEY=your_groq_api_key_here
SERPAPI_KEY=your_serpapi_key_here
DATABASE_URL=postgresql://postgres:postgres@db:5432/resume_matcher
CORS_ORIGINS=https://your-domain.com
DEBUG=false
```

### Step 3: Deploy with Docker Compose

```bash
docker-compose up -d --build
```

That's it! Your app is running at:
- **Frontend**: http://your-server-ip:3000
- **Backend**: http://your-server-ip:8000

### Step 4: (Optional) Add Nginx + HTTPS

```bash
sudo apt install nginx certbot python3-certbot-nginx

# Create nginx config
sudo nano /etc/nginx/sites-available/resume-matcher
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/resume-matcher /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Get free SSL certificate
sudo certbot --nginx -d your-domain.com
```

---

## ⚡ Option 3: Deploy to Vercel (Frontend) + Railway (Backend)

### Backend on Railway
1. Go to **https://railway.app**
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repo
4. Set root directory to `backend`
5. Add environment variables:
   ```
   GROQ_API_KEY = your_key
   SERPAPI_KEY = your_key
   CORS_ORIGINS = https://your-frontend.vercel.app
   DATABASE_URL = (Railway auto-generates this when you add PostgreSQL)
   ```
6. Deploy → Copy your Railway URL

### Frontend on Vercel
1. Go to **https://vercel.com**
2. Click **"New Project"** → Import your repo
3. Set root directory to `.`
4. Build command: `npm run build`
5. Output directory: `dist`
6. Add environment variable:
   ```
   VITE_API_URL = https://your-backend.railway.app
   ```
7. Deploy → Done!

---

## 🔧 Troubleshooting

### Frontend can't connect to backend
- Check CORS_ORIGINS in backend includes your frontend URL
- Verify VITE_API_URL points to backend URL (not localhost)

### Backend database errors
- Render free PostgreSQL expires after 90 days → upgrade or switch to SQLite
- Check DATABASE_URL format is correct

### Build fails on Render
- Check Node.js version (Render uses v18+ by default)
- Check Python version (Render uses 3.11 by default)
- Ensure all dependencies are in requirements.txt / package.json

### App is slow on free tier
- Render free tier spins down after 15 min → add uptime monitor to keep alive
- Consider upgrading to paid plan ($7/month)

---

## 📊 Cost Comparison

| Platform | Frontend | Backend | Database | Total/Month |
|----------|----------|---------|----------|-------------|
| **Render (Free)** | Free | Free* | Free (90 days) | $0 |
| **Render (Paid)** | $7 | $7 | $7 | $21 |
| **Railway** | $5 | $5 | $5 | $15 |
| **Vercel + Railway** | Free | $5 | $5 | $10 |
| **DigitalOcean** | $6 | $6 | $15 | $27 |

*Render free tier spins down after 15 min of inactivity (30s cold start)
