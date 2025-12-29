"""
Orders app models.
Order management and tracking.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class OrderStatus(models.TextChoices):
    """Sipariş durumları."""
    DRAFT = 'draft', _('Taslak')
    PENDING_DOCUMENTS = 'pending_docs', _('Belge Bekleniyor')
    DOCUMENTS_REVIEW = 'docs_review', _('Belgeler İnceleniyor')
    PENDING_APPROVAL = 'pending_approval', _('Onay Bekliyor')
    APPROVED = 'approved', _('Onaylandı')
    PROCESSING = 'processing', _('İşleniyor')
    READY_FOR_DELIVERY = 'ready', _('Teslime Hazır')
    DELIVERED = 'delivered', _('Teslim Edildi')
    COMPLETED = 'completed', _('Tamamlandı')
    CANCELLED = 'cancelled', _('İptal Edildi')
    REJECTED = 'rejected', _('Reddedildi')


class EquipmentType(models.TextChoices):
    """Ekipman türleri."""
    VEHICLE = 'vehicle', _('Araç')
    MACHINERY = 'machinery', _('İş Makinesi')
    COMPUTER = 'computer', _('Bilgisayar/IT')
    OFFICE = 'office', _('Ofis Ekipmanı')
    MEDICAL = 'medical', _('Medikal Cihaz')
    CONSTRUCTION = 'construction', _('İnşaat Ekipmanı')
    AGRICULTURAL = 'agricultural', _('Tarım Ekipmanı')
    OTHER = 'other', _('Diğer')


class LeaseType(models.TextChoices):
    """Kiralama türleri."""
    FINANCIAL = 'financial', _('Finansal Kiralama')
    OPERATIONAL = 'operational', _('Operasyonel Kiralama')
    SALE_LEASEBACK = 'leaseback', _('Sat-Geri Kirala')


class Order(models.Model):
    """
    Sipariş modeli.
    Müşterilerin leasing siparişlerini temsil eder.
    """
    
    # Benzersiz tanımlayıcı
    order_number = models.CharField(
        _('Sipariş Numarası'),
        max_length=20,
        unique=True,
        editable=False
    )
    
    # İlişkiler
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('Müşteri')
    )
    salesperson = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='handled_orders',
        verbose_name=_('Satış Temsilcisi'),
        limit_choices_to={'user_type': 'salesperson'}
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_orders',
        verbose_name=_('Oluşturan')
    )
    
    # Ekipman bilgileri
    equipment_type = models.CharField(
        _('Ekipman Türü'),
        max_length=20,
        choices=EquipmentType.choices
    )
    equipment_brand = models.CharField(
        _('Marka'),
        max_length=100,
        blank=True
    )
    equipment_model = models.CharField(
        _('Model'),
        max_length=100,
        blank=True
    )
    equipment_year = models.PositiveIntegerField(
        _('Yıl'),
        null=True,
        blank=True
    )
    equipment_description = models.TextField(
        _('Ekipman Açıklaması'),
        blank=True
    )
    equipment_quantity = models.PositiveIntegerField(
        _('Adet'),
        default=1
    )
    
    # Kiralama bilgileri
    lease_type = models.CharField(
        _('Kiralama Türü'),
        max_length=20,
        choices=LeaseType.choices,
        default=LeaseType.FINANCIAL
    )
    lease_term_months = models.PositiveIntegerField(
        _('Kiralama Süresi (Ay)'),
        default=36
    )
    
    # Finansal bilgiler
    equipment_value = models.DecimalField(
        _('Ekipman Değeri'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    down_payment = models.DecimalField(
        _('Peşinat'),
        max_digits=15,
        decimal_places=2,
        default=0
    )
    monthly_payment = models.DecimalField(
        _('Aylık Ödeme'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    total_amount = models.DecimalField(
        _('Toplam Tutar'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField(
        _('Para Birimi'),
        max_length=3,
        default='TRY'
    )
    
    # Durum
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT
    )
    
    # Tarihler
    requested_delivery_date = models.DateField(
        _('İstenen Teslim Tarihi'),
        null=True,
        blank=True
    )
    estimated_delivery_date = models.DateField(
        _('Tahmini Teslim Tarihi'),
        null=True,
        blank=True
    )
    actual_delivery_date = models.DateField(
        _('Gerçek Teslim Tarihi'),
        null=True,
        blank=True
    )
    lease_start_date = models.DateField(
        _('Kiralama Başlangıç Tarihi'),
        null=True,
        blank=True
    )
    lease_end_date = models.DateField(
        _('Kiralama Bitiş Tarihi'),
        null=True,
        blank=True
    )
    
    # Notlar
    customer_notes = models.TextField(
        _('Müşteri Notları'),
        blank=True
    )
    internal_notes = models.TextField(
        _('İç Notlar'),
        blank=True
    )
    rejection_reason = models.TextField(
        _('Red Sebebi'),
        blank=True
    )
    
    # Wizard durumu
    wizard_step = models.PositiveIntegerField(
        _('Wizard Adımı'),
        default=1
    )
    wizard_completed = models.BooleanField(
        _('Wizard Tamamlandı'),
        default=False
    )
    
    # Zaman damgaları
    created_at = models.DateTimeField(
        _('Oluşturulma Tarihi'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Güncellenme Tarihi'),
        auto_now=True
    )
    submitted_at = models.DateTimeField(
        _('Gönderilme Tarihi'),
        null=True,
        blank=True
    )
    approved_at = models.DateTimeField(
        _('Onay Tarihi'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Sipariş')
        verbose_name_plural = _('Siparişler')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['salesperson', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['order_number']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.company_name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_order_number():
        """Generate unique order number."""
        from django.utils import timezone
        import random
        date_part = timezone.now().strftime('%Y%m')
        random_part = str(random.randint(1000, 9999))
        return f"ORD-{date_part}-{random_part}"
    
    @property
    def status_display_class(self):
        """CSS class for status badge."""
        classes = {
            OrderStatus.DRAFT: 'bg-slate-100 text-slate-700',
            OrderStatus.PENDING_DOCUMENTS: 'bg-amber-100 text-amber-700',
            OrderStatus.DOCUMENTS_REVIEW: 'bg-blue-100 text-blue-700',
            OrderStatus.PENDING_APPROVAL: 'bg-purple-100 text-purple-700',
            OrderStatus.APPROVED: 'bg-emerald-100 text-emerald-700',
            OrderStatus.PROCESSING: 'bg-cyan-100 text-cyan-700',
            OrderStatus.READY_FOR_DELIVERY: 'bg-teal-100 text-teal-700',
            OrderStatus.DELIVERED: 'bg-green-100 text-green-700',
            OrderStatus.COMPLETED: 'bg-emerald-100 text-emerald-700',
            OrderStatus.CANCELLED: 'bg-gray-100 text-gray-700',
            OrderStatus.REJECTED: 'bg-red-100 text-red-700',
        }
        return classes.get(self.status, 'bg-slate-100 text-slate-700')
    
    @property
    def status_icon(self):
        """Icon for status."""
        icons = {
            OrderStatus.DRAFT: 'file-edit',
            OrderStatus.PENDING_DOCUMENTS: 'file-plus',
            OrderStatus.DOCUMENTS_REVIEW: 'search',
            OrderStatus.PENDING_APPROVAL: 'clock',
            OrderStatus.APPROVED: 'check-circle',
            OrderStatus.PROCESSING: 'loader',
            OrderStatus.READY_FOR_DELIVERY: 'package',
            OrderStatus.DELIVERED: 'truck',
            OrderStatus.COMPLETED: 'check-square',
            OrderStatus.CANCELLED: 'x-circle',
            OrderStatus.REJECTED: 'x-octagon',
        }
        return icons.get(self.status, 'file')
    
    @property
    def progress_percentage(self):
        """Progress percentage based on status."""
        progress = {
            OrderStatus.DRAFT: 10,
            OrderStatus.PENDING_DOCUMENTS: 20,
            OrderStatus.DOCUMENTS_REVIEW: 40,
            OrderStatus.PENDING_APPROVAL: 50,
            OrderStatus.APPROVED: 60,
            OrderStatus.PROCESSING: 70,
            OrderStatus.READY_FOR_DELIVERY: 85,
            OrderStatus.DELIVERED: 95,
            OrderStatus.COMPLETED: 100,
            OrderStatus.CANCELLED: 0,
            OrderStatus.REJECTED: 0,
        }
        return progress.get(self.status, 0)
    
    @property
    def down_payment_percentage(self):
        """Down payment as percentage of equipment value."""
        if self.equipment_value and self.equipment_value > 0:
            return (self.down_payment / self.equipment_value) * 100
        return 0
    
    @property
    def required_documents_count(self):
        """Number of required documents."""
        from documents.models import DocumentTemplate
        return DocumentTemplate.objects.filter(is_active=True, is_required=True).count()
    
    @property
    def uploaded_documents_count(self):
        """Number of uploaded documents."""
        return self.documents.count()
    
    @property
    def approved_documents_count(self):
        """Number of approved documents."""
        return self.documents.filter(status='approved').count()
    
    def can_submit(self):
        """Check if order can be submitted."""
        # All required documents must be uploaded
        from documents.models import DocumentTemplate
        required_types = DocumentTemplate.objects.filter(
            is_active=True, is_required=True
        ).values_list('document_type', flat=True)
        
        uploaded_types = self.documents.values_list('document_type', flat=True)
        
        return all(rt in uploaded_types for rt in required_types)
    
    def submit(self):
        """Submit order for processing."""
        from django.utils import timezone
        if self.status == OrderStatus.DRAFT:
            self.status = OrderStatus.PENDING_DOCUMENTS
        elif self.status == OrderStatus.PENDING_DOCUMENTS and self.can_submit():
            self.status = OrderStatus.DOCUMENTS_REVIEW
            self.submitted_at = timezone.now()
        self.save()
    
    def approve(self, user=None):
        """Approve order."""
        from django.utils import timezone
        self.status = OrderStatus.APPROVED
        self.approved_at = timezone.now()
        self.save()
        
        # Create timeline entry
        OrderNote.objects.create(
            order=self,
            author=user,
            note_type=OrderNote.NoteType.STATUS_CHANGE,
            content=f"Sipariş onaylandı."
        )
    
    def reject(self, reason, user=None):
        """Reject order."""
        self.status = OrderStatus.REJECTED
        self.rejection_reason = reason
        self.save()
        
        # Create timeline entry
        OrderNote.objects.create(
            order=self,
            author=user,
            note_type=OrderNote.NoteType.STATUS_CHANGE,
            content=f"Sipariş reddedildi: {reason}"
        )


class OrderNote(models.Model):
    """
    Sipariş notu/timeline modeli.
    Sipariş geçmişini ve notlarını takip eder.
    """
    
    class NoteType(models.TextChoices):
        NOTE = 'note', _('Not')
        STATUS_CHANGE = 'status', _('Durum Değişikliği')
        DOCUMENT = 'document', _('Belge')
        SYSTEM = 'system', _('Sistem')
        CUSTOMER = 'customer', _('Müşteri Mesajı')
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name=_('Sipariş')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_notes',
        verbose_name=_('Yazar')
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
    is_internal = models.BooleanField(
        _('İç Not'),
        default=False,
        help_text=_('İç notlar müşteri tarafından görülmez')
    )
    is_pinned = models.BooleanField(
        _('Sabitlenmiş'),
        default=False
    )
    created_at = models.DateTimeField(
        _('Oluşturulma Tarihi'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('Sipariş Notu')
        verbose_name_plural = _('Sipariş Notları')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.get_note_type_display()}"
    
    @property
    def note_type_icon(self):
        """Icon for note type."""
        icons = {
            self.NoteType.NOTE: 'message-square',
            self.NoteType.STATUS_CHANGE: 'refresh-cw',
            self.NoteType.DOCUMENT: 'file',
            self.NoteType.SYSTEM: 'settings',
            self.NoteType.CUSTOMER: 'user',
        }
        return icons.get(self.note_type, 'message-square')
    
    @property
    def note_type_color(self):
        """Color for note type."""
        colors = {
            self.NoteType.NOTE: 'text-slate-600',
            self.NoteType.STATUS_CHANGE: 'text-blue-600',
            self.NoteType.DOCUMENT: 'text-purple-600',
            self.NoteType.SYSTEM: 'text-gray-600',
            self.NoteType.CUSTOMER: 'text-emerald-600',
        }
        return colors.get(self.note_type, 'text-slate-600')


class RequiredDocument(models.Model):
    """
    Sipariş için gerekli belge ilişkisi.
    Her sipariş için hangi belgelerin gerekli olduğunu tanımlar.
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='required_documents',
        verbose_name=_('Sipariş')
    )
    template = models.ForeignKey(
        'documents.DocumentTemplate',
        on_delete=models.CASCADE,
        related_name='order_requirements',
        verbose_name=_('Belge Şablonu')
    )
    is_satisfied = models.BooleanField(
        _('Tamamlandı'),
        default=False
    )
    uploaded_document = models.ForeignKey(
        'documents.UploadedDocument',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requirement',
        verbose_name=_('Yüklenen Belge')
    )
    
    class Meta:
        verbose_name = _('Gerekli Belge')
        verbose_name_plural = _('Gerekli Belgeler')
        unique_together = ['order', 'template']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.template.name}"
