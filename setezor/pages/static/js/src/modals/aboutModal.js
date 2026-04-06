// Для работы нужен copyHandler и modal_manager
const AboutModal = {
    modalId: 'aboutModal',
    modalData: null,
    
    getConfig: function() {
        return {
            id: this.modalId,
            title: i18next.t('About project'),
            size: '',
            staticBackdrop: true,
            keyboard: true,
            bodyContent: this.getBodyContent(),
            buttons: this.getButtons(),
            onClose: () => this.onClose()
        };
    },

    getBodyContent: function() {
        return `
            <div data-i18n="About Setezor text" style="margin-bottom: 0.5rem;"></div>
            
            <div class="list-group">
                <a href="https://setezor.net" class="list-group-item list-group-item-action list-group-item-success" 
                   target="_blank" data-i18n="Site">Site</a>
                <a href="https://t.me/lmsecurity" class="list-group-item list-group-item-action list-group-item-primary" 
                   target="_blank" data-i18n="Telegram">Telegram</a>
                <a href="https://github.com/lmsecure/Setezor" class="list-group-item list-group-item-action list-group-item-secondary" 
                   target="_blank" data-i18n="GitHub">GitHub</a>
                <a href="https://hub.docker.com/r/lmsecure/setezor" class="list-group-item list-group-item-action list-group-item-danger" 
                   target="_blank" data-i18n="DockerHub">DockerHub</a>
            </div>
            
            <hr>
            
            <div data-i18n="Donates" style="margin-top: 1rem; margin-bottom: 0.5rem; font-size: large;"></div>
            
            <div class="list-group">
                <span data-i18n="Bitcoin">Bitcoin:</span>
                <div class="input-group mb-3">
                    <input type="text" class="form-control" value="bc1qa2evk7khm246lhvljy8ujqu7m9m88gt84am9rz" disabled>
                    <button class="btn btn-outline-secondary" type="button" 
                            id="${this.modalId}_copyBitcoinBtn" data-i18n="Copy"></button>
                </div>
                
                <span data-i18n="Dash">Dash:</span>
                <div class="input-group mb-3">
                    <input type="text" class="form-control" value="XoJ3pBDG6f5L6NwoqUqg7dpeT9MHKcNtwT" disabled>
                    <button class="btn btn-outline-secondary" type="button" 
                            id="${this.modalId}_copyDashBtn" data-i18n="Copy"></button>
                </div>
            </div>
            
            <div class="modal-footer flex-row justify-content-between bd-highlight mb-3" style="padding: 1rem 0 0 0;">
                <h6 data-i18n="SetezorVersion"></h6>
            </div>
        `;
    },

    getButtons: function() {
        return [
            {
                id: 'CloseAbout',
                text: i18next.t('Close'),
                class: 'btn-secondary',
                onClick: () => {
                    modalManager.destroyModal(this.modalId);
                }
            }
        ];
    },

    show: function() {
        const showModal = () => {
            if (!modalManager.hasModal(this.modalId)) {
                this.modalData = modalManager.createModal(this.getConfig());
                
                this.attachCopyHandlers();
            } else {
                this.modalData = modalManager.modals.get(this.modalId);
            }
            
            modalManager.showModal(this.modalId);
            
            this.updateTranslations();
        };

        if (window.i18nReady) {
            showModal();
        } else {
            document.addEventListener('i18nReady', showModal, { once: true });
        }
    },

    updateTranslations: function() {
        if (window.updateContent) {
            setTimeout(() => {
                const modalBody = document.getElementById(`${this.modalId}_body`);
                if (modalBody) {
                    updateContent();
                }
            }, 50);
        }
    },

    attachCopyHandlers: function() {
        setTimeout(() => {
            if (window.CopyHandler) {
                CopyHandler.attachToButtons({
                    [`${this.modalId}_copyBitcoinBtn`]: {},
                    [`${this.modalId}_copyDashBtn`]: {}
                });
            }
        }, 100);
    },

    onClose: function() {
        this.modalData = null;
    }
};