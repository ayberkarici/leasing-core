"""
Accounts app models.
Custom user model and department management.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    """
    Departman modeli.
    Şirket içi departmanları temsil eder (Satış, Finans, Hukuk, Operasyon).
    """
    
    class DepartmentType(models.TextChoices):
        SALES = 'sales', _('Satış')
        FINANCE = 'finance', _('Finans')
        LEGAL = 'legal', _('Hukuk')
        OPERATIONS = 'operations', _('Operasyon')
        IT = 'it', _('Bilgi Teknolojileri')
        HR = 'hr', _('İnsan Kaynakları')
    
    name = models.CharField(
        _('Departman Adı'),
        max_length=100,
        unique=True
    )
    department_type = models.CharField(
        _('Departman Tipi'),
        max_length=20,
        choices=DepartmentType.choices,
        default=DepartmentType.SALES
    )
    description = models.TextField(
        _('Açıklama'),
        blank=True
    )
    is_active = models.BooleanField(
        _('Aktif'),
        default=True
    )
    created_at = models.DateTimeField(
        _('Oluşturulma Tarihi'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Güncellenme Tarihi'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('Departman')
        verbose_name_plural = _('Departmanlar')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    """
    Özelleştirilmiş kullanıcı modeli.
    Admin, Satış Elemanı ve Müşteri rollerini destekler.
    """
    
    class UserType(models.TextChoices):
        ADMIN = 'admin', _('Yönetici')
        SALESPERSON = 'salesperson', _('Satış Elemanı')
        CUSTOMER = 'customer', _('Müşteri')
    
    # User type and department
    user_type = models.CharField(
        _('Kullanıcı Tipi'),
        max_length=20,
        choices=UserType.choices,
        default=UserType.CUSTOMER
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('Departman')
    )
    
    # Contact information
    phone = models.CharField(
        _('Telefon'),
        max_length=20,
        blank=True
    )
    
    # Profile
    avatar = models.ImageField(
        _('Profil Fotoğrafı'),
        upload_to='avatars/',
        blank=True,
        null=True
    )
    bio = models.TextField(
        _('Hakkında'),
        blank=True
    )
    
    # Status
    is_verified = models.BooleanField(
        _('Doğrulanmış'),
        default=False
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        _('Oluşturulma Tarihi'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Güncellenme Tarihi'),
        auto_now=True
    )
    last_activity = models.DateTimeField(
        _('Son Aktivite'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Kullanıcı')
        verbose_name_plural = _('Kullanıcılar')
        ordering = ['-created_at']
    
    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def full_name(self):
        """Tam ad döndürür."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def initials(self):
        """Ad soyadının baş harflerini döndürür."""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[0].upper() if self.username else "?"
    
    @property
    def is_admin(self):
        """Yönetici mi kontrol eder."""
        return self.user_type == self.UserType.ADMIN or self.is_superuser
    
    @property
    def is_salesperson(self):
        """Satış elemanı mı kontrol eder."""
        return self.user_type == self.UserType.SALESPERSON
    
    @property
    def is_customer_user(self):
        """Müşteri mi kontrol eder."""
        return self.user_type == self.UserType.CUSTOMER
    
    def get_dashboard_url(self):
        """Kullanıcı tipine göre dashboard URL'ini döndürür."""
        if self.is_admin:
            return '/admin-dashboard/'
        elif self.is_salesperson:
            return '/sales-dashboard/'
        else:
            return '/customer-dashboard/'
