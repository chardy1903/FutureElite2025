# Security Best Practices Guide

This document provides comprehensive security best practices for production deployment and ongoing operations.

---

## 1. Secret Management

### 1.1 Environment Variables

**✅ DO:**
- Store all secrets in environment variables
- Use your hosting platform's secret management (Render, Railway, Heroku, etc.)
- Never commit secrets to version control
- Use different secrets for development, staging, and production

**❌ DON'T:**
- Hardcode secrets in code
- Store secrets in `.env` files in production
- Commit `.env` files to git
- Share secrets via email or chat
- Use the same secrets across environments

### 1.2 Secret Rotation

**Rotation Schedule:**
- **SECRET_KEY**: Every 6-12 months (or immediately if compromised)
- **API Keys**: Every 90 days (or per provider policy)
- **Database Passwords**: Every 90 days
- **OAuth Secrets**: Every 90 days

**Rotation Process:**
1. Generate new secret
2. Update in hosting platform
3. Deploy application (will pick up new secret)
4. Verify application works
5. Mark old secret as deprecated
6. Delete old secret after 7 days (grace period)

**Example Rotation Script:**
```bash
#!/bin/bash
# Rotate SECRET_KEY

# Generate new key
NEW_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Update in hosting platform (example for Render)
render secrets:set SECRET_KEY="$NEW_KEY"

# Restart application
render services:restart your-service-name

# Verify
curl https://yourdomain.com/health
```

### 1.3 Secret Generation

**Generate secure secrets:**
```python
# Python
import secrets
print(secrets.token_hex(32))  # 64 character hex string

# Or use OpenSSL
openssl rand -hex 32
```

**Requirements:**
- Minimum 32 characters (64 for hex)
- Cryptographically random
- Unique per environment
- Never reuse old secrets

---

## 2. Environment Variable Handling

### 2.1 Development vs Production

**Development:**
- Use `.env` file (gitignored)
- Load via `python-dotenv`
- Document in `env.example`

**Production:**
- Use hosting platform environment variables
- Never use `.env` file
- Verify `.env` not in deployment

### 2.2 Validation

**Always validate required variables:**
```python
# app/config.py
import os

def validate_required_env_vars():
    """Validate all required environment variables are set"""
    required = ['SECRET_KEY', 'FLASK_ENV']
    missing = [var for var in required if not os.environ.get(var)]
    
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
```

### 2.3 Sensitive Variable Handling

**Never log secrets:**
```python
# ❌ BAD
logger.info(f"API Key: {api_key}")

# ✅ GOOD
logger.info("API Key configured")
logger.debug(f"API Key length: {len(api_key)}")
```

---

## 3. Deployment Pipeline Security

### 3.1 Pre-Deployment Checks

**Automated Checks:**
```bash
#!/bin/bash
# pre-deploy-check.sh

# Check for .env files
if [ -f ".env" ]; then
    echo "ERROR: .env file found in deployment"
    exit 1
fi

# Check for secrets in code
if grep -r "SECRET_KEY.*=" app/ --exclude-dir=__pycache__ | grep -v "os.environ"; then
    echo "ERROR: Hardcoded secrets found"
    exit 1
fi

# Check for .git directory
if [ -d ".git" ]; then
    echo "WARNING: .git directory found (should be excluded)"
fi

# Check debug mode
if [ "$FLASK_ENV" != "production" ]; then
    echo "WARNING: FLASK_ENV is not 'production'"
fi
```

### 3.2 CI/CD Security

**GitHub Actions Example:**
```yaml
name: Security Check

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Check for secrets
        run: |
          # Install secret scanning tool
          pip install detect-secrets
          detect-secrets scan --baseline .secrets.baseline
      
      - name: Check for .env files
        run: |
          if find . -name ".env" -not -path "./.git/*"; then
            echo "ERROR: .env files found"
            exit 1
          fi
```

### 3.3 Deployment Package

**Create secure deployment package:**
```bash
#!/bin/bash
# create-deployment-package.sh

# Exclude sensitive files
tar --exclude='.env' \
    --exclude='.env.*' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    --exclude='*.sql' \
    --exclude='*.db' \
    -czf deployment.tar.gz .
```

---

## 4. Logging and Alerting

### 4.1 Security Event Logging

**Log all security events:**
```python
# app/security_middleware.py
import logging

security_logger = logging.getLogger('security')

def log_security_event(event_type, details):
    """Log security events with structured data"""
    security_logger.warning(
        f"SECURITY_EVENT: {event_type}",
        extra={
            'event_type': event_type,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string
        }
    )
```

### 4.2 Alerting Rules

**Set up alerts for:**
- Multiple failed login attempts (>5 in 5 minutes)
- Admin access from new IP
- High volume of 404 requests (>100 in 1 minute)
- WAF rule triggers (>10 in 1 minute)
- Unusual geographic access patterns
- Database connection failures

**Example Alert Configuration (PagerDuty/Datadog):**
```yaml
alerts:
  - name: "Multiple Failed Logins"
    condition: "count(failed_logins) > 5 in 5m"
    action: "notify_security_team"
    
  - name: "Reconnaissance Attack"
    condition: "count(404_requests) > 100 in 1m"
    action: "block_ip_and_alert"
    
  - name: "Admin Access from New IP"
    condition: "admin_access AND ip NOT IN known_ips"
    action: "require_mfa_and_alert"
```

### 4.3 Log Retention

**Retention Policy:**
- **Security logs**: 90 days minimum
- **Access logs**: 30 days
- **Error logs**: 30 days
- **Audit logs**: 1 year (if required by compliance)

---

## 5. Access Control

### 5.1 Admin Access

**Best Practices:**
- Use strong, unique passwords
- Enable 2FA if available
- Restrict admin access by IP (optional)
- Log all admin actions
- Use separate admin accounts (not shared)
- Rotate admin credentials regularly

**IP Allowlisting (Optional):**
```python
# app/routes.py
from app.security_middleware import require_admin_ip

@bp.route('/admin/users')
@login_required
@require_admin_ip(allowed_ips=['1.2.3.4', '5.6.7.8'])
def admin_users():
    ...
```

### 5.2 User Access

**Password Requirements:**
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- No common passwords
- Password history (prevent reuse)

**Session Management:**
- Secure session cookies
- Session timeout (30 minutes inactivity)
- Session regeneration on login
- Limit concurrent sessions

---

## 6. Dependency Management

### 6.1 Regular Updates

**Update Schedule:**
- **Security patches**: Immediately
- **Minor updates**: Monthly
- **Major updates**: Quarterly (with testing)

**Automated Dependency Scanning:**
```bash
# Use safety or pip-audit
pip install safety
safety check

# Or use GitHub Dependabot
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

### 6.2 Vulnerability Management

**Process:**
1. Monitor security advisories
2. Test updates in staging
3. Deploy security patches immediately
4. Document all updates

**Tools:**
- `safety` (Python)
- `npm audit` (Node.js)
- GitHub Dependabot
- Snyk

---

## 7. Incident Response

### 7.1 Preparation

**Incident Response Plan:**
1. **Detection**: Automated monitoring and alerts
2. **Containment**: Isolate affected systems
3. **Eradication**: Remove threat
4. **Recovery**: Restore services
5. **Lessons Learned**: Post-incident review

### 7.2 Response Procedures

**If Secret Compromised:**
1. Rotate secret immediately
2. Review access logs
3. Check for unauthorized access
4. Notify affected users (if required)
5. Document incident

**If Attack Detected:**
1. Block offending IPs
2. Review attack scope
3. Check for data access
4. Update security rules
5. Monitor for recurrence

### 7.3 Communication

**Stakeholder Notification:**
- **Internal**: Immediate (security team)
- **Management**: Within 1 hour
- **Users**: If data accessed (per policy)
- **Regulators**: If required by compliance

---

## 8. Compliance Considerations

### 8.1 Data Protection

**GDPR (if applicable):**
- Data minimization
- Right to access
- Right to deletion
- Data breach notification (72 hours)

**PCI DSS (if processing payments):**
- Encrypt card data
- Secure network
- Access control
- Regular testing

### 8.2 Audit Requirements

**Maintain Audit Logs:**
- User authentication
- Admin actions
- Data access
- Configuration changes
- Security events

**Log Format:**
```json
{
  "timestamp": "2026-01-03T12:00:00Z",
  "event_type": "admin_action",
  "user": "admin_user",
  "action": "delete_user",
  "target": "user_id_123",
  "ip": "1.2.3.4",
  "result": "success"
}
```

---

## 9. Regular Security Reviews

### 9.1 Weekly

- [ ] Review security logs
- [ ] Check for failed login attempts
- [ ] Review blocked IPs
- [ ] Check for new attack patterns

### 9.2 Monthly

- [ ] Review and update WAF rules
- [ ] Check dependency vulnerabilities
- [ ] Review access logs
- [ ] Update security documentation

### 9.3 Quarterly

- [ ] Full security audit
- [ ] Penetration testing (if budget allows)
- [ ] Review and update security policies
- [ ] Security training for team

### 9.4 Annually

- [ ] Comprehensive security assessment
- [ ] Review and update incident response plan
- [ ] Security certification renewal (if applicable)
- [ ] Disaster recovery testing

---

## 10. Resources and Tools

### 10.1 Security Tools

**Scanning:**
- OWASP ZAP (web app scanning)
- Nmap (network scanning)
- Nikto (web server scanning)

**Monitoring:**
- Cloudflare Analytics
- Application Performance Monitoring (APM)
- Security Information and Event Management (SIEM)

**Dependency Scanning:**
- Safety (Python)
- npm audit (Node.js)
- Snyk

### 10.2 Security Resources

**Standards:**
- OWASP Top 10
- NIST Cybersecurity Framework
- CIS Controls

**Training:**
- OWASP WebGoat
- PortSwigger Web Security Academy
- Security training courses

---

## 11. Quick Reference

### Critical Security Checks

```bash
# Check for .env files
find . -name ".env*" -not -path "./.git/*"

# Check for secrets in code
grep -r "SECRET_KEY.*=" app/ --exclude-dir=__pycache__

# Check for .git directory
ls -la | grep "\.git"

# Verify security headers
curl -I https://yourdomain.com | grep -i "x-frame-options"

# Test blocked paths
curl -I https://yourdomain.com/.env
curl -I https://yourdomain.com/.git/HEAD
```

### Emergency Contacts

- **Security Team**: [your-security-email]
- **Hosting Provider Support**: [support-contact]
- **Cloudflare Support**: [cloudflare-contact]

---

**Last Updated:** 2026-01-03  
**Next Review:** 2026-04-03

