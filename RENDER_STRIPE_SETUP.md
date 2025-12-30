# Setting Up Stripe in Render Production

This guide explains how to configure Stripe environment variables in your Render deployment so the "Sync Subscriptions from Stripe" feature works.

## The Problem

If `STRIPE_SECRET_KEY` is not set in Render, you'll see this error when trying to sync subscriptions:
```
{"errors":["Stripe API key not configured"],"success":false}
```

## Solution: Set Stripe Environment Variables in Render

### Step 1: Get Your Stripe Keys

1. **Log in to Stripe Dashboard**: Go to [https://dashboard.stripe.com](https://dashboard.stripe.com)
2. **Get your API keys**:
   - Click on "Developers" → "API keys"
   - For **production**, use keys that start with `sk_live_` (secret) and `pk_live_` (publishable)
   - For **testing**, use keys that start with `sk_test_` (secret) and `pk_test_` (publishable)
3. **Get your Price IDs**:
   - Go to "Products" → Select your subscription product
   - Copy the Price ID for Monthly and Annual plans

### Step 2: Set Environment Variables in Render

1. **Go to your Render Dashboard**: [https://dashboard.render.com](https://dashboard.render.com)
2. **Select your FutureElite service**
3. **Navigate to "Environment" tab**
4. **Add the following environment variables**:

   | Variable Name | Value | Example |
   |--------------|-------|---------|
   | `STRIPE_SECRET_KEY` | Your Stripe secret key | `sk_live_51...` or `rk_live_...` |
   | `STRIPE_PUBLISHABLE_KEY` | Your Stripe publishable key | `pk_live_51...` |
   | `STRIPE_MONTHLY_PRICE_ID` | Monthly subscription price ID | `price_1...` |
   | `STRIPE_ANNUAL_PRICE_ID` | Annual subscription price ID | `price_1...` |
   | `STRIPE_WEBHOOK_SECRET` | Webhook signing secret (optional but recommended) | `whsec_...` |

5. **Click "Save Changes"**
6. **Redeploy your service** (Render will prompt you)

### Step 3: Verify the Setup

After redeployment:

1. **Log in to your admin page**: `https://www.futureelite.pro/admin/users`
2. **Click "Sync Subscriptions from Stripe"**
3. **You should see**: "Synced X subscription(s) from Stripe" instead of an error

## Important Notes

- **Secret keys** (`sk_` or `rk_`) should NEVER be exposed in client-side code
- **Publishable keys** (`pk_`) are safe to use in frontend code
- **Restricted keys** (`rk_`) are more secure than standard secret keys (`sk_`)
- Make sure you're using **live keys** (`sk_live_` / `pk_live_`) for production, not test keys

## Troubleshooting

### Still getting "Stripe API key not configured" error?

1. **Check the variable name**: It must be exactly `STRIPE_SECRET_KEY` (case-sensitive)
2. **Check the value**: Make sure there are no extra spaces or quotes
3. **Redeploy**: After setting environment variables, you must redeploy
4. **Check Render logs**: Look for any errors during startup

### Keys work locally but not in production?

- Local `.env` file is not used in production
- Environment variables must be set in Render dashboard
- Make sure you're using the correct keys (live vs test)

## Security Best Practices

- ✅ Use **restricted keys** (`rk_`) instead of standard secret keys when possible
- ✅ Never commit Stripe keys to version control
- ✅ Rotate keys periodically
- ✅ Use different keys for test and production environments
- ✅ Enable webhook signature verification (`STRIPE_WEBHOOK_SECRET`)

