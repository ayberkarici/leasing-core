"""
Orders app views.
Order management and wizard views.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Order, OrderNote, OrderStatus, EquipmentType, LeaseType
from .services import OrderService
from documents.services import DocumentService


class CustomerRequiredMixin(LoginRequiredMixin):
    """Müşteri veya satışçı erişimi gerektiren mixin."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class OrderListView(CustomerRequiredMixin, ListView):
    """Sipariş listesi görünümü."""
    
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        filters = {
            'status': self.request.GET.get('status'),
            'search': self.request.GET.get('search'),
        }
        
        # If customer, show their orders
        if user.user_type == 'customer' and hasattr(user, 'customer_profile'):
            return OrderService.get_customer_orders(
                user.customer_profile,
                status=filters.get('status')
            )
        
        # If salesperson or admin
        elif user.user_type in ['salesperson', 'admin']:
            return OrderService.get_salesperson_orders(user, filters)
        
        # Superuser sees all
        elif user.is_superuser:
            return Order.objects.all().select_related('customer', 'salesperson')
        
        return Order.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Siparişler'
        context['status_choices'] = OrderStatus.choices
        context['stats'] = OrderService.get_order_stats(
            salesperson=self.request.user if self.request.user.user_type == 'salesperson' else None,
            customer=self.request.user.customer_profile if self.request.user.user_type == 'customer' and hasattr(self.request.user, 'customer_profile') else None
        )
        context['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'search': self.request.GET.get('search', ''),
        }
        return context


class OrderDetailView(CustomerRequiredMixin, DetailView):
    """Sipariş detay görünümü."""
    
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'customer' and hasattr(user, 'customer_profile'):
            return Order.objects.filter(customer=user.customer_profile)
        elif user.user_type in ['salesperson', 'admin']:
            return Order.objects.filter(salesperson=user)
        elif user.is_superuser:
            return Order.objects.all()
        
        return Order.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Sipariş #{self.object.order_number}'
        context['timeline'] = OrderService.get_order_timeline(
            self.object,
            include_internal=(self.request.user.user_type in ['salesperson', 'admin'])
        )
        context['documents'] = self.object.documents.all()
        context['required_documents'] = self.object.required_documents.select_related('template', 'uploaded_document')
        context['status_choices'] = OrderStatus.choices
        return context


# Order Wizard Views

class OrderWizardStartView(CustomerRequiredMixin, TemplateView):
    """Sipariş wizard başlangıç."""
    
    template_name = 'orders/wizard/start.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Yeni Sipariş'
        return context
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        # Get or create customer
        if user.user_type == 'customer' and hasattr(user, 'customer_profile'):
            customer = user.customer_profile
        else:
            messages.error(request, 'Sipariş oluşturmak için müşteri hesabına sahip olmalısınız.')
            return redirect('orders:order_list')
        
        # Create draft order
        order = OrderService.create_order(
            customer=customer,
            created_by=user,
            equipment_data={'equipment_type': 'other'}
        )
        
        return redirect('orders:wizard_step', pk=order.pk, step=1)


class OrderWizardStepView(CustomerRequiredMixin, UpdateView):
    """Sipariş wizard adımı."""
    
    model = Order
    template_name = 'orders/wizard/step.html'
    fields = []  # Will be set dynamically in get_form_class
    
    # Step-based field definitions
    STEP_FIELDS = {
        1: ['equipment_type', 'equipment_brand', 'equipment_model', 
            'equipment_year', 'equipment_description', 'equipment_quantity', 
            'equipment_value'],
        2: ['lease_type', 'lease_term_months', 'down_payment', 
            'requested_delivery_date', 'customer_notes'],
        3: [],  # Document upload step - no form fields
    }
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'customer' and hasattr(user, 'customer_profile'):
            return Order.objects.filter(customer=user.customer_profile, wizard_completed=False)
        return Order.objects.none()
    
    def get_form_class(self):
        from django import forms
        step = int(self.kwargs.get('step', 1))
        step_fields = self.STEP_FIELDS.get(step, [])
        
        if not step_fields:
            # For step 3 (document upload), return a minimal form
            class EmptyForm(forms.ModelForm):
                class Meta:
                    model = Order
                    fields = []
            return EmptyForm
        
        # Dynamically create form class with step-specific fields
        class StepForm(forms.ModelForm):
            class Meta:
                model = Order
                fields = step_fields
                widgets = {
                    'equipment_description': forms.Textarea(attrs={'rows': 3}),
                    'customer_notes': forms.Textarea(attrs={'rows': 3}),
                    'requested_delivery_date': forms.DateInput(attrs={'type': 'date'}),
                }
        
        return StepForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        step = int(self.kwargs.get('step', 1))
        context['step'] = step
        context['total_steps'] = 3
        context['page_title'] = f'Sipariş Oluştur - Adım {step}/3'
        context['equipment_types'] = EquipmentType.choices
        context['lease_types'] = LeaseType.choices
        
        if step == 3:
            # Document upload step
            context['required_templates'] = DocumentService.get_required_templates()
            context['uploaded_documents'] = self.object.documents.all()
        
        return context
    
    def form_valid(self, form):
        step = int(self.kwargs.get('step', 1))
        order = form.save()
        order.wizard_step = step + 1
        order.save()
        
        if step < 3:
            return redirect('orders:wizard_step', pk=order.pk, step=step + 1)
        else:
            # Final step - submit order
            OrderService.submit_order(order, self.request.user)
            messages.success(self.request, 'Siparişiniz başarıyla oluşturuldu!')
            return redirect('orders:order_detail', pk=order.pk)
    
    def get_template_names(self):
        step = int(self.kwargs.get('step', 1))
        return [f'orders/wizard/step{step}.html', 'orders/wizard/step.html']


class OrderCreateView(CustomerRequiredMixin, CreateView):
    """Satışçı için hızlı sipariş oluşturma."""
    
    model = Order
    template_name = 'orders/order_form.html'
    fields = [
        'customer', 'equipment_type', 'equipment_brand', 'equipment_model',
        'equipment_year', 'equipment_description', 'equipment_quantity',
        'equipment_value', 'lease_type', 'lease_term_months', 'down_payment',
        'requested_delivery_date', 'customer_notes', 'internal_notes'
    ]
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in ['salesperson', 'admin'] and not request.user.is_superuser:
            messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.salesperson = self.request.user
        form.instance.created_by = self.request.user
        form.instance.status = OrderStatus.PENDING_DOCUMENTS
        form.instance.wizard_completed = True
        response = super().form_valid(form)
        
        # Initialize required documents
        OrderService.initialize_required_documents(self.object)
        
        messages.success(self.request, f'Sipariş #{self.object.order_number} oluşturuldu.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('orders:order_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Yeni Sipariş'
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        from customers.models import Customer
        form.fields['customer'].queryset = Customer.objects.filter(
            salesperson=self.request.user,
            is_active=True
        )
        return form


# AJAX Views

@require_POST
def update_order_status(request, pk):
    """AJAX: Sipariş durumunu güncelle."""
    user = request.user
    
    if user.user_type not in ['salesperson', 'admin'] and not user.is_superuser:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    order = get_object_or_404(Order, pk=pk)
    
    if user.user_type == 'salesperson' and order.salesperson != user:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    new_status = request.POST.get('status')
    
    if new_status not in dict(OrderStatus.choices):
        return JsonResponse({'error': 'Geçersiz durum'}, status=400)
    
    order.status = new_status
    order.save()
    
    return JsonResponse({
        'success': True,
        'status': order.status,
        'status_display': order.get_status_display(),
        'status_class': order.status_display_class
    })


@require_POST
def add_order_note(request, pk):
    """AJAX: Siparişe not ekle."""
    user = request.user
    order = get_object_or_404(Order, pk=pk)
    
    # Check access
    if user.user_type == 'customer':
        if not hasattr(user, 'customer_profile') or order.customer != user.customer_profile:
            return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    elif user.user_type == 'salesperson' and order.salesperson != user:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Not içeriği boş olamaz'}, status=400)
    
    is_internal = request.POST.get('is_internal') == 'true' and user.user_type != 'customer'
    note_type = 'customer' if user.user_type == 'customer' else 'note'
    
    note = OrderService.add_note(order, content, user, note_type, is_internal)
    
    return JsonResponse({
        'success': True,
        'note': {
            'id': note.pk,
            'content': note.content,
            'note_type': note.note_type,
            'author': user.get_full_name() or user.username,
            'created_at': note.created_at.strftime('%d.%m.%Y %H:%i')
        }
    })


@require_POST
def approve_order(request, pk):
    """AJAX: Siparişi onayla."""
    user = request.user
    
    if user.user_type not in ['salesperson', 'admin'] and not user.is_superuser:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    order = get_object_or_404(Order, pk=pk)
    
    if user.user_type == 'salesperson' and order.salesperson != user:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    OrderService.approve_order(order, user)
    
    return JsonResponse({
        'success': True,
        'message': 'Sipariş onaylandı.',
        'status': order.status,
        'status_display': order.get_status_display()
    })


@require_POST
def reject_order(request, pk):
    """AJAX: Siparişi reddet."""
    user = request.user
    
    if user.user_type not in ['salesperson', 'admin'] and not user.is_superuser:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    order = get_object_or_404(Order, pk=pk)
    
    reason = request.POST.get('reason', '').strip()
    if not reason:
        return JsonResponse({'error': 'Red sebebi belirtilmedi'}, status=400)
    
    OrderService.reject_order(order, reason, user)
    
    return JsonResponse({
        'success': True,
        'message': 'Sipariş reddedildi.',
        'status': order.status
    })


@require_POST
def complete_documents(request, pk):
    """AJAX: Belge yüklemesini tamamla."""
    user = request.user
    order = get_object_or_404(Order, pk=pk)
    
    # Check access
    if user.user_type == 'customer':
        if not hasattr(user, 'customer_profile') or order.customer != user.customer_profile:
            return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    OrderService.complete_document_upload(order, user)
    
    return JsonResponse({
        'success': True,
        'message': 'Belgeler gönderildi. İncelenmeye alındı.',
        'status': order.status,
        'status_display': order.get_status_display()
    })


import json
from django.contrib.auth.decorators import login_required
from decimal import Decimal


@login_required
@require_POST
def ai_fill_order(request):
    """
    AI ile sipariş formunu otomatik doldur.
    Müşteri kısa bilgiler girer, AI geri kalanını önerir.
    """
    if request.user.user_type not in ['salesperson', 'admin'] and not request.user.is_superuser:
        return JsonResponse({'error': 'Yetkiniz yok'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        equipment_info = data.get('equipment_info', '').strip()
        
        if not equipment_info:
            return JsonResponse({'success': False, 'error': 'Ekipman bilgisi zorunludur.'})
        
        # AI servisini kullan
        from ai_services.services.claude import ClaudeService
        claude = ClaudeService()
        
        prompt = f"""Aşağıdaki kısa ekipman açıklamasından bir leasing sipariş formu için gerekli bilgileri çıkar.
Yanıtını sadece JSON formatında ver, başka hiçbir şey yazma.

Ekipman bilgisi: {equipment_info}

JSON formatı:
{{
    "equipment_type": "vehicle|machinery|technology|office|medical|agricultural|other",
    "equipment_brand": "marka (tahmin et veya boş bırak)",
    "equipment_model": "model (tahmin et veya boş bırak)",
    "equipment_year": null veya 2020-2025 arası bir sayı,
    "equipment_description": "detaylı açıklama",
    "equipment_quantity": sayı,
    "equipment_value": tahmini değer (sadece sayı, TL cinsinden),
    "lease_type": "financial|operational",
    "lease_term_months": 12|24|36|48|60,
    "down_payment_percentage": 0-30 arası peşinat oranı,
    "suggested_monthly_payment": tahmini aylık ödeme (sadece sayı)
}}"""

        try:
            response = claude.generate_text(prompt, max_tokens=500)
            
            # JSON'u parse et
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                ai_data = json.loads(json_match.group())
            else:
                ai_data = {}
        except Exception as ai_error:
            # AI başarısız olursa varsayılan değerler dön
            ai_data = {
                "equipment_type": "other",
                "equipment_description": equipment_info,
                "equipment_quantity": 1,
                "lease_type": "financial",
                "lease_term_months": 36,
                "down_payment_percentage": 10
            }
        
        return JsonResponse({
            'success': True,
            'data': ai_data
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz veri formatı.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
