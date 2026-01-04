from django.db import models
from django.conf import settings
import os
from datetime import datetime


class UsageType(models.Model):
    """İş Kolları - Sistemdeki farklı işlem türlerinin tanımları"""
    
    name = models.CharField('İş Kolu Adı', max_length=100, unique=True,
                           help_text='Örn: AD Log Analizi, Email Şablonları, Yedekleme')
    code = models.CharField('Kod', max_length=50, unique=True,
                           help_text='Programatik erişim için kod (örn: AD_LOG)')
    description = models.TextField('Açıklama', blank=True,
                                  help_text='Bu iş kolunun detaylı açıklaması')
    is_active = models.BooleanField('Aktif', default=True)
    created_at = models.DateTimeField('Oluşturma Tarihi', auto_now_add=True)
    updated_at = models.DateTimeField('Güncellenme Tarihi', auto_now=True)
    
    class Meta:
        verbose_name = 'İş Kolu'
        verbose_name_plural = 'İş Kolları'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class PathDefinition(models.Model):
    """Genel path tanımları - farklı işlemler için kullanılabilir"""
    
    name = models.CharField('Tanım Adı', max_length=255, 
                           help_text='Bu path için açıklayıcı bir isim')
    usage_type = models.ForeignKey(UsageType, on_delete=models.PROTECT, 
                                   verbose_name='Kullanım Türü (İş Kolu)',
                                   related_name='path_definitions',
                                   help_text='Bu path hangi işlem için kullanılacak')
    source_path = models.CharField('Kaynak Path (Fileserver)', max_length=500, 
                                   help_text='Dosyaların okunacağı kaynak yol')
    output_path = models.CharField('Çıktı Path', max_length=500, 
                                   help_text='Sonuç dosyalarının kaydedileceği hedef klasör')
    is_active = models.BooleanField('Aktif', default=True)
    is_default = models.BooleanField('Varsayılan', default=False,
                                     help_text='Bu tip için varsayılan path')
    
    created_at = models.DateTimeField('Oluşturulma Tarihi', auto_now_add=True)
    updated_at = models.DateTimeField('Güncellenme Tarihi', auto_now=True)
    
    class Meta:
        verbose_name = 'Path Tanımı'
        verbose_name_plural = 'Path Tanımları'
        ordering = ['usage_type', '-is_default', 'name']
        unique_together = [['usage_type', 'name']]
    
    def __str__(self):
        return f"{self.name} ({self.usage_type.name}) {'[Varsayılan]' if self.is_default else ''}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Aynı usage_type için diğer varsayılanları kaldır
            PathDefinition.objects.filter(
                usage_type=self.usage_type, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# Geriye uyumluluk için alias
ADLogSourcePath = PathDefinition


class ADLogAnalysis(models.Model):
    """AD Log analiz kaydı"""
    
    STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('downloading', 'Dosyalar İndiriliyor'),
        ('processing', 'İşleniyor'),
        ('comparing', 'Karşılaştırılıyor'),
        ('completed', 'Tamamlandı'),
        ('email_pending', 'Email Onayı Bekliyor'),
        ('email_sent', 'Email Gönderildi'),
        ('failed', 'Hatalı'),
    ]
    
    MONTH_CHOICES = [
        (1, 'Ocak'), (2, 'Şubat'), (3, 'Mart'), (4, 'Nisan'),
        (5, 'Mayıs'), (6, 'Haziran'), (7, 'Temmuz'), (8, 'Ağustos'),
        (9, 'Eylül'), (10, 'Ekim'), (11, 'Kasım'), (12, 'Aralık'),
    ]
    
    name = models.CharField('Analiz Adı', max_length=255)
    description = models.TextField('Açıklama', blank=True, null=True)
    
    # Path tanımı referansı
    source_path_config = models.ForeignKey(ADLogSourcePath, on_delete=models.SET_NULL, 
                                           null=True, blank=True,
                                           related_name='analyses',
                                           verbose_name='Kaynak Path Tanımı')
    
    # Yıl ve Ay seçimi
    year = models.IntegerField('Yıl', default=datetime.now().year)
    month = models.IntegerField('Ay', choices=MONTH_CHOICES, 
                                default=datetime.now().month - 1 if datetime.now().month > 1 else 12)
    
    # Eski alan (geriye uyumluluk)
    source_path = models.CharField('Kaynak Dosya Yolu', max_length=500, blank=True, null=True,
                                   help_text='Excel dosyalarının okunacağı klasör yolu')
    
    # Sonuç dosyaları
    user_checklist_file = models.FileField('Kullanıcı Kontrol Listesi', 
                                           upload_to='ad_logs/checklists/', 
                                           blank=True, null=True)
    unique_gids_file = models.FileField('Unique GID Listesi', 
                                        upload_to='ad_logs/gids/', 
                                        blank=True, null=True)
    log_file = models.FileField('Farklılık Log Dosyası', 
                                upload_to='ad_logs/logs/', 
                                blank=True, null=True)
    
    # İşlenen dosya sayısı
    processed_files_count = models.IntegerField('İşlenen Dosya Sayısı', default=0)
    total_gids_found = models.IntegerField('Bulunan Toplam GID', default=0)
    unique_gids_count = models.IntegerField('Unique GID Sayısı', default=0)
    discrepancy_count = models.IntegerField('Farklılık Sayısı', default=0)
    
    status = models.CharField('Durum', max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField('Hata Mesajı', blank=True, null=True)
    
    # Email bilgileri
    email_to = models.TextField('Email Alıcıları (TO)', blank=True, null=True,
                                help_text='Virgülle ayrılmış email adresleri')
    email_cc = models.TextField('Email CC', blank=True, null=True,
                                help_text='Virgülle ayrılmış email adresleri')
    email_subject = models.CharField('Email Konusu', max_length=255, blank=True, null=True)
    email_body = models.TextField('Email İçeriği', blank=True, null=True)
    email_sent_at = models.DateTimeField('Email Gönderim Zamanı', blank=True, null=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                   null=True, related_name='ad_analyses',
                                   verbose_name='Oluşturan')
    created_at = models.DateTimeField('Oluşturulma Tarihi', auto_now_add=True)
    updated_at = models.DateTimeField('Güncellenme Tarihi', auto_now=True)
    
    class Meta:
        verbose_name = 'AD Log Analizi'
        verbose_name_plural = 'AD Log Analizleri'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    @property
    def month_name(self):
        """Ay adını döndür"""
        return dict(self.MONTH_CHOICES).get(self.month, '')
    
    @property
    def period_display(self):
        """Dönem gösterimi: Ocak 2025"""
        return f"{self.month_name} {self.year}"
    
    def get_output_folder(self):
        """Çıktı klasörünü döndür - ay-ismi_yıl formatında"""
        if self.source_path_config:
            base_path = self.source_path_config.output_path
        else:
            base_path = os.path.join(settings.MEDIA_ROOT, 'ad_logs', 'outputs')
        
        # Ay ismini küçük harfe çevir ve Türkçe karakterleri düzelt
        month_name_lower = self.month_name.lower()
        month_name_lower = month_name_lower.replace('ş', 's').replace('ç', 'c').replace('ı', 'i').replace('ü', 'u').replace('ö', 'o').replace('ğ', 'g')
        
        # ay-ismi_yıl formatı: kasim_2025
        folder_name = f"{month_name_lower}_{self.year}"
        return os.path.join(base_path, folder_name)


class ProcessedADFile(models.Model):
    """İşlenmiş AD Excel dosyası"""
    
    analysis = models.ForeignKey(ADLogAnalysis, on_delete=models.CASCADE, 
                                  related_name='processed_files',
                                  verbose_name='Analiz')
    original_filename = models.CharField('Orijinal Dosya Adı', max_length=255)
    file = models.FileField('Dosya', upload_to='ad_logs/processed/')
    
    gids_count = models.IntegerField('GID Sayısı', default=0)
    processed_at = models.DateTimeField('İşlenme Zamanı', auto_now_add=True)
    
    class Meta:
        verbose_name = 'İşlenmiş AD Dosyası'
        verbose_name_plural = 'İşlenmiş AD Dosyaları'
        ordering = ['-processed_at']
    
    def __str__(self):
        return f"{self.original_filename} - {self.analysis.name}"


class SystemGID(models.Model):
    """Sistem içindeki GID kayıtları"""
    
    gid = models.CharField('GID', max_length=100, unique=True)
    display_name = models.CharField('Görünen Ad', max_length=255, blank=True, null=True)
    email = models.EmailField('Email', blank=True, null=True)
    department = models.CharField('Departman', max_length=255, blank=True, null=True)
    is_active = models.BooleanField('Aktif', default=True)
    
    created_at = models.DateTimeField('Oluşturulma Tarihi', auto_now_add=True)
    updated_at = models.DateTimeField('Güncellenme Tarihi', auto_now=True)
    
    class Meta:
        verbose_name = 'Sistem GID'
        verbose_name_plural = 'Sistem GID\'leri'
        ordering = ['gid']
    
    def __str__(self):
        return f"{self.gid} - {self.display_name or 'N/A'}"


class GIDDiscrepancy(models.Model):
    """GID farklılık kaydı"""
    
    TYPE_CHOICES = [
        ('missing_in_system', 'Sistemde Yok'),
        ('missing_in_ad', 'AD\'de Yok'),
        ('data_mismatch', 'Veri Uyuşmazlığı'),
    ]
    
    analysis = models.ForeignKey(ADLogAnalysis, on_delete=models.CASCADE, 
                                  related_name='discrepancies',
                                  verbose_name='Analiz')
    gid = models.CharField('GID', max_length=100)
    discrepancy_type = models.CharField('Farklılık Tipi', max_length=30, choices=TYPE_CHOICES)
    details = models.TextField('Detaylar', blank=True, null=True)
    
    source_file = models.CharField('Kaynak Dosya', max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField('Oluşturulma Tarihi', auto_now_add=True)
    
    class Meta:
        verbose_name = 'GID Farklılığı'
        verbose_name_plural = 'GID Farklılıkları'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.gid} - {self.get_discrepancy_type_display()}"


class ADLogEmailTemplate(models.Model):
    """Email şablonları - farklı işlemler için kullanılabilir"""
    
    name = models.CharField('Şablon Adı', max_length=255)
    usage_type = models.ForeignKey(UsageType, on_delete=models.PROTECT,
                                   verbose_name='Kullanım Türü (İş Kolu)',
                                   related_name='email_templates',
                                   help_text='Bu şablon hangi işlem için kullanılacak')
    subject = models.CharField('Konu', max_length=255, 
                               help_text='Kullanılabilir: {{analysis_name}}, {{period}}, {{date}}')
    body = models.TextField('İçerik', 
                           help_text='Kullanılabilir: {{analysis_name}}, {{period}}, {{date}}, {{total_gids}}, {{unique_gids}}, {{discrepancy_count}}, {{unmatched_gids}}')
    
    default_to = models.TextField('Varsayılan Alıcılar (TO)', blank=True, null=True,
                                  help_text='Virgülle ayrılmış email adresleri')
    default_cc = models.TextField('Varsayılan CC', blank=True, null=True,
                                  help_text='Virgülle ayrılmış email adresleri')
    
    is_active = models.BooleanField('Aktif', default=True)
    is_default = models.BooleanField('Varsayılan Şablon', default=False,
                                     help_text='Bu tip için varsayılan şablon')
    
    created_at = models.DateTimeField('Oluşturulma Tarihi', auto_now_add=True)
    updated_at = models.DateTimeField('Güncellenme Tarihi', auto_now=True)
    
    class Meta:
        verbose_name = 'Email Şablonu'
        verbose_name_plural = 'Email Şablonları'
        ordering = ['usage_type', '-is_default', 'name']
        unique_together = [['usage_type', 'name']]
    
    def __str__(self):
        return f"{self.name} ({self.get_usage_type_display()}) {'[Varsayılan]' if self.is_default else ''}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Aynı usage_type için diğer varsayılanları kaldır
            ADLogEmailTemplate.objects.filter(
                usage_type=self.usage_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    def render(self, context):
        """Template'i context ile render et"""
        from django.template import Template, Context
        subject_template = Template(self.subject)
        body_template = Template(self.body)
        
        django_context = Context(context)
        
        return {
            'subject': subject_template.render(django_context),
            'body': body_template.render(django_context),
            'to': self.default_to or '',
            'cc': self.default_cc or ''
        }


class BulkUserImport(models.Model):
    """Toplu kullanıcı import kaydı"""
    
    STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('processing', 'İşleniyor'),
        ('completed', 'Tamamlandı'),
        ('completed_with_errors', 'Hatalarla Tamamlandı'),
        ('failed', 'Başarısız'),
    ]
    
    name = models.CharField('Import Adı', max_length=255)
    excel_file = models.FileField('Excel Dosyası', upload_to='bulk_imports/users/')
    status = models.CharField('Durum', max_length=30, choices=STATUS_CHOICES, default='pending')
    
    # İstatistikler
    total_rows = models.IntegerField('Toplam Satır', default=0)
    created_count = models.IntegerField('Oluşturulan', default=0)
    updated_count = models.IntegerField('Güncellenen', default=0)
    skipped_count = models.IntegerField('Atlanan', default=0)
    error_count = models.IntegerField('Hatalı', default=0)
    
    # Log
    log = models.TextField('İşlem Logu', blank=True, null=True)
    error_details = models.TextField('Hata Detayları', blank=True, null=True)
    
    # İşlem yapan kullanıcı
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bulk_user_imports',
        verbose_name='Oluşturan'
    )
    
    created_at = models.DateTimeField('Oluşturulma Tarihi', auto_now_add=True)
    completed_at = models.DateTimeField('Tamamlanma Tarihi', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Toplu Kullanıcı Import'
        verbose_name_plural = 'Toplu Kullanıcı Import\'ları'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
