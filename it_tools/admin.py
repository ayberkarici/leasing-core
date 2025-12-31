from django.contrib import admin
from .models import ADLogAnalysis, PathDefinition, ProcessedADFile, SystemGID, GIDDiscrepancy, ADLogEmailTemplate, UsageType

# PathDefinition için alias
ADLogSourcePath = PathDefinition


@admin.register(UsageType)
class UsageTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at', 'path_count', 'template_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def path_count(self, obj):
        return obj.path_definitions.count()
    path_count.short_description = 'Path Sayısı'
    
    def template_count(self, obj):
        return obj.email_templates.count()
    template_count.short_description = 'Şablon Sayısı'


@admin.register(PathDefinition)
class PathDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'usage_type', 'source_path', 'output_path', 'is_active', 'is_default', 'created_at']
    list_filter = ['usage_type', 'is_active', 'is_default']
    search_fields = ['name', 'source_path']


@admin.register(ADLogAnalysis)
class ADLogAnalysisAdmin(admin.ModelAdmin):
    list_display = ['name', 'year', 'month', 'status', 'processed_files_count', 'unique_gids_count', 'discrepancy_count', 'created_at']
    list_filter = ['status', 'year', 'month', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProcessedADFile)
class ProcessedADFileAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'analysis', 'gids_count', 'processed_at']
    list_filter = ['processed_at']


@admin.register(SystemGID)
class SystemGIDAdmin(admin.ModelAdmin):
    list_display = ['gid', 'display_name', 'email', 'department', 'is_active']
    list_filter = ['is_active', 'department']
    search_fields = ['gid', 'display_name', 'email']


@admin.register(GIDDiscrepancy)
class GIDDiscrepancyAdmin(admin.ModelAdmin):
    list_display = ['gid', 'discrepancy_type', 'analysis', 'source_file', 'created_at']
    list_filter = ['discrepancy_type', 'created_at']
    search_fields = ['gid']


@admin.register(ADLogEmailTemplate)
class ADLogEmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'usage_type', 'subject', 'is_active', 'is_default', 'created_at']
    list_filter = ['usage_type', 'is_active', 'is_default']
