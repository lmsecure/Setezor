const wappalyzerModalWindow = {
    modalId: 'wappalyzerModalWindow',
    modalData: null,
    
    getConfig: function() {
        return {
            id: this.modalId,
            title: 'Wappalyzer',
            size: '',
            helpUrl: 'https://help.setezor.net/%D0%98%D0%BD%D1%81%D1%82%D1%80%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B.html#wappalyzer',
            staticBackdrop: true,
            keyboard: true,
            bodyContent: this.getBodyContent(),
            buttons: this.getButtons(),
            onClose: () => this.onClose()
        };
    },

    getBodyContent: function() {
        return `
            <div class="d-flex mb-2" id="agent_interface_bar_wappalyzer">
                <div data-agent-bar="agent_wappalyzer"></div>
                <div data-interface-bar="interface_wappalyzer" class="ms-3"></div>
                <div id="scans_bar_wappalyzer" class="ms-3"></div>
            </div>
            <form id="wappalyzerScanForm" name="wappalyzerScanFormName" class="needs-validation"
                style="padding-top: 7px;" novalidate>
                <div class="tab-pane fade show active" id="v-pills-wappalyzer" role="tabpanel"
                    aria-labelledby="v-pills-wappalyzer-setting-tab" style="opacity: 1;">
                    <div class="flex-column">
                        <div class="py-2 bg-highlight">
                            <button type="button" class="btn btn-primary" id="wappalyzer_button_parse" disabled
                                style="min-width: 310px;" data-i18n="Parse wappalyzer logs">
                            </button>
                        </div>

                        <div class="btn-group" role="group" aria-label="Basic example">
                            <button type="button" class="btn btn-success" id="wappalyzer_select_all_btn" data-i18n="Select all"></button>
                            <button type="button" class="btn btn-danger" id="wappalyzer_clear_btn" data-i18n="Clear"></button>
                        </div>
                    </div>

                    <div class="container-fluid mt-2">
                        <div id="wappalyzer_groups">
                            <!--Wappalyzer content -->
                        </div>
                    </div>
                </div>
            </form>
        `;
    },

    getButtons: function() {
        return [
            {
                id: 'closeWappalyzerButton',
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
                
                this.attachEventHandlers();
                
                this.fetchWappalyzerGroups();
                
                const modalElement = this.modalData.element;
                modalElement.addEventListener('hidden.bs.modal', () => {
                    this.clearCategories();
                });
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

    attachEventHandlers: function() {
        document.getElementById('wappalyzer_button_parse').addEventListener('click', () => {
            this.startLogParse();
        });

        document.getElementById('wappalyzer_select_all_btn').addEventListener('click', () => {
            this.selectAll();
        });

        document.getElementById('wappalyzer_clear_btn').addEventListener('click', () => {
            this.clearCategories();
        });
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
    },

    async startLogParse() {
        const files = await this.selectFiles();
        if (!files.length) return;

        const results = await Promise.allSettled(files.map(file => this.uploadFile(file)));

        results.forEach((result) => {
            if (result.status === 'rejected') {
                create_toast('Error', result.reason.message, 'error');
            }
        });

        modalManager.hideModal(this.modalId, true);
    },

    async readFileAsDataURL(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = () => reject(new Error(`Not enough permissions. Check file owner: ${file.name}`));
            reader.readAsDataURL(file);
        });
    },

    async uploadFile(file) {
        const fileData = await this.readFileAsDataURL(file);

        const response = await fetch('/api/v1/task/wappalyzer_log_parse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file: fileData,
                agent_id: window.agentData?.default_agent || '',
                filename: file.name,
                groups: this.getSelectedGroups()
            })
        });

        if (!response.ok) {
            throw new Error(`Server error ${response.status} for file: ${file.name}`);
        }

        return response;
    },

    selectFiles() {
        return new Promise((resolve) => {
            const input = document.createElement('input');
            input.type = 'file';
            input.multiple = true;
            input.accept = '.json';
            input.onchange = (e) => resolve(Array.from(e.target.files));
            input.addEventListener('cancel', () => resolve([]));
            input.click();
        });
    },

    async fetchWappalyzerGroups() {
        try {
            const response = await axios.get('/api/v1/tasks_data/wappalyzer-groups');
            const data = response.data;
            this.renderWappalyzerGroups(data.wappalyzer_groups, data.wappalyzer_name_categories_by_group);
        } catch (error) {
            console.error('Error fetching Wappalyzer groups:', error);
        }
    },

    renderWappalyzerGroups(groups, categoriesByGroup) {
        const container = document.getElementById('wappalyzer_groups');
        if (!container) return;
        
        container.innerHTML = '';

        for (const [name, categoryIds] of Object.entries(groups)) {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'col';

            const formCheckDiv = document.createElement('div');
            formCheckDiv.className = 'form-check form-switch';
            formCheckDiv.setAttribute('data-bs-toggle', 'tooltip');
            formCheckDiv.setAttribute('data-bs-placement', 'right');

            const checkbox = document.createElement('input');
            checkbox.className = 'form-check-input shadow-none';
            checkbox.type = 'checkbox';
            checkbox.id = `wappgroup_${name}`;
            checkbox.addEventListener('change', () => this.elementChanged());

            const label = document.createElement('label');
            label.className = 'form-check-label';
            label.htmlFor = checkbox.id;
            label.title = categoriesByGroup[name] || '';
            label.textContent = name;

            formCheckDiv.appendChild(checkbox);
            formCheckDiv.appendChild(label);
            groupDiv.appendChild(formCheckDiv);
            container.appendChild(groupDiv);
        }
    },

    selectAll() {
        document.getElementById("wappalyzer_button_parse").disabled = false;
        const groups = document.getElementById("wappalyzer_groups");
        if (groups) {
            for (let element of groups.getElementsByClassName("form-check-input")) {
                element.checked = true;
            }
        }
    },

    clearCategories() {
        document.getElementById("wappalyzer_button_parse").disabled = true;
        const groups = document.getElementById("wappalyzer_groups");
        if (groups) {
            for (let element of groups.getElementsByClassName("form-check-input")) {
                element.checked = false;
            }
        }
    },

    elementChanged() {
        document.getElementById("wappalyzer_button_parse").disabled = true;
        const groups = document.getElementById("wappalyzer_groups");
        if (groups) {
            for (let element of groups.getElementsByClassName("form-check-input")) {
                if (element.checked) {
                    document.getElementById("wappalyzer_button_parse").disabled = false;
                    break;
                }
            }
        }
    },

    getSelectedGroups() {
        let ids = [];
        const groups = document.getElementById("wappalyzer_groups");
        if (groups) {
            for (let element of groups.getElementsByClassName("form-check-input")) {
                if (element.checked) {
                    ids.push(element.id.split("_")[1]);
                }
            }
        }
        return ids;
    }
};