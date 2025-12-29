"""
PDF Generator Service for Proposals.
Generates professional PDF documents from proposals.
"""

import os
from io import BytesIO
from typing import Optional
from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.base import ContentFile


class PDFGenerator:
    """
    Teklif PDF oluşturucu.
    HTML şablonlarından PDF dosyaları oluşturur.
    """
    
    def __init__(self):
        self.template_name = 'proposals/pdf/proposal_template.html'
    
    def generate_pdf(self, proposal) -> Optional[bytes]:
        """
        Tekliften PDF oluştur.
        
        Args:
            proposal: Proposal model instance
            
        Returns:
            PDF bytes or None
        """
        try:
            # Try to use weasyprint if available
            from weasyprint import HTML, CSS
            
            # Render HTML
            html_content = self._render_html(proposal)
            
            # Generate PDF
            html = HTML(string=html_content, base_url=settings.BASE_DIR)
            
            # Add CSS
            css = CSS(string=self._get_pdf_css())
            
            pdf_bytes = html.write_pdf(stylesheets=[css])
            return pdf_bytes
            
        except ImportError:
            # Fallback: just return HTML as a simple text-based approach
            # In production, weasyprint should be installed
            return self._generate_simple_pdf(proposal)
    
    def _render_html(self, proposal) -> str:
        """Teklif HTML'ini oluştur."""
        context = {
            'proposal': proposal,
            'customer': proposal.customer,
            'sections': proposal.sections.all().order_by('order'),
            'company_info': {
                'name': 'Leasing Şirketi',
                'address': 'İstanbul, Türkiye',
                'phone': '+90 212 XXX XX XX',
                'email': 'info@leasing.com',
                'website': 'www.leasing.com'
            }
        }
        return render_to_string(self.template_name, context)
    
    def _get_pdf_css(self) -> str:
        """PDF için CSS stilleri."""
        return """
        @page {
            size: A4;
            margin: 2cm;
            @top-right {
                content: "Sayfa " counter(page) " / " counter(pages);
                font-size: 10px;
                color: #666;
            }
        }
        
        body {
            font-family: 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }
        
        .header {
            border-bottom: 2px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #2563eb;
        }
        
        h1 {
            font-size: 24px;
            color: #1e293b;
            margin-bottom: 10px;
        }
        
        h2 {
            font-size: 18px;
            color: #2563eb;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 5px;
            margin-top: 25px;
        }
        
        h3 {
            font-size: 14px;
            color: #475569;
        }
        
        .section {
            margin-bottom: 25px;
            page-break-inside: avoid;
        }
        
        .equipment-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        
        .equipment-table th,
        .equipment-table td {
            border: 1px solid #e2e8f0;
            padding: 10px;
            text-align: left;
        }
        
        .equipment-table th {
            background: #f1f5f9;
            font-weight: bold;
        }
        
        .pricing-box {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .price-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px dashed #e2e8f0;
        }
        
        .price-total {
            font-size: 18px;
            font-weight: bold;
            color: #2563eb;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            font-size: 10px;
            color: #64748b;
        }
        
        .signature-area {
            margin-top: 50px;
            display: flex;
            justify-content: space-between;
        }
        
        .signature-box {
            width: 45%;
            border-top: 1px solid #333;
            padding-top: 10px;
            text-align: center;
        }
        """
    
    def _generate_simple_pdf(self, proposal) -> bytes:
        """
        Basit metin tabanlı PDF (weasyprint olmadan).
        Not: Gerçek uygulamada weasyprint kullanılmalı.
        """
        # Create a simple text representation
        content = f"""
LEASING TEKLİFİ
===============

Teklif No: {proposal.id}
Tarih: {proposal.created_at.strftime('%d.%m.%Y')}

MÜŞTERİ BİLGİLERİ
-----------------
{proposal.customer.company_name or proposal.customer.full_name}
{proposal.customer.email}

TEKLİF BAŞLIĞI
--------------
{proposal.title}

TEKLİF İÇERİĞİ
--------------
{proposal.generated_content or proposal.description}

FİNANSAL DETAYLAR
-----------------
Ekipman Değeri: {proposal.equipment_value or 'Belirtilmemiş'} TL
Kiralama Süresi: {proposal.lease_term_months} Ay
Aylık Ödeme: {proposal.monthly_payment or 'Hesaplanacak'} TL

---
Bu teklif {proposal.valid_until or '30 gün'} tarihine kadar geçerlidir.
        """
        
        return content.encode('utf-8')
    
    def save_pdf_to_proposal(self, proposal) -> bool:
        """
        PDF'i oluştur ve proposal'a kaydet.
        
        Args:
            proposal: Proposal model instance
            
        Returns:
            Success status
        """
        pdf_bytes = self.generate_pdf(proposal)
        
        if pdf_bytes:
            filename = f"proposal_{proposal.id}_{proposal.created_at.strftime('%Y%m%d')}.pdf"
            proposal.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
            return True
        
        return False



