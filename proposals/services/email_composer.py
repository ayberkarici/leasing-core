"""
AI Email Composer Service for Proposals.
Generates professional email content for sending proposals.
"""

from typing import Dict, Any, Optional
from ai_services.services.claude import ClaudeService


class ProposalEmailComposer:
    """
    AI destekli teklif email oluşturucu.
    Profesyonel email içerikleri oluşturur.
    """
    
    def __init__(self):
        self.claude = ClaudeService()
    
    def compose_email(
        self,
        proposal,
        recipient_name: str,
        tone: str = 'professional',
        custom_message: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Teklif için email oluştur.
        
        Args:
            proposal: Proposal model instance
            recipient_name: Alıcı adı
            tone: Email tonu (professional, friendly, formal)
            custom_message: Eklenecek özel mesaj
            
        Returns:
            Dict with 'subject' and 'body'
        """
        prompt = self._build_prompt(proposal, recipient_name, tone, custom_message)
        
        response = self.claude.call_api(
            prompt=prompt,
            system_prompt=self._get_system_prompt(tone)
        )
        
        return self._parse_response(response, proposal, recipient_name)
    
    def _get_system_prompt(self, tone: str) -> str:
        """Ton'a göre sistem promptu."""
        tone_descriptions = {
            'professional': 'profesyonel ve iş odaklı',
            'friendly': 'samimi ama profesyonel',
            'formal': 'resmi ve kurumsal'
        }
        
        tone_desc = tone_descriptions.get(tone, 'profesyonel')
        
        return f"""Sen profesyonel bir email yazarısın. {tone_desc} bir dil kullanıyorsun.
        
Görevin:
1. Leasing teklifleri için etkili emailler yaz
2. Müşteriyi teklife yönlendir
3. Net ve öz ol
4. Call-to-action ekle

Yanıtını SADECE aşağıdaki formatta ver:
KONU: [Email konusu]
---
[Email içeriği]"""
    
    def _build_prompt(
        self,
        proposal,
        recipient_name: str,
        tone: str,
        custom_message: Optional[str]
    ) -> str:
        """Email oluşturma promptu."""
        customer = proposal.customer
        
        equipment_summary = ""
        if proposal.equipment_details:
            items = proposal.equipment_details[:3]  # İlk 3 ekipman
            equipment_summary = ", ".join([
                item.get('name', 'Ekipman') for item in items
            ])
        
        prompt = f"""Aşağıdaki teklif için email yaz:

Alıcı: {recipient_name}
Şirket: {customer.company_name or ''}
Teklif Başlığı: {proposal.title}
Ekipmanlar: {equipment_summary}
Toplam Değer: {proposal.equipment_value or 'Belirtilmemiş'} TL
Kiralama Süresi: {proposal.lease_term_months} ay
Geçerlilik: {proposal.valid_until or '30 gün içinde'}"""
        
        if custom_message:
            prompt += f"\n\nEklenecek özel mesaj:\n{custom_message}"
        
        return prompt
    
    def _parse_response(
        self,
        response: str,
        proposal,
        recipient_name: str
    ) -> Dict[str, str]:
        """AI yanıtını parse et."""
        try:
            if 'KONU:' in response and '---' in response:
                parts = response.split('---', 1)
                subject_line = parts[0].replace('KONU:', '').strip()
                body = parts[1].strip() if len(parts) > 1 else response
                
                return {
                    'subject': subject_line,
                    'body': body
                }
        except Exception:
            pass
        
        # Fallback
        return {
            'subject': f'Leasing Teklifi: {proposal.title}',
            'body': f"""Sayın {recipient_name},

Size özel hazırladığımız leasing teklifimizi dikkatinize sunmak isteriz.

{proposal.title}

Teklifimiz {proposal.lease_term_months} aylık bir süre için hazırlanmış olup, detayları ekte bulabilirsiniz.

Sorularınız için benimle iletişime geçebilirsiniz.

Saygılarımla,
{proposal.salesperson.full_name if proposal.salesperson else 'Leasing Ekibi'}"""
        }
    
    def compose_followup_email(
        self,
        proposal,
        recipient_name: str,
        days_since_sent: int
    ) -> Dict[str, str]:
        """
        Takip emaili oluştur.
        
        Args:
            proposal: Proposal instance
            recipient_name: Alıcı adı
            days_since_sent: Gönderimden bu yana geçen gün
            
        Returns:
            Dict with 'subject' and 'body'
        """
        prompt = f"""Aşağıdaki teklif için takip emaili yaz:

Alıcı: {recipient_name}
Teklif: {proposal.title}
Gönderimden bu yana: {days_since_sent} gün

Nazik bir hatırlatma emaili yaz. Baskıcı olma ama harekete geçirici ol."""
        
        response = self.claude.call_api(
            prompt=prompt,
            system_prompt=self._get_system_prompt('friendly')
        )
        
        return self._parse_response(response, proposal, recipient_name)



