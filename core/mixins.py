"""
Mixins for Django models and views.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages


class SalespersonRequiredMixin(LoginRequiredMixin):
    """
    Mixin that requires user to be a salesperson.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.user_type != 'salesperson' and not request.user.is_superuser:
            messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
            return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)


class CustomerRequiredMixin(LoginRequiredMixin):
    """
    Mixin that requires user to be a customer.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.user_type != 'customer' and not request.user.is_superuser:
            messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
            return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(LoginRequiredMixin):
    """
    Mixin that requires user to be an admin.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.user_type != 'admin' and not request.user.is_superuser:
            messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
            return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)


class AuditMixin(models.Model):
    """
    Mixin for audit trail functionality.
    Tracks who created and last modified a record.
    """
    
    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name=_('Oluşturan')
    )
    updated_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name=_('Güncelleyen')
    )
    
    class Meta:
        abstract = True
    
    def save_with_user(self, user, *args, **kwargs):
        """
        Save the model with user tracking.
        
        Args:
            user: The user performing the save operation
        """
        if not self.pk:
            self.created_by = user
        self.updated_by = user
        self.save(*args, **kwargs)


class SoftDeleteMixin(models.Model):
    """
    Mixin for soft delete functionality.
    Records are marked as deleted instead of being removed from database.
    """
    
    is_deleted = models.BooleanField(
        _('Silindi'),
        default=False,
        db_index=True
    )
    deleted_at = models.DateTimeField(
        _('Silinme Tarihi'),
        null=True,
        blank=True
    )
    deleted_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted',
        verbose_name=_('Silen')
    )
    
    class Meta:
        abstract = True
    
    def soft_delete(self, user=None):
        """
        Soft delete the record.
        
        Args:
            user: The user performing the delete operation
        """
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    def restore(self):
        """
        Restore a soft-deleted record.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class StatusMixin(models.Model):
    """
    Mixin for status tracking with history.
    """
    
    status = models.CharField(
        _('Durum'),
        max_length=50,
        default='pending'
    )
    status_changed_at = models.DateTimeField(
        _('Durum Değişiklik Tarihi'),
        null=True,
        blank=True
    )
    status_changed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_status_changes',
        verbose_name=_('Durumu Değiştiren')
    )
    
    class Meta:
        abstract = True
    
    def change_status(self, new_status: str, user=None):
        """
        Change the status of the record.
        
        Args:
            new_status: The new status value
            user: The user making the change
        """
        from django.utils import timezone
        
        old_status = self.status
        self.status = new_status
        self.status_changed_at = timezone.now()
        if user:
            self.status_changed_by = user
        self.save(update_fields=['status', 'status_changed_at', 'status_changed_by'])
        
        # Log the status change
        from core.utils.logging import ActivityLogger
        ActivityLogger().log(
            action_type='update',
            description=f"Durum değiştirildi: {old_status} -> {new_status}",
            model_name=self.__class__.__name__,
            object_id=self.pk,
            object_repr=str(self),
            extra_data={'old_status': old_status, 'new_status': new_status}
        )

