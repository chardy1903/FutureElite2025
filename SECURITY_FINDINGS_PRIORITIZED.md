# Security Findings - Prioritized Report

**Date:** 2025-01-XX  
**Application:** GoalTracker  
**Total Findings:** 23 (5 Critical, 8 High, 7 Medium, 3 Low)

---

## 🔴 CRITICAL PRIORITY (Fix Immediately)

### CRIT-001: Hard-coded Default SECRET_KEY
**Severity:** Critical  
**OWASP:** A02:2021 – Cryptographic Failures  
**File:** `app/main.py:39`  
**Line:** 39

```python
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'futureelite-2025-dev-only')
```

**Issue:** Predictable default secret key allows session cookie forgery and account takeover.

**Fix:** Require SECRET_KEY environment variable, fail startup if not set.

**Impact:** Complete session hijacking, account takeover, data breach.

---

### CRIT-002: Missing CSRF Protection
**Severity:** Critical  
**OWASP:** A01:2021 – Broken Access Control  
**Files:** All POST/PUT/DELETE endpoints  
**Primary:** `app/routes.py`, `app/auth_routes.py`, `app/subscription_routes.py`

**Affected Endpoints:**
- `app/routes.py:135` - POST `/matches`
- `app/routes.py:196` - PUT `/matches/<match_id>`
- `app/routes.py:260` - DELETE `/matches/<match_id>`
- `app/routes.py:1469` - POST `/settings`
- `app/routes.py:1583` - POST `/api/upload-photo`
- `app/routes.py:841` - POST `/import`
- `app/routes.py:1040` - POST `/import-excel`
- `app/routes.py:1705` - POST `/api/physical-measurements`
- `app/routes.py:1773` - PUT `/api/physical-measurements/<measurement_id>`
- `app/routes.py:1834` - DELETE `/api/physical-measurements/<measurement_id>`
- `app/routes.py:2198` - POST `/api/achievements`
- `app/routes.py:2271` - PUT `/api/achievements/<achievement_id>`
- `app/routes.py:2335` - DELETE `/api/achievements/<achievement_id>`
- `app/routes.py:2808` - POST `/api/club-history`
- `app/routes.py:2845` - PUT `/api/club-history/<entry_id>`
- `app/routes.py:2880` - DELETE `/api/club-history/<entry_id>`
- `app/routes.py:2925` - POST `/api/training-camps`
- `app/routes.py:2972` - PUT `/api/training-camps/<camp_id>`
- `app/routes.py:3009` - DELETE `/api/training-camps/<camp_id>`
- `app/routes.py:3060` - POST `/api/physical-metrics`
- `app/routes.py:3156` - PUT `/api/physical-metrics/<metric_id>`
- `app/routes.py:3245` - DELETE `/api/physical-metrics/<metric_id>`
- `app/auth_routes.py:19` - POST `/login`
- `app/auth_routes.py:61` - POST `/register`
- `app/subscription_routes.py:54` - POST `/api/subscription/status`
- `app/subscription_routes.py:111` - POST `/api/subscription/create-checkout`
- `app/subscription_routes.py:261` - POST `/api/subscription/create-portal`
- `app/subscription_routes.py:555` - POST `/api/subscription/sync`

**Issue:** No CSRF token validation on any state-changing operations.

**Fix:** Install Flask-WTF, add CSRFProtect, require tokens on all POST/PUT/DELETE.

**Impact:** Cross-site request forgery, unauthorized data modification, payment fraud.

---

### CRIT-003: Insecure Client-Side Password Hashing
**Severity:** Critical  
**OWASP:** A02:2021 – Cryptographic Failures  
**File:** `app/static/js/storage.js:518-530`  
**Lines:** 518-530

```javascript
async hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}
```

**Issue:** SHA-256 without salt, fast hash vulnerable to brute force, client-side hashing is insecure.

**Fix:** Remove client-side hashing entirely, send plain password over HTTPS to server.

**Impact:** Password recovery from client storage, rainbow table attacks, weak security.

---

### CRIT-004: Stripe Webhook Signature Verification Bypass
**Severity:** Critical  
**OWASP:** A01:2021 – Broken Access Control  
**File:** `app/subscription_routes.py:324-326`  
**Lines:** 324-326

```python
if webhook_secret:
    event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
else:
    # In development, you might skip signature verification
    event = json.loads(payload)  # ← Bypass!
```

**Issue:** If STRIPE_WEBHOOK_SECRET not set, signature verification is bypassed.

**Fix:** Require webhook_secret, reject webhooks without valid signature.

**Impact:** Forged webhook events, free premium access, subscription manipulation.

---

### CRIT-005: IDOR in Subscription Status Endpoint
**Severity:** Critical  
**OWASP:** A01:2021 – Broken Access Control  
**File:** `app/subscription_routes.py:54-108`  
**Lines:** 59-60

```python
data = request.get_json() if request.is_json else {}
user_id = data.get('user_id')  # ← User-controlled!
```

**Issue:** Endpoint accepts user_id from client, no authorization check.

**Fix:** Use `@login_required` and `current_user.id` instead of user-provided user_id.

**Impact:** Information disclosure, subscription status enumeration, privacy violation.

---

## 🟠 HIGH PRIORITY (Fix This Week)

### HIGH-001: Missing Rate Limiting on Authentication
**Severity:** High  
**OWASP:** A07:2021 – Identification and Authentication Failures  
**Files:** `app/auth_routes.py:19, 61`  
**Lines:** 19-58, 61-100

**Issue:** No rate limiting on `/login` or `/register` endpoints.

**Fix:** Install flask-limiter, add `@limiter.limit("5 per minute")` to auth endpoints.

**Impact:** Brute force attacks, account enumeration, DoS via registration spam.

---

### HIGH-002: Verbose Error Messages Expose Internals
**Severity:** High  
**OWASP:** A04:2021 – Security Logging and Monitoring Failures  
**File:** `app/main.py:65-79`  
**Lines:** 65-79

```python
return jsonify({
    'success': False,
    'errors': [f'Internal server error: {error_details}']  # ← Exposes stack traces
}), 500
```

**Issue:** Stack traces and exception details leaked to clients.

**Fix:** Log errors server-side, return generic message to client.

**Impact:** Information disclosure, aids exploit development, reveals code structure.

---

### HIGH-003: Insecure Session Cookie Configuration
**Severity:** High  
**OWASP:** A02:2021 – Cryptographic Failures  
**File:** `app/main.py:33-49`  
**Lines:** 33-49 (missing configuration)

**Issue:** No explicit session cookie security flags (HttpOnly, Secure, SameSite).

**Fix:** Add `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE`.

**Impact:** XSS session theft, session hijacking, CSRF vulnerability.

---

### HIGH-004: Missing Security Headers
**Severity:** High  
**OWASP:** A05:2021 – Security Misconfiguration  
**File:** `app/main.py` (missing entirely)

**Issue:** No CSP, HSTS, X-Frame-Options, X-Content-Type-Options headers.

**Fix:** Install flask-talisman, configure security headers.

**Impact:** XSS attacks, clickjacking, MIME sniffing, man-in-the-middle.

---

### HIGH-005: File Upload Validation Insufficient
**Severity:** High  
**OWASP:** A03:2021 – Injection  
**File:** `app/routes.py:1583-1629`  
**Lines:** 1597-1613

```python
allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
filename = secure_filename(file.filename)
if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
    return jsonify({'success': False, 'errors': ['Invalid file type']}), 400
file.save(filepath)  # ← No content validation
```

**Issue:** Only extension check, no MIME type validation, no content scanning.

**Fix:** Validate MIME type with python-magic, verify image with PIL, use random filenames.

**Impact:** Malicious file uploads, code execution if files served, storage exhaustion.

---

### HIGH-006: ZIP Bomb Vulnerability
**Severity:** High  
**OWASP:** A03:2021 – Injection  
**File:** `app/routes.py:841-938`  
**Lines:** 871-908

```python
with zipfile.ZipFile(temp_file.name, 'r') as zip_file:
    matches_data = json.loads(zip_file.read('matches.json').decode('utf-8'))
    # ... no size checks on uncompressed data
```

**Issue:** No check on uncompressed size, vulnerable to ZIP bomb attacks.

**Fix:** Check total uncompressed size, limit per-file size, limit number of files.

**Impact:** DoS via memory exhaustion, server crash, resource exhaustion.

---

### HIGH-007: Excel Import Code Injection Risk
**Severity:** High  
**OWASP:** A03:2021 – Injection  
**File:** `app/routes.py:1040-1200`  
**Lines:** 1075-1200

```python
workbook = openpyxl.load_workbook(temp_file.name)  # ← No validation
sheet = workbook.active
# Processes cell values directly
```

**Issue:** Excel formulas not sanitized, potential formula injection.

**Fix:** Load with `data_only=True`, sanitize cell values, reject formulas.

**Impact:** Formula injection, data corruption, potential code execution.

---

### HIGH-008: Missing Input Length Validation
**Severity:** High  
**OWASP:** A03:2021 – Injection  
**Files:** `app/models.py` (multiple models)  
**Lines:** 421, 427-436, 22-33, 100-122, etc.

**Issue:** No maximum length validation on text fields.

**Affected Models:**
- `app/models.py:421` - User.username (only min_length=3)
- `app/models.py:423` - User.email (no validation)
- `app/models.py:23` - Match.opponent (no max)
- `app/models.py:24` - Match.location (no max)
- `app/models.py:31` - Match.notes (no max)
- `app/models.py:100-122` - AppSettings fields (no max)
- All other string fields in models

**Fix:** Add `max_length` to all string Field definitions.

**Impact:** DoS via large payloads, memory exhaustion, storage exhaustion.

---

## 🟡 MEDIUM PRIORITY (Fix This Month)

### MED-001: Weak Password Policy
**Severity:** Medium  
**OWASP:** A07:2021 – Identification and Authentication Failures  
**File:** `app/auth_routes.py:77`  
**Line:** 77

```python
if len(password) < 6:
    return jsonify({'success': False, 'errors': ['Password must be at least 6 characters']}), 400
```

**Issue:** Minimum length only 6 characters, no complexity requirements.

**Fix:** Require 12+ characters, uppercase, lowercase, number, special character.

**Impact:** Weak passwords, easier brute force attacks.

---

### MED-002: Information Disclosure in Error Messages
**Severity:** Medium  
**OWASP:** A04:2021 – Security Logging and Monitoring Failures  
**File:** `app/auth_routes.py:35-47`  
**Lines:** 35-47

**Issue:** Different error messages reveal whether username exists (account enumeration).

**Fix:** Always return same error message, add timing delay to prevent timing attacks.

**Impact:** Account enumeration, user privacy violation.

---

### MED-003: Missing Audit Logging
**Severity:** Medium  
**OWASP:** A09:2021 – Security Logging and Monitoring Failures  
**Files:** All state-changing endpoints

**Issue:** No logging of security-relevant events (logins, data changes, uploads).

**Fix:** Add security logger, log all authentication attempts, data modifications, file uploads.

**Impact:** No audit trail, difficult incident response, compliance issues.

---

### MED-004: Session Fixation Vulnerability
**Severity:** Medium  
**OWASP:** A01:2021 – Broken Access Control  
**File:** `app/auth_routes.py:50-51`  
**Lines:** 50-51

```python
login_user(user_session, remember=True)  # ← Doesn't regenerate session ID
```

**Issue:** Session ID not regenerated on login.

**Fix:** Call `session.regenerate()` after successful login.

**Impact:** Session fixation attacks, account takeover.

---

### MED-005: Missing Content-Type Validation
**Severity:** Medium  
**OWASP:** A03:2021 – Injection  
**Files:** All JSON endpoints

**Issue:** Endpoints don't validate Content-Type header.

**Fix:** Add decorator to require `Content-Type: application/json`.

**Impact:** Request smuggling, MIME confusion attacks.

---

### MED-006: Predictable Resource IDs
**Severity:** Medium  
**OWASP:** A01:2021 – Broken Access Control  
**File:** `app/models.py` (multiple models)  
**Lines:** 20, 145, 171, 199, 222, 316, 420, 481

```python
id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
```

**Issue:** Timestamp-based IDs are predictable and enumerable.

**Fix:** Use `secrets.token_urlsafe(16)` for unpredictable IDs.

**Impact:** Resource enumeration, easier IDOR exploitation.

---

### MED-007: Missing Output Encoding Verification
**Severity:** Medium  
**OWASP:** A03:2021 – Injection  
**Files:** `app/templates/*.html` (needs manual review)

**Issue:** Need to verify all template variables are properly escaped.

**Status:** Requires manual template audit to confirm no `|safe` filters on user input.

**Fix:** Ensure all user-controlled data uses `{{ variable }}` (auto-escaped), never `{{ variable|safe }}`.

**Impact:** Potential XSS if templates not properly escaped.

---

## 🟢 LOW PRIORITY (Fix When Possible)

### LOW-001: Missing HSTS Preload
**Severity:** Low  
**OWASP:** A05:2021 – Security Misconfiguration  
**File:** Security headers implementation (when added)

**Issue:** HSTS not configured for preload.

**Fix:** Add `includeSubDomains` and `preload` directives to HSTS header.

**Impact:** Reduced protection against SSL stripping.

---

### LOW-002: Debug Mode Configuration
**Severity:** Low  
**OWASP:** A05:2021 – Security Misconfiguration  
**File:** `app/main.py:42`  
**Line:** 42

```python
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Should be False in production
```

**Issue:** Template auto-reload enabled (development setting).

**Fix:** Set based on environment: `os.environ.get('FLASK_ENV') != 'production'`.

**Impact:** Performance impact, potential information disclosure.

---

### LOW-003: Missing Dependency Pinning
**Severity:** Low  
**OWASP:** A06:2021 – Vulnerable and Outdated Components  
**File:** `requirements.txt`  
**Lines:** 1-7

```txt
Flask>=2.0.0  # ← Should pin exact versions
flask-login>=0.6.0
```

**Issue:** Unpinned versions can pull in vulnerable updates.

**Fix:** Pin exact versions: `Flask==2.3.3`, use `pip freeze > requirements.txt`.

**Impact:** Unpredictable builds, potential vulnerable dependencies.

---

## Summary Statistics

| Priority | Count | Estimated Fix Time |
|----------|-------|-------------------|
| Critical | 5 | 30 minutes |
| High | 8 | 5 hours |
| Medium | 7 | 2 hours |
| Low | 3 | 1 hour |
| **Total** | **23** | **~8 hours** |

---

## Quick Reference: File Locations

### Critical Files Requiring Immediate Attention
- `app/main.py:39` - SECRET_KEY
- `app/subscription_routes.py:54-108` - IDOR
- `app/subscription_routes.py:324-326` - Webhook bypass
- `app/static/js/storage.js:518-530` - Client password hashing
- All POST/PUT/DELETE endpoints - CSRF protection needed

### High Priority Files
- `app/auth_routes.py` - Rate limiting, password policy, account enumeration
- `app/main.py:65-79` - Error handling
- `app/main.py:33-49` - Session cookies
- `app/routes.py:1583-1629` - File upload
- `app/routes.py:841-938` - ZIP import
- `app/routes.py:1040-1200` - Excel import
- `app/models.py` - Input validation

### Medium Priority Files
- `app/auth_routes.py` - Session fixation, error messages
- `app/models.py` - Predictable IDs
- `app/templates/*.html` - Output encoding audit needed

### Low Priority Files
- `app/main.py:42` - Debug mode
- `requirements.txt` - Dependency pinning

---

## Testing Verification

After applying fixes, verify:

```bash
# Test SECRET_KEY requirement
python -c "from app.main import create_app; create_app()"  # Should fail without SECRET_KEY

# Test CSRF protection
curl -X POST http://localhost:8080/matches -H "Cookie: session=..." -d '{}'  # Should fail

# Test rate limiting
for i in {1..10}; do curl -X POST http://localhost:8080/login -d '{}'; done  # Should block

# Test IDOR fix
curl -X POST http://localhost:8080/api/subscription/status \
  -d '{"user_id":"other_user"}'  # Should require authentication

# Test webhook signature
curl -X POST http://localhost:8080/api/subscription/webhook \
  -d '{"type":"test"}'  # Should reject without signature
```

---

**Report Generated:** 2025-01-XX  
**Next Review:** After implementing critical and high priority fixes

