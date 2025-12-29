"""
Orders app URLs.
"""

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Order list and detail
    path('', views.OrderListView.as_view(), name='order_list'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    
    # Order creation
    path('new/', views.OrderCreateView.as_view(), name='order_create'),
    
    # Order wizard
    path('wizard/', views.OrderWizardStartView.as_view(), name='wizard_start'),
    path('wizard/<int:pk>/step/<int:step>/', views.OrderWizardStepView.as_view(), name='wizard_step'),
    
    # AI fill
    path('ai-fill/', views.ai_fill_order, name='ai_fill'),
    
    # AJAX actions
    path('<int:pk>/status/', views.update_order_status, name='update_status'),
    path('<int:pk>/note/', views.add_order_note, name='add_note'),
    path('<int:pk>/approve/', views.approve_order, name='approve'),
    path('<int:pk>/reject/', views.reject_order, name='reject'),
    path('<int:pk>/complete-documents/', views.complete_documents, name='complete_documents'),
]



