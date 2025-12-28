# User Signup Notifications & Management

This document explains how to get notified and manage user registrations in FutureElite.

## Options for Getting Notified

### 1. Email Notifications (Recommended)

When a new user registers, you can receive an email notification.

**Setup:**
1. Add these environment variables to your `.env` file or hosting platform:

```bash
SMTP_ENABLED=true
ADMIN_EMAIL=your-email@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**For Gmail:**
- Use an [App Password](https://support.google.com/accounts/answer/185833) (not your regular password)
- Enable 2-factor authentication first
- Generate app password: Google Account → Security → App passwords

**For other email providers:**
- Gmail: `smtp.gmail.com:587`
- Outlook: `smtp-mail.outlook.com:587`
- Yahoo: `smtp.mail.yahoo.com:587`
- Custom SMTP: Check your provider's documentation

**What you'll receive:**
- Email subject: "New User Registration: [username]"
- Includes: username, email (if provided), user ID, registration date
- Link to admin panel to view all users

### 2. Admin Dashboard (Web Interface)

View all registered users in a web interface.

**Access:**
- URL: `https://futureelite.co.uk/admin/users`
- Requires: You must be logged in
- Optional: Set `ADMIN_USERNAME` environment variable to restrict access to only that user

**Features:**
- View all registered users
- See username, email, registration date
- Export users to JSON file
- Refresh to see latest registrations

**Setup:**
Add to `.env` (optional - restricts admin access):
```bash
ADMIN_USERNAME=your-admin-username
```

### 3. API Endpoint (Programmatic Access)

Get user list as JSON via API.

**Endpoint:**
- `GET /api/admin/users`
- Returns: JSON with all users (password hashes excluded)

**Example response:**
```json
{
  "success": true,
  "users": [
    {
      "id": "20251115_221430",
      "username": "Brodie_Baller",
      "email": null,
      "created_at": "15 Nov 2025",
      "is_active": true
    }
  ],
  "total": 1
}
```

### 4. Command-Line Export Script

Export all users to a JSON file from the command line.

**Usage:**
```bash
python export_users.py [output_file.json]
```

**Example:**
```bash
python export_users.py users_backup.json
```

This will:
- Export all users to a JSON file
- Remove password hashes for security
- Display summary in terminal
- Sort by registration date (newest first)

### 5. Server Logs

All new registrations are logged to the application logs.

**Log format:**
```
NEW USER REGISTRATION: username=chris1903, email=chris@example.com, user_id=20251115_222002, created_at=15 Nov 2025
```

**Where to find:**
- Local development: Console output
- Production: Check your hosting platform's logs (Render, Heroku, etc.)

## Quick Start

### Option A: Just View Users (No Setup Required)
1. Log in to your app
2. Visit: `https://futureelite.co.uk/admin/users`
3. View and export users

### Option B: Email Notifications
1. Set up SMTP credentials in environment variables
2. Set `SMTP_ENABLED=true`
3. Receive email when each new user registers

### Option C: Export via Script
1. Run: `python export_users.py`
2. Get JSON file with all users

## Security Notes

- Password hashes are **never** included in exports or admin views
- Admin routes require authentication
- Set `ADMIN_USERNAME` to restrict admin access to specific user
- Email notifications are optional and won't break registration if they fail

## Troubleshooting

**Email notifications not working:**
- Check SMTP credentials are correct
- Verify `SMTP_ENABLED=true`
- Check application logs for SMTP errors
- For Gmail, ensure you're using an App Password, not regular password

**Can't access admin page:**
- Make sure you're logged in
- If `ADMIN_USERNAME` is set, you must be that user
- Check application logs for errors

**Export script fails:**
- Ensure you're in the project root directory
- Check that `data/users.json` exists
- Verify Python can import the app modules

