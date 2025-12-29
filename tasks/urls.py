"""
Tasks app URL configuration.
"""

from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.TaskListView.as_view(), name='task_list'),
    path('new/', views.TaskCreateView.as_view(), name='task_create'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
    path('<int:pk>/update-status/', views.update_task_status, name='update_status'),
    path('<int:pk>/complete/', views.mark_task_complete, name='mark_complete'),
    path('recalculate-priorities/', views.recalculate_priorities, name='recalculate_priorities'),
]



