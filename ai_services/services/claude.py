"""
Claude AI Service.
Base class for all Claude API interactions.
"""

import json
import time
import hashlib
import logging
from typing import Any, Dict, List, Optional, Union
from django.conf import settings

from core.services.base import BaseService, ServiceResult
from ..models import AIRequestLog


logger = logging.getLogger(__name__)


class ClaudeService(BaseService):
    """
    Base service class for Claude AI interactions.
    Provides common functionality for all AI services.
    """
    
    def __init__(self, user=None):
        super().__init__()
        self.user = user
        self.model = getattr(settings, 'AI_MODEL', 'claude-sonnet-4-20250514')
        self.max_tokens = getattr(settings, 'AI_MAX_TOKENS', 4096)
        self.timeout = getattr(settings, 'AI_TIMEOUT', 30)
        self._client = None
    
    @property
    def client(self):
        """
        Lazy-load the Anthropic client.
        """
        if self._client is None:
            try:
                import anthropic
                api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY is not configured")
                self._client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("anthropic package is not installed")
        return self._client
    
    def _create_request_hash(self, prompt: str, **kwargs) -> str:
        """
        Create a hash of the request for caching/deduplication.
        """
        content = f"{prompt}{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _log_request(
        self,
        service_type: str,
        status: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        response_time_ms: int = 0,
        error_message: str = "",
        request_hash: str = "",
        extra_data: Dict = None
    ) -> AIRequestLog:
        """
        Log an AI request.
        """
        return AIRequestLog.objects.create(
            user=self.user,
            service_type=service_type,
            model_name=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            status=status,
            response_time_ms=response_time_ms,
            error_message=error_message,
            request_hash=request_hash,
            extra_data=extra_data or {}
        )
    
    def send_message(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        service_type: str = "general",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> ServiceResult:
        """
        Send a message to Claude and get a response.
        
        Args:
            prompt: The user message/prompt
            system_prompt: Optional system prompt for context
            service_type: Type of service for logging
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0-1)
        
        Returns:
            ServiceResult with the AI response
        """
        request_hash = self._create_request_hash(prompt, system=system_prompt)
        start_time = time.time()
        
        try:
            # Build messages
            messages = [{"role": "user", "content": prompt}]
            
            # Make API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                system=system_prompt or "",
                messages=messages,
                temperature=temperature
            )
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract response content
            content = response.content[0].text if response.content else ""
            
            # Log successful request
            log = self._log_request(
                service_type=service_type,
                status=AIRequestLog.Status.SUCCESS,
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                response_time_ms=response_time_ms,
                request_hash=request_hash,
                extra_data={'model': self.model, 'temperature': temperature}
            )
            
            self.log_info(f"AI request successful: {service_type} ({response_time_ms}ms)")
            
            return ServiceResult.ok(
                data={
                    'content': content,
                    'tokens': {
                        'input': response.usage.input_tokens,
                        'output': response.usage.output_tokens,
                        'total': response.usage.input_tokens + response.usage.output_tokens
                    },
                    'log_id': log.id
                },
                message="AI yanıtı alındı"
            )
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            # Determine status based on error type
            status = AIRequestLog.Status.FAILED
            if 'timeout' in error_msg.lower():
                status = AIRequestLog.Status.TIMEOUT
            
            # Log failed request
            self._log_request(
                service_type=service_type,
                status=status,
                response_time_ms=response_time_ms,
                error_message=error_msg,
                request_hash=request_hash
            )
            
            self.log_error(f"AI request failed: {error_msg}", exc=e)
            
            return ServiceResult.fail(
                message="AI servisinden yanıt alınamadı",
                errors={'exception': error_msg},
                code="AI_ERROR"
            )
    
    def send_json_message(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        service_type: str = "general",
        **kwargs
    ) -> ServiceResult:
        """
        Send a message expecting a JSON response.
        Automatically parses the JSON from the response.
        """
        # Add JSON instruction to system prompt
        json_system = (system_prompt or "") + "\n\nYanıtınızı geçerli JSON formatında verin."
        
        result = self.send_message(
            prompt=prompt,
            system_prompt=json_system,
            service_type=service_type,
            **kwargs
        )
        
        if not result.success:
            return result
        
        try:
            # Extract JSON from response
            content = result.data['content']
            
            # Try to find JSON in the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                # Try array
                json_start = content.find('[')
                json_end = content.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = content[json_start:json_end]
                parsed = json.loads(json_str)
                result.data['parsed'] = parsed
            else:
                # Try to parse the entire content
                result.data['parsed'] = json.loads(content)
            
            return result
            
        except json.JSONDecodeError as e:
            self.log_error(f"Failed to parse JSON response: {e}")
            result.data['parsed'] = None
            result.data['parse_error'] = str(e)
            return result
    
    def is_available(self) -> bool:
        """
        Check if the AI service is available.
        """
        try:
            api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
            if not api_key:
                return False
            
            # Simple check - just verify the client can be created
            _ = self.client
            return True
        except Exception:
            return False
    
    def get_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get usage statistics for the past N days.
        """
        from django.utils import timezone
        from django.db.models import Sum, Count, Avg
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        logs = AIRequestLog.objects.filter(created_at__gte=start_date)
        
        stats = logs.aggregate(
            total_requests=Count('id'),
            successful_requests=Count('id', filter={'status': AIRequestLog.Status.SUCCESS}),
            total_tokens=Sum('total_tokens'),
            avg_response_time=Avg('response_time_ms')
        )
        
        # Calculate by service type
        by_service = logs.values('service_type').annotate(
            count=Count('id'),
            tokens=Sum('total_tokens')
        ).order_by('-count')
        
        return {
            'period_days': days,
            'total_requests': stats['total_requests'] or 0,
            'successful_requests': stats['successful_requests'] or 0,
            'success_rate': (
                (stats['successful_requests'] / stats['total_requests'] * 100)
                if stats['total_requests'] else 0
            ),
            'total_tokens': stats['total_tokens'] or 0,
            'avg_response_time_ms': round(stats['avg_response_time'] or 0, 2),
            'by_service': list(by_service)
        }

