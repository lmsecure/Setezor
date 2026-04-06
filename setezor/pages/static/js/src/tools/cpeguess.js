const cpeModalWindow = {
    modalId: 'cpeModalWindow',
    modalData: null,
    
    getConfig: function() {
        return {
            id: this.modalId,
            title: i18next.t('CPEGuess'),
            size: 'xl',
            helpUrl: 'https://help.setezor.net/%D0%98%D0%BD%D1%81%D1%82%D1%80%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B.html#cpeguess',
            staticBackdrop: true,
            keyboard: false,
            bodyContent: this.getBodyContent(),
            buttons: this.getButtons(),
            onClose: () => this.onClose()
        };
    },

    getBodyContent: function() {
        return `
            <div class="d-flex mb-2" id="agent_interface_bar_cpeguess">
                <div data-agent-bar="agent_cpeguess"></div>
                <div data-interface-bar="interface_cpeguess" class="ms-3"></div>
                <div id="scans_bar_cpeguess" class="ms-3"></div>
            </div>
            <div class="d-flex flex-column">
                <div class="tab-content" id="dsa" style="padding-top: 7px;">
                    <div class="p2 tab-content">
                        <div class="row d-flex flex-row">
                            <div class="col-3">
                                <form onsubmit="findCPE(event)" name="cpeFinderFormName" id="cpeFinder">
                                    <div class="mb-3">
                                        <label for="cpeVendorInput" class="form-label" data-i18n="Vendor"></label>
                                        <input type="text" class="form-control" id="cpeVendorInput" name="vendor">
                                    </div>
                                    <div class="mb-3">
                                        <label for="cpeProductInput" class="form-label" data-i18n="Product"></label>
                                        <input type="text" class="form-control" id="cpeProductInput" name="product" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="cpeVersionInput" class="form-label" data-i18n="Version"></label>
                                        <input type="text" class="form-control" id="cpeVersionInput" name="version" required>
                                    </div>
                                    <div class="form-check mb-3">
                                        <label for="cpeExactInput" class="form-check-label" data-i18n="Exact"></label>
                                        <input type="checkbox" class="form-check-input" id="cpeExactInput" name="mode">
                                    </div>
                                    <div class="btn-group d-flex my-2" role="group">
                                        <input class="btn btn-outline-secondary w-50" name="reset_params" type="reset" data-i18n-value="Reset Params">
                                        <button type="submit" class="btn btn-success w-50" data-i18n="Search"></button>
                                    </div>
                                </form>
                            </div>
                            <div class="col-9 overflow-auto" style="max-height: 500px;">
                                <h5>CPE's</h5>
                                <ul id="cpeList" class="list-group">
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    getButtons: function() {
        const modalId = this.modalId;
        return [
            {
                id: 'CloseCPE',
                text: i18next.t('Close'),
                class: 'btn-secondary',
                onClick: () => {
                    modalManager.destroyModal(modalId);
                }
            }
        ];
    },

    show: function() {
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

    onClose: function() {
        this.modalData = null;
    }
};

    async function findCPE(event) {
        event.preventDefault()
        let el = document.getElementById("cpeList")
        let data = new FormData(event.target)
        params = new URLSearchParams()

        el.innerHTML = `<div class="spinner-border" role="status">
                <span class="visually-hidden">${i18next.t('Loading...')}</span>
            </div>`
        for (const [key, value] of data) {
            params.set(key, value)
        }
        let resp = await fetch("/api/v1/vulnerability/cpe/?" + params)
        data = await resp.json()
        if (resp.status == 200) {
            let result = ""
            for (let cpe of data) {
                result += `<li class="list-group-item">${cpe}</li>`
            }
            el.innerHTML = result
        }else{
            create_toast('Error', data.error, 'error')
        }

    }