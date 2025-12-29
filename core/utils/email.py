"""
Email utilities for sending emails.
"""

import logging
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails.
    Provides consistent email sending functionality.
    """
    
    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
    
    def send_simple_email(
        self,
        subject: str,
        message: str,
        recipients: List[str],
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send a simple text email.
        
        Args:
            subject: Email subject
            message: Email body (plain text)
            recipients: List of recipient email addresses
            from_email: Sender email (uses default if not provided)
        
        Returns:
            True if email was sent successfully
        """
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email or self.from_email,
                recipient_list=recipients,
                fail_silently=False
            )
            logger.info(f"Email sent successfully to {recipients}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipients}: {e}")
            return False
    
    def send_template_email(
        self,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        recipients: List[str],
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send an HTML email using a template.
        
        Args:
            subject: Email subject
            template_name: Path to the email template
            context: Context data for the template
            recipients: List of recipient email addresses
            from_email: Sender email (uses default if not provided)
        
        Returns:
            True if email was sent successfully
        """
        try:
            # Render HTML content
            html_content = render_to_string(template_name, context)
            text_content = strip_tags(html_content)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email or self.from_email,
                to=recipients
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Template email sent successfully to {recipients}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send template email to {recipients}: {e}")
            return False
    
    # Specific email methods
    
    def send_welcome_email(self, user, password: Optional[str] = None) -> bool:
        """
        Send welcome email to a new user.
        """
        context = {
            'user': user,
            'password': password,
            'login_url': f"{settings.SITE_URL}/accounts/login/",
            'site_name': 'Leasing Yönetim Sistemi'
        }
        return self.send_template_email(
            subject="Hoş Geldiniz - Leasing Yönetim Sistemi",
            template_name="emails/welcome.html",
            context=context,
            recipients=[user.email]
        )
    
    def send_kvkk_approval_notification(self, salesperson, customer) -> bool:
        """
        Notify salesperson that customer has uploaded KVKK document.
        """
        context = {
            'salesperson': salesperson,
            'customer': customer,
            'review_url': f"{settings.SITE_URL}/customers/{customer.id}/kvkk/",
        }
        return self.send_template_email(
            subject=f"KVKK Onay Bekliyor - {customer.full_name}",
            template_name="emails/kvkk_approval_needed.html",
            context=context,
            recipients=[salesperson.email]
        )
    
    def send_kvkk_revision_notification(self, customer, kvkk_doc, salesperson_note: str = '') -> bool:
        """
        Notify customer that KVKK document has been revised.
        """
        context = {
            'customer': customer,
            'kvkk_doc': kvkk_doc,
            'salesperson_note': salesperson_note,
            'kvkk_url': f"{settings.SITE_URL}/customers/kvkk/{kvkk_doc.pk}/",
        }
        return self.send_template_email(
            subject="KVKK Metniniz Güncellendi - Leasing Yönetim Sistemi",
            template_name="emails/kvkk_revision.html",
            context=context,
            recipients=[customer.email] if customer.email else []
        )
    
    def send_account_activated_email(self, user) -> bool:
        """
        Notify user that their account has been activated.
        """
        context = {
            'user': user,
            'login_url': f"{settings.SITE_URL}/accounts/login/",
        }
        return self.send_template_email(
            subject="Hesabınız Aktif Edildi - Leasing Yönetim Sistemi",
            template_name="emails/account_activated.html",
            context=context,
            recipients=[user.email]
        )
    
    def send_order_status_notification(self, user, order, new_status: str) -> bool:
        """
        Notify user about order status change.
        """
        context = {
            'user': user,
            'order': order,
            'new_status': new_status,
            'order_url': f"{settings.SITE_URL}/orders/{order.id}/",
        }
        return self.send_template_email(
            subject=f"Sipariş Durumu Güncellendi - #{order.id}",
            template_name="emails/order_status_changed.html",
            context=context,
            recipients=[user.email]
        )
    
    def send_daily_digest(self, user, tasks: List, orders: List) -> bool:
        """
        Send daily digest email to user.
        """
        context = {
            'user': user,
            'tasks': tasks,
            'orders': orders,
            'dashboard_url': f"{settings.SITE_URL}/dashboard/",
        }
        return self.send_template_email(
            subject="Günlük Özet - Leasing Yönetim Sistemi",
            template_name="emails/daily_digest.html",
            context=context,
            recipients=[user.email]
        )
    
    def send_proposal_email(
        self,
        subject: str,
        body: str,
        recipients: List[str],
        pdf_attachment: Optional[bytes] = None,
        pdf_filename: str = 'teklif.pdf'
    ) -> bool:
        """
        Send proposal email with optional PDF attachment.
        
        Args:
            subject: Email subject
            body: Email body (plain text)
            recipients: List of recipient email addresses
            pdf_attachment: PDF file bytes (optional)
            pdf_filename: Name of the PDF attachment
        
        Returns:
            True if email was sent successfully
        """
        try:
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=self.from_email,
                to=recipients
            )
            
            # Add PDF attachment if provided
            if pdf_attachment:
                email.attach(pdf_filename, pdf_attachment, 'application/pdf')
            
            email.send(fail_silently=False)
            
            logger.info(f"Proposal email sent successfully to {recipients}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send proposal email to {recipients}: {e}")
            return False


# Singleton instance
email_service = EmailService()

