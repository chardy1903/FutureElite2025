# Admin Setup for Production (Render)

## Critical: Set ADMIN_USERNAME Environment Variable

The admin page will NOT work unless `ADMIN_USERNAME` is set in your Render environment variables.

### Steps to Set ADMIN_USERNAME in Render:

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Select your service** (FutureElite)
3. **Go to Environment tab**
4. **Add new environment variable**:
   - **Key**: `ADMIN_USERNAME`
   - **Value**: `Admin_Chris1903_FutureElite`
5. **Save** and **Redeploy** your service

### Verify It's Set:

After redeploying, check the logs. You should see:
```
Login check - Admin username: 'Admin_Chris1903_FutureElite', User username: '...'
```

If you see `Admin username: ''` (empty), the environment variable is NOT set.

### Test Admin Access:

1. Log in with:
   - Username: `Admin_Chris1903_FutureElite`
   - Password: `bBrodie@x2027`

2. You should be automatically redirected to `/admin/users`

3. If you're NOT redirected, check:
   - Environment variable is set correctly
   - Username matches exactly (case-sensitive)
   - Service has been redeployed after setting the variable

### Required Environment Variables for Production:

```bash
SECRET_KEY=<your-secret-key>
FLASK_ENV=production
ADMIN_USERNAME=Admin_Chris1903_FutureElite
```

### Troubleshooting:

**Problem**: Admin user can still access `/dashboard`  
**Solution**: `ADMIN_USERNAME` is not set or doesn't match exactly

**Problem**: "Access denied" when accessing `/admin/users`  
**Solution**: Username doesn't match `ADMIN_USERNAME` exactly (check for spaces, case)

**Problem**: No redirect after login  
**Solution**: Check server logs for "Login check" messages to see if username matching is working

