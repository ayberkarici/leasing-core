"""
Tasks app views.
Task management views for sales dashboard.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Task, TaskStatus, TaskType
from .services import TaskService, TaskPrioritizer


class SalespersonRequiredMixin(LoginRequiredMixin):
    """Sadece satış elemanlarının erişebileceği view mixin."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.user_type not in ['salesperson', 'admin'] and not request.user.is_superuser:
            messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class TaskListView(SalespersonRequiredMixin, ListView):
    """Görev listesi görünümü."""
    
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20
    
    def get_queryset(self):
        filters = {
            'status': self.request.GET.get('status'),
            'task_type': self.request.GET.get('task_type'),
            'search': self.request.GET.get('search'),
        }
        return TaskService.get_tasks_for_user(self.request.user, filters)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Görevlerim'
        context['status_choices'] = TaskStatus.choices
        context['type_choices'] = TaskType.choices
        context['stats'] = TaskService.get_dashboard_stats(self.request.user)
        context['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'task_type': self.request.GET.get('task_type', ''),
            'search': self.request.GET.get('search', ''),
        }
        return context


class TaskDetailView(SalespersonRequiredMixin, DetailView):
    """Görev detay görünümü."""
    
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'
    
    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.user_type == 'admin':
            return Task.objects.all()
        return Task.objects.filter(assigned_to=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.object.title
        context['status_choices'] = TaskStatus.choices
        
        # Get priority explanation
        prioritizer = TaskPrioritizer()
        context['priority_explanation'] = prioritizer.get_priority_explanation(self.object)
        
        return context


class TaskCreateView(SalespersonRequiredMixin, CreateView):
    """Yeni görev oluşturma görünümü."""
    
    model = Task
    template_name = 'tasks/task_form.html'
    fields = [
        'title', 'description', 'task_type', 'manual_priority',
        'customer', 'due_date', 'reminder_date'
    ]
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.assigned_to = self.request.user
        response = super().form_valid(form)
        
        # Calculate initial priority
        self.object.ai_priority_score = self.object.calculate_base_priority()
        self.object.save()
        
        messages.success(self.request, 'Görev başarıyla oluşturuldu.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('tasks:task_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Yeni Görev'
        context['is_edit'] = False
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Sadece kullanıcının müşterilerini göster
        from customers.models import Customer
        form.fields['customer'].queryset = Customer.objects.filter(
            salesperson=self.request.user,
            is_active=True
        )
        return form


class TaskUpdateView(SalespersonRequiredMixin, UpdateView):
    """Görev düzenleme görünümü."""
    
    model = Task
    template_name = 'tasks/task_form.html'
    fields = [
        'title', 'description', 'task_type', 'status', 'manual_priority',
        'customer', 'due_date', 'reminder_date'
    ]
    
    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.user_type == 'admin':
            return Task.objects.all()
        return Task.objects.filter(assigned_to=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Recalculate priority if relevant fields changed
        self.object.ai_priority_score = self.object.calculate_base_priority()
        self.object.save()
        
        messages.success(self.request, 'Görev güncellendi.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('tasks:task_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'{self.object.title} - Düzenle'
        context['is_edit'] = True
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        from customers.models import Customer
        form.fields['customer'].queryset = Customer.objects.filter(
            salesperson=self.request.user,
            is_active=True
        )
        return form


@require_POST
def update_task_status(request, pk):
    """AJAX: Görev durumunu güncelle."""
    task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
    
    new_status = request.POST.get('status')
    
    if new_status not in dict(TaskStatus.choices):
        return JsonResponse({'error': 'Geçersiz durum'}, status=400)
    
    TaskService.update_task_status(task, new_status, request.user)
    
    return JsonResponse({
        'success': True,
        'status': new_status,
        'status_display': task.get_status_display(),
        'status_class': task.status_display_class,
    })


@require_POST
def mark_task_complete(request, pk):
    """AJAX: Görevi tamamlandı olarak işaretle."""
    task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
    
    task.mark_completed()
    
    return JsonResponse({
        'success': True,
        'status': 'completed',
        'status_display': task.get_status_display(),
    })


@require_POST
def recalculate_priorities(request):
    """AJAX: Tüm görevlerin önceliklerini yeniden hesapla."""
    count = TaskService.recalculate_priorities(request.user)
    
    return JsonResponse({
        'success': True,
        'message': f'{count} görevin önceliği yeniden hesaplandı.',
    })
