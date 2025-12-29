"""
Documents app views.
Document upload and management views.
"""

from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import UploadedDocument, DocumentTemplate, KVKKDocument, DocumentStatus
from .services import DocumentService
from .validators import validate_document_file


class CustomerRequiredMixin(LoginRequiredMixin):
    """Müşteri veya satışçı erişimi gerektiren mixin."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class DocumentListView(CustomerRequiredMixin, ListView):
    """Belge listesi görünümü."""
    
    model = UploadedDocument
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        # If customer, show their documents
        if user.user_type == 'customer' and hasattr(user, 'customer_profile'):
            return DocumentService.get_customer_documents(user.customer_profile)
        
        # If salesperson, show their customers' documents
        elif user.user_type in ['salesperson', 'admin']:
            customer_id = self.request.GET.get('customer')
            if customer_id:
                from customers.models import Customer
                customer = get_object_or_404(Customer, pk=customer_id, salesperson=user)
                return DocumentService.get_customer_documents(customer)
            return DocumentService.get_pending_documents(user)
        
        return UploadedDocument.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Belgelerim' if self.request.user.user_type == 'customer' else 'Belgeler'
        context['templates'] = DocumentService.get_all_templates()
        
        user = self.request.user
        
        # For customer, show KVKK documents too
        if user.user_type == 'customer' and hasattr(user, 'customer_profile'):
            kvkk_docs = KVKKDocument.objects.filter(
                customer=user.customer_profile
            ).order_by('-created_at')
            context['kvkk_documents'] = kvkk_docs
            
            # Stats for customer
            customer = user.customer_profile
            context['stats'] = {
                'total': UploadedDocument.objects.filter(customer=customer).count() + kvkk_docs.count(),
                'pending': UploadedDocument.objects.filter(customer=customer, status=DocumentStatus.UPLOADED).count(),
                'reviewing': UploadedDocument.objects.filter(customer=customer, status=DocumentStatus.REVIEWING).count(),
                'approved': UploadedDocument.objects.filter(customer=customer, status=DocumentStatus.APPROVED).count() + kvkk_docs.filter(status='approved').count(),
                'rejected': UploadedDocument.objects.filter(customer=customer, status=DocumentStatus.REJECTED).count(),
            }
        else:
            context['stats'] = DocumentService.get_document_stats(
                salesperson=self.request.user if self.request.user.user_type == 'salesperson' else None
            )
        
        return context


class DocumentDetailView(CustomerRequiredMixin, DetailView):
    """Belge detay görünümü."""
    
    model = UploadedDocument
    template_name = 'documents/document_detail.html'
    context_object_name = 'document'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'customer' and hasattr(user, 'customer_profile'):
            return UploadedDocument.objects.filter(customer=user.customer_profile)
        elif user.user_type in ['salesperson', 'admin']:
            return UploadedDocument.objects.filter(customer__salesperson=user)
        elif user.is_superuser:
            return UploadedDocument.objects.all()
        
        return UploadedDocument.objects.none()


@require_POST
def upload_document(request):
    """AJAX: Belge yükleme."""
    user = request.user
    
    if not user.is_authenticated:
        return JsonResponse({'error': 'Giriş yapmalısınız'}, status=401)
    
    file = request.FILES.get('file')
    document_type = request.POST.get('document_type')
    customer_id = request.POST.get('customer_id')
    order_id = request.POST.get('order_id')
    template_id = request.POST.get('template_id')
    title = request.POST.get('title', '')
    
    if not file:
        return JsonResponse({'error': 'Dosya seçilmedi'}, status=400)
    
    if not document_type:
        return JsonResponse({'error': 'Belge tipi seçilmedi'}, status=400)
    
    # Validate file
    try:
        validate_document_file(file)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
    # Get customer
    from customers.models import Customer
    
    if user.user_type == 'customer' and hasattr(user, 'customer_profile'):
        customer = user.customer_profile
    elif customer_id:
        customer = get_object_or_404(Customer, pk=customer_id)
        if user.user_type == 'salesperson' and customer.salesperson != user:
            return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    else:
        return JsonResponse({'error': 'Müşteri belirtilmedi'}, status=400)
    
    # Get optional order
    order = None
    if order_id:
        from orders.models import Order
        order = get_object_or_404(Order, pk=order_id, customer=customer)
    
    # Get optional template
    template = None
    if template_id:
        template = get_object_or_404(DocumentTemplate, pk=template_id)
    
    # Upload document
    document = DocumentService.upload_document(
        file=file,
        customer=customer,
        uploaded_by=user,
        document_type=document_type,
        title=title,
        order=order,
        template=template
    )
    
    return JsonResponse({
        'success': True,
        'document': {
            'id': document.pk,
            'title': document.title,
            'file_url': document.file.url,
            'file_size': document.file_size_display,
            'status': document.status,
            'status_display': document.get_status_display(),
        }
    })


@require_POST
def approve_document(request, pk):
    """AJAX: Belgeyi onayla."""
    user = request.user
    
    if user.user_type not in ['salesperson', 'admin'] and not user.is_superuser:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    document = get_object_or_404(UploadedDocument, pk=pk)
    
    # Check permission
    if user.user_type == 'salesperson' and document.customer.salesperson != user:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    notes = request.POST.get('notes', '')
    DocumentService.approve_document(document, user, notes)
    
    return JsonResponse({
        'success': True,
        'status': document.status,
        'status_display': document.get_status_display()
    })


@require_POST
def reject_document(request, pk):
    """AJAX: Belgeyi reddet."""
    user = request.user
    
    if user.user_type not in ['salesperson', 'admin'] and not user.is_superuser:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    document = get_object_or_404(UploadedDocument, pk=pk)
    
    # Check permission
    if user.user_type == 'salesperson' and document.customer.salesperson != user:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    reason = request.POST.get('reason', '')
    if not reason:
        return JsonResponse({'error': 'Red sebebi belirtilmedi'}, status=400)
    
    DocumentService.reject_document(document, user, reason)
    
    return JsonResponse({
        'success': True,
        'status': document.status,
        'status_display': document.get_status_display()
    })


# KVKK Views

class KVKKDocumentView(CustomerRequiredMixin, DetailView):
    """KVKK belgesi görünümü."""
    
    model = KVKKDocument
    template_name = 'documents/kvkk_document.html'
    context_object_name = 'kvkk'
    
    def get_object(self, queryset=None):
        user = self.request.user
        
        if user.user_type == 'customer' and hasattr(user, 'customer_profile'):
            customer = user.customer_profile
        else:
            customer_id = self.kwargs.get('customer_id')
            from customers.models import Customer
            customer = get_object_or_404(Customer, pk=customer_id)
        
        return DocumentService.get_or_create_kvkk(customer)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'KVKK Onay'
        context['comments'] = self.object.comments.filter(is_internal=False)
        return context


@require_POST
def send_kvkk_form(request, customer_id):
    """AJAX: KVKK formunu gönder."""
    user = request.user
    
    if user.user_type not in ['salesperson', 'admin'] and not user.is_superuser:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    from customers.models import Customer
    customer = get_object_or_404(Customer, pk=customer_id)
    
    # Check permission
    if user.user_type == 'salesperson' and customer.salesperson != user:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    kvkk = DocumentService.send_kvkk_form(customer, user)
    
    return JsonResponse({
        'success': True,
        'message': f'KVKK formu {customer.email} adresine gönderildi.'
    })


@require_POST
def upload_signed_kvkk(request, customer_id):
    """AJAX: İmzalı KVKK belgesini yükle."""
    user = request.user
    
    from customers.models import Customer
    
    if user.user_type == 'customer' and hasattr(user, 'customer_profile'):
        customer = user.customer_profile
    else:
        customer = get_object_or_404(Customer, pk=customer_id)
    
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'Dosya seçilmedi'}, status=400)
    
    try:
        validate_document_file(file, allowed_extensions=['pdf'], max_size_mb=10)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
    kvkk = DocumentService.upload_signed_kvkk(customer, file, user)
    
    return JsonResponse({
        'success': True,
        'message': 'KVKK belgesi yüklendi. Onay için bekleyiniz.'
    })


@require_POST
def approve_kvkk(request, pk):
    """AJAX: KVKK belgesini onayla."""
    user = request.user
    
    if user.user_type not in ['salesperson', 'admin'] and not user.is_superuser:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    kvkk = get_object_or_404(KVKKDocument, pk=pk)
    
    # Check permission
    if user.user_type == 'salesperson' and kvkk.customer.salesperson != user:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    DocumentService.approve_kvkk(kvkk, user)
    
    return JsonResponse({
        'success': True,
        'message': 'KVKK belgesi onaylandı.'
    })
