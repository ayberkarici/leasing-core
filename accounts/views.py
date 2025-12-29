"""
Accounts app views.
Authentication, user management, and dashboards.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView, LogoutView, 
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.utils import timezone


class CustomLoginView(LoginView):
    """
    Özelleştirilmiş giriş görünümü.
    """
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Kullanıcı tipine göre yönlendirme yapar."""
        user = self.request.user
        if user.is_superuser or user.user_type == 'admin':
            return reverse_lazy('admin_dashboard')
        elif user.user_type == 'salesperson':
            return reverse_lazy('sales_dashboard')
        else:
            return reverse_lazy('customer_dashboard')
    
    def form_valid(self, form):
        """Başarılı giriş sonrası işlemler."""
        response = super().form_valid(form)
        # Update last activity
        self.request.user.last_activity = timezone.now()
        self.request.user.save(update_fields=['last_activity'])
        messages.success(self.request, f'Hoş geldiniz, {self.request.user.full_name}!')
        return response
    
    def form_invalid(self, form):
        """Hatalı giriş sonrası işlemler."""
        messages.error(self.request, 'Kullanıcı adı veya şifre hatalı.')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """
    Özelleştirilmiş çıkış görünümü.
    """
    next_page = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        """Çıkış öncesi mesaj göster."""
        if request.user.is_authenticated:
            messages.info(request, 'Güvenli bir şekilde çıkış yaptınız.')
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordResetView(PasswordResetView):
    """
    Şifre sıfırlama isteği görünümü.
    """
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    
    def form_valid(self, form):
        messages.info(
            self.request, 
            'Şifre sıfırlama bağlantısı email adresinize gönderildi.'
        )
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """
    Şifre sıfırlama emaili gönderildi görünümü.
    """
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Şifre sıfırlama onay görünümü.
    """
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    
    def form_valid(self, form):
        messages.success(self.request, 'Şifreniz başarıyla değiştirildi!')
        return super().form_valid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """
    Şifre sıfırlama tamamlandı görünümü.
    """
    template_name = 'accounts/password_reset_complete.html'


# Dashboard Views

class DashboardRedirectView(TemplateView):
    """
    Kullanıcı tipine göre uygun dashboard'a yönlendirir.
    """
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        user = request.user
        if user.is_superuser or user.user_type == 'admin':
            return redirect('admin_dashboard')
        elif user.user_type == 'salesperson':
            return redirect('sales_dashboard')
        else:
            return redirect('customer_dashboard')


class AdminDashboardView(TemplateView):
    """
    Admin dashboard görünümü.
    """
    template_name = 'dashboard/admin_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Admin kontrolü yap."""
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_superuser or request.user.user_type == 'admin'):
            messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Yönetici Paneli'
        
        from .services import DashboardStatisticsService
        
        # Get all statistics
        context['user_stats'] = DashboardStatisticsService.get_user_stats()
        
        try:
            context['order_stats'] = DashboardStatisticsService.get_order_stats()
        except Exception:
            context['order_stats'] = {'total': 0, 'pending_approval': 0, 'processing': 0, 'completed': 0}
        
        try:
            context['customer_stats'] = DashboardStatisticsService.get_customer_stats()
        except Exception:
            context['customer_stats'] = {'total': 0, 'active': 0}
        
        try:
            context['document_stats'] = DashboardStatisticsService.get_document_stats()
        except Exception:
            context['document_stats'] = {'total': 0, 'pending': 0}
        
        try:
            context['department_stats'] = DashboardStatisticsService.get_department_stats()
        except Exception:
            context['department_stats'] = []
        
        try:
            context['recent_activities'] = DashboardStatisticsService.get_recent_activities(limit=10)
        except Exception:
            context['recent_activities'] = []
        
        try:
            context['pending_approvals'] = DashboardStatisticsService.get_pending_approvals()
        except Exception:
            context['pending_approvals'] = {'orders': [], 'documents': [], 'kvkk': []}
        
        try:
            context['system_health'] = DashboardStatisticsService.get_system_health()
        except Exception:
            context['system_health'] = {'ai_requests_24h': 0, 'ai_success_rate': 100}
        
        try:
            context['salesperson_performance'] = DashboardStatisticsService.get_salesperson_performance()[:10]
        except Exception:
            context['salesperson_performance'] = []
        
        try:
            context['orders_by_month'] = DashboardStatisticsService.get_orders_by_month()
        except Exception:
            context['orders_by_month'] = []
        
        return context


class SalesDashboardView(TemplateView):
    """
    Satış elemanı dashboard görünümü.
    """
    template_name = 'dashboard/sales_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Satış Paneli'
        
        user = self.request.user
        
        # Import services
        from customers.services import CustomerService
        from tasks.services import TaskService
        from customers.models import CustomerNote
        from documents.models import KVKKDocument
        
        # Customer statistics
        context['customer_stats'] = CustomerService.get_dashboard_stats(user)
        
        # Pending customer requests (revision requests from customers)
        context['pending_customer_requests'] = CustomerNote.objects.filter(
            customer__salesperson=user,
            note_type='customer_request'
        ).select_related('customer', 'created_by').order_by('-created_at')[:5]
        context['stage_summary'] = CustomerService.get_stage_summary(user)
        
        # Task statistics
        context['task_stats'] = TaskService.get_dashboard_stats(user)
        
        # Today's priorities - Combined list of all pending actions
        pending_actions = []
        
        # 1. KVKK documents needing action (pending_approval, uploaded, revision_requested)
        kvkk_docs = KVKKDocument.objects.filter(
            customer__salesperson=user,
            status__in=['pending_approval', 'uploaded', 'revision_requested', 'pending_signature']
        ).select_related('customer')
        
        for kvkk in kvkk_docs:
            priority = 90 if kvkk.status == 'pending_approval' else 85 if kvkk.status == 'uploaded' else 80
            action_type = 'kvkk_approval' if kvkk.status == 'pending_approval' else 'kvkk_review' if kvkk.status == 'uploaded' else 'kvkk_pending'
            pending_actions.append({
                'type': 'kvkk',
                'action_type': action_type,
                'priority': priority,
                'title': f"KVKK - {kvkk.customer.company_name}",
                'description': kvkk.get_status_display(),
                'customer': kvkk.customer,
                'url': f"/customers/{kvkk.customer.pk}/",
                'status': kvkk.status,
                'status_display': kvkk.get_status_display(),
                'status_class': kvkk.status_display_class,
                'created_at': kvkk.created_at,
            })
        
        # 2. Tasks with high priority
        tasks = TaskService.get_todays_priorities(user, limit=10)
        for task in tasks:
            pending_actions.append({
                'type': 'task',
                'action_type': 'task',
                'priority': task.ai_priority_score or 50,
                'title': task.title,
                'description': task.get_task_type_display(),
                'customer': task.customer,
                'url': f"/tasks/{task.pk}/",
                'status': task.status,
                'status_display': task.get_status_display(),
                'status_class': task.status_display_class,
                'due_date': task.due_date,
                'is_overdue': task.is_overdue if hasattr(task, 'is_overdue') else False,
                'task_obj': task,
            })
        
        # 3. Customer requests
        customer_requests = CustomerNote.objects.filter(
            customer__salesperson=user,
            note_type='customer_request'
        ).select_related('customer', 'created_by').order_by('-created_at')[:5]
        
        for req in customer_requests:
            pending_actions.append({
                'type': 'customer_request',
                'action_type': 'customer_request',
                'priority': 88,  # High priority for customer requests
                'title': f"Müşteri İsteği - {req.customer.company_name}",
                'description': req.content[:100] + '...' if len(req.content) > 100 else req.content,
                'customer': req.customer,
                'url': f"/customers/{req.customer.pk}/",
                'created_at': req.created_at,
            })
        
        # Sort by priority descending
        pending_actions.sort(key=lambda x: x['priority'], reverse=True)
        
        # Take top 8 items
        context['pending_actions'] = pending_actions[:8]
        
        # Legacy - keep todays_priorities for backward compatibility
        context['todays_priorities'] = tasks[:5]
        
        # Overdue tasks
        context['overdue_tasks'] = TaskService.get_overdue_tasks(user)[:3]
        
        # Customers needing followup
        context['followup_customers'] = CustomerService.get_customers_needing_followup(user, days=3)[:5]
        
        # Recent activities
        context['recent_activities'] = CustomerService.get_recent_activities(user, limit=5)
        
        return context


class CustomerDashboardView(TemplateView):
    """
    Müşteri dashboard görünümü.
    """
    template_name = 'dashboard/customer_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Müşteri Paneli'
        
        user = self.request.user
        
        # Get customer profile
        customer = getattr(user, 'customer_profile', None)
        
        if customer:
            # Import services
            from .services import DashboardStatisticsService
            
            # Proposal statistics
            context['proposal_stats'] = DashboardStatisticsService.get_customer_proposal_stats(customer)
            
            # Recent proposals
            context['recent_proposals'] = DashboardStatisticsService.get_customer_recent_proposals(customer)
            
            # Document count
            context['document_count'] = DashboardStatisticsService.get_customer_document_count(customer)
            
            # Customer's salesperson
            context['salesperson'] = customer.salesperson
        
        return context
