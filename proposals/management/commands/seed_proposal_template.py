"""
Management command to seed default proposal template.
"""
from django.core.management.base import BaseCommand
from proposals.models import ProposalTemplate, TemplateSectionField


class Command(BaseCommand):
    help = 'Create default proposal template with sections'

    def handle(self, *args, **options):
        # Check if active template exists
        if ProposalTemplate.objects.filter(is_active=True).exists():
            self.stdout.write(self.style.WARNING('Aktif teklif şablonu zaten mevcut.'))
            return
        
        # Default input guide
        input_guide = """Teklif oluşturmak için aşağıdaki bilgileri içeren bir açıklama yazın:

• Ekipman türü ve markası (örn: Caterpillar ekskavatör, Komatsu dozer)
• Ekipman adedi
• Tahmini ekipman değeri
• İstenen kiralama süresi (ay)
• Peşinat tercihi varsa
• Özel istekler veya notlar

Örnek:
"ABC İnşaat için 2 adet Caterpillar 320 ekskavatör ve 1 adet Komatsu D65 dozer teklifi hazırla. Toplam değer yaklaşık 5 milyon TL, 36 ay vade istiyorlar. %10 peşinat ödeyebilirler, aylık taksitleri mümkün olduğunca düşük tutmak istiyorlar."
"""
        
        # Default email content
        email_subject = "Leasing Teklifi - {company_name}"
        
        email_body = """Sayın {contact_person},

{company_name} için hazırladığımız leasing teklifini ekte bulabilirsiniz.

TEKLİF DETAYLARI:
-----------------
Ekipman: {equipment_description}
Kiralama Süresi: {lease_term_months} Ay
Aylık Taksit: {monthly_payment} {currency}

Bu teklif {valid_days} gün geçerlidir.

Teklifimiz hakkında sorularınız için bize ulaşabilirsiniz.

Saygılarımızla,

{salesperson_name}
{salesperson_email}
{salesperson_phone}
"""

        # Create template
        template = ProposalTemplate.objects.create(
            name='Varsayılan Teklif Şablonu',
            description='Genel amaçlı leasing teklif şablonu. Tüm ekipman türleri için uygundur.',
            input_guide=input_guide,
            email_subject=email_subject,
            email_body=email_body,
            default_valid_days=30,
            is_active=True
        )
        
        self.stdout.write(self.style.SUCCESS(f'Teklif şablonu oluşturuldu: {template.name}'))
        
        # Create default sections
        sections = [
            {
                'field_type': 'introduction',
                'title': 'Giriş',
                'description': 'Müşteriye hitaben profesyonel bir giriş yazın. Firmaya özgü detaylar ekleyin ve iş birliği fırsatını vurgulayın.',
                'placeholder_content': 'Sayın ABC İnşaat Yetkilileri, Sektörünüzde 10 yıllık deneyiminiz ve başarılı projelerinizle tanınan firmanız için özel olarak hazırladığımız leasing teklifimizi...',
                'is_ai_generated': True,
                'order': 0
            },
            {
                'field_type': 'equipment_details',
                'title': 'Ekipman Detayları',
                'description': 'Talep edilen ekipmanların detaylı açıklamasını yapın. Marka, model, özellikler ve teknik detayları listeleyin.',
                'placeholder_content': '1. Caterpillar 320 Ekskavatör (2 adet)\n   - Motor Gücü: 121 kW\n   - Çalışma Ağırlığı: 20.000 kg',
                'is_ai_generated': True,
                'order': 1
            },
            {
                'field_type': 'pricing',
                'title': 'Fiyatlandırma ve Ödeme Planı',
                'description': 'Finansal detayları net ve anlaşılır şekilde sunun. Toplam değer, peşinat, vade ve aylık ödeme bilgilerini içerin.',
                'placeholder_content': 'Toplam Ekipman Değeri: 5.000.000 TL\nPeşinat (%10): 500.000 TL\nVade: 36 Ay\nAylık Taksit: 150.000 TL',
                'is_ai_generated': True,
                'order': 2
            },
            {
                'field_type': 'benefits',
                'title': 'Avantajlar',
                'description': 'Leasing teklifinin müşteriye sağlayacağı avantajları listeleyin. Vergi avantajları, nakit akışı, bakım dahil seçenekleri belirtin.',
                'placeholder_content': '• Sermaye koruma: Yatırımınızı koruyun\n• Vergi avantajı: Kira ödemeleri gider yazılabilir\n• Güncel ekipman: Vade sonunda yenileme imkanı',
                'is_ai_generated': True,
                'order': 3
            },
            {
                'field_type': 'terms',
                'title': 'Şartlar ve Koşullar',
                'description': 'Genel şartları ve koşulları açıklayın. Sigorta, bakım, teslim süresi gibi detayları belirtin.',
                'placeholder_content': '• Sigorta: Kasko sigortası kiracıya aittir\n• Bakım: Periyodik bakımlar kiracı tarafından yapılır\n• Teslim: Sözleşme tarihinden itibaren 15 iş günü',
                'is_ai_generated': True,
                'order': 4
            },
            {
                'field_type': 'conclusion',
                'title': 'Sonuç',
                'description': 'Teklifi özetleyin ve bir sonraki adımları belirtin. İletişim bilgileri ve aksiyon çağrısı ekleyin.',
                'placeholder_content': 'Bu teklifin firmanızın ihtiyaçlarına uygun olduğuna inanıyoruz. Detayları görüşmek için sizinle bir toplantı planlamaktan memnuniyet duyarız.',
                'is_ai_generated': True,
                'order': 5
            }
        ]
        
        for section_data in sections:
            TemplateSectionField.objects.create(
                template=template,
                **section_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'{len(sections)} bölüm oluşturuldu.'))
