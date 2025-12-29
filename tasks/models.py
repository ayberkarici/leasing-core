"""
Tasks app models.
Task management with AI-powered prioritization.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from decimal import Decimal


class TaskStatus(models.TextChoices):
    """Görev durumları."""
    PENDING = 'pending', _('Bekliyor')
    IN_PROGRESS = 'in_progress', _('Devam Ediyor')
    WAITING_RESPONSE = 'waiting_response', _('Cevap Bekleniyor')
    COMPLETED = 'completed', _('Tamamlandı')
    CANCELLED = 'cancelled', _('İptal Edildi')


class TaskType(models.TextChoices):
    """Görev tipleri."""
    FOLLOWUP = 'followup', _('Takip')
    PROPOSAL = 'proposal', _('Teklif Hazırla')
    DOCUMENT_REVIEW = 'document_review', _('Belge İncele')
    CALL = 'call', _('Telefon Görüşmesi')
    MEETING = 'meeting', _('Toplantı')
    APPROVAL = 'approval', _('Onay Bekliyor')
    CONTRACT = 'contract', _('Sözleşme')
    OTHER = 'other', _('Diğer')


class TaskPriority(models.TextChoices):
    """Görev öncelik seviyeleri (manuel)."""
    LOW = 'low', _('Düşük')
    MEDIUM = 'medium', _('Orta')
    HIGH = 'high', _('Yüksek')
    URGENT = 'urgent', _('Acil')


class Task(models.Model):
    """
    Görev modeli.
    Satış elemanlarının takip etmesi gereken görevler.
    """
    
    # Basic Information
    title = models.CharField(
        _('Başlık'),
        max_length=255
    )
    description = models.TextField(
        _('Açıklama'),
        blank=True
    )
    task_type = models.CharField(
        _('Görev Tipi'),
        max_length=20,
        choices=TaskType.choices,
        default=TaskType.FOLLOWUP
    )
    
    # Status & Priority
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING
    )
    manual_priority = models.CharField(
        _('Manuel Öncelik'),
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM
    )
    
    # AI Priority Score (0-100)
    ai_priority_score = models.IntegerField(
        _('AI Öncelik Skoru'),
        default=50,
        help_text=_('0-100 arası, AI tarafından hesaplanır')
    )
    ai_priority_reasoning = models.TextField(
        _('AI Öncelik Açıklaması'),
        blank=True,
        help_text=_('AI neden bu skoru verdiğini açıklar')
    )
    ai_priority_updated_at = models.DateTimeField(
        _('AI Skoru Güncellenme Tarihi'),
        null=True,
        blank=True
    )
    
    # Relationships
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_tasks',
        verbose_name=_('Atanan Kişi')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name=_('Oluşturan')
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name=_('Müşteri')
    )
    
    # Dates
    due_date = models.DateField(
        _('Son Tarih'),
        null=True,
        blank=True
    )
    reminder_date = models.DateTimeField(
        _('Hatırlatma Tarihi'),
        null=True,
        blank=True
    )
    completed_at = models.DateTimeField(
        _('Tamamlanma Tarihi'),
        null=True,
        blank=True
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
    
    class Meta:
        verbose_name = _('Görev')
        verbose_name_plural = _('Görevler')
        ordering = ['-ai_priority_score', 'due_date', '-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['due_date']),
            models.Index(fields=['ai_priority_score']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_overdue(self):
        """Görev gecikmiş mi?"""
        if self.due_date and self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return self.due_date < timezone.now().date()
        return False
    
    @property
    def days_until_due(self):
        """Son tarihe kalan gün sayısı."""
        if self.due_date:
            delta = self.due_date - timezone.now().date()
            return delta.days
        return None
    
    @property
    def status_display_class(self):
        """CSS class for status badge."""
        status_classes = {
            TaskStatus.PENDING: 'bg-slate-100 text-slate-700',
            TaskStatus.IN_PROGRESS: 'bg-blue-100 text-blue-700',
            TaskStatus.WAITING_RESPONSE: 'bg-amber-100 text-amber-700',
            TaskStatus.COMPLETED: 'bg-emerald-100 text-emerald-700',
            TaskStatus.CANCELLED: 'bg-red-100 text-red-700',
        }
        return status_classes.get(self.status, 'bg-slate-100 text-slate-700')
    
    @property
    def priority_display_class(self):
        """CSS class based on AI priority score."""
        if self.ai_priority_score >= 80:
            return 'bg-red-100 text-red-700 border-red-200'
        elif self.ai_priority_score >= 60:
            return 'bg-amber-100 text-amber-700 border-amber-200'
        elif self.ai_priority_score >= 40:
            return 'bg-blue-100 text-blue-700 border-blue-200'
        else:
            return 'bg-slate-100 text-slate-700 border-slate-200'
    
    @property
    def priority_label(self):
        """Label based on AI priority score."""
        if self.ai_priority_score >= 80:
            return _('Kritik')
        elif self.ai_priority_score >= 60:
            return _('Yüksek')
        elif self.ai_priority_score >= 40:
            return _('Orta')
        else:
            return _('Düşük')
    
    @property
    def task_type_icon(self):
        """Icon for task type."""
        icons = {
            TaskType.FOLLOWUP: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
            TaskType.PROPOSAL: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
            TaskType.DOCUMENT_REVIEW: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
            TaskType.CALL: 'M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z',
            TaskType.MEETING: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
            TaskType.APPROVAL: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
            TaskType.CONTRACT: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
            TaskType.OTHER: 'M4 6h16M4 12h16M4 18h16',
        }
        return icons.get(self.task_type, icons[TaskType.OTHER])
    
    def mark_completed(self):
        """Görevi tamamlandı olarak işaretle."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save()
    
    def calculate_base_priority(self):
        """
        Temel öncelik skorunu hesapla.
        Bu skor AI tarafından detaylandırılacak.
        """
        score = 50  # Base score
        
        # Due date factor
        if self.due_date:
            days = self.days_until_due
            if days is not None:
                if days < 0:  # Overdue
                    score += min(30, abs(days) * 3)
                elif days == 0:  # Today
                    score += 25
                elif days <= 3:
                    score += 15
                elif days <= 7:
                    score += 5
        
        # Customer priority factor
        if self.customer:
            priority_scores = {
                'critical': 20,
                'high': 15,
                'medium': 5,
                'low': 0,
            }
            score += priority_scores.get(self.customer.priority, 0)
            
            # Customer value factor
            if self.customer.estimated_value > Decimal('100000'):
                score += 10
            elif self.customer.estimated_value > Decimal('50000'):
                score += 5
        
        # Task type urgency
        urgent_types = [TaskType.APPROVAL, TaskType.CONTRACT, TaskType.CALL]
        if self.task_type in urgent_types:
            score += 10
        
        # Manual priority boost
        if self.manual_priority == TaskPriority.URGENT:
            score += 20
        elif self.manual_priority == TaskPriority.HIGH:
            score += 10
        
        return min(100, max(0, score))
