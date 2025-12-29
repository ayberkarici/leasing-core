"""
Customers app URL configuration.
"""

from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.CustomerListView.as_view(), name='customer_list'),
    path('new/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_edit'),
    path('<int:pk>/add-note/', views.add_customer_note, name='add_note'),
    path('<int:pk>/update-stage/', views.update_customer_stage, name='update_stage'),
    path('<int:pk>/resend-email/', views.resend_welcome_email, name='resend_email'),
    path('<int:pk>/delete/', views.delete_customer, name='customer_delete'),
    
    # KVKK endpoints
    path('kvkk/<int:pk>/review/', views.KVKKReviewView.as_view(), name='kvkk_review'),
    path('kvkk/<int:pk>/download/', views.KVKKDownloadPDFView.as_view(), name='kvkk_download'),
    path('kvkk/<int:pk>/customer-note/', views.kvkk_customer_note, name='kvkk_customer_note'),
    path('kvkk/<int:pk>/edit/', views.kvkk_edit_content, name='kvkk_edit'),
    path('kvkk/<int:pk>/send-revision/', views.kvkk_send_revision, name='kvkk_send_revision'),
    path('<int:customer_pk>/kvkk/send/', views.send_kvkk_for_signature, name='kvkk_send'),
    path('api/kvkk/default-content/', views.get_default_kvkk_content, name='kvkk_default_content'),
    
    # Company endpoints
    path('api/companies/search/', views.search_companies, name='search_companies'),
    path('api/companies/create/', views.create_company, name='create_company'),
]

