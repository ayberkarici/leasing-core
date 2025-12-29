"""
Order signals.
Handles order status change notifications.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order, OrderNote, OrderStatus


@receiver(pre_save, sender=Order)
def track_status_change(sender, instance, **kwargs):
    """Track order status changes."""
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Order)
def create_status_change_note(sender, instance, created, **kwargs):
    """Create timeline entry when status changes."""
    if created:
        # New order created
        OrderNote.objects.create(
            order=instance,
            note_type=OrderNote.NoteType.SYSTEM,
            content="Sipariş oluşturuldu.",
            is_internal=False
        )
    elif hasattr(instance, '_old_status') and instance._old_status != instance.status:
        # Status changed
        old_status_display = dict(OrderStatus.choices).get(instance._old_status, instance._old_status)
        new_status_display = instance.get_status_display()
        
        OrderNote.objects.create(
            order=instance,
            note_type=OrderNote.NoteType.STATUS_CHANGE,
            content=f"Sipariş durumu değişti: {old_status_display} → {new_status_display}",
            is_internal=False
        )
        
        # Send notification to customer
        _notify_customer_status_change(instance)


def _notify_customer_status_change(order):
    """Send notification to customer about status change."""
    from core.models import Notification
    
    if order.customer and order.customer.user_account:
        Notification.objects.create(
            user=order.customer.user_account,
            title="Sipariş Durumu Güncellendi",
            message=f"Siparişiniz ({order.order_number}) durumu: {order.get_status_display()}",
            notification_type='order',
            related_object_id=order.pk,
            related_object_type='order'
        )



