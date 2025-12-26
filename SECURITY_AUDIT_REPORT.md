# Security Audit Report: GoalTracker Application

**Date:** 2025-01-XX  
**Auditor:** Senior Application Security Engineer  
**Scope:** Complete codebase security review  
**Methodology:** STRIDE threat modeling, automated pattern search, manual code review

---

## Executive Summary

This security audit identified **23 findings** across multiple severity levels:
- **5 Critical** - Immediate remediation required
- **8 High** - Address within 1 week
- **7 Medium** - Address within 1 month
- **3 Low** - Address as time permits

**Top 5 Critical Risks:**
1. **Hard-coded default SECRET_KEY** (app/main.py:39) - Allows session hijacking
2. **Missing CSRF protection** - All state-changing operations vulnerable
3. **Insecure password hashing in client-side storage** (app/static/js/storage.js:518-524) - SHA-256 without salt
4. **Stripe webhook signature verification bypass** (app/subscription_routes.py:324-326) - Allows subscription manipulation
5. **Missing authorization checks on subscription status endpoint** (app/subscription_routes.py:54-108) - IDOR vulnerability

---

## 1. Application Architecture & Threat Model

### Components Identified

**Backend:**
- Flask application (app/main.py)
- JSON file-based storage (app/storage.py)
- Authentication via Flask-Login (app/auth.py, app/auth_routes.py)
- API routes (app/routes.py, app/subscription_routes.py)
- PDF generation (app/pdf.py)

**Frontend:**
- Client-side IndexedDB storage (app/static/js/storage.js)
- Client-side authentication (app/static/js/auth.js)
- Jinja2 templates (app/templates/)

**External Services:**
- Stripe payment processing
- CDN for TailwindCSS

### Trust Boundaries

1. **Client ↔ Server:** All API endpoints, authentication
2. **User ↔ Storage:** JSON files in `data/` directory
3. **Server ↔ Stripe:** Webhook endpoints, payment processing
4. **File Uploads:** Photo uploads, Excel/ZIP imports

### Data Flow

```
User Input → Client Validation → API Endpoint → Server Validation → Storage
                                                      ↓
                                              Authorization Check
```

**Critical Finding:** Authorization checks exist but are bypassable (see IDOR findings).

---

## 2. Critical Findings

### CRIT-001: Hard-coded Default SECRET_KEY

**Severity:** Critical  
**OWASP Category:** A02:2021 – Cryptographic Failures  
**ASVS:** V7.1.1, V7.1.2  
**File:** `app/main.py:39`

**Issue:**
```python
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'futureelite-2025-dev-only')
```

**Impact:**
- If `SECRET_KEY` environment variable is not set, a predictable default is used
- Attackers can forge session cookies and impersonate any user
- All authenticated sessions are compromised

**Exploit Scenario:**
```python
# Attacker can generate valid session cookies
from flask.sessions import SecureCookieSessionInterface
app.secret_key = 'futureelite-2025-dev-only'
session_serializer = SecureCookieSessionInterface().get_signing_serializer(app)
forged_session = session_serializer.dumps({'user_id': 'target_user_id'})
```

**Fix:**
```python
# app/main.py:39
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable must be set in production. "
        "Generate with: python -c 'import secrets; print(secrets.token_hex(32))'"
    )
app.config['SECRET_KEY'] = secret_key
```

**Quick Win:** 5 minutes

---

### CRIT-002: Missing CSRF Protection

**Severity:** Critical  
**OWASP Category:** A01:2021 – Broken Access Control  
**ASVS:** V4.2.1, V4.2.2  
**Files:** All POST/PUT/DELETE endpoints

**Issue:**
- No CSRF token validation on any state-changing endpoints
- Flask-WTF not installed or configured
- All authenticated POST/PUT/DELETE requests are vulnerable

**Affected Endpoints:**
- `/matches` (POST, PUT, DELETE)
- `/api/physical-measurements` (POST, PUT, DELETE)
- `/api/achievements` (POST, PUT, DELETE)
- `/settings` (POST)
- `/api/upload-photo` (POST)
- `/import` (POST)
- `/import-excel` (POST)
- `/api/subscription/*` (POST)
- All other state-changing operations

**Impact:**
- Attackers can perform actions on behalf of authenticated users
- Cross-site request forgery attacks can modify/delete data
- Payment subscription manipulation possible

**Exploit Scenario:**
```html
<!-- Attacker's website -->
<form action="https://victim-app.com/matches" method="POST" id="csrf">
  <input name="category" value="League">
  <input name="date" value="01 Jan 2025">
  <input name="opponent" value="Hacked Team">
  <input name="location" value="Hacker Stadium">
</form>
<script>
  // Victim visits attacker's site while logged in
  document.getElementById('csrf').submit();
</script>
```

**Fix:**
```python
# Install: pip install flask-wtf

# app/main.py
from flask_wtf.csrf import CSRFProtect

def create_app():
    app = Flask(__name__)
    # ... existing config ...
    csrf = CSRFProtect(app)
    # ... rest of setup ...
```

Then add CSRF token to all forms and validate on API endpoints:
```python
# For JSON APIs, use CSRF token in header
# X-CSRFToken: <token>
```

**Quick Win:** 1 hour (install + basic implementation)

---

### CRIT-003: Insecure Client-Side Password Hashing

**Severity:** Critical  
**OWASP Category:** A02:2021 – Cryptographic Failures  
**ASVS:** V2.1.1, V2.1.2  
**File:** `app/static/js/storage.js:518-530`

**Issue:**
```javascript
async hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}
```

**Problems:**
1. SHA-256 is a fast hash, vulnerable to brute force
2. No salt - same password produces same hash
3. Client-side hashing is fundamentally insecure
4. Server uses proper `werkzeug.security.generate_password_hash` (scrypt), but client bypasses it

**Impact:**
- Passwords stored client-side can be cracked easily
- Rainbow table attacks possible
- If client storage is compromised, passwords are recoverable

**Exploit Scenario:**
```javascript
// Attacker with access to client storage
const user = await storage.getUserByUsername('victim');
// user.password_hash is SHA-256 of password
// Can brute force or use rainbow tables
```

**Fix:**
**Remove client-side password hashing entirely.** Passwords should:
1. Never be stored client-side
2. Be sent to server over HTTPS
3. Be hashed server-side only using werkzeug (already correct)

```javascript
// app/static/js/auth.js - Remove client-side hashing
// Send plain password to server (over HTTPS)
async login(username, password) {
    const response = await fetch('/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    });
    // Server handles hashing
}
```

**Quick Win:** 30 minutes

---

### CRIT-004: Stripe Webhook Signature Verification Bypass

**Severity:** Critical  
**OWASP Category:** A01:2021 – Broken Access Control  
**ASVS:** V4.3.1  
**File:** `app/subscription_routes.py:324-326`

**Issue:**
```python
if webhook_secret:
    event = stripe.Webhook.construct_event(
        payload, sig_header, webhook_secret
    )
else:
    # In development, you might skip signature verification
    event = json.loads(payload)
```

**Impact:**
- If `STRIPE_WEBHOOK_SECRET` is not set, webhook signature verification is bypassed
- Attackers can forge webhook events
- Can activate subscriptions without payment
- Can cancel subscriptions
- Can manipulate subscription status

**Exploit Scenario:**
```python
# Attacker sends fake webhook
POST /api/subscription/webhook
Headers:
  Stripe-Signature: (ignored if secret not set)
Body:
{
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "metadata": {"user_id": "attacker_user_id"},
      "subscription": "sub_fake",
      "customer": "cus_fake"
    }
  }
}
# Attacker gets free premium access
```

**Fix:**
```python
# app/subscription_routes.py:309
@subscription_bp.route('/api/subscription/webhook', methods=['POST'])
def stripe_webhook():
    if not STRIPE_AVAILABLE:
        return jsonify({'error': 'Stripe is not installed'}), 500
    
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    
    if not webhook_secret:
        current_app.logger.error("STRIPE_WEBHOOK_SECRET not configured - rejecting webhook")
        return jsonify({'error': 'Webhook secret not configured'}), 500
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        current_app.logger.warning(f"Webhook signature verification failed: {e}")
        return jsonify({'error': 'Invalid signature'}), 400
    
    # ... rest of handler ...
```

**Quick Win:** 5 minutes

---

### CRIT-005: IDOR in Subscription Status Endpoint

**Severity:** Critical  
**OWASP Category:** A01:2021 – Broken Access Control  
**ASVS:** V4.1.1, V4.1.3  
**File:** `app/subscription_routes.py:54-108`

**Issue:**
```python
@subscription_bp.route('/api/subscription/status', methods=['POST'])
def get_subscription_status():
    data = request.get_json() if request.is_json else {}
    user_id = data.get('user_id')  # ← User-controlled!
    
    if not user_id:
        return jsonify({...}), 400
    
    subscription = storage.get_subscription_by_user_id(user_id)
    # Returns subscription for ANY user_id provided
```

**Impact:**
- Any authenticated user can query subscription status of any other user
- Leaks subscription information (plan, status, customer IDs)
- No authorization check to verify `user_id` matches `current_user.id`

**Exploit Scenario:**
```javascript
// Attacker can query any user's subscription
fetch('/api/subscription/status', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({user_id: 'victim_user_id'})
})
// Returns victim's subscription details
```

**Fix:**
```python
@subscription_bp.route('/api/subscription/status', methods=['POST'])
@login_required  # ← Add this decorator
def get_subscription_status():
    # Use current_user.id instead of user-provided user_id
    user_id = current_user.id  # ← Server-controlled
    
    subscription = storage.get_subscription_by_user_id(user_id)
    # ... rest of handler ...
```

**Quick Win:** 2 minutes

---

## 3. High Severity Findings

### HIGH-001: Missing Rate Limiting on Authentication Endpoints

**Severity:** High  
**OWASP Category:** A07:2021 – Identification and Authentication Failures  
**ASVS:** V2.1.4  
**Files:** `app/auth_routes.py:19-58, 61-100`

**Issue:**
- No rate limiting on `/login` or `/register`
- Brute force attacks possible
- Account enumeration via timing differences

**Impact:**
- Brute force password attacks
- Account enumeration
- DoS via registration spam

**Fix:**
```python
# Install: pip install flask-limiter

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # 5 attempts per minute
def login():
    # ... existing code ...
```

**Quick Win:** 30 minutes

---

### HIGH-002: Verbose Error Messages Expose Internal Details

**Severity:** High  
**OWASP Category:** A04:2021 – Security Logging and Monitoring Failures  
**ASVS:** V7.3.1  
**File:** `app/main.py:65-79`

**Issue:**
```python
@app.errorhandler(500)
def handle_500_error(e):
    if request.path.startswith('/api/'):
        import traceback
        error_details = str(e)
        if hasattr(e, 'original_exception'):
            error_details = str(e.original_exception)
        return jsonify({
            'success': False,
            'errors': [f'Internal server error: {error_details}']  # ← Exposes internals
        }), 500
```

**Impact:**
- Stack traces and exception details leaked to clients
- Reveals file paths, code structure, dependencies
- Aids attackers in crafting exploits

**Fix:**
```python
@app.errorhandler(500)
def handle_500_error(e):
    if request.path.startswith('/api/'):
        # Log full error server-side
        current_app.logger.error(f"500 error: {e}", exc_info=True)
        # Return generic message to client
        return jsonify({
            'success': False,
            'errors': ['An internal error occurred. Please try again later.']
        }), 500
    return e
```

**Quick Win:** 10 minutes

---

### HIGH-003: Insecure Session Cookie Configuration

**Severity:** High  
**OWASP Category:** A02:2021 – Cryptographic Failures  
**ASVS:** V3.1.1, V3.1.2  
**File:** `app/main.py:33-49`

**Issue:**
- No explicit session cookie security flags set
- Missing `HttpOnly`, `Secure`, `SameSite` attributes
- Session cookies may be accessible to JavaScript
- Vulnerable to XSS session theft

**Fix:**
```python
# app/main.py
def create_app():
    app = Flask(__name__)
    # ... existing config ...
    
    # Secure session cookies
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    
    # ... rest of setup ...
```

**Quick Win:** 5 minutes

---

### HIGH-004: Missing Security Headers

**Severity:** High  
**OWASP Category:** A05:2021 – Security Misconfiguration  
**ASVS:** V4.2.1, V4.2.2  
**File:** `app/main.py` (missing)

**Issue:**
- No Content Security Policy (CSP)
- No HSTS header
- No X-Frame-Options
- No X-Content-Type-Options
- Vulnerable to XSS, clickjacking, MIME sniffing

**Fix:**
```python
# Install: pip install flask-talisman

from flask_talisman import Talisman

def create_app():
    app = Flask(__name__)
    # ... existing config ...
    
    Talisman(
        app,
        force_https=False,  # Set True in production with HTTPS
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,
        content_security_policy={
            'default-src': "'self'",
            'script-src': "'self' https://cdn.tailwindcss.com",
            'style-src': "'self' 'unsafe-inline' https://cdn.tailwindcss.com",
            'img-src': "'self' data: https:",
            'font-src': "'self' data:",
        },
        frame_options='DENY',
        content_type_nosniff=True,
        referrer_policy='strict-origin-when-cross-origin'
    )
    
    # ... rest of setup ...
```

**Quick Win:** 15 minutes

---

### HIGH-005: File Upload Validation Insufficient

**Severity:** High  
**OWASP Category:** A03:2021 – Injection  
**ASVS:** V8.3.1, V8.3.2  
**File:** `app/routes.py:1583-1629`

**Issue:**
```python
# Only checks extension, not file content
allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
filename = secure_filename(file.filename)
if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
    return jsonify({'success': False, 'errors': ['Invalid file type']}), 400

file.save(filepath)  # ← No content validation
```

**Problems:**
1. Extension-based validation can be bypassed (double extension: `photo.jpg.php`)
2. No MIME type validation
3. No file content scanning
4. No virus/malware scanning
5. Files saved with predictable names

**Impact:**
- Malicious file uploads possible
- If files are served, could execute code
- Storage exhaustion attacks

**Fix:**
```python
import magic  # python-magic
from PIL import Image

@bp.route('/api/upload-photo', methods=['POST'])
@login_required
def upload_photo():
    # ... existing checks ...
    
    # Validate MIME type
    file_content = file.read()
    file.seek(0)  # Reset for save
    
    mime_type = magic.from_buffer(file_content, mime=True)
    allowed_mimes = {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}
    if mime_type not in allowed_mimes:
        return jsonify({'success': False, 'errors': ['Invalid file type']}), 400
    
    # Validate image can be opened
    try:
        img = Image.open(file)
        img.verify()
        file.seek(0)  # Reset again
    except Exception:
        return jsonify({'success': False, 'errors': ['Invalid image file']}), 400
    
    # Use secure random filename
    import secrets
    ext = filename.rsplit('.', 1)[1].lower()
    new_filename = f"player_photo_{secrets.token_hex(16)}.{ext}"
    
    # ... rest of handler ...
```

**Quick Win:** 1 hour (install dependencies + implement)

---

### HIGH-006: ZIP Bomb Vulnerability in Import Endpoint

**Severity:** High  
**OWASP Category:** A03:2021 – Injection  
**ASVS:** V8.3.1  
**File:** `app/routes.py:841-938`

**Issue:**
```python
with zipfile.ZipFile(temp_file.name, 'r') as zip_file:
    matches_data = json.loads(zip_file.read('matches.json').decode('utf-8'))
    # ... reads multiple files without size checks
```

**Problems:**
1. No check on uncompressed size
2. ZIP bomb attacks possible (small compressed file, huge uncompressed)
3. Memory exhaustion possible
4. No limit on number of files in ZIP

**Impact:**
- DoS via memory exhaustion
- Server crash
- Resource exhaustion

**Fix:**
```python
MAX_UNCOMPRESSED_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES_IN_ZIP = 100

with zipfile.ZipFile(temp_file.name, 'r') as zip_file:
    # Check number of files
    file_list = zip_file.namelist()
    if len(file_list) > MAX_FILES_IN_ZIP:
        return jsonify({'success': False, 'errors': ['Too many files in archive']}), 400
    
    # Check uncompressed size
    total_size = sum(zip_file.getinfo(f).file_size for f in file_list)
    if total_size > MAX_UNCOMPRESSED_SIZE:
        return jsonify({'success': False, 'errors': ['Archive too large']}), 400
    
    # Read files with size limits
    matches_data = json.loads(
        zip_file.read('matches.json', pwd=None)[:10*1024*1024].decode('utf-8')  # 10MB limit per file
    )
```

**Quick Win:** 30 minutes

---

### HIGH-007: Excel Import Code Injection Risk

**Severity:** High  
**OWASP Category:** A03:2021 – Injection  
**ASVS:** V5.1.1  
**File:** `app/routes.py:1040-1200`

**Issue:**
```python
workbook = openpyxl.load_workbook(temp_file.name)  # ← No validation
sheet = workbook.active
# Processes cell values directly without sanitization
```

**Problems:**
1. Excel files can contain formulas that execute
2. No validation of cell content
3. Data processed directly into JSON/database
4. Potential for formula injection

**Impact:**
- Formula injection if data is exported to other Excel files
- Data corruption
- Potential code execution if formulas are evaluated

**Fix:**
```python
# Load workbook in data-only mode
workbook = openpyxl.load_workbook(temp_file.name, data_only=True)

# Sanitize all cell values
def sanitize_cell_value(cell_value):
    if cell_value is None:
        return None
    # Convert to string and strip
    value = str(cell_value).strip()
    # Remove formula indicators
    if value.startswith('='):
        return None  # Reject formulas
    return value

# Apply sanitization when reading cells
for row in sheet.iter_rows(values_only=True):
    sanitized_row = [sanitize_cell_value(cell) for cell in row]
    # ... process sanitized_row ...
```

**Quick Win:** 30 minutes

---

### HIGH-008: Missing Input Length Validation

**Severity:** High  
**OWASP Category:** A03:2021 – Injection  
**ASVS:** V5.1.1  
**Files:** Multiple endpoints

**Issue:**
- No maximum length validation on text inputs
- Username, email, notes, opponent, location fields unlimited
- Potential for DoS via large payloads

**Affected Fields:**
- Username (models.py:427-436) - only min length checked
- Email - no validation
- Match notes, opponent, location
- All text fields in models

**Impact:**
- DoS via large payloads
- Memory exhaustion
- Database/file storage exhaustion

**Fix:**
```python
# app/models.py
class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)  # ← Add max
    email: Optional[str] = Field(None, max_length=255)  # ← Add max

class Match(BaseModel):
    opponent: str = Field(..., max_length=200)  # ← Add max
    location: str = Field(..., max_length=200)  # ← Add max
    notes: str = Field("", max_length=5000)  # ← Add max
```

**Quick Win:** 1 hour (update all models)

---

## 4. Medium Severity Findings

### MED-001: Weak Password Policy

**Severity:** Medium  
**OWASP Category:** A07:2021 – Identification and Authentication Failures  
**ASVS:** V2.1.1  
**File:** `app/auth_routes.py:77`

**Issue:**
```python
if len(password) < 6:
    return jsonify({'success': False, 'errors': ['Password must be at least 6 characters']}), 400
```

**Problems:**
- Minimum length only 6 characters (too weak)
- No complexity requirements
- No password strength meter
- No password history/reuse prevention

**Fix:**
```python
import re

def validate_password_strength(password):
    errors = []
    if len(password) < 12:
        errors.append('Password must be at least 12 characters')
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter')
    if not re.search(r'\d', password):
        errors.append('Password must contain at least one number')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Password must contain at least one special character')
    return errors
```

**Quick Win:** 30 minutes

---

### MED-002: Information Disclosure in Error Messages

**Severity:** Medium  
**OWASP Category:** A04:2021 – Security Logging and Monitoring Failures  
**Files:** Multiple endpoints

**Issue:**
- Error messages reveal whether username exists
- Timing differences allow account enumeration
- Different error messages for invalid username vs invalid password

**File:** `app/auth_routes.py:35-47`

**Fix:**
```python
# Always return same error message and timing
user = storage.get_user_by_username(username)
if not user:
    # Simulate password check to prevent timing attacks
    check_password_hash("$2b$12$dummy", "dummy")
    time.sleep(0.1)  # Add small delay
    return jsonify({'success': False, 'errors': ['Invalid username or password']}), 401

if not storage.verify_password(user, password):
    return jsonify({'success': False, 'errors': ['Invalid username or password']}), 401
```

**Quick Win:** 15 minutes

---

### MED-003: Missing Audit Logging

**Severity:** Medium  
**OWASP Category:** A09:2021 – Security Logging and Monitoring Failures  
**ASVS:** V7.3.1  
**Files:** All state-changing endpoints

**Issue:**
- No logging of security-relevant events
- No audit trail for:
  - Login attempts (success/failure)
  - Password changes
  - Data modifications
  - File uploads
  - Subscription changes

**Fix:**
```python
import logging
security_logger = logging.getLogger('security')

@auth_bp.route('/login', methods=['POST'])
def login():
    username = data.get('username', '').strip()
    # ... existing code ...
    
    if not user or not storage.verify_password(user, password):
        security_logger.warning(f"Failed login attempt for username: {username}, IP: {request.remote_addr}")
        return jsonify({'success': False, 'errors': ['Invalid username or password']}), 401
    
    security_logger.info(f"Successful login for user: {user.id}, username: {username}, IP: {request.remote_addr}")
    # ... rest of handler ...
```

**Quick Win:** 2 hours (add logging to all critical endpoints)

---

### MED-004: Session Fixation Vulnerability

**Severity:** Medium  
**OWASP Category:** A01:2021 – Broken Access Control  
**ASVS:** V3.1.3  
**File:** `app/auth_routes.py:50-51`

**Issue:**
```python
login_user(user_session, remember=True)  # ← Doesn't regenerate session ID
```

**Impact:**
- If attacker can set session ID before login, they maintain access after victim logs in
- Session ID not regenerated on login

**Fix:**
```python
from flask import session

login_user(user_session, remember=True)
session.permanent = True
# Regenerate session ID on login
session.regenerate()
```

**Quick Win:** 5 minutes

---

### MED-005: Missing Content-Type Validation

**Severity:** Medium  
**OWASP Category:** A03:2021 – Injection  
**Files:** All JSON endpoints

**Issue:**
- Endpoints accept JSON but don't validate Content-Type header
- Potential for request smuggling
- MIME confusion attacks

**Fix:**
```python
from functools import wraps

def require_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'success': False, 'errors': ['Content-Type must be application/json']}), 400
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/matches', methods=['POST'])
@login_required
@require_json  # ← Add this
def create_match():
    # ... existing code ...
```

**Quick Win:** 30 minutes

---

### MED-006: Predictable Resource IDs

**Severity:** Medium  
**OWASP Category:** A01:2021 – Broken Access Control  
**ASVS:** V4.1.1  
**File:** `app/models.py:20, 145, 171, etc.`

**Issue:**
```python
id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
```

**Problems:**
1. IDs are predictable (timestamp-based)
2. Easy to enumerate resources
3. Makes IDOR attacks easier

**Impact:**
- Resource enumeration
- Easier IDOR exploitation

**Fix:**
```python
import secrets

id: str = Field(default_factory=lambda: secrets.token_urlsafe(16))
```

**Quick Win:** 1 hour (update all models + migration)

---

### MED-007: Missing Output Encoding

**Severity:** Medium  
**OWASP Category:** A03:2021 – Injection  
**ASVS:** V5.2.1  
**Files:** Templates (needs verification)

**Issue:**
- Need to verify all template variables are properly escaped
- Jinja2 auto-escapes by default, but need to verify no `|safe` filters on user input

**Status:** Needs manual template review

**Fix:**
- Ensure all user-controlled data in templates uses `{{ variable }}` (auto-escaped)
- Never use `{{ variable|safe }}` with user input
- Use `|escape` explicitly if needed

**Quick Win:** 1 hour (template audit)

---

## 5. Low Severity Findings

### LOW-001: Missing HSTS Preload

**Severity:** Low  
**OWASP Category:** A05:2021 – Security Misconfiguration  
**File:** Security headers implementation

**Issue:**
- HSTS header present but not configured for preload
- Missing `includeSubDomains` and `preload` directives

**Fix:**
```python
Talisman(
    app,
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,
    strict_transport_security_include_subdomains=True,
    strict_transport_security_preload=True
)
```

**Quick Win:** 5 minutes

---

### LOW-002: Debug Mode Configuration

**Severity:** Low  
**OWASP Category:** A05:2021 – Security Misconfiguration  
**File:** `app/main.py:42`

**Issue:**
```python
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Should be False in production
```

**Fix:**
```python
app.config['TEMPLATES_AUTO_RELOAD'] = os.environ.get('FLASK_ENV') != 'production'
```

**Quick Win:** 2 minutes

---

### LOW-003: Missing Dependency Pinning

**Severity:** Low  
**OWASP Category:** A06:2021 – Vulnerable and Outdated Components  
**File:** `requirements.txt`

**Issue:**
```txt
Flask>=2.0.0  # ← Should pin exact versions
flask-login>=0.6.0
```

**Problems:**
- Unpinned versions can pull in vulnerable updates
- No version lock file
- Difficult to reproduce builds

**Fix:**
```txt
Flask==2.3.3
flask-login==0.6.3
# ... pin all dependencies ...
```

Then use `pip freeze > requirements.txt` to generate exact versions.

**Quick Win:** 30 minutes

---

## 6. Hardening Checklist

### Immediate Actions (1 Hour)

- [ ] **CRIT-001:** Remove default SECRET_KEY, require environment variable
- [ ] **CRIT-004:** Require STRIPE_WEBHOOK_SECRET, reject webhooks without it
- [ ] **CRIT-005:** Fix IDOR in subscription status endpoint
- [ ] **HIGH-003:** Configure secure session cookies (HttpOnly, Secure, SameSite)
- [ ] **HIGH-002:** Sanitize error messages in production

### Short-term (1 Day)

- [ ] **CRIT-002:** Implement CSRF protection (Flask-WTF)
- [ ] **CRIT-003:** Remove client-side password hashing
- [ ] **HIGH-001:** Add rate limiting to auth endpoints
- [ ] **HIGH-004:** Implement security headers (Flask-Talisman)
- [ ] **HIGH-005:** Improve file upload validation (MIME type, content scanning)
- [ ] **HIGH-006:** Add ZIP bomb protection
- [ ] **HIGH-007:** Sanitize Excel import data
- [ ] **HIGH-008:** Add input length validation to all models

### Medium-term (1 Week)

- [ ] **MED-001:** Strengthen password policy
- [ ] **MED-002:** Fix account enumeration via error messages
- [ ] **MED-003:** Implement audit logging
- [ ] **MED-004:** Fix session fixation
- [ ] **MED-005:** Add Content-Type validation
- [ ] **MED-006:** Use unpredictable resource IDs
- [ ] **MED-007:** Audit template output encoding

### Long-term (1 Month)

- [ ] **LOW-001:** Configure HSTS preload
- [ ] **LOW-002:** Fix debug mode configuration
- [ ] **LOW-003:** Pin all dependencies
- [ ] Set up automated dependency scanning (e.g., Dependabot, Snyk)
- [ ] Implement CI/CD security checks (SAST, secret scanning)
- [ ] Set up security monitoring and alerting
- [ ] Conduct penetration testing
- [ ] Implement WAF rules if using reverse proxy

---

## 7. Most Likely Real-World Attack Paths

### Attack Path 1: Session Hijacking via Default SECRET_KEY

**Entry Point:** Application deployed without SECRET_KEY environment variable

**Steps:**
1. Attacker discovers default SECRET_KEY in code or error messages
2. Attacker generates valid session cookie for any user_id
3. Attacker accesses victim's account
4. Attacker modifies/deletes data, changes subscription status

**Impact:** Complete account takeover, data loss, financial fraud

**Mitigation:** CRIT-001 fix

---

### Attack Path 2: CSRF + IDOR Chain

**Entry Point:** Victim visits attacker's website while logged in

**Steps:**
1. Attacker crafts CSRF form targeting `/matches` endpoint
2. Form includes match_id of victim's match
3. Victim's browser automatically submits form with session cookie
4. Attacker deletes/modifies victim's matches
5. Attacker uses IDOR to query victim's subscription status
6. Attacker manipulates subscription via CSRF

**Impact:** Data loss, subscription fraud, service disruption

**Mitigation:** CRIT-002 (CSRF) + CRIT-005 (IDOR) fixes

---

### Attack Path 3: Webhook Forgery → Free Premium Access

**Entry Point:** STRIPE_WEBHOOK_SECRET not configured

**Steps:**
1. Attacker discovers webhook endpoint doesn't verify signatures
2. Attacker crafts fake `checkout.session.completed` webhook
3. Attacker includes their user_id in metadata
4. Server processes webhook and activates subscription
5. Attacker gains premium features without payment

**Impact:** Revenue loss, service abuse, unfair advantage

**Mitigation:** CRIT-004 fix

---

## 8. Recommendations Summary

### Priority 1 (Critical - Fix Immediately)
1. Remove default SECRET_KEY
2. Implement CSRF protection
3. Remove client-side password hashing
4. Fix Stripe webhook signature verification
5. Fix IDOR in subscription endpoint

### Priority 2 (High - Fix This Week)
1. Add rate limiting
2. Secure session cookies
3. Implement security headers
4. Improve file upload validation
5. Add ZIP bomb protection
6. Sanitize Excel imports
7. Add input length validation
8. Sanitize error messages

### Priority 3 (Medium - Fix This Month)
1. Strengthen password policy
2. Fix account enumeration
3. Add audit logging
4. Fix session fixation
5. Add Content-Type validation
6. Use unpredictable IDs
7. Audit template encoding

### Priority 4 (Low - Fix When Possible)
1. Configure HSTS preload
2. Fix debug mode
3. Pin dependencies

---

## Appendix: Testing Commands

### Test CSRF Protection
```bash
# Should fail without CSRF token
curl -X POST http://localhost:8080/matches \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"category":"League","date":"01 Jan 2025","opponent":"Test"}'
```

### Test Rate Limiting
```bash
# Should block after 5 attempts
for i in {1..10}; do
  curl -X POST http://localhost:8080/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"wrong"}'
done
```

### Test IDOR
```bash
# Should fail - can't access other user's subscription
curl -X POST http://localhost:8080/api/subscription/status \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{"user_id":"other_user_id"}'
```

---

**Report End**

