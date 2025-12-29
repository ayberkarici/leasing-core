"""
Dashboard statistics service.
Provides metrics and statistics for admin dashboard.
"""

from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()


class DashboardStatisticsService:
    """
    Admin dashboard istatistikleri için servis.
    """
    
    @staticmethod
    def get_user_stats():
        """
        Kullanıcı istatistikleri.
        """
        users = User.objects.all()
        
        return {
            'total': users.count(),
            'admins': users.filter(user_type='admin').count(),
            'salespersons': users.filter(user_type='salesperson').count(),
            'customers': users.filter(user_type='customer').count(),
            'active_today': users.filter(
                last_activity__date=timezone.now().date()
            ).count(),
            'active_week': users.filter(
                last_activity__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'new_this_month': users.filter(
                date_joined__month=timezone.now().month,
                date_joined__year=timezone.now().year
            ).count(),
        }
    
    @staticmethod
    def get_order_stats():
        """
        Sipariş istatistikleri.
        """
        from orders.models import Order, OrderStatus
        
        orders = Order.objects.all()
        now = timezone.now()
        
        return {
            'total': orders.count(),
            'pending_approval': orders.filter(status=OrderStatus.PENDING_APPROVAL).count(),
            'processing': orders.filter(status=OrderStatus.PROCESSING).count(),
            'completed': orders.filter(status=OrderStatus.COMPLETED).count(),
            'this_month': orders.filter(
                created_at__month=now.month,
                created_at__year=now.year
            ).count(),
            'total_value': orders.aggregate(Sum('equipment_value'))['equipment_value__sum'] or 0,
            'avg_value': orders.aggregate(Avg('equipment_value'))['equipment_value__avg'] or 0,
        }
    
    @staticmethod
    def get_customer_stats():
        """
        Müşteri istatistikleri.
        """
        from customers.models import Customer, CustomerStage
        
        customers = Customer.objects.all()
        now = timezone.now()
        
        return {
            'total': customers.count(),
            'active': customers.filter(is_active=True).count(),
            'new_this_month': customers.filter(
                created_at__month=now.month,
                created_at__year=now.year
            ).count(),
            'by_stage': {
                stage.value: customers.filter(stage=stage.value).count()
                for stage in CustomerStage
            },
            'won': customers.filter(stage=CustomerStage.WON).count(),
            'lost': customers.filter(stage=CustomerStage.LOST).count(),
        }
    
    @staticmethod
    def get_document_stats():
        """
        Belge istatistikleri.
        """
        from documents.models import UploadedDocument, DocumentStatus
        
        docs = UploadedDocument.objects.all()
        
        return {
            'total': docs.count(),
            'pending': docs.filter(status=DocumentStatus.UPLOADED).count(),
            'reviewing': docs.filter(status=DocumentStatus.REVIEWING).count(),
            'approved': docs.filter(status=DocumentStatus.APPROVED).count(),
            'rejected': docs.filter(status=DocumentStatus.REJECTED).count(),
        }
    
    @staticmethod
    def get_department_stats():
        """
        Departman bazlı istatistikler.
        """
        from accounts.models import Department
        from customers.models import Customer
        from orders.models import Order
        
        departments = Department.objects.all()
        stats = []
        
        for dept in departments:
            salespersons = User.objects.filter(department=dept, user_type='salesperson')
            salesperson_ids = salespersons.values_list('id', flat=True)
            
            customers = Customer.objects.filter(salesperson_id__in=salesperson_ids)
            orders = Order.objects.filter(salesperson_id__in=salesperson_ids)
            
            stats.append({
                'department': dept,
                'salesperson_count': salespersons.count(),
                'customer_count': customers.count(),
                'order_count': orders.count(),
                'total_value': orders.aggregate(Sum('equipment_value'))['equipment_value__sum'] or 0,
            })
        
        return stats
    
    @staticmethod
    def get_orders_by_month(months=6):
        """
        Aylık sipariş trendi.
        """
        from orders.models import Order
        
        start_date = timezone.now() - timedelta(days=months * 30)
        
        orders = Order.objects.filter(
            created_at__gte=start_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id'),
            total_value=Sum('equipment_value')
        ).order_by('month')
        
        return list(orders)
    
    @staticmethod
    def get_recent_activities(limit=20):
        """
        Son aktiviteler.
        """
        from core.models import ActivityLog
        
        return ActivityLog.objects.select_related(
            'user'
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def get_pending_approvals():
        """
        Onay bekleyen işlemler.
        """
        from orders.models import Order, OrderStatus
        from documents.models import UploadedDocument, DocumentStatus, KVKKDocument
        
        pending_orders = Order.objects.filter(
            status=OrderStatus.PENDING_APPROVAL
        ).select_related('customer', 'salesperson').order_by('submitted_at')[:10]
        
        pending_documents = UploadedDocument.objects.filter(
            status__in=[DocumentStatus.UPLOADED, DocumentStatus.REVIEWING]
        ).select_related('customer', 'uploaded_by').order_by('created_at')[:10]
        
        pending_kvkk = KVKKDocument.objects.filter(
            signed_document__isnull=False,
            status__in=['uploaded', 'pending_approval']
        ).select_related('customer').order_by('uploaded_at')[:10]
        
        return {
            'orders': pending_orders,
            'documents': pending_documents,
            'kvkk': pending_kvkk,
        }
    
    @staticmethod
    def get_system_health():
        """
        Sistem sağlığı metrikleri.
        """
        from ai_services.models import AIRequestLog
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        ai_requests = AIRequestLog.objects.filter(created_at__gte=last_24h)
        
        return {
            'ai_requests_24h': ai_requests.count(),
            'ai_success_rate': (
                ai_requests.filter(status='success').count() / ai_requests.count() * 100
                if ai_requests.count() > 0 else 100
            ),
            'ai_avg_response_time': ai_requests.aggregate(
                Avg('response_time')
            )['response_time__avg'] or 0,
            'total_users_online': User.objects.filter(
                last_activity__gte=now - timedelta(minutes=15)
            ).count(),
        }
    
    @staticmethod
    def get_salesperson_performance():
        """
        Satışçı performans sıralaması.
        """
        from customers.models import Customer, CustomerStage
        from orders.models import Order, OrderStatus
        
        salespersons = User.objects.filter(user_type='salesperson')
        
        performance = []
        for sp in salespersons:
            customers = Customer.objects.filter(salesperson=sp)
            orders = Order.objects.filter(salesperson=sp)
            
            won_customers = customers.filter(stage=CustomerStage.WON).count()
            total_value = orders.filter(
                status=OrderStatus.COMPLETED
            ).aggregate(Sum('equipment_value'))['equipment_value__sum'] or 0
            
            performance.append({
                'user': sp,
                'customer_count': customers.count(),
                'won_customers': won_customers,
                'order_count': orders.count(),
                'completed_orders': orders.filter(status=OrderStatus.COMPLETED).count(),
                'total_value': total_value,
                'conversion_rate': (won_customers / customers.count() * 100) if customers.count() > 0 else 0,
            })
        
        # Sort by total value
        performance.sort(key=lambda x: x['total_value'], reverse=True)
        
        return performance
    
    @staticmethod
    def get_customer_proposal_stats(customer):
        """
        Müşteri için teklif istatistikleri.
        """
        from proposals.models import Proposal
        
        proposals = Proposal.objects.filter(customer=customer)
        
        return {
            'total': proposals.count(),
            'active': proposals.filter(status__in=['draft', 'sent', 'viewed']).count(),
            'sent': proposals.filter(status='sent').count(),
            'accepted': proposals.filter(status='accepted').count(),
            'rejected': proposals.filter(status='rejected').count(),
        }
    
    @staticmethod
    def get_customer_recent_proposals(customer, limit=5):
        """
        Müşterinin son teklifleri.
        """
        from proposals.models import Proposal
        
        return Proposal.objects.filter(
            customer=customer
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def get_customer_document_count(customer):
        """
        Müşterinin toplam belge sayısı.
        """
        from documents.models import UploadedDocument, KVKKDocument
        
        uploaded_docs = UploadedDocument.objects.filter(customer=customer).count()
        kvkk_docs = KVKKDocument.objects.filter(customer=customer).count()
        
        return uploaded_docs + kvkk_docs



