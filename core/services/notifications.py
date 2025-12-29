"""
Notification service for managing in-app notifications.
"""

from typing import Optional, List
from django.conf import settings
from django.db.models import QuerySet

from .base import BaseService, ServiceResult
from ..models import Notification


class NotificationService(BaseService):
    """
    Service for creating and managing notifications.
    """
    
    def create_notification(
        self,
        user,
        title: str,
        message: str,
        notification_type: str = Notification.NotificationType.INFO,
        link: Optional[str] = None
    ) -> ServiceResult:
        """
        Create a new notification for a user.
        
        Args:
            user: The user to receive the notification
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, success, warning, error)
            link: Optional URL to link to
        
        Returns:
            ServiceResult with the created notification
        """
        try:
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                link=link
            )
            self.log_info(f"Notification created for user {user.username}: {title}")
            return ServiceResult.ok(
                data=notification,
                message="Bildirim oluşturuldu"
            )
        except Exception as e:
            self.log_error(f"Failed to create notification: {str(e)}", exc=e)
            return ServiceResult.fail(
                message="Bildirim oluşturulamadı",
                errors={'exception': str(e)}
            )
    
    def get_user_notifications(
        self,
        user,
        unread_only: bool = False,
        limit: Optional[int] = None
    ) -> QuerySet:
        """
        Get notifications for a user.
        
        Args:
            user: The user to get notifications for
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return
        
        Returns:
            QuerySet of notifications
        """
        qs = Notification.objects.filter(user=user)
        
        if unread_only:
            qs = qs.filter(is_read=False)
        
        qs = qs.order_by('-created_at')
        
        if limit:
            qs = qs[:limit]
        
        return qs
    
    def get_unread_count(self, user) -> int:
        """
        Get the count of unread notifications for a user.
        """
        return Notification.objects.filter(user=user, is_read=False).count()
    
    def mark_as_read(self, notification_id: int, user) -> ServiceResult:
        """
        Mark a notification as read.
        """
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.mark_as_read()
            return ServiceResult.ok(message="Bildirim okundu olarak işaretlendi")
        except Notification.DoesNotExist:
            return ServiceResult.fail(message="Bildirim bulunamadı", code="NOT_FOUND")
        except Exception as e:
            self.log_error(f"Failed to mark notification as read: {str(e)}", exc=e)
            return ServiceResult.fail(message="İşlem başarısız")
    
    def mark_all_as_read(self, user) -> ServiceResult:
        """
        Mark all notifications as read for a user.
        """
        try:
            from django.utils import timezone
            updated = Notification.objects.filter(
                user=user, 
                is_read=False
            ).update(
                is_read=True, 
                read_at=timezone.now()
            )
            self.log_info(f"Marked {updated} notifications as read for user {user.username}")
            return ServiceResult.ok(
                data={'updated_count': updated},
                message=f"{updated} bildirim okundu olarak işaretlendi"
            )
        except Exception as e:
            self.log_error(f"Failed to mark all notifications as read: {str(e)}", exc=e)
            return ServiceResult.fail(message="İşlem başarısız")
    
    def delete_notification(self, notification_id: int, user) -> ServiceResult:
        """
        Delete a notification.
        """
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.delete()
            return ServiceResult.ok(message="Bildirim silindi")
        except Notification.DoesNotExist:
            return ServiceResult.fail(message="Bildirim bulunamadı", code="NOT_FOUND")
        except Exception as e:
            self.log_error(f"Failed to delete notification: {str(e)}", exc=e)
            return ServiceResult.fail(message="İşlem başarısız")
    
    # Convenience methods for creating specific notification types
    
    def notify_task_assigned(self, user, task_title: str, link: str = None):
        """Notify user about a new task assignment."""
        return self.create_notification(
            user=user,
            title="Yeni Görev Atandı",
            message=f"Size yeni bir görev atandı: {task_title}",
            notification_type=Notification.NotificationType.TASK,
            link=link
        )
    
    def notify_order_status_change(self, user, order_id: str, new_status: str, link: str = None):
        """Notify user about an order status change."""
        return self.create_notification(
            user=user,
            title="Sipariş Durumu Güncellendi",
            message=f"Sipariş #{order_id} durumu güncellendi: {new_status}",
            notification_type=Notification.NotificationType.ORDER,
            link=link
        )
    
    def notify_document_uploaded(self, user, document_name: str, link: str = None):
        """Notify user about a new document upload."""
        return self.create_notification(
            user=user,
            title="Yeni Belge Yüklendi",
            message=f"Yeni belge yüklendi: {document_name}",
            notification_type=Notification.NotificationType.DOCUMENT,
            link=link
        )
    
    def notify_approval_needed(self, user, item_type: str, item_title: str, link: str = None):
        """Notify user about an item needing approval."""
        return self.create_notification(
            user=user,
            title="Onay Bekliyor",
            message=f"{item_type} onayınızı bekliyor: {item_title}",
            notification_type=Notification.NotificationType.WARNING,
            link=link
        )

