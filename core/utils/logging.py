"""
Logging utilities for the application.
"""

import logging
from typing import Optional
from functools import wraps
from django.conf import settings


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_function_call(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function calls with arguments and return values.
    
    Args:
        logger: Logger instance to use (defaults to function's module logger)
    
    Usage:
        @log_function_call()
        def my_function(arg1, arg2):
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or logging.getLogger(func.__module__)
            
            # Log function call
            func_name = func.__qualname__
            _logger.debug(f"Calling {func_name} with args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                _logger.debug(f"{func_name} returned: {result}")
                return result
            except Exception as e:
                _logger.error(f"{func_name} raised exception: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator


def log_request(logger: Optional[logging.Logger] = None):
    """
    Decorator to log HTTP request details for views.
    
    Args:
        logger: Logger instance to use
    
    Usage:
        @log_request()
        def my_view(request):
            return response
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            _logger = logger or logging.getLogger(view_func.__module__)
            
            # Log request details
            _logger.info(
                f"Request: {request.method} {request.path} "
                f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'} "
                f"IP: {get_client_ip(request)}"
            )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def get_client_ip(request) -> str:
    """
    Get client IP address from request.
    Handles proxy headers.
    
    Args:
        request: Django HTTP request
    
    Returns:
        Client IP address string
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


class ActivityLogger:
    """
    Specialized logger for user activities.
    Logs to both standard logger and ActivityLog model.
    """
    
    def __init__(self, request=None):
        self.request = request
        self.logger = logging.getLogger('leasing_core.activity')
    
    def log(
        self,
        action_type: str,
        description: str,
        model_name: str = "",
        object_id: int = None,
        object_repr: str = "",
        extra_data: dict = None
    ):
        """
        Log an activity.
        
        Args:
            action_type: Type of action (create, update, delete, etc.)
            description: Human-readable description
            model_name: Name of the model being acted upon
            object_id: ID of the object being acted upon
            object_repr: String representation of the object
            extra_data: Additional data to store
        """
        from core.models import ActivityLog
        
        user = None
        ip_address = None
        user_agent = ""
        
        if self.request:
            if self.request.user.is_authenticated:
                user = self.request.user
            ip_address = get_client_ip(self.request)
            user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        
        # Log to standard logger
        self.logger.info(
            f"Activity: {action_type} | "
            f"User: {user.username if user else 'System'} | "
            f"Model: {model_name} | "
            f"Object: {object_repr} | "
            f"Description: {description}"
        )
        
        # Log to database
        try:
            ActivityLog.objects.create(
                user=user,
                action_type=action_type,
                model_name=model_name,
                object_id=object_id,
                object_repr=object_repr,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                extra_data=extra_data or {}
            )
        except Exception as e:
            self.logger.error(f"Failed to create activity log: {e}")

