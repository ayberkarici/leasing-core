"""
Documents app models.
KVKK document management and file uploads.
"""

import os
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import FileExtensionValidator


def document_upload_path(instance, filename):
    """Generate upload path for documents."""
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    if hasattr(instance, 'customer') and instance.customer:
        return f"documents/customer_{instance.customer.id}/{new_filename}"
    elif hasattr(instance, 'order') and instance.order:
        return f"documents/order_{instance.order.id}/{new_filename}"
    return f"documents/general/{new_filename}"


class DocumentType(models.TextChoices):
    """Belge tipleri."""
    KVKK = 'kvkk', _('KVKK Onay Formu')
    ID_CARD = 'id_card', _('Kimlik Fotokopisi')
    TAX_CERTIFICATE = 'tax_cert', _('Vergi Levhası')
    SIGNATURE_CIRCULAR = 'signature', _('İmza Sirküleri')
    TRADE_REGISTRY = 'trade_reg', _('Ticaret Sicil Gazetesi')
    FINANCIAL_STATEMENT = 'financial', _('Mali Tablolar')
    INVOICE = 'invoice', _('Fatura')
    CONTRACT = 'contract', _('Sözleşme')
    PROPOSAL = 'proposal', _('Teklif')
    OTHER = 'other', _('Diğer')


class DocumentStatus(models.TextChoices):
    """Belge durumları."""
    PENDING = 'pending', _('Beklemede')
    UPLOADED = 'uploaded', _('Yüklendi')
    REVIEWING = 'reviewing', _('İnceleniyor')
    APPROVED = 'approved', _('Onaylandı')
    REJECTED = 'rejected', _('Reddedildi')
    EXPIRED = 'expired', _('Süresi Doldu')


class DocumentTemplate(models.Model):
    """
    Belge şablonu modeli.
    Siparişler için gerekli belge türlerini tanımlar.
    """
    
    name = models.CharField(
        _('Şablon Adı'),
        max_length=255
    )
    document_type = models.CharField(
        _('Belge Tipi'),
        max_length=20,
        choices=DocumentType.choices
    )
    description = models.TextField(
        _('Açıklama'),
        blank=True
    )
    is_required = models.BooleanField(
        _('Zorunlu'),
        default=True
    )
    allowed_extensions = models.CharField(
        _('İzin Verilen Uzantılar'),
        max_length=100,
        default='pdf,doc,docx,jpg,jpeg,png',
        help_text=_('Virgülle ayrılmış uzantılar')
    )
    max_file_size_mb = models.PositiveIntegerField(
        _('Maksimum Dosya Boyutu (MB)'),
        default=10
    )
    sample_file = models.FileField(
        _('Örnek Dosya'),
        upload_to='document_templates/',
        blank=True,
        null=True
    )
    instructions = models.TextField(
        _('Yükleme Talimatları'),
        blank=True
    )
    order = models.PositiveIntegerField(
        _('Sıralama'),
        default=0
    )
    is_active = models.BooleanField(
        _('Aktif'),
        default=True
    )
    created_at = models.DateTimeField(
        _('Oluşturulma Tarihi'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('Belge Şablonu')
        verbose_name_plural = _('Belge Şablonları')
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_document_type_display()})"
    
    @property
    def allowed_extensions_list(self):
        return [ext.strip() for ext in self.allowed_extensions.split(',')]


class UploadedDocument(models.Model):
    """
    Yüklenen belge modeli.
    Müşterilerin yüklediği belgeleri saklar.
    """
    
    # İlişkiler
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Müşteri')
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=_('Sipariş')
    )
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_documents',
        verbose_name=_('Belge Şablonu')
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents',
        verbose_name=_('Yükleyen')
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_documents',
        verbose_name=_('İnceleyen')
    )
    
    # Belge bilgileri
    document_type = models.CharField(
        _('Belge Tipi'),
        max_length=20,
        choices=DocumentType.choices
    )
    title = models.CharField(
        _('Başlık'),
        max_length=255
    )
    file = models.FileField(
        _('Dosya'),
        upload_to=document_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'xls', 'xlsx']
            )
        ]
    )
    original_filename = models.CharField(
        _('Orijinal Dosya Adı'),
        max_length=255
    )
    file_size = models.PositiveIntegerField(
        _('Dosya Boyutu (bytes)'),
        default=0
    )
    mime_type = models.CharField(
        _('MIME Tipi'),
        max_length=100,
        blank=True
    )
    
    # Durum
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.UPLOADED
    )
    
    # AI Doğrulama
    ai_validated = models.BooleanField(
        _('AI Doğrulandı'),
        default=False
    )
    ai_validation_score = models.FloatField(
        _('AI Doğrulama Skoru'),
        null=True,
        blank=True
    )
    ai_validation_notes = models.TextField(
        _('AI Doğrulama Notları'),
        blank=True
    )
    
    # Notlar
    notes = models.TextField(
        _('Notlar'),
        blank=True
    )
    rejection_reason = models.TextField(
        _('Red Sebebi'),
        blank=True
    )
    
    # Zaman damgaları
    created_at = models.DateTimeField(
        _('Yüklenme Tarihi'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Güncellenme Tarihi'),
        auto_now=True
    )
    reviewed_at = models.DateTimeField(
        _('İnceleme Tarihi'),
        null=True,
        blank=True
    )
    expires_at = models.DateField(
        _('Son Geçerlilik Tarihi'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Yüklenen Belge')
        verbose_name_plural = _('Yüklenen Belgeler')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'document_type']),
            models.Index(fields=['order', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.customer.company_name}"
    
    @property
    def file_size_display(self):
        """Human readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    @property
    def file_extension(self):
        return os.path.splitext(self.original_filename)[1].lower()
    
    @property
    def is_image(self):
        return self.file_extension in ['.jpg', '.jpeg', '.png', '.gif']
    
    @property
    def is_pdf(self):
        return self.file_extension == '.pdf'
    
    @property
    def status_display_class(self):
        """CSS class for status badge."""
        classes = {
            DocumentStatus.PENDING: 'bg-slate-100 text-slate-700',
            DocumentStatus.UPLOADED: 'bg-blue-100 text-blue-700',
            DocumentStatus.REVIEWING: 'bg-amber-100 text-amber-700',
            DocumentStatus.APPROVED: 'bg-emerald-100 text-emerald-700',
            DocumentStatus.REJECTED: 'bg-red-100 text-red-700',
            DocumentStatus.EXPIRED: 'bg-gray-100 text-gray-700',
        }
        return classes.get(self.status, 'bg-slate-100 text-slate-700')
    
    def approve(self, user, notes=''):
        """Belgeyi onayla."""
        from django.utils import timezone
        self.status = DocumentStatus.APPROVED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()
    
    def reject(self, user, reason):
        """Belgeyi reddet."""
        from django.utils import timezone
        self.status = DocumentStatus.REJECTED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()


class KVKKTemplate(models.Model):
    """
    KVKK şablon modeli.
    Admin tarafından düzenlenebilir varsayılan KVKK metni.
    """
    
    name = models.CharField(
        _('Şablon Adı'),
        max_length=255,
        default='Varsayılan KVKK Metni'
    )
    content = models.TextField(
        _('KVKK Metni'),
        help_text=_('HTML formatında KVKK aydınlatma metni')
    )
    version = models.CharField(
        _('Versiyon'),
        max_length=20,
        default='1.0'
    )
    is_active = models.BooleanField(
        _('Aktif'),
        default=True,
        help_text=_('Yeni müşteriler için kullanılacak şablon')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kvkk_templates_created',
        verbose_name=_('Oluşturan')
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
        verbose_name = _('KVKK Şablonu')
        verbose_name_plural = _('KVKK Şablonları')
        ordering = ['-is_active', '-updated_at']
    
    def __str__(self):
        return f"{self.name} (v{self.version})"
    
    def save(self, *args, **kwargs):
        # Sadece bir aktif şablon olabilir
        if self.is_active:
            KVKKTemplate.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_template(cls):
        """Aktif KVKK şablonunu getir."""
        return cls.objects.filter(is_active=True).first()


class KVKKStatus(models.TextChoices):
    """KVKK belge durumları."""
    DRAFT = 'draft', _('Taslak')
    PENDING_SIGNATURE = 'pending_signature', _('İmza Bekliyor')
    UPLOADED = 'uploaded', _('Yüklendi')
    PENDING_APPROVAL = 'pending_approval', _('Onay Bekliyor')
    REVISION_REQUESTED = 'revision_requested', _('Revize İstendi')
    APPROVED = 'approved', _('Onaylandı')
    REJECTED = 'rejected', _('Reddedildi')


class KVKKDocument(models.Model):
    """
    KVKK onay belgesi modeli.
    Müşteriye özel KVKK metni ve imza/onay süreci.
    """
    
    customer = models.OneToOneField(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='kvkk_document',
        verbose_name=_('Müşteri')
    )
    
    # Müşteriye özel KVKK metni (default'tan kopyalanır, düzenlenebilir)
    kvkk_content = models.TextField(
        _('KVKK Metni'),
        help_text=_('Bu müşteri için özelleştirilmiş KVKK metni'),
        default=''
    )
    template_version = models.CharField(
        _('Şablon Versiyonu'),
        max_length=20,
        blank=True
    )
    
    # Durum
    status = models.CharField(
        _('Durum'),
        max_length=30,
        choices=KVKKStatus.choices,
        default=KVKKStatus.DRAFT
    )
    
    # İmzalı belge yüklemesi
    signed_document = models.FileField(
        _('İmzalı Belge'),
        upload_to='kvkk_documents/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])
        ]
    )
    uploaded_at = models.DateTimeField(
        _('Yüklenme Tarihi'),
        null=True,
        blank=True
    )
    
    # Satışçı tarafı
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kvkk_documents_created',
        verbose_name=_('Oluşturan Satışçı')
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kvkk_documents_reviewed',
        verbose_name=_('İnceleyen')
    )
    reviewed_at = models.DateTimeField(
        _('İnceleme Tarihi'),
        null=True,
        blank=True
    )
    
    # Onay bilgileri
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kvkk_approvals',
        verbose_name=_('Onaylayan')
    )
    approved_at = models.DateTimeField(
        _('Onay Tarihi'),
        null=True,
        blank=True
    )
    
    # Revizyon bilgileri
    revision_count = models.PositiveIntegerField(
        _('Revizyon Sayısı'),
        default=0
    )
    revision_reason = models.TextField(
        _('Revizyon Sebebi'),
        blank=True
    )
    
    # Notlar
    salesperson_notes = models.TextField(
        _('Satışçı Notu'),
        blank=True,
        help_text=_('Müşterinin göreceği not')
    )
    internal_notes = models.TextField(
        _('İç Notlar'),
        blank=True,
        help_text=_('Sadece personelin göreceği notlar')
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
    
    class Meta:
        verbose_name = _('KVKK Belgesi')
        verbose_name_plural = _('KVKK Belgeleri')
    
    def __str__(self):
        return f"KVKK - {self.customer.display_company_name}"
    
    @property
    def status_display_class(self):
        """CSS class for status badge."""
        classes = {
            KVKKStatus.DRAFT: 'bg-slate-100 text-slate-700',
            KVKKStatus.PENDING_SIGNATURE: 'bg-blue-100 text-blue-700',
            KVKKStatus.UPLOADED: 'bg-cyan-100 text-cyan-700',
            KVKKStatus.PENDING_APPROVAL: 'bg-amber-100 text-amber-700',
            KVKKStatus.REVISION_REQUESTED: 'bg-orange-100 text-orange-700',
            KVKKStatus.APPROVED: 'bg-emerald-100 text-emerald-700',
            KVKKStatus.REJECTED: 'bg-red-100 text-red-700',
        }
        return classes.get(self.status, 'bg-slate-100 text-slate-700')
    
    @property
    def can_be_downloaded(self):
        """PDF indirilebilir mi?"""
        return self.status in [
            KVKKStatus.PENDING_SIGNATURE, 
            KVKKStatus.REVISION_REQUESTED,
            KVKKStatus.APPROVED
        ]
    
    @property
    def can_upload(self):
        """İmzalı belge yüklenebilir mi?"""
        return self.status in [
            KVKKStatus.PENDING_SIGNATURE, 
            KVKKStatus.REVISION_REQUESTED
        ]
    
    def send_for_signature(self, user):
        """KVKK'yı imzaya gönder."""
        self.status = KVKKStatus.PENDING_SIGNATURE
        self.created_by = user
        self.save()
    
    def request_revision(self, user, reason):
        """Revizyon iste."""
        from django.utils import timezone
        self.status = KVKKStatus.REVISION_REQUESTED
        self.revision_count += 1
        self.revision_reason = reason
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.signed_document = None  # Eski belgeyi sil
        self.save()
    
    def approve(self, user):
        """KVKK'yı onayla."""
        from django.utils import timezone
        self.status = KVKKStatus.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save()
        
        # Müşterinin KVKK durumunu güncelle
        self.customer.kvkk_approved = True
        self.customer.kvkk_approved_at = timezone.now()
        self.customer.save(update_fields=['kvkk_approved', 'kvkk_approved_at'])


class KVKKComment(models.Model):
    """KVKK belgesi yorumları."""
    
    kvkk_document = models.ForeignKey(
        KVKKDocument,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('KVKK Belgesi')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kvkk_comments',
        verbose_name=_('Yazar')
    )
    content = models.TextField(
        _('Yorum')
    )
    is_internal = models.BooleanField(
        _('İç Yorum'),
        default=False,
        help_text=_('İç yorumlar müşteri tarafından görülmez')
    )
    created_at = models.DateTimeField(
        _('Oluşturulma Tarihi'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('KVKK Yorumu')
        verbose_name_plural = _('KVKK Yorumları')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Yorum - {self.kvkk_document.customer.company_name}"
