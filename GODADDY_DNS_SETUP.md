# GoDaddy DNS Configuration for futureelite.co.uk

This guide shows you exactly how to configure DNS records in GoDaddy for your FutureElite application.

---

## Prerequisites

Before configuring DNS, you need:
- ✅ Your server's IP address (where you'll deploy the app)
- ✅ Access to your GoDaddy account
- ✅ Domain: `futureelite.co.uk`

---

## Step 1: Find Your Server IP Address

**If you haven't deployed yet:**
- You'll get the IP when you create your VPS/server
- Common providers: DigitalOcean, Linode, Vultr, AWS EC2

**If you already have a server:**
```bash
# On your server, run:
curl ifconfig.me
# Or
hostname -I
```

**Write down your server IP:** `_________________`

---

## Step 2: Access GoDaddy DNS Management

1. **Log in to GoDaddy:**
   - Go to: https://www.godaddy.com
   - Sign in to your account

2. **Navigate to DNS:**
   - Click "My Products" or "Domains"
   - Find `futureelite.co.uk` in your domain list
   - Click on the domain name
   - Click "DNS" or "Manage DNS"

3. **You should see the DNS Records page**

---

## Step 3: Configure DNS Records

### Record 1: A Record (Root Domain)

**Purpose:** Points `futureelite.co.uk` to your server

**Configuration:**
- **Type:** `A`
- **Name:** `@` (or leave blank, or `futureelite.co.uk`)
- **Value:** `YOUR_SERVER_IP` (the IP address you wrote down)
- **TTL:** `600` (10 minutes) or `3600` (1 hour)

**In GoDaddy interface:**
1. Click "Add" or "+" to add a new record
2. Select "A" from the Type dropdown
3. Name field: Leave blank or enter `@`
4. Value field: Enter your server IP (e.g., `192.0.2.100`)
5. TTL: Select `600 seconds` (or your preference)
6. Click "Save"

**Example:**
```
Type: A
Name: @
Value: 192.0.2.100
TTL: 600
```

### Record 2: CNAME Record (www Subdomain)

**Purpose:** Points `www.futureelite.co.uk` to `futureelite.co.uk`

**Configuration:**
- **Type:** `CNAME`
- **Name:** `www`
- **Value:** `futureelite.co.uk` (or `@`)
- **TTL:** `600` (10 minutes) or `3600` (1 hour)

**In GoDaddy interface:**
1. Click "Add" or "+" to add a new record
2. Select "CNAME" from the Type dropdown
3. Name field: Enter `www`
4. Value field: Enter `futureelite.co.uk` or `@`
5. TTL: Select `600 seconds`
6. Click "Save"

**Example:**
```
Type: CNAME
Name: www
Value: futureelite.co.uk
TTL: 600
```

### Record 3: Remove/Update Existing Records (If Needed)

**Check for existing A or CNAME records:**
- If there's an existing A record pointing to a different IP, **update it** to your server IP
- If there's an existing CNAME for `www` pointing elsewhere, **update it** to `futureelite.co.uk`
- Remove any conflicting records

---

## Step 4: Verify DNS Configuration

### Expected DNS Records

After configuration, you should have:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | YOUR_SERVER_IP | 600 |
| CNAME | www | futureelite.co.uk | 600 |

### Verify Using Command Line

**Wait 5-15 minutes for DNS propagation, then test:**

```bash
# Check A record
dig futureelite.co.uk +short
# Should return your server IP

# Check www subdomain
dig www.futureelite.co.uk +short
# Should return futureelite.co.uk (which resolves to your IP)

# Or use nslookup
nslookup futureelite.co.uk
nslookup www.futureelite.co.uk
```

**Online DNS Checker:**
- Visit: https://www.whatsmydns.net/#A/futureelite.co.uk
- Enter your domain and check if DNS has propagated globally

---

## Step 5: DNS Propagation Timeline

**Typical propagation times:**
- **GoDaddy:** 5-15 minutes (usually very fast)
- **Global propagation:** 15 minutes to 48 hours
- **Most users:** Will see changes within 1-2 hours

**Factors affecting speed:**
- TTL value (lower = faster updates, but more DNS queries)
- Your location
- Your ISP's DNS cache

---

## Step 6: Test After Deployment

**Once your app is deployed and DNS is configured:**

```bash
# Test HTTP (should redirect to HTTPS)
curl -I http://futureelite.co.uk

# Test HTTPS
curl https://futureelite.co.uk/health

# Expected response:
# {"status":"healthy","service":"FutureElite"}
```

**In browser:**
- Visit: `https://futureelite.co.uk`
- Should load your application

---

## Troubleshooting

### DNS Not Resolving

**Problem:** `dig futureelite.co.uk` returns nothing or wrong IP

**Solutions:**
1. **Wait longer** - DNS can take up to 48 hours
2. **Check GoDaddy records** - Verify they're saved correctly
3. **Clear DNS cache:**
   ```bash
   # macOS
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder
   
   # Linux
   sudo systemd-resolve --flush-caches
   
   # Windows
   ipconfig /flushdns
   ```
4. **Use different DNS servers:**
   - Try Google DNS: `8.8.8.8`
   - Try Cloudflare DNS: `1.1.1.1`

### Wrong IP Address

**Problem:** DNS points to old/wrong server

**Solution:**
1. Update the A record in GoDaddy with correct IP
2. Wait for propagation
3. Verify with `dig futureelite.co.uk`

### www Subdomain Not Working

**Problem:** `www.futureelite.co.uk` doesn't resolve

**Solutions:**
1. Verify CNAME record exists in GoDaddy
2. Check CNAME value points to `futureelite.co.uk` (not the IP)
3. Wait for DNS propagation

### SSL Certificate Issues

**Problem:** Let's Encrypt can't verify domain

**Solution:**
- Ensure DNS is fully propagated before running certbot
- Use `certbot --nginx -d futureelite.co.uk -d www.futureelite.co.uk`
- Certbot will verify DNS automatically

---

## GoDaddy-Specific Notes

### DNS Management Interface

**GoDaddy's DNS interface may look like:**
- Records are listed in a table
- You can edit/delete existing records
- Add new records with a "+" or "Add" button
- Changes save automatically or require a "Save" button

### Common GoDaddy Issues

1. **"Hostname already exists"**
   - Delete the old record first, then add new one

2. **Changes not saving**
   - Make sure you click "Save" if there's a save button
   - Refresh the page and check if changes persisted

3. **TTL Options**
   - GoDaddy may offer: 600, 3600, 7200, etc.
   - Lower TTL = faster updates but more DNS queries
   - For initial setup: Use 600 (10 minutes)
   - After stable: Use 3600 (1 hour)

---

## Quick Reference

**Your DNS Records:**
```
A     @              YOUR_SERVER_IP     600
CNAME www            futureelite.co.uk  600
```

**Verification Commands:**
```bash
dig futureelite.co.uk +short
dig www.futureelite.co.uk +short
curl https://futureelite.co.uk/health
```

**GoDaddy DNS Management:**
- URL: https://www.godaddy.com → My Products → Domains → futureelite.co.uk → DNS

---

## Next Steps After DNS Configuration

1. ✅ DNS records configured in GoDaddy
2. ⏳ Wait 5-15 minutes for propagation
3. ⏳ Deploy your application to the server
4. ⏳ Set up SSL certificate (Let's Encrypt)
5. ⏳ Test: `https://futureelite.co.uk`

**See `DEPLOYMENT_GUIDE.md` for complete deployment instructions.**

---

**DNS Configuration Complete!** ✅

