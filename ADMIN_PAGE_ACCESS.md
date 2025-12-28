# Admin Page Access Guide

## How to Access the Admin Page

### URL
Navigate to: **`/admin/users`**

Example:
- Local: `http://localhost:8080/admin/users`
- Production: `https://yourdomain.com/admin/users`

### Requirements

1. **Must be logged in** - You need to be authenticated to access the admin page
2. **Optional: Admin Username Restriction** - You can restrict access to only a specific admin user

### Setting Up Admin Access Restriction (Optional)

To restrict admin access to only your username:

1. Add to your `.env` file:
```bash
ADMIN_USERNAME=your-admin-username
```

2. Replace `your-admin-username` with your actual FutureElite username

3. Restart the server

**Note:** If `ADMIN_USERNAME` is not set, any logged-in user can access the admin page. It's recommended to set this in production.

## What the Admin Page Shows

The admin page displays a table with the following information for each registered user:

| Column | Description |
|--------|-------------|
| **Username** | The user's login username (with avatar) |
| **Email** | User's email address (if provided) |
| **Login** | Same as username (for reference) |
| **Password** | Shows "Hashed (secure) - Cannot display" |
| **Subscription Status** | Current subscription status (Active, Free, Canceled, etc.) and plan name |
| **Account Status** | Whether the account is Active or Inactive |
| **Registered** | Registration date |

### Subscription Status Values

- **Active** (green badge) - User has an active paid subscription
- **Free** (gray badge) - User is on the free tier
- **Canceled** (yellow badge) - Subscription was canceled
- **Past Due** (orange badge) - Payment is past due
- Other statuses as applicable

### Password Security Note

**Passwords cannot be displayed** - This is a security best practice. Passwords are:
- Hashed using secure algorithms (bcrypt)
- Never stored in plain text
- Cannot be retrieved or displayed
- This protects user accounts even if the database is compromised

If you need to reset a user's password, you would need to implement a password reset feature (not currently available in the admin panel).

## Features

### Export Users
- Click "Export Users (JSON)" to download all user data as a JSON file
- Includes all user information except password hashes

### Refresh
- Click "Refresh" to reload the page and see the latest user registrations

## API Endpoint

You can also access user data programmatically:

**Endpoint:** `GET /api/admin/users`

**Authentication:** Must be logged in (and match ADMIN_USERNAME if set)

**Response:**
```json
{
  "success": true,
  "users": [
    {
      "id": "user_123",
      "username": "example_user",
      "email": "user@example.com",
      "created_at": "15 Jan 2025",
      "is_active": true,
      "subscription_status": "active",
      "subscription_plan": "Monthly"
    }
  ],
  "total": 1
}
```

## Troubleshooting

### "Access denied" Error
- Make sure you're logged in
- If `ADMIN_USERNAME` is set, ensure you're logged in with that exact username
- Check that `ADMIN_USERNAME` in your `.env` matches your actual username exactly

### No Users Showing
- This is normal if no users have registered yet
- Check that the server is running and connected to the correct data directory

### Subscription Status Not Showing
- Subscription data is loaded from `data/subscriptions.json`
- If a user doesn't have a subscription record, it will show as "Free" (none)

