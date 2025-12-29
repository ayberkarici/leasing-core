"""
AI Document Validator Service.
Uses Claude API to validate uploaded documents.
"""

import json
from typing import Dict, List, Any, Optional
from django.conf import settings
from .claude import ClaudeService


class DocumentValidator:
    """
    AI destekli belge validatörü.
    Belgelerdeki eksik/hatalı alanları tespit eder.
    """
    
    # Document field requirements by type
    DOCUMENT_REQUIREMENTS = {
        'identity': {
            'name': 'Kimlik Belgesi',
            'required_fields': [
                {'field': 'tc_kimlik_no', 'label': 'TC Kimlik No', 'pattern': r'\d{11}'},
                {'field': 'ad_soyad', 'label': 'Ad Soyad'},
                {'field': 'dogum_tarihi', 'label': 'Doğum Tarihi'},
                {'field': 'gecerlilik_tarihi', 'label': 'Geçerlilik Tarihi'},
            ]
        },
        'tax_certificate': {
            'name': 'Vergi Levhası',
            'required_fields': [
                {'field': 'vergi_no', 'label': 'Vergi No', 'pattern': r'\d{10}'},
                {'field': 'unvan', 'label': 'Ünvan'},
                {'field': 'vergi_dairesi', 'label': 'Vergi Dairesi'},
                {'field': 'yil', 'label': 'Yıl'},
            ]
        },
        'signature_circular': {
            'name': 'İmza Sirküleri',
            'required_fields': [
                {'field': 'sirket_unvani', 'label': 'Şirket Ünvanı'},
                {'field': 'yetkili_adi', 'label': 'Yetkili Adı'},
                {'field': 'imza', 'label': 'İmza', 'is_signature': True},
                {'field': 'noter_onayi', 'label': 'Noter Onayı'},
                {'field': 'tarih', 'label': 'Tarih'},
            ]
        },
        'trade_registry': {
            'name': 'Ticaret Sicil Gazetesi',
            'required_fields': [
                {'field': 'sirket_unvani', 'label': 'Şirket Ünvanı'},
                {'field': 'sicil_no', 'label': 'Sicil No'},
                {'field': 'sermaye', 'label': 'Sermaye'},
                {'field': 'ortaklar', 'label': 'Ortaklar'},
                {'field': 'tarih', 'label': 'Tarih'},
            ]
        },
        'financial_statement': {
            'name': 'Mali Tablo',
            'required_fields': [
                {'field': 'sirket_unvani', 'label': 'Şirket Ünvanı'},
                {'field': 'donem', 'label': 'Dönem'},
                {'field': 'aktif_toplam', 'label': 'Aktif Toplamı'},
                {'field': 'pasif_toplam', 'label': 'Pasif Toplamı'},
                {'field': 'ciro', 'label': 'Ciro'},
                {'field': 'imza', 'label': 'İmza/Kaşe', 'is_signature': True},
            ]
        },
        'kvkk_consent': {
            'name': 'KVKK Onay Belgesi',
            'required_fields': [
                {'field': 'ad_soyad', 'label': 'Ad Soyad'},
                {'field': 'tc_kimlik_no', 'label': 'TC Kimlik No'},
                {'field': 'tarih', 'label': 'Tarih'},
                {'field': 'imza', 'label': 'İmza', 'is_signature': True},
            ]
        },
        'contract': {
            'name': 'Sözleşme',
            'required_fields': [
                {'field': 'taraflar', 'label': 'Taraflar'},
                {'field': 'konu', 'label': 'Sözleşme Konusu'},
                {'field': 'tutar', 'label': 'Tutar'},
                {'field': 'tarih', 'label': 'Tarih'},
                {'field': 'imza_1', 'label': 'Taraf 1 İmza', 'is_signature': True},
                {'field': 'imza_2', 'label': 'Taraf 2 İmza', 'is_signature': True},
            ]
        },
    }
    
    def __init__(self):
        self.claude = ClaudeService()
    
    def validate_document(
        self,
        document_text: str,
        document_type: str,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Belgeyi validate et.
        
        Args:
            document_text: Belgeden çıkarılan metin
            document_type: Belge tipi
            additional_context: Ek bağlam bilgisi
            
        Returns:
            Validation sonuçları
        """
        requirements = self.DOCUMENT_REQUIREMENTS.get(document_type, {})
        required_fields = requirements.get('required_fields', [])
        
        if not required_fields:
            # Generic validation
            return self._validate_generic(document_text)
        
        prompt = self._build_validation_prompt(
            document_text,
            requirements,
            additional_context
        )
        
        response = self.claude.call_api(
            prompt=prompt,
            system_prompt=self._get_system_prompt()
        )
        
        return self._parse_validation_response(response, required_fields)
    
    def _get_system_prompt(self) -> str:
        """AI sistem promptu."""
        return """Sen bir belge validasyon uzmanısın. Türkçe belgeleri analiz ediyorsun.

Görevin:
1. Belgede gerekli alanların bulunup bulunmadığını kontrol et
2. Bulunan alanların değerlerini çıkar
3. Eksik veya okunamayan alanları belirle
4. Her alan için güven skoru (0-100) ver

Yanıtını SADECE aşağıdaki JSON formatında ver:
{
    "is_valid": true/false,
    "overall_score": 0-100,
    "fields": [
        {
            "field_id": "alan_adi",
            "found": true/false,
            "value": "bulunan değer veya null",
            "confidence": 0-100,
            "issue": "sorun varsa açıklama"
        }
    ],
    "warnings": ["uyarı mesajları"],
    "errors": ["hata mesajları"],
    "recommendations": ["öneriler"]
}"""
    
    def _build_validation_prompt(
        self,
        document_text: str,
        requirements: Dict,
        additional_context: Optional[str]
    ) -> str:
        """Validasyon promptu oluştur."""
        fields_list = "\n".join([
            f"- {f['label']} ({f['field']})" + 
            (f" [Pattern: {f.get('pattern', '')}]" if f.get('pattern') else "") +
            (" [İMZA GEREKLİ]" if f.get('is_signature') else "")
            for f in requirements.get('required_fields', [])
        ])
        
        prompt = f"""Belge Tipi: {requirements.get('name', 'Belge')}

Kontrol Edilecek Alanlar:
{fields_list}

Belge İçeriği:
---
{document_text[:5000]}  # Limit text length
---

Bu belgeyi analiz et ve her alanın durumunu raporla."""

        if additional_context:
            prompt += f"\n\nEk Bilgi:\n{additional_context}"
        
        return prompt
    
    def _parse_validation_response(
        self,
        response: str,
        required_fields: List[Dict]
    ) -> Dict[str, Any]:
        """AI yanıtını parse et."""
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Ensure required structure
                result.setdefault('is_valid', False)
                result.setdefault('overall_score', 0)
                result.setdefault('fields', [])
                result.setdefault('warnings', [])
                result.setdefault('errors', [])
                result.setdefault('recommendations', [])
                
                return result
                
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Fallback
        return {
            'is_valid': False,
            'overall_score': 0,
            'fields': [
                {'field_id': f['field'], 'found': False, 'value': None, 'confidence': 0}
                for f in required_fields
            ],
            'warnings': [],
            'errors': ['Belge analizi başarısız oldu.'],
            'recommendations': ['Belgeyi tekrar yükleyin veya daha net bir kopya deneyin.']
        }
    
    def _validate_generic(self, document_text: str) -> Dict[str, Any]:
        """Genel belge validasyonu."""
        prompt = f"""Aşağıdaki belgeyi analiz et ve genel bir değerlendirme yap:

{document_text[:3000]}

Şunları değerlendir:
1. Belgenin okunabilirliği
2. Resmi bir belge gibi görünüp görünmediği
3. İmza/kaşe varlığı
4. Tarih bilgisi

JSON formatında yanıt ver:
{{
    "is_valid": true/false,
    "overall_score": 0-100,
    "document_type_guess": "tahmin edilen belge tipi",
    "has_signature": true/false,
    "has_date": true/false,
    "readability": "good/medium/poor",
    "warnings": [],
    "recommendations": []
}}"""
        
        response = self.claude.call_api(
            prompt=prompt,
            system_prompt="Sen bir belge analiz uzmanısın."
        )
        
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                return json.loads(response[start_idx:end_idx])
        except (json.JSONDecodeError, ValueError):
            pass
        
        return {
            'is_valid': False,
            'overall_score': 0,
            'warnings': ['Belge analizi yapılamadı'],
            'recommendations': ['Manuel inceleme gerekli']
        }
    
    def get_completion_percentage(self, validation_result: Dict) -> float:
        """
        Belge tamamlanma yüzdesini hesapla.
        
        Args:
            validation_result: Validation sonucu
            
        Returns:
            Completion percentage (0-100)
        """
        fields = validation_result.get('fields', [])
        if not fields:
            return validation_result.get('overall_score', 0)
        
        found_count = sum(1 for f in fields if f.get('found', False))
        total_count = len(fields)
        
        return (found_count / total_count * 100) if total_count > 0 else 0
    
    def get_missing_fields(self, validation_result: Dict) -> List[Dict]:
        """
        Eksik alanları getir.
        
        Args:
            validation_result: Validation sonucu
            
        Returns:
            List of missing fields
        """
        return [
            f for f in validation_result.get('fields', [])
            if not f.get('found', False)
        ]
    
    def compare_with_customer_data(
        self,
        validation_result: Dict,
        customer_data: Dict
    ) -> Dict[str, Any]:
        """
        Validasyon sonuçlarını müşteri verileriyle karşılaştır.
        
        Args:
            validation_result: AI validation sonucu
            customer_data: Müşteri verileri
            
        Returns:
            Karşılaştırma sonuçları
        """
        mismatches = []
        matches = []
        
        for field in validation_result.get('fields', []):
            field_id = field.get('field_id')
            found_value = field.get('value')
            
            if field_id and found_value:
                expected_value = customer_data.get(field_id)
                
                if expected_value:
                    if str(found_value).lower().strip() == str(expected_value).lower().strip():
                        matches.append({
                            'field': field_id,
                            'value': found_value
                        })
                    else:
                        mismatches.append({
                            'field': field_id,
                            'found': found_value,
                            'expected': expected_value
                        })
        
        return {
            'matches': matches,
            'mismatches': mismatches,
            'match_rate': len(matches) / (len(matches) + len(mismatches)) * 100 if (matches or mismatches) else 100
        }



