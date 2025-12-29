"""
Documents app URLs.
"""

from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Document list and detail
    path('', views.DocumentListView.as_view(), name='document_list'),
    path('<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    
    # Document upload and actions
    path('upload/', views.upload_document, name='upload'),
    path('<int:pk>/approve/', views.approve_document, name='approve'),
    path('<int:pk>/reject/', views.reject_document, name='reject'),
    
    # KVKK
    path('kvkk/', views.KVKKDocumentView.as_view(), name='kvkk'),
    path('kvkk/<int:customer_id>/', views.KVKKDocumentView.as_view(), name='kvkk_customer'),
    path('kvkk/<int:customer_id>/send/', views.send_kvkk_form, name='send_kvkk'),
    path('kvkk/<int:customer_id>/upload/', views.upload_signed_kvkk, name='upload_kvkk'),
    path('kvkk/<int:pk>/approve/', views.approve_kvkk, name='approve_kvkk'),
]



