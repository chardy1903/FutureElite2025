# Quick Stripe Setup Guide

## Step 1: Get Your Stripe API Keys

1. Go to https://dashboard.stripe.com
2. Make sure you're in **TEST MODE** (toggle in top right)
3. Navigate to **Developers** > **API keys**
4. Copy:
   - **Publishable key** (starts with `pk_test_...`)
   - **Secret key** (starts with `sk_test_...`)

## Step 2: Create Products in Stripe

1. In Stripe Dashboard, go to **Products**
2. Click **Add product**
3. Create **Monthly Subscription**:
   - Name: "Monthly Subscription"
   - Pricing: $9.99 USD
   - Billing period: Monthly (recurring)
   - Copy the **Price ID** (starts with `price_...`)
4. Create **Annual Subscription**:
   - Name: "Annual Subscription"
   - Pricing: $99.99 USD
   - Billing period: Yearly (recurring)
   - Copy the **Price ID** (starts with `price_...`)

## Step 3: Create .env File

Create a file named `.env` in the project root with:

```
STRIPE_SECRET_KEY=sk_test_YOUR_SECRET_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_PUBLISHABLE_KEY_HERE
STRIPE_MONTHLY_PRICE_ID=price_YOUR_MONTHLY_PRICE_ID_HERE
STRIPE_ANNUAL_PRICE_ID=price_YOUR_ANNUAL_PRICE_ID_HERE
```

Replace the placeholder values with your actual keys and price IDs.

## Step 4: Restart the App

After creating the `.env` file, restart the application.

## Testing

Use test card: `4242 4242 4242 4242` with any future expiry date and CVC.

