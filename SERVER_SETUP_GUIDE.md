# Server Setup Guide for FutureElite

This guide helps you choose and set up a VPS (Virtual Private Server) for deploying FutureElite.

---

## Quick Recommendation

**Best for beginners:** **DigitalOcean** ($6/month)
- Easy to use
- Great documentation
- Reliable
- Simple interface

**Alternative options:**
- **Linode** ($5/month) - Similar to DigitalOcean
- **Vultr** ($6/month) - Good performance
- **Hetzner** (€4.15/month) - Great value (Europe)

---

## Option 1: DigitalOcean (Recommended)

### Step 1: Create Account

1. Go to: https://www.digitalocean.com
2. Click "Sign Up"
3. Create account (email verification required)
4. Add payment method (credit card or PayPal)

### Step 2: Create Droplet (Server)

1. **Click "Create" → "Droplets"**

2. **Choose configuration:**
   - **Image:** Ubuntu 22.04 (LTS) x64
   - **Plan:** Basic
   - **CPU:** Regular (1 vCPU)
   - **Memory:** 1 GB / 25 GB Disk ($6/month)
   - **Datacenter region:** Choose closest to you (London, Amsterdam, etc.)
   - **Authentication:** 
     - **Recommended:** SSH keys (more secure)
     - **Alternative:** Root password (easier for beginners)

3. **Finalize:**
   - **Hostname:** `futureelite` (optional)
   - Click "Create Droplet"

4. **Wait 1-2 minutes** for droplet to be created

### Step 3: Get Your Server IP

1. Once created, you'll see your droplet in the dashboard
2. **Copy the IP address** (e.g., `192.0.2.100`)
3. **Write it down** - you'll need it for:
   - SSH access
   - DNS configuration in GoDaddy

### Step 4: Connect to Your Server

**On macOS/Linux:**
```bash
ssh root@YOUR_SERVER_IP
```

**On Windows:**
- Use PuTTY or Windows Terminal
- Host: `YOUR_SERVER_IP`
- Port: `22`
- User: `root`

**First connection:** Type "yes" when asked to accept the fingerprint

---

## Option 2: Linode

### Step 1: Create Account

1. Go to: https://www.linode.com
2. Click "Sign Up"
3. Create account and verify email
4. Add payment method

### Step 2: Create Linode

1. **Click "Create" → "Linode"**

2. **Choose configuration:**
   - **Image:** Ubuntu 22.04 LTS
   - **Region:** Choose closest to you
   - **Plan:** Shared CPU - Nanode 1 GB ($5/month)
   - **Root Password:** Set a strong password
   - **SSH Keys:** Optional (recommended)

3. **Click "Create Linode"**

4. **Wait 2-3 minutes** for Linode to boot

### Step 3: Get IP Address

1. In Linode dashboard, click on your Linode
2. **Copy the IPv4 address**
3. **Write it down**

### Step 4: Connect

```bash
ssh root@YOUR_LINODE_IP
```

---

## Option 3: Vultr

### Step 1: Create Account

1. Go to: https://www.vultr.com
2. Click "Sign Up"
3. Create account and verify email
4. Add payment method

### Step 2: Deploy Server

1. **Click "Deploy Server"**

2. **Choose configuration:**
   - **Server:** Cloud Compute
   - **Location:** Choose closest region
   - **OS:** Ubuntu 22.04 LTS
   - **Plan:** Regular Performance - $6/month (1 vCPU, 1GB RAM)
   - **SSH Keys:** Optional (recommended)
   - **Server Hostname:** `futureelite` (optional)

3. **Click "Deploy Now"**

4. **Wait 1-2 minutes**

### Step 3: Get IP Address

1. In dashboard, find your server
2. **Copy the IP address**
3. **Write it down**

### Step 4: Connect

```bash
ssh root@YOUR_VULTR_IP
```

---

## After Server Creation: Initial Setup

**Once you've created your server and have the IP address:**

### 1. Connect to Server

```bash
ssh root@YOUR_SERVER_IP
```

### 2. Update System

```bash
apt update && apt upgrade -y
```

### 3. Install Basic Tools

```bash
apt install -y curl wget git ufw
```

### 4. Set Up Firewall (Security)

```bash
# Allow SSH
ufw allow 22/tcp

# Allow HTTP and HTTPS (for web server)
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw --force enable

# Check status
ufw status
```

### 5. Verify Server IP

```bash
# Get your server's public IP
curl ifconfig.me
```

**This should match the IP from your provider's dashboard.**

---

## Server Requirements Summary

**Minimum requirements:**
- **CPU:** 1 vCPU
- **RAM:** 1 GB
- **Storage:** 25 GB
- **OS:** Ubuntu 22.04 LTS (recommended)
- **Cost:** $5-6/month

**Recommended for production:**
- **CPU:** 2 vCPU
- **RAM:** 2 GB
- **Storage:** 40 GB
- **Cost:** $12-15/month

**For your app:** The $6/month plan (1GB RAM) is sufficient to start.

---

## Cost Comparison

| Provider | Plan | Price/Month | RAM | Storage |
|----------|------|-------------|-----|---------|
| DigitalOcean | Basic | $6 | 1 GB | 25 GB |
| Linode | Nanode | $5 | 1 GB | 25 GB |
| Vultr | Regular | $6 | 1 GB | 25 GB |
| Hetzner | CX11 | €4.15 (~$4.50) | 2 GB | 20 GB |

**Note:** All prices are approximate and may vary. Check current pricing on provider websites.

---

## Next Steps After Server Setup

1. ✅ Server created and IP address obtained
2. ⏳ Configure DNS in GoDaddy (point `futureelite.co.uk` to server IP)
3. ⏳ Deploy application (follow `QUICK_DEPLOY_CHECKLIST.md`)
4. ⏳ Set up SSL certificate
5. ⏳ Test: `https://futureelite.co.uk`

---

## Troubleshooting

### Can't Connect via SSH

**Problem:** Connection refused or timeout

**Solutions:**
1. **Check IP address** - Make sure you're using the correct IP
2. **Check firewall** - Provider may have a firewall - check their dashboard
3. **Wait longer** - Server may still be booting (wait 2-3 minutes)
4. **Check SSH port** - Should be port 22

### Forgot Root Password

**DigitalOcean:**
- Go to droplet → Access → Reset Root Password

**Linode:**
- Go to Linode → Settings → Reset Root Password

**Vultr:**
- Go to server → Settings → Reset Root Password

### Server Not Responding

1. **Check provider dashboard** - Is server running?
2. **Reboot server** - Use provider's dashboard
3. **Check logs** - Provider dashboard usually has console/logs

---

## Security Best Practices

### 1. Use SSH Keys (Recommended)

**Generate SSH key on your Mac:**
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter to accept default location
# Set a passphrase (optional but recommended)
```

**Add to server:**
- DigitalOcean: Settings → Security → SSH Keys → Add SSH Key
- Linode: Account → SSH Keys → Add SSH Key
- Vultr: Settings → SSH Keys → Add SSH Key

**Then connect without password:**
```bash
ssh root@YOUR_SERVER_IP
```

### 2. Disable Root Login (After Setup)

**After deploying your app, create a non-root user:**
```bash
adduser futureelite
usermod -aG sudo futureelite
# Then use this user instead of root
```

### 3. Keep System Updated

```bash
# Run regularly
apt update && apt upgrade -y
```

---

## Quick Start Commands

**After connecting to your server:**

```bash
# 1. Update system
apt update && apt upgrade -y

# 2. Install required packages
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx libmagic1

# 3. Set up firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 4. Verify IP
curl ifconfig.me
```

**Then proceed with deployment following `QUICK_DEPLOY_CHECKLIST.md`**

---

## Recommendation

**For your first deployment, I recommend DigitalOcean:**
- ✅ Easiest interface
- ✅ Great documentation
- ✅ Reliable
- ✅ Good support
- ✅ $6/month is affordable

**Sign up here:** https://www.digitalocean.com

---

**Once you have your server IP, proceed to:**
1. Configure DNS in GoDaddy (`GODADDY_DNS_SETUP.md`)
2. Deploy application (`QUICK_DEPLOY_CHECKLIST.md`)


