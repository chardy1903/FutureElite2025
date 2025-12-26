# Quick Deploy Checklist

Follow these steps to deploy FutureElite to production.

---

## Before You Start

- [ ] You have a server (VPS) with root/sudo access
- [ ] You have a domain name pointing to your server (or will set it up)
- [ ] You have SSH access to your server
- [ ] You know your server's IP address

---

## Step 1: Prepare Local Environment (5 minutes)

### 1.1 Generate SECRET_KEY

```bash
cd /Users/chrishardy/Desktop/Library/Software\ Projects/GoalTracker
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Copy the output** - you'll need it.

### 1.2 Create .env File

```bash
cp env.example .env
nano .env  # or open in your editor
```

**Set these values:**
- `SECRET_KEY=<paste-generated-key>`
- `FLASK_ENV=production`
- If using Stripe: Add your Stripe keys

### 1.3 Run Preflight Check

```bash
export $(cat .env | xargs)
python3 scripts/preflight_check.py
```

**Expected:** ✅ All pre-flight checks passed!

---

## Step 2: Prepare Deployment Package (2 minutes)

```bash
./scripts/deploy.sh
```

This will:
- Generate SECRET_KEY if needed
- Run preflight check
- Create deployment package

**Output:** `futureelite-deployment-YYYYMMDD-HHMMSS.tar.gz`

---

## Step 3: Set Up Server (15 minutes)

### 3.1 SSH Into Server

```bash
ssh root@your-server-ip
```

### 3.2 Install Dependencies

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx libmagic1
```

### 3.3 Create Application User

```bash
adduser --disabled-password --gecos "" futureelite
usermod -aG sudo futureelite
```

---

## Step 4: Deploy Application (10 minutes)

### 4.1 Transfer Files

**On your local machine:**
```bash
scp futureelite-deployment-*.tar.gz root@your-server-ip:/tmp/
```

### 4.2 Extract and Set Up

**On server:**
```bash
mkdir -p /opt/futureelite
tar -xzf /tmp/futureelite-deployment-*.tar.gz -C /opt/futureelite
cd /opt/futureelite
chown -R futureelite:futureelite /opt/futureelite
```

### 4.3 Create .env File

```bash
su - futureelite
cd /opt/futureelite
cp env.example .env
nano .env
```

**Set:**
- `SECRET_KEY=<your-generated-key>`
- `FLASK_ENV=production`
- Stripe keys if using

```bash
chmod 600 .env
exit
```

### 4.4 Install Python Dependencies

```bash
su - futureelite
cd /opt/futureelite
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
exit
```

### 4.5 Run Preflight Check

```bash
su - futureelite
cd /opt/futureelite
source venv/bin/activate
export $(cat .env | xargs)
python scripts/preflight_check.py
exit
```

---

## Step 5: Create Systemd Service (5 minutes)

```bash
sudo nano /etc/systemd/system/futureelite.service
```

**Paste:**
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

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
systemctl daemon-reload
systemctl enable futureelite
systemctl start futureelite
systemctl status futureelite
```

---

## Step 6: Configure Nginx (10 minutes)

### 6.1 Create Config

```bash
nano /etc/nginx/sites-available/futureelite
```

**Paste (replace `yourdomain.com`):**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /opt/futureelite/app/static/;
        expires 30d;
    }
}
```

### 6.2 Enable Site

```bash
ln -s /etc/nginx/sites-available/futureelite /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

## Step 7: Set Up SSL (5 minutes)

```bash
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**Follow prompts** - certbot will update nginx config automatically.

---

## Step 8: Configure DNS (5 minutes)

**For GoDaddy (futureelite.co.uk):**
- See `GODADDY_DNS_SETUP.md` for detailed GoDaddy instructions

**Quick setup:**
1. Log in to GoDaddy: https://www.godaddy.com
2. Go to: My Products → Domains → futureelite.co.uk → DNS
3. Add A record:
   - Type: `A`
   - Name: `@` (or leave blank)
   - Value: `YOUR_SERVER_IP`
   - TTL: `600`
4. Add CNAME record:
   - Type: `CNAME`
   - Name: `www`
   - Value: `futureelite.co.uk`
   - TTL: `600`

**Wait 5-15 minutes for DNS propagation.**

---

## Step 9: Verify Deployment (5 minutes)

### 9.1 Check Service

```bash
systemctl status futureelite
```

### 9.2 Test Health Endpoint

```bash
curl http://localhost:8080/health
curl https://yourdomain.com/health
```

**Expected:** `{"status":"healthy","service":"FutureElite"}`

### 9.3 Test in Browser

Visit: `https://yourdomain.com`

---

## Step 10: Set Up Backups (5 minutes)

```bash
nano /opt/futureelite/backup.sh
```

**Paste:**
```bash
#!/bin/bash
BACKUP_DIR="/backups/futureelite"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/data-$DATE.tar.gz" -C /opt/futureelite data/
find "$BACKUP_DIR" -name "data-*.tar.gz" -mtime +30 -delete
```

```bash
chmod +x /opt/futureelite/backup.sh
crontab -e
```

**Add:**
```
0 2 * * * /opt/futureelite/backup.sh
```

---

## ✅ Deployment Complete!

**Quick Commands:**
```bash
# Start/Stop
systemctl start futureelite
systemctl stop futureelite
systemctl restart futureelite
systemctl status futureelite

# View logs
journalctl -u futureelite -f

# Check health
curl https://yourdomain.com/health
```

---

## Need Help?

- See `DEPLOYMENT_GUIDE.md` for detailed instructions
- See `PRODUCTION_DEPLOYMENT_RUNBOOK.md` for troubleshooting
- Check logs: `journalctl -u futureelite -n 50`

