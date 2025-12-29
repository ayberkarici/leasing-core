"""
Base service class for all services in the application.
Provides common functionality like logging and error handling.
"""

import logging
from typing import Any, Dict, Optional
from django.db import transaction


class BaseService:
    """
    Base service class providing common functionality.
    All service classes should inherit from this.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__module__)
    
    def log_info(self, message: str, **kwargs):
        """Log an info message."""
        self.logger.info(f"{self.__class__.__name__}: {message}", extra=kwargs)
    
    def log_error(self, message: str, exc: Optional[Exception] = None, **kwargs):
        """Log an error message."""
        self.logger.error(
            f"{self.__class__.__name__}: {message}", 
            exc_info=exc,
            extra=kwargs
        )
    
    def log_warning(self, message: str, **kwargs):
        """Log a warning message."""
        self.logger.warning(f"{self.__class__.__name__}: {message}", extra=kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log a debug message."""
        self.logger.debug(f"{self.__class__.__name__}: {message}", extra=kwargs)


class ServiceResult:
    """
    Standard result object for service operations.
    Provides consistent response structure across all services.
    """
    
    def __init__(
        self,
        success: bool,
        data: Optional[Any] = None,
        message: str = "",
        errors: Optional[Dict[str, Any]] = None,
        code: str = ""
    ):
        self.success = success
        self.data = data
        self.message = message
        self.errors = errors or {}
        self.code = code
    
    @classmethod
    def ok(cls, data: Any = None, message: str = "İşlem başarılı"):
        """Create a successful result."""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def fail(
        cls, 
        message: str = "İşlem başarısız", 
        errors: Optional[Dict[str, Any]] = None,
        code: str = "ERROR"
    ):
        """Create a failed result."""
        return cls(success=False, message=message, errors=errors, code=code)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'data': self.data,
            'message': self.message,
            'errors': self.errors,
            'code': self.code
        }
    
    def __bool__(self):
        return self.success

