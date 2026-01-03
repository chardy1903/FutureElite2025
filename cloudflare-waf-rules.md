# Cloudflare WAF Rules Configuration

This document provides production-ready Cloudflare WAF (Web Application Firewall) rules to protect against automated reconnaissance attacks.

## Implementation Method

Cloudflare WAF rules can be configured via:
1. **Cloudflare Dashboard** → Security → WAF → Custom Rules
2. **Cloudflare API** (for automation)
3. **Terraform** (for Infrastructure as Code)

---

## Rule Set 1: Block Environment Variable File Access

**Priority:** 1 (Highest)  
**Action:** Block  
**Description:** Blocks all requests attempting to access `.env` files and variants

### Rule Expression (Cloudflare Dashboard)

```
(http.request.uri.path contains ".env" or http.request.uri.path contains ".env." or http.request.uri.path matches "^.*\\.env[0-9]*$")
```

### Rule Expression (API/Terraform)

```json
{
  "expression": "(http.request.uri.path contains \".env\" or http.request.uri.path contains \".env.\" or http.request.uri.path matches \"^.*\\.env[0-9]*$\")",
  "action": "block",
  "description": "Block .env file access attempts"
}
```

### Matches
- `/.env`
- `/.env.bak`
- `/.env.save`
- `/.env.backup`
- `/.env.old`
- `/.env1`
- `/backend/.env`
- `/admin/.env`
- `/app/.env`

---

## Rule Set 2: Block Git Metadata Access

**Priority:** 1 (Highest)  
**Action:** Block  
**Description:** Blocks access to Git repository metadata

### Rule Expression

```
(http.request.uri.path contains ".git" or http.request.uri.path contains ".git/" or http.request.uri.path contains ".gitignore" or http.request.uri.path contains ".gitattributes" or http.request.uri.path contains ".gitmodules")
```

### Matches
- `/.git/`
- `/.git/HEAD`
- `/.git/config`
- `/.gitignore`
- `/.gitattributes`
- `/.gitmodules`

---

## Rule Set 3: Block Backup File Patterns

**Priority:** 2 (High)  
**Action:** Block  
**Description:** Blocks common backup file extensions and patterns

### Rule Expression

```
(http.request.uri.path matches "\\.(bak|backup|save|old|orig|swp|swo|tmp|temp)$" or http.request.uri.path contains "/backup" or http.request.uri.path contains "/backups" or http.request.uri.path contains "/old" or http.request.uri.path contains "/temp")
```

### Matches
- `/config.php.bak`
- `/file.save`
- `/data.old`
- `/backup/`
- `/backups/`
- `/old/`
- `/temp/`

---

## Rule Set 4: Block Configuration File Access

**Priority:** 2 (High)  
**Action:** Block  
**Description:** Blocks access to configuration files that may contain secrets

### Rule Expression

```
(http.request.uri.path matches "/(wp-config|config|aws-config|aws\\.config)\\.(php|js|json|bak|old|save)$" or http.request.uri.path matches "/config\\.(php|js|json|yaml|yml|toml|ini)$")
```

### Matches
- `/wp-config.php`
- `/wp-config.php.old`
- `/config.php`
- `/config.js`
- `/aws-config.js`
- `/config.yaml`

---

## Rule Set 5: Block Build Artifacts

**Priority:** 3 (Medium)  
**Action:** Block  
**Description:** Blocks Python bytecode and build artifacts

### Rule Expression

```
(http.request.uri.path contains "__pycache__" or http.request.uri.path matches "\\.pyc$" or http.request.uri.path matches "\\.pyo$" or http.request.uri.path contains "node_modules")
```

### Matches
- `/__pycache__/`
- `/app/__pycache__/module.pyc`
- `/node_modules/`
- `/package.pyc`

---

## Rule Set 6: Block Version Control Metadata

**Priority:** 2 (High)  
**Action:** Block  
**Description:** Blocks Subversion and Mercurial metadata

### Rule Expression

```
(http.request.uri.path contains ".svn" or http.request.uri.path contains ".hg")
```

### Matches
- `/.svn/`
- `/.hg/`
- `/.svn/entries`

---

## Rule Set 7: Block Database Files

**Priority:** 2 (High)  
**Action:** Block  
**Description:** Blocks SQL and database dump files

### Rule Expression

```
(http.request.uri.path matches "\\.(sql|dump|db|sqlite|sqlite3)$" or http.request.uri.path matches "/(database|dump|backup)\\.sql$")
```

### Matches
- `/database.sql`
- `/dump.sql`
- `/backup.sql`
- `/data.db`
- `/app.sqlite`

---

## Rule Set 8: Rate Limit 404 Requests (Reconnaissance Detection)

**Priority:** 1 (Highest)  
**Action:** Challenge (CAPTCHA) or Block  
**Description:** Detects reconnaissance by rate limiting repeated 404 responses

### Rule Expression

```
(http.response.code eq 404)
```

### Rate Limiting Configuration
- **Requests:** 10 per minute per IP
- **Action:** Challenge (CAPTCHA) after threshold
- **Duration:** 1 hour

### Cloudflare Dashboard Setup
1. Go to Security → WAF → Rate Limiting Rules
2. Create rule:
   - **Rule name:** "Reconnaissance Detection - 404 Rate Limit"
   - **Match:** `(http.response.code eq 404)`
   - **Requests:** 10
   - **Period:** 1 minute
   - **Action:** Challenge
   - **Duration:** 1 hour

---

## Rule Set 9: Block Admin Path Enumeration

**Priority:** 2 (High)  
**Action:** Challenge (CAPTCHA)  
**Description:** Challenges requests to admin paths from suspicious sources

### Rule Expression

```
(http.request.uri.path matches "^/admin" or http.request.uri.path matches "^/api/admin") and not (ip.geoip.country in {"US" "CA" "GB" "AU" "DE" "FR"})
```

**Note:** Adjust country list based on your legitimate user base. Remove country restriction if you have global users.

### Alternative (IP-based allowlist)
If you have a static IP for admin access:

```
(http.request.uri.path matches "^/admin" or http.request.uri.path matches "^/api/admin") and not (ip.src in {YOUR_ADMIN_IP_1 YOUR_ADMIN_IP_2})
```

---

## Rule Set 10: Block PHP Files (This is Python App)

**Priority:** 3 (Medium)  
**Action:** Block  
**Description:** Blocks PHP files (this application doesn't use PHP)

### Rule Expression

```
(http.request.uri.path matches "\\.php$" or http.request.uri.path contains "phpinfo" or http.request.uri.path contains "phpmyadmin" or http.request.uri.path contains "xmlrpc")
```

### Matches
- `/index.php`
- `/phpinfo.php`
- `/phpmyadmin/`
- `/xmlrpc.php`

---

## Rule Set 11: Block Hidden Files (Catch-All)

**Priority:** 3 (Medium)  
**Action:** Block  
**Description:** Blocks hidden files while allowing `.well-known`

### Rule Expression

```
(http.request.uri.path matches "^/\\." and not http.request.uri.path matches "^\\.well-known")
```

**Note:** This is a catch-all. Make sure `.well-known` is explicitly allowed for Let's Encrypt.

---

## Rule Set 12: Block Suspicious User Agents

**Priority:** 2 (High)  
**Action:** Challenge (CAPTCHA)  
**Description:** Challenges requests with suspicious or empty user agents

### Rule Expression

```
(http.user_agent eq "" or http.user_agent contains "sqlmap" or http.user_agent contains "nikto" or http.user_agent contains "masscan" or http.user_agent contains "nmap" or http.user_agent contains "scanner")
```

---

## Complete Rule Configuration (JSON for API)

```json
{
  "rules": [
    {
      "id": "block-env-files",
      "expression": "(http.request.uri.path contains \".env\" or http.request.uri.path contains \".env.\" or http.request.uri.path matches \"^.*\\.env[0-9]*$\")",
      "action": "block",
      "description": "Block .env file access attempts",
      "priority": 1
    },
    {
      "id": "block-git-metadata",
      "expression": "(http.request.uri.path contains \".git\" or http.request.uri.path contains \".git/\" or http.request.uri.path contains \".gitignore\")",
      "action": "block",
      "description": "Block Git metadata access",
      "priority": 1
    },
    {
      "id": "block-backup-files",
      "expression": "(http.request.uri.path matches \"\\.(bak|backup|save|old|orig)$\" or http.request.uri.path contains \"/backup\")",
      "action": "block",
      "description": "Block backup file access",
      "priority": 2
    },
    {
      "id": "block-config-files",
      "expression": "(http.request.uri.path matches \"/(wp-config|config|aws-config)\\.(php|js|json|bak)$\")",
      "action": "block",
      "description": "Block configuration file access",
      "priority": 2
    },
    {
      "id": "block-build-artifacts",
      "expression": "(http.request.uri.path contains \"__pycache__\" or http.request.uri.path matches \"\\.pyc$\" or http.request.uri.path contains \"node_modules\")",
      "action": "block",
      "description": "Block build artifacts",
      "priority": 3
    },
    {
      "id": "block-php-files",
      "expression": "(http.request.uri.path matches \"\\.php$\" or http.request.uri.path contains \"phpinfo\")",
      "action": "block",
      "description": "Block PHP files (Python app)",
      "priority": 3
    },
    {
      "id": "block-hidden-files",
      "expression": "(http.request.uri.path matches \"^/\\\\.\" and not http.request.uri.path matches \"^\\\\.well-known\")",
      "action": "block",
      "description": "Block hidden files (except .well-known)",
      "priority": 3
    }
  ]
}
```

---

## Rate Limiting Rules (Separate Configuration)

### 404 Rate Limiting

**Rule Name:** Reconnaissance Detection  
**Match:** `(http.response.code eq 404)`  
**Rate:** 10 requests per minute  
**Action:** Challenge (CAPTCHA)  
**Duration:** 1 hour

### Admin Path Rate Limiting

**Rule Name:** Admin Path Protection  
**Match:** `(http.request.uri.path matches "^/admin" or http.request.uri.path matches "^/api/admin")`  
**Rate:** 20 requests per minute  
**Action:** Challenge (CAPTCHA)  
**Duration:** 30 minutes

### Login Rate Limiting

**Rule Name:** Login Protection  
**Match:** `(http.request.uri.path eq "/login" and http.request.method eq "POST")`  
**Rate:** 5 requests per minute  
**Action:** Challenge (CAPTCHA)  
**Duration:** 15 minutes

---

## Implementation Steps

1. **Log into Cloudflare Dashboard**
2. **Select your domain**
3. **Navigate to Security → WAF → Custom Rules**
4. **Create each rule** using the expressions above
5. **Set priorities** (lower number = higher priority)
6. **Test rules** in "Logs" to ensure no false positives
7. **Monitor** for 24-48 hours after deployment
8. **Adjust** rules based on legitimate traffic patterns

---

## Testing

After deployment, test that:
- ✅ Legitimate requests still work
- ✅ `.env` access attempts are blocked
- ✅ Admin paths are protected
- ✅ Rate limiting works for 404s
- ✅ `.well-known` paths still work (for Let's Encrypt)

---

## Monitoring and Alerting

Set up Cloudflare notifications for:
- WAF rule triggers (high volume)
- Rate limit violations
- Blocked requests from specific IPs
- Geographic anomalies

---

## Notes

1. **Order matters:** Rules are evaluated in priority order
2. **Test thoroughly:** Some rules may need adjustment for your use case
3. **Monitor logs:** Watch for false positives
4. **Update regularly:** Add new patterns as attackers evolve
5. **Combine with application-level protection:** Defense in depth

---

**Last Updated:** 2026-01-03

