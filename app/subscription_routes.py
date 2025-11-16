"""
Stripe subscription routes for FutureElite
"""

from flask import Blueprint, request, jsonify, redirect, url_for, render_template, current_app
from datetime import datetime
import os
import json
from typing import Optional

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
def get_subscription_status():
    """Get subscription status for current user (client-side)"""
    try:
        # This endpoint accepts user_id from client since we're using client-side auth
        data = request.get_json() if request.is_json else {}
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'subscription': {
                    'status': SubscriptionStatus.NONE,
                    'has_access': False
                }
            }), 400
        
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
        
        if not user_id:
            return jsonify({'success': False, 'errors': ['User ID is required']}), 400
        
        if plan_type not in SUBSCRIPTION_PLANS:
            return jsonify({'success': False, 'errors': ['Invalid plan type']}), 400
        
        plan = SUBSCRIPTION_PLANS[plan_type]
        
        if not plan['price_id'] or plan['price_id'].strip() == '' or 'YOUR_' in plan['price_id']:
            return jsonify({
                'success': False,
                'errors': [
                    f'Stripe {plan_type} price ID not configured.',
                    'Please set STRIPE_MONTHLY_PRICE_ID or STRIPE_ANNUAL_PRICE_ID environment variable in your .env file.',
                    'See QUICK_STRIPE_SETUP.md for instructions.'
                ]
            }), 500
        
        # Check if Stripe API key is configured
        if not stripe.api_key or stripe.api_key.strip() == '' or stripe.api_key == 'sk_test_YOUR_SECRET_KEY_HERE':
            return jsonify({
                'success': False,
                'errors': [
                    'Stripe API key not configured.',
                    'Please set STRIPE_SECRET_KEY environment variable in your .env file.',
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
                'price': plan['price_id'],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'subscription/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'subscription/cancel',
            metadata={
                'user_id': user_id,
                'plan_type': plan_type
            },
            subscription_data={
                'metadata': {
                    'user_id': user_id,
                    'plan_type': plan_type
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
def stripe_webhook():
    """Handle Stripe webhook events"""
    if not STRIPE_AVAILABLE:
        return jsonify({'error': 'Stripe is not installed'}), 500
    
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            # In development, you might skip signature verification
            event = json.loads(payload)
        
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
        
        return jsonify({'success': True}), 200
        
    except ValueError as e:
        # Invalid payload
        return jsonify({'error': str(e)}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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


def update_subscription_from_stripe(stripe_subscription, user_id: str, customer_id: str):
    """Update or create subscription record from Stripe subscription object"""
    try:
        # Get plan details
        price_id = stripe_subscription.get('items', {}).get('data', [{}])[0].get('price', {}).get('id', '')
        plan_name = 'Monthly' if 'monthly' in price_id.lower() else 'Annual'
        
        # Create or update subscription
        subscription = Subscription(
            user_id=user_id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=stripe_subscription.get('id'),
            status=SubscriptionStatus(stripe_subscription.get('status', 'none')),
            plan_id=price_id,
            plan_name=plan_name,
            current_period_start=datetime.fromtimestamp(stripe_subscription.get('current_period_start', 0)).isoformat() if stripe_subscription.get('current_period_start') else None,
            current_period_end=datetime.fromtimestamp(stripe_subscription.get('current_period_end', 0)).isoformat() if stripe_subscription.get('current_period_end') else None,
            cancel_at_period_end=stripe_subscription.get('cancel_at_period_end', False),
            updated_at=datetime.now().isoformat()
        )
        
        storage.save_subscription(subscription)
        print(f"Subscription saved for user {user_id}: {subscription.status}")
        
    except Exception as e:
        print(f"Error updating subscription: {e}")


@subscription_bp.route('/subscription/success')
def subscription_success():
    """Success page after checkout"""
    session_id = request.args.get('session_id')
    
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            # You can retrieve subscription info here
            return redirect(url_for('subscription.subscription_page', success=True))
        except:
            pass
    
    return redirect(url_for('subscription.subscription_page', success=True))


@subscription_bp.route('/subscription/cancel')
def subscription_cancel():
    """Cancel page"""
    return redirect(url_for('subscription.subscription_page', canceled=True))


@subscription_bp.route('/subscription')
def subscription_page():
    """Subscription management page"""
    return render_template('subscription.html', 
                         stripe_publishable_key=STRIPE_PUBLISHABLE_KEY,
                         plans=SUBSCRIPTION_PLANS)

