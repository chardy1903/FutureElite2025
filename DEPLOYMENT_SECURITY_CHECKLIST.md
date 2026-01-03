# Deployment Security Checklist

Use this checklist before deploying to production to ensure all security measures are in place.

---

## Pre-Deployment Verification

### ✅ Environment Variables

- [ ] **`.env` file is NOT in deployment directory**
  - Verify: `ls -la | grep .env` should return nothing
  - Check: `.env` is in `.gitignore`
  - Action: Use environment variables from hosting platform, not `.env` file

- [ ] **All required secrets are set in hosting platform**
  - [ ] `SECRET_KEY` (minimum 32 characters)
  - [ ] `STRIPE_SECRET_KEY` (if using Stripe)
  - [ ] `STRIPE_WEBHOOK_SECRET` (if using Stripe)
  - [ ] `ADMIN_USERNAME` (recommended)
  - [ ] `SMTP_*` variables (if using email)

- [ ] **No secrets in code or configuration files**
  - [ ] No hardcoded API keys
  - [ ] No hardcoded passwords
  - [ ] No secrets in comments

### ✅ File System Security

- [ ] **No sensitive files in deployment**
  - [ ] No `.env` files
  - [ ] No `.env.bak`, `.env.save`, `.env.backup` files
  - [ ] No `.git/` directory
  - [ ] No `__pycache__/` directories (or they're excluded from web root)
  - [ ] No `node_modules/` in web root
  - [ ] No backup SQL files
  - [ ] No configuration files with secrets

- [ ] **Build artifacts excluded**
  - [ ] `__pycache__/` not accessible via HTTP
  - [ ] `*.pyc` files not accessible
  - [ ] Source maps (`.map`) not in production (optional)

### ✅ Application Configuration

- [ ] **Debug mode disabled**
  - [ ] `FLASK_ENV=production`
  - [ ] `FLASK_DEBUG` not set or set to `False`
  - [ ] `TEMPLATES_AUTO_RELOAD=False` in production

- [ ] **Security features enabled**
  - [ ] CSRF protection enabled
  - [ ] Rate limiting enabled
  - [ ] Security headers enabled (Flask-Talisman)
  - [ ] Session cookies secure (Secure=True in production)

- [ ] **Admin protection**
  - [ ] `ADMIN_USERNAME` set (recommended)
  - [ ] Admin routes require authentication
  - [ ] Admin IP allowlisting configured (optional)

### ✅ Web Server Configuration

- [ ] **Nginx/Web server security rules applied**
  - [ ] `.env*` files blocked
  - [ ] `.git*` blocked
  - [ ] Backup files blocked
  - [ ] Build artifacts blocked
  - [ ] Configuration files blocked

- [ ] **Rate limiting configured**
  - [ ] 404 rate limiting enabled
  - [ ] Admin path rate limiting enabled
  - [ ] Login rate limiting enabled

- [ ] **Security headers set**
  - [ ] `X-Frame-Options`
  - [ ] `X-Content-Type-Options`
  - [ ] `X-XSS-Protection`
  - [ ] `Strict-Transport-Security` (if using HTTPS)
  - [ ] `Content-Security-Policy`

### ✅ CDN/WAF Configuration (Cloudflare)

- [ ] **WAF rules deployed**
  - [ ] `.env` file blocking rule
  - [ ] Git metadata blocking rule
  - [ ] Backup file blocking rule
  - [ ] Configuration file blocking rule
  - [ ] Build artifact blocking rule

- [ ] **Rate limiting rules configured**
  - [ ] 404 rate limiting (reconnaissance detection)
  - [ ] Admin path rate limiting
  - [ ] Login rate limiting

- [ ] **Security settings enabled**
  - [ ] SSL/TLS mode: Full (strict)
  - [ ] Always Use HTTPS: Enabled
  - [ ] Automatic HTTPS Rewrites: Enabled
  - [ ] Minimum TLS Version: 1.2 (or higher)

### ✅ Database and Storage

- [ ] **Database files not accessible**
  - [ ] No `.sql`, `.db`, `.sqlite` files in web root
  - [ ] Database connection uses environment variables
  - [ ] Database credentials not in code

- [ ] **File uploads secured**
  - [ ] File type validation
  - [ ] File size limits
  - [ ] Upload directory outside web root (if possible)
  - [ ] Filename sanitization

### ✅ Logging and Monitoring

- [ ] **Security logging enabled**
  - [ ] Failed login attempts logged
  - [ ] Blocked requests logged
  - [ ] Admin access logged
  - [ ] Suspicious activity logged

- [ ] **Monitoring configured**
  - [ ] Error tracking (Sentry, etc.)
  - [ ] Uptime monitoring
  - [ ] Security alerting (if available)

---

## Post-Deployment Verification

### ✅ Functional Testing

- [ ] **Legitimate requests work**
  - [ ] Homepage loads
  - [ ] Login works
  - [ ] Registration works
  - [ ] Authenticated pages work
  - [ ] API endpoints work

- [ ] **Security blocks work**
  - [ ] `.env` access returns 404
  - [ ] `.git/HEAD` access returns 404
  - [ ] `wp-config.php` access returns 404
  - [ ] Backup files return 404

### ✅ Security Testing

- [ ] **Test blocked paths** (should all return 404):
  ```bash
  curl -I https://yourdomain.com/.env
  curl -I https://yourdomain.com/.env.bak
  curl -I https://yourdomain.com/.git/HEAD
  curl -I https://yourdomain.com/wp-config.php
  curl -I https://yourdomain.com/config.php.bak
  ```

- [ ] **Test rate limiting**
  - [ ] Make 15+ 404 requests quickly → should trigger rate limit
  - [ ] Make 10+ login attempts quickly → should trigger rate limit

- [ ] **Test security headers**
  ```bash
  curl -I https://yourdomain.com | grep -i "x-frame-options\|x-content-type-options\|strict-transport-security"
  ```

### ✅ Monitoring

- [ ] **Check logs for blocked requests**
  - [ ] Review web server logs
  - [ ] Review application logs
  - [ ] Review Cloudflare WAF logs (if using)

- [ ] **Verify no false positives**
  - [ ] Legitimate users can access site
  - [ ] No legitimate requests blocked
  - [ ] Admin access works (if configured)

---

## Ongoing Maintenance

### Weekly

- [ ] Review security logs
- [ ] Check for new attack patterns
- [ ] Review rate limit violations
- [ ] Check for failed login attempts

### Monthly

- [ ] Review and update WAF rules
- [ ] Rotate secrets (if policy requires)
- [ ] Review blocked IPs
- [ ] Update dependencies (security patches)

### Quarterly

- [ ] Full security audit
- [ ] Review and update security configurations
- [ ] Test incident response procedures
- [ ] Review access logs for anomalies

---

## Incident Response

If you detect a security incident:

1. **Immediate Actions**
   - [ ] Block offending IPs
   - [ ] Review logs for scope
   - [ ] Check if any data was accessed
   - [ ] Rotate affected secrets

2. **Investigation**
   - [ ] Review access logs
   - [ ] Check for data exfiltration
   - [ ] Identify attack vector
   - [ ] Document findings

3. **Remediation**
   - [ ] Patch vulnerabilities
   - [ ] Update security rules
   - [ ] Notify affected users (if required)
   - [ ] Update security documentation

4. **Post-Incident**
   - [ ] Review what worked
   - [ ] Identify improvements
   - [ ] Update security procedures
   - [ ] Share lessons learned

---

## Quick Reference

### Critical Files to Block
- `.env`, `.env.*`
- `.git/`, `.git*`
- `*.bak`, `*.backup`, `*.save`, `*.old`
- `wp-config.php`, `config.php`, `config.js`
- `__pycache__/`, `*.pyc`
- `node_modules/`
- `*.sql`, `*.db`, `*.sqlite`

### Critical Environment Variables
- `SECRET_KEY` (required)
- `FLASK_ENV=production` (required)
- `ADMIN_USERNAME` (recommended)
- `STRIPE_*` (if using Stripe)

### Security Headers to Set
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: ...`

---

**Last Updated:** 2026-01-03  
**Next Review:** 2026-04-03

