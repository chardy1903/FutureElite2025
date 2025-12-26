# Managed Hosting Deployment Guide

**Platform:** Managed hosting (Heroku, Railway, Render, Fly.io, etc.)  
**Domain:** futureelite.co.uk  
**Entry Point:** `wsgi.py` with Gunicorn

---

## Overview

This guide is for deploying to managed hosting platforms where:
- ✅ Platform handles HTTPS/SSL automatically
- ✅ Platform provides reverse proxy
- ✅ Platform manages process lifecycle
- ✅ No root access or systemd needed
- ✅ Gunicorn runs via `wsgi.py`

---

## Supported Platforms

This configuration works with:
- **Heroku** - Most popular, easy to use
- **Railway** - Modern, simple deployment
- **Render** - Good free tier
- **Fly.io** - Global edge deployment
- **DigitalOcean App Platform** - Managed PaaS
- **Any platform supporting:** Python, Gunicorn, WSGI

---

## Prerequisites

1. ✅ Deployment package ready: `futureelite-deployment-*.tar.gz`
2. ✅ Account on your chosen platform
3. ✅ Domain: `futureelite.co.uk` (GoDaddy)

---

## Step 1: Platform-Specific Setup

### Option A: Heroku

**1. Install Heroku CLI:**
```bash
# macOS
brew tap heroku/brew && brew install heroku

# Or download from: https://devcenter.heroku.com/articles/heroku-cli
```

**2. Login:**
```bash
heroku login
```

**3. Create app:**
```bash
cd /path/to/GoalTracker
heroku create futureelite
```

**4. Set environment variables:**
```bash
heroku config:set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
heroku config:set FLASK_ENV=production

# If using Stripe:
heroku config:set STRIPE_SECRET_KEY=sk_live_...
heroku config:set STRIPE_PUBLISHABLE_KEY=pk_live_...
heroku config:set STRIPE_WEBHOOK_SECRET=whsec_...
```

**5. Deploy:**
```bash
git init
git add .
git commit -m "Initial deployment"
git push heroku main
```

### Option B: Railway

**1. Install Railway CLI:**
```bash
# macOS
brew install railway

# Or: https://docs.railway.app/develop/cli
```

**2. Login:**
```bash
railway login
```

**3. Initialize project:**
```bash
cd /path/to/GoalTracker
railway init
```

**4. Set environment variables:**
- Go to Railway dashboard → Your project → Variables
- Add: `SECRET_KEY`, `FLASK_ENV=production`, etc.

**5. Deploy:**
```bash
railway up
```

### Option C: Render

**1. Connect repository:**
- Go to: https://render.com
- Connect your Git repository (GitHub, GitLab, etc.)

**2. Create Web Service:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn -c gunicorn.conf.py wsgi:app`
- **Environment:** Python 3

**3. Set environment variables:**
- In Render dashboard → Environment
- Add: `SECRET_KEY`, `FLASK_ENV=production`, etc.

**4. Deploy:**
- Render auto-deploys on git push

### Option D: Fly.io

**1. Install Fly CLI:**
```bash
# macOS
brew install flyctl
```

**2. Login:**
```bash
fly auth login
```

**3. Initialize:**
```bash
cd /path/to/GoalTracker
fly launch
```

**4. Set secrets:**
```bash
fly secrets set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
fly secrets set FLASK_ENV=production
```

**5. Deploy:**
```bash
fly deploy
```

---

## Step 2: Create Procfile (For Heroku/Railway)

**Create `Procfile` in project root:**

```
web: gunicorn -c gunicorn.conf.py wsgi:app
```

**Or simpler version:**
```
web: gunicorn wsgi:app --bind 0.0.0.0:$PORT
```

**Note:** Some platforms auto-detect Gunicorn and don't need Procfile.

---

## Step 3: Update Gunicorn Configuration

**The existing `gunicorn.conf.py` should work, but ensure it uses `$PORT`:**

```python
# In gunicorn.conf.py, update bind to use PORT environment variable
import os
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
```

**Most platforms set `PORT` automatically.**

---

## Step 4: Environment Variables

**Required variables (set in platform dashboard):**

```bash
SECRET_KEY=<generate-with: python3 -c "import secrets; print(secrets.token_hex(32))">
FLASK_ENV=production
```

**If using Stripe:**
```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_MONTHLY_PRICE_ID=price_...
STRIPE_ANNUAL_PRICE_ID=price_...
```

**Optional:**
```bash
PROXY_FIX_NUM_PROXIES=1  # Usually 1 for managed platforms
```

---

## Step 5: Update Application for Managed Hosting

**The app already handles:**
- ✅ Gunicorn via `wsgi.py`
- ✅ Environment variables
- ✅ Production mode detection
- ✅ Proxy headers (ProxyFix)

**No changes needed!** The app is already configured correctly.

---

## Step 6: Configure Custom Domain

### Heroku

```bash
heroku domains:add futureelite.co.uk
heroku domains:add www.futureelite.co.uk
```

**Then configure DNS in GoDaddy:**
- Add CNAME: `futureelite.co.uk` → `your-app.herokuapp.com`
- Add CNAME: `www` → `your-app.herokuapp.com`

### Railway

1. Go to Railway dashboard → Settings → Networking
2. Add custom domain: `futureelite.co.uk`
3. Add custom domain: `www.futureelite.co.uk`
4. Configure DNS in GoDaddy per Railway's instructions

### Render

1. Go to Render dashboard → Your service → Settings → Custom Domains
2. Add: `futureelite.co.uk`
3. Add: `www.futureelite.co.uk`
4. Configure DNS in GoDaddy per Render's instructions

### Fly.io

```bash
fly domains add futureelite.co.uk
fly domains add www.futureelite.co.uk
```

**Then configure DNS in GoDaddy per Fly.io's instructions.**

---

## Step 7: Configure DNS in GoDaddy

**Each platform provides specific DNS instructions. Generally:**

### For CNAME-based platforms (Heroku, Railway, Render):

**In GoDaddy DNS:**
1. Add CNAME record:
   - Name: `@` (or leave blank)
   - Value: `your-app.platform-domain.com` (provided by platform)
   - TTL: `600`

2. Add CNAME record:
   - Name: `www`
   - Value: `your-app.platform-domain.com`
   - TTL: `600`

**Note:** Some platforms require A records - check platform documentation.

---

## Step 8: Verify Deployment

### Check Health Endpoint

```bash
curl https://futureelite.co.uk/health
```

**Expected:**
```json
{"status":"healthy","service":"FutureElite"}
```

### Check Application

Visit: `https://futureelite.co.uk` in browser

---

## Platform-Specific Notes

### Heroku

**Dyno types:**
- **Free tier:** Discontinued (use paid)
- **Basic:** $7/month (recommended)
- **Standard:** $25/month (for higher traffic)

**Buildpacks:**
- Python buildpack auto-detected
- No Procfile needed if using standard structure

**Logs:**
```bash
heroku logs --tail
```

### Railway

**Pricing:**
- Pay-as-you-go
- ~$5-10/month for small apps

**Logs:**
```bash
railway logs
```

### Render

**Free tier:**
- Spins down after 15 min inactivity
- Good for testing

**Paid:**
- $7/month for always-on

**Logs:**
- Available in Render dashboard

### Fly.io

**Pricing:**
- Generous free tier
- Pay for resources used

**Logs:**
```bash
fly logs
```

---

## Troubleshooting

### Application Won't Start

**Check logs:**
- Platform dashboard → Logs
- Or CLI: `platform logs` (varies by platform)

**Common issues:**
1. **Missing SECRET_KEY** - Set in environment variables
2. **Port binding** - Ensure Gunicorn uses `$PORT` environment variable
3. **Dependencies** - Check `requirements.txt` is complete

### Health Check Fails

**Verify:**
```bash
curl https://futureelite.co.uk/health
```

**Check:**
- Application is running (check platform dashboard)
- Environment variables are set
- No errors in logs

### DNS Not Working

**Verify DNS:**
```bash
dig futureelite.co.uk
```

**Check:**
- DNS records in GoDaddy match platform requirements
- DNS has propagated (wait 5-15 minutes)
- Platform has custom domain configured

---

## Quick Reference

### Required Files

- ✅ `wsgi.py` - WSGI entry point
- ✅ `gunicorn.conf.py` - Gunicorn configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Process definition (some platforms)

### Environment Variables

**Required:**
- `SECRET_KEY` (min 32 chars)
- `FLASK_ENV=production`

**Optional:**
- Stripe keys (if using)
- `PROXY_FIX_NUM_PROXIES=1`

### Deployment Commands

**Heroku:**
```bash
git push heroku main
```

**Railway:**
```bash
railway up
```

**Render:**
- Auto-deploys on git push

**Fly.io:**
```bash
fly deploy
```

---

## Next Steps

1. ✅ Choose your platform
2. ✅ Create account and project
3. ✅ Set environment variables
4. ✅ Deploy application
5. ✅ Configure custom domain
6. ✅ Configure DNS in GoDaddy
7. ✅ Test: `https://futureelite.co.uk`

---

**Ready for managed hosting deployment!** 🚀

