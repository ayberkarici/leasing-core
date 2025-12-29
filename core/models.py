"""
Core app models.
Shared models used across the application.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """
    Abstract base model with created_at and updated_at fields.
    """
    created_at = models.DateTimeField(_('Oluşturulma Tarihi'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Güncellenme Tarihi'), auto_now=True)
    
    class Meta:
        abstract = True


class Notification(models.Model):
    """
    Bildirim modeli.
    In-app bildirimler için kullanılır.
    """
    
    class NotificationType(models.TextChoices):
        INFO = 'info', _('Bilgi')
        SUCCESS = 'success', _('Başarılı')
        WARNING = 'warning', _('Uyarı')
        ERROR = 'error', _('Hata')
        TASK = 'task', _('Görev')
        ORDER = 'order', _('Sipariş')
        DOCUMENT = 'document', _('Belge')
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('Kullanıcı')
    )
    notification_type = models.CharField(
        _('Bildirim Tipi'),
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO
    )
    title = models.CharField(
        _('Başlık'),
        max_length=200
    )
    message = models.TextField(
        _('Mesaj')
    )
    link = models.URLField(
        _('Bağlantı'),
        blank=True,
        null=True
    )
    is_read = models.BooleanField(
        _('Okundu'),
        default=False
    )
    read_at = models.DateTimeField(
        _('Okunma Tarihi'),
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        _('Oluşturulma Tarihi'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('Bildirim')
        verbose_name_plural = _('Bildirimler')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Bildirimi okundu olarak işaretle."""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class ActivityLog(models.Model):
    """
    Aktivite log modeli.
    Kullanıcı aktivitelerini takip etmek için kullanılır.
    """
    
    class ActionType(models.TextChoices):
        CREATE = 'create', _('Oluşturma')
        UPDATE = 'update', _('Güncelleme')
        DELETE = 'delete', _('Silme')
        VIEW = 'view', _('Görüntüleme')
        LOGIN = 'login', _('Giriş')
        LOGOUT = 'logout', _('Çıkış')
        UPLOAD = 'upload', _('Yükleme')
        DOWNLOAD = 'download', _('İndirme')
        APPROVE = 'approve', _('Onaylama')
        REJECT = 'reject', _('Reddetme')
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        verbose_name=_('Kullanıcı')
    )
    action_type = models.CharField(
        _('Aksiyon Tipi'),
        max_length=20,
        choices=ActionType.choices
    )
    model_name = models.CharField(
        _('Model Adı'),
        max_length=100,
        blank=True
    )
    object_id = models.PositiveIntegerField(
        _('Nesne ID'),
        null=True,
        blank=True
    )
    object_repr = models.CharField(
        _('Nesne Temsili'),
        max_length=200,
        blank=True
    )
    description = models.TextField(
        _('Açıklama'),
        blank=True
    )
    ip_address = models.GenericIPAddressField(
        _('IP Adresi'),
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        _('User Agent'),
        blank=True
    )
    extra_data = models.JSONField(
        _('Ekstra Veri'),
        default=dict,
        blank=True
    )
    created_at = models.DateTimeField(
        _('Oluşturulma Tarihi'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('Aktivite Logu')
        verbose_name_plural = _('Aktivite Logları')
        ordering = ['-created_at']
    
    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        return f"{user_str} - {self.action_type} - {self.model_name}"
