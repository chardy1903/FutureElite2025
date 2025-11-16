# How to Create Stripe Products and Get Price IDs

## Step-by-Step Instructions

### 1. Go to Stripe Products Page
- Open https://dashboard.stripe.com/products
- Make sure you're in **LIVE MODE** (since you're using live keys)

### 2. Create Monthly Subscription Product

1. Click the **"+ Add product"** button (top right)
2. Fill in the form:
   - **Name**: `Monthly Subscription`
   - **Description**: (optional) `FutureElite Monthly Subscription`
3. In the **Pricing** section:
   - **Price**: `9.99`
   - **Currency**: `USD` (or your preferred currency)
   - **Billing period**: Select **Monthly** (recurring)
   - **Recurring usage type**: Leave as default
4. Click **"Save product"** button
5. After saving, you'll see the product page
6. **Copy the Price ID** - it will be shown in the pricing section, starts with `price_1...` or `price_...`
   - It looks like: `price_1AbC123xyz...`
   - Click the copy icon next to it

### 3. Create Annual Subscription Product

1. Click **"+ Add product"** again
2. Fill in the form:
   - **Name**: `Annual Subscription`
   - **Description**: (optional) `FutureElite Annual Subscription`
3. In the **Pricing** section:
   - **Price**: `99.99`
   - **Currency**: `USD` (or your preferred currency)
   - **Billing period**: Select **Yearly** or **Annual** (recurring)
   - **Recurring usage type**: Leave as default
4. Click **"Save product"** button
5. After saving, **copy the Price ID** (starts with `price_...`)

### 4. Where to Find Price IDs

After creating a product, the Price ID appears:
- On the product page, in the **Pricing** section
- It's labeled as "Price ID" or "API ID"
- Format: `price_1AbC123xyz...` (long string)
- Click the copy icon to copy it

### 5. Update Your .env File

Once you have both Price IDs, share them with me or update your `.env` file:

```
STRIPE_MONTHLY_PRICE_ID=price_1YOUR_ACTUAL_MONTHLY_PRICE_ID
STRIPE_ANNUAL_PRICE_ID=price_1YOUR_ACTUAL_ANNUAL_PRICE_ID
```

## Quick Visual Guide

**Product Creation Form:**
```
┌─────────────────────────────────┐
│ Name: Monthly Subscription      │
│ Description: (optional)         │
│                                 │
│ Pricing:                        │
│   Price: 9.99                   │
│   Currency: USD                 │
│   Billing: Monthly (recurring)  │
│                                 │
│   [Save product]                │
└─────────────────────────────────┘
```

**After Saving - Find Price ID:**
```
Product: Monthly Subscription
├─ Pricing
│  └─ Price ID: price_1AbC123... [📋 Copy]
```

## Troubleshooting

**Can't find Price ID?**
- Make sure you saved the product
- Look in the "Pricing" section of the product page
- It might be labeled as "API ID" or "Price ID"

**Price ID doesn't start with "price_"?**
- Make sure you're copying the Price ID, not the Product ID
- Product IDs start with `prod_`
- Price IDs start with `price_`

