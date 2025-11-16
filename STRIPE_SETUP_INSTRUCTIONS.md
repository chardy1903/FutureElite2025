# Stripe Setup Instructions

## Quick Setup Steps

### Step 1: Create/Login to Stripe Account

1. Go to **https://dashboard.stripe.com**
2. Sign up for a free account (or log in if you have one)
3. Make sure you're in **TEST MODE** (toggle switch in the top right corner)

### Step 2: Get Your API Keys

1. In Stripe Dashboard, click **Developers** in the left menu
2. Click **API keys**
3. You'll see two keys:
   - **Publishable key** (starts with `pk_test_...`) - Copy this
   - **Secret key** (starts with `sk_test_...`) - Click "Reveal test key" and copy it

### Step 3: Create Subscription Products

1. In Stripe Dashboard, click **Products** in the left menu
2. Click **+ Add product** button

#### Create Monthly Subscription:
- **Name**: `Monthly Subscription`
- **Description**: (optional) `FutureElite Monthly Subscription`
- **Pricing section:
  - **Price**: `9.99`
  - **Currency**: `USD`
  - **Billing period**: Select **Monthly** (recurring)
- Click **Save product**
- **Copy the Price ID** (starts with `price_...`) - This appears after saving

#### Create Annual Subscription:
- Click **+ Add product** again
- **Name**: `Annual Subscription`
- **Description**: (optional) `FutureElite Annual Subscription`
- Pricing section:
  - **Price**: `99.99`
  - **Currency**: `USD`
  - **Billing period**: Select **Yearly** (recurring)
- Click **Save product**
- **Copy the Price ID** (starts with `price_...`)

### Step 4: Update Your .env File

1. Open the `.env` file in your project root
2. Replace the placeholder values with your actual keys:

```
STRIPE_SECRET_KEY=sk_test_YOUR_ACTUAL_SECRET_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_ACTUAL_PUBLISHABLE_KEY_HERE
STRIPE_MONTHLY_PRICE_ID=price_YOUR_ACTUAL_MONTHLY_PRICE_ID_HERE
STRIPE_ANNUAL_PRICE_ID=price_YOUR_ACTUAL_ANNUAL_PRICE_ID_HERE
```

**Important**: 
- Remove any spaces around the `=` sign
- Don't include quotes around the values
- Make sure there are no extra spaces at the end of lines

### Step 5: Restart the Application

After updating the `.env` file, restart your Flask application.

## Testing

Once configured, you can test the subscription flow using Stripe's test card:
- **Card Number**: `4242 4242 4242 4242`
- **Expiry**: Any future date (e.g., `12/25`)
- **CVC**: Any 3 digits (e.g., `123`)
- **ZIP**: Any 5 digits (e.g., `12345`)

## Need Help?

If you don't have a Stripe account yet:
1. Go to https://dashboard.stripe.com/register
2. Sign up (it's free)
3. You'll automatically be in Test Mode
4. Follow the steps above

## Common Issues

**"Stripe API key not configured"**
- Make sure you copied the entire key (they're long!)
- Check that there are no extra spaces in your .env file
- Make sure you're using TEST MODE keys (start with `sk_test_` and `pk_test_`)

**"Price ID not configured"**
- Make sure you created the products in Stripe Dashboard
- Copy the Price ID (not the Product ID)
- Price IDs start with `price_`

