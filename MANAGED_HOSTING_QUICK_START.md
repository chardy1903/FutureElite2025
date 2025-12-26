# Managed Hosting Quick Start

**Platform:** Managed hosting (Heroku, Railway, Render, Fly.io)  
**Domain:** futureelite.co.uk  
**Time:** 15-30 minutes

---

## Quick Steps

### 1. Choose Platform (5 min)

**Recommended:** Railway or Render (easiest)

**Options:**
- **Railway** - https://railway.app (modern, simple)
- **Render** - https://render.com (good free tier)
- **Heroku** - https://heroku.com (most popular)
- **Fly.io** - https://fly.io (global edge)

### 2. Create Project (5 min)

**Railway:**
```bash
# Install CLI
brew install railway

# Login and init
railway login
railway init
```

**Render:**
- Go to render.com
- Connect GitHub/GitLab repo
- Create Web Service

**Heroku:**
```bash
heroku login
heroku create futureelite
```

### 3. Set Environment Variables (5 min)

**In platform dashboard, add:**
```bash
SECRET_KEY=<generate: python3 -c "import secrets; print(secrets.token_hex(32))">
FLASK_ENV=production
```

**If using Stripe, also add:**
```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 4. Deploy (5 min)

**Railway:**
```bash
railway up
```

**Render:**
- Auto-deploys on git push

**Heroku:**
```bash
git push heroku main
```

### 5. Configure Custom Domain (5 min)

**In platform dashboard:**
- Add custom domain: `futureelite.co.uk`
- Add custom domain: `www.futureelite.co.uk`
- Platform will provide DNS instructions

### 6. Configure DNS in GoDaddy (5 min)

**Follow platform's DNS instructions. Usually:**
- Add CNAME: `@` → `platform-provided-domain`
- Add CNAME: `www` → `platform-provided-domain`

**See:** `GODADDY_DNS_SETUP.md` for GoDaddy-specific steps

### 7. Test (2 min)

```bash
curl https://futureelite.co.uk/health
```

Visit: `https://futureelite.co.uk`

---

## Platform Comparison

| Platform | Ease | Free Tier | Cost | Best For |
|----------|------|-----------|------|----------|
| Railway | ⭐⭐⭐⭐⭐ | Limited | $5-10/mo | Modern apps |
| Render | ⭐⭐⭐⭐ | Yes (spins down) | $7/mo | Simple deployment |
| Heroku | ⭐⭐⭐ | No | $7/mo | Established platform |
| Fly.io | ⭐⭐⭐⭐ | Generous | Pay-as-go | Global edge |

---

## Required Files (Already Created)

- ✅ `wsgi.py` - WSGI entry point
- ✅ `gunicorn.conf.py` - Gunicorn config (uses $PORT)
- ✅ `Procfile` - Process definition
- ✅ `requirements.txt` - Dependencies
- ✅ `runtime.txt` - Python version

---

## Environment Variables Checklist

**Required:**
- [ ] `SECRET_KEY` (32+ chars)
- [ ] `FLASK_ENV=production`

**If using Stripe:**
- [ ] `STRIPE_SECRET_KEY`
- [ ] `STRIPE_PUBLISHABLE_KEY`
- [ ] `STRIPE_WEBHOOK_SECRET`
- [ ] `STRIPE_MONTHLY_PRICE_ID`
- [ ] `STRIPE_ANNUAL_PRICE_ID`

---

## Troubleshooting

### App Won't Start
- Check logs in platform dashboard
- Verify `SECRET_KEY` is set
- Verify `PORT` is used (platform sets this automatically)

### Health Check Fails
```bash
curl https://futureelite.co.uk/health
```
- Check app is running
- Check environment variables

### DNS Issues
- Wait 5-15 minutes for propagation
- Verify DNS records match platform requirements
- Check platform's custom domain status

---

## Next Steps

1. Choose platform
2. Follow `MANAGED_HOSTING_DEPLOYMENT.md` for detailed steps
3. Configure DNS per platform instructions
4. Test deployment

---

**Ready to deploy!** 🚀

