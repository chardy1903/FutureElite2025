# SMTP Email Setup for Render (Office 365/GoDaddy)

This guide explains how to configure SMTP email sending in your Render production environment so the contact form can send emails directly.

## Why This Is Needed

The contact form currently falls back to opening your email client (mailto link) because SMTP is not configured in production. Once SMTP is configured, the contact form will send emails directly from the website without requiring users to open their email client.

## Office 365/GoDaddy SMTP Settings

For Office 365 email (through GoDaddy), use these settings:

### Required Environment Variables

Add these environment variables in your Render dashboard:

1. **Enable SMTP:**
   ```
   SMTP_ENABLED=true
   ```

2. **SMTP Server Settings:**
   ```
   SMTP_HOST=smtp.office365.com
   SMTP_PORT=587
   ```

3. **Email Credentials:**
   ```
   SMTP_USER=admin@futureelite.pro
   SMTP_PASSWORD=your-email-password
   ```

4. **Email Addresses:**
   ```
   FROM_EMAIL=admin@futureelite.pro
   ADMIN_EMAIL=support@futureelite.pro
   ```

   **Note:** 
   - `FROM_EMAIL` is the "From" address in sent emails
   - `ADMIN_EMAIL` is where contact form submissions are sent
   - Both can be the same email address

## How to Add Environment Variables in Render

1. **Go to your Render Dashboard:**
   - Navigate to your web service (FutureElite)

2. **Open Environment Tab:**
   - Click on "Environment" in the left sidebar

3. **Add Each Variable:**
   - Click "Add Environment Variable"
   - Enter the variable name (e.g., `SMTP_ENABLED`)
   - Enter the value (e.g., `true`)
   - Click "Save Changes"
   - Repeat for each variable

4. **Redeploy:**
   - After adding all variables, Render will automatically redeploy
   - Or manually trigger a redeploy from the "Manual Deploy" section

## Complete Environment Variables List

Here's the complete list to add (copy and paste each one):

```
SMTP_ENABLED=true
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=admin@futureelite.pro
SMTP_PASSWORD=your-actual-password-here
FROM_EMAIL=admin@futureelite.pro
ADMIN_EMAIL=support@futureelite.pro
```

**Important:** Replace `your-actual-password-here` with your actual email password.

## Testing

After adding the environment variables and redeploying:

1. **Go to the Contact page:** `https://www.futureelite.pro/contact`
2. **Fill out the contact form**
3. **Submit the form**
4. **You should see:** "Message sent successfully! We will respond within 24-48 hours."
5. **Check your email:** You should receive the contact form submission at `support@futureelite.pro` (or whatever you set as `ADMIN_EMAIL`)

## Troubleshooting

### "Email sending is not configured" Error

- **Check:** `SMTP_ENABLED` is set to `true` (not `True` or `TRUE`)
- **Check:** All SMTP variables are set correctly
- **Check:** Render has redeployed after adding variables

### "SMTP credentials not configured" Error

- **Check:** `SMTP_USER` and `SMTP_PASSWORD` are both set
- **Check:** No extra spaces in the values
- **Check:** Password is correct

### "Failed to send email" Error

- **Check:** SMTP server settings are correct for Office 365:
  - Host: `smtp.office365.com`
  - Port: `587`
- **Check:** Email account allows SMTP access (some accounts require enabling "Less secure app access" or using an app password)
- **Check:** Firewall/network isn't blocking port 587
- **Check:** Render logs for detailed error messages

### Office 365 Authentication Issues

If you get authentication errors:

1. **Check if your Office 365 account requires MFA (Multi-Factor Authentication):**
   - If yes, you may need to use an "App Password" instead of your regular password
   - Or enable "Less secure app access" (if available)

2. **Verify SMTP is enabled for your Office 365 account:**
   - Some Office 365 plans require enabling SMTP AUTH
   - Check your Office 365 admin center

## Alternative: Use Gmail SMTP

If Office 365 SMTP doesn't work, you can use Gmail instead:

```
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
FROM_EMAIL=your-email@gmail.com
ADMIN_EMAIL=support@futureelite.pro
```

**Note:** Gmail requires an "App Password" (not your regular password):
1. Enable 2-factor authentication
2. Go to Google Account → Security → App passwords
3. Generate an app password for "Mail"
4. Use that app password in `SMTP_PASSWORD`

## What Happens After Setup

Once SMTP is configured:

✅ Contact form sends emails directly (no mailto popup)  
✅ Password reset emails are sent automatically  
✅ New user registration notifications are sent (if enabled)  
✅ All emails come from `admin@futureelite.pro` (or your `FROM_EMAIL`)  
✅ Contact form submissions go to `support@futureelite.pro` (or your `ADMIN_EMAIL`)

## Security Notes

- **Never commit passwords to git** - Environment variables in Render are secure
- **Use strong passwords** - Your email password should be strong
- **Consider app passwords** - For better security, use app-specific passwords when available
- **Regularly rotate passwords** - Update `SMTP_PASSWORD` if you change your email password

