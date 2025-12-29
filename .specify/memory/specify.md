# Leasing Yönetim Sistemi - Temel Spesifikasyon

## Sistem Genel Bakış

### Amaç
Leasing şirketlerinin satış, belge yönetimi, müşteri takibi ve teklif süreçlerini AI destekli otomatik hale getiren web tabanlı yönetim sistemi.

### Kapsam
- Çoklu departman desteği (Sales, Finance, Legal, Operations)
- Rol bazlı kullanıcı yönetimi (Admin, Department Users, Customers)
- AI destekli belge validasyonu ve içerik kontrolü
- Akıllı görev önceliklendirme
- Otomatik teklif oluşturma
- Müşteri istihbaratı ve risk analizi
- Dinamik form yönetimi
- Varlık değerleme sistemi

### Temel Kullanıcı Hikayeleri
1. Satış elemanı olarak, müşterilerimin hangi aşamada olduğunu ve bugün neyle ilgilenmem gerektiğini görmek istiyorum
2. Müşteri olarak, istenen belgeleri kolayca yüklemek ve sipariş durumumu takip etmek istiyorum
3. Admin olarak, tüm departmanların performansını ve sistem kullanımını görmek istiyorum
4. Satış elemanı olarak, ses veya metin ile hızlıca teklif oluşturmak istiyorum
5. Sistem olarak, eksik veya hatalı belgeleri otomatik tespit etmek istiyorum

## Fonksiyonel Gereksinimler

### FR-1: Kullanıcı Yönetimi ve Kimlik Doğrulama

#### FR-1.1: Kullanıcı Tipleri
- Admin: Tam sistem erişimi
- Departman Kullanıcısı: Departman bazlı erişim
- Müşteri: Kendi portal erişimi

#### FR-1.2: Kimlik Doğrulama
- Email/şifre ile giriş
- Şifre sıfırlama (email ile)
- Oturum yönetimi (30 dakika timeout)
- Güvenli çıkış

#### FR-1.3: Yetkilendirme
- Rol bazlı erişim kontrolü
- Departman bazlı veri izolasyonu
- Müşteri bazlı veri izolasyonu
- Permission sistemi (Django built-in)

### FR-2: KVKK ve Müşteri Onboarding

#### FR-2.1: Müşteri Kaydı
- Satış elemanı müşteri kaydı oluşturur
- Otomatik satış elemanı ataması
- Müşteriye aktivasyon emaili gönderilir
- Müşteri ID otomatik generate edilir

#### FR-2.2: KVKK Onay Süreci
- İlk giriş: Sadece KVKK belgesi gösterilir
- KVKK belge görüntüleme (PDF)
- Yorum ekleme özelliği (belirli kısımlara)
- Paraf ve imza talimatları
- Paraflı/imzalı belge yükleme
- AI ile paraf/imza kontrolü
- Satış elemanına onay bildirimi

#### FR-2.3: Hesap Aktivasyonu
- Satış elemanı KVKK belgesini inceler
- Onaylama/reddetme seçeneği
- Red durumunda müşteriye bildirim
- Onay sonrası hesap aktif edilir
- Müşteri dashboard erişimi

### FR-3: Sipariş ve Belge Yönetimi

#### FR-3.1: Belge Şablonu Tanımlama
- Belge adı ve açıklama
- Gerekli alanlar (JSON formatında)
- Alan tipleri: metin, sayı, tarih, imza, paraf
- Validasyon kuralları per alan
- Örnek belge yükleme
- Sıralama (order)

#### FR-3.2: Sipariş Oluşturma
- Müşteri "Yeni Sipariş" butonu
- Wizard interface (multi-step)
- Ekipman seçimi/tanımlama
- Gerekli belgelerin listelenmesi
- Belge örnek indirme

#### FR-3.3: Belge Yükleme
- Drag-and-drop file upload
- Desteklenen formatlar: PDF, Word, JPG, PNG
- Maksimum dosya boyutu: 10MB
- Multiple file upload
- Progress indicator

#### FR-3.4: AI Belge Validasyonu
- Otomatik metin çıkarma (OCR if needed)
- Şablona göre alan kontrolü
- İmza/paraf görsel kontrolü
- Real-time feedback
- Validasyon sonucu gösterimi:
  - Yeşil: Geçerli
  - Kırmızı: Hatalı/eksik
  - Sarı: Uyarı
- Hata detayları ve düzeltme önerileri

#### FR-3.5: Sipariş Onay Süreci
- Tüm belgeler valid olunca submit aktif
- Satış elemanı onay kuyruğuna düşer
- Onay/red seçenekleri
- Red durumunda müşteriye düzeltme talebi
- Onay sonrası departman yönlendirmesi

#### FR-3.6: Sipariş Durum Takibi
- Status değişiklikleri:
  - Taslak
  - Belge Bekliyor
  - Satış Onayında
  - Onaylandı
  - Muhasebede
  - Hukukta
  - Tamamlandı
- Timeline görünümü
- Durum değişikliği bildirimleri
- Geçmiş görüntüleme

### FR-4: Görev Yönetimi ve Önceliklendirme

#### FR-4.1: Görev Oluşturma
- Manuel görev oluşturma
- Otomatik görev oluşturma (sipariş bazlı)
- Görev tipleri:
  - Teklif Bekliyor
  - Belge Bekliyor
  - Muhasebede
  - İmzada
  - Takip Gerekli

#### FR-4.2: AI Önceliklendirme
- Tüm açık görevlerin analizi
- Priority score hesaplama (0-100)
- Faktörler:
  - Son etkileşimden geçen süre
  - Sipariş değeri
  - Eksik belge sayısı
  - Deadline yakınlığı
  - Müşteri önemi
- Günlük öncelik listesi oluşturma
- Açıklayıcı reasoning

#### FR-4.3: Görev Görünümleri
- "Bugünün Önemlileri" widget
- Tüm görevler listesi
- Filtreleme: durum, müşteri, tarih
- Sıralama: öncelik, tarih, müşteri
- Arama fonksiyonu

#### FR-4.4: Görev Detay
- Müşteri bilgileri
- Sipariş detayları
- Belge durumu
- İletişim geçmişi
- Quick actions: Ara, Email, Güncelle
- AI önerileri

#### FR-4.5: Bildirimler
- Günlük email özeti
- Yeni görev bildirimi
- Deadline yaklaşıyor uyarısı
- Yüksek öncelikli görev
- In-app bildirimler

### FR-5: Teklif Oluşturma

#### FR-5.1: Teklif Giriş Metodları
- Serbest metin (voice-to-text destekli)
- Yapılandırılmış form
- Şablon seçimi

#### FR-5.2: AI Teklif Üretimi
- Gereksinim analizi
- Ekipman tanımlama
- Vade ve tutar hesaplama
- Teklif yapısı oluşturma:
  - Başlık
  - Müşteri bilgileri
  - Ekipman detayları
  - Finansal koşullar
  - Ödeme planı
  - Şartlar ve koşullar

#### FR-5.3: PDF Oluşturma
- Profesyonel template
- Şirket logosu ve branding
- Tablo ve formatlamalar
- PDF export

#### FR-5.4: Teklif Gönderimi
- Müşteri seçimi
- AI email oluşturma
- Otomatik email gönderimi
- Tracking (açılma/tıklama)
- Gönderim kayıtları

#### FR-5.5: Teklif Yönetimi
- Teklif listesi
- Durum takibi
- Versiyon yönetimi
- Geçmiş görüntüleme

### FR-6: Müşteri İstihbaratı

#### FR-6.1: Araştırma Tetikleyici
- KVKK onayı sonrası otomatik başlama
- Manuel yenileme seçeneği

#### FR-6.2: AI Web Araştırması
- Şirket adı ve vergi no ile arama
- Toplanan bilgiler:
  - Şirket büyüklüğü
  - Çalışan sayısı
  - Faaliyet alanı
  - Finansal sağlık
  - Haberler ve gelişmeler
  - Risk faktörleri
  - Sektör pozisyonu

#### FR-6.3: Risk Değerlendirmesi
- Düşük/Orta/Yüksek risk sınıflandırması
- Risk faktörleri listesi
- Öneriler ve uyarılar

#### FR-6.4: Araştırma Sonuçları
- Müşteri kartında görünüm
- Sadece yetkili kullanıcılara görünür
- Kaynak URL'leri
- Son güncelleme tarihi
- Yenileme butonu

### FR-7: Dinamik Form Sistemi

#### FR-7.1: Form Şablonu Oluşturma
- Form adı ve açıklama
- Section yapısı
- Alan tanımlamaları:
  - Alan tipi (text, number, date, dropdown, file, signature)
  - Zorunlu/opsiyonel
  - Validasyon kuralları
  - Yardım metni
- Görüntüleme sırası

#### FR-7.2: Form Aktivasyonu
- Müşteri için form erişim kontrolü
- Koşullu aktivasyon (KVKK+belgeler)

#### FR-7.3: Form Doldurma
- Step-by-step interface
- Real-time validasyon
- AI içerik kontrolü
- İlerleme göstergesi
- Taslak kaydetme

#### FR-7.4: Form Gönderimi
- Tüm alanlar geçerli olunca submit
- PDF oluşturma
- Email gönderimi (müşteri + satış)
- Sipariş/müşteri kaydına ekleme

### FR-8: Varlık Yönetimi

#### FR-8.1: Varlık Veritabanı
- Varlık adı, kategori
- Marka, model
- Güncel piyasa fiyatı
- Son güncelleme tarihi

#### FR-8.2: AI Piyasa Araştırması
- Varlık bazlı fiyat araştırması
- Web'den fiyat toplama
- Trend analizi (artıyor/azalıyor)
- İkinci el değer tahmini
- Leasing uygunluk değerlendirmesi

#### FR-8.3: Anlaşma Analizi
- Talep edilen fiyat vs piyasa
- Müşteri risk durumu
- Vade uygunluğu
- Öneri ve uyarılar
- Onay recommendation

#### FR-8.4: Varlık Görünümü
- Sipariş detayında varlık bilgisi
- Piyasa analizi kartı
- AI önerileri
- Tarihsel veri

### FR-9: Dashboard ve Raporlama

#### FR-9.1: Admin Dashboard
- Tüm departman istatistikleri
- Aktif sipariş sayıları
- Bekleyen onaylar
- Kullanıcı aktiviteleri
- Grafik ve tablolar
- Sistem sağlık metrikleri

#### FR-9.2: Satış Dashboard
- Bugünün önemlileri widget
- Müşteri listesi
- Görev özeti
- Hızlı aksiyonlar
- İstatistikler:
  - Aylık sipariş sayısı
  - Conversion rate
  - Ortalama işlem süresi

#### FR-9.3: Müşteri Portalı
- Hoş geldin mesajı
- Aktif siparişler
- Yeni sipariş butonu
- Doldurulacak formlar
- Geçmiş siparişler
- İletişim merkezi

#### FR-9.4: Raporlar
- Satış performans raporu
- Belge uyumluluk raporu
- Görev tamamlama raporu
- Müşteri aktivite raporu
- Excel/PDF export

### FR-10: İletişim ve Bildirimler

#### FR-10.1: Email Bildirimleri
- Müşteri kaydı
- KVKK onayı
- Sipariş durumu değişikliği
- Görev atamaları
- Günlük özet
- Teklif gönderimi

#### FR-10.2: In-App Bildirimler
- Bell icon ile bildirim merkezi
- Okunmamış sayacı
- Bildirim tipleri:
  - Belge yüklendi
  - Onay gerekli
  - Deadline yaklaşıyor
  - Mesaj alındı

#### FR-10.3: İletişim Geçmişi
- Sipariş bazlı timeline
- Email logları
- Durum değişiklik notları
- Kullanıcı yorumları

## Fonksiyonel Olmayan Gereksinimler

### NFR-1: Performans
- Sayfa yükleme süresi: <2 saniye
- AI yanıt süresi: <5 saniye
- Dosya yükleme: Progress indicator
- Eş zamanlı kullanıcı: 100+
- Database query optimization

### NFR-2: Güvenlik
- HTTPS zorunlu
- Password hashing (Django default)
- CSRF protection
- XSS prevention
- SQL injection protection
- File upload validation
- Rate limiting
- Session management

### NFR-3: Kullanılabilirlik
- Türkçe arayüz
- Responsive design (mobil uyumlu)
- Sezgisel navigasyon
- Tutarlı UI/UX
- Accessibility standartları
- Yardım metinleri

### NFR-4: Güvenilirlik
- %99.5 uptime hedefi
- Graceful error handling
- Automatic retry mekanizması
- Data backup (daily)
- Disaster recovery planı

### NFR-5: Bakım ve Destek
- Kapsamlı logging
- Error tracking (Sentry optional)
- Database migration yönetimi
- Environment-based configuration
- Documentation

### NFR-6: Uyumluluk
- KVKK compliance
- Data retention policies
- Audit trail
- User consent management
- Right to be forgotten

## Veri Modeli (High-Level)

### Core Models
- CustomUser (extends AbstractUser)
- Department
- Customer (extends CustomUser)

### Document Management
- DocumentTemplate
- UploadedDocument
- KVKKDocument
- KVKKComment

### Order Management
- Order
- OrderStatus (choices)
- OrderNote

### Task Management
- Task
- TaskPriority

### Proposal System
- Proposal
- ProposalSection

### Form System
- FormTemplate
- FormField
- FilledForm

### Asset Management
- Asset
- AssetValuation

### Communication
- EmailLog
- Notification

## İş Akışları

### Workflow 1: Müşteri Onboarding
1. Satış elemanı müşteri kaydı oluşturur
2. Sistem email gönderir
3. Müşteri giriş yapar → KVKK sayfası
4. Müşteri KVKK'yı imzalar ve yükler
5. AI paraf/imza kontrolü yapar
6. Satış elemanına bildirim gider
7. Satış elemanı onaylar
8. Hesap aktif olur
9. Müşteri dashboard'a erişir

### Workflow 2: Sipariş Süreci
1. Müşteri "Yeni Sipariş" oluşturur
2. Ekipman bilgisini girer
3. İstenilen belgeler listelenir
4. Müşteri belgeleri yükler
5. AI her belgeyi validate eder
6. Real-time feedback gösterilir
7. Tüm belgeler valid olunca submit
8. Satış elemanı onay kuyruğunda görür
9. Satış elemanı inceler ve onaylar
10. Sipariş Finance departmanına gider

### Workflow 3: Günlük Görev Yönetimi
1. Satış elemanı sabah giriş yapar
2. Dashboard "Bugünün Önemlileri" gösterir
3. AI 5 öncelikli görev listelemiş
4. Satış elemanı görevlere tıklar
5. Detayları görür, aksiyon alır
6. Görev durumunu günceller
7. AI yeniden önceliklendirme yapar

### Workflow 4: Teklif Oluşturma
1. Satış elemanı "Yeni Teklif" der
2. "36 ay 15 ton forklift leasing" yazar
3. AI teklif yapısını oluşturur
4. Satış elemanı gözden geçirir/düzenler
5. PDF generate edilir
6. Müşteri seçilir
7. AI email oluşturur
8. Teklif otomatik gönderilir

## AI Entegrasyon Detayları

### AI Service Architecture
- Merkezi ClaudeService sınıfı
- Specialized metodlar her use case için
- Error handling ve retry logic
- Response caching
- API key güvenliği

### AI Use Cases
1. **Belge Validasyonu**: Metin analizi, alan tespiti, imza kontrolü
2. **Görev Önceliklendirme**: Multi-factor scoring, reasoning
3. **Müşteri Araştırması**: Web search, risk analizi
4. **Teklif Oluşturma**: NLP parsing, content generation
5. **Form Validasyonu**: İçerik kalite kontrolü
6. **Varlık Analizi**: Piyasa araştırması, fiyat analizi
7. **Anlaşma Değerlendirmesi**: Risk assessment, öneri

### AI Response Format
Tüm AI servisleri JSON döndürmeli:
```json
{
  "success": true,
  "data": {...},
  "confidence": 0.95,
  "reasoning": "...",
  "warnings": [],
  "timestamp": "..."
}
```

## Test Gereksinimleri

### Unit Tests
- Model validasyonları
- Business logic functions
- AI service metodları
- Utility functions

### Integration Tests
- KVKK onay akışı
- Sipariş oluşturma akışı
- Teklif gönderme akışı
- Form doldurma akışı

### E2E Tests
- Kullanıcı rolleri ve erişim
- Komple müşteri onboarding
- Satış elemanı günlük akışı
- Admin dashboard

### Performance Tests
- Load testing (100 concurrent users)
- Database query profiling
- AI service response times
- File upload performance

## Deployment Gereksinimleri

### Development Environment
- Python 3.11+
- Django 5.x
- SQLite
- Local file storage

### Production Recommendations
- PostgreSQL
- Cloud storage (AWS S3 / Azure Blob)
- Redis for caching
- Celery for background tasks (optional)
- Gunicorn + Nginx
- SSL certificate

### Environment Variables
```
DJANGO_SECRET_KEY
ANTHROPIC_API_KEY
DATABASE_URL
EMAIL_HOST
EMAIL_PORT
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
ALLOWED_HOSTS
DEBUG
```

## Bağımlılıklar

### Python Packages
- django>=5.0
- anthropic
- PyPDF2
- Pillow
- python-docx
- django-crispy-forms
- python-dotenv
- requests

### Optional Packages
- celery (background tasks)
- redis (caching)
- sentry-sdk (error tracking)
- django-debug-toolbar (development)

## Kısıtlamalar ve Varsayımlar

### Kısıtlamalar
- SQLite (initial phase)
- Tek şirket kullanımı
- Türkçe dil desteği
- Max 10MB dosya boyutu
- Web only (no mobile app)

### Varsayımlar
- Kullanıcılar internet erişimi var
- Modern browser kullanımı
- Anthropic API availability
- Email server erişimi
- Kullanıcılar temel bilgisayar kullanımını biliyor

## Dışarıda Kalan Özellikler (Out of Scope - Phase 1)

- Multi-tenant architecture
- Mobile application
- Real-time chat
- Advanced reporting/BI
- Integration with external systems
- Internationalization (i18n)
- Advanced workflow engine
- Document e-signature integration
- Payment gateway integration
- Advanced role/permission customization