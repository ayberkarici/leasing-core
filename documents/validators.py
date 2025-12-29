"""
Document validators.
File type and size validation for uploads.
"""

import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Try to import python-magic for content type validation
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


# Allowed MIME types
ALLOWED_MIME_TYPES = {
    'application/pdf': ['pdf'],
    'application/msword': ['doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['docx'],
    'application/vnd.ms-excel': ['xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['xlsx'],
    'image/jpeg': ['jpg', 'jpeg'],
    'image/png': ['png'],
    'image/gif': ['gif'],
}

# Max file size (10MB)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def validate_file_extension(file, allowed_extensions=None):
    """
    Validate file extension.
    
    Args:
        file: Uploaded file object
        allowed_extensions: List of allowed extensions (without dot)
    
    Raises:
        ValidationError: If extension is not allowed
    """
    if allowed_extensions is None:
        allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'xls', 'xlsx']
    
    ext = os.path.splitext(file.name)[1].lower().lstrip('.')
    
    if ext not in allowed_extensions:
        raise ValidationError(
            _('Dosya uzantısı desteklenmiyor. İzin verilen uzantılar: %(extensions)s'),
            params={'extensions': ', '.join(allowed_extensions)},
            code='invalid_extension'
        )


def validate_file_size(file, max_size_mb=10):
    """
    Validate file size.
    
    Args:
        file: Uploaded file object
        max_size_mb: Maximum file size in MB
    
    Raises:
        ValidationError: If file is too large
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file.size > max_size_bytes:
        raise ValidationError(
            _('Dosya boyutu çok büyük. Maksimum boyut: %(max_size)s MB'),
            params={'max_size': max_size_mb},
            code='file_too_large'
        )


def validate_file_content_type(file):
    """
    Validate file content type using magic bytes.
    Ensures file content matches its extension.
    
    Args:
        file: Uploaded file object
    
    Raises:
        ValidationError: If content type doesn't match extension
    """
    if not HAS_MAGIC:
        # Skip content type validation if magic is not available
        return
    
    # Read first 2048 bytes to detect file type
    file.seek(0)
    file_header = file.read(2048)
    file.seek(0)
    
    try:
        detected_mime = magic.from_buffer(file_header, mime=True)
    except Exception:
        # If magic fails, skip content type validation
        return
    
    # Get extension
    ext = os.path.splitext(file.name)[1].lower().lstrip('.')
    
    # Check if detected MIME type allows this extension
    allowed_extensions = ALLOWED_MIME_TYPES.get(detected_mime, [])
    
    if ext not in allowed_extensions and detected_mime not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            _('Dosya içeriği uzantısıyla uyuşmuyor. Güvenlik nedeniyle reddedildi.'),
            code='content_type_mismatch'
        )


def validate_document_file(file, allowed_extensions=None, max_size_mb=10):
    """
    Comprehensive file validation.
    
    Args:
        file: Uploaded file object
        allowed_extensions: List of allowed extensions
        max_size_mb: Maximum file size in MB
    
    Raises:
        ValidationError: If any validation fails
    """
    validate_file_extension(file, allowed_extensions)
    validate_file_size(file, max_size_mb)
    
    # Content type validation is optional (requires python-magic)
    try:
        validate_file_content_type(file)
    except ImportError:
        pass


class DocumentFileValidator:
    """
    Reusable file validator class.
    """
    
    def __init__(self, allowed_extensions=None, max_size_mb=10):
        self.allowed_extensions = allowed_extensions
        self.max_size_mb = max_size_mb
    
    def __call__(self, file):
        validate_document_file(file, self.allowed_extensions, self.max_size_mb)
    
    def __eq__(self, other):
        return (
            isinstance(other, DocumentFileValidator) and
            self.allowed_extensions == other.allowed_extensions and
            self.max_size_mb == other.max_size_mb
        )


# Pre-configured validators
pdf_validator = DocumentFileValidator(allowed_extensions=['pdf'], max_size_mb=10)
image_validator = DocumentFileValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'], max_size_mb=5)
document_validator = DocumentFileValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx'], max_size_mb=10)
any_document_validator = DocumentFileValidator(max_size_mb=10)

