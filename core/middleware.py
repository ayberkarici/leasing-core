"""
Role-based routing middleware.
Redirects users to their appropriate dashboards based on user type.
"""

from django.shortcuts import redirect
from django.urls import reverse


class RoleBasedRoutingMiddleware:
    """
    Middleware that redirects users to their role-specific dashboards.
    
    - Admin users → Admin Dashboard
    - Salesperson users → Sales Dashboard
    - Customer users → Customer Dashboard
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Paths that don't require redirection
        self.exempt_paths = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/password-reset/',
            '/admin/',
            '/static/',
            '/media/',
            '/__debug__/',
        ]
    
    def __call__(self, request):
        # Check if path is exempt
        path = request.path
        if any(path.startswith(exempt) for exempt in self.exempt_paths):
            return self.get_response(request)
        
        # Only handle authenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Handle root path redirection
        if path == '/':
            return self.redirect_to_dashboard(request.user)
        
        # Allow customers to access KVKK download endpoint
        if path.startswith('/customers/kvkk/'):
            return self.get_response(request)
        
        # Check access permissions for specific areas
        if path.startswith('/customers/') or path.startswith('/tasks/'):
            if not self.can_access_sales_area(request.user):
                return redirect('customer_dashboard')
        
        if path.startswith('/admin-dashboard/'):
            if not self.can_access_admin_area(request.user):
                return redirect('dashboard')
        
        return self.get_response(request)
    
    def redirect_to_dashboard(self, user):
        """
        Redirect user to their appropriate dashboard.
        """
        if user.is_superuser or user.user_type == 'admin':
            return redirect('admin_dashboard')
        elif user.user_type == 'salesperson':
            return redirect('sales_dashboard')
        elif user.user_type == 'customer':
            return redirect('customer_dashboard')
        else:
            return redirect('dashboard')
    
    def can_access_sales_area(self, user):
        """
        Check if user can access sales-related pages.
        """
        return user.is_superuser or user.user_type in ['admin', 'salesperson']
    
    def can_access_admin_area(self, user):
        """
        Check if user can access admin-related pages.
        """
        return user.is_superuser or user.user_type == 'admin'


class CustomerAccessMiddleware:
    """
    Middleware that ensures customers can only access their own data.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response


class KVKKApprovalMiddleware:
    """
    Middleware that enforces KVKK approval for customer users.
    
    Customers MUST have approved KVKK before accessing any page.
    Workflow:
    1. Customer sees KVKK page with PDF download
    2. Customer downloads, gets signature, uploads signed document
    3. Salesperson reviews and approves
    4. Only then customer can access dashboard
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Paths that don't require KVKK approval
        self.exempt_paths = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/password-reset/',
            '/kvkk/',  # KVKK approval page itself
            '/customers/kvkk/',  # KVKK download etc
            '/admin/',
            '/static/',
            '/media/',
            '/__debug__/',
        ]
    
    def __call__(self, request):
        # Check if path is exempt
        path = request.path
        if any(path.startswith(exempt) for exempt in self.exempt_paths):
            return self.get_response(request)
        
        # Only check for authenticated customer users
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Only apply to customer users
        if request.user.user_type != 'customer':
            return self.get_response(request)
        
        # Check if customer has approved KVKK
        if hasattr(request.user, 'customer_profile') and request.user.customer_profile:
            customer = request.user.customer_profile
            
            # Check KVKK approval status
            if not customer.kvkk_approved:
                # Redirect to KVKK approval/waiting page
                return redirect('kvkk_approval')
        
        return self.get_response(request)


class ActivityTrackingMiddleware:
    """
    Middleware that tracks user activity.
    Updates last_activity timestamp for authenticated users.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Update last activity for authenticated users
        if request.user.is_authenticated:
            # Only update periodically to avoid excessive DB writes
            from django.utils import timezone
            from datetime import timedelta
            
            user = request.user
            now = timezone.now()
            
            # Update if last_activity is None or older than 5 minutes
            if not user.last_activity or (now - user.last_activity) > timedelta(minutes=5):
                user.last_activity = now
                user.save(update_fields=['last_activity'])
        
        return response


class RateLimitMiddleware:
    """
    Basit rate limiting middleware.
    API abuse'u önlemek için.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.cache = {}  # In production, use Django cache or Redis
        self.rate_limit = 100  # requests per minute
        self.window = 60  # seconds
    
    def __call__(self, request):
        from django.http import JsonResponse
        from django.utils import timezone
        import time
        
        # Only rate limit API endpoints
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Get client identifier
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries
        self.clean_old_entries(current_time)
        
        # Check rate limit
        if client_ip in self.cache:
            requests = self.cache[client_ip]
            if len(requests) >= self.rate_limit:
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': 'Çok fazla istek gönderdiniz. Lütfen bekleyin.'
                }, status=429)
            requests.append(current_time)
        else:
            self.cache[client_ip] = [current_time]
        
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', 'unknown')
    
    def clean_old_entries(self, current_time):
        """Remove entries older than the rate limit window."""
        cutoff = current_time - self.window
        for ip in list(self.cache.keys()):
            self.cache[ip] = [t for t in self.cache[ip] if t > cutoff]
            if not self.cache[ip]:
                del self.cache[ip]


class SecurityHeadersMiddleware:
    """
    Güvenlik header'ları ekleyen middleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy (basic)
        if not response.get('Content-Security-Policy'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.tailwindcss.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
        
        return response

