/**
 * Document Validation JavaScript
 * Real-time validation feedback
 */

class DocumentValidator {
    constructor(options = {}) {
        this.apiEndpoint = options.apiEndpoint || '/api/documents/validate/';
        this.pollInterval = options.pollInterval || 3000;
        this.maxRetries = options.maxRetries || 10;
        this.onValidationComplete = options.onValidationComplete || (() => {});
        this.onValidationError = options.onValidationError || (() => {});
        this.onProgress = options.onProgress || (() => {});
        
        this.currentJobId = null;
        this.retryCount = 0;
    }
    
    /**
     * Start document validation
     * @param {number} documentId - Document ID to validate
     */
    async startValidation(documentId) {
        this.retryCount = 0;
        
        try {
            const response = await fetch(`${this.apiEndpoint}${documentId}/start/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (!response.ok) {
                throw new Error('Validation start failed');
            }
            
            const data = await response.json();
            this.currentJobId = data.job_id;
            
            this.onProgress({
                status: 'started',
                message: 'Belge analizi başladı...',
                progress: 10
            });
            
            // Start polling for results
            this.pollForResults(documentId);
            
        } catch (error) {
            this.onValidationError(error);
        }
    }
    
    /**
     * Poll for validation results
     * @param {number} documentId - Document ID
     */
    async pollForResults(documentId) {
        if (this.retryCount >= this.maxRetries) {
            this.onValidationError(new Error('Validation timeout'));
            return;
        }
        
        try {
            const response = await fetch(`${this.apiEndpoint}${documentId}/status/`);
            
            if (!response.ok) {
                throw new Error('Status check failed');
            }
            
            const data = await response.json();
            
            if (data.status === 'completed') {
                this.onProgress({
                    status: 'completed',
                    message: 'Analiz tamamlandı!',
                    progress: 100
                });
                this.onValidationComplete(data.results);
                return;
            }
            
            if (data.status === 'failed') {
                this.onValidationError(new Error(data.error || 'Validation failed'));
                return;
            }
            
            // Still processing
            this.onProgress({
                status: 'processing',
                message: data.message || 'Belge analiz ediliyor...',
                progress: Math.min(20 + (this.retryCount * 8), 90)
            });
            
            this.retryCount++;
            setTimeout(() => this.pollForResults(documentId), this.pollInterval);
            
        } catch (error) {
            this.retryCount++;
            if (this.retryCount < this.maxRetries) {
                setTimeout(() => this.pollForResults(documentId), this.pollInterval);
            } else {
                this.onValidationError(error);
            }
        }
    }
    
    /**
     * Get CSRF token from cookies
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

/**
 * Validation Results Renderer
 */
class ValidationResultsRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
    }
    
    render(results) {
        if (!this.container) return;
        
        const html = `
            <div class="validation-results">
                ${this.renderOverallScore(results)}
                ${this.renderFieldChecklist(results.fields)}
                ${this.renderMessages(results)}
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    renderOverallScore(results) {
        const score = results.overall_score || 0;
        const isValid = results.is_valid;
        
        let colorClass = 'bg-red-500';
        if (score >= 80) colorClass = 'bg-emerald-500';
        else if (score >= 50) colorClass = 'bg-amber-500';
        
        return `
            <div class="p-4 bg-slate-50 rounded-xl mb-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-slate-600">Tamamlanma Oranı</span>
                    <span class="text-sm font-bold">${score.toFixed(0)}%</span>
                </div>
                <div class="w-full bg-slate-200 rounded-full h-2.5">
                    <div class="${colorClass} h-2.5 rounded-full transition-all duration-500" style="width: ${score}%"></div>
                </div>
                <div class="mt-3 text-center">
                    ${isValid 
                        ? '<span class="text-emerald-600 font-medium">✓ Belge geçerli</span>'
                        : '<span class="text-amber-600 font-medium">⚠ İnceleme gerekli</span>'
                    }
                </div>
            </div>
        `;
    }
    
    renderFieldChecklist(fields) {
        if (!fields || fields.length === 0) return '';
        
        const fieldItems = fields.map(field => {
            const found = field.found;
            const bgClass = found ? 'bg-emerald-50' : 'bg-red-50';
            const iconClass = found ? 'text-emerald-500' : 'text-red-500';
            const icon = found
                ? '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
                : '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>';
            
            return `
                <div class="flex items-center justify-between p-3 rounded-lg ${bgClass}">
                    <div class="flex items-center">
                        <span class="${iconClass} mr-3">${icon}</span>
                        <div>
                            <p class="text-sm font-medium">${field.field_id || 'Alan'}</p>
                            ${field.value ? `<p class="text-xs text-slate-500">${field.value}</p>` : ''}
                            ${field.issue ? `<p class="text-xs text-red-600">${field.issue}</p>` : ''}
                        </div>
                    </div>
                    <span class="text-xs font-medium ${field.confidence >= 80 ? 'text-emerald-600' : 'text-amber-600'}">
                        ${field.confidence || 0}%
                    </span>
                </div>
            `;
        }).join('');
        
        return `
            <div class="mb-4">
                <h4 class="text-sm font-semibold text-slate-700 mb-3">Alan Kontrolü</h4>
                <div class="space-y-2">${fieldItems}</div>
            </div>
        `;
    }
    
    renderMessages(results) {
        let html = '';
        
        if (results.warnings && results.warnings.length > 0) {
            const warnings = results.warnings.map(w => `
                <div class="flex items-start p-2 bg-amber-50 rounded">
                    <span class="text-amber-500 mr-2">⚠</span>
                    <span class="text-sm text-amber-700">${w}</span>
                </div>
            `).join('');
            
            html += `
                <div class="mb-4">
                    <h4 class="text-sm font-semibold text-amber-700 mb-2">Uyarılar</h4>
                    <div class="space-y-2">${warnings}</div>
                </div>
            `;
        }
        
        if (results.errors && results.errors.length > 0) {
            const errors = results.errors.map(e => `
                <div class="flex items-start p-2 bg-red-50 rounded">
                    <span class="text-red-500 mr-2">✕</span>
                    <span class="text-sm text-red-700">${e}</span>
                </div>
            `).join('');
            
            html += `
                <div class="mb-4">
                    <h4 class="text-sm font-semibold text-red-700 mb-2">Hatalar</h4>
                    <div class="space-y-2">${errors}</div>
                </div>
            `;
        }
        
        if (results.recommendations && results.recommendations.length > 0) {
            const recs = results.recommendations.map(r => `<li>${r}</li>`).join('');
            html += `
                <div>
                    <h4 class="text-sm font-semibold text-slate-700 mb-2">Öneriler</h4>
                    <ul class="list-disc list-inside text-sm text-slate-600 space-y-1">${recs}</ul>
                </div>
            `;
        }
        
        return html;
    }
}

/**
 * Progress Indicator Component
 */
class ValidationProgressIndicator {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
    }
    
    show() {
        if (!this.container) return;
        this.container.classList.remove('hidden');
    }
    
    hide() {
        if (!this.container) return;
        this.container.classList.add('hidden');
    }
    
    update(progress) {
        if (!this.container) return;
        
        const progressBar = this.container.querySelector('.progress-bar');
        const message = this.container.querySelector('.progress-message');
        
        if (progressBar) {
            progressBar.style.width = `${progress.progress}%`;
        }
        
        if (message) {
            message.textContent = progress.message;
        }
    }
}

// Export for use
window.DocumentValidator = DocumentValidator;
window.ValidationResultsRenderer = ValidationResultsRenderer;
window.ValidationProgressIndicator = ValidationProgressIndicator;



