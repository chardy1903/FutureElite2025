# Step-by-Step Deployment Guide

This guide walks you through deploying FutureElite to production.

---

## Step 1: Choose Your Deployment Platform

**Options:**
- **VPS (DigitalOcean, Linode, Vultr, etc.)** - Full control, recommended
- **Cloud Platform (AWS, GCP, Azure)** - Scalable, more complex
- **Platform-as-a-Service (Heroku, Railway, Render)** - Easiest, less control

**This guide assumes a VPS (most common). Adapt as needed for other platforms.**

---

## Step 2: Prepare Your Server

### 2.1 Server Requirements
- Ubuntu 20.04+ or Debian 11+ (recommended)
- At least 1GB RAM, 1 CPU core
- Python 3.8+
- Root or sudo access

### 2.2 Initial Server Setup

```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Python and dependencies
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx

# Install system dependencies for python-magic (if using)
apt install -y libmagic1

# Create application user
adduser --disabled-password --gecos "" futureelite
usermod -aG sudo futureelite
```

---

## Step 3: Deploy Application Code

### 3.1 Transfer Code to Server

**Option A: Using Git (Recommended)**
```bash
# On server
su - futureelite
cd ~
git clone <your-repository-url> GoalTracker
cd GoalTracker
```

**Option B: Using SCP**
```bash
# On your local machine
cd /Users/chrishardy/Desktop/Library/Software\ Projects/GoalTracker
tar -czf deployment.tar.gz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='venv' .
scp deployment.tar.gz futureelite@your-server-ip:~/
```

```bash
# On server
ssh futureelite@your-server-ip
tar -xzf deployment.tar.gz -C GoalTracker
cd GoalTracker
```

### 3.2 Set Up Application Directory

```bash
# On server
sudo mkdir -p /opt/futureelite
sudo chown futureelite:futureelite /opt/futureelite
mv ~/GoalTracker/* /opt/futureelite/
cd /opt/futureelite
```

---

## Step 4: Configure Environment Variables

### 4.1 Generate SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Copy the output** - you'll need it in the next step.

### 4.2 Create .env File

```bash
cd /opt/futureelite
cp env.example .env
nano .env  # or use vim, emacs, etc.
```

**Edit `.env` and set:**
```bash
SECRET_KEY=<paste-the-generated-key-here>
FLASK_ENV=production

# If using Stripe:
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_MONTHLY_PRICE_ID=price_...
STRIPE_ANNUAL_PRICE_ID=price_...
```

**Save and exit** (Ctrl+X, then Y, then Enter in nano)

### 4.3 Secure the .env File

```bash
chmod 600 .env
```

---

## Step 5: Install Dependencies

### 5.1 Create Virtual Environment

```bash
cd /opt/futureelite
python3 -m venv venv
source venv/bin/activate
```

### 5.2 Install Python Packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 6: Run Preflight Check

```bash
# Load environment variables
export $(cat .env | xargs)

# Run validation
python scripts/preflight_check.py
```

**Expected output:** `✅ All pre-flight checks passed!`

If it fails, fix the issues before proceeding.

---

## Step 7: Set Up Data Directory

```bash
cd /opt/futureelite
mkdir -p data/photos
chmod 755 data data/photos
```

---

## Step 8: Test Application Startup

```bash
cd /opt/futureelite
source venv/bin/activate
export $(cat .env | xargs)

# Test startup (will run in foreground)
gunicorn -c gunicorn.conf.py wsgi:app
```

**Expected:** You should see "FutureElite server is ready. Accepting connections."

**Press Ctrl+C to stop** after verifying it starts.

---

## Step 9: Create Systemd Service

### 9.1 Create Service File

```bash
sudo nano /etc/systemd/system/futureelite.service
```

**Paste this content:**

```ini
[Unit]
Description=FutureElite Application
After=network.target

[Service]
Type=notify
User=futureelite
Group=futureelite
WorkingDirectory=/opt/futureelite
EnvironmentFile=/opt/futureelite/.env
ExecStart=/opt/futureelite/venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Save and exit.**

### 9.2 Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable futureelite
sudo systemctl start futureelite
sudo systemctl status futureelite
```

**Expected:** Service should be "active (running)"

---

## Step 10: Configure Nginx Reverse Proxy

### 10.1 Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/futureelite
```

**Paste this (using `futureelite.co.uk`):**

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name futureelite.co.uk www.futureelite.co.uk;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all other HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name futureelite.co.uk www.futureelite.co.uk;

    # SSL Configuration (will be updated by certbot)
    ssl_certificate /etc/letsencrypt/live/futureelite.co.uk/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/futureelite.co.uk/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    # Logging
    access_log /var/log/nginx/futureelite-access.log;
    error_log /var/log/nginx/futureelite-error.log;

    # Client body size (must be >= Flask MAX_CONTENT_LENGTH)
    client_max_body_size 16M;

    # Proxy settings
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_redirect off;
    proxy_buffering off;

    # Static files
    location /static/ {
        alias /opt/futureelite/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8080;
        access_log off;
    }

    # Application
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

**Save and exit.**

### 10.2 Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/futureelite /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
```

**If test passes:**
```bash
sudo systemctl reload nginx
```

---

## Step 11: Set Up SSL Certificate (Let's Encrypt)

### 11.1 Get Certificate

```bash
sudo certbot --nginx -d futureelite.co.uk -d www.futureelite.co.uk
```

**Follow the prompts:**
- Enter your email
- Agree to terms
- Choose whether to redirect HTTP to HTTPS (recommended: Yes)

### 11.2 Auto-Renewal

Certbot sets up auto-renewal automatically. Test it:

```bash
sudo certbot renew --dry-run
```

---

## Step 12: Configure DNS

### 12.1 DNS Records for futureelite.co.uk (GoDaddy)

**For GoDaddy users, see `GODADDY_DNS_SETUP.md` for detailed instructions.**

**Quick setup:**
1. Log in to GoDaddy: https://www.godaddy.com
2. Navigate to: My Products → Domains → futureelite.co.uk → DNS
3. Add A record:
   - Type: `A`
   - Name: `@` (or leave blank)
   - Value: `<your-server-ip>`
   - TTL: `600`
4. Add CNAME record:
   - Type: `CNAME`
   - Name: `www`
   - Value: `futureelite.co.uk`
   - TTL: `600`

**Expected DNS Records:**
```
A     @              YOUR_SERVER_IP     600
CNAME www            futureelite.co.uk  600
```

### 12.2 Verify DNS

```bash
# Wait 5-15 minutes for propagation, then check
dig futureelite.co.uk +short
dig www.futureelite.co.uk +short
nslookup futureelite.co.uk

# Online checker
# Visit: https://www.whatsmydns.net/#A/futureelite.co.uk
```

---

## Step 13: Final Verification

### 13.1 Check Service Status

```bash
sudo systemctl status futureelite
```

### 13.2 Test Health Endpoint

```bash
curl http://localhost:8080/health
```

**Expected:** `{"status":"healthy","service":"FutureElite"}`

### 13.3 Test via Domain

```bash
curl https://futureelite.co.uk/health
```

**Expected:** `{"status":"healthy","service":"FutureElite"}`

### 13.4 Test HTTPS Redirect

```bash
curl -I http://futureelite.co.uk/
```

**Expected:** `301 Moved Permanently` with `Location: https://futureelite.co.uk/`

### 13.5 Open in Browser

Visit `https://futureelite.co.uk` in your browser. You should see the application.

---

## Step 14: Set Up Logging (Optional but Recommended)

### 14.1 Create Log Directory

```bash
sudo mkdir -p /var/log/futureelite
sudo chown futureelite:futureelite /var/log/futureelite
```

### 14.2 Update .env

```bash
nano /opt/futureelite/.env
```

Add:
```bash
GUNICORN_ACCESS_LOG=/var/log/futureelite/access.log
GUNICORN_ERROR_LOG=/var/log/futureelite/error.log
```

### 14.3 Restart Service

```bash
sudo systemctl restart futureelite
```

### 14.4 Set Up Log Rotation

```bash
sudo nano /etc/logrotate.d/futureelite
```

Paste:
```
/var/log/futureelite/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    sharedscripts
    postrotate
        systemctl reload futureelite > /dev/null 2>&1 || true
    endscript
}
```

---

## Step 15: Set Up Backups (Critical!)

### 15.1 Create Backup Script

```bash
nano /opt/futureelite/backup.sh
```

Paste:
```bash
#!/bin/bash
BACKUP_DIR="/backups/futureelite"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/data-$DATE.tar.gz" -C /opt/futureelite data/
# Keep last 30 days
find "$BACKUP_DIR" -name "data-*.tar.gz" -mtime +30 -delete
```

```bash
chmod +x /opt/futureelite/backup.sh
```

### 15.2 Set Up Cron Job

```bash
crontab -e
```

Add:
```
0 2 * * * /opt/futureelite/backup.sh
```

This runs daily at 2 AM.

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u futureelite -n 50
tail -f /var/log/futureelite/error.log

# Check environment variables
sudo -u futureelite bash -c 'cd /opt/futureelite && source venv/bin/activate && export $(cat .env | xargs) && python scripts/preflight_check.py'
```

### 502 Bad Gateway

- Check if service is running: `sudo systemctl status futureelite`
- Check nginx error log: `sudo tail -f /var/log/nginx/error.log`
- Verify port 8080 is listening: `sudo netstat -tlnp | grep 8080`

### SSL Certificate Issues

```bash
# Check certificate
sudo certbot certificates

# Renew manually
sudo certbot renew
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R futureelite:futureelite /opt/futureelite
sudo chmod 600 /opt/futureelite/.env
```

---

## Quick Reference Commands

```bash
# Start/Stop/Restart
sudo systemctl start futureelite
sudo systemctl stop futureelite
sudo systemctl restart futureelite
sudo systemctl status futureelite

# View logs
sudo journalctl -u futureelite -f
tail -f /var/log/futureelite/error.log

# Reload nginx
sudo nginx -t && sudo systemctl reload nginx

# Check health
curl https://yourdomain.com/health
```

---

## Next Steps

1. ✅ Application is deployed and running
2. ✅ SSL certificate is active
3. ✅ DNS is configured
4. ⚠️ **Test all features** (login, registration, data entry, etc.)
5. ⚠️ **Set up monitoring** (UptimeRobot, Pingdom, etc.)
6. ⚠️ **Review security** (firewall, SSH keys, etc.)

---

**Deployment Complete!** 🎉

