"""
Task service.
Business logic for task management.
"""

from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from ..models import Task, TaskStatus, TaskType


class TaskService:
    """
    Görev işlemleri için servis sınıfı.
    """
    
    @staticmethod
    def get_tasks_for_user(user, filters=None):
        """
        Kullanıcının görevlerini getir.
        
        Args:
            user: User instance
            filters: Optional filters (status, task_type, search)
        """
        queryset = Task.objects.filter(
            assigned_to=user
        ).select_related('customer', 'created_by')
        
        if filters:
            if status := filters.get('status'):
                queryset = queryset.filter(status=status)
            if task_type := filters.get('task_type'):
                queryset = queryset.filter(task_type=task_type)
            if search := filters.get('search'):
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(customer__company_name__icontains=search)
                )
        
        return queryset.order_by('-ai_priority_score', 'due_date')
    
    @staticmethod
    def get_pending_tasks(user):
        """
        Bekleyen görevler (tamamlanmamış/iptal edilmemiş).
        """
        return Task.objects.filter(
            assigned_to=user,
            status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING_RESPONSE]
        ).select_related('customer').order_by('-ai_priority_score', 'due_date')
    
    @staticmethod
    def get_todays_priorities(user, limit=5):
        """
        Bugünün öncelikleri - AI skoruna göre sıralı.
        
        Args:
            user: User instance
            limit: Max tasks to return
        """
        return Task.objects.filter(
            assigned_to=user,
            status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
        ).select_related('customer').order_by('-ai_priority_score', 'due_date')[:limit]
    
    @staticmethod
    def get_overdue_tasks(user):
        """
        Gecikmiş görevler.
        """
        today = timezone.now().date()
        return Task.objects.filter(
            assigned_to=user,
            due_date__lt=today,
            status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING_RESPONSE]
        ).select_related('customer').order_by('due_date')
    
    @staticmethod
    def get_tasks_due_today(user):
        """
        Bugün son tarihli görevler.
        """
        today = timezone.now().date()
        return Task.objects.filter(
            assigned_to=user,
            due_date=today,
            status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
        ).select_related('customer').order_by('-ai_priority_score')
    
    @staticmethod
    def get_dashboard_stats(user):
        """
        Dashboard istatistikleri.
        """
        tasks = Task.objects.filter(assigned_to=user)
        today = timezone.now().date()
        
        stats = {
            'total': tasks.count(),
            'pending': tasks.filter(status=TaskStatus.PENDING).count(),
            'in_progress': tasks.filter(status=TaskStatus.IN_PROGRESS).count(),
            'waiting_response': tasks.filter(status=TaskStatus.WAITING_RESPONSE).count(),
            'completed': tasks.filter(status=TaskStatus.COMPLETED).count(),
            'overdue': tasks.filter(
                due_date__lt=today,
                status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING_RESPONSE]
            ).count(),
            'due_today': tasks.filter(
                due_date=today,
                status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
            ).count(),
            'high_priority': tasks.filter(
                ai_priority_score__gte=60,
                status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
            ).count(),
        }
        
        return stats
    
    @staticmethod
    def create_task(user, customer=None, **kwargs):
        """
        Yeni görev oluştur.
        
        Args:
            user: Oluşturan kullanıcı
            customer: İlgili müşteri (opsiyonel)
            **kwargs: Task fields
        """
        task = Task.objects.create(
            created_by=user,
            assigned_to=kwargs.pop('assigned_to', user),
            customer=customer,
            **kwargs
        )
        
        # Calculate initial priority
        task.ai_priority_score = task.calculate_base_priority()
        task.save()
        
        return task
    
    @staticmethod
    def update_task_status(task, new_status, user=None):
        """
        Görev durumunu güncelle.
        
        Args:
            task: Task instance
            new_status: New TaskStatus
            user: User making the change
        """
        task.status = new_status
        
        if new_status == TaskStatus.COMPLETED:
            task.completed_at = timezone.now()
        
        task.save()
        return task
    
    @staticmethod
    def recalculate_priorities(user):
        """
        Kullanıcının tüm bekleyen görevlerinin önceliklerini yeniden hesapla.
        
        Args:
            user: User instance
        """
        tasks = Task.objects.filter(
            assigned_to=user,
            status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING_RESPONSE]
        )
        
        for task in tasks:
            task.ai_priority_score = task.calculate_base_priority()
            task.save(update_fields=['ai_priority_score'])
        
        return tasks.count()



