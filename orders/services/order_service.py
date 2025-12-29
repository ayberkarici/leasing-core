"""
Order service.
Business logic for order management.
"""

import logging
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone
from ..models import Order, OrderNote, OrderStatus, RequiredDocument

logger = logging.getLogger(__name__)


class OrderService:
    """
    Sipariş işlemleri için servis sınıfı.
    """
    
    @staticmethod
    def get_customer_orders(customer, status=None):
        """
        Müşterinin siparişlerini getir.
        """
        queryset = Order.objects.filter(
            customer=customer
        ).select_related('salesperson')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def get_salesperson_orders(salesperson, filters=None):
        """
        Satış elemanının siparişlerini getir.
        """
        queryset = Order.objects.filter(
            salesperson=salesperson
        ).select_related('customer')
        
        if filters:
            if status := filters.get('status'):
                queryset = queryset.filter(status=status)
            if search := filters.get('search'):
                queryset = queryset.filter(
                    Q(order_number__icontains=search) |
                    Q(customer__company_name__icontains=search)
                )
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def get_order_stats(salesperson=None, customer=None):
        """
        Sipariş istatistikleri.
        """
        queryset = Order.objects.all()
        
        if salesperson:
            queryset = queryset.filter(salesperson=salesperson)
        elif customer:
            queryset = queryset.filter(customer=customer)
        
        stats = {
            'total': queryset.count(),
            'draft': queryset.filter(status=OrderStatus.DRAFT).count(),
            'pending_docs': queryset.filter(status=OrderStatus.PENDING_DOCUMENTS).count(),
            'reviewing': queryset.filter(status=OrderStatus.DOCUMENTS_REVIEW).count(),
            'pending_approval': queryset.filter(status=OrderStatus.PENDING_APPROVAL).count(),
            'approved': queryset.filter(status=OrderStatus.APPROVED).count(),
            'processing': queryset.filter(status=OrderStatus.PROCESSING).count(),
            'completed': queryset.filter(status=OrderStatus.COMPLETED).count(),
            'cancelled': queryset.filter(status=OrderStatus.CANCELLED).count(),
        }
        
        # Active orders (not cancelled, rejected, or completed)
        stats['active'] = queryset.exclude(
            status__in=[OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.COMPLETED]
        ).count()
        
        return stats
    
    @staticmethod
    @transaction.atomic
    def create_order(customer, created_by, equipment_data, lease_data=None):
        """
        Yeni sipariş oluştur.
        
        Args:
            customer: Customer instance
            created_by: User creating the order
            equipment_data: Equipment information dict
            lease_data: Optional lease information dict
        
        Returns:
            Order instance
        """
        # Determine salesperson
        salesperson = customer.salesperson
        
        order = Order.objects.create(
            customer=customer,
            salesperson=salesperson,
            created_by=created_by,
            equipment_type=equipment_data.get('equipment_type', 'other'),
            equipment_brand=equipment_data.get('equipment_brand', ''),
            equipment_model=equipment_data.get('equipment_model', ''),
            equipment_year=equipment_data.get('equipment_year'),
            equipment_description=equipment_data.get('equipment_description', ''),
            equipment_quantity=equipment_data.get('equipment_quantity', 1),
            equipment_value=equipment_data.get('equipment_value', 0),
            status=OrderStatus.DRAFT
        )
        
        if lease_data:
            order.lease_type = lease_data.get('lease_type', 'financial')
            order.lease_term_months = lease_data.get('lease_term_months', 36)
            order.down_payment = lease_data.get('down_payment', 0)
            order.requested_delivery_date = lease_data.get('requested_delivery_date')
            order.save()
        
        # Create required documents
        OrderService.initialize_required_documents(order)
        
        logger.info(f"Order created: {order.order_number} for {customer.company_name}")
        
        return order
    
    @staticmethod
    def initialize_required_documents(order):
        """
        Sipariş için gerekli belgeleri oluştur.
        """
        from documents.models import DocumentTemplate
        
        templates = DocumentTemplate.objects.filter(
            is_active=True,
            is_required=True
        )
        
        for template in templates:
            RequiredDocument.objects.get_or_create(
                order=order,
                template=template
            )
    
    @staticmethod
    def update_order_step(order, step_data, step_number):
        """
        Wizard adımını güncelle.
        
        Args:
            order: Order instance
            step_data: Step data dict
            step_number: Current step number
        """
        if step_number == 1:
            # Equipment step
            order.equipment_type = step_data.get('equipment_type', order.equipment_type)
            order.equipment_brand = step_data.get('equipment_brand', '')
            order.equipment_model = step_data.get('equipment_model', '')
            order.equipment_year = step_data.get('equipment_year')
            order.equipment_description = step_data.get('equipment_description', '')
            order.equipment_quantity = step_data.get('equipment_quantity', 1)
            order.equipment_value = step_data.get('equipment_value', 0)
        
        elif step_number == 2:
            # Lease terms step
            order.lease_type = step_data.get('lease_type', 'financial')
            order.lease_term_months = step_data.get('lease_term_months', 36)
            order.down_payment = step_data.get('down_payment', 0)
            order.requested_delivery_date = step_data.get('requested_delivery_date')
            order.customer_notes = step_data.get('customer_notes', '')
        
        order.wizard_step = step_number + 1
        order.save()
        
        return order
    
    @staticmethod
    def submit_order(order, user=None):
        """
        Siparişi gönder.
        """
        if order.status == OrderStatus.DRAFT:
            order.status = OrderStatus.PENDING_DOCUMENTS
            order.wizard_completed = True
            order.save()
            
            OrderNote.objects.create(
                order=order,
                author=user,
                note_type=OrderNote.NoteType.STATUS_CHANGE,
                content="Sipariş oluşturuldu ve belge yüklemesi için hazır."
            )
            
            logger.info(f"Order submitted: {order.order_number}")
        
        return order
    
    @staticmethod
    def complete_document_upload(order, user=None):
        """
        Belge yüklemesini tamamla.
        """
        if order.status == OrderStatus.PENDING_DOCUMENTS:
            order.status = OrderStatus.DOCUMENTS_REVIEW
            order.submitted_at = timezone.now()
            order.save()
            
            OrderNote.objects.create(
                order=order,
                author=user,
                note_type=OrderNote.NoteType.DOCUMENT,
                content="Tüm belgeler yüklendi. İncelemeye alındı."
            )
            
            logger.info(f"Documents completed for order: {order.order_number}")
        
        return order
    
    @staticmethod
    def approve_documents(order, user):
        """
        Belgeleri onayla ve onay sürecine al.
        """
        if order.status == OrderStatus.DOCUMENTS_REVIEW:
            order.status = OrderStatus.PENDING_APPROVAL
            order.save()
            
            OrderNote.objects.create(
                order=order,
                author=user,
                note_type=OrderNote.NoteType.STATUS_CHANGE,
                content="Belgeler onaylandı. Sipariş onayı bekleniyor."
            )
        
        return order
    
    @staticmethod
    def approve_order(order, user):
        """
        Siparişi onayla.
        """
        order.approve(user)
        logger.info(f"Order approved: {order.order_number} by {user}")
        return order
    
    @staticmethod
    def reject_order(order, reason, user):
        """
        Siparişi reddet.
        """
        order.reject(reason, user)
        logger.info(f"Order rejected: {order.order_number} by {user}")
        return order
    
    @staticmethod
    def add_note(order, content, user, note_type='note', is_internal=False):
        """
        Siparişe not ekle.
        """
        note = OrderNote.objects.create(
            order=order,
            author=user,
            note_type=note_type,
            content=content,
            is_internal=is_internal
        )
        return note
    
    @staticmethod
    def get_order_timeline(order, include_internal=False):
        """
        Sipariş zaman çizelgesi.
        """
        queryset = order.notes.select_related('author')
        
        if not include_internal:
            queryset = queryset.filter(is_internal=False)
        
        return queryset.order_by('created_at')
    
    @staticmethod
    def get_active_orders_for_dashboard(salesperson):
        """
        Dashboard için aktif siparişler.
        """
        return Order.objects.filter(
            salesperson=salesperson
        ).exclude(
            status__in=[OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REJECTED]
        ).select_related('customer').order_by('-updated_at')[:10]
    
    @staticmethod
    def get_pending_approval_orders(salesperson=None):
        """
        Onay bekleyen siparişler.
        """
        queryset = Order.objects.filter(
            status=OrderStatus.PENDING_APPROVAL
        ).select_related('customer', 'salesperson')
        
        if salesperson:
            queryset = queryset.filter(salesperson=salesperson)
        
        return queryset.order_by('submitted_at')



