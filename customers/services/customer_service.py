"""
Customer service.
Business logic for customer management.
"""

import secrets
import string
import logging
from django.db.models import Count, Q
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from ..models import Customer, CustomerStage, CustomerNote
from core.utils.email import email_service

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomerService:
    """
    Müşteri işlemleri için servis sınıfı.
    """
    
    @staticmethod
    def get_customers_for_salesperson(user, filters=None):
        """
        Satış elemanının müşterilerini getir.
        
        Args:
            user: Satış elemanı kullanıcısı
            filters: Opsiyonel filtreler (stage, priority, search)
        """
        queryset = Customer.objects.filter(
            salesperson=user,
            is_active=True
        ).select_related('salesperson', 'company')
        
        if filters:
            if stage := filters.get('stage'):
                queryset = queryset.filter(stage=stage)
            if priority := filters.get('priority'):
                queryset = queryset.filter(priority=priority)
            if search := filters.get('search'):
                queryset = queryset.filter(
                    Q(company_name__icontains=search) |
                    Q(company__name__icontains=search) |
                    Q(contact_person__icontains=search) |
                    Q(email__icontains=search)
                )
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def get_stage_summary(user):
        """
        Satış elemanının müşterilerinin aşama özeti.
        
        Returns:
            Dict with stage counts
        """
        customers = Customer.objects.filter(
            salesperson=user,
            is_active=True
        )
        
        summary = {
            'total': customers.count(),
            'stages': {}
        }
        
        for stage in CustomerStage.choices:
            count = customers.filter(stage=stage[0]).count()
            summary['stages'][stage[0]] = {
                'label': stage[1],
                'count': count,
            }
        
        return summary
    
    @staticmethod
    def get_dashboard_stats(user):
        """
        Dashboard istatistikleri.
        
        Args:
            user: Satış elemanı kullanıcısı
            
        Returns:
            Dict with various stats
        """
        customers = Customer.objects.filter(
            salesperson=user,
            is_active=True
        )
        
        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        stats = {
            'total_customers': customers.count(),
            'new_this_month': customers.filter(created_at__gte=this_month_start).count(),
            'pending_followup': customers.filter(
                next_followup_date__lte=now.date()
            ).count(),
            'by_stage': {},
            'by_priority': {},
        }
        
        # Stage breakdown
        for stage in CustomerStage.choices:
            stats['by_stage'][stage[0]] = customers.filter(stage=stage[0]).count()
        
        return stats
    
    @staticmethod
    def get_customers_needing_followup(user, days=7):
        """
        Takip edilmesi gereken müşteriler.
        
        Args:
            user: Satış elemanı
            days: Kaç gün içinde takip edilmeli
            
        Returns:
            QuerySet of customers
        """
        threshold_date = timezone.now().date() + timedelta(days=days)
        
        return Customer.objects.filter(
            salesperson=user,
            is_active=True,
            next_followup_date__lte=threshold_date
        ).exclude(
            stage__in=[CustomerStage.WON, CustomerStage.LOST]
        ).order_by('next_followup_date')
    
    @staticmethod
    def update_stage(customer, new_stage, user, note=None):
        """
        Müşteri aşamasını güncelle ve not ekle.
        
        Args:
            customer: Customer instance
            new_stage: New CustomerStage
            user: User making the change
            note: Optional note
        """
        old_stage = customer.stage
        customer.stage = new_stage
        customer.save()
        
        # Create activity note
        content = f"Aşama değişikliği: {CustomerStage(old_stage).label} → {CustomerStage(new_stage).label}"
        if note:
            content += f"\n{note}"
        
        CustomerNote.objects.create(
            customer=customer,
            note_type=CustomerNote.NoteType.STATUS_CHANGE,
            content=content,
            created_by=user
        )
        
        return customer
    
    @staticmethod
    def add_note(customer, note_type, content, user):
        """
        Müşteriye not ekle.
        
        Args:
            customer: Customer instance
            note_type: CustomerNote.NoteType
            content: Note content
            user: User creating the note
        """
        note = CustomerNote.objects.create(
            customer=customer,
            note_type=note_type,
            content=content,
            created_by=user
        )
        
        # Update last contact date
        customer.last_contact_date = timezone.now()
        customer.save(update_fields=['last_contact_date'])
        
        return note
    
    @staticmethod
    def get_recent_activities(user, limit=10):
        """
        Son aktiviteler.
        
        Args:
            user: Satış elemanı
            limit: Maksimum kayıt sayısı
        """
        return CustomerNote.objects.filter(
            customer__salesperson=user
        ).select_related('customer', 'created_by').order_by('-created_at')[:limit]
    
    @staticmethod
    def generate_password(length=12):
        """
        Güvenli rastgele şifre oluştur.
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_username_from_email(email):
        """
        Email adresinden kullanıcı adı oluştur.
        """
        base_username = email.split('@')[0].lower()
        # Geçersiz karakterleri temizle
        base_username = ''.join(c for c in base_username if c.isalnum() or c in '_-.')
        
        # Eğer kullanıcı adı zaten varsa, numara ekle
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    @classmethod
    @transaction.atomic
    def create_customer_with_user(cls, salesperson, customer_data, send_email=True):
        """
        Müşteri oluştur ve otomatik kullanıcı hesabı aç.
        
        Args:
            salesperson: Satış elemanı (oluşturan)
            customer_data: Müşteri verileri dict
            send_email: Hoşgeldin emaili gönderilsin mi
            
        Returns:
            tuple: (customer, user, password)
        """
        email = customer_data.get('email')
        contact_person = customer_data.get('contact_person', '')
        
        # Kullanıcı adı ve şifre oluştur
        username = cls.generate_username_from_email(email)
        password = cls.generate_password()
        
        # İsim ve soyismi ayır
        name_parts = contact_person.split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Kullanıcı hesabı oluştur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            user_type='customer',
            is_active=True,  # Aktif olarak oluştur
            phone=customer_data.get('phone', ''),
        )
        
        logger.info(f"User account created for customer: {email} (username: {username})")
        
        # Müşteri kaydı oluştur
        company = customer_data.get('company')
        company_name = customer_data.get('company_name', '')
        
        # If company object provided, use its name
        if company:
            company_name = company.name
        
        customer = Customer.objects.create(
            salesperson=salesperson,
            user_account=user,
            company=company,
            company_name=company_name,
            contact_person=contact_person,
            email=email,
            phone=customer_data.get('phone', ''),
            secondary_phone=customer_data.get('secondary_phone', ''),
            address=customer_data.get('address', ''),
            city=customer_data.get('city', ''),
            tax_number=customer_data.get('tax_number', ''),
            tax_office=customer_data.get('tax_office', ''),
            sector=customer_data.get('sector', ''),
            company_size=customer_data.get('company_size', ''),
            stage=customer_data.get('stage', CustomerStage.LEAD),
            priority=customer_data.get('priority', 'medium'),
            estimated_value=customer_data.get('estimated_value', 0),
            next_followup_date=customer_data.get('next_followup_date'),
            notes=customer_data.get('notes', ''),
        )
        
        logger.info(f"Customer created: {customer.display_company_name} (ID: {customer.pk})")
        
        # Hoşgeldin emaili gönder
        if send_email:
            try:
                email_service.send_welcome_email(user, password)
                logger.info(f"Welcome email sent to: {email}")
                
                # Aktivite notu ekle
                CustomerNote.objects.create(
                    customer=customer,
                    note_type=CustomerNote.NoteType.NOTE,
                    content=f"Müşteri hesabı oluşturuldu. Kullanıcı adı: {username}. Hoşgeldin emaili gönderildi.",
                    created_by=salesperson
                )
            except Exception as e:
                logger.error(f"Failed to send welcome email to {email}: {e}")
                # Email gönderilemese bile müşteriyi oluştur
                CustomerNote.objects.create(
                    customer=customer,
                    note_type=CustomerNote.NoteType.NOTE,
                    content=f"Müşteri hesabı oluşturuldu. Kullanıcı adı: {username}. Email gönderilemedi!",
                    created_by=salesperson
                )
        
        return customer, user, password
    
    @staticmethod
    def resend_welcome_email(customer):
        """
        Müşteriye hoşgeldin emailini tekrar gönder (yeni şifre ile).
        
        Args:
            customer: Customer instance
            
        Returns:
            tuple: (success, new_password)
        """
        if not customer.user_account:
            logger.warning(f"Customer {customer.pk} has no user account")
            return False, None
        
        user = customer.user_account
        new_password = CustomerService.generate_password()
        user.set_password(new_password)
        user.save()
        
        try:
            email_service.send_welcome_email(user, new_password)
            logger.info(f"Welcome email resent to: {user.email}")
            return True, new_password
        except Exception as e:
            logger.error(f"Failed to resend welcome email: {e}")
            return False, new_password

