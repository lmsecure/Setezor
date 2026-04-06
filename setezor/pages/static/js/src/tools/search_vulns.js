const searchVulnsModalWindow = {
    modalId: 'searchVulnsModalWindow',
    modalData: null,
    
    getConfig: function() {
        return {
            id: this.modalId,
            title: 'SearchVulns',
            size: 'xl',
            helpUrl: 'https://help.setezor.net/%D0%98%D0%BD%D1%81%D1%82%D1%80%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B.html#searchvulns',
            staticBackdrop: true,
            keyboard: false,
            bodyContent: this.getBodyContent(),
            buttons: this.getButtons(),
            onClose: () => this.onClose()
        };
    },

    getBodyContent: function() {
        return `
            <div class="d-flex mb-2" id="agent_interface_bar_searchvulns">
                <div data-agent-bar="agent_searchvulns"></div>
                <div data-interface-bar="interface_searchvulns" class="ms-3"></div>
                <div id="scans_bar_searchvulns" class="ms-3"></div>
            </div>
            <div class="d-flex flex-column">
                <div class="tab-content" id="dsa" style="padding-top: 7px;">
                    <div class="p2 tab-content">
                        <div class="row">
                            <div class="col-3">
                                <div class="row">
                                    <form onsubmit="searchVulnsModalWindow.saveToken(event)" name="tokenSaveSearchVulnsFormName" id="tokenSaveFormSearchVulns" class="flex-column">
                                        <label for="cpeNameInput" class="form-label" data-i18n="Token"></label>
                                        <div class="mb-3 d-flex">
                                            <input type="text" class="form-control me-2" name="token" required>
                                            <button type="submit" class="btn btn-primary" data-i18n="Set"></button>
                                        </div>
                                    </form>
                                </div>
                                <div class="row">
                                    <form onsubmit="searchVulnsModalWindow.findVulnerabilities(event)" name="tokenSearchSearchVulnsFormName" id="tokenSearchFormSearchVulns">
                                        <div class="mb-3">
                                            <label for="queryInput" class="form-label" data-i18n="Query String"></label>
                                            <input type="text" class="form-control" name="query" id="queryInput" required>
                                        </div>
                                        <button type="submit" class="btn btn-success" data-i18n="Search"></button>
                                    </form>
                                </div>
                                <button class="btn btn-primary mt-2" onclick="searchVulnsModalWindow.refreshCVE()" data-i18n="Refresh CVE"></button>
                            </div>
                            <div class="col-9 overflow-auto" style="max-height: 700px;">
                                <h5>CVE's</h5>
                                <h6 id="softName"></h6>
                                <table class="table table-bordered">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th data-i18n="Description"></th>
                                            <th data-i18n="Links"></th>
                                        </tr>
                                    </thead>
                                    <tbody id="vulnsList">
                                    </tbody>
                                </table>
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
                id: 'CloseSearchVulns',
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
    },

    saveToken: async function(event) {
        event.preventDefault();
        let data = new FormData(event.target);
        const resp = await fetch("/api/v1/project/search_vulns_token", { 
            method: 'PUT', 
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(Object.fromEntries(data))
        });
        
        if (resp.status == 200) {
            create_toast('Success', 'Token was set', 'success');
        } else {
            create_toast('Error', 'Invalid token SearchVulns', 'error');
        }
    },

    findVulnerabilities: async function(event) {
        event.preventDefault();
        let el = document.getElementById("vulnsList");
        let data = new FormData(event.target);
        let params = new URLSearchParams();
        
        for (const [key, value] of data) {
            params.set(key, value);
        }
        
        const queryValue = params.get('query');
        
        el.innerHTML = `<div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>`;
            
        const resp = await fetch("/api/v1/vulnerability/search_vulns?" + params);
        
        if (resp.status == 500) {
            create_toast('Error', 'Invalid token', 'error');
            el.innerHTML = "";
            return;
        }
        
        const responseData = await resp.json();
        
        if (resp.status == 200) {
            let result = "";
            const dict_data = {[queryValue] : responseData};
            
            for (let [key, value] of Object.entries(dict_data)) {
                document.getElementById("softName").innerHTML = `${key}. Latest version: ${value.version_status.latest}`;
                
                for (let [k, v] of Object.entries(value.vulns)) {
                    result += `
                    <tr>
                        <td>${k}</td>
                        <td>${v.description}</td>
                        <td>`;
                    
                    if (v.exploits != undefined){
                        for (let link of v.exploits) {
                            result += `<p><a href="${link}">${link}</a></p>`;
                        }
                    }
                    result += `</td></tr>`;
                }
            }
            el.innerHTML = result;
        } else {
            create_toast('Error', responseData.error, 'error');
            el.innerHTML = "";
        }
    },

    refreshCVE: async function() {
        await fetch("/api/v1/task/refresh_cve", { method: "POST" });
        create_toast('Success', 'CVE refresh started', 'success');
    }
};