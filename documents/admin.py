"""
Documents admin configuration.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import DocumentTemplate, UploadedDocument, KVKKTemplate, KVKKDocument, KVKKComment


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'document_type', 'is_required', 'is_active', 'order']
    list_filter = ['document_type', 'is_required', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'customer', 'document_type', 'status', 'created_at']
    list_filter = ['document_type', 'status', 'ai_validated']
    search_fields = ['title', 'customer__company_name', 'original_filename']
    raw_id_fields = ['customer', 'order', 'uploaded_by', 'reviewed_by']
    date_hierarchy = 'created_at'
    readonly_fields = ['file_size', 'mime_type', 'created_at', 'updated_at']


@admin.register(KVKKTemplate)
class KVKKTemplateAdmin(admin.ModelAdmin):
    """KVKK şablon yönetimi - Admin varsayılan metni buradan düzenler."""
    
    list_display = ['name', 'version', 'is_active_badge', 'created_by', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['name', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Şablon Bilgileri', {
            'fields': ('name', 'version', 'is_active')
        }),
        ('KVKK Metni', {
            'fields': ('content',),
            'description': 'HTML formatında KVKK aydınlatma metnini girin. Bu metin yeni müşteriler için varsayılan olarak kullanılacaktır.'
        }),
        ('Sistem Bilgileri', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Aktif</span>')
        return format_html('<span style="color: gray;">Pasif</span>')
    is_active_badge.short_description = 'Durum'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('admin/css/forms.css',)
        }


@admin.register(KVKKDocument)
class KVKKDocumentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'status', 'revision_count', 'created_by', 'approved_by', 'created_at']
    list_filter = ['status']
    search_fields = ['customer__company_name', 'customer__contact_person']
    raw_id_fields = ['customer', 'created_by', 'reviewed_by', 'approved_by']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'uploaded_at', 'reviewed_at', 'approved_at']
    
    fieldsets = (
        ('Müşteri', {
            'fields': ('customer',)
        }),
        ('KVKK Metni', {
            'fields': ('kvkk_content', 'template_version'),
            'classes': ('collapse',)
        }),
        ('Durum', {
            'fields': ('status', 'signed_document', 'uploaded_at')
        }),
        ('İnceleme', {
            'fields': ('created_by', 'reviewed_by', 'reviewed_at', 'approved_by', 'approved_at')
        }),
        ('Revizyon', {
            'fields': ('revision_count', 'revision_reason'),
            'classes': ('collapse',)
        }),
        ('Notlar', {
            'fields': ('salesperson_notes', 'internal_notes'),
            'classes': ('collapse',)
        }),
    )


@admin.register(KVKKComment)
class KVKKCommentAdmin(admin.ModelAdmin):
    list_display = ['kvkk_document', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal']
    raw_id_fields = ['kvkk_document', 'author']
