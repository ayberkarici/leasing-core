"""
Proposals app views.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.views import View
from django.http import JsonResponse, HttpResponse, FileResponse
from django.urls import reverse_lazy
from django.utils import timezone

from core.mixins import SalespersonRequiredMixin, AdminRequiredMixin
from .models import Proposal, ProposalSection, ProposalEmail, ProposalStatus, ProposalTemplate, TemplateSectionField
from .services import ProposalGenerator, PDFGenerator, ProposalEmailComposer


class ProposalListView(LoginRequiredMixin, ListView):
    """Teklif listesi görünümü."""
    model = Proposal
    template_name = 'proposals/proposal_list.html'
    context_object_name = 'proposals'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        # Müşteri ise kendi tekliflerini görsün
        if user.user_type == 'customer' and hasattr(user, 'customer_profile'):
            queryset = Proposal.objects.filter(
                customer=user.customer_profile
            ).select_related('customer', 'salesperson').order_by('-created_at')
        else:
            # Satışçı/admin kendi tekliflerini görsün
            queryset = Proposal.objects.filter(
                salesperson=user
            ).select_related('customer').order_by('-created_at')
        
        # Filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                title__icontains=search
            ) | queryset.filter(
                customer__company_name__icontains=search
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['page_title'] = 'Tekliflerim' if user.user_type == 'customer' else 'Teklifler'
        context['status_choices'] = ProposalStatus.choices
        context['is_customer'] = user.user_type == 'customer'
        return context


class ProposalDetailView(LoginRequiredMixin, DetailView):
    """Teklif detay görünümü."""
    model = Proposal
    context_object_name = 'proposal'
    
    def get_template_names(self):
        # Müşteri için farklı template kullan
        if self.request.user.user_type == 'customer':
            return ['proposals/proposal_detail_customer.html']
        return ['proposals/proposal_detail.html']
    
    def get_queryset(self):
        user = self.request.user
        
        # Müşteri ise kendi tekliflerini görsün
        if user.user_type == 'customer' and hasattr(user, 'customer_profile'):
            return Proposal.objects.filter(
                customer=user.customer_profile
            ).select_related('customer', 'salesperson').prefetch_related('sections', 'emails')
        else:
            return Proposal.objects.filter(
                salesperson=user
            ).select_related('customer').prefetch_related('sections', 'emails')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.object.title
        context['sections'] = self.object.sections.all().order_by('order')
        context['emails'] = self.object.emails.all().order_by('-sent_at')[:5]
        context['is_customer'] = self.request.user.user_type == 'customer'
        return context


class ProposalCreateView(SalespersonRequiredMixin, TemplateView):
    """
    Yeni teklif oluşturma görünümü.
    Sadece bir text input ve örnek metin içerir.
    AI, template section'larını doldurur.
    """
    template_name = 'proposals/proposal_create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Yeni Teklif Oluştur'
        
        # Aktif template'i getir
        template = ProposalTemplate.get_active_template()
        context['template'] = template
        
        # Template varsa input guide'ı göster
        if template:
            context['input_guide'] = template.input_guide
            context['template_sections'] = template.sections.filter(is_ai_generated=True).order_by('order')
        else:
            context['input_guide'] = '''Teklif oluşturmak için aşağıdaki bilgileri içeren bir açıklama yazın:

• Ekipman türü ve markası
• Ekipman adedi
• Tahmini ekipman değeri
• İstenen kiralama süresi
• Peşinat tercihi
• Özel istekler'''
        
        # Get salesperson's customers
        from customers.models import Customer
        context['customers'] = Customer.objects.filter(
            salesperson=self.request.user,
            is_active=True
        ).order_by('company_name', 'contact_person')
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle proposal creation with AI."""
        customer_id = request.POST.get('customer_id')
        input_text = request.POST.get('input_text', '').strip()
        
        if not customer_id or not input_text:
            messages.error(request, 'Lütfen müşteri seçin ve teklif detaylarını girin.')
            return redirect('proposals:create')
        
        from customers.models import Customer
        customer = get_object_or_404(Customer, id=customer_id, salesperson=request.user)
        
        # Aktif template'i al
        template = ProposalTemplate.get_active_template()
        
        # Create initial proposal
        proposal = Proposal.objects.create(
            customer=customer,
            salesperson=request.user,
            title='Oluşturuluyor...',
            original_text=input_text,
            status=ProposalStatus.GENERATING
        )
        
        # Generate with AI using template
        generator = ProposalGenerator()
        customer_info = {
            'company_name': customer.company_name or customer.contact_person,
            'contact_person': customer.contact_person,
            'email': customer.email,
            'industry': getattr(customer, 'sector', '') or getattr(customer.company, 'sector', '') if customer.company else ''
        }
        
        try:
            # Template section'larını AI'a gönder
            template_sections = []
            if template:
                for section in template.sections.filter(is_ai_generated=True).order_by('order'):
                    template_sections.append({
                        'field_type': section.field_type,
                        'title': section.title,
                        'description': section.description,
                        'placeholder': section.placeholder_content
                    })
            
            result = generator.generate_proposal_with_template(
                input_text=input_text,
                customer_info=customer_info,
                template_sections=template_sections
            )
            
            if 'error' not in result:
                # Update proposal with generated content
                proposal.title = result.get('title', 'Leasing Teklifi')
                proposal.description = result.get('summary', '')
                proposal.generated_content = str(result)
                proposal.equipment_details = result.get('equipment_details', [])
                proposal.ai_model_used = result.get('ai_model', '')
                proposal.generation_time = result.get('generation_time', 0)
                proposal.status = ProposalStatus.READY
                
                # Set suggested terms
                suggested = result.get('suggested_terms', {})
                proposal.lease_term_months = suggested.get('lease_term_months', 36)
                
                # Finansal bilgileri set et
                if 'equipment_value' in result:
                    from decimal import Decimal
                    proposal.equipment_value = Decimal(str(result['equipment_value']))
                if 'monthly_payment' in result:
                    from decimal import Decimal
                    proposal.monthly_payment = Decimal(str(result['monthly_payment']))
                
                # Email template'ini doldur
                if template:
                    proposal.email_subject = template.email_subject
                    proposal.email_body = template.email_body
                
                proposal.save()
                
                # Create sections
                sections = result.get('sections', [])
                for i, section_data in enumerate(sections):
                    ProposalSection.objects.create(
                        proposal=proposal,
                        section_type=section_data.get('type', 'custom'),
                        title=section_data.get('title', f'Bölüm {i+1}'),
                        content=section_data.get('content', ''),
                        order=i
                    )
                
                messages.success(request, 'Teklif başarıyla oluşturuldu!')
            else:
                proposal.status = ProposalStatus.DRAFT
                proposal.title = 'Teklif Taslağı'
                proposal.save()
                messages.warning(request, 'AI oluşturma başarısız oldu, taslak kaydedildi.')
                
        except Exception as e:
            proposal.status = ProposalStatus.DRAFT
            proposal.title = 'Teklif Taslağı'
            proposal.save()
            messages.error(request, f'Bir hata oluştu: {str(e)}')
        
        return redirect('proposals:detail', pk=proposal.pk)


# ============================================
# Admin Template Yönetimi
# ============================================

class TemplateManagementView(AdminRequiredMixin, TemplateView):
    """Admin için template yönetim sayfası."""
    template_name = 'proposals/admin/template_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Teklif Şablonu Yönetimi'
        context['templates'] = ProposalTemplate.objects.all().prefetch_related('sections')
        context['active_template'] = ProposalTemplate.get_active_template()
        return context


class TemplateEditView(AdminRequiredMixin, View):
    """Template düzenleme görünümü."""
    
    def get(self, request, pk=None):
        if pk:
            template = get_object_or_404(ProposalTemplate, pk=pk)
        else:
            template = None
        
        return render(request, 'proposals/admin/template_edit.html', {
            'template': template,
            'page_title': 'Şablon Düzenle' if template else 'Yeni Şablon',
            'section_types': TemplateSectionField.FieldType.choices
        })
    
    def post(self, request, pk=None):
        if pk:
            template = get_object_or_404(ProposalTemplate, pk=pk)
        else:
            template = ProposalTemplate()
        
        # Template bilgilerini güncelle
        template.name = request.POST.get('name', 'Varsayılan Şablon')
        template.description = request.POST.get('description', '')
        template.input_guide = request.POST.get('input_guide', '')
        template.email_subject = request.POST.get('email_subject', '')
        template.email_body = request.POST.get('email_body', '')
        template.default_valid_days = int(request.POST.get('default_valid_days', 30))
        template.is_active = request.POST.get('is_active') == 'on'
        
        # Eğer bu template aktif yapılıyorsa, diğerlerini pasif yap
        if template.is_active:
            ProposalTemplate.objects.exclude(pk=template.pk if template.pk else None).update(is_active=False)
        
        template.save()
        
        # Section'ları güncelle
        section_ids = request.POST.getlist('section_ids[]')
        section_titles = request.POST.getlist('section_titles[]')
        section_types = request.POST.getlist('section_types[]')
        section_descriptions = request.POST.getlist('section_descriptions[]')
        section_ai_generated = request.POST.getlist('section_ai_generated[]')
        section_orders = request.POST.getlist('section_orders[]')
        
        # Mevcut section'ları sil ve yeniden oluştur
        template.sections.all().delete()
        
        for i in range(len(section_titles)):
            if section_titles[i].strip():
                TemplateSectionField.objects.create(
                    template=template,
                    title=section_titles[i],
                    field_type=section_types[i] if i < len(section_types) else 'custom',
                    description=section_descriptions[i] if i < len(section_descriptions) else '',
                    is_ai_generated=str(i) in section_ai_generated,
                    order=int(section_orders[i]) if i < len(section_orders) else i
                )
        
        messages.success(request, 'Şablon başarıyla kaydedildi.')
        return redirect('proposals:template_management')


class TemplateDeleteView(AdminRequiredMixin, View):
    """Template silme görünümü."""
    
    def post(self, request, pk):
        template = get_object_or_404(ProposalTemplate, pk=pk)
        template.delete()
        messages.success(request, 'Şablon silindi.')
        return redirect('proposals:template_management')


class ProposalEditView(SalespersonRequiredMixin, UpdateView):
    """Teklif düzenleme görünümü."""
    model = Proposal
    template_name = 'proposals/proposal_edit.html'
    fields = ['title', 'description', 'equipment_value', 'monthly_payment', 
              'lease_term_months', 'down_payment', 'valid_until']
    
    def get_queryset(self):
        return Proposal.objects.filter(salesperson=self.request.user)
    
    def get_success_url(self):
        messages.success(self.request, 'Teklif güncellendi.')
        return reverse_lazy('proposals:detail', kwargs={'pk': self.object.pk})


class ProposalGeneratePDFView(SalespersonRequiredMixin, View):
    """PDF oluşturma görünümü."""
    
    def post(self, request, pk):
        proposal = get_object_or_404(
            Proposal, pk=pk, salesperson=request.user
        )
        
        pdf_generator = PDFGenerator()
        success = pdf_generator.save_pdf_to_proposal(proposal)
        
        if success:
            messages.success(request, 'PDF başarıyla oluşturuldu.')
        else:
            messages.error(request, 'PDF oluşturulurken bir hata oluştu.')
        
        return redirect('proposals:detail', pk=pk)


class ProposalDownloadPDFView(SalespersonRequiredMixin, View):
    """PDF indirme görünümü."""
    
    def get(self, request, pk):
        proposal = get_object_or_404(
            Proposal, pk=pk, salesperson=request.user
        )
        
        if proposal.pdf_file:
            return FileResponse(
                proposal.pdf_file.open('rb'),
                as_attachment=True,
                filename=f'Teklif_{proposal.id}.pdf'
            )
        
        # Generate on the fly if not exists
        pdf_generator = PDFGenerator()
        pdf_bytes = pdf_generator.generate_pdf(proposal)
        
        if pdf_bytes:
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Teklif_{proposal.id}.pdf"'
            return response
        
        messages.error(request, 'PDF bulunamadı.')
        return redirect('proposals:detail', pk=pk)


class ProposalSendEmailView(SalespersonRequiredMixin, View):
    """Email gönderme görünümü."""
    
    def get(self, request, pk):
        proposal = get_object_or_404(
            Proposal, pk=pk, salesperson=request.user
        )
        
        # Generate email content
        composer = ProposalEmailComposer()
        recipient_name = proposal.customer.full_name
        
        email_content = composer.compose_email(
            proposal=proposal,
            recipient_name=recipient_name,
            tone='professional'
        )
        
        return render(request, 'proposals/proposal_send_email.html', {
            'proposal': proposal,
            'email_subject': email_content['subject'],
            'email_body': email_content['body'],
            'recipient_email': proposal.customer.email
        })
    
    def post(self, request, pk):
        proposal = get_object_or_404(
            Proposal, pk=pk, salesperson=request.user
        )
        
        recipient_email = request.POST.get('recipient_email')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        
        if not all([recipient_email, subject, body]):
            messages.error(request, 'Tüm alanları doldurun.')
            return redirect('proposals:send_email', pk=pk)
        
        # Send email
        from core.utils.email import EmailService
        
        email_service = EmailService()
        success = email_service.send_simple_email(
            to_email=recipient_email,
            subject=subject,
            message=body
        )
        
        if success:
            # Record email
            ProposalEmail.objects.create(
                proposal=proposal,
                recipient_email=recipient_email,
                subject=subject,
                body=body,
                ai_generated=True
            )
            
            # Update proposal status
            if proposal.status in [ProposalStatus.READY, ProposalStatus.DRAFT]:
                proposal.status = ProposalStatus.SENT
                proposal.sent_at = timezone.now()
                proposal.save()
            
            messages.success(request, 'Email başarıyla gönderildi.')
        else:
            messages.error(request, 'Email gönderilemedi.')
        
        return redirect('proposals:detail', pk=pk)


class ProposalRegenerateView(SalespersonRequiredMixin, View):
    """Teklifi yeniden oluştur."""
    
    def post(self, request, pk):
        proposal = get_object_or_404(
            Proposal, pk=pk, salesperson=request.user
        )
        
        feedback = request.POST.get('feedback', '')
        
        if not feedback:
            messages.error(request, 'Lütfen geri bildirim girin.')
            return redirect('proposals:detail', pk=pk)
        
        # Regenerate with feedback
        new_input = f"{proposal.original_text}\n\nEk bilgi/değişiklik: {feedback}"
        
        generator = ProposalGenerator()
        customer = proposal.customer
        customer_info = {
            'company_name': customer.company_name,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'email': customer.email,
            'industry': customer.industry
        }
        
        try:
            result = generator.generate_proposal(new_input, customer_info)
            
            if 'error' not in result:
                proposal.generated_content = str(result)
                proposal.equipment_details = result.get('equipment_details', [])
                proposal.save()
                
                # Update sections
                proposal.sections.all().delete()
                sections = result.get('sections', [])
                for i, section_data in enumerate(sections):
                    ProposalSection.objects.create(
                        proposal=proposal,
                        section_type=section_data.get('type', 'custom'),
                        title=section_data.get('title', f'Bölüm {i+1}'),
                        content=section_data.get('content', ''),
                        order=i
                    )
                
                messages.success(request, 'Teklif yeniden oluşturuldu!')
            else:
                messages.warning(request, 'Yeniden oluşturma başarısız.')
        except Exception as e:
            messages.error(request, f'Hata: {str(e)}')
        
        return redirect('proposals:detail', pk=pk)


# ============================================
# AJAX API Views
# ============================================

from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from customers.models import Customer
from decimal import Decimal
import json
from datetime import date, timedelta


@login_required
@require_POST
def create_proposal_for_customer(request, customer_pk):
    """Müşteri kartından AI destekli teklif oluşturma."""
    
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    # Yetki kontrolü
    if customer.salesperson != request.user and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Bu müşteri için yetkiniz yok.'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        # AI modu kontrolü
        use_ai = data.get('use_ai', False)
        input_text = data.get('input_text', '').strip()
        
        if use_ai:
            # AI ile içerik oluştur
            if not input_text:
                return JsonResponse({'success': False, 'error': 'Teklif açıklaması zorunludur.'})
            
            if len(input_text) < 20:
                return JsonResponse({'success': False, 'error': 'Lütfen daha detaylı bir açıklama yazın.'})
            
            from .models import ProposalTemplate, TemplateSectionField
            from .services.generator import ProposalGenerator
            
            template = ProposalTemplate.get_active_template()
            if not template:
                return JsonResponse({'success': False, 'error': 'Aktif teklif şablonu bulunamadı.'})
            
            # Müşteri bilgilerini hazırla
            customer_info = {
                'company_name': customer.display_company_name,
                'contact_person': customer.contact_person,
                'email': customer.email,
                'sector': customer.sector or '',
                'address': customer.address or '',
            }
            
            # AI ile içerik oluştur
            generator = ProposalGenerator()
            
            # Template section'larını al
            sections = template.sections.all().order_by('order')
            template_sections = []
            for section in sections:
                template_sections.append({
                    'field_type': section.field_type,
                    'title': section.get_field_type_display(),
                    'description': section.description,
                    'is_ai_generated': section.is_ai_generated,
                })
            
            # AI içerik üret
            print(f"[DEBUG] Calling AI with input: {input_text[:100]}...")
            print(f"[DEBUG] Customer info: {customer_info}")
            print(f"[DEBUG] Template sections: {len(template_sections)}")
            
            ai_result = generator.generate_proposal_with_template(
                input_text=input_text,
                customer_info=customer_info,
                template_sections=template_sections
            )
            
            print(f"[DEBUG] AI Result: {ai_result}")
            
            # Hata kontrolü
            if 'error' in ai_result and not ai_result.get('sections'):
                print(f"[DEBUG] AI Error: {ai_result.get('error')}")
                return JsonResponse({'success': False, 'error': f"AI Hatası: {ai_result.get('error', 'AI içerik oluşturulamadı.')}"})
            
            # AI yanıtından sections listesini al
            generated_sections_list = ai_result.get('sections', [])
            
            # Section'ları birleştir
            pdf_content = ""
            
            # AI sections bir liste olarak geliyor, dictionary'ye çevir
            sections_dict = {}
            for s in generated_sections_list:
                if isinstance(s, dict):
                    sections_dict[s.get('type', '')] = s.get('content', '')
            
            for section in sections:
                section_key = section.field_type
                if section_key in sections_dict:
                    pdf_content += f"## {section.get_field_type_display()}\n\n{sections_dict[section_key]}\n\n"
                elif generated_sections_list:
                    # Eğer type eşleşmezse, sırayla ekle
                    for gs in generated_sections_list:
                        if isinstance(gs, dict) and gs.get('content'):
                            pdf_content += f"## {gs.get('title', section.get_field_type_display())}\n\n{gs.get('content', '')}\n\n"
                            break
            
            # Eğer hala boşsa, summary'yi kullan
            if not pdf_content.strip() and ai_result.get('summary'):
                pdf_content = f"## Teklif Özeti\n\n{ai_result.get('summary')}\n\n"
            
            # Değerleri çıkar (AI sonuçlarından veya varsayılan değerler)
            equipment_value = Decimal(str(ai_result.get('equipment_value', 0) or 0))
            monthly_payment = Decimal(str(ai_result.get('monthly_payment', 0) or 0))
            
            # suggested_terms'den değerleri al
            suggested_terms = ai_result.get('suggested_terms', {})
            lease_term_months = int(suggested_terms.get('lease_term_months', 36) or 36)
            down_payment_percent = Decimal(str(suggested_terms.get('suggested_down_payment_percent', 10) or 10))
            down_payment = equipment_value * down_payment_percent / Decimal('100')
            
            # Eğer değerler 0 ise varsayılan değerler ata
            if monthly_payment == 0 and equipment_value > 0:
                remaining = equipment_value - down_payment
                monthly_payment = (remaining / lease_term_months) * Decimal('1.02')
            
            total_amount = down_payment + (monthly_payment * lease_term_months)
            
            # Teklif başlığı
            title = f"Leasing Teklifi - {customer.display_company_name}"
            
            # Email içeriği
            email_subject = template.email_subject.replace('{company_name}', customer.display_company_name)
            email_body = template.email_body
            
            # Template değişkenlerini değiştir
            template_vars = {
                'company_name': customer.display_company_name,
                'contact_person': customer.contact_person,
                'customer_email': customer.email,
                'date': date.today().strftime('%d.%m.%Y'),
                'salesperson_name': request.user.get_full_name() or request.user.username,
            }
            for key, value in template_vars.items():
                email_body = email_body.replace('{' + key + '}', str(value))
            
            # Geçerlilik tarihi
            valid_until = date.today() + timedelta(days=template.default_valid_days)
            
            # Teklifi oluştur
            proposal = Proposal.objects.create(
                customer=customer,
                salesperson=request.user,
                title=title,
                description=input_text[:500],
                original_text=input_text,
                equipment_value=equipment_value,
                monthly_payment=monthly_payment,
                lease_term_months=lease_term_months,
                down_payment=down_payment,
                total_amount=total_amount,
                currency='TRY',
                email_subject=email_subject,
                email_body=email_body,
                pdf_content=pdf_content,
                valid_until=valid_until,
                status=ProposalStatus.PENDING_APPROVAL
            )
            
            return JsonResponse({
                'success': True,
                'proposal_id': proposal.pk,
                'redirect_url': reverse_lazy('proposals:preview', kwargs={'pk': proposal.pk}).__str__()
            })
        
        else:
            # Eski format (geriye uyumluluk)
            equipment_description = data.get('equipment_description', '').strip()
            equipment_value = data.get('equipment_value')
            lease_term_months = int(data.get('lease_term_months', 36))
            down_payment = Decimal(data.get('down_payment', '0') or '0')
            monthly_payment = data.get('monthly_payment')
            notes = data.get('notes', '').strip()
            
            if not equipment_description:
                return JsonResponse({'success': False, 'error': 'Ekipman açıklaması zorunludur.'})
            
            if not equipment_value:
                return JsonResponse({'success': False, 'error': 'Ekipman değeri zorunludur.'})
            
            equipment_value = Decimal(equipment_value)
            
            # Aylık ödeme hesapla
            if monthly_payment:
                monthly_payment = Decimal(monthly_payment)
            else:
                remaining = equipment_value - down_payment
                monthly_payment = (remaining / lease_term_months) * Decimal('1.02')
            
            total_amount = down_payment + (monthly_payment * lease_term_months)
            
            from .models import ProposalTemplate
            template = ProposalTemplate.get_active_template()
            
            title = f"Leasing Teklifi - {customer.display_company_name}"
            
            template_vars = {
                'company_name': customer.display_company_name,
                'contact_person': customer.contact_person,
                'customer_email': customer.email,
                'equipment_description': equipment_description,
                'equipment_value': f"{equipment_value:,.2f}",
                'down_payment': f"{down_payment:,.2f}",
                'lease_term_months': str(lease_term_months),
                'monthly_payment': f"{monthly_payment:,.2f}",
                'total_amount': f"{total_amount:,.2f}",
                'currency': 'TRY',
                'valid_days': str(template.default_valid_days if template else 30),
                'salesperson_name': request.user.get_full_name() or request.user.username,
                'salesperson_email': request.user.email,
                'salesperson_phone': getattr(request.user, 'phone', ''),
                'date': date.today().strftime('%d.%m.%Y'),
                'proposal_number': f"TKL-{date.today().strftime('%Y%m%d')}-{customer.pk}",
            }
            
            email_subject = template.email_subject if template else "Leasing Teklifi - {company_name}"
            email_body = template.email_body if template else ""
            pdf_content = ""
            
            for key, value in template_vars.items():
                email_subject = email_subject.replace('{' + key + '}', str(value))
                email_body = email_body.replace('{' + key + '}', str(value))
            
            valid_days = template.default_valid_days if template else 30
            valid_until = date.today() + timedelta(days=valid_days)
            
            proposal = Proposal.objects.create(
                customer=customer,
                salesperson=request.user,
                title=title,
                description=equipment_description,
                original_text=f"{equipment_description}\n\nNotlar: {notes}" if notes else equipment_description,
                equipment_value=equipment_value,
                monthly_payment=monthly_payment,
                lease_term_months=lease_term_months,
                down_payment=down_payment,
                total_amount=total_amount,
                currency='TRY',
                email_subject=email_subject,
                email_body=email_body,
                pdf_content=pdf_content,
                valid_until=valid_until,
                status=ProposalStatus.PENDING_APPROVAL
            )
            
            return JsonResponse({
                'success': True,
                'proposal_id': proposal.pk,
                'redirect_url': reverse_lazy('proposals:preview', kwargs={'pk': proposal.pk}).__str__()
            })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz veri formatı.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def proposal_preview(request, pk):
    """Teklif önizleme sayfası."""
    proposal = get_object_or_404(Proposal, pk=pk, salesperson=request.user)
    
    return render(request, 'proposals/proposal_preview.html', {
        'proposal': proposal,
        'page_title': f'Teklif Önizleme - {proposal.title}'
    })


@login_required
@require_POST
def proposal_approve(request, pk):
    """Teklifi onayla ve müşteriye gönder."""
    proposal = get_object_or_404(Proposal, pk=pk, salesperson=request.user)
    
    if proposal.status not in [ProposalStatus.PENDING_APPROVAL, ProposalStatus.DRAFT, ProposalStatus.READY]:
        return JsonResponse({'success': False, 'error': 'Bu teklif onaylanamaz.'})
    
    try:
        data = json.loads(request.body) if request.body else {}
        send_email = data.get('send_email', True)
        
        # PDF oluştur
        pdf_generator = PDFGenerator()
        pdf_success = pdf_generator.save_pdf_to_proposal(proposal)
        
        if send_email and proposal.customer.email:
            # Email gönder
            from core.utils.email import email_service
            from django.core.mail import EmailMessage
            from django.conf import settings
            
            email = EmailMessage(
                subject=proposal.email_subject,
                body=proposal.email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[proposal.customer.email]
            )
            
            # PDF eki
            if proposal.pdf_file:
                email.attach_file(proposal.pdf_file.path)
            
            email.send(fail_silently=False)
            
            proposal.status = ProposalStatus.SENT
            proposal.sent_at = timezone.now()
            
            # Email kaydı
            ProposalEmail.objects.create(
                proposal=proposal,
                recipient_email=proposal.customer.email,
                subject=proposal.email_subject,
                body=proposal.email_body,
                ai_generated=False
            )
        else:
            proposal.status = ProposalStatus.READY
        
        proposal.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Teklif onaylandı ve müşteriye gönderildi.' if send_email else 'Teklif onaylandı.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def customer_respond_proposal(request, pk):
    """
    Müşterinin teklifi kabul veya reddetmesi.
    """
    import json
    
    user = request.user
    
    # Sadece müşteriler bu endpoint'i kullanabilir
    if user.user_type != 'customer' or not hasattr(user, 'customer_profile'):
        return JsonResponse({'success': False, 'error': 'Bu işlem için yetkiniz yok.'}, status=403)
    
    try:
        proposal = Proposal.objects.get(pk=pk, customer=user.customer_profile)
    except Proposal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Teklif bulunamadı.'}, status=404)
    
    # Sadece gönderilmiş, görüntülenmiş veya hazır teklifler yanıtlanabilir
    if proposal.status not in ['sent', 'viewed', 'ready']:
        return JsonResponse({'success': False, 'error': 'Bu teklif zaten yanıtlanmış.'}, status=400)
    
    try:
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'accept':
            proposal.status = ProposalStatus.ACCEPTED
            proposal.responded_at = timezone.now()
            proposal.save()
            
            # Aktivite logu
            from core.models import ActivityLog
            ActivityLog.objects.create(
                user=user,
                action='proposal_accepted',
                description=f'{proposal.customer.display_company_name} teklifi kabul etti: {proposal.title}',
                content_type_id=None,
                object_id=proposal.pk
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Teklif kabul edildi! Satış temsilciniz sizinle iletişime geçecektir.'
            })
            
        elif action == 'reject':
            proposal.status = ProposalStatus.REJECTED
            proposal.responded_at = timezone.now()
            proposal.rejection_reason = data.get('reason', '')
            proposal.save()
            
            # Aktivite logu
            from core.models import ActivityLog
            ActivityLog.objects.create(
                user=user,
                action='proposal_rejected',
                description=f'{proposal.customer.display_company_name} teklifi reddetti: {proposal.title}',
                content_type_id=None,
                object_id=proposal.pk
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Teklif reddedildi.'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Geçersiz işlem.'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz veri.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
