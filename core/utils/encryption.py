"""
Encryption utilities for sensitive data.
KVKK compliance for data protection.
"""

import base64
import hashlib
import hmac
import os
from typing import Optional, Union
from django.conf import settings


class EncryptionService:
    """
    Hassas veri şifreleme servisi.
    KVKK uyumluluğu için veri koruma.
    """
    
    def __init__(self):
        self.key = self._get_or_create_key()
    
    def _get_or_create_key(self) -> bytes:
        """Şifreleme anahtarını al veya oluştur."""
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if key:
            return key.encode() if isinstance(key, str) else key
        
        # Fallback to secret key hash
        secret = settings.SECRET_KEY.encode()
        return hashlib.sha256(secret).digest()
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """
        Veriyi şifrele.
        
        Args:
            data: Şifrelenecek veri
            
        Returns:
            Base64 encoded şifreli veri
        """
        try:
            from cryptography.fernet import Fernet
            
            # Derive key
            key = base64.urlsafe_b64encode(self.key[:32])
            fernet = Fernet(key)
            
            if isinstance(data, str):
                data = data.encode()
            
            encrypted = fernet.encrypt(data)
            return base64.urlsafe_b64encode(encrypted).decode()
            
        except ImportError:
            # Fallback: Simple XOR with base64 (less secure but works without cryptography)
            return self._simple_encrypt(data)
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Şifreli veriyi çöz.
        
        Args:
            encrypted_data: Base64 encoded şifreli veri
            
        Returns:
            Çözülmüş veri
        """
        try:
            from cryptography.fernet import Fernet
            
            key = base64.urlsafe_b64encode(self.key[:32])
            fernet = Fernet(key)
            
            encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = fernet.decrypt(encrypted)
            return decrypted.decode()
            
        except ImportError:
            return self._simple_decrypt(encrypted_data)
    
    def _simple_encrypt(self, data: Union[str, bytes]) -> str:
        """Basit XOR şifreleme (fallback)."""
        if isinstance(data, str):
            data = data.encode()
        
        key_bytes = self.key * (len(data) // len(self.key) + 1)
        encrypted = bytes(a ^ b for a, b in zip(data, key_bytes[:len(data)]))
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def _simple_decrypt(self, encrypted_data: str) -> str:
        """Basit XOR şifre çözme (fallback)."""
        encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
        key_bytes = self.key * (len(encrypted) // len(self.key) + 1)
        decrypted = bytes(a ^ b for a, b in zip(encrypted, key_bytes[:len(encrypted)]))
        return decrypted.decode()
    
    def hash_sensitive_data(self, data: str) -> str:
        """
        Hassas veriyi hash'le (geri dönüşümsüz).
        Şifre saklama için kullanılabilir.
        
        Args:
            data: Hash'lenecek veri
            
        Returns:
            Hash değeri
        """
        salt = self.key[:16]
        return hashlib.pbkdf2_hmac(
            'sha256',
            data.encode(),
            salt,
            100000
        ).hex()
    
    def verify_hash(self, data: str, hash_value: str) -> bool:
        """
        Hash değerini doğrula.
        
        Args:
            data: Kontrol edilecek veri
            hash_value: Beklenen hash değeri
            
        Returns:
            Eşleşme durumu
        """
        return hmac.compare_digest(self.hash_sensitive_data(data), hash_value)
    
    def mask_sensitive_data(self, data: str, visible_chars: int = 4) -> str:
        """
        Hassas veriyi maskele (görüntüleme için).
        
        Args:
            data: Maskelenecek veri
            visible_chars: Görünür karakter sayısı
            
        Returns:
            Maskelenmiş veri
        """
        if len(data) <= visible_chars * 2:
            return '*' * len(data)
        
        return data[:visible_chars] + '*' * (len(data) - visible_chars * 2) + data[-visible_chars:]
    
    def mask_email(self, email: str) -> str:
        """
        Email adresini maskele.
        
        Args:
            email: Email adresi
            
        Returns:
            Maskelenmiş email
        """
        if '@' not in email:
            return self.mask_sensitive_data(email)
        
        local, domain = email.split('@', 1)
        
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    def mask_tc_kimlik(self, tc: str) -> str:
        """
        TC Kimlik numarasını maskele.
        
        Args:
            tc: TC Kimlik numarası
            
        Returns:
            Maskelenmiş TC
        """
        if len(tc) != 11:
            return '*' * len(tc)
        
        return tc[:3] + '*' * 5 + tc[-3:]
    
    def mask_phone(self, phone: str) -> str:
        """
        Telefon numarasını maskele.
        
        Args:
            phone: Telefon numarası
            
        Returns:
            Maskelenmiş telefon
        """
        # Remove non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        if len(digits) <= 4:
            return '*' * len(digits)
        
        return digits[:3] + '*' * (len(digits) - 5) + digits[-2:]


class KVKKCompliance:
    """
    KVKK uyumluluk yardımcı sınıfı.
    """
    
    @staticmethod
    def log_data_access(user, data_type: str, reason: str):
        """
        Veri erişimini logla.
        
        Args:
            user: Erişen kullanıcı
            data_type: Erişilen veri tipi
            reason: Erişim sebebi
        """
        from core.models import ActivityLog
        
        ActivityLog.objects.create(
            user=user,
            action_type='view',
            model_name='KVKK_DataAccess',
            description=f"Veri erişimi: {data_type} - {reason}",
            extra_data={
                'data_type': data_type,
                'reason': reason,
                'kvkk_audit': True
            }
        )
    
    @staticmethod
    def export_user_data(user) -> dict:
        """
        Kullanıcının tüm verilerini dışa aktar (KVKK hakkı).
        
        Args:
            user: Kullanıcı
            
        Returns:
            Kullanıcı verileri
        """
        data = {
            'user_info': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'date_joined': str(user.date_joined),
                'last_login': str(user.last_login) if user.last_login else None,
            },
            'activity_logs': [],
            'notifications': [],
        }
        
        # Activity logs
        from core.models import ActivityLog, Notification
        
        for log in ActivityLog.objects.filter(user=user)[:100]:
            data['activity_logs'].append({
                'action': log.action_type,
                'description': log.description,
                'date': str(log.created_at)
            })
        
        # Notifications
        for notif in Notification.objects.filter(user=user)[:50]:
            data['notifications'].append({
                'title': notif.title,
                'message': notif.message,
                'date': str(notif.created_at),
                'read': notif.is_read
            })
        
        # Customer data if exists
        if hasattr(user, 'customer_profile') and user.customer_profile:
            customer = user.customer_profile
            data['customer_info'] = {
                'company_name': customer.company_name,
                'tax_number': EncryptionService().mask_sensitive_data(customer.tax_number) if customer.tax_number else None,
                'phone': EncryptionService().mask_phone(customer.phone) if customer.phone else None,
            }
        
        return data
    
    @staticmethod
    def anonymize_user_data(user):
        """
        Kullanıcı verilerini anonimleştir (KVKK hakkı - unutulma).
        
        Args:
            user: Kullanıcı
        """
        import uuid
        from django.utils import timezone
        
        # Anonymize user
        random_suffix = uuid.uuid4().hex[:8]
        user.email = f"anonymized_{random_suffix}@deleted.local"
        user.first_name = "Anonim"
        user.last_name = "Kullanıcı"
        user.phone = None
        user.is_active = False
        user.save()
        
        # Anonymize related customer if exists
        if hasattr(user, 'customer_profile') and user.customer_profile:
            customer = user.customer_profile
            customer.email = user.email
            customer.first_name = "Anonim"
            customer.last_name = "Müşteri"
            customer.phone = None
            customer.address = None
            customer.tax_number = None
            customer.is_active = False
            customer.save()
        
        # Log the anonymization
        from core.models import ActivityLog
        ActivityLog.objects.create(
            user=None,  # Don't link to user
            action_type='delete',
            model_name='KVKK_Anonymization',
            description=f"Kullanıcı anonimleştirildi: {random_suffix}",
            extra_data={
                'anonymized_id': random_suffix,
                'timestamp': str(timezone.now()),
                'kvkk_audit': True
            }
        )



