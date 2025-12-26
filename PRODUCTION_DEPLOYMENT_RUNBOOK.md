# FutureElite Production Deployment Runbook

**Version:** 1.0  
**Last Updated:** 2025-01-XX  
**Application:** FutureElite - Youth Football Match Tracker

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Installation](#installation)
4. [Pre-Deployment Validation](#pre-deployment-validation)
5. [Starting the Application](#starting-the-application)
6. [Reverse Proxy Configuration](#reverse-proxy-configuration)
7. [Health Checks](#health-checks)
8. [Database/Data Initialization](#database-data-initialization)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- Python 3.8 or higher
- pip (Python package manager)
- Systemd or process manager (for service management)
- Reverse proxy (nginx, Apache, or cloud load balancer) for HTTPS termination
- SSL/TLS certificate for custom domain

### Required Python Packages
All dependencies are listed in `requirements.txt`. Install with:
```bash
pip install -r requirements.txt
```

### Required System Packages (if using python-magic)
```bash
# Ubuntu/Debian
sudo apt-get install libmagic1

# macOS
brew install libmagic

# CentOS/RHEL
sudo yum install file-devel
```

---

## Environment Variables

### Required Variables (Application will not start without these)

| Variable | Description | Example | Mandatory |
|----------|-------------|---------|-----------|
| `SECRET_KEY` | Flask secret key (min 32 chars) | `a1b2c3d4e5f6...` (64 hex chars) | ✅ **YES** |
| `FLASK_ENV` | Application environment | `production` | ✅ **YES** |

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Required if Using Stripe

| Variable | Description | Example | Mandatory |
|----------|-------------|---------|-----------|
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | `whsec_...` | ✅ **YES** (if Stripe enabled) |
| `STRIPE_SECRET_KEY` | Stripe API secret key | `sk_live_...` | ✅ **YES** (if Stripe enabled) |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | `pk_live_...` | ✅ **YES** (if Stripe enabled) |
| `STRIPE_MONTHLY_PRICE_ID` | Monthly subscription price ID | `price_...` | ⚠️ **If using subscriptions** |
| `STRIPE_ANNUAL_PRICE_ID` | Annual subscription price ID | `price_...` | ⚠️ **If using subscriptions** |

### Optional Variables

| Variable | Description | Default | Recommended |
|----------|-------------|---------|-------------|
| `PROXY_FIX_NUM_PROXIES` | Number of proxies in front | `1` | Set to `2` if behind load balancer + nginx |
| `GUNICORN_BIND` | Gunicorn bind address | `0.0.0.0:8080` | Keep default unless port conflict |
| `GUNICORN_WORKERS` | Number of worker processes | `CPU * 2 + 1` | Adjust based on load |
| `GUNICORN_ACCESS_LOG` | Access log path | `-` (stdout) | `/var/log/futureelite/access.log` |
| `GUNICORN_ERROR_LOG` | Error log path | `-` (stderr) | `/var/log/futureelite/error.log` |
| `GUNICORN_LOG_LEVEL` | Log level | `info` | `info` or `warning` |
| `GUNICORN_PIDFILE` | PID file location | None | `/var/run/futureelite.pid` |
| `GUNICORN_USER` | Run as user | None | `www-data` or `nginx` |
| `GUNICORN_GROUP` | Run as group | None | `www-data` or `nginx` |

### Environment File Setup

1. Copy the example file:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` and fill in all required values:
   ```bash
   nano .env  # or vim, emacs, etc.
   ```

3. **NEVER commit `.env` to version control** (it should be in `.gitignore`)

---

## Installation

### 1. Clone/Deploy Code
```bash
# If using git
git clone <repository-url>
cd GoalTracker

# Or extract deployment package
tar -xzf futureelite-deployment.tar.gz
cd GoalTracker
```

### 2. Create Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Set Up Data Directory
```bash
# Ensure data directory exists with proper permissions
mkdir -p data/photos
chmod 755 data
chmod 755 data/photos
```

---

## Pre-Deployment Validation

**Always run the preflight check before deploying:**

```bash
# Load environment variables
export $(cat .env | xargs)

# Run preflight check
python scripts/preflight_check.py
```

Expected output:
```
============================================================
FutureElite Pre-Flight Check
============================================================

Checking required environment variables...
✅ SECRET_KEY: Set (length: 64)
✅ FLASK_ENV: production (production mode)

Checking Stripe configuration...
✅ STRIPE_WEBHOOK_SECRET: Set
✅ STRIPE_SECRET_KEY: Set
...

Checking application initialization...
✅ Application imports and initializes successfully

============================================================
✅ All pre-flight checks passed!
   Application is ready for production deployment.
```

**If any check fails, fix the issue before proceeding.**

---

## Starting the Application

### Production Start Command

**DO NOT use `python run.py` in production** - it will refuse to start.

Use Gunicorn instead:

```bash
# Basic start
gunicorn -c gunicorn.conf.py wsgi:app

# Or with explicit config
gunicorn --config gunicorn.conf.py wsgi:app

# Or using environment variables
export $(cat .env | xargs)
gunicorn wsgi:app
```

### Systemd Service (Recommended)

Create `/etc/systemd/system/futureelite.service`:

```ini
[Unit]
Description=FutureElite Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/futureelite
EnvironmentFile=/opt/futureelite/.env
ExecStart=/opt/futureelite/venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable futureelite
sudo systemctl start futureelite
sudo systemctl status futureelite
```

### Supervisor (Alternative)

Create `/etc/supervisor/conf.d/futureelite.conf`:

```ini
[program:futureelite]
command=/opt/futureelite/venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
directory=/opt/futureelite
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/futureelite/supervisor.log
environment=FLASK_ENV="production"
```

---

## Reverse Proxy Configuration

### Nginx Configuration

The application should run behind nginx (or similar) for HTTPS termination and static file serving.

**Example `/etc/nginx/sites-available/futureelite`:**

```nginx
# Upstream backend
upstream futureelite {
    server 127.0.0.1:8080;
    keepalive 32;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers (Flask-Talisman handles most, but add these for extra safety)
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

    # Static files (if serving from nginx)
    location /static/ {
        alias /opt/futureelite/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Application
    location / {
        proxy_pass http://futureelite;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://futureelite;
        access_log off;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/futureelite /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Apache Configuration (Alternative)

**Example `/etc/apache2/sites-available/futureelite.conf`:**

```apache
<VirtualHost *:443>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com

    SSLEngine on
    SSLCertificateFile /path/to/cert.pem
    SSLCertificateKeyFile /path/to/key.pem

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8080/
    ProxyPassReverse / http://127.0.0.1:8080/

    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Port "443"
</VirtualHost>
```

### ProxyFix Configuration

The application automatically handles reverse proxy headers via `werkzeug.middleware.proxy_fix.ProxyFix`.

**Set in `.env`:**
```bash
# Single reverse proxy (nginx/Apache)
PROXY_FIX_NUM_PROXIES=1

# Load balancer + reverse proxy
PROXY_FIX_NUM_PROXIES=2
```

---

## Health Checks

### Health Endpoint

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "FutureElite"
}
```

**Status Code:** `200 OK`

### Health Check Usage

**Load Balancer Health Check:**
```bash
curl -f https://yourdomain.com/health || exit 1
```

**Monitoring Script:**
```bash
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" https://yourdomain.com/health)
if [ "$response" != "200" ]; then
    echo "Health check failed: $response"
    exit 1
fi
```

**Systemd Health Check (optional):**
Add to service file:
```ini
ExecStartPost=/bin/bash -c 'until curl -f http://127.0.0.1:8080/health; do sleep 1; done'
```

---

## Database/Data Initialization

### Data Storage

This application uses JSON files for data storage (no database migrations required).

**Data Directory Structure:**
```
data/
├── users.json          # User accounts
├── matches.json        # Match records
├── settings.json       # Application settings
├── subscriptions.json  # Subscription data
├── achievements.json   # Achievement records
├── club_history.json  # Club history
├── physical_measurements.json
├── physical_metrics.json
├── references.json
├── training_camps.json
└── photos/            # Uploaded photos
```

### Initial Setup

1. **Ensure data directory exists:**
   ```bash
   mkdir -p data/photos
   chmod 755 data
   chmod 755 data/photos
   ```

2. **Set proper ownership:**
   ```bash
   chown -R www-data:www-data data/
   ```

3. **Create initial admin user (if needed):**
   - Use the registration endpoint: `POST /register`
   - Or manually create entry in `data/users.json` (password must be hashed with werkzeug)

### Backup Strategy

**Recommended backup schedule:**
```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/futureelite"
DATE=$(date +%Y%m%d)
tar -czf "$BACKUP_DIR/data-$DATE.tar.gz" data/
# Keep last 30 days
find "$BACKUP_DIR" -name "data-*.tar.gz" -mtime +30 -delete
```

---

## Monitoring and Logging

### Application Logs

**Gunicorn Logs:**
- Access log: Set via `GUNICORN_ACCESS_LOG` (default: stdout)
- Error log: Set via `GUNICORN_ERROR_LOG` (default: stderr)

**Recommended log locations:**
```bash
/var/log/futureelite/access.log
/var/log/futureelite/error.log
```

**Log Rotation:**
Create `/etc/logrotate.d/futureelite`:
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

### Monitoring Metrics

**Key metrics to monitor:**
- HTTP response codes (200, 4xx, 5xx)
- Response times
- Worker process health
- Disk space (data directory)
- Memory usage

**Example monitoring script:**
```bash
#!/bin/bash
# Check application health
curl -f https://yourdomain.com/health || alert "Health check failed"

# Check disk space
df -h /opt/futureelite/data | awk 'NR==2 {if ($5 > 80) exit 1}'

# Check process
systemctl is-active --quiet futureelite || alert "Service not running"
```

---

## Troubleshooting

### Application Won't Start

**Check 1: Environment Variables**
```bash
python scripts/preflight_check.py
```

**Check 2: Port Already in Use**
```bash
sudo lsof -i :8080
# Kill process or change GUNICORN_BIND
```

**Check 3: Permissions**
```bash
ls -la data/
# Ensure www-data (or service user) can read/write
```

### 500 Errors

**Check logs:**
```bash
tail -f /var/log/futureelite/error.log
journalctl -u futureelite -f
```

**Common causes:**
- Missing environment variables
- File permission issues
- Disk space full
- Invalid JSON in data files

### CSRF Token Errors

**Symptoms:** `400 Bad Request: The CSRF token is missing.`

**Solutions:**
1. Ensure frontend includes CSRF token in requests
2. Check that `X-CSRF-Token` header is sent
3. Verify session cookies are being set (check browser dev tools)

### Rate Limiting Issues

**Symptoms:** `429 Too Many Requests`

**Solutions:**
1. Wait for rate limit window to reset
2. Adjust rate limits in `app/main.py` if needed
3. Consider using Redis for distributed rate limiting

### Stripe Webhook Failures

**Check webhook secret:**
```bash
echo $STRIPE_WEBHOOK_SECRET
# Should start with whsec_
```

**Verify webhook endpoint:**
- Stripe Dashboard -> Webhooks -> Endpoint URL
- Must match your domain: `https://yourdomain.com/api/subscription/webhook`

**Test webhook:**
```bash
# Use Stripe CLI for local testing
stripe listen --forward-to https://yourdomain.com/api/subscription/webhook
```

---

## Quick Reference

### Start Application
```bash
gunicorn -c gunicorn.conf.py wsgi:app
```

### Stop Application
```bash
# If using systemd
sudo systemctl stop futureelite

# If running directly
pkill -f "gunicorn.*wsgi:app"
```

### Restart Application
```bash
sudo systemctl restart futureelite
```

### Check Status
```bash
sudo systemctl status futureelite
curl https://yourdomain.com/health
```

### View Logs
```bash
journalctl -u futureelite -f
tail -f /var/log/futureelite/error.log
```

---

**End of Runbook**

