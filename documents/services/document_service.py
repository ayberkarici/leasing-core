"""
Document service.
Business logic for document management.
"""

import os
import logging
from django.db import transaction
from django.utils import timezone
from ..models import (
    DocumentTemplate, UploadedDocument, KVKKDocument, 
    DocumentStatus, DocumentType
)

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Belge işlemleri için servis sınıfı.
    """
    
    @staticmethod
    def get_required_templates():
        """
        Aktif ve zorunlu belge şablonlarını getir.
        """
        return DocumentTemplate.objects.filter(
            is_active=True,
            is_required=True
        ).order_by('order')
    
    @staticmethod
    def get_all_templates():
        """
        Tüm aktif belge şablonlarını getir.
        """
        return DocumentTemplate.objects.filter(
            is_active=True
        ).order_by('order')
    
    @staticmethod
    def get_customer_documents(customer, document_type=None):
        """
        Müşterinin belgelerini getir.
        
        Args:
            customer: Customer instance
            document_type: Optional filter by document type
        """
        queryset = UploadedDocument.objects.filter(
            customer=customer
        ).select_related('template', 'uploaded_by', 'reviewed_by')
        
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        return queryset.order_by('-created_at')
    
    @staticmethod
    def get_order_documents(order):
        """
        Siparişin belgelerini getir.
        """
        return UploadedDocument.objects.filter(
            order=order
        ).select_related('template', 'uploaded_by').order_by('-created_at')
    
    @staticmethod
    @transaction.atomic
    def upload_document(file, customer, uploaded_by, document_type, 
                        title=None, order=None, template=None):
        """
        Belge yükle.
        
        Args:
            file: Uploaded file
            customer: Customer instance
            uploaded_by: User who uploaded
            document_type: DocumentType value
            title: Optional title (defaults to filename)
            order: Optional Order instance
            template: Optional DocumentTemplate instance
        
        Returns:
            UploadedDocument instance
        """
        # Get file info
        original_filename = file.name
        file_size = file.size
        
        # Detect MIME type
        mime_type = file.content_type if hasattr(file, 'content_type') else ''
        
        # Generate title if not provided
        if not title:
            title = os.path.splitext(original_filename)[0]
        
        # Create document record
        document = UploadedDocument.objects.create(
            customer=customer,
            order=order,
            template=template,
            uploaded_by=uploaded_by,
            document_type=document_type,
            title=title,
            file=file,
            original_filename=original_filename,
            file_size=file_size,
            mime_type=mime_type,
            status=DocumentStatus.UPLOADED
        )
        
        logger.info(f"Document uploaded: {document.title} for {customer.company_name}")
        
        return document
    
    @staticmethod
    def approve_document(document, user, notes=''):
        """
        Belgeyi onayla.
        """
        document.approve(user, notes)
        logger.info(f"Document approved: {document.title} by {user}")
        return document
    
    @staticmethod
    def reject_document(document, user, reason):
        """
        Belgeyi reddet.
        """
        document.reject(user, reason)
        logger.info(f"Document rejected: {document.title} by {user} - {reason}")
        return document
    
    @staticmethod
    def get_pending_documents(salesperson=None):
        """
        İnceleme bekleyen belgeleri getir.
        """
        queryset = UploadedDocument.objects.filter(
            status__in=[DocumentStatus.UPLOADED, DocumentStatus.REVIEWING]
        ).select_related('customer', 'order', 'uploaded_by')
        
        if salesperson:
            queryset = queryset.filter(customer__salesperson=salesperson)
        
        return queryset.order_by('created_at')
    
    @staticmethod
    def get_document_stats(customer=None, salesperson=None):
        """
        Belge istatistikleri.
        """
        queryset = UploadedDocument.objects.all()
        
        if customer:
            queryset = queryset.filter(customer=customer)
        elif salesperson:
            queryset = queryset.filter(customer__salesperson=salesperson)
        
        stats = {
            'total': queryset.count(),
            'pending': queryset.filter(status=DocumentStatus.UPLOADED).count(),
            'reviewing': queryset.filter(status=DocumentStatus.REVIEWING).count(),
            'approved': queryset.filter(status=DocumentStatus.APPROVED).count(),
            'rejected': queryset.filter(status=DocumentStatus.REJECTED).count(),
        }
        
        return stats
    
    # KVKK Methods
    
    @staticmethod
    def get_or_create_kvkk(customer):
        """
        Müşteri için KVKK kaydı getir veya oluştur.
        """
        kvkk, created = KVKKDocument.objects.get_or_create(
            customer=customer
        )
        return kvkk
    
    @staticmethod
    def send_kvkk_form(customer, sent_by):
        """
        KVKK formunu müşteriye gönder.
        """
        kvkk = DocumentService.get_or_create_kvkk(customer)
        kvkk.form_sent = True
        kvkk.form_sent_at = timezone.now()
        kvkk.form_sent_by = sent_by
        kvkk.save()
        
        # TODO: Send email notification to customer
        logger.info(f"KVKK form sent to {customer.company_name}")
        
        return kvkk
    
    @staticmethod
    def upload_signed_kvkk(customer, file, user):
        """
        İmzalı KVKK belgesini yükle.
        """
        kvkk = DocumentService.get_or_create_kvkk(customer)
        kvkk.signed_document = file
        kvkk.signed_at = timezone.now()
        kvkk.save()
        
        logger.info(f"Signed KVKK uploaded for {customer.company_name}")
        
        return kvkk
    
    @staticmethod
    def approve_kvkk(kvkk, approved_by):
        """
        KVKK belgesini onayla.
        """
        kvkk.is_approved = True
        kvkk.approved_by = approved_by
        kvkk.approved_at = timezone.now()
        kvkk.save()
        
        logger.info(f"KVKK approved for {kvkk.customer.company_name}")
        
        return kvkk
    
    @staticmethod
    def get_pending_kvkk(salesperson=None):
        """
        Onay bekleyen KVKK belgelerini getir.
        """
        queryset = KVKKDocument.objects.filter(
            form_sent=True,
            signed_document__isnull=False,
            is_approved=False
        ).select_related('customer', 'customer__salesperson')
        
        if salesperson:
            queryset = queryset.filter(customer__salesperson=salesperson)
        
        return queryset.order_by('signed_at')



