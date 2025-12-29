"""
Customers app views.
Customer management views for sales dashboard.
"""

import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import Customer, CustomerNote, CustomerStage, Company
from .services import CustomerService


class SalespersonRequiredMixin(LoginRequiredMixin):
    """Sadece satış elemanlarının erişebileceği view mixin."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.user_type not in ['salesperson', 'admin'] and not request.user.is_superuser:
            messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class CustomerListView(SalespersonRequiredMixin, ListView):
    """Müşteri listesi görünümü."""
    
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20
    
    def get_queryset(self):
        filters = {
            'stage': self.request.GET.get('stage'),
            'priority': self.request.GET.get('priority'),
            'search': self.request.GET.get('search'),
        }
        return CustomerService.get_customers_for_salesperson(self.request.user, filters)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Müşterilerim'
        context['stage_choices'] = CustomerStage.choices
        context['stage_summary'] = CustomerService.get_stage_summary(self.request.user)
        context['current_filters'] = {
            'stage': self.request.GET.get('stage', ''),
            'priority': self.request.GET.get('priority', ''),
            'search': self.request.GET.get('search', ''),
        }
        return context


class CustomerDetailView(SalespersonRequiredMixin, DetailView):
    """Müşteri detay görünümü."""
    
    model = Customer
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'
    
    def get_queryset(self):
        # Sadece kullanıcının müşterilerini göster (admin hariç)
        if self.request.user.is_superuser or self.request.user.user_type == 'admin':
            return Customer.objects.select_related('company').all()
        return Customer.objects.select_related('company').filter(salesperson=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.object.display_company_name
        context['notes'] = self.object.customer_notes.select_related('created_by')[:20]
        context['tasks'] = self.object.tasks.filter(
            status__in=['pending', 'in_progress', 'waiting_response']
        ).order_by('-ai_priority_score')[:5]
        context['stage_choices'] = CustomerStage.choices
        return context


class CustomerCreateView(SalespersonRequiredMixin, CreateView):
    """Yeni müşteri oluşturma görünümü."""
    
    model = Customer
    template_name = 'customers/customer_form.html'
    fields = ['contact_person', 'email', 'phone', 'secondary_phone', 'notes']
    
    def post(self, request, *args, **kwargs):
        # Get company
        company_id = request.POST.get('company_id')
        company = None
        
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                messages.error(request, 'Seçilen şirket bulunamadı.')
                return redirect('customers:customer_create')
        
        if not company:
            messages.error(request, 'Lütfen bir şirket seçin veya yeni şirket ekleyin.')
            return redirect('customers:customer_create')
        
        # Build customer data
        customer_data = {
            'company': company,
            'company_name': company.name,
            'contact_person': request.POST.get('contact_person', ''),
            'email': request.POST.get('email', ''),
            'phone': request.POST.get('phone', ''),
            'secondary_phone': request.POST.get('secondary_phone', ''),
            'notes': request.POST.get('notes', ''),
            'stage': 'lead',
            'priority': 'medium',
        }
        
        # Validate required fields
        if not customer_data['contact_person']:
            messages.error(request, 'İlgili kişi alanı zorunludur.')
            return redirect('customers:customer_create')
        
        if not customer_data['email']:
            messages.error(request, 'Email alanı zorunludur.')
            return redirect('customers:customer_create')
        
        if not customer_data['phone']:
            messages.error(request, 'Telefon alanı zorunludur.')
            return redirect('customers:customer_create')
        
        # Create customer with user account
        try:
            customer, user, password = CustomerService.create_customer_with_user(
                salesperson=request.user,
                customer_data=customer_data,
                send_email=True
            )
            
            # Create KVKK document for the customer
            kvkk_content = request.POST.get('kvkk_content', '').strip()
            kvkk_doc = KVKKService.create_kvkk_for_customer(
                customer=customer,
                created_by=request.user,
                custom_content=kvkk_content if kvkk_content else None
            )
            
            # Send KVKK for signature
            KVKKService.send_for_signature(kvkk_doc, request.user)
            
            messages.success(
                request, 
                f'Müşteri başarıyla oluşturuldu! Giriş bilgileri {customer.email} adresine gönderildi. '
                f'KVKK belgesi imzaya gönderildi.'
            )
            return redirect('customers:customer_detail', pk=customer.pk)
        except Exception as e:
            messages.error(request, f'Müşteri oluşturulurken hata: {str(e)}')
            return redirect('customers:customer_create')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Yeni Müşteri'
        context['is_edit'] = False
        return context


class CustomerUpdateView(SalespersonRequiredMixin, UpdateView):
    """Müşteri düzenleme görünümü."""
    
    model = Customer
    template_name = 'customers/customer_form.html'
    fields = ['contact_person', 'email', 'phone', 'secondary_phone', 'notes']
    
    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.user_type == 'admin':
            return Customer.objects.select_related('company').all()
        return Customer.objects.select_related('company').filter(salesperson=self.request.user)
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Get company
        company_id = request.POST.get('company_id')
        company = None
        
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                messages.error(request, 'Seçilen şirket bulunamadı.')
                return redirect('customers:customer_update', pk=self.object.pk)
        
        if not company:
            messages.error(request, 'Lütfen bir şirket seçin veya yeni şirket ekleyin.')
            return redirect('customers:customer_update', pk=self.object.pk)
        
        # Update customer
        self.object.company = company
        self.object.company_name = company.name
        self.object.contact_person = request.POST.get('contact_person', self.object.contact_person)
        self.object.email = request.POST.get('email', self.object.email)
        self.object.phone = request.POST.get('phone', self.object.phone)
        self.object.secondary_phone = request.POST.get('secondary_phone', '')
        self.object.notes = request.POST.get('notes', '')
        
        try:
            self.object.save()
            messages.success(request, 'Müşteri bilgileri güncellendi.')
            return redirect('customers:customer_detail', pk=self.object.pk)
        except Exception as e:
            messages.error(request, f'Güncelleme sırasında hata: {str(e)}')
            return redirect('customers:customer_update', pk=self.object.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'{self.object.display_company_name} - Düzenle'
        context['is_edit'] = True
        context['customer'] = self.object
        return context


def search_companies(request):
    """AJAX: Şirket arama."""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'companies': []})
    
    companies = Company.objects.filter(
        name__icontains=query
    ).order_by('name')[:10]
    
    return JsonResponse({
        'companies': [
            {
                'id': c.id,
                'name': c.name,
                'city': c.city,
                'sector': c.sector,
                'tax_number': c.tax_number,
            }
            for c in companies
        ]
    })


def create_company(request):
    """AJAX: Yeni şirket oluştur."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    name = data.get('name', '').strip()
    
    if not name:
        return JsonResponse({'error': 'Şirket adı gereklidir'}, status=400)
    
    # Check if company exists
    if Company.objects.filter(name__iexact=name).exists():
        return JsonResponse({'error': 'Bu isimde bir şirket zaten mevcut'}, status=400)
    
    company = Company.objects.create(
        name=name,
        tax_number=data.get('tax_number', ''),
        sector=data.get('sector', ''),
        city=data.get('city', ''),
    )
    
    return JsonResponse({
        'success': True,
        'company': {
            'id': company.id,
            'name': company.name,
            'city': company.city,
            'sector': company.sector,
            'tax_number': company.tax_number,
        }
    })


def add_customer_note(request, pk):
    """AJAX: Müşteriye not ekle."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    customer = get_object_or_404(Customer, pk=pk, salesperson=request.user)
    
    note_type = request.POST.get('note_type', 'note')
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'error': 'İçerik boş olamaz'}, status=400)
    
    note = CustomerService.add_note(customer, note_type, content, request.user)
    
    return JsonResponse({
        'success': True,
        'note': {
            'id': note.id,
            'type': note.get_note_type_display(),
            'content': note.content,
            'created_at': note.created_at.strftime('%d.%m.%Y %H:%M'),
            'created_by': note.created_by.full_name if note.created_by else 'Sistem',
        }
    })


def update_customer_stage(request, pk):
    """AJAX: Müşteri aşamasını güncelle."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    customer = get_object_or_404(Customer, pk=pk, salesperson=request.user)
    
    new_stage = request.POST.get('stage')
    note = request.POST.get('note', '')
    
    if new_stage not in dict(CustomerStage.choices):
        return JsonResponse({'error': 'Geçersiz aşama'}, status=400)
    
    CustomerService.update_stage(customer, new_stage, request.user, note)
    
    return JsonResponse({
        'success': True,
        'stage': new_stage,
        'stage_display': customer.get_stage_display(),
        'stage_class': customer.stage_display_class,
    })


def resend_welcome_email(request, pk):
    """AJAX: Müşteriye hoşgeldin emailini tekrar gönder."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    customer = get_object_or_404(Customer, pk=pk, salesperson=request.user)
    
    if not customer.user_account:
        return JsonResponse({'error': 'Müşterinin kullanıcı hesabı yok'}, status=400)
    
    success, new_password = CustomerService.resend_welcome_email(customer)
    
    if success:
        # Aktivite notu ekle
        CustomerService.add_note(
            customer=customer,
            note_type='note',
            content=f"Hoşgeldin emaili tekrar gönderildi. Yeni şifre oluşturuldu.",
            user=request.user
        )
        return JsonResponse({
            'success': True,
            'message': f'Email başarıyla gönderildi: {customer.email}'
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Email gönderilemedi. Lütfen tekrar deneyin.',
            'password': new_password  # Yönetici görebilir
        })


def delete_customer(request, pk):
    """AJAX: Müşteriyi sil (deaktif et)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    # Check permissions
    if request.user.is_superuser or request.user.user_type == 'admin':
        customer = get_object_or_404(Customer, pk=pk)
    else:
        customer = get_object_or_404(Customer, pk=pk, salesperson=request.user)
    
    try:
        customer_name = customer.display_company_name
        
        # Soft delete - deactivate the customer
        customer.is_active = False
        customer.save(update_fields=['is_active'])
        
        # Also deactivate the user account if exists
        if customer.user_account:
            customer.user_account.is_active = False
            customer.user_account.save(update_fields=['is_active'])
        
        # Log the action
        CustomerService.add_note(
            customer=customer,
            note_type='status_change',
            content=f"Müşteri silindi (deaktif edildi) - {request.user.full_name}",
            user=request.user
        )
        
        # Add flash message
        messages.success(request, f'"{customer_name}" müşterisi başarıyla silindi.')
        
        return JsonResponse({
            'success': True,
            'message': 'Müşteri başarıyla silindi.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Silme işlemi başarısız: {str(e)}'
        }, status=500)


# =====================
# KVKK Views
# =====================

from django.views import View
from django.views.generic import TemplateView
from django.http import HttpResponse, FileResponse
from documents.models import KVKKDocument, KVKKStatus, KVKKTemplate
from documents.services.kvkk_service import KVKKService


class KVKKApprovalView(LoginRequiredMixin, TemplateView):
    """
    Müşteri KVKK sayfası.
    - KVKK onaylanmamışsa: Bekleme ekranı + PDF indirme + İmzalı belge yükleme
    - KVKK onaylandıysa: Dashboard'a yönlendir
    """
    
    template_name = 'customers/kvkk_approval.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Only for customer users
        if request.user.user_type != 'customer':
            return redirect('dashboard')
        
        # If already approved, redirect to dashboard
        if hasattr(request.user, 'customer_profile') and request.user.customer_profile:
            if request.user.customer_profile.kvkk_approved:
                return redirect('customer_dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'KVKK Onayı'
        
        customer = self.request.user.customer_profile if hasattr(self.request.user, 'customer_profile') else None
        
        print(f"DEBUG KVKKApprovalView: user={self.request.user}, customer={customer}")
        
        if customer:
            # Get or create KVKK document
            kvkk_doc = getattr(customer, 'kvkk_document', None)
            context['kvkk_doc'] = kvkk_doc
            context['customer'] = customer
            
            print(f"DEBUG KVKKApprovalView: kvkk_doc={kvkk_doc}")
            
            if kvkk_doc:
                context['can_upload'] = kvkk_doc.can_upload
                context['can_download'] = kvkk_doc.can_be_downloaded
                print(f"DEBUG KVKKApprovalView: status={kvkk_doc.status}, can_upload={kvkk_doc.can_upload}, can_download={kvkk_doc.can_be_downloaded}")
        else:
            print("DEBUG KVKKApprovalView: No customer found!")
        
        return context
    
    def post(self, request, *args, **kwargs):
        """İmzalı KVKK belgesini yükle."""
        
        if not hasattr(request.user, 'customer_profile') or not request.user.customer_profile:
            messages.error(request, 'Müşteri profili bulunamadı.')
            return redirect('accounts:login')
        
        customer = request.user.customer_profile
        kvkk_doc = getattr(customer, 'kvkk_document', None)
        
        if not kvkk_doc:
            messages.error(request, 'KVKK belgesi bulunamadı. Lütfen satışçınızla iletişime geçin.')
            return redirect('kvkk_approval')
        
        if not kvkk_doc.can_upload:
            messages.error(request, 'Şu anda belge yükleyemezsiniz.')
            return redirect('kvkk_approval')
        
        # Get uploaded file
        uploaded_file = request.FILES.get('signed_document')
        if not uploaded_file:
            messages.error(request, 'Lütfen imzalı belgeyi yükleyin.')
            return redirect('kvkk_approval')
        
        # Validate file
        allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
        ext = uploaded_file.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            messages.error(request, f'Geçersiz dosya formatı. İzin verilen: {", ".join(allowed_extensions)}')
            return redirect('kvkk_approval')
        
        # Max 10MB
        if uploaded_file.size > 10 * 1024 * 1024:
            messages.error(request, 'Dosya boyutu 10MB\'ı aşamaz.')
            return redirect('kvkk_approval')
        
        # Upload
        KVKKService.upload_signed_document(kvkk_doc, uploaded_file)
        
        # Log
        CustomerService.add_note(
            customer=customer,
            note_type='status_change',
            content="İmzalı KVKK belgesi yüklendi, onay bekliyor.",
            user=request.user
        )
        
        messages.success(request, 'İmzalı belge başarıyla yüklendi. Satışçınız inceleyecektir.')
        return redirect('kvkk_approval')


@login_required
@require_POST
def kvkk_customer_note(request, pk):
    """Müşteri KVKK hakkında not/düzeltme isteği gönderir."""
    from documents.models import KVKKDocument
    
    kvkk_doc = get_object_or_404(KVKKDocument, pk=pk)
    
    # Check if user is the customer for this KVKK
    user = request.user
    if user.user_type != 'customer':
        messages.error(request, 'Bu işlem sadece müşteriler için geçerlidir.')
        return redirect('kvkk_approval')
    
    if not hasattr(user, 'customer_profile') or user.customer_profile != kvkk_doc.customer:
        messages.error(request, 'Bu belgeye erişim yetkiniz yok.')
        return redirect('kvkk_approval')
    
    customer_note = request.POST.get('customer_note', '').strip()
    
    if not customer_note:
        messages.error(request, 'Lütfen bir not yazın.')
        return redirect('kvkk_approval')
    
    # Add to internal notes
    from django.utils import timezone
    timestamp = timezone.now().strftime('%d.%m.%Y %H:%M')
    note_entry = f"[{timestamp}] Müşteri Notu: {customer_note}"
    
    if kvkk_doc.internal_notes:
        kvkk_doc.internal_notes = f"{kvkk_doc.internal_notes}\n\n{note_entry}"
    else:
        kvkk_doc.internal_notes = note_entry
    
    kvkk_doc.save(update_fields=['internal_notes'])
    
    # Add customer note
    CustomerService.add_note(
        customer=kvkk_doc.customer,
        note_type='customer_request',
        content=f"KVKK hakkında müşteri isteği: {customer_note}",
        user=request.user
    )
    
    # Notify salesperson (you can add email notification here if needed)
    
    messages.success(request, 'İsteğiniz satışçınıza iletildi.')
    return redirect('kvkk_approval')


class KVKKDownloadPDFView(LoginRequiredMixin, View):
    """KVKK PDF indirme."""
    
    def get(self, request, pk):
        print(f"DEBUG KVKKDownloadPDFView: pk={pk}, user={request.user}")
        
        # Get customer's KVKK document
        from documents.models import KVKKDocument
        
        kvkk_doc = get_object_or_404(KVKKDocument, pk=pk)
        print(f"DEBUG KVKKDownloadPDFView: kvkk_doc.customer={kvkk_doc.customer}")
        
        # Check access
        user = request.user
        print(f"DEBUG KVKKDownloadPDFView: user_type={user.user_type}, is_superuser={user.is_superuser}")
        
        # Admin and superuser can access all
        if not user.is_superuser and user.user_type != 'admin':
            if user.user_type == 'customer':
                has_profile = hasattr(user, 'customer_profile') and user.customer_profile
                print(f"DEBUG KVKKDownloadPDFView: has_profile={has_profile}")
                if has_profile:
                    print(f"DEBUG KVKKDownloadPDFView: customer_profile={user.customer_profile}, equals={user.customer_profile == kvkk_doc.customer}")
                if not has_profile or user.customer_profile != kvkk_doc.customer:
                    print(f"DEBUG KVKKDownloadPDFView: ACCESS DENIED for customer")
                    return JsonResponse({'error': 'Bu belgeye erişim yetkiniz yok.'}, status=403)
            elif user.user_type == 'salesperson':
                if kvkk_doc.customer.salesperson != user:
                    print(f"DEBUG KVKKDownloadPDFView: ACCESS DENIED for salesperson")
                    return JsonResponse({'error': 'Bu belgeye erişim yetkiniz yok.'}, status=403)
        
        print(f"DEBUG KVKKDownloadPDFView: Access granted, generating PDF...")
        
        # Generate PDF
        try:
            pdf_bytes, filename = KVKKService.generate_pdf(kvkk_doc)
            print(f"DEBUG KVKKDownloadPDFView: PDF generated: {filename}, size={len(pdf_bytes)}")
            
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"DEBUG KVKKDownloadPDFView: Error generating PDF: {str(e)}")
            return JsonResponse({'error': f'PDF oluşturulurken hata: {str(e)}'}, status=500)


class KVKKReviewView(SalespersonRequiredMixin, TemplateView):
    """Satışçı KVKK inceleme sayfası."""
    
    template_name = 'customers/kvkk_review.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        pk = self.kwargs.get('pk')
        kvkk_doc = get_object_or_404(KVKKDocument, pk=pk)
        
        # Check access
        if kvkk_doc.customer.salesperson != self.request.user and not self.request.user.is_superuser:
            messages.error(self.request, 'Bu belgeye erişim yetkiniz yok.')
            return context
        
        context['kvkk_doc'] = kvkk_doc
        context['customer'] = kvkk_doc.customer
        context['page_title'] = f'KVKK İnceleme - {kvkk_doc.customer.display_company_name}'
        
        return context
    
    def post(self, request, pk):
        """KVKK'yı onayla veya revizyon iste."""
        
        kvkk_doc = get_object_or_404(KVKKDocument, pk=pk)
        
        # Check access
        if kvkk_doc.customer.salesperson != request.user and not request.user.is_superuser:
            return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
        
        action = request.POST.get('action')
        
        if action == 'approve':
            KVKKService.approve_kvkk(kvkk_doc, request.user)
            
            CustomerService.add_note(
                customer=kvkk_doc.customer,
                note_type='status_change',
                content=f"KVKK belgesi onaylandı - {request.user.full_name}",
                user=request.user
            )
            
            messages.success(request, 'KVKK belgesi onaylandı. Müşteri artık sisteme erişebilir.')
            
        elif action == 'revision':
            reason = request.POST.get('reason', '').strip()
            if not reason:
                messages.error(request, 'Revizyon sebebi belirtmelisiniz.')
                return redirect('customers:kvkk_review', pk=pk)
            
            KVKKService.request_revision(kvkk_doc, request.user, reason)
            
            CustomerService.add_note(
                customer=kvkk_doc.customer,
                note_type='status_change',
                content=f"KVKK revizyon istendi: {reason}",
                user=request.user
            )
            
            messages.warning(request, 'Revizyon talebi gönderildi. Müşteri yeni belge yükleyecek.')
        
        return redirect('customers:customer_detail', pk=kvkk_doc.customer.pk)


@login_required
@require_POST
def kvkk_edit_content(request, pk):
    """KVKK içeriğini düzenle - Satış elemanı için."""
    from documents.models import KVKKDocument
    import json
    
    kvkk_doc = get_object_or_404(KVKKDocument, pk=pk)
    
    # Yetki kontrolü - sadece satış elemanı veya admin
    if kvkk_doc.customer.salesperson != request.user and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Bu işlem için yetkiniz yok.'}, status=403)
    
    try:
        data = json.loads(request.body)
        new_content = data.get('kvkk_content', '').strip()
        
        if not new_content:
            return JsonResponse({'success': False, 'error': 'KVKK içeriği boş olamaz.'})
        
        # İçeriği güncelle
        kvkk_doc.kvkk_content = new_content
        kvkk_doc.save(update_fields=['kvkk_content', 'updated_at'])
        
        # Not ekle
        CustomerService.add_note(
            customer=kvkk_doc.customer,
            note_type='status_change',
            content=f"KVKK metni düzenlendi.",
            user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'KVKK içeriği güncellendi.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz veri formatı.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_default_kvkk_content(request):
    """AJAX: Varsayılan KVKK metnini getir."""
    content = KVKKService.get_default_kvkk_content()
    return JsonResponse({'content': content})


@login_required
@require_POST
def kvkk_send_revision(request, pk):
    """KVKK revizyonunu müşteriye gönder - içeriği güncelle ve email at."""
    from documents.models import KVKKDocument, KVKKStatus
    from core.utils.email import email_service
    from django.conf import settings
    import json
    
    kvkk_doc = get_object_or_404(KVKKDocument, pk=pk)
    
    # Yetki kontrolü
    if kvkk_doc.customer.salesperson != request.user and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Bu işlem için yetkiniz yok.'}, status=403)
    
    try:
        data = json.loads(request.body)
        new_content = data.get('kvkk_content', '').strip()
        salesperson_note = data.get('salesperson_note', '').strip()
        
        if not new_content:
            return JsonResponse({'success': False, 'error': 'KVKK içeriği boş olamaz.'})
        
        # İçeriği güncelle
        kvkk_doc.kvkk_content = new_content
        kvkk_doc.status = KVKKStatus.REVISION_REQUESTED
        kvkk_doc.revision_count += 1
        kvkk_doc.revision_reason = f"Satışçı tarafından revize edildi. {'Not: ' + salesperson_note if salesperson_note else ''}"
        kvkk_doc.salesperson_notes = salesperson_note
        
        # İmzalı belgeyi temizle (yeni imza gerekecek)
        if kvkk_doc.signed_document:
            kvkk_doc.signed_document = None
            kvkk_doc.uploaded_at = None
        
        kvkk_doc.save()
        
        # Not ekle
        CustomerService.add_note(
            customer=kvkk_doc.customer,
            note_type='status_change',
            content=f"KVKK metni revize edildi ve müşteriye gönderildi. {salesperson_note if salesperson_note else ''}",
            user=request.user
        )
        
        # Email gönder
        customer = kvkk_doc.customer
        if customer.email:
            kvkk_url = f"{settings.SITE_URL}/customers/kvkk/{kvkk_doc.pk}/"
            
            email_service.send_template_email(
                subject=f"KVKK Metniniz Güncellendi - Leasing Yönetim Sistemi",
                template_name="emails/kvkk_revision.html",
                context={
                    'customer': customer,
                    'kvkk_doc': kvkk_doc,
                    'salesperson': request.user,
                    'salesperson_note': salesperson_note,
                    'kvkk_url': kvkk_url,
                },
                recipients=[customer.email]
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Revize edilen KVKK müşteriye gönderildi.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz veri formatı.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def send_kvkk_for_signature(request, customer_pk):
    """AJAX: KVKK'yı imzaya gönder."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    # Check access
    if customer.salesperson != request.user and not request.user.is_superuser:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    # Get custom content if provided
    import json
    try:
        data = json.loads(request.body)
        custom_content = data.get('kvkk_content')
    except:
        custom_content = None
    
    # Create or update KVKK document
    kvkk_doc = KVKKService.create_kvkk_for_customer(
        customer=customer,
        created_by=request.user,
        custom_content=custom_content
    )
    
    # Send for signature
    KVKKService.send_for_signature(kvkk_doc, request.user)
    
    # Log
    CustomerService.add_note(
        customer=customer,
        note_type='status_change',
        content="KVKK belgesi imzaya gönderildi.",
        user=request.user
    )
    
    return JsonResponse({
        'success': True,
        'message': 'KVKK belgesi imzaya gönderildi.'
    })
