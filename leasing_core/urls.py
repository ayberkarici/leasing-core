"""
URL configuration for leasing_core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required

from accounts.views import (
    DashboardRedirectView,
    AdminDashboardView,
    SalesDashboardView,
    CustomerDashboardView,
)
from customers.views import KVKKApprovalView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('accounts/', include('accounts.urls')),
    
    # KVKK Approval - Must be before other routes
    path('kvkk/', login_required(KVKKApprovalView.as_view()), name='kvkk_approval'),
    
    # Dashboard routes
    path('', login_required(DashboardRedirectView.as_view()), name='dashboard'),
    path('admin-dashboard/', login_required(AdminDashboardView.as_view()), name='admin_dashboard'),
    path('sales-dashboard/', login_required(SalesDashboardView.as_view()), name='sales_dashboard'),
    path('customer-dashboard/', login_required(CustomerDashboardView.as_view()), name='customer_dashboard'),
    
    # App URLs
    path('customers/', include('customers.urls')),
    path('tasks/', include('tasks.urls')),
    path('orders/', include('orders.urls')),
    path('documents/', include('documents.urls')),
    path('proposals/', include('proposals.urls')),
    path('it-tools/', include('it_tools.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    
    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Admin customization
admin.site.site_header = 'Leasing Yönetim Sistemi'
admin.site.site_title = 'Leasing Admin'
admin.site.index_title = 'Yönetim Paneli'
