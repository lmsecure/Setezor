// Для работы нужен modal_manager
const addScanModal = {
    modalId: 'addScanModal',
    modalData: null,

    getConfig: function () {
        return {
            id: this.modalId,
            title: i18next.t('Add scan'),
            staticBackdrop: true,
            keyboard: true,
            bodyContent: this.getBodyContent(),
            buttons: this.getButtons(),
            zIndex: 1100,
            onClose: () => this.onClose()
        };
    },

    getBodyContent: function () {
        return `
            <div class="mb-3">
                <label for="scanNameID" class="col-form-label" data-i18n="Scan name"></label>
                <input type="text" class="form-control" id="scanNameID" name="name" required>
            </div>
            <div class="mb-3">
                <label for="scanDescriptionID" class="col-form-label" data-i18n="Description"></label>
                <input type="text" class="form-control" id="scanDescriptionID" name="description">
            </div>
        `;
    },

    getButtons: function () {
        return [
            {
                id: 'closeAddScan',
                text: i18next.t('Close'),
                class: 'btn-secondary',
                onClick: () => modalManager.destroyModal(this.modalId)
            },
            {
                id: 'submit',
                text: i18next.t('Add'),
                class: 'btn-primary',
                onClick: () => this.submit()
            }
        ];
    },

    submit: async function () {
        const name = document.getElementById('scanNameID').value.trim();
        const description = document.getElementById('scanDescriptionID').value.trim();

        if (!name) {
            document.getElementById('scanNameID').reportValidity();
            return;
        }

        modalManager.updateButton(this.modalId, 'submit', { disabled: true, text: i18next.t('Adding...') });

        const resp = await fetch('/api/v1/scan', {
            method: 'POST',
            headers: { 'Content-type': 'application/json' },
            body: JSON.stringify({ name, description })
        });

        if (resp.ok) {
            const [scans, currentScan] = await Promise.all([getScans(), getCurrentScan()]);
            redrawScanPickDropdown(scans, currentScan, window.SCAN_BAR_IDS);
            modalManager.destroyModal(this.modalId);
        } else {
            modalManager.updateButton(this.modalId, 'submit', { disabled: false, text: i18next.t('Add') });
        }
    },

    show: function () {
        const showModal = () => {
            if (!modalManager.hasModal(this.modalId)) {
                this.modalData = modalManager.createModal(this.getConfig());
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

    updateTranslations: function () {
        if (window.updateContent) {
            setTimeout(() => {
                const modalBody = document.getElementById(`${this.modalId}_body`);
                if (modalBody) updateContent();
            }, 50);
        }
    },

    onClose: function () {
        this.modalData = null;
    }
};