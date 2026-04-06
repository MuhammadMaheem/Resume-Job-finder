# 🔑 Vercel Environment Variables - Quick Reference

## Variables to Set in Vercel Dashboard

### Step-by-Step (Copy-Paste)

#### 1. GROQ_API_KEY
**Where to get**: https://console.groq.com
```
sk-proj-xxxxx... (your actual API key)
```

#### 2. SERPAPI_KEY  
**Where to get**: https://serpapi.com/manage/api_key
```
xxxxx... (your actual API key)
```

#### 3. DATABASE_URL
**Where to get**: https://neon.tech → Click project → Connection strings
```
postgresql://user:password@ep-XXX.region.aws.neon.tech/resume_db?sslmode=require
```
⚠️ **CRITICAL**: Must include `?sslmode=require` at the end

#### 4. DEBUG
```
false
```

#### 5. PYTHON_RUNTIME  
```
python3.11
```

---

## Vercel Dashboard Setup

1. Go to your project in Vercel
2. Click **"Settings"**
3. Click **"Environment Variables"**
4. Click **"Add New"**
5. Enter each variable above
6. Click **"Save"**
7. **Redeploy** after adding variables

---

## ✅ Verify Variables Are Set

After deployment:
```bash
# Test health endpoint (no env vars needed)
curl https://your-project.vercel.app/api/health

# Should return:
# {"status":"ok","app":"Resume Job Matcher AI"}
```

If this works, all env vars are properly configured!
