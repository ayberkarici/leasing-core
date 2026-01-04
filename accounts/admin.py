"""
Accounts app admin configuration.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    Departman admin yapılandırması.
    """
    list_display = ['name', 'code', 'org_code', 'user_count', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'org_code', 'description']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'org_code', 'description')
        }),
        (_('Durum'), {
            'fields': ('is_active',)
        }),
    )
    
    def user_count(self, obj):
        return obj.user_count
    user_count.short_description = _('Kullanıcı Sayısı')


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Özelleştirilmiş kullanıcı admin yapılandırması.
    """
    list_display = ['username', 'email', 'full_name', 'user_type', 
                    'department', 'is_verified', 'is_active']
    list_filter = ['user_type', 'department', 'is_verified', 'is_active', 
                   'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Kişisel Bilgiler'), {
            'fields': ('first_name', 'last_name', 'email', 'phone', 
                      'avatar', 'bio')
        }),
        (_('Rol ve Departman'), {
            'fields': ('user_type', 'department')
        }),
        (_('İzinler'), {
            'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser',
                      'groups', 'user_permissions'),
        }),
        (_('Önemli Tarihler'), {
            'fields': ('last_login', 'date_joined', 'last_activity'),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 
                      'user_type', 'department'),
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined', 'last_activity', 
                       'created_at', 'updated_at']
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = _('Ad Soyad')
