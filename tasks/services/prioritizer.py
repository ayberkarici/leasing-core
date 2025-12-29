"""
AI Task Prioritizer Service.
Uses Claude AI to analyze and prioritize tasks.
"""

import json
import logging
from django.db import models
from django.utils import timezone
from django.conf import settings

from ai_services.services.claude import ClaudeService
from ..models import Task, TaskStatus

logger = logging.getLogger(__name__)


class TaskPrioritizer:
    """
    AI destekli görev önceliklendirme servisi.
    Claude API kullanarak görevleri analiz eder ve öncelik skoru verir.
    """
    
    def __init__(self):
        self.claude_service = ClaudeService()
    
    def prioritize_tasks(self, user, force_recalculate=False):
        """
        Kullanıcının tüm bekleyen görevlerini AI ile önceliklendir.
        
        Args:
            user: User instance
            force_recalculate: True ise tüm görevleri yeniden hesapla
            
        Returns:
            List of updated tasks
        """
        tasks = Task.objects.filter(
            assigned_to=user,
            status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING_RESPONSE]
        ).select_related('customer')
        
        if not force_recalculate:
            # Sadece bugün güncellenmemiş görevleri al
            today = timezone.now().date()
            tasks = tasks.filter(
                models.Q(ai_priority_updated_at__isnull=True) |
                models.Q(ai_priority_updated_at__date__lt=today)
            )
        
        if not tasks.exists():
            return []
        
        # Prepare task data for AI
        task_data = self._prepare_task_data(tasks)
        
        # Get AI analysis
        try:
            ai_response = self._get_ai_prioritization(task_data)
            self._apply_ai_priorities(tasks, ai_response)
        except Exception as e:
            logger.error(f"AI prioritization failed: {e}")
            # Fallback to base priority calculation
            for task in tasks:
                task.ai_priority_score = task.calculate_base_priority()
                task.ai_priority_updated_at = timezone.now()
                task.save(update_fields=['ai_priority_score', 'ai_priority_updated_at'])
        
        return list(tasks)
    
    def prioritize_single_task(self, task):
        """
        Tek bir görevi AI ile önceliklendir.
        
        Args:
            task: Task instance
            
        Returns:
            Updated task
        """
        task_data = self._prepare_task_data([task])
        
        try:
            ai_response = self._get_ai_prioritization(task_data)
            self._apply_ai_priorities([task], ai_response)
        except Exception as e:
            logger.error(f"AI prioritization failed for task {task.id}: {e}")
            task.ai_priority_score = task.calculate_base_priority()
            task.ai_priority_updated_at = timezone.now()
            task.save(update_fields=['ai_priority_score', 'ai_priority_updated_at'])
        
        return task
    
    def _prepare_task_data(self, tasks):
        """
        AI için görev verilerini hazırla.
        """
        task_list = []
        today = timezone.now().date()
        
        for task in tasks:
            task_info = {
                'id': task.id,
                'title': task.title,
                'description': task.description[:500] if task.description else '',
                'type': task.get_task_type_display(),
                'status': task.get_status_display(),
                'manual_priority': task.get_manual_priority_display(),
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'days_until_due': task.days_until_due,
                'is_overdue': task.is_overdue,
                'created_days_ago': (today - task.created_at.date()).days,
            }
            
            if task.customer:
                task_info['customer'] = {
                    'company': task.customer.company_name,
                    'stage': task.customer.get_stage_display(),
                    'priority': task.customer.get_priority_display(),
                    'estimated_value': float(task.customer.estimated_value),
                }
            
            task_list.append(task_info)
        
        return task_list
    
    def _get_ai_prioritization(self, task_data):
        """
        Claude API'den önceliklendirme al.
        """
        prompt = f"""Aşağıdaki satış görevlerini analiz et ve her birine 0-100 arası bir öncelik skoru ver.

Önceliklendirme kriterleri:
1. Gecikmiş görevler en yüksek öncelik almalı (80-100)
2. Bugün veya yarın son tarihli görevler yüksek öncelik (70-90)
3. Yüksek değerli müşteriler (+10-20 bonus)
4. Kritik müşteri önceliği (+15 bonus)
5. Onay/Sözleşme tipi görevler (+10 bonus)
6. Manuel acil işaretli görevler (+20 bonus)

Görevler:
{json.dumps(task_data, ensure_ascii=False, indent=2)}

Her görev için aşağıdaki JSON formatında yanıt ver:
{{
    "priorities": [
        {{
            "task_id": <task_id>,
            "score": <0-100 arası skor>,
            "reasoning": "<kısa açıklama>"
        }}
    ]
}}

Sadece JSON yanıt ver, başka açıklama ekleme."""

        response = self.claude_service.send_message(
            prompt=prompt,
            system="Sen bir satış yönetimi asistanısın. Görevleri analiz edip önceliklendiriyorsun. Yanıtları Türkçe ver."
        )
        
        # Parse JSON response
        try:
            # Clean up response if needed
            response_text = response.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            raise
    
    def _apply_ai_priorities(self, tasks, ai_response):
        """
        AI önceliklerini görevlere uygula.
        """
        priority_map = {
            p['task_id']: p for p in ai_response.get('priorities', [])
        }
        
        now = timezone.now()
        
        for task in tasks:
            if priority_data := priority_map.get(task.id):
                task.ai_priority_score = min(100, max(0, priority_data['score']))
                task.ai_priority_reasoning = priority_data.get('reasoning', '')
                task.ai_priority_updated_at = now
                task.save(update_fields=[
                    'ai_priority_score', 
                    'ai_priority_reasoning', 
                    'ai_priority_updated_at'
                ])
    
    def get_priority_explanation(self, task):
        """
        Görevin öncelik açıklamasını döndür.
        
        Args:
            task: Task instance
            
        Returns:
            String explanation
        """
        if task.ai_priority_reasoning:
            return task.ai_priority_reasoning
        
        # Generate basic explanation
        reasons = []
        
        if task.is_overdue:
            reasons.append("⚠️ Görev gecikmiş durumda")
        elif task.days_until_due is not None:
            if task.days_until_due == 0:
                reasons.append("⏰ Son tarih bugün")
            elif task.days_until_due <= 3:
                reasons.append(f"📅 Son tarihe {task.days_until_due} gün kaldı")
        
        if task.customer:
            if task.customer.priority in ['high', 'critical']:
                reasons.append(f"🔥 {task.customer.get_priority_display()} öncelikli müşteri")
            if task.customer.estimated_value >= 100000:
                reasons.append(f"💰 Yüksek değerli müşteri")
        
        if task.manual_priority == 'urgent':
            reasons.append("🚨 Manuel olarak acil işaretlenmiş")
        
        return " • ".join(reasons) if reasons else "Normal öncelik"

