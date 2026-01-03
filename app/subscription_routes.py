"""
Stripe subscription routes for FutureElite
"""

from flask import Blueprint, request, jsonify, redirect, url_for, render_template, current_app
from flask_login import login_required, current_user
from datetime import datetime
import os
import json
from typing import Optional

# CSRF exemption for webhook (external service verified by signature)
try:
    from flask_wtf.csrf import csrf_exempt
except ImportError:
    # If flask-wtf not available, create a no-op decorator
    def csrf_exempt(f):
        return f

# Try to import stripe, but make it optional
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None

from .models import Subscription, SubscriptionStatus
from .storage import StorageManager

# Create blueprint
subscription_bp = Blueprint('subscription', __name__)

# Initialize storage
storage = StorageManager()

# Security: In-memory store for webhook event IDs (for idempotency)
# TODO: Replace with persistent storage (Redis/DB) in production for distributed systems
_processed_webhook_events = set()

# Initialize Stripe (use environment variables)
if STRIPE_AVAILABLE:
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '').strip()
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '').strip()
else:
    STRIPE_PUBLISHABLE_KEY = ''

# Subscription plans (configure these in Stripe Dashboard)
SUBSCRIPTION_PLANS = {
    'monthly': {
        'price_id': os.environ.get('STRIPE_MONTHLY_PRICE_ID', '').strip(),
        'name': 'Monthly Subscription',
        'amount': 9.99,
        'currency': 'usd',
        'interval': 'month'
    },
    'annual': {
        'price_id': os.environ.get('STRIPE_ANNUAL_PRICE_ID', '').strip(),
        'name': 'Annual Subscription',
        'amount': 99.99,
        'currency': 'usd',
        'interval': 'year'
    }
}


@subscription_bp.route('/api/subscription/status', methods=['POST'])
@login_required
def get_subscription_status():
    """Get subscription status for current authenticated user"""
    try:
        # Security: Use authenticated user's ID, not client-provided user_id
        user_id = current_user.id
        
        # Check server-side storage for subscription
        subscription = storage.get_subscription_by_user_id(user_id)
        
        if subscription and subscription.status == SubscriptionStatus.ACTIVE:
            return jsonify({
                'success': True,
                'subscription': {
                    'status': subscription.status,
                    'has_access': True,
                    'plan_name': subscription.plan_name,
                    'current_period_end': subscription.current_period_end,
                    'cancel_at_period_end': subscription.cancel_at_period_end,
                    'stripe_customer_id': subscription.stripe_customer_id,
                    'stripe_subscription_id': subscription.stripe_subscription_id,
                    'stripe_publishable_key': STRIPE_PUBLISHABLE_KEY
                }
            })
        else:
            return jsonify({
                'success': True,
                'subscription': {
                    'status': subscription.status if subscription else SubscriptionStatus.NONE,
                    'has_access': False,
                    'stripe_publishable_key': STRIPE_PUBLISHABLE_KEY
                }
            })
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return jsonify({
            'success': False,
            'subscription': {
                'status': SubscriptionStatus.NONE,
                'has_access': False
            },
            'errors': [f'Server error: {error_msg}']
        }), 500


@subscription_bp.route('/api/subscription/create-checkout', methods=['POST'])
def create_checkout_session():
    """Create Stripe Checkout session"""
    try:
        if not STRIPE_AVAILABLE:
            return jsonify({
                'success': False,
                'errors': ['Stripe is not installed. Please install it with: pip install stripe']
            }), 500
        
        if not request.is_json:
            return jsonify({
                'success': False,
                'errors': ['Request must be JSON']
            }), 400
        
        data = request.get_json() or {}
        user_id = data.get('user_id')
        plan_type = data.get('plan_type', 'monthly')  # 'monthly' or 'annual'
        requested_currency = data.get('currency', 'usd').lower()  # Get currency from request
        
        if not user_id:
            return jsonify({'success': False, 'errors': ['User ID is required']}), 400
        
        if plan_type not in SUBSCRIPTION_PLANS:
            return jsonify({'success': False, 'errors': ['Invalid plan type']}), 400
        
        plan = SUBSCRIPTION_PLANS[plan_type]
        
        # Check if Stripe API key is configured and valid
        if not stripe.api_key or stripe.api_key.strip() == '' or stripe.api_key == 'sk_test_YOUR_SECRET_KEY_HERE':
            return jsonify({
                'success': False,
                'errors': [
                    'Stripe API key not configured.',
                    'Please set STRIPE_SECRET_KEY environment variable in your .env file.',
                    'See QUICK_STRIPE_SETUP.md for instructions.'
                ]
            }), 500
        
        # Validate that it's a secret key (starts with sk_ or rk_ for restricted keys)
        if not stripe.api_key.startswith(('sk_', 'rk_')):
            current_app.logger.error(f"Invalid Stripe API key format. Secret keys must start with 'sk_' or 'rk_'. Got: {stripe.api_key[:10]}...")
            return jsonify({
                'success': False,
                'errors': [
                    'Invalid Stripe API key format.',
                    'STRIPE_SECRET_KEY must be a secret key (starts with sk_ or rk_).',
                    'You may have accidentally used a publishable key (pk_) instead.',
                    'Please check your .env file and set the correct STRIPE_SECRET_KEY.'
                ]
            }), 500
        
        # Currency conversion rates (approximate)
        currency_rates = {
            'usd': {'monthly': 9.99, 'annual': 99.99},
            'gbp': {'monthly': 7.99, 'annual': 79.99},
            'eur': {'monthly': 9.49, 'annual': 94.99},
            'aed': {'monthly': 36.99, 'annual': 369.99},
            'sar': {'monthly': 37.49, 'annual': 374.99}
        }
        
        # Get price ID - check for currency-specific price IDs first
        price_id = None
        if requested_currency == 'usd':
            # Use default price ID for USD
            price_id = plan['price_id']
        else:
            # Check for currency-specific price ID in environment variables
            currency_price_key = f'STRIPE_{plan_type.upper()}_PRICE_ID_{requested_currency.upper()}'
            price_id = os.environ.get(currency_price_key, '').strip()
            
            # If no currency-specific price ID, try to create one dynamically
            if not price_id or price_id == '':
                try:
                    # Get product ID from existing price (if available)
                    if plan['price_id'] and plan['price_id'].strip() and 'YOUR_' not in plan['price_id']:
                        try:
                            existing_price = stripe.Price.retrieve(plan['price_id'])
                            product_id = existing_price.product
                            
                            # Create new price for requested currency
                            amount = int(currency_rates.get(requested_currency, currency_rates['usd'])[plan_type] * 100)  # Convert to cents
                            
                            new_price = stripe.Price.create(
                                product=product_id,
                                unit_amount=amount,
                                currency=requested_currency,
                                recurring={'interval': plan['interval']}
                            )
                            price_id = new_price.id
                        except Exception as e:
                            current_app.logger.warning(f"Could not create dynamic price: {e}")
                            # Fall back to default price ID
                            price_id = plan['price_id']
                    else:
                        price_id = plan['price_id']
                except Exception as e:
                    current_app.logger.warning(f"Error creating price for {requested_currency}: {e}")
                    price_id = plan['price_id']
        
        if not price_id or price_id.strip() == '' or 'YOUR_' in price_id:
            return jsonify({
                'success': False,
                'errors': [
                    f'Stripe {plan_type} price ID not configured.',
                    'Please set STRIPE_MONTHLY_PRICE_ID or STRIPE_ANNUAL_PRICE_ID environment variable in your .env file.',
                    'See QUICK_STRIPE_SETUP.md for instructions.'
                ]
            }), 500
        
        # Create or retrieve Stripe customer
        # In production, you'd store customer_id in your database
        # For now, we'll create a new customer each time (not ideal, but works)
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer_email=data.get('email'),  # Optional: pass email if available
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'subscription/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'subscription/cancel',
            metadata={
                'user_id': user_id,
                'plan_type': plan_type,
                'currency': requested_currency
            },
            subscription_data={
                'metadata': {
                    'user_id': user_id,
                    'plan_type': plan_type,
                    'currency': requested_currency
                }
            }
        )
        
        return jsonify({
            'success': True,
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        })
        
    except stripe.error.StripeError as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'errors': [f'Stripe error: {str(e)}']
        }), 400
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error creating checkout session: {error_trace}")
        return jsonify({
            'success': False,
            'errors': [f'Error creating checkout session: {str(e)}', f'Details: {error_trace[:200]}']
        }), 500


@subscription_bp.route('/api/subscription/create-portal', methods=['POST'])
def create_portal_session():
    """Create Stripe Customer Portal session for managing subscription"""
    try:
        if not STRIPE_AVAILABLE:
            return jsonify({
                'success': False,
                'errors': ['Stripe is not installed. Please install it with: pip install stripe']
            }), 500
        
        if not request.is_json:
            return jsonify({
                'success': False,
                'errors': ['Request must be JSON']
            }), 400
        
        data = request.get_json() or {}
        customer_id = data.get('customer_id')
        
        if not customer_id:
            return jsonify({'success': False, 'errors': ['Customer ID is required']}), 400
        
        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=request.host_url + 'subscription',
        )
        
        return jsonify({
            'success': True,
            'portal_url': portal_session.url
        })
        
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'errors': [f'Stripe error: {str(e)}']
        }), 400
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return jsonify({
            'success': False,
            'errors': [f'Error creating portal session: {error_msg}']
        }), 500


@subscription_bp.route('/api/subscription/webhook', methods=['POST'])
@subscription_bp.route('/stripe/webhook', methods=['POST'])  # Alias for Render/Stripe configuration
@csrf_exempt  # Exempt from CSRF - verified by Stripe signature instead
def stripe_webhook():
    """
    Handle Stripe webhook events.
    
    SECURITY: This endpoint bypasses:
    - CSRF protection (verified by Stripe signature instead)
    - Rate limiting (exempted globally, verified by signature instead)
    - Request blocking middleware (allowlisted in p0_security_blocking)
    
    All requests are verified using Stripe-Signature header and STRIPE_WEBHOOK_SECRET.
    Invalid signatures are rejected with HTTP 400.
    """
    if not STRIPE_AVAILABLE:
        return jsonify({'error': 'Stripe is not installed'}), 500
    
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '').strip()
    
    # Security: Require webhook secret - reject if not configured
    if not webhook_secret:
        current_app.logger.error("STRIPE_WEBHOOK_SECRET not configured - rejecting webhook")
        return jsonify({'error': 'Webhook secret not configured'}), 500
    
    try:
        # Always verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        
        # Security: Idempotency check - prevent duplicate event processing
        event_id = event.get('id')
        if event_id:
            if event_id in _processed_webhook_events:
                current_app.logger.info(f"Duplicate webhook event ignored: {event_id}")
                return jsonify({'success': True, 'message': 'Event already processed'}), 200
            _processed_webhook_events.add(event_id)
            # TODO: In production, use persistent storage (Redis/DB) for event IDs
            # Limit in-memory set size to prevent memory issues
            if len(_processed_webhook_events) > 10000:
                # Clear oldest 50% (simple cleanup)
                _processed_webhook_events.clear()
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            # Handle successful checkout
            handle_checkout_completed(session)
            
        elif event['type'] == 'customer.subscription.created':
            subscription = event['data']['object']
            handle_subscription_created(subscription)
            
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            handle_subscription_updated(subscription)
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            handle_subscription_deleted(subscription)
        
        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            handle_payment_failed(invoice)
        
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            handle_payment_succeeded(invoice)
        
        return jsonify({'success': True}), 200
        
    except ValueError as e:
        # Invalid payload
        current_app.logger.warning(f"Invalid webhook payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature - log for security monitoring
        current_app.logger.warning(f"Webhook signature verification failed: {e}")
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        current_app.logger.error(f"Webhook processing error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


def handle_checkout_completed(session):
    """Handle successful checkout"""
    if not STRIPE_AVAILABLE:
        return
    
    user_id = session.get('metadata', {}).get('user_id')
    subscription_id = session.get('subscription')
    customer_id = session.get('customer')
    
    if not user_id:
        print("Warning: No user_id in checkout session metadata")
        return
    
    # Retrieve subscription from Stripe to get full details
    try:
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        update_subscription_from_stripe(stripe_subscription, user_id, customer_id)
    except Exception as e:
        print(f"Error retrieving subscription from Stripe: {e}")


def handle_subscription_created(subscription):
    """Handle subscription created"""
    customer_id = subscription.get('customer')
    subscription_id = subscription.get('id')
    status = subscription.get('status')
    
    # Get user_id from subscription metadata
    user_id = subscription.get('metadata', {}).get('user_id')
    
    if user_id:
        update_subscription_from_stripe(subscription, user_id, customer_id)
    else:
        print(f"Warning: No user_id in subscription metadata for {subscription_id}")


def handle_subscription_updated(subscription):
    """Handle subscription updated"""
    subscription_id = subscription.get('id')
    customer_id = subscription.get('customer')
    
    # Try to find existing subscription
    existing = storage.get_subscription_by_stripe_id(subscription_id)
    
    if existing:
        update_subscription_from_stripe(subscription, existing.user_id, customer_id)
    else:
        # Try to get user_id from metadata
        user_id = subscription.get('metadata', {}).get('user_id')
        if user_id:
            update_subscription_from_stripe(subscription, user_id, customer_id)


def handle_subscription_deleted(subscription):
    """Handle subscription deleted"""
    subscription_id = subscription.get('id')
    
    # Find and update subscription status
    existing = storage.get_subscription_by_stripe_id(subscription_id)
    if existing:
        existing.status = SubscriptionStatus.CANCELED
        existing.updated_at = datetime.now().isoformat()
        storage.save_subscription(existing)


def handle_payment_failed(invoice):
    """Handle failed payment - mark subscription as past_due"""
    if not STRIPE_AVAILABLE:
        return
    
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return
    
    try:
        # Get subscription from Stripe to get full details
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Find existing subscription
        existing = storage.get_subscription_by_stripe_id(subscription_id)
        if existing:
            # Update subscription status to past_due
            update_subscription_from_stripe(stripe_subscription, existing.user_id, existing.stripe_customer_id or '')
            current_app.logger.info(f"Marked subscription {subscription_id} as past_due due to payment failure")
    except Exception as e:
        current_app.logger.error(f"Error handling payment failure: {e}", exc_info=True)


def handle_payment_succeeded(invoice):
    """Handle successful payment - update subscription period dates"""
    if not STRIPE_AVAILABLE:
        return
    
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return
    
    try:
        # Get subscription from Stripe to get updated period dates
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Find existing subscription
        existing = storage.get_subscription_by_stripe_id(subscription_id)
        if existing:
            # Update subscription with new period dates
            update_subscription_from_stripe(stripe_subscription, existing.user_id, existing.stripe_customer_id or '')
            current_app.logger.info(f"Updated subscription {subscription_id} after successful payment")
    except Exception as e:
        current_app.logger.error(f"Error handling payment success: {e}", exc_info=True)


def update_subscription_from_stripe(stripe_subscription, user_id: str, customer_id: str):
    """Update or create subscription record from Stripe subscription object"""
    try:
        # Handle both dict and object formats
        if hasattr(stripe_subscription, 'get'):
            # It's a dict
            sub_dict = stripe_subscription
        else:
            # It's a Stripe object, convert to dict
            sub_dict = stripe_subscription.to_dict() if hasattr(stripe_subscription, 'to_dict') else dict(stripe_subscription)
        
        # Get plan details
        items = sub_dict.get('items', {})
        if isinstance(items, dict):
            price_id = items.get('data', [{}])[0].get('price', {}).get('id', '')
        else:
            # Handle Stripe object
            price_id = items.data[0].price.id if hasattr(items, 'data') and items.data else ''
        
        # Determine plan name from price_id or metadata
        plan_name = 'Monthly'
        if price_id:
            # Check metadata first
            metadata = sub_dict.get('metadata', {})
            plan_type = metadata.get('plan_type', '')
            if 'annual' in plan_type.lower() or 'year' in price_id.lower():
                plan_name = 'Annual'
            elif 'monthly' in plan_type.lower() or 'month' in price_id.lower():
                plan_name = 'Monthly'
        
        # Get status - handle both string and enum
        status_str = sub_dict.get('status', 'none')
        if isinstance(status_str, str):
            # Map Stripe status to our enum
            status_map = {
                'active': SubscriptionStatus.ACTIVE,
                'canceled': SubscriptionStatus.CANCELED,
                'past_due': SubscriptionStatus.PAST_DUE,
                'unpaid': SubscriptionStatus.UNPAID,
                'trialing': SubscriptionStatus.TRIALING,
                'incomplete': SubscriptionStatus.INCOMPLETE,
                'incomplete_expired': SubscriptionStatus.INCOMPLETE_EXPIRED,
            }
            status = status_map.get(status_str.lower(), SubscriptionStatus.NONE)
        else:
            status = SubscriptionStatus(status_str)
        
        # Handle dates - Stripe returns timestamps
        current_period_start = None
        current_period_end = None
        
        if sub_dict.get('current_period_start'):
            start_val = sub_dict.get('current_period_start')
            if isinstance(start_val, (int, float)):
                current_period_start = datetime.fromtimestamp(start_val).isoformat()
            else:
                current_period_start = start_val.isoformat() if hasattr(start_val, 'isoformat') else str(start_val)
        
        if sub_dict.get('current_period_end'):
            end_val = sub_dict.get('current_period_end')
            if isinstance(end_val, (int, float)):
                current_period_end = datetime.fromtimestamp(end_val).isoformat()
            else:
                current_period_end = end_val.isoformat() if hasattr(end_val, 'isoformat') else str(end_val)
        
        # Create or update subscription
        subscription = Subscription(
            user_id=user_id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=sub_dict.get('id'),
            status=status,
            plan_id=price_id,
            plan_name=plan_name,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=sub_dict.get('cancel_at_period_end', False),
            updated_at=datetime.now().isoformat()
        )
        
        storage.save_subscription(subscription)
        print(f"Subscription saved for user {user_id}: {subscription.status} (plan: {plan_name})")
        
    except Exception as e:
        print(f"Error updating subscription: {e}")
        import traceback
        traceback.print_exc()


@subscription_bp.route('/subscription/success')
def subscription_success():
    """Success page after checkout - manually sync subscription from Stripe"""
    session_id = request.args.get('session_id')
    
    if session_id and STRIPE_AVAILABLE:
        try:
            # Retrieve the checkout session from Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            
            # Get user_id from session metadata
            user_id = session.get('metadata', {}).get('user_id')
            subscription_id = session.get('subscription')
            customer_id = session.get('customer')
            
            if user_id and subscription_id:
                try:
                    # Retrieve the subscription from Stripe
                    stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                    
                    # Update or create subscription in our database
                    update_subscription_from_stripe(stripe_subscription, user_id, customer_id)
                    
                    print(f"Subscription synced for user {user_id} from success page")
                except Exception as e:
                    print(f"Error syncing subscription from success page: {e}")
                    import traceback
                    traceback.print_exc()
            
            return redirect(url_for('subscription.subscription_page', success=True))
        except Exception as e:
            print(f"Error retrieving checkout session: {e}")
            import traceback
            traceback.print_exc()
    
    return redirect(url_for('subscription.subscription_page', success=True))


@subscription_bp.route('/subscription/cancel')
def subscription_cancel():
    """Cancel page"""
    return redirect(url_for('subscription.subscription_page', canceled=True))


@subscription_bp.route('/api/subscription/sync', methods=['POST'])
def sync_subscription():
    """Manually sync subscription from Stripe for a user"""
    try:
        if not STRIPE_AVAILABLE:
            return jsonify({
                'success': False,
                'errors': ['Stripe is not installed']
            }), 500
        
        data = request.get_json() if request.is_json else {}
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'errors': ['User ID is required']
            }), 400
        
        # Check if user has any existing subscription in our database
        existing_sub = storage.get_subscription_by_user_id(user_id)
        
        # If they have a Stripe subscription ID, retrieve it
        if existing_sub and existing_sub.stripe_subscription_id:
            try:
                stripe_sub = stripe.Subscription.retrieve(existing_sub.stripe_subscription_id)
                update_subscription_from_stripe(stripe_sub, user_id, existing_sub.stripe_customer_id)
                return jsonify({
                    'success': True,
                    'message': 'Subscription synced from Stripe'
                })
            except stripe.error.StripeError as e:
                return jsonify({
                    'success': False,
                    'errors': [f'Stripe error: {str(e)}']
                }), 400
        
        # Search Stripe for subscriptions with this user_id in metadata
        try:
            subscriptions = stripe.Subscription.list(
                limit=100,
                expand=['data.default_payment_method']
            )
            
            # Find subscription with matching user_id in metadata
            for sub in subscriptions.data:
                metadata = sub.metadata or {}
                if metadata.get('user_id') == user_id:
                    # Found it! Update our database
                    customer_id = sub.customer if isinstance(sub.customer, str) else sub.customer.id
                    update_subscription_from_stripe(sub, user_id, customer_id)
                    return jsonify({
                        'success': True,
                        'message': 'Subscription found and synced from Stripe'
                    })
            
            return jsonify({
                'success': False,
                'errors': ['No active subscription found in Stripe for this user. Please complete checkout first.']
            }), 404
            
        except stripe.error.StripeError as e:
            return jsonify({
                'success': False,
                'errors': [f'Stripe error searching subscriptions: {str(e)}']
            }), 400
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'errors': [f'Error syncing subscription: {str(e)}']
        }), 500


@subscription_bp.route('/subscription')
def subscription_page():
    """Subscription management page"""
    return render_template('subscription.html', 
                         stripe_publishable_key=STRIPE_PUBLISHABLE_KEY,
                         plans=SUBSCRIPTION_PLANS)

