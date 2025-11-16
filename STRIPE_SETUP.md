# Stripe Subscription Setup Guide

This guide will help you set up Stripe subscriptions for FutureElite.

## Prerequisites

1. A Stripe account (sign up at https://stripe.com)
2. Stripe API keys (available in Stripe Dashboard)

## Setup Steps

### 1. Install Stripe Python Library

```bash
pip install stripe>=7.0.0
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Get Your Stripe API Keys

1. Go to https://dashboard.stripe.com
2. Navigate to **Developers** > **API keys**
3. Copy your **Publishable key** and **Secret key**

### 3. Create Subscription Products and Prices

1. In Stripe Dashboard, go to **Products**
2. Click **Add product**
3. Create two products:
   - **Monthly Subscription**: $9.99/month
   - **Annual Subscription**: $99.99/year
4. For each product, create a recurring price
5. Copy the **Price ID** for each (starts with `price_...`)

### 4. Set Environment Variables

Create a `.env` file in the project root (or set environment variables):

```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_MONTHLY_PRICE_ID=price_...
STRIPE_ANNUAL_PRICE_ID=price_...
STRIPE_WEBHOOK_SECRET=whsec_...  # For webhook signature verification
```

### 5. Set Up Webhook Endpoint

1. In Stripe Dashboard, go to **Developers** > **Webhooks**
2. Click **Add endpoint**
3. Set endpoint URL to: `https://yourdomain.com/api/subscription/webhook`
4. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Copy the **Signing secret** (starts with `whsec_...`)

### 6. Test Mode vs Live Mode

- **Test Mode**: Use test API keys (start with `sk_test_` and `pk_test_`)
  - Use test card: `4242 4242 4242 4242`
  - Any future expiry date and CVC
  
- **Live Mode**: Use live API keys (start with `sk_live_` and `pk_live_`)
  - Real payments will be processed

## Testing

1. Start the application
2. Log in or register
3. Navigate to **Subscription** page
4. Click "Subscribe Monthly" or "Subscribe Annual"
5. Use test card `4242 4242 4242 4242` in Stripe Checkout
6. Complete the payment
7. You should be redirected back with an active subscription

## Important Notes

- **Webhook Security**: Always verify webhook signatures in production
- **Customer Portal**: Users can manage subscriptions via Stripe Customer Portal
- **Subscription Status**: Stored in client-side IndexedDB for offline access
- **Server Sync**: Subscription status is synced from server when user checks subscription page

## Troubleshooting

- **"Stripe price ID not configured"**: Make sure environment variables are set
- **Webhook not working**: Check webhook URL is accessible and signature is correct
- **Payment fails**: Check Stripe Dashboard for error details

