"""
AI Services models.
Models for storing AI-related data like responses and logs.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class AIRequestLog(models.Model):
    """
    Log of AI API requests.
    Used for monitoring, debugging, and cost tracking.
    """
    
    class ServiceType(models.TextChoices):
        DOCUMENT_VALIDATION = 'document_validation', _('Belge Validasyonu')
        TASK_PRIORITIZATION = 'task_prioritization', _('Görev Önceliklendirme')
        PROPOSAL_GENERATION = 'proposal_generation', _('Teklif Oluşturma')
        CUSTOMER_RESEARCH = 'customer_research', _('Müşteri Araştırması')
        SIGNATURE_DETECTION = 'signature_detection', _('İmza Tespiti')
        FORM_VALIDATION = 'form_validation', _('Form Validasyonu')
        ASSET_ANALYSIS = 'asset_analysis', _('Varlık Analizi')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Bekliyor')
        SUCCESS = 'success', _('Başarılı')
        FAILED = 'failed', _('Başarısız')
        TIMEOUT = 'timeout', _('Zaman Aşımı')
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_requests',
        verbose_name=_('Kullanıcı')
    )
    service_type = models.CharField(
        _('Servis Tipi'),
        max_length=30,
        choices=ServiceType.choices
    )
    model_name = models.CharField(
        _('Model Adı'),
        max_length=100,
        default='claude-sonnet-4-20250514'
    )
    
    # Request details
    prompt_tokens = models.PositiveIntegerField(
        _('Prompt Token Sayısı'),
        default=0
    )
    completion_tokens = models.PositiveIntegerField(
        _('Tamamlama Token Sayısı'),
        default=0
    )
    total_tokens = models.PositiveIntegerField(
        _('Toplam Token Sayısı'),
        default=0
    )
    
    # Response details
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    response_time_ms = models.PositiveIntegerField(
        _('Yanıt Süresi (ms)'),
        default=0
    )
    error_message = models.TextField(
        _('Hata Mesajı'),
        blank=True
    )
    
    # Metadata
    request_hash = models.CharField(
        _('İstek Hash'),
        max_length=64,
        blank=True,
        db_index=True
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
        verbose_name = _('AI İstek Logu')
        verbose_name_plural = _('AI İstek Logları')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.service_type} - {self.status} - {self.created_at}"
    
    @property
    def estimated_cost(self) -> float:
        """
        Calculate estimated cost based on token usage.
        Uses Claude Sonnet pricing (approximate).
        """
        # Claude Sonnet 4 pricing (approximate, per 1M tokens)
        input_cost_per_million = 3.0
        output_cost_per_million = 15.0
        
        input_cost = (self.prompt_tokens / 1_000_000) * input_cost_per_million
        output_cost = (self.completion_tokens / 1_000_000) * output_cost_per_million
        
        return round(input_cost + output_cost, 6)


class AIValidationResult(models.Model):
    """
    Stores AI validation results for documents.
    """
    
    document_id = models.PositiveIntegerField(
        _('Belge ID'),
        db_index=True
    )
    document_type = models.CharField(
        _('Belge Tipi'),
        max_length=100
    )
    
    # Validation results
    is_valid = models.BooleanField(
        _('Geçerli'),
        default=False
    )
    confidence_score = models.FloatField(
        _('Güven Skoru'),
        default=0.0
    )
    validation_details = models.JSONField(
        _('Validasyon Detayları'),
        default=dict
    )
    
    # Fields validation
    missing_fields = models.JSONField(
        _('Eksik Alanlar'),
        default=list
    )
    invalid_fields = models.JSONField(
        _('Geçersiz Alanlar'),
        default=list
    )
    warnings = models.JSONField(
        _('Uyarılar'),
        default=list
    )
    
    # AI reasoning
    ai_reasoning = models.TextField(
        _('AI Açıklaması'),
        blank=True
    )
    
    # Metadata
    request_log = models.ForeignKey(
        AIRequestLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validation_results',
        verbose_name=_('İstek Logu')
    )
    
    created_at = models.DateTimeField(
        _('Oluşturulma Tarihi'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('AI Validasyon Sonucu')
        verbose_name_plural = _('AI Validasyon Sonuçları')
        ordering = ['-created_at']
    
    def __str__(self):
        status = "Geçerli" if self.is_valid else "Geçersiz"
        return f"Doc #{self.document_id} - {status} ({self.confidence_score:.0%})"
