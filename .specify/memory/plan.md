# Leasing Yönetim Sistemi - Uygulama Planı

## Faz Yapısı ve Timeline

### Genel Yaklaşım
- **Toplam Süre**: 12 hafta
- **Sprint Uzunluğu**: 2 hafta
- **Toplam Sprint**: 6 sprint
- **Methodology**: Agile/Scrum
- **İlk Çalışır Versiyon**: 6. hafta sonu
- **Production Ready**: 12. hafta

## Faz 1: Temel Altyapı (Sprint 1 - Hafta 1-2)

### Hedefler
- Django projesi kurulumu ve yapılandırması
- Temel authentication sistemi
- Database şeması
- Admin interface
- Basit dashboard'lar

### Teknik Görevler

#### Django Proje Kurulumu
- Django 5.x projesi oluştur
- Virtual environment setup
- requirements.txt hazırla
- .env dosyası ve environment variable yapısı
- .gitignore konfigürasyonu
- settings.py yapılandırması (dev/prod separation)

#### Database Tasarımı
- CustomUser modeli (AbstractUser'dan extend)
- Department modeli
- İlk migration'lar
- Admin user seeding

#### Authentication Sistemi
- Login/Logout views
- Password reset flow
- Session management
- Login required decorators

#### Admin Interface
- Django admin özelleştirme
- User management interface
- Department management

#### Dashboard Temelleri
- Base template oluştur
- Navigation menu
- Role-based routing logic
- Basit admin dashboard
- Basit sales dashboard
- Basit customer dashboard

### Deliverables
- ✅ Çalışan Django projesi
- ✅ Login/Logout yapılabiliyor
- ✅ 3 farklı kullanıcı tipi oluşturulabiliyor
- ✅ Her rol kendi dashboard'unu görüyor
- ✅ Admin temel CRUD işlemleri yapabiliyor

### Başarı Kriterleri
- Unit testler yazılmış ve passing
- 3 farklı kullanıcı ile manuel test yapılmış
- Code review tamamlanmış
- Documentation (README) güncellenmiş

---

## Faz 2: KVKK ve Müşteri Onboarding (Sprint 2 - Hafta 3-4)

### Hedefler
- Müşteri kayıt sistemi
- KVKK belge upload ve yorum sistemi
- AI ile paraf/imza validasyonu
- Hesap aktivasyon akışı
- Email notification sistemi

### Teknik Görevler

#### Müşteri Modeli
- Customer model (CustomUser extend)
- Salesperson assignment logic
- Customer-Salesperson relationship
- Customer status (pending_kvkk, active, suspended)

#### KVKK Sistemi
- KVKKDocument modeli
- KVKKComment modeli
- KVKK PDF viewer interface
- Comment UI (highlight and comment)
- Signed document upload interface
- File validation (PDF only, max 10MB)

#### AI Paraf/İmza Kontrolü
- Claude API integration setup
- Image/PDF to base64 conversion
- AI service class: SignatureValidator
- Prompt engineering for signature detection
- Response parsing and validation
- Error handling and fallback

#### Email Sistemi
- Django email backend configuration
- Email template'ler:
  - Müşteri kayıt
  - KVKK onay talebi
  - Hesap aktivasyon
- Email sending utility functions
- Email log modeli (tracking)

#### Approval Workflow
- Salesperson approval queue interface
- KVKK review screen
- Approve/Reject actions
- Customer notification on status change
- Account activation logic

### Deliverables
- ✅ Satışçı müşteri kaydı oluşturabiliyor
- ✅ Müşteri email alıp giriş yapabiliyor
- ✅ KVKK belgesi görüntülenip yorum eklenebiliyor
- ✅ İmzalı KVKK yüklenip AI kontrolü yapılıyor
- ✅ Satışçı onaylayıp hesap aktif oluyor
- ✅ Müşteri dashboard'una erişebiliyor

### Başarı Kriterleri
- AI imza tespiti %90+ doğruluk
- End-to-end onboarding akışı çalışıyor
- Email'ler doğru gönderiliyor
- Unit ve integration testler yazılmış

---

## Faz 3: Sipariş ve Belge Yönetimi (Sprint 3-4 - Hafta 5-8)

### Hedefler
- Sipariş oluşturma wizard
- Belge şablon sistemi
- Belge yükleme ve real-time validasyon
- AI belge içerik kontrolü
- Satışçı onay interface
- Durum takip sistemi

### Teknik Görevler

#### Belge Şablon Sistemi (Sprint 3)
- DocumentTemplate modeli
- Template field yapısı (JSON)
- Template CRUD interface (admin için)
- Example document upload
- Template listing ve detay sayfaları

#### Sipariş Modeli (Sprint 3)
- Order modeli
- Order status choices
- OrderNote modeli (timeline için)
- Customer-Order relationship

#### Sipariş Wizard (Sprint 3)
- Multi-step form UI
- Step 1: Equipment selection
- Step 2: Document upload
- Progress indicator
- Save as draft functionality
- Session-based state management

#### Belge Upload Sistemi (Sprint 3-4)
- UploadedDocument modeli
- Drag-and-drop file upload UI
- File type validation (PDF, Word, Images)
- File size validation (max 10MB)
- Multiple file support
- Upload progress indicator

#### AI Belge Validasyonu (Sprint 4)
- DocumentValidator service class
- OCR integration (Tesseract optional)
- PDF text extraction (PyPDF2)
- Word text extraction (python-docx)
- Claude API ile içerik analizi
- Field matching logic
- Signature/paraf detection (visual)
- Validation result JSON structure
- Real-time validation feedback UI

#### Validation Feedback UI (Sprint 4)
- Per-document validation status
- Field checklist with status icons
- Error/warning messages
- Missing field highlighting
- Re-upload functionality
- Overall completion percentage

#### Satışçı Onay Interface (Sprint 4)
- Pending orders queue
- Order detail view for sales
- Document preview
- AI validation results display
- Approve/Reject actions
- Request correction functionality
- Department forwarding logic

#### Durum Takibi (Sprint 4)
- Order status transitions
- Timeline view (activity log)
- Status change notifications
- Customer order list
- Order detail view for customer

### Deliverables
- ✅ Belge şablonları tanımlanabiliyor
- ✅ Müşteri sipariş oluşturup belge yükleyebiliyor
- ✅ AI belgeleri analiz edip feedback veriyor
- ✅ Geçersiz belgeler tespit ediliyor
- ✅ Tüm belgeler valid olunca submit edilebiliyor
- ✅ Satışçı onay kuyruğunda görebiliyor
- ✅ Onay sonrası durum değişiyor
- ✅ Müşteri sipariş durumunu takip edebiliyor

### Başarı Kriterleri
- AI belge validasyonu %95+ accuracy
- Upload süreci sorunsuz
- Real-time feedback çalışıyor
- End-to-end sipariş akışı tamamlanabiliyor
- Performance acceptable (2s page load)

---

## Faz 4: Görev Yönetimi ve AI Önceliklendirme (Sprint 5 - Hafta 9-10)

### Hedefler
- Task modeli ve ilişkiler
- Görev listeleme ve filtreleme
- AI görev önceliklendirme
- Günlük özet ve "Bugünün Önemlileri"
- Bildirim sistemi

### Teknik Görevler

#### Task Modeli
- Task modeli
- Task-Order relationship
- Task-Customer relationship
- Task status choices
- Priority score field
- Last interaction tracking
- AI notes field

#### Task Listeleme UI
- All tasks view
- Filtreleme: status, customer, date range
- Sıralama: priority, date, customer
- Search functionality
- Pagination
- Color-coded by priority

#### AI Önceliklendirme
- TaskPrioritizer service class
- Task data collection ve serialization
- Claude API integration
- Priority score calculation prompt
- Daily focus list generation
- Reasoning extraction
- Automated scoring (cron job veya manual trigger)

#### "Bugünün Önemlileri" Widget
- Dashboard widget component
- Top 5 priority tasks display
- Task card design (compact)
- Quick action buttons
- AI reasoning display
- Link to full task detail

#### Task Detail View
- Complete task information
- Customer profile card
- Order details
- Document status
- Communication history
- AI suggestions section
- Quick actions: Call, Email, Update
- Status update form

#### Bildirimler
- Notification modeli
- In-app notification sistem
- Bell icon with unread count
- Notification dropdown
- Mark as read functionality
- Notification types
- Email daily digest (optional)

### Deliverables
- ✅ Görevler oluşturuluyor (manuel + otomatik)
- ✅ AI görevleri önceliklendiriyor
- ✅ Satışçı günlük öncelik listesini görüyor
- ✅ Görev detaylarına erişebiliyor
- ✅ Durum güncelleyebiliyor
- ✅ Bildirimler çalışıyor

### Başarı Kriterleri
- AI önceliklendirme mantıklı ve tutarlı
- Günlük özet faydalı
- Performance: 100 görev için <3s
- Satışçı feedback'i pozitif
- Test coverage >80%

---

## Faz 5: Teklif Oluşturma ve Gönderme (Sprint 5 - Hafta 9-10)

### Hedefler
- Teklif modeli
- AI ile teklif oluşturma (text/voice)
- PDF generation
- Email gönderimi
- Teklif yönetimi

### Teknik Görevler

#### Teklif Modeli
- Proposal modeli
- Structure field (JSON)
- Customer relationship (optional)
- Salesperson relationship
- PDF file field
- Sent status ve timestamp

#### Teklif Oluşturma UI
- "Yeni Teklif" button
- Input method seçimi:
  - Serbest metin
  - Yapılandırılmış form
  - Şablon seçimi
- Multi-line text area (voice destekli opsiyonel)
- Form interface (ekipman, vade, tutar, koşullar)
- Template selection dropdown

#### AI Teklif Üretimi
- ProposalGenerator service class
- Requirement parsing (NLP)
- Equipment identification
- Term calculation
- Content generation
- Structure JSON creation
- Claude API integration
- Prompt engineering for proposals

#### PDF Generation
- PDF template design
- Django template for PDF veya ReportLab
- Company branding
- Section rendering
- Table formatting
- PDF file creation
- Storage to database

#### Email Gönderimi
- Customer selection
- AI email composition
- Email template with proposal attachment
- Send functionality
- Tracking (sent timestamp)
- Email log

#### Teklif Yönetimi
- Proposal list view
- Filter by customer, date, status
- Proposal detail view
- Edit/regenerate functionality
- Version history (optional)
- Status tracking (sent, accepted, rejected)

### Deliverables
- ✅ Satışçı metin ile teklif oluşturabiliyor
- ✅ AI teklif içeriği üretiyor
- ✅ PDF generate ediliyor
- ✅ Müşteriye email gönderiliyor
- ✅ Teklif listesi ve detayları görülebiliyor

### Başarı Kriterleri
- AI teklif kalitesi yüksek
- PDF profesyonel görünüyor
- Email gönderimi çalışıyor
- End-to-end akış sorunsuz
- User feedback pozitif

---

## Faz 6: İleri Özellikler - Müşteri Araştırması, Formlar, Varlık Analizi (Sprint 6 - Hafta 11-12)

### Hedefler
- Müşteri AI araştırması
- Dinamik form sistemi
- Varlık değerleme ve analizi
- Dashboard iyileştirmeleri

### Teknik Görevler

#### Müşteri Araştırması (3 gün)
- CustomerResearcher service class
- Web search integration (Claude tool)
- Research trigger (post-KVKK)
- Data collection ve parsing
- Risk assessment logic
- Research data JSON storage
- Customer card research section
- Manual refresh button

#### Dinamik Form Sistemi (4 gün)
- FormTemplate modeli
- Field definition structure (JSON)
- FilledForm modeli
- Form builder UI (admin)
- Customer form filling interface
- Step-by-step form wizard
- Real-time validation
- AI content validation
- PDF generation from forms
- Email distribution

#### Varlık Yönetimi (3 gün)
- Asset modeli
- AssetValuation modeli
- AssetAnalyzer service class
- Market research integration (web search)
- Price trend analysis
- Deal analysis logic
- Asset info display in order
- AI recommendations

#### Dashboard İyileştirmeleri (2 gün)
- Admin dashboard charts (Chart.js)
- Statistics cards
- Recent activity feed
- Quick stats
- User activity metrics
- Sales dashboard improvements
- Customer portal enhancements

### Deliverables
- ✅ KVKK sonrası müşteri araştırılıyor
- ✅ Risk değerlendirmesi yapılıyor
- ✅ Form şablonları oluşturulabiliyor
- ✅ Müşteri form doldurabiliyor
- ✅ Form PDF'i generate ediliyor
- ✅ Varlık fiyatları araştırılıyor
- ✅ Anlaşma analizi yapılıyor
- ✅ Dashboard'lar zenginleştirilmiş

### Başarı Kriterleri
- Araştırma verileri faydalı
- Form sistemi esnek ve kullanılabilir
- Varlık analizi doğru
- Dashboard'lar bilgilendirici
- Genel sistem performansı iyi

---

## Faz 7: Test, Optimizasyon ve Deployment (Tüm Sprint'ler + Son Hafta)

### Continuous Testing
Her sprint boyunca:
- Unit test yazımı (her feature için)
- Integration test yazımı (her workflow için)
- Manual testing
- Bug fixing

### Sprint 6 - Kapsamlı Test ve Optimizasyon

#### Comprehensive Testing (3 gün)
- End-to-end testing (tüm user journeys)
- Performance testing (load testing)
- Security audit
- Cross-browser testing
- Mobile responsiveness testing
- AI service validation (accuracy check)

#### Performance Optimization (2 gün)
- Database query optimization
- Index ekleme
- N+1 query problemi çözümü
- Caching stratejisi (optional)
- Frontend optimizasyon (CSS/JS minification)
- Image optimization

#### Bug Fixes ve Polish (3 gün)
- Known bug'ların çözümü
- UI/UX iyileştirmeleri
- Error message'ları netleştirme
- Validation mesajları iyileştirme
- Loading indicators ekleme
- Toast notifications polish

#### Documentation (2 gün)
- README completion
- User manual (Turkish)
- Admin guide
- API documentation (if any)
- Deployment guide
- Troubleshooting guide

### Deployment Preparation

#### Environment Setup
- Production server configuration
- Environment variables setup
- SSL certificate
- Domain configuration
- Email server setup
- Database setup (PostgreSQL migration)

#### Deployment
- Code deployment
- Static files collection
- Database migration
- Initial data seeding (departments, templates)
- Smoke testing
- Monitoring setup (optional)

#### Training
- User training session
- Admin training
- Demo preparation
- FAQ document

---

## Risk Yönetimi ve Azaltma Stratejileri

### Teknik Riskler

**Risk 1: AI API Kesintisi**
- **Olasılık**: Düşük
- **Etki**: Yüksek
- **Azaltma**: 
  - Fallback to manual process UI
  - Retry logic with exponential backoff
  - Error messaging to users
  - Queue mechanism for failed requests

**Risk 2: Performans Problemleri**
- **Olasılık**: Orta
- **Etki**: Orta
- **Azaltma**: 
  - Erken profiling (Sprint 3'ten itibaren)
  - Database indexing
  - Query optimization
  - Caching strategy (if needed)

**Risk 3: Karmaşık AI Prompt'ları**
- **Olasılık**: Orta
- **Etki**: Orta
- **Azaltma**: 
  - Extensive testing of AI responses
  - Multiple prompt iterations
  - Fallback prompts
  - Human review option

### Proje Yönetim Riskleri

**Risk 4: Scope Creep**
- **Olasılık**: Yüksek
- **Etki**: Yüksek
- **Azaltma**: 
  - Strict sprint planning
  - Feature freeze after Sprint 5
  - "Out of scope" list maintenance
  - Stakeholder expectation management

**Risk 5: Resource Availability**
- **Olasılık**: Orta
- **Etki**: Yüksek
- **Azaltma**: 
  - Buffer time in planning
  - Cross-training team members
  - Clear documentation
  - Modular development

---

## Bağımlılıklar ve Kritik Yollar

### Kritik Yol
1. **Temel Altyapı** (Sprint 1) → Bloklar: Her şey
2. **KVKK Sistemi** (Sprint 2) → Bloklar: Müşteri işlemleri
3. **Sipariş + Belge** (Sprint 3-4) → Bloklar: Ana workflow
4. Görev Yönetimi ve Teklif (Sprint 5) → Paralel geliştirilebilir
5. İleri Özellikler (Sprint 6) → Bağımsız

### Paralel Geliştirme Fırsatları
- Sprint 5: Görev Yönetimi ve Teklif sistemi aynı anda
- Sprint 6: Üç feature (Araştırma, Form, Varlık) farklı developer'lar

### Dış Bağımlılıklar
- Anthropic API key (hemen gerekli)
- Email server credentials (Sprint 2'ye kadar)
- Production server (Sprint 6'ya kadar)
- Domain ve SSL (Sprint 6'ya kadar)

