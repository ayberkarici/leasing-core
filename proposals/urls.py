from django.urls import path
from . import views

app_name = 'proposals'

urlpatterns = [
    path('', views.ProposalListView.as_view(), name='list'),
    path('create/', views.ProposalCreateView.as_view(), name='create'),
    path('create/customer/<int:customer_pk>/', views.create_proposal_for_customer, name='create_for_customer'),
    path('<int:pk>/', views.ProposalDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ProposalEditView.as_view(), name='edit'),
    path('<int:pk>/preview/', views.proposal_preview, name='preview'),
    path('<int:pk>/approve/', views.proposal_approve, name='approve'),
    path('<int:pk>/respond/', views.customer_respond_proposal, name='respond'),
    path('<int:pk>/generate-pdf/', views.ProposalGeneratePDFView.as_view(), name='generate_pdf'),
    path('<int:pk>/download-pdf/', views.ProposalDownloadPDFView.as_view(), name='download_pdf'),
    path('<int:pk>/send-email/', views.ProposalSendEmailView.as_view(), name='send_email'),
    path('<int:pk>/regenerate/', views.ProposalRegenerateView.as_view(), name='regenerate'),
    
    # Admin Template Yönetimi
    path('admin/templates/', views.TemplateManagementView.as_view(), name='template_management'),
    path('admin/templates/new/', views.TemplateEditView.as_view(), name='template_create'),
    path('admin/templates/<int:pk>/edit/', views.TemplateEditView.as_view(), name='template_edit'),
    path('admin/templates/<int:pk>/delete/', views.TemplateDeleteView.as_view(), name='template_delete'),
]



