"""
Security Middleware for Production Hardening

This module provides additional security layers beyond the basic
request filtering in main.py. It includes:
- Enhanced request validation
- Security header injection
- Attack pattern detection
- Logging and alerting
"""

import os
import re
import time
from functools import wraps
from flask import request, jsonify, current_app, g
from collections import defaultdict
from datetime import datetime, timedelta


class SecurityMiddleware:
    """Enhanced security middleware for production"""
    
    def __init__(self, app=None):
        self.app = app
        self.attack_patterns = self._load_attack_patterns()
        self.suspicious_ips = defaultdict(list)  # IP -> list of timestamps
        self.blocked_ips = set()  # IPs that should be blocked
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        self.app = app
        
        # Register before_request hooks
        @app.before_request
        def security_checks():
            """Run security checks before processing request"""
            # Check if IP is blocked
            client_ip = self._get_client_ip()
            if client_ip in self.blocked_ips:
                current_app.logger.warning(f"Blocked request from blocked IP: {client_ip}")
                return self._block_response("Access denied")
            
            # Check for attack patterns
            attack_detected = self._detect_attack_patterns(request.path)
            if attack_detected:
                self._log_suspicious_activity(client_ip, request.path, attack_detected)
                return self._block_response("Invalid request")
            
            # Rate limit suspicious IPs
            if self._is_suspicious_ip(client_ip):
                if self._exceeded_rate_limit(client_ip):
                    current_app.logger.warning(f"Rate limit exceeded for suspicious IP: {client_ip}")
                    return self._block_response("Rate limit exceeded", 429)
        
        # Register after_request hook for security headers
        @app.after_request
        def add_security_headers(response):
            """Add additional security headers"""
            # Remove server header (already handled by gunicorn/nginx)
            response.headers.pop('Server', None)
            
            # Add custom security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions Policy (formerly Feature Policy)
            response.headers['Permissions-Policy'] = (
                'geolocation=(), microphone=(), camera=(), '
                'payment=(), usb=(), magnetometer=(), gyroscope=()'
            )
            
            return response
    
    def _load_attack_patterns(self):
        """Load known attack patterns"""
        return [
            # Environment files
            r'\.env',
            r'\.env\.',
            r'\.env[0-9]',
            
            # Git metadata
            r'\.git',
            r'\.git/',
            r'\.gitignore',
            r'\.gitattributes',
            
            # Backup files
            r'\.(bak|backup|save|old|orig|swp|swo|tmp|temp)$',
            r'/backup',
            r'/backups',
            r'/old',
            r'/temp',
            
            # Configuration files
            r'wp-config',
            r'config\.(php|js|json|yaml|yml)',
            r'aws-config',
            r'aws\.config',
            
            # Build artifacts
            r'__pycache__',
            r'\.pyc$',
            r'\.pyo$',
            r'node_modules',
            
            # Version control
            r'\.svn',
            r'\.hg',
            
            # Database files
            r'\.(sql|dump|db|sqlite)$',
            r'database\.sql',
            r'dump\.sql',
            
            # PHP files (this is Python app)
            r'\.php$',
            r'phpinfo',
            r'phpmyadmin',
            r'xmlrpc',
            
            # Shell scripts
            r'shell\.php',
            r'cmd\.php',
            r'eval\.php',
            
            # Admin enumeration
            r'/admin/config',
            r'/admin/backup',
            r'/admin/database',
        ]
    
    def _get_client_ip(self):
        """Get client IP address, handling proxy headers"""
        # Check for proxy headers (set by ProxyFix middleware)
        if request.headers.get('X-Forwarded-For'):
            # X-Forwarded-For can contain multiple IPs, take the first
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'
    
    def _detect_attack_patterns(self, path):
        """Detect if request path matches attack patterns"""
        path_lower = path.lower()
        
        for pattern in self.attack_patterns:
            if re.search(pattern, path_lower, re.IGNORECASE):
                return pattern
        
        return None
    
    def _log_suspicious_activity(self, ip, path, pattern):
        """Log suspicious activity and track IP"""
        current_app.logger.warning(
            f"SECURITY ALERT: Suspicious request detected - "
            f"IP: {ip}, Path: {path}, Pattern: {pattern}"
        )
        
        # Track suspicious IP
        self.suspicious_ips[ip].append(time.time())
        
        # Clean old entries (older than 1 hour)
        cutoff = time.time() - 3600
        self.suspicious_ips[ip] = [
            ts for ts in self.suspicious_ips[ip] if ts > cutoff
        ]
        
        # Auto-block IPs with too many suspicious requests
        if len(self.suspicious_ips[ip]) >= 10:
            self.blocked_ips.add(ip)
            current_app.logger.error(
                f"SECURITY ALERT: Auto-blocked IP {ip} after 10 suspicious requests"
            )
    
    def _is_suspicious_ip(self, ip):
        """Check if IP has suspicious activity history"""
        if ip in self.suspicious_ips:
            # Check if recent activity (within last hour)
            recent_activity = [
                ts for ts in self.suspicious_ips[ip]
                if time.time() - ts < 3600
            ]
            return len(recent_activity) >= 3
        
        return False
    
    def _exceeded_rate_limit(self, ip):
        """Check if suspicious IP exceeded rate limit"""
        if ip not in self.suspicious_ips:
            return False
        
        # Count requests in last minute
        one_minute_ago = time.time() - 60
        recent_requests = [
            ts for ts in self.suspicious_ips[ip]
            if ts > one_minute_ago
        ]
        
        # Limit suspicious IPs to 5 requests per minute
        return len(recent_requests) >= 5
    
    def _block_response(self, message="Access denied", status_code=403):
        """Return blocked response"""
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'errors': [message]
            }), status_code
        else:
            return f'<html><head><title>{status_code}</title></head><body><h1>{status_code}</h1><p>{message}</p></body></html>', status_code


def require_admin_ip(allowed_ips=None):
    """
    Decorator to restrict admin routes to specific IPs
    
    Usage:
        @bp.route('/admin/users')
        @login_required
        @require_admin_ip(allowed_ips=['1.2.3.4', '5.6.7.8'])
        def admin_users():
            ...
    """
    if allowed_ips is None:
        # Get from environment variable
        allowed_ips_str = os.environ.get('ADMIN_ALLOWED_IPS', '').strip()
        if allowed_ips_str:
            allowed_ips = [ip.strip() for ip in allowed_ips_str.split(',')]
        else:
            # If no IPs configured, allow all (fallback to application-level auth)
            allowed_ips = []
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if allowed_ips:
                client_ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or \
                           request.headers.get('X-Real-IP', '') or \
                           request.remote_addr
                
                if client_ip not in allowed_ips:
                    current_app.logger.warning(
                        f"Admin access denied for IP {client_ip} (not in allowlist)"
                    )
                    return jsonify({
                        'success': False,
                        'errors': ['Access denied']
                    }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_security_event(event_type, details):
    """
    Log security events for monitoring and alerting
    
    Usage:
        log_security_event('failed_login', {
            'ip': request.remote_addr,
            'username': username,
            'timestamp': datetime.now().isoformat()
        })
    """
    current_app.logger.warning(
        f"SECURITY EVENT: {event_type} - {details}"
    )
    
    # In production, you might want to send this to:
    # - Security Information and Event Management (SIEM)
    # - Log aggregation service (Datadog, Splunk, etc.)
    # - Alerting system (PagerDuty, OpsGenie, etc.)


# Initialize middleware (will be called from main.py)
security_middleware = SecurityMiddleware()

