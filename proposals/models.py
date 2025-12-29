"""
Proposals app models.
AI-powered proposal generation and management.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


class ProposalStatus(models.TextChoices):
    """Teklif durumları."""
    DRAFT = 'draft', _('Taslak')
    PENDING_APPROVAL = 'pending_approval', _('Onay Bekliyor')
    GENERATING = 'generating', _('Oluşturuluyor')
    READY = 'ready', _('Hazır')
    SENT = 'sent', _('Gönderildi')
    VIEWED = 'viewed', _('Görüntülendi')
    ACCEPTED = 'accepted', _('Kabul Edildi')
    REJECTED = 'rejected', _('Reddedildi')
    EXPIRED = 'expired', _('Süresi Doldu')


class ProposalTemplate(models.Model):
    """
    Teklif şablonu modeli.
    Admin tarafından yönetilen ve AI tarafından doldurulan teklif şablonu.
    """
    
    name = models.CharField(
        _('Şablon Adı'),
        max_length=200,
        default='Varsayılan Teklif Şablonu'
    )
    
    description = models.TextField(
        _('Şablon Açıklaması'),
        blank=True,
        help_text=_('Bu şablonun ne amaçla kullanılacağına dair açıklama')
    )
    
    # Email subject template
    email_subject = models.CharField(
        _('Email Konusu'),
        max_length=300,
        default='Leasing Teklifi - {company_name}',
        help_text=_('Kullanılabilir değişkenler: {company_name}, {contact_person}, {equipment_type}')
    )
    
    # Email body template
    email_body = models.TextField(
        _('Email İçeriği'),
        default='''Sayın {contact_person},

{company_name} için hazırladığımız leasing teklifini ekte bulabilirsiniz.

Teklif Özeti:
- Ekipman: {equipment_description}
- Kiralama Süresi: {lease_term_months} ay
- Aylık Ödeme: {monthly_payment} {currency}
- Toplam Tutar: {total_amount} {currency}

Teklifimizin geçerlilik süresi {valid_days} gündür.

Sorularınız için bizimle iletişime geçebilirsiniz.

Saygılarımızla,
{salesperson_name}
{salesperson_email}
{salesperson_phone}''',
        help_text=_('Kullanılabilir değişkenler: {company_name}, {contact_person}, {equipment_description}, {lease_term_months}, {monthly_payment}, {total_amount}, {currency}, {valid_days}, {salesperson_name}, {salesperson_email}, {salesperson_phone}')
    )
    
    # AI Input Guide - Kullanıcıya ne yazması gerektiğini gösteren örnek
    input_guide = models.TextField(
        _('Giriş Rehberi'),
        default='''Teklif oluşturmak için aşağıdaki bilgileri içeren bir açıklama yazın:

• Ekipman türü ve markası (örn: Caterpillar ekskavatör, Komatsu dozer)
• Ekipman adedi
• Tahmini ekipman değeri
• İstenen kiralama süresi (ay)
• Peşinat tercihi varsa
• Özel istekler veya notlar

Örnek:
"ABC İnşaat için 2 adet Caterpillar 320 ekskavatör ve 1 adet Komatsu D65 dozer teklifi hazırla. Toplam değer yaklaşık 5 milyon TL, 36 ay vade istiyorlar. %10 peşinat ödeyebilirler, aylık taksitleri mümkün olduğunca düşük tutmak istiyorlar. Firma inşaat sektöründe 10 yıldır faaliyet gösteriyor."''',
        help_text=_('Kullanıcıya teklif oluşturmak için ne yazması gerektiğini gösteren örnek metin')
    )
    
    # Settings
    default_valid_days = models.PositiveIntegerField(
        _('Varsayılan Geçerlilik Süresi (Gün)'),
        default=30
    )
    
    is_active = models.BooleanField(
        _('Aktif'),
        default=True
    )
    
    created_at = models.DateTimeField(_('Oluşturulma Tarihi'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Güncellenme Tarihi'), auto_now=True)
    
    class Meta:
        verbose_name = _('Teklif Şablonu')
        verbose_name_plural = _('Teklif Şablonları')
        ordering = ['-is_active', '-updated_at']
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_active_template(cls):
        """Aktif şablonu getir."""
        return cls.objects.filter(is_active=True).first()
    
    def get_sections_for_ai(self):
        """AI'ın doldurması gereken section'ları getir."""
        return self.sections.filter(is_ai_generated=True).order_by('order')


class TemplateSectionField(models.Model):
    """
    Şablon bölüm alanı.
    Admin tarafından tanımlanan ve AI tarafından doldurulan bölümler.
    """
    
    class FieldType(models.TextChoices):
        INTRODUCTION = 'introduction', _('Giriş')
        EQUIPMENT_DETAILS = 'equipment_details', _('Ekipman Detayları')
        PRICING = 'pricing', _('Fiyatlandırma')
        TERMS = 'terms', _('Şartlar ve Koşullar')
        BENEFITS = 'benefits', _('Avantajlar')
        TIMELINE = 'timeline', _('Zaman Çizelgesi')
        CONCLUSION = 'conclusion', _('Sonuç')
        CUSTOM = 'custom', _('Özel Bölüm')
    
    template = models.ForeignKey(
        ProposalTemplate,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name=_('Şablon')
    )
    
    field_type = models.CharField(
        _('Alan Tipi'),
        max_length=30,
        choices=FieldType.choices,
        default=FieldType.CUSTOM
    )
    
    title = models.CharField(
        _('Başlık'),
        max_length=200,
        help_text=_('Bu bölümün başlığı (örn: "Giriş", "Ekipman Detayları")')
    )
    
    description = models.TextField(
        _('Alan Açıklaması'),
        help_text=_('AI\'a bu alanı nasıl doldurması gerektiğini anlatan talimat'),
        default='Bu bölümü profesyonel ve ikna edici bir dille doldurun.'
    )
    
    placeholder_content = models.TextField(
        _('Örnek İçerik'),
        blank=True,
        help_text=_('Bu alanda ne tür içerik olacağına dair örnek')
    )
    
    is_ai_generated = models.BooleanField(
        _('AI Tarafından Oluşturulacak'),
        default=True,
        help_text=_('Bu alan AI tarafından mı doldurulacak yoksa sabit mi kalacak')
    )
    
    static_content = models.TextField(
        _('Sabit İçerik'),
        blank=True,
        help_text=_('AI oluşturmayacaksa kullanılacak sabit içerik')
    )
    
    order = models.PositiveIntegerField(
        _('Sıra'),
        default=0
    )
    
    is_required = models.BooleanField(
        _('Zorunlu'),
        default=True,
        help_text=_('Bu bölüm teklifte mutlaka bulunmalı mı')
    )
    
    include_in_pdf = models.BooleanField(
        _('PDF\'e Dahil Et'),
        default=True
    )
    
    include_in_email = models.BooleanField(
        _('Email\'e Dahil Et'),
        default=False
    )
    
    class Meta:
        verbose_name = _('Şablon Bölümü')
        verbose_name_plural = _('Şablon Bölümleri')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.template.name} - {self.title}"


class Proposal(models.Model):
    """
    Teklif modeli.
    AI ile oluşturulan teklifler.
    """
    
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='proposals',
        verbose_name=_('Müşteri')
    )
    salesperson = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_proposals',
        verbose_name=_('Satış Temsilcisi'),
        limit_choices_to={'user_type': 'salesperson'}
    )
    
    # Proposal Details
    title = models.CharField(
        _('Başlık'),
        max_length=300
    )
    description = models.TextField(
        _('Açıklama'),
        blank=True,
        help_text=_('Teklif için genel açıklama')
    )
    
    # Original Input
    original_text = models.TextField(
        _('Orijinal Metin'),
        help_text=_('Kullanıcının girdiği orijinal teklif açıklaması')
    )
    
    # Generated Content
    generated_content = models.TextField(
        _('Oluşturulan İçerik'),
        blank=True,
        help_text=_('AI tarafından oluşturulan teklif içeriği')
    )
    
    # Equipment Details (extracted by AI)
    equipment_details = models.JSONField(
        _('Ekipman Detayları'),
        default=list,
        blank=True,
        help_text=_('AI tarafından çıkarılan ekipman bilgileri')
    )
    
    # Financial Details
    equipment_value = models.DecimalField(
        _('Ekipman Değeri'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    monthly_payment = models.DecimalField(
        _('Aylık Ödeme'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    lease_term_months = models.PositiveIntegerField(
        _('Kiralama Süresi (Ay)'),
        default=36
    )
    down_payment = models.DecimalField(
        _('Peşinat'),
        max_digits=15,
        decimal_places=2,
        default=0
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
    
    # Email content (customized from template)
    email_subject = models.CharField(
        _('Email Konusu'),
        max_length=300,
        blank=True
    )
    email_body = models.TextField(
        _('Email İçeriği'),
        blank=True
    )
    pdf_content = models.TextField(
        _('PDF İçeriği'),
        blank=True,
        help_text=_('Özelleştirilmiş PDF içeriği')
    )
    
    # Status
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=ProposalStatus.choices,
        default=ProposalStatus.DRAFT
    )
    
    # PDF
    pdf_file = models.FileField(
        _('PDF Dosyası'),
        upload_to='proposals/pdfs/',
        blank=True,
        null=True
    )
    
    # Tracking
    sent_at = models.DateTimeField(
        _('Gönderilme Tarihi'),
        null=True,
        blank=True
    )
    viewed_at = models.DateTimeField(
        _('Görüntülenme Tarihi'),
        null=True,
        blank=True
    )
    responded_at = models.DateTimeField(
        _('Yanıt Tarihi'),
        null=True,
        blank=True
    )
    rejection_reason = models.TextField(
        _('Red Sebebi'),
        blank=True,
        help_text=_('Müşterinin red sebebi')
    )
    
    # Validity
    valid_until = models.DateField(
        _('Geçerlilik Tarihi'),
        null=True,
        blank=True
    )
    
    # AI Metadata
    ai_model_used = models.CharField(
        _('Kullanılan AI Modeli'),
        max_length=100,
        blank=True
    )
    generation_time = models.FloatField(
        _('Oluşturma Süresi (sn)'),
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('Oluşturulma Tarihi'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Güncellenme Tarihi'), auto_now=True)
    
    class Meta:
        verbose_name = _('Teklif')
        verbose_name_plural = _('Teklifler')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.customer}"
    
    def get_absolute_url(self):
        return reverse('proposals:detail', kwargs={'pk': self.pk})


class ProposalSection(models.Model):
    """
    Teklif bölümü modeli.
    Teklifin farklı bölümlerini saklar.
    """
    
    class SectionType(models.TextChoices):
        INTRODUCTION = 'introduction', _('Giriş')
        EQUIPMENT = 'equipment', _('Ekipman Detayları')
        PRICING = 'pricing', _('Fiyatlandırma')
        TERMS = 'terms', _('Şartlar ve Koşullar')
        TIMELINE = 'timeline', _('Zaman Çizelgesi')
        BENEFITS = 'benefits', _('Avantajlar')
        CONCLUSION = 'conclusion', _('Sonuç')
        CUSTOM = 'custom', _('Özel Bölüm')
    
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name=_('Teklif')
    )
    section_type = models.CharField(
        _('Bölüm Tipi'),
        max_length=20,
        choices=SectionType.choices
    )
    title = models.CharField(
        _('Bölüm Başlığı'),
        max_length=200
    )
    content = models.TextField(
        _('İçerik')
    )
    order = models.PositiveIntegerField(
        _('Sıra'),
        default=0
    )
    is_editable = models.BooleanField(
        _('Düzenlenebilir'),
        default=True
    )
    
    class Meta:
        verbose_name = _('Teklif Bölümü')
        verbose_name_plural = _('Teklif Bölümleri')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.proposal.title} - {self.title}"


class ProposalEmail(models.Model):
    """
    Teklif email kaydı.
    Gönderilen emailleri takip eder.
    """
    
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='emails',
        verbose_name=_('Teklif')
    )
    recipient_email = models.EmailField(
        _('Alıcı Email')
    )
    subject = models.CharField(
        _('Konu'),
        max_length=300
    )
    body = models.TextField(
        _('İçerik')
    )
    ai_generated = models.BooleanField(
        _('AI Tarafından Oluşturuldu'),
        default=False
    )
    sent_at = models.DateTimeField(
        _('Gönderilme Tarihi'),
        auto_now_add=True
    )
    opened_at = models.DateTimeField(
        _('Açılma Tarihi'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Teklif Emaili')
        verbose_name_plural = _('Teklif Emailleri')
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.proposal.title} - {self.recipient_email}"
