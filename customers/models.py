"""
Customers app models.
Customer management and relationship tracking.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Company(models.Model):
    """
    Şirket modeli.
    Müşterilerin bağlı olduğu şirketleri temsil eder.
    """
    
    name = models.CharField(
        _('Şirket Adı'),
        max_length=255,
        unique=True
    )
    tax_number = models.CharField(
        _('Vergi Numarası'),
        max_length=20,
        blank=True
    )
    tax_office = models.CharField(
        _('Vergi Dairesi'),
        max_length=100,
        blank=True
    )
    sector = models.CharField(
        _('Sektör'),
        max_length=100,
        blank=True
    )
    address = models.TextField(
        _('Adres'),
        blank=True
    )
    city = models.CharField(
        _('Şehir'),
        max_length=100,
        blank=True
    )
    phone = models.CharField(
        _('Telefon'),
        max_length=20,
        blank=True
    )
    website = models.URLField(
        _('Website'),
        blank=True
    )
    company_size = models.CharField(
        _('Şirket Büyüklüğü'),
        max_length=50,
        blank=True,
        help_text=_('Örn: 1-10, 11-50, 51-200, 200+')
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
        verbose_name = _('Şirket')
        verbose_name_plural = _('Şirketler')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CustomerStage(models.TextChoices):
    """Müşteri aşamaları - satış hunisi."""
    LEAD = 'lead', _('Potansiyel')
    CONTACTED = 'contacted', _('İletişime Geçildi')
    QUALIFIED = 'qualified', _('Değerlendirildi')
    PROPOSAL_SENT = 'proposal_sent', _('Teklif Gönderildi')
    NEGOTIATION = 'negotiation', _('Müzakere')
    CONTRACT = 'contract', _('Sözleşme Aşaması')
    WON = 'won', _('Kazanıldı')
    LOST = 'lost', _('Kaybedildi')


class CustomerPriority(models.TextChoices):
    """Müşteri öncelik seviyeleri."""
    LOW = 'low', _('Düşük')
    MEDIUM = 'medium', _('Orta')
    HIGH = 'high', _('Yüksek')
    CRITICAL = 'critical', _('Kritik')


class Customer(models.Model):
    """
    Müşteri modeli.
    Satış elemanlarının takip ettiği müşterileri temsil eder.
    """
    
    # Company Relationship
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
        verbose_name=_('Şirket')
    )
    
    # Keep for backwards compatibility (will be populated from company)
    company_name = models.CharField(
        _('Şirket Adı'),
        max_length=255,
        blank=True
    )
    
    # Basic Information
    contact_person = models.CharField(
        _('İlgili Kişi'),
        max_length=255
    )
    email = models.EmailField(
        _('Email'),
        unique=True
    )
    phone = models.CharField(
        _('Telefon'),
        max_length=20
    )
    secondary_phone = models.CharField(
        _('İkinci Telefon'),
        max_length=20,
        blank=True
    )
    
    # Address (kept for backwards compatibility but not shown in form)
    address = models.TextField(
        _('Adres'),
        blank=True
    )
    city = models.CharField(
        _('Şehir'),
        max_length=100,
        blank=True
    )
    
    # Business Information (kept for backwards compatibility but not shown in form)
    tax_number = models.CharField(
        _('Vergi Numarası'),
        max_length=20,
        blank=True
    )
    tax_office = models.CharField(
        _('Vergi Dairesi'),
        max_length=100,
        blank=True
    )
    sector = models.CharField(
        _('Sektör'),
        max_length=100,
        blank=True
    )
    company_size = models.CharField(
        _('Şirket Büyüklüğü'),
        max_length=50,
        blank=True,
        help_text=_('Örn: 1-10, 11-50, 51-200, 200+')
    )
    
    # Stage & Status
    stage = models.CharField(
        _('Aşama'),
        max_length=20,
        choices=CustomerStage.choices,
        default=CustomerStage.LEAD
    )
    priority = models.CharField(
        _('Öncelik'),
        max_length=20,
        choices=CustomerPriority.choices,
        default=CustomerPriority.MEDIUM
    )
    is_active = models.BooleanField(
        _('Aktif'),
        default=True
    )
    
    # KVKK Onay Durumu
    kvkk_approved = models.BooleanField(
        _('KVKK Onaylandı'),
        default=False,
        help_text=_('Müşteri KVKK metnini onayladı mı?')
    )
    kvkk_approved_at = models.DateTimeField(
        _('KVKK Onay Tarihi'),
        null=True,
        blank=True
    )
    kvkk_ip_address = models.GenericIPAddressField(
        _('KVKK Onay IP'),
        null=True,
        blank=True,
        help_text=_('KVKK onayı yapılan IP adresi')
    )
    
    # Relationships
    salesperson = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='customers',
        verbose_name=_('Satış Temsilcisi'),
        limit_choices_to={'user_type': 'salesperson'}
    )
    user_account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_profile',
        verbose_name=_('Kullanıcı Hesabı'),
        help_text=_('Müşteri portal girişi için')
    )
    
    # Financial
    estimated_value = models.DecimalField(
        _('Tahmini Değer'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    # Notes
    notes = models.TextField(
        _('Notlar'),
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
    last_contact_date = models.DateTimeField(
        _('Son İletişim Tarihi'),
        null=True,
        blank=True
    )
    next_followup_date = models.DateField(
        _('Sonraki Takip Tarihi'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Müşteri')
        verbose_name_plural = _('Müşteriler')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stage']),
            models.Index(fields=['salesperson']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        company = self.company.name if self.company else self.company_name
        return f"{company} - {self.contact_person}"
    
    def save(self, *args, **kwargs):
        # Sync company_name from company relationship
        if self.company:
            self.company_name = self.company.name
        super().save(*args, **kwargs)
    
    @property
    def display_company_name(self):
        """Get company name from relationship or field."""
        return self.company.name if self.company else self.company_name
    
    @property
    def stage_display_class(self):
        """CSS class for stage badge."""
        stage_classes = {
            CustomerStage.LEAD: 'bg-slate-100 text-slate-700',
            CustomerStage.CONTACTED: 'bg-blue-100 text-blue-700',
            CustomerStage.QUALIFIED: 'bg-cyan-100 text-cyan-700',
            CustomerStage.PROPOSAL_SENT: 'bg-purple-100 text-purple-700',
            CustomerStage.NEGOTIATION: 'bg-amber-100 text-amber-700',
            CustomerStage.CONTRACT: 'bg-orange-100 text-orange-700',
            CustomerStage.WON: 'bg-emerald-100 text-emerald-700',
            CustomerStage.LOST: 'bg-red-100 text-red-700',
        }
        return stage_classes.get(self.stage, 'bg-slate-100 text-slate-700')
    
    @property
    def priority_display_class(self):
        """CSS class for priority badge."""
        priority_classes = {
            CustomerPriority.LOW: 'bg-slate-100 text-slate-600',
            CustomerPriority.MEDIUM: 'bg-blue-100 text-blue-600',
            CustomerPriority.HIGH: 'bg-amber-100 text-amber-600',
            CustomerPriority.CRITICAL: 'bg-red-100 text-red-600',
        }
        return priority_classes.get(self.priority, 'bg-slate-100 text-slate-600')


class CustomerNote(models.Model):
    """
    Müşteri notu modeli.
    Müşteri ile ilgili aktivite ve notları takip eder.
    """
    
    class NoteType(models.TextChoices):
        CALL = 'call', _('Telefon Görüşmesi')
        MEETING = 'meeting', _('Toplantı')
        EMAIL = 'email', _('Email')
        NOTE = 'note', _('Not')
        TASK = 'task', _('Görev')
        STATUS_CHANGE = 'status_change', _('Durum Değişikliği')
        CUSTOMER_REQUEST = 'customer_request', _('Müşteri İsteği')
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='customer_notes',
        verbose_name=_('Müşteri')
    )
    note_type = models.CharField(
        _('Not Tipi'),
        max_length=20,
        choices=NoteType.choices,
        default=NoteType.NOTE
    )
    content = models.TextField(
        _('İçerik')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='customer_notes_created',
        verbose_name=_('Oluşturan')
    )
    created_at = models.DateTimeField(
        _('Oluşturulma Tarihi'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('Müşteri Notu')
        verbose_name_plural = _('Müşteri Notları')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.display_company_name} - {self.get_note_type_display()}"
    
    @property
    def note_type_icon(self):
        """Icon for note type."""
        icons = {
            self.NoteType.CALL: 'phone',
            self.NoteType.MEETING: 'calendar',
            self.NoteType.EMAIL: 'mail',
            self.NoteType.NOTE: 'file-text',
            self.NoteType.TASK: 'check-square',
            self.NoteType.STATUS_CHANGE: 'activity',
            self.NoteType.CUSTOMER_REQUEST: 'message-circle',
        }
        return icons.get(self.note_type, 'file')
