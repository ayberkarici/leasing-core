from django.urls import path
from . import views

app_name = 'it_tools'

urlpatterns = [
    # Ana sayfa
    path('', views.ITToolsDashboardView.as_view(), name='dashboard'),
    
    # İş Kolları
    path('usage-types/', views.UsageTypeListView.as_view(), name='usage_type_list'),
    path('usage-types/create/', views.UsageTypeCreateView.as_view(), name='usage_type_create'),
    path('usage-types/<int:pk>/edit/', views.UsageTypeUpdateView.as_view(), name='usage_type_edit'),
    path('usage-types/<int:pk>/delete/', views.UsageTypeDeleteView.as_view(), name='usage_type_delete'),
    
    # Departmanlar
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/create/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_edit'),
    path('departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),
    path('departments/<int:pk>/toggle-active/', views.department_toggle_active, name='department_toggle_active'),
    
    # AD Log Kaynak Path'leri
    path('source-paths/', views.ADLogSourcePathListView.as_view(), name='source_path_list'),
    path('source-paths/create/', views.ADLogSourcePathCreateView.as_view(), name='source_path_create'),
    path('source-paths/<int:pk>/edit/', views.ADLogSourcePathUpdateView.as_view(), name='source_path_edit'),
    path('source-paths/<int:pk>/delete/', views.ADLogSourcePathDeleteView.as_view(), name='source_path_delete'),
    
    # AD Logs
    path('ad-logs/', views.ADLogListView.as_view(), name='ad_log_list'),
    path('ad-logs/create/', views.ADLogCreateView.as_view(), name='ad_log_create'),
    path('ad-logs/<int:pk>/', views.ADLogDetailView.as_view(), name='ad_log_detail'),
    path('ad-logs/<int:pk>/run/', views.ad_log_run_analysis, name='ad_log_run'),
    path('ad-logs/<int:pk>/progress/', views.ad_log_progress, name='ad_log_progress'),
    path('ad-logs/<int:pk>/email-preview/', views.ad_log_email_preview, name='ad_log_email_preview'),
    path('ad-logs/<int:pk>/send-email/', views.ad_log_send_email, name='ad_log_send_email'),
    path('ad-logs/<int:pk>/delete/', views.ADLogDeleteView.as_view(), name='ad_log_delete'),
    
    # Şirket Kullanıcıları (Company Users)
    path('users/', views.CompanyUserListView.as_view(), name='company_user_list'),
    path('users/create/', views.CompanyUserCreateView.as_view(), name='company_user_create'),
    path('users/<int:pk>/', views.CompanyUserDetailView.as_view(), name='company_user_detail'),
    path('users/<int:pk>/edit/', views.CompanyUserUpdateView.as_view(), name='company_user_edit'),
    path('users/<int:pk>/delete/', views.CompanyUserDeleteView.as_view(), name='company_user_delete'),
    path('users/<int:pk>/toggle-active/', views.company_user_toggle_active, name='company_user_toggle_active'),
    
    # Toplu Kullanıcı Import
    path('users/bulk-import/', views.BulkUserImportListView.as_view(), name='bulk_user_import_list'),
    path('users/bulk-import/create/', views.BulkUserImportCreateView.as_view(), name='bulk_user_import_create'),
    path('users/bulk-import/<int:pk>/', views.BulkUserImportDetailView.as_view(), name='bulk_user_import_detail'),
    path('users/bulk-import/download-sample/', views.bulk_user_import_download_sample, name='bulk_user_import_download_sample'),
    
    # Müşteriler (Customers)
    path('customers/', views.CustomerUserListView.as_view(), name='customer_user_list'),
    path('customers/<int:pk>/', views.CustomerUserDetailView.as_view(), name='customer_user_detail'),
    path('customers/<int:pk>/create-account/', views.customer_create_account, name='customer_create_account'),
    
    # Email Şablonları
    path('email-templates/', views.EmailTemplateListView.as_view(), name='email_template_list'),
    path('email-templates/create/', views.EmailTemplateCreateView.as_view(), name='email_template_create'),
    path('email-templates/<int:pk>/edit/', views.EmailTemplateUpdateView.as_view(), name='email_template_edit'),
    path('email-templates/<int:pk>/delete/', views.EmailTemplateDeleteView.as_view(), name='email_template_delete'),
]
