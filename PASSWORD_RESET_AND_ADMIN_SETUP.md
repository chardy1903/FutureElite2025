# Password Reset & Admin Setup

## Password Reset Feature

### Overview
Users can now reset their password if they forget it and cannot log in.

### How It Works

1. **Forgot Password Page** (`/forgot-password`)
   - User enters their email address or username
   - System generates a secure reset token (valid for 1 hour)
   - If email is configured, reset link is sent via email
   - If email is not configured, reset link is logged in server logs for admin to share manually

2. **Reset Password Page** (`/reset-password/<token>`)
   - User clicks the reset link (from email or admin-provided link)
   - User enters new password (minimum 8 characters)
   - Password is updated and token is deleted
   - User is redirected to login page

### Access Points

- **Login Page**: "Forgot your password?" link at the bottom
- **Direct URL**: `/forgot-password`

### Email Configuration (Optional)

If SMTP is configured in `.env`, reset links will be sent via email:
```bash
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

If email is not configured, the reset link will be logged in the server logs. Check logs for:
```
PASSWORD RESET REQUEST for user: <username>
Reset URL: http://yourdomain.com/reset-password/<token>
Token expires in 1 hour.
```

### Security Features

- Reset tokens expire after 1 hour
- Tokens are single-use (deleted after password reset)
- Tokens are cryptographically secure (32-byte random tokens)
- Rate limiting: 5 requests per hour for forgot password, 10 per hour for reset
- Does not reveal if email/username exists (security best practice)

## Admin User Setup

### Admin Credentials

**Username:** `Admin_Chris1903_FutureElite`  
**Password:** `bBrodie@x2027`

### Access

1. **Login**: Go to `/login` and use the admin credentials above
2. **Admin Page**: After logging in, go to `/admin/users` to view all registered users

### Admin Page Features

The admin page shows:
- Username
- Email
- Login (username)
- Password status (hashed, cannot be displayed)
- Subscription status (Active, Free, Canceled, etc.)
- Account status (Active/Inactive)
- Registration date

### Environment Variable

The `.env` file has been updated with:
```bash
ADMIN_USERNAME=Admin_Chris1903_FutureElite
```

This restricts admin page access to only this user (if set). If not set, any logged-in user can access the admin page.

### Creating/Updating Admin User

To create or update the admin user, run:
```bash
python create_admin_user.py
```

This script will:
- Create the admin user if it doesn't exist
- Update the password if the user already exists
- Update the `.env` file with `ADMIN_USERNAME`

## Files Modified/Created

### New Files
- `app/templates/forgot_password.html` - Forgot password page
- `app/templates/reset_password.html` - Reset password page
- `create_admin_user.py` - Script to create/update admin user
- `PASSWORD_RESET_AND_ADMIN_SETUP.md` - This documentation

### Modified Files
- `app/auth_routes.py` - Added forgot/reset password routes
- `app/storage.py` - Added password reset token management methods
- `app/templates/login.html` - Added "Forgot password?" link
- `.env` - Added `ADMIN_USERNAME` setting

## Testing

### Test Password Reset

1. Go to `/login`
2. Click "Forgot your password?"
3. Enter your username or email
4. Check server logs for reset link (if email not configured)
5. Click the reset link
6. Enter new password
7. Log in with new password

### Test Admin Access

1. Go to `/login`
2. Log in with:
   - Username: `Admin_Chris1903_FutureElite`
   - Password: `bBrodie@x2027`
3. Navigate to `/admin/users`
4. Verify you can see all registered users

## Notes

- Passwords are hashed and cannot be retrieved or displayed (security best practice)
- Reset tokens are stored in `data/reset_tokens.json`
- Tokens are automatically cleaned up when expired
- If a user doesn't have an email address, the reset link will only be in server logs

