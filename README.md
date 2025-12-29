# Leasing Yönetim Sistemi

Modern, AI destekli leasing şirketi yönetim sistemi. Django 5.x ile geliştirilmiştir.

## 🚀 Özellikler

### Satış Elemanı Modülü
- **Müşteri Yönetimi**: Müşteri ekleme, düzenleme, takip
- **Görev Yönetimi**: AI destekli görev önceliklendirme
- **Teklif Oluşturma**: AI ile profesyonel teklif oluşturma
- **Dashboard**: Günlük öncelikler ve performans metrikleri

### Müşteri Portalı
- **Sipariş Takibi**: Sipariş durumu görüntüleme
- **Belge Yükleme**: KVKK uyumlu güvenli belge yükleme
- **Bildirimler**: Sipariş güncellemeleri için bildirimler

### Admin Dashboard
- **Departman İstatistikleri**: Performans metrikleri
- **Kullanıcı Yönetimi**: Rol bazlı erişim kontrolü
- **Sistem Sağlığı**: AI servisi ve sistem durumu

### AI Özellikleri
- **Görev Önceliklendirme**: Claude AI ile akıllı görev sıralama
- **Teklif Oluşturma**: Metin girdisinden profesyonel teklif
- **Belge Validasyonu**: Otomatik belge kontrolü
- **Email Oluşturma**: AI destekli email içerikleri

## 📋 Gereksinimler

- Python 3.11+
- Django 5.0+
- SQLite (geliştirme) / PostgreSQL (production)
- Anthropic API anahtarı (Claude AI için)

## 🛠️ Kurulum

### 1. Repository'yi klonlayın
```bash
git clone https://github.com/your-repo/leasing_core.git
cd leasing_core
```

### 2. Virtual environment oluşturun
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# veya
venv\Scripts\activate  # Windows
```

### 3. Bağımlılıkları yükleyin
```bash
pip install -r requirements.txt
```

### 4. Environment değişkenlerini ayarlayın
```bash
cp .env.example .env
# .env dosyasını düzenleyin ve gerekli değerleri girin
```

### 5. Veritabanını hazırlayın
```bash
python manage.py migrate
python manage.py seed_admin  # Admin kullanıcısı oluşturur
```

### 6. Statik dosyaları toplayın
```bash
python manage.py collectstatic
```

### 7. Geliştirme sunucusunu başlatın
```bash
python manage.py runserver
```

Uygulama `http://localhost:8000` adresinde çalışacaktır.

## 📁 Proje Yapısı

```
leasing_core/
├── accounts/           # Kullanıcı yönetimi ve authentication
├── ai_services/        # Claude AI entegrasyonu
├── core/               # Ortak modeller ve utilities
├── customers/          # Müşteri yönetimi
├── documents/          # Belge yönetimi (KVKK uyumlu)
├── orders/             # Sipariş yönetimi
├── proposals/          # AI teklif oluşturma
├── tasks/              # Görev yönetimi
├── templates/          # HTML şablonları
├── static/             # Statik dosyalar (CSS, JS)
├── media/              # Yüklenen dosyalar
└── leasing_core/       # Django proje ayarları
```

## 🔐 Kullanıcı Rolleri

| Rol | Erişim |
|-----|--------|
| Admin | Tüm sistem, departman yönetimi, raporlar |
| Salesperson | Müşteriler, görevler, teklifler, siparişler |
| Customer | Kendi siparişleri, belge yükleme |

## 🔧 Konfigürasyon

### AI Servisi (Claude)
```env
ANTHROPIC_API_KEY=your-api-key
AI_MODEL=claude-sonnet-4-20250514
AI_MAX_TOKENS=4096
```

### Email (Gmail SMTP)
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Veritabanı (Production)
```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

## 🧪 Test

```bash
# Tüm testleri çalıştır
python manage.py test

# Belirli bir app için
python manage.py test customers

# Coverage raporu
coverage run manage.py test
coverage report
```

## 📊 API Endpoints

| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/accounts/login/` | POST | Kullanıcı girişi |
| `/customers/` | GET | Müşteri listesi |
| `/customers/<id>/` | GET | Müşteri detayı |
| `/tasks/` | GET | Görev listesi |
| `/orders/` | GET | Sipariş listesi |
| `/proposals/` | GET | Teklif listesi |
| `/documents/` | GET | Belge listesi |

## 🔒 Güvenlik

- HTTPS zorunlu (production)
- CSRF koruması
- Rate limiting
- KVKK uyumlu veri şifreleme
- Audit logging
- Role-based access control

## 📝 KVKK Uyumluluğu

- Kişisel veri şifreleme
- Veri erişim logları
- Veri silme/anonimleştirme
- Veri dışa aktarma
- Açık rıza yönetimi

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'i push edin (`git push origin feature/amazing`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📞 İletişim

Sorularınız için: support@leasing.com
