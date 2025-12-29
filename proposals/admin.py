from django.contrib import admin
from .models import Proposal, ProposalSection, ProposalEmail, ProposalTemplate, TemplateSectionField


class TemplateSectionFieldInline(admin.TabularInline):
    """Template section'ları inline olarak düzenleme."""
    model = TemplateSectionField
    extra = 1
    ordering = ['order']
    fields = ['order', 'field_type', 'title', 'description', 'is_ai_generated', 'is_required', 'include_in_pdf']


@admin.register(ProposalTemplate)
class ProposalTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'default_valid_days', 'is_active', 'section_count', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    inlines = [TemplateSectionFieldInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active', 'default_valid_days')
        }),
        ('Kullanıcı Rehberi', {
            'fields': ('input_guide',),
            'description': 'Kullanıcıya teklif oluşturmak için ne yazması gerektiğini gösteren örnek metin'
        }),
        ('Email Şablonu', {
            'fields': ('email_subject', 'email_body'),
            'description': 'Kullanılabilir değişkenler: {company_name}, {contact_person}, {equipment_description}, {lease_term_months}, {monthly_payment}, {total_amount}, {currency}, {valid_days}, {salesperson_name}, {salesperson_email}, {salesperson_phone}'
        }),
    )
    
    def section_count(self, obj):
        return obj.sections.count()
    section_count.short_description = 'Bölüm Sayısı'


@admin.register(TemplateSectionField)
class TemplateSectionFieldAdmin(admin.ModelAdmin):
    list_display = ['template', 'title', 'field_type', 'order', 'is_ai_generated', 'is_required']
    list_filter = ['template', 'field_type', 'is_ai_generated', 'is_required']
    search_fields = ['title', 'description']
    ordering = ['template', 'order']


class ProposalSectionInline(admin.TabularInline):
    model = ProposalSection
    extra = 0


class ProposalEmailInline(admin.TabularInline):
    model = ProposalEmail
    extra = 0
    readonly_fields = ['sent_at', 'opened_at']


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ['title', 'customer', 'salesperson', 'status', 'equipment_value', 'created_at']
    list_filter = ['status', 'created_at', 'salesperson']
    search_fields = ['title', 'customer__company_name', 'customer__first_name', 'customer__last_name']
    raw_id_fields = ['customer', 'salesperson']
    readonly_fields = ['created_at', 'updated_at', 'ai_model_used', 'generation_time']
    inlines = [ProposalSectionInline, ProposalEmailInline]
    
    fieldsets = (
        (None, {
            'fields': ('customer', 'salesperson', 'title', 'description', 'status')
        }),
        ('İçerik', {
            'fields': ('original_text', 'generated_content', 'equipment_details')
        }),
        ('Finansal', {
            'fields': ('equipment_value', 'monthly_payment', 'lease_term_months', 'down_payment')
        }),
        ('Takip', {
            'fields': ('sent_at', 'viewed_at', 'responded_at', 'valid_until')
        }),
        ('AI Bilgileri', {
            'fields': ('ai_model_used', 'generation_time'),
            'classes': ('collapse',)
        }),
        ('Tarihler', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProposalSection)
class ProposalSectionAdmin(admin.ModelAdmin):
    list_display = ['proposal', 'section_type', 'title', 'order']
    list_filter = ['section_type']
    search_fields = ['title', 'content', 'proposal__title']


@admin.register(ProposalEmail)
class ProposalEmailAdmin(admin.ModelAdmin):
    list_display = ['proposal', 'recipient_email', 'subject', 'sent_at', 'opened_at']
    list_filter = ['ai_generated', 'sent_at']
    search_fields = ['recipient_email', 'subject']
    readonly_fields = ['sent_at']
