"""
Orders admin configuration.
"""

from django.contrib import admin
from .models import Order, OrderNote, RequiredDocument


class OrderNoteInline(admin.TabularInline):
    model = OrderNote
    extra = 0
    readonly_fields = ['created_at']
    fields = ['note_type', 'content', 'is_internal', 'is_pinned', 'created_at']


class RequiredDocumentInline(admin.TabularInline):
    model = RequiredDocument
    extra = 0
    raw_id_fields = ['template', 'uploaded_document']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer', 'equipment_type', 'status', 
        'equipment_value', 'created_at'
    ]
    list_filter = ['status', 'equipment_type', 'lease_type', 'created_at']
    search_fields = [
        'order_number', 'customer__company_name', 
        'equipment_brand', 'equipment_model'
    ]
    raw_id_fields = ['customer', 'salesperson', 'created_by']
    date_hierarchy = 'created_at'
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('order_number', 'customer', 'salesperson', 'status')
        }),
        ('Ekipman Bilgileri', {
            'fields': (
                'equipment_type', 'equipment_brand', 'equipment_model',
                'equipment_year', 'equipment_description', 'equipment_quantity'
            )
        }),
        ('Kiralama Bilgileri', {
            'fields': ('lease_type', 'lease_term_months')
        }),
        ('Finansal Bilgiler', {
            'fields': (
                'equipment_value', 'down_payment', 'monthly_payment',
                'total_amount', 'currency'
            )
        }),
        ('Tarihler', {
            'fields': (
                'requested_delivery_date', 'estimated_delivery_date',
                'actual_delivery_date', 'lease_start_date', 'lease_end_date'
            )
        }),
        ('Notlar', {
            'fields': ('customer_notes', 'internal_notes', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Sistem', {
            'fields': (
                'wizard_step', 'wizard_completed', 
                'created_at', 'updated_at', 'submitted_at', 'approved_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [OrderNoteInline, RequiredDocumentInline]


@admin.register(OrderNote)
class OrderNoteAdmin(admin.ModelAdmin):
    list_display = ['order', 'note_type', 'author', 'is_internal', 'created_at']
    list_filter = ['note_type', 'is_internal']
    search_fields = ['order__order_number', 'content']
    raw_id_fields = ['order', 'author']
