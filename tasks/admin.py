"""
Tasks app admin configuration.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Task admin configuration."""
    
    list_display = [
        'title', 'task_type', 'status_badge', 'priority_score_badge',
        'assigned_to', 'customer', 'due_date', 'created_at'
    ]
    list_filter = ['status', 'task_type', 'manual_priority', 'assigned_to', 'due_date', 'created_at']
    search_fields = ['title', 'description', 'customer__company_name']
    readonly_fields = ['ai_priority_score', 'ai_priority_reasoning', 'ai_priority_updated_at', 'created_at', 'updated_at', 'completed_at']
    raw_id_fields = ['assigned_to', 'created_by', 'customer']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('title', 'description', 'task_type')
        }),
        ('Durum ve Öncelik', {
            'fields': ('status', 'manual_priority')
        }),
        ('AI Öncelik', {
            'fields': ('ai_priority_score', 'ai_priority_reasoning', 'ai_priority_updated_at'),
            'classes': ('collapse',)
        }),
        ('Atama', {
            'fields': ('assigned_to', 'created_by', 'customer')
        }),
        ('Tarihler', {
            'fields': ('due_date', 'reminder_date', 'completed_at')
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Status as colored badge."""
        colors = {
            'pending': '#64748b',
            'in_progress': '#3b82f6',
            'waiting_response': '#f59e0b',
            'completed': '#10b981',
            'cancelled': '#ef4444',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background-color: {}20; color: {}; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, color, obj.get_status_display()
        )
    status_badge.short_description = 'Durum'
    
    def priority_score_badge(self, obj):
        """AI Priority score as colored badge."""
        if obj.ai_priority_score >= 80:
            color = '#ef4444'
        elif obj.ai_priority_score >= 60:
            color = '#f59e0b'
        elif obj.ai_priority_score >= 40:
            color = '#3b82f6'
        else:
            color = '#64748b'
        
        return format_html(
            '<span style="background-color: {}20; color: {}; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">{}</span>',
            color, color, obj.ai_priority_score
        )
    priority_score_badge.short_description = 'AI Skor'
    
    actions = ['recalculate_priorities']
    
    def recalculate_priorities(self, request, queryset):
        """Recalculate base priorities for selected tasks."""
        for task in queryset:
            task.ai_priority_score = task.calculate_base_priority()
            task.save()
        self.message_user(request, f'{queryset.count()} görev için öncelik skoru yeniden hesaplandı.')
    recalculate_priorities.short_description = 'Öncelik skorlarını yeniden hesapla'
