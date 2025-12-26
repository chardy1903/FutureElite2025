# Security Quick Fixes - Priority Order

## 🔴 CRITICAL - Fix Immediately (5-30 minutes each)

### 1. Fix Default SECRET_KEY (5 min)
**File:** `app/main.py:39`

```python
# BEFORE:
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'futureelite-2025-dev-only')

# AFTER:
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise RuntimeError(
        "SECRET_KEY environment variable must be set in production. "
        "Generate with: python -c 'import secrets; print(secrets.token_hex(32))'"
    )
app.config['SECRET_KEY'] = secret_key
```

---

### 2. Fix Subscription IDOR (2 min)
**File:** `app/subscription_routes.py:54`

```python
# BEFORE:
@subscription_bp.route('/api/subscription/status', methods=['POST'])
def get_subscription_status():
    data = request.get_json() if request.is_json else {}
    user_id = data.get('user_id')  # ← User-controlled!

# AFTER:
@subscription_bp.route('/api/subscription/status', methods=['POST'])
@login_required  # ← Add this
def get_subscription_status():
    user_id = current_user.id  # ← Server-controlled
    # Remove: data = request.get_json()...
```

---

### 3. Fix Stripe Webhook Bypass (5 min)
**File:** `app/subscription_routes.py:319-326`

```python
# BEFORE:
if webhook_secret:
    event = stripe.Webhook.construct_event(...)
else:
    event = json.loads(payload)  # ← Bypass!

# AFTER:
if not webhook_secret:
    current_app.logger.error("STRIPE_WEBHOOK_SECRET not configured - rejecting webhook")
    return jsonify({'error': 'Webhook secret not configured'}), 500

try:
    event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
except stripe.error.SignatureVerificationError as e:
    current_app.logger.warning(f"Webhook signature verification failed: {e}")
    return jsonify({'error': 'Invalid signature'}), 400
```

---

### 4. Secure Session Cookies (5 min)
**File:** `app/main.py` (add after line 42)

```python
# Add after app.config settings:
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # Set False for localhost development
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
```

Add import: `from datetime import timedelta`

---

### 5. Sanitize Error Messages (10 min)
**File:** `app/main.py:65-79`

```python
# BEFORE:
return jsonify({
    'success': False,
    'errors': [f'Internal server error: {error_details}']  # ← Exposes internals
}), 500

# AFTER:
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

---

## 🟠 HIGH - Fix This Week (15-60 minutes each)

### 6. Add CSRF Protection (1 hour)
**Install:** `pip install flask-wtf`

**File:** `app/main.py`

```python
from flask_wtf.csrf import CSRFProtect

def create_app():
    app = Flask(__name__)
    # ... existing config ...
    csrf = CSRFProtect(app)
    # ... rest of setup ...
```

**File:** Templates - Add to all forms:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
```

**File:** API endpoints - Add header validation:
```python
from flask_wtf.csrf import validate_csrf

@bp.route('/matches', methods=['POST'])
@login_required
def create_match():
    # For JSON APIs, validate CSRF token from header
    csrf_token = request.headers.get('X-CSRFToken')
    if not csrf_token or not validate_csrf(csrf_token):
        return jsonify({'success': False, 'errors': ['Invalid CSRF token']}), 403
    # ... rest of handler ...
```

---

### 7. Remove Client-Side Password Hashing (30 min)
**File:** `app/static/js/storage.js:518-530` - DELETE these functions

**File:** `app/static/js/auth.js` - Update to send plain password:

```javascript
// BEFORE:
const passwordHash = await clientStorage.hashPassword(password);
// Send passwordHash to server

// AFTER:
// Send plain password to server (over HTTPS)
async login(username, password) {
    const response = await fetch('/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})  // ← Plain password
    });
    // Server handles hashing
}
```

**Note:** Server-side hashing in `app/storage.py:794` is already correct (uses werkzeug scrypt).

---

### 8. Add Rate Limiting (30 min)
**Install:** `pip install flask-limiter`

**File:** `app/main.py`

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def create_app():
    app = Flask(__name__)
    # ... existing config ...
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    # ... rest of setup ...
```

**File:** `app/auth_routes.py`

```python
from flask_limiter import limiter

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # ← Add this
def login():
    # ... existing code ...
```

---

### 9. Add Security Headers (15 min)
**Install:** `pip install flask-talisman`

**File:** `app/main.py`

```python
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

---

### 10. Improve File Upload Validation (1 hour)
**Install:** `pip install python-magic Pillow`

**File:** `app/routes.py:1583-1629`

```python
import magic
from PIL import Image
import secrets

@bp.route('/api/upload-photo', methods=['POST'])
@login_required
def upload_photo():
    # ... existing checks ...
    
    # Read file content for MIME validation
    file_content = file.read()
    file.seek(0)  # Reset for save
    
    # Validate MIME type
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
    ext = filename.rsplit('.', 1)[1].lower()
    new_filename = f"player_photo_{secrets.token_hex(16)}.{ext}"  # ← Random, not timestamp
    
    # ... rest of handler ...
```

---

### 11. Add ZIP Bomb Protection (30 min)
**File:** `app/routes.py:871`

```python
MAX_UNCOMPRESSED_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES_IN_ZIP = 100
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file

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
    matches_json = zip_file.read('matches.json')[:MAX_FILE_SIZE].decode('utf-8')
    matches_data = json.loads(matches_json)
    # ... repeat for other files ...
```

---

### 12. Add Input Length Validation (1 hour)
**File:** `app/models.py` - Update all string fields:

```python
# User model
class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)  # ← Add max
    email: Optional[str] = Field(None, max_length=255)  # ← Add max

# Match model
class Match(BaseModel):
    opponent: str = Field(..., max_length=200)  # ← Add max
    location: str = Field(..., max_length=200)  # ← Add max
    notes: str = Field("", max_length=5000)  # ← Add max

# Repeat for all models with string fields
```

---

## 🟡 MEDIUM - Fix This Month

### 13. Strengthen Password Policy (30 min)
**File:** `app/auth_routes.py:77`

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

# In register() function:
password_errors = validate_password_strength(password)
if password_errors:
    return jsonify({'success': False, 'errors': password_errors}), 400
```

---

### 14. Fix Account Enumeration (15 min)
**File:** `app/auth_routes.py:35-47`

```python
import time
from werkzeug.security import check_password_hash

# Always perform same operations regardless of user existence
user = storage.get_user_by_username(username)
dummy_hash = "$2b$12$dummyhash"  # Dummy hash for timing

if not user:
    # Simulate password check to prevent timing attacks
    check_password_hash(dummy_hash, password)
    time.sleep(0.1)  # Add small delay
    return jsonify({'success': False, 'errors': ['Invalid username or password']}), 401

if not storage.verify_password(user, password):
    return jsonify({'success': False, 'errors': ['Invalid username or password']}), 401
```

---

### 15. Fix Session Fixation (5 min)
**File:** `app/auth_routes.py:50-51`

```python
from flask import session

login_user(user_session, remember=True)
session.permanent = True
session.regenerate()  # ← Regenerate session ID on login
```

---

## Testing Checklist

After applying fixes, test:

- [ ] SECRET_KEY required - app fails to start without it
- [ ] Subscription status requires authentication
- [ ] Webhook rejects requests without valid signature
- [ ] Session cookies have HttpOnly, Secure, SameSite flags
- [ ] Error messages don't expose stack traces
- [ ] CSRF tokens required for POST/PUT/DELETE
- [ ] Rate limiting blocks after 5 login attempts
- [ ] Security headers present (CSP, HSTS, etc.)
- [ ] File uploads validate MIME type
- [ ] ZIP imports check uncompressed size
- [ ] Input length limits enforced

---

## Environment Variables Required

Create `.env` file with:

```bash
# Required
SECRET_KEY=<generate with: python -c 'import secrets; print(secrets.token_hex(32))'>

# Stripe (if using)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_MONTHLY_PRICE_ID=price_...
STRIPE_ANNUAL_PRICE_ID=price_...

# Optional
FLASK_ENV=production
```

---

**Total Time Estimate:**
- Critical fixes: ~30 minutes
- High priority fixes: ~5 hours
- Medium priority fixes: ~2 hours
- **Total: ~8 hours for all fixes**

