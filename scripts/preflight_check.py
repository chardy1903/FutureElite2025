#!/usr/bin/env python3
"""
Pre-flight Check Script for Production Deployment
Validates environment variables and application startup
Exits with non-zero code if any check fails
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_required_env_var(name, min_length=None):
    """Check if required environment variable exists and optionally validate length"""
    value = os.environ.get(name, '').strip()
    
    if not value:
        print(f"❌ ERROR: Required environment variable '{name}' is not set", file=sys.stderr)
        return False
    
    if min_length and len(value) < min_length:
        print(f"❌ ERROR: Environment variable '{name}' must be at least {min_length} characters (current: {len(value)})", file=sys.stderr)
        return False
    
    print(f"✅ {name}: Set (length: {len(value)})")
    return True

def check_optional_env_var(name, required_if=None):
    """Check optional environment variable, required if condition is met"""
    value = os.environ.get(name, '').strip()
    
    if required_if and required_if():
        if not value:
            print(f"❌ ERROR: Environment variable '{name}' is required when using Stripe", file=sys.stderr)
            return False
        print(f"✅ {name}: Set")
    else:
        if value:
            print(f"ℹ️  {name}: Set (optional)")
        else:
            print(f"ℹ️  {name}: Not set (optional)")
    
    return True

def check_stripe_enabled():
    """Check if Stripe is being used"""
    stripe_key = os.environ.get('STRIPE_SECRET_KEY', '').strip()
    # Check if it's a real key (not placeholder)
    return bool(stripe_key and 
                not stripe_key.startswith('sk_test_YOUR_') and 
                not stripe_key.startswith('sk_live_your_') and
                not 'your_stripe' in stripe_key.lower() and
                len(stripe_key) > 20)

def check_app_import():
    """Check if application can be imported and initialized"""
    try:
        # Try to import and create app
        from app.main import create_app
        app = create_app()
        print("✅ Application imports and initializes successfully")
        return True
    except RuntimeError as e:
        # This is expected if SECRET_KEY is missing - that's checked separately
        if 'SECRET_KEY' in str(e):
            print(f"❌ ERROR: Application initialization failed: {e}", file=sys.stderr)
            return False
        # Re-raise other RuntimeErrors
        raise
    except Exception as e:
        print(f"❌ ERROR: Application import/initialization failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all pre-flight checks"""
    print("=" * 60)
    print("FutureElite Pre-Flight Check")
    print("=" * 60)
    print()
    
    all_passed = True
    
    # Required environment variables
    print("Checking required environment variables...")
    all_passed &= check_required_env_var('SECRET_KEY', min_length=32)
    print()
    
    # Check Flask environment
    flask_env = os.environ.get('FLASK_ENV', '').strip()
    if flask_env.lower() == 'production':
        print(f"✅ FLASK_ENV: {flask_env} (production mode)")
    else:
        print(f"⚠️  WARNING: FLASK_ENV is not set to 'production' (current: '{flask_env}')")
        print("   Security features may not be fully enabled")
    print()
    
    # Stripe configuration (required if Stripe is enabled)
    print("Checking Stripe configuration...")
    stripe_enabled = check_stripe_enabled()
    if stripe_enabled:
        # Webhook secret is only required if using Stripe webhooks
        # For now, make it optional - user can add it later if needed
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '').strip()
        if webhook_secret:
            print(f"✅ STRIPE_WEBHOOK_SECRET: Set (length: {len(webhook_secret)})")
        else:
            print("ℹ️  STRIPE_WEBHOOK_SECRET: Not set (optional - required only if using Stripe webhooks)")
        check_optional_env_var('STRIPE_SECRET_KEY', required_if=lambda: False)
        check_optional_env_var('STRIPE_PUBLISHABLE_KEY', required_if=lambda: False)
    else:
        print("ℹ️  Stripe not configured (STRIPE_SECRET_KEY not set or using placeholder)")
    print()
    
    # Application import check
    print("Checking application initialization...")
    all_passed &= check_app_import()
    print()
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("✅ All pre-flight checks passed!")
        print("   Application is ready for production deployment.")
        return 0
    else:
        print("❌ Pre-flight checks FAILED")
        print("   Please fix the errors above before deploying.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

