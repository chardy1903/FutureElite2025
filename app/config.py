"""
Configuration constants for FutureElite
"""
import os
from datetime import datetime

# Support email - can be overridden by environment variable
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'support@futureelite.com')

# Subscription pricing (USD)
SUBSCRIPTION_PRICING = {
    'monthly': {
        'amount': 9.99,
        'currency': 'USD',
        'symbol': '$',
        'interval': 'month'
    },
    'annual': {
        'amount': 99.99,
        'currency': 'USD',
        'symbol': '$',
        'interval': 'year',
        'original_amount': 119.88,  # Before discount
        'discount_percent': 17
    }
}

# Current year for copyright
CURRENT_YEAR = datetime.now().year

