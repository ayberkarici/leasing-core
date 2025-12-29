"""
KVKK Service - KVKK belge yönetimi ve PDF oluşturma.
"""

import io
import logging
from typing import Optional, Tuple
from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings

from documents.models import KVKKTemplate, KVKKDocument, KVKKStatus

logger = logging.getLogger(__name__)


class KVKKService:
    """KVKK belge yönetim servisi."""
    
    # Varsayılan KVKK metni (admin henüz şablon oluşturmadıysa)
    DEFAULT_KVKK_CONTENT = """
    <h3>1. Veri Sorumlusu</h3>
    <p>
        6698 sayılı Kişisel Verilerin Korunması Kanunu ("KVKK") uyarınca, kişisel verileriniz; 
        veri sorumlusu olarak <strong>Leasing Yönetim Sistemi</strong> tarafından aşağıda açıklanan 
        kapsamda işlenebilecektir.
    </p>
    
    <h3>2. Kişisel Verilerin İşlenme Amaçları</h3>
    <p>Toplanan kişisel verileriniz;</p>
    <ul>
        <li>Leasing hizmetlerinin sunulması ve yürütülmesi</li>
        <li>Sözleşme süreçlerinin yürütülmesi</li>
        <li>Müşteri ilişkileri yönetimi</li>
        <li>Finans ve muhasebe işlemlerinin yürütülmesi</li>
        <li>Risk değerlendirme ve kredi skorlama süreçleri</li>
        <li>Yasal yükümlülüklerin yerine getirilmesi</li>
        <li>İletişim faaliyetlerinin yürütülmesi</li>
        <li>Bilgi güvenliği süreçlerinin yürütülmesi</li>
    </ul>
    <p>amaçlarıyla KVKK'nın 5. ve 6. maddelerinde belirtilen kişisel veri işleme şartları dahilinde işlenebilecektir.</p>
    
    <h3>3. İşlenen Kişisel Veriler</h3>
    <p>Aşağıdaki kişisel verileriniz işlenebilecektir:</p>
    <ul>
        <li><strong>Kimlik Bilgileri:</strong> Ad, soyad, T.C. kimlik numarası, doğum tarihi</li>
        <li><strong>İletişim Bilgileri:</strong> Telefon numarası, e-posta adresi, adres</li>
        <li><strong>Finansal Bilgiler:</strong> Banka hesap bilgileri, vergi numarası, gelir bilgileri</li>
        <li><strong>Şirket Bilgileri:</strong> Ticaret sicil bilgileri, yetkili kişi bilgileri</li>
        <li><strong>İşlem Güvenliği:</strong> IP adresi, log kayıtları, oturum bilgileri</li>
    </ul>
    
    <h3>4. Kişisel Verilerin Aktarımı</h3>
    <p>
        Kişisel verileriniz, yukarıda belirtilen amaçların gerçekleştirilmesi doğrultusunda;
    </p>
    <ul>
        <li>Bankalar ve finansal kuruluşlar</li>
        <li>Kamu kurum ve kuruluşları (BDDK, SPK, Hazine vb.)</li>
        <li>Hizmet aldığımız iş ortakları ve tedarikçiler</li>
        <li>Bağımsız denetim şirketleri</li>
    </ul>
    <p>ile KVKK'nın 8. ve 9. maddelerinde belirtilen kişisel veri işleme şartları dahilinde paylaşılabilecektir.</p>
    
    <h3>5. Kişisel Verilerin Toplanma Yöntemi ve Hukuki Sebebi</h3>
    <p>
        Kişisel verileriniz; elektronik ortamda (web sitesi, e-posta, mobil uygulama) ve fiziki ortamda 
        (başvuru formları, sözleşmeler) toplanabilmektedir.
    </p>
    
    <h3>6. Kişisel Veri Sahibinin Hakları</h3>
    <p>KVKK'nın 11. maddesi uyarınca aşağıdaki haklara sahipsiniz:</p>
    <ul>
        <li>Kişisel verilerinizin işlenip işlenmediğini öğrenme</li>
        <li>İşlenmişse buna ilişkin bilgi talep etme</li>
        <li>İşlenme amacını ve bunların amacına uygun kullanılıp kullanılmadığını öğrenme</li>
        <li>Yurt içinde veya yurt dışında aktarıldığı üçüncü kişileri bilme</li>
        <li>Eksik veya yanlış işlenmişse düzeltilmesini isteme</li>
        <li>KVKK'nın 7. maddesinde öngörülen şartlar çerçevesinde silinmesini veya yok edilmesini isteme</li>
        <li>Aktarıldığı üçüncü kişilere bildirilmesini isteme</li>
        <li>Münhasıran otomatik sistemler vasıtasıyla analiz edilmesi suretiyle aleyhinize bir sonucun ortaya çıkmasına itiraz etme</li>
        <li>Kanuna aykırı olarak işlenmesi sebebiyle zarara uğramanız halinde zararın giderilmesini talep etme</li>
    </ul>
    
    <h3>7. Veri Güvenliği</h3>
    <p>
        Kişisel verilerinizin güvenliği için gerekli teknik ve idari tedbirler alınmaktadır. 
        Verileriniz şifreli olarak saklanmakta, yetkisiz erişime karşı koruma altında tutulmaktadır.
    </p>
    
    <h3>8. İletişim</h3>
    <p>
        KVKK kapsamındaki haklarınızı kullanmak için bizimle iletişime geçebilirsiniz.
    </p>
    """
    
    @classmethod
    def get_default_kvkk_content(cls) -> str:
        """Varsayılan KVKK metnini getir."""
        template = KVKKTemplate.get_active_template()
        if template:
            return template.content
        return cls.DEFAULT_KVKK_CONTENT
    
    @classmethod
    def get_template_version(cls) -> str:
        """Aktif şablon versiyonunu getir."""
        template = KVKKTemplate.get_active_template()
        if template:
            return template.version
        return "1.0"
    
    @classmethod
    def create_kvkk_for_customer(cls, customer, created_by, custom_content: Optional[str] = None) -> KVKKDocument:
        """
        Müşteri için KVKK belgesi oluştur.
        
        Args:
            customer: Customer instance
            created_by: User who creates the document
            custom_content: Optional custom KVKK content (uses default if not provided)
        
        Returns:
            KVKKDocument instance
        """
        content = custom_content if custom_content else cls.get_default_kvkk_content()
        version = cls.get_template_version()
        
        kvkk_doc, created = KVKKDocument.objects.get_or_create(
            customer=customer,
            defaults={
                'kvkk_content': content,
                'template_version': version,
                'status': KVKKStatus.DRAFT,
                'created_by': created_by,
            }
        )
        
        if not created:
            # Güncelle
            kvkk_doc.kvkk_content = content
            kvkk_doc.template_version = version
            kvkk_doc.save()
        
        return kvkk_doc
    
    @classmethod
    def send_for_signature(cls, kvkk_doc: KVKKDocument, user) -> bool:
        """KVKK'yı imzaya gönder."""
        kvkk_doc.status = KVKKStatus.PENDING_SIGNATURE
        kvkk_doc.created_by = user
        kvkk_doc.save()
        return True
    
    @classmethod
    def upload_signed_document(cls, kvkk_doc: KVKKDocument, file) -> bool:
        """İmzalı belgeyi yükle."""
        kvkk_doc.signed_document = file
        kvkk_doc.uploaded_at = timezone.now()
        kvkk_doc.status = KVKKStatus.PENDING_APPROVAL
        kvkk_doc.save()
        return True
    
    @classmethod
    def approve_kvkk(cls, kvkk_doc: KVKKDocument, user) -> bool:
        """KVKK'yı onayla."""
        kvkk_doc.approve(user)
        return True
    
    @classmethod
    def request_revision(cls, kvkk_doc: KVKKDocument, user, reason: str) -> bool:
        """Revizyon iste."""
        kvkk_doc.request_revision(user, reason)
        return True
    
    _font_registered = False
    _font_name = 'Helvetica'
    
    @classmethod
    def _register_turkish_fonts(cls):
        """Türkçe karakter destekli fontları kaydet."""
        if cls._font_registered:
            return cls._font_name
        
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os
        
        # Font arama yolları
        font_paths = [
            # macOS
            '/Library/Fonts/Arial Unicode.ttf',
            '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
            '/System/Library/Fonts/Geneva.ttf',
            # Linux
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
            '/usr/share/fonts/TTF/DejaVuSans.ttf',
            # Windows
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/ARIALUNI.TTF',
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('TurkishFont', font_path))
                    cls._font_registered = True
                    cls._font_name = 'TurkishFont'
                    logger.info(f"Turkish font registered from: {font_path}")
                    return cls._font_name
                except Exception as e:
                    logger.warning(f"Could not register font from {font_path}: {e}")
                    continue
        
        # Fallback - use built-in Helvetica (limited Turkish support)
        logger.warning("No Turkish-supporting font found, using Helvetica")
        cls._font_registered = True
        return 'Helvetica'
    
    @classmethod
    def generate_pdf(cls, kvkk_doc: KVKKDocument) -> Tuple[bytes, str]:
        """
        KVKK PDF'i oluştur.
        
        Returns:
            Tuple of (pdf_bytes, filename)
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
            from bs4 import BeautifulSoup
            import re
            
            # Türkçe font kaydet
            font_name = cls._register_turkish_fonts()
            
            # PDF buffer
            buffer = io.BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Styles with Turkish font support
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=18,
                textColor=colors.HexColor('#1e3a5f'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=font_name,
                fontSize=12,
                textColor=colors.HexColor('#1e3a5f'),
                spaceBefore=15,
                spaceAfter=10
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=10,
                leading=14,
                alignment=TA_JUSTIFY
            )
            
            # Build story
            story = []
            
            # Title
            story.append(Paragraph("KVKK AYDINLATMA METNİ", title_style))
            story.append(Spacer(1, 20))
            
            # Company info
            customer = kvkk_doc.customer
            company_info = f"""
            <b>Firma:</b> {customer.display_company_name}<br/>
            <b>İlgili Kişi:</b> {customer.contact_person}<br/>
            <b>Tarih:</b> {timezone.now().strftime('%d.%m.%Y')}
            """
            story.append(Paragraph(company_info, body_style))
            story.append(Spacer(1, 30))
            
            # Parse HTML content and convert to PDF elements
            soup = BeautifulSoup(kvkk_doc.kvkk_content, 'html.parser')
            
            for element in soup.children:
                if element.name == 'h3':
                    story.append(Paragraph(element.get_text(), heading_style))
                elif element.name == 'p':
                    text = str(element).replace('<p>', '').replace('</p>', '')
                    story.append(Paragraph(text, body_style))
                    story.append(Spacer(1, 8))
                elif element.name == 'ul':
                    for li in element.find_all('li'):
                        text = f"• {li.get_text()}"
                        story.append(Paragraph(text, body_style))
                    story.append(Spacer(1, 8))
            
            # Signature section
            story.append(Spacer(1, 40))
            story.append(Paragraph("<b>ONAY VE İMZA</b>", heading_style))
            story.append(Spacer(1, 10))
            
            approval_text = """
            Yukarıda yer alan KVKK Aydınlatma Metnini okudum, anladım ve kişisel verilerimin 
            belirtilen amaçlarla işlenmesine onay veriyorum.
            """
            story.append(Paragraph(approval_text, body_style))
            story.append(Spacer(1, 30))
            
            # Signature table
            sig_data = [
                ['İmza:', '______________________'],
                ['Ad Soyad:', '______________________'],
                ['Tarih:', '______________________'],
                ['Kaşe:', '______________________'],
            ]
            
            sig_table = Table(sig_data, colWidths=[3*cm, 8*cm])
            sig_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ]))
            story.append(sig_table)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            # Filename
            safe_company = re.sub(r'[^\w\s-]', '', customer.display_company_name).strip()
            filename = f"KVKK_{safe_company}_{timezone.now().strftime('%Y%m%d')}.pdf"
            
            return pdf_bytes, filename
            
        except ImportError:
            logger.warning("reportlab or beautifulsoup4 not installed, returning simple PDF")
            return cls._generate_simple_pdf(kvkk_doc)
    
    @classmethod
    def _generate_simple_pdf(cls, kvkk_doc: KVKKDocument) -> Tuple[bytes, str]:
        """Basit PDF oluştur (reportlab yoksa)."""
        import re
        from bs4 import BeautifulSoup
        
        # Plain text version
        soup = BeautifulSoup(kvkk_doc.kvkk_content, 'html.parser')
        text_content = soup.get_text(separator='\n')
        
        customer = kvkk_doc.customer
        
        content = f"""
KVKK AYDINLATMA METNİ

Firma: {customer.display_company_name}
İlgili Kişi: {customer.contact_person}
Tarih: {timezone.now().strftime('%d.%m.%Y')}

{'='*50}

{text_content}

{'='*50}

ONAY VE İMZA

Yukarıda yer alan KVKK Aydınlatma Metnini okudum, anladım ve 
kişisel verilerimin belirtilen amaçlarla işlenmesine onay veriyorum.

İmza: ______________________

Ad Soyad: ______________________

Tarih: ______________________

Kaşe: ______________________
"""
        
        safe_company = re.sub(r'[^\w\s-]', '', customer.display_company_name).strip()
        filename = f"KVKK_{safe_company}_{timezone.now().strftime('%Y%m%d')}.txt"
        
        return content.encode('utf-8'), filename


# Singleton instance
kvkk_service = KVKKService()

