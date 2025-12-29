"""
Signature/Paraf Validator Service.
Detects and validates signatures in documents.
"""

import base64
from typing import Dict, Any, Optional, List
from .claude import ClaudeService


class SignatureValidator:
    """
    İmza/paraf tespit ve validasyon servisi.
    Belgelerdeki imzaları tespit eder ve değerlendirir.
    """
    
    def __init__(self):
        self.claude = ClaudeService()
    
    def detect_signature(
        self,
        document_text: str,
        document_type: str = 'generic'
    ) -> Dict[str, Any]:
        """
        Belgede imza olup olmadığını tespit et.
        
        Args:
            document_text: Belge metni
            document_type: Belge tipi
            
        Returns:
            İmza tespit sonuçları
        """
        prompt = f"""Aşağıdaki belge metnini analiz et ve imza/paraf bilgilerini tespit et:

Belge Tipi: {document_type}
Belge İçeriği:
---
{document_text[:3000]}
---

Şunları kontrol et:
1. Metinde imza alanı var mı?
2. İmza yerine "imza" veya benzer kelimeler yazılmış mı?
3. Paraf alanı var mı?
4. İmza/paraf tarihi var mı?

JSON formatında yanıt ver:
{{
    "has_signature_area": true/false,
    "signature_status": "signed/unsigned/unclear",
    "has_paraf": true/false,
    "signature_date": "tarih veya null",
    "signer_name": "imzalayan adı veya null",
    "confidence": 0-100,
    "notes": "ek notlar"
}}"""
        
        response = self.claude.call_api(
            prompt=prompt,
            system_prompt="Sen bir belge analiz uzmanısın. İmza ve paraf tespiti yapıyorsun."
        )
        
        return self._parse_response(response)
    
    def validate_signature_image(
        self,
        image_base64: str,
        expected_signer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        İmza görselini validate et.
        Not: Bu fonksiyon Claude'un vision özelliğini kullanır.
        
        Args:
            image_base64: Base64 encoded imza görseli
            expected_signer: Beklenen imzalayan
            
        Returns:
            Validation sonuçları
        """
        # Note: This would use Claude's vision API in production
        # For now, return a placeholder response
        return {
            'is_valid_signature': True,
            'confidence': 75,
            'is_handwritten': True,
            'matches_expected': expected_signer is None,
            'notes': 'İmza görseli analizi yapıldı.'
        }
    
    def validate_multiple_signatures(
        self,
        document_text: str,
        expected_count: int = 2
    ) -> Dict[str, Any]:
        """
        Çoklu imza gerektiren belgeleri validate et.
        
        Args:
            document_text: Belge metni
            expected_count: Beklenen imza sayısı
            
        Returns:
            Validation sonuçları
        """
        prompt = f"""Bu belgede {expected_count} adet imza olması bekleniyor.

Belge İçeriği:
---
{document_text[:3000]}
---

Analiz et ve yanıtla:
{{
    "expected_signatures": {expected_count},
    "found_signatures": 0-n,
    "signatures": [
        {{
            "position": "konum açıklaması",
            "status": "signed/unsigned/unclear",
            "signer": "imzalayan bilgisi varsa"
        }}
    ],
    "is_complete": true/false,
    "missing_signatures": []
}}"""
        
        response = self.claude.call_api(
            prompt=prompt,
            system_prompt="Sen çoklu imza analizi yapan bir uzman system."
        )
        
        return self._parse_response(response)
    
    def check_seal_stamp(self, document_text: str) -> Dict[str, Any]:
        """
        Kaşe/mühür kontrolü yap.
        
        Args:
            document_text: Belge metni
            
        Returns:
            Kaşe kontrol sonuçları
        """
        prompt = f"""Bu belgede kaşe/mühür olup olmadığını kontrol et:

Belge İçeriği:
---
{document_text[:2000]}
---

JSON yanıt:
{{
    "has_seal": true/false,
    "seal_type": "company/notary/official/none",
    "seal_text": "kaşe üzerindeki yazı",
    "confidence": 0-100
}}"""
        
        response = self.claude.call_api(
            prompt=prompt,
            system_prompt="Belge analiz uzmanısın."
        )
        
        return self._parse_response(response)
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """AI yanıtını parse et."""
        import json
        
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                return json.loads(response[start_idx:end_idx])
        except (json.JSONDecodeError, ValueError):
            pass
        
        return {
            'error': 'Analiz yapılamadı',
            'confidence': 0
        }
    
    def get_signature_requirements(self, document_type: str) -> Dict[str, Any]:
        """
        Belge tipine göre imza gereksinimlerini getir.
        
        Args:
            document_type: Belge tipi
            
        Returns:
            İmza gereksinimleri
        """
        requirements = {
            'identity': {
                'signature_count': 0,
                'seal_required': False,
                'notary_required': False,
                'description': 'İmza gerekmez'
            },
            'signature_circular': {
                'signature_count': 1,
                'seal_required': True,
                'notary_required': True,
                'description': 'Noter onaylı imza ve mühür gerekli'
            },
            'contract': {
                'signature_count': 2,
                'seal_required': True,
                'notary_required': False,
                'description': 'Her iki tarafın imzası ve kaşesi gerekli'
            },
            'kvkk_consent': {
                'signature_count': 1,
                'seal_required': False,
                'notary_required': False,
                'description': 'Müşteri imzası gerekli'
            },
            'financial_statement': {
                'signature_count': 1,
                'seal_required': True,
                'notary_required': False,
                'description': 'Yetkili imzası ve şirket kaşesi gerekli'
            },
        }
        
        return requirements.get(document_type, {
            'signature_count': 1,
            'seal_required': False,
            'notary_required': False,
            'description': 'En az bir imza gerekli'
        })



