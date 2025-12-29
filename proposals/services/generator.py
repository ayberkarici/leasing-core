"""
AI Proposal Generator Service.
Uses Claude API to generate professional proposals from text input.
"""

import json
import time
from typing import Dict, List, Optional, Any
from django.conf import settings
from ai_services.services.claude import ClaudeService


class ProposalGenerator:
    """
    AI destekli teklif oluşturucu.
    Metin girdisinden profesyonel teklifler oluşturur.
    Template section'larını doldurma desteği sağlar.
    """
    
    def __init__(self):
        self.claude = ClaudeService()
    
    def generate_proposal_with_template(
        self,
        input_text: str,
        customer_info: Dict[str, Any],
        template_sections: List[Dict[str, Any]],
        company_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Template section'larını kullanarak teklif oluştur.
        
        Args:
            input_text: Kullanıcının girdiği metin
            customer_info: Müşteri bilgileri
            template_sections: Admin tarafından tanımlanan template bölümleri
            company_info: Şirket bilgileri (opsiyonel)
            
        Returns:
            Generated proposal data with filled sections
        """
        start_time = time.time()
        
        # Build prompt with template sections
        prompt = self._build_template_prompt(input_text, customer_info, template_sections, company_info)
        
        # Call Claude API
        result = self.claude.send_message(
            prompt=prompt,
            system_prompt=self._get_template_system_prompt(template_sections),
            service_type="proposal_generation"
        )
        
        generation_time = time.time() - start_time
        
        # Check for errors
        if not result.success:
            return {
                'error': result.message or 'AI yanıt vermedi',
                'generation_time': generation_time
            }
        
        response = result.data.get('content', '') if result.data else ''
        
        # Parse response
        try:
            proposal_data = self._parse_response(response)
            proposal_data['generation_time'] = generation_time
            proposal_data['ai_model'] = getattr(settings, 'AI_MODEL', 'claude')
            proposal_data['success'] = True
            return proposal_data
        except Exception as e:
            return {
                'error': str(e),
                'raw_response': response,
                'generation_time': generation_time
            }
    
    def _get_template_system_prompt(self, template_sections: List[Dict[str, Any]]) -> str:
        """Template bazlı sistem promptu oluştur."""
        
        sections_description = ""
        if template_sections:
            sections_description = "\n\nOluşturman gereken bölümler:\n"
            for i, section in enumerate(template_sections, 1):
                sections_description += f"\n{i}. {section['title']} ({section['field_type']})\n"
                sections_description += f"   Talimat: {section['description']}\n"
                if section.get('placeholder'):
                    sections_description += f"   Örnek içerik tarzı: {section['placeholder'][:200]}...\n"
        
        return f"""Sen profesyonel bir leasing teklif uzmanısın. Türkçe olarak profesyonel ve ikna edici teklifler oluşturuyorsun.

Görevin:
1. Kullanıcının girdiği metinden ekipman bilgilerini çıkar
2. Verilen template bölümlerini doldur
3. Müşteriye özel hitap et
4. İkna edici ve profesyonel bir dil kullan
5. Her bölüm için detaylı ve anlamlı içerik üret
{sections_description}

Yanıtını SADECE aşağıdaki JSON formatında ver, başka hiçbir şey ekleme:
{{
    "title": "Teklif başlığı",
    "summary": "Kısa özet (2-3 cümle)",
    "equipment_details": [
        {{
            "name": "Ekipman adı",
            "brand": "Marka",
            "model": "Model",
            "quantity": 1,
            "estimated_value": 0
        }}
    ],
    "equipment_value": 0,
    "monthly_payment": 0,
    "sections": [
        {{
            "type": "section_type",
            "title": "Bölüm Başlığı",
            "content": "Detaylı bölüm içeriği..."
        }}
    ],
    "suggested_terms": {{
        "lease_term_months": 36,
        "suggested_down_payment_percent": 10
    }}
}}"""
    
    def _build_template_prompt(
        self,
        input_text: str,
        customer_info: Dict[str, Any],
        template_sections: List[Dict[str, Any]],
        company_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Template bazlı teklif oluşturma promptu."""
        
        customer_name = customer_info.get('company_name') or \
                       f"{customer_info.get('first_name', '')} {customer_info.get('last_name', '')}".strip()
        
        prompt = f"""Müşteri Bilgileri:
- Firma/Ad: {customer_name}
- Sektör: {customer_info.get('industry', 'Belirtilmemiş')}
- İletişim: {customer_info.get('email', '')}

Kullanıcının Teklif Talebi:
{input_text}

"""
        
        if template_sections:
            prompt += "\nDoldurulması Gereken Bölümler:\n"
            for section in template_sections:
                prompt += f"\n### {section['title']}\n"
                prompt += f"Talimat: {section['description']}\n"
        
        prompt += "\n\nBu bilgiler doğrultusunda profesyonel bir leasing teklifi oluştur. Her bölümü detaylı şekilde doldur."

        if company_info:
            prompt += f"""

Şirket Bilgileri:
- Şirket Adı: {company_info.get('name', 'Leasing Şirketi')}
- Telefon: {company_info.get('phone', '')}
- Email: {company_info.get('email', '')}"""
        
        return prompt
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """AI yanıtını parse et."""
        # Try to extract JSON from response
        try:
            # Find JSON in response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # If JSON parsing fails, create structured response from text
        return {
            'title': 'Leasing Teklifi',
            'summary': response[:500] if len(response) > 500 else response,
            'equipment_details': [],
            'sections': [
                {
                    'type': 'custom',
                    'title': 'Teklif İçeriği',
                    'content': response
                }
            ],
            'suggested_terms': {
                'lease_term_months': 36,
                'suggested_down_payment_percent': 10
            }
        }
    
    def extract_equipment(self, text: str) -> List[Dict[str, Any]]:
        """
        Metinden ekipman bilgilerini çıkar.
        
        Args:
            text: Analiz edilecek metin
            
        Returns:
            Ekipman listesi
        """
        prompt = f"""Aşağıdaki metinden ekipman bilgilerini çıkar ve JSON formatında döndür.

Metin:
{text}

Yanıtını SADECE aşağıdaki JSON formatında ver:
{{
    "equipment": [
        {{
            "name": "Ekipman adı",
            "brand": "Marka (varsa)",
            "model": "Model (varsa)",
            "quantity": 1,
            "estimated_value": 0,
            "category": "Kategori (örn: İş Makinesi, Araç, Medikal, IT vb.)"
        }}
    ]
}}"""
        
        system_prompt = "Sen bir ekipman analiz uzmanısın. Metinlerden ekipman bilgilerini doğru şekilde çıkarırsın."
        
        response = self.claude.call_api(prompt=prompt, system_prompt=system_prompt)
        
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                return data.get('equipment', [])
        except (json.JSONDecodeError, KeyError):
            pass
        
        return []
    
    def regenerate_section(
        self,
        section_type: str,
        current_content: str,
        feedback: str,
        proposal_context: Dict[str, Any]
    ) -> str:
        """
        Belirli bir bölümü yeniden oluştur.
        
        Args:
            section_type: Bölüm tipi
            current_content: Mevcut içerik
            feedback: Kullanıcı geri bildirimi
            proposal_context: Teklif bağlamı
            
        Returns:
            Yeniden oluşturulan içerik
        """
        prompt = f"""Aşağıdaki teklif bölümünü kullanıcının geri bildirimine göre yeniden yaz.

Bölüm Tipi: {section_type}
Mevcut İçerik:
{current_content}

Kullanıcı Geri Bildirimi:
{feedback}

Teklif Bağlamı:
- Müşteri: {proposal_context.get('customer_name', '')}
- Ekipman: {proposal_context.get('equipment_summary', '')}

Sadece yeni bölüm içeriğini yaz, başka açıklama ekleme."""
        
        return self.claude.call_api(
            prompt=prompt,
            system_prompt="Sen profesyonel bir teklif yazarısın. İkna edici ve profesyonel içerikler oluşturursun."
        )



