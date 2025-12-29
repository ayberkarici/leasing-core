"""
Customers app admin configuration.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Customer, CustomerNote, Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Company admin configuration."""
    
    list_display = ['name', 'sector', 'city', 'tax_number', 'customer_count', 'created_at']
    list_filter = ['sector', 'city', 'created_at']
    search_fields = ['name', 'tax_number']
    readonly_fields = ['created_at', 'updated_at']
    
    def customer_count(self, obj):
        return obj.customers.count()
    customer_count.short_description = 'Müşteri Sayısı'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Customer admin configuration."""
    
    list_display = [
        'display_company', 'contact_person', 'email', 'phone',
        'stage_badge', 'priority_badge', 'salesperson', 'created_at'
    ]
    list_filter = ['stage', 'priority', 'is_active', 'salesperson', 'company', 'created_at']
    search_fields = ['company__name', 'company_name', 'contact_person', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'company_name']
    raw_id_fields = ['salesperson', 'user_account', 'company']
    
    fieldsets = (
        ('Şirket', {
            'fields': ('company', 'company_name')
        }),
        ('İletişim Bilgileri', {
            'fields': ('contact_person', 'email', 'phone', 'secondary_phone')
        }),
        ('Durum', {
            'fields': ('stage', 'priority', 'is_active')
        }),
        ('İlişkiler', {
            'fields': ('salesperson', 'user_account')
        }),
        ('Takip', {
            'fields': ('last_contact_date', 'next_followup_date', 'notes')
        }),
        ('Eski Alanlar (Uyumluluk)', {
            'fields': ('address', 'city', 'tax_number', 'tax_office', 'sector', 'company_size', 'estimated_value'),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_company(self, obj):
        return obj.display_company_name
    display_company.short_description = 'Şirket'
    
    def stage_badge(self, obj):
        """Stage as colored badge."""
        colors = {
            'lead': '#64748b',
            'contacted': '#3b82f6',
            'qualified': '#06b6d4',
            'proposal_sent': '#a855f7',
            'negotiation': '#f59e0b',
            'contract': '#f97316',
            'won': '#10b981',
            'lost': '#ef4444',
        }
        color = colors.get(obj.stage, '#64748b')
        return format_html(
            '<span style="background-color: {}20; color: {}; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, color, obj.get_stage_display()
        )
    stage_badge.short_description = 'Aşama'
    
    def priority_badge(self, obj):
        """Priority as colored badge."""
        colors = {
            'low': '#64748b',
            'medium': '#3b82f6',
            'high': '#f59e0b',
            'critical': '#ef4444',
        }
        color = colors.get(obj.priority, '#64748b')
        return format_html(
            '<span style="background-color: {}20; color: {}; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Öncelik'


@admin.register(CustomerNote)
class CustomerNoteAdmin(admin.ModelAdmin):
    """CustomerNote admin configuration."""
    
    list_display = ['customer', 'note_type', 'content_preview', 'created_by', 'created_at']
    list_filter = ['note_type', 'created_at']
    search_fields = ['customer__company_name', 'content']
    raw_id_fields = ['customer', 'created_by']
    
    def content_preview(self, obj):
        """Show first 50 chars of content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'İçerik'
