const CopyHandler = {
    /**
     * Обработчик копирования текста из input в буфер обмена
     * @param {Event} event - событие клика
     * @param {Object} options - дополнительные опции
     * @param {Function} options.onCopy - колбэк после копирования
     * @param {string} options.successClass - класс для успешного копирования (по умолчанию 'btn-success')
     * @param {number} options.resetTimeout - время сброса в мс (по умолчанию 2000)
     */
    handleCopy: function(event, options = {}) {
        const button = event.currentTarget;
        const inputGroup = button.closest('.input-group');
        
        if (!inputGroup) {
            console.error('Input group not found');
            return;
        }

        const input = inputGroup.querySelector('input');
        
        if (!input || !input.value) {
            console.error('Input not found or empty');
            return;
        }

        navigator.clipboard.writeText(input.value)
            .then(() => {
                this.showCopySuccess(button, options);
                if (options.onCopy) options.onCopy(button, input.value);
            })
            .catch(err => {
                console.error('Error copying to clipboard:', err);
                this.fallbackCopy(input.value, button);
            });
    },

    showCopySuccess: function(button, options) {
        const successClass = options.successClass || 'btn-success';
        const originalClass = button.className;
        const originalText = button.innerHTML;
        const originalTextContent = button.textContent;
        
        button.classList.remove('btn-outline-secondary');
        button.classList.add(successClass);
        
        if (window.i18next && window.i18next.t) {
            button.innerHTML = window.i18next.t('Copied!');
        } else {
            button.innerHTML = 'Copied!';
        }
        
        setTimeout(() => {
            button.className = originalClass;
            button.innerHTML = originalText;
            if (!originalText && originalTextContent) {
                button.textContent = originalTextContent;
            }
        }, options.resetTimeout || 2000);
    },

    fallbackCopy: function(text, button) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        
        try {
            document.execCommand('copy');
            this.showCopySuccess(button, {});
        } catch (err) {
            console.error('Fallback copy failed:', err);
            alert('Failed to copy to clipboard');
        }
        
        document.body.removeChild(textarea);
    },

    /**
     * Привязать обработчики копирования к кнопкам
     * @param {Object} buttonMap - объект с id кнопок и опциями
     */
    attachToButtons: function(buttonMap) {
        Object.entries(buttonMap).forEach(([buttonId, options]) => {
            const button = document.getElementById(buttonId);
            if (button) {
                const oldHandler = button._copyHandler;
                if (oldHandler) {
                    button.removeEventListener('click', oldHandler);
                }
                
                const handler = (e) => this.handleCopy(e, options);
                button._copyHandler = handler;
                button.addEventListener('click', handler);
            }
        });
    }
};

window.CopyHandler = CopyHandler;