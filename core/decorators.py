"""
Custom decorators for views and functions.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse


def user_type_required(*allowed_types):
    """
    Decorator to restrict access to specific user types.
    
    Args:
        *allowed_types: Allowed user types ('admin', 'salesperson', 'customer')
    
    Usage:
        @user_type_required('admin', 'salesperson')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Bu sayfayı görüntülemek için giriş yapmalısınız.')
                return redirect('accounts:login')
            
            # Superusers always have access
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check user type
            if request.user.user_type not in allowed_types:
                messages.error(request, 'Bu sayfaya erişim yetkiniz bulunmamaktadır.')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Decorator to restrict access to admin users only.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Bu sayfayı görüntülemek için giriş yapmalısınız.')
            return redirect('accounts:login')
        
        if not request.user.is_admin:
            messages.error(request, 'Bu sayfaya erişim yetkiniz bulunmamaktadır.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def salesperson_required(view_func):
    """
    Decorator to restrict access to salesperson users.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Bu sayfayı görüntülemek için giriş yapmalısınız.')
            return redirect('accounts:login')
        
        if not (request.user.is_salesperson or request.user.is_admin):
            messages.error(request, 'Bu sayfaya erişim yetkiniz bulunmamaktadır.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def customer_required(view_func):
    """
    Decorator to restrict access to customer users.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Bu sayfayı görüntülemek için giriş yapmalısınız.')
            return redirect('accounts:login')
        
        if not request.user.is_customer_user:
            messages.error(request, 'Bu sayfaya erişim yetkiniz bulunmamaktadır.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def ajax_required(view_func):
    """
    Decorator to ensure request is AJAX.
    Returns 400 Bad Request for non-AJAX requests.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'message': 'Invalid request'},
                status=400
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def verified_user_required(view_func):
    """
    Decorator to ensure user is verified.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Bu sayfayı görüntülemek için giriş yapmalısınız.')
            return redirect('accounts:login')
        
        if not request.user.is_verified and not request.user.is_superuser:
            messages.warning(request, 'Hesabınız henüz doğrulanmamış.')
            return redirect('accounts:verification_required')
        
        return view_func(request, *args, **kwargs)
    return wrapper

