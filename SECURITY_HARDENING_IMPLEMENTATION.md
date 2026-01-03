# Security Hardening Implementation Guide

**Date:** 2026-01-03  
**Status:** 🚨 URGENT - Production Under Attack  
**Priority:** P0 - Implement Immediately

---

## Executive Summary

Your production application is being targeted by automated reconnaissance attacks. This guide provides step-by-step instructions to implement comprehensive security hardening across all layers of your infrastructure.

**Implementation Time:** 2-4 hours  
**Risk if Not Implemented:** Critical - Secrets could be exposed, application compromised

---

## Implementation Order

### Phase 1: Immediate (Today) - 30 minutes
1. ✅ Cloudflare WAF Rules (if using Cloudflare)
2. ✅ Verify `.env` files not in deployment
3. ✅ Test current blocking (already implemented in app)

### Phase 2: Critical (This Week) - 2 hours
1. ✅ Nginx/Web Server Configuration
2. ✅ Enhanced Application Security
3. ✅ Security Monitoring Setup

### Phase 3: Best Practices (This Month) - Ongoing
1. ✅ Secret Rotation Procedures
2. ✅ Regular Security Reviews
3. ✅ Incident Response Planning

---

## Phase 1: Immediate Actions (30 minutes)

### Step 1.1: Cloudflare WAF Rules

**If you're using Cloudflare:**

1. **Log into Cloudflare Dashboard**
   - Go to: https://dash.cloudflare.com
   - Select your domain: `futureelite.pro`

2. **Navigate to WAF**
   - Security → WAF → Custom Rules

3. **Create Rules** (use expressions from `cloudflare-waf-rules.md`)

   **Rule 1: Block .env Files**
   ```
   (http.request.uri.path contains ".env" or http.request.uri.path contains ".env." or http.request.uri.path matches "^.*\\.env[0-9]*$")
   ```
   - Action: Block
   - Priority: 1

   **Rule 2: Block Git Metadata**
   ```
   (http.request.uri.path contains ".git" or http.request.uri.path contains ".git/" or http.request.uri.path contains ".gitignore")
   ```
   - Action: Block
   - Priority: 1

   **Rule 3: Block Backup Files**
   ```
   (http.request.uri.path matches "\\.(bak|backup|save|old|orig)$" or http.request.uri.path contains "/backup")
   ```
   - Action: Block
   - Priority: 2

4. **Set Up Rate Limiting**
   - Security → WAF → Rate Limiting Rules
   - Create rule: "404 Rate Limit"
     - Match: `(http.response.code eq 404)`
     - Rate: 10 requests per minute
     - Action: Challenge (CAPTCHA)

5. **Verify Rules**
   - Test blocked paths return 404
   - Check WAF logs for rule triggers

**Time:** 15 minutes

---

### Step 1.2: Verify Deployment Security

**Check for sensitive files in deployment:**

```bash
# SSH into your production server (or check deployment package)

# Check for .env files
find /path/to/app -name ".env*" -type f

# Check for .git directory
ls -la /path/to/app | grep "\.git"

# Check for backup files
find /path/to/app -name "*.bak" -o -name "*.backup" -o -name "*.save"

# If any found, remove them immediately
```

**If using managed hosting (Render, Railway, etc.):**
- Verify `.env` is NOT in your repository
- Verify environment variables are set in hosting platform
- Check deployment logs for `.env` file warnings

**Time:** 10 minutes

---

### Step 1.3: Test Current Protection

**Test that application-level blocking works:**

```bash
# Test blocked paths (should return 404)
curl -I https://futureelite.pro/.env
curl -I https://futureelite.pro/.env.bak
curl -I https://futureelite.pro/.git/HEAD
curl -I https://futureelite.pro/wp-config.php

# All should return 404
```

**Time:** 5 minutes

---

## Phase 2: Critical Hardening (2 hours)

### Step 2.1: Nginx Configuration

**If you have nginx access:**

1. **Copy security configuration**
   ```bash
   # Copy nginx-security.conf to your server
   scp nginx-security.conf user@your-server:/etc/nginx/conf.d/security.conf
   ```

2. **Include in main nginx config**
   ```nginx
   # In /etc/nginx/sites-available/your-site
   server {
       # ... existing config ...
       
       # Include security rules
       include /etc/nginx/conf.d/security.conf;
       
       # ... rest of config ...
   }
   ```

3. **Test configuration**
   ```bash
   sudo nginx -t
   ```

4. **Reload nginx**
   ```bash
   sudo systemctl reload nginx
   ```

5. **Verify blocking works**
   ```bash
   curl -I http://localhost/.env
   # Should return 404
   ```

**If using managed hosting without nginx access:**
- Skip this step (rely on Cloudflare WAF and application-level protection)
- Document that nginx rules are not applicable

**Time:** 30 minutes

---

### Step 2.2: Enhanced Application Security (Optional)

**Add enhanced security middleware:**

1. **File already created:** `app/security_middleware.py`

2. **Enable in application** (optional - current protection may be sufficient):
   ```python
   # In app/main.py, uncomment:
   from .security_middleware import security_middleware
   security_middleware.init_app(app)
   ```

3. **Configure admin IP allowlisting** (optional):
   ```bash
   # In your hosting platform, set:
   ADMIN_ALLOWED_IPS=1.2.3.4,5.6.7.8
   ```

**Time:** 15 minutes

---

### Step 2.3: Security Monitoring

**Set up logging and alerting:**

1. **Application Logs**
   - Ensure security events are logged
   - Review logs regularly

2. **Cloudflare Analytics**
   - Monitor WAF rule triggers
   - Set up alerts for high volume

3. **Error Tracking** (if using Sentry, etc.)
   - Monitor for security-related errors
   - Set up alerts for suspicious patterns

**Time:** 30 minutes

---

## Phase 3: Best Practices (Ongoing)

### Step 3.1: Secret Rotation

**Create rotation schedule:**
- See `SECURITY_BEST_PRACTICES.md` Section 1.2

**Immediate action:**
- Rotate `SECRET_KEY` if you suspect it may have been exposed
- Rotate API keys if logs show access attempts

**Time:** 30 minutes (initial setup)

---

### Step 3.2: Regular Security Reviews

**Weekly:**
- Review security logs
- Check for new attack patterns
- Review blocked IPs

**Monthly:**
- Update WAF rules
- Review dependencies
- Update security documentation

**Time:** 1-2 hours per month

---

## Verification Checklist

After implementation, verify:

- [ ] `.env` access returns 404
- [ ] `.git/HEAD` access returns 404
- [ ] `wp-config.php` access returns 404
- [ ] Backup files return 404
- [ ] Legitimate requests still work
- [ ] Admin access works (if configured)
- [ ] Rate limiting works for 404s
- [ ] Security headers are present
- [ ] No false positives in logs

---

## Testing Commands

**Test blocked paths:**
```bash
# Should all return 404
curl -I https://futureelite.pro/.env
curl -I https://futureelite.pro/.env.bak
curl -I https://futureelite.pro/.git/HEAD
curl -I https://futureelite.pro/wp-config.php
curl -I https://futureelite.pro/config.php.bak
curl -I https://futureelite.pro/__pycache__/
```

**Test security headers:**
```bash
curl -I https://futureelite.pro | grep -i "x-frame-options\|x-content-type-options\|strict-transport-security"
```

**Test rate limiting:**
```bash
# Make 15 rapid 404 requests
for i in {1..15}; do
  curl -I https://futureelite.pro/nonexistent-page-$i
done
# Should trigger rate limit after 10 requests
```

---

## Troubleshooting

### Issue: Legitimate requests blocked

**Solution:**
1. Check WAF logs for false positives
2. Adjust rule expressions to be more specific
3. Add exceptions for legitimate paths

### Issue: Rules not working

**Solution:**
1. Verify rules are enabled in Cloudflare
2. Check rule priority (lower number = higher priority)
3. Test rules in "Logs" section
4. Verify nginx config syntax (if using nginx)

### Issue: High false positive rate

**Solution:**
1. Review blocked requests
2. Identify patterns
3. Refine rule expressions
4. Consider using "Challenge" instead of "Block"

---

## Support and Resources

**Documentation:**
- `SECURITY_AUDIT_COMPREHENSIVE.md` - Full audit
- `nginx-security.conf` - Nginx configuration
- `cloudflare-waf-rules.md` - WAF rules
- `DEPLOYMENT_SECURITY_CHECKLIST.md` - Pre-deployment checks
- `SECURITY_BEST_PRACTICES.md` - Ongoing best practices

**External Resources:**
- Cloudflare WAF Documentation: https://developers.cloudflare.com/waf/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework

---

## Next Steps

1. **Today:** Implement Phase 1 (Cloudflare WAF rules)
2. **This Week:** Implement Phase 2 (Nginx + monitoring)
3. **This Month:** Implement Phase 3 (Best practices)

**After Implementation:**
- Monitor for 48 hours
- Review logs daily
- Adjust rules as needed
- Document any changes

---

## Emergency Contacts

If you detect a security incident:

1. **Immediate:** Block offending IPs
2. **Within 1 hour:** Review logs and assess scope
3. **Within 24 hours:** Document incident and remediation

**Security Team:** [Your contact information]

---

**Last Updated:** 2026-01-03  
**Status:** Ready for Implementation

