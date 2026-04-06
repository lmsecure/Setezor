// Для работы нужен copyHandler и modal_manager
const InviteToSetezorModal = {
    modalId: 'inviteToSetezorTokenModal',
    modalData: null,
    
    getConfig: function() {
        return {
            id: this.modalId,
            title: i18next.t('Registration token'),
            size: '',
            staticBackdrop: true,
            keyboard: false,
            bodyContent: this.getBodyContent(),
            buttons: this.getButtons(),
            onClose: () => this.onClose()
        };
    },

    getBodyContent: function() {
        // Используем сырой HTML без переводов, они применятся позже через updateContent
        return `
            <form id="${this.modalId}_form" onsubmit="InviteToSetezorModal.generateToken(event); return false;">
                <div class="mb-3">
                    <label for="${this.modalId}_count" class="col-form-label" data-i18n="Person count"></label>
                    <input type="number" id="${this.modalId}_count" min="1" class="form-control" name="count" value="1">
                    
                    <label for="${this.modalId}_token" class="col-form-label" data-i18n="Token"></label>
                    <div class="input-group mb-3">
                        <input type="text" class="form-control" name="invite_to_setezor_token" 
                               disabled id="${this.modalId}_token">
                        <button class="btn btn-outline-secondary" type="button" 
                                id="${this.modalId}_copyTokenBtn" data-i18n="Copy"></button>
                    </div>
                    
                    <label for="${this.modalId}_url" class="col-form-label" data-i18n="Registration link"></label>
                    <div class="input-group mb-3">
                        <input type="text" class="form-control" name="invite_to_setezor_url" 
                               id="${this.modalId}_url" readonly>
                        <button class="btn btn-outline-secondary" type="button" 
                                id="${this.modalId}_copyUrlBtn" data-i18n="Copy"></button>
                    </div>
                </div>
            </form>
        `;
    },

    getButtons: function() {
        return [
            {
                id: 'CloseInviteToSetezor',
                text: i18next.t('Close'),
                class: 'btn-secondary',
                onClick: () => {
                    modalManager.destroyModal(this.modalId);
                }
            },
            {
                text: i18next.t('Create'),
                class: 'btn-success',
                onClick: (modalData) => {
                    this.generateToken();
                }
            }
        ];
    },

    updateTranslations: function() {
        setTimeout(() => {
            const modalElement = document.getElementById(this.modalId);
            if (modalElement && window.updateContent) {
                updateContent();
                
                const modalTitle = modalElement.querySelector('.modal-title');
                if (modalTitle) {
                    modalTitle.textContent = i18next.t('Registration token');
                }
            }
        }, 50);
    },

    generateToken: async function(event) {
        if (event) event.preventDefault();
        
        const form = document.getElementById(`${this.modalId}_form`);
        if (!form) {
            console.error('Form not found');
            return;
        }

        const formData = new FormData(form);
        const tokenInput = document.getElementById(`${this.modalId}_token`);
        const urlInput = document.getElementById(`${this.modalId}_url`);
        
        if (!tokenInput || !urlInput) {
            console.error('Token or URL input not found');
            return;
        }
        
        try {
            const response = await fetch("/api/v1/auth/generate_register_token", {
                method: "POST",
                body: JSON.stringify(Object.fromEntries(formData)),
                headers: { "Content-type": "application/json" },
            });
            
            if (!response.ok) throw new Error("Network response was not ok");
            
            const data = await response.json();
            const baseUrl = window.location.origin;
            const registrationLink = `${baseUrl}/registration?token=${data.token}`;
            
            tokenInput.value = data.token;
            urlInput.value = registrationLink;
            
        } catch (error) {
            console.error("Error:", error);
            alert(i18next.t('Error generating token') + ": " + error.message);
        }
    },

    show: function() {
        const showModal = () => {
            if (!modalManager.hasModal(this.modalId)) {
                this.modalData = modalManager.createModal(this.getConfig());
                
                this.updateTranslations();
                
                this.attachCopyHandlers();
            } else {
                this.modalData = modalManager.modals.get(this.modalId);
                this.updateTranslations();
            }
            
            setTimeout(() => {
                this.resetFields();
            }, 100);
            
            modalManager.showModal(this.modalId);
        };

        if (window.i18nReady) {
            showModal();
        } else {
            document.addEventListener('i18nReady', showModal, { once: true });
        }
    },

    resetFields: function() {
        const countInput = document.getElementById(`${this.modalId}_count`);
        const tokenInput = document.getElementById(`${this.modalId}_token`);
        const urlInput = document.getElementById(`${this.modalId}_url`);
        
        if (countInput) countInput.value = 1;
        if (tokenInput) tokenInput.value = '';
        if (urlInput) urlInput.value = '';
    },

    attachCopyHandlers: function() {
        setTimeout(() => {
            if (window.CopyHandler) {
                CopyHandler.attachToButtons({
                    [`${this.modalId}_copyTokenBtn`]: {},
                    [`${this.modalId}_copyUrlBtn`]: {}
                });
            }
        }, 150);
    },

    onClose: function() {
        console.log('Invite modal closed');
        this.modalData = null;
    }
};