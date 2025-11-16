# How to Find Price IDs in Stripe

## Important: Product ID vs Price ID

- **Product ID** starts with `prod_` ❌ (This is what you have)
- **Price ID** starts with `price_` ✅ (This is what we need)

## How to Find Price IDs

### Method 1: From the Product Page

1. Go to https://dashboard.stripe.com/products
2. Click on your **Monthly Subscription** product
3. On the product page, look for the **Pricing** section
4. You'll see the price listed with a **Price ID** next to it
5. The Price ID looks like: `price_1AbC123xyz...` (long string)
6. Click the copy icon 📋 next to it

### Method 2: From the Prices Page

1. Go to https://dashboard.stripe.com/prices
2. Find your subscription prices
3. Each price will show its **Price ID** (starts with `price_...`)
4. Copy the Price ID for:
   - Monthly subscription ($9.99/month)
   - Annual subscription ($99.99/year)

### Visual Guide

**On Product Page:**
```
Product: Monthly Subscription
├─ Product ID: prod_TR3qGyMM2xzvsw (this is what you have)
└─ Pricing
   └─ Price: $9.99/month
      └─ Price ID: price_1AbC123... ← THIS IS WHAT WE NEED
```

**On Prices Page:**
```
Prices List:
├─ Monthly Subscription - $9.99/month
│  └─ Price ID: price_1AbC123... ← Copy this
└─ Annual Subscription - $99.99/year
   └─ Price ID: price_1XyZ789... ← Copy this
```

## Quick Steps

1. Go to https://dashboard.stripe.com/prices (easiest way)
2. Find your two subscription prices
3. Copy the Price ID for each (they start with `price_...`)
4. Share them with me

The Price IDs are much longer than Product IDs and start with `price_1...`

