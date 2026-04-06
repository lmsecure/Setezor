class AgentManager {
    constructor(config = {}) {
        this.modalId = config.modalId || 'agentManagerModal';
        this.projectMode = config.projectMode ?? true;

        this.modalElement = null;
        this.modal = null;

        this.state = {
            currentStep: 'SELECT',
            selectedAgent: null,
            newAgentData: null,
            parentAgents: [],
            agentId: null,
            interfaces: [],
            modules: []
        };

        this.steps = {
            SELECT: new SelectStep(this),
            CREATE: new CreateStep(this),
            PARENTS: new ParentsStep(this),
            CONNECT: new ConnectStep(this),
            INTERFACES: new InterfacesStep(this),
            MODULES: new ModulesStep(this),
            ASSIGN: new AssignStep(this),
            FINISH: new FinishStep(this)
        };

        this.allowModalClose = false;
    }

    _mount() {
        this.createModal();
        this.modalElement = document.getElementById(this.modalId);
        this.modal = new bootstrap.Modal(this.modalElement);
        this.initEventListeners();
    }

    _unmount() {
        if (this.modal) {
            this.modal.dispose();
            this.modal = null;
        }
        if (this.modalElement) {
            this.modalElement.remove();
            this.modalElement = null;
        }

        document.querySelector('.modal-backdrop')?.remove();
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('overflow');
        document.body.style.removeProperty('padding-right');
    }


    createModal() {
        if (document.getElementById(this.modalId)) return;

        const modalHTML = `
            <div class="modal fade" id="${this.modalId}" tabindex="-1" aria-hidden="true" data-bs-backdrop="static" data-bs-keyboard="false">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title"></h5>
                            <button type="button" class="btn-close js-agent-modal-close" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="step-content" style="height: 270px; display: flex; flex-direction: column; overflow-y: auto;">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">${i18next.t('Loading...')}</span>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer step-footer d-flex justify-content-between"></div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    initEventListeners() {
        this.modalElement.addEventListener('show.bs.modal', () => {
            if (!this.state._autoCloseAfterInterfaces) {
                this.reset();
            }
        });

        this.modalElement.addEventListener('hidden.bs.modal', () => {
            delete this.state._autoCloseAfterInterfaces;
            delete this.state._useProjectInterfacesApi;
            if (typeof window.agent_table !== 'undefined') {
                window.agent_table.replaceData();
            }
            this._unmount();
        });

        this.modalElement.addEventListener('click', (e) => {
            if (e.target.closest('.js-agent-modal-close')) {
                const { mode, agentId, currentStep } = this.state;
                const stepsBeforeConnect = ['SELECT', 'CREATE', 'PARENTS'];
                const stepsAfterConnect = ['CONNECT', 'INTERFACES', 'MODULES', 'ASSIGN', 'FINISH'];

                if (mode === 'create' && agentId && stepsBeforeConnect.includes(currentStep)) {
                    this.showConfirmCloseModal();
                }
                else if (stepsAfterConnect.includes(currentStep)) {
                    this.showToast(
                        'Incomplete Setup',
                        i18next.t('Agent configuration is not complete. You can finish it later when connecting the agent to a project or in administrator settings.'),
                        'warning'
                    );
                    this.modal.hide();
                } else {
                    this.modal.hide();
                }
            }
        });
    }

    reset() {
        const startStep = (!this.projectMode && this.state.mode !== 'edit')
            ? 'CREATE'
            : 'SELECT';

        this.state = {
            currentStep: startStep,
            selectedAgent: null,
            newAgentData: null,
            parentAgents: [],
            agentId: null,
            interfaces: [],
            modules: []
        };
        this.renderStep();
    }

    renderStep() {
        const stepInstance = this.steps[this.state.currentStep];
        if (!stepInstance) {
            console.error(`Unknown step: ${this.state.currentStep}`);
            return;
        }

        const contentEl = this.modalElement.querySelector('.step-content');
        const footerEl = this.modalElement.querySelector('.step-footer');
        const closeBtn = this.modalElement.querySelector('.js-agent-modal-close');
        if (contentEl) contentEl.innerHTML = stepInstance.renderContent();
        if (footerEl) footerEl.innerHTML = stepInstance.renderFooter() || '';
        if (closeBtn) {
            closeBtn.style.display = this.state.currentStep === 'FINISH' ? 'none' : '';
        }
        stepInstance.init?.();
        this.updateHeader();
    }

    updateHeader() {
        const titleEl = this.modalElement.querySelector('.modal-title');
        if (!titleEl) return;

        const stepTitles = {
            SELECT: 'Select or Create Agent',
            CREATE: 'Create New Agent',
            PARENTS: 'Configure Parent Agents',
            CONNECT: 'Connect Agent',
            INTERFACES: 'Configure Interfaces',
            MODULES: 'Configure Modules',
            ASSIGN: 'Assign to project',
            FINISH: 'Setup Complete'
        };

        titleEl.textContent = i18next.t(stepTitles[this.state.currentStep] || 'Agent Manager');
    }

    goToStep(stepName) {
        if (this.steps[stepName]) {
            this.state.currentStep = stepName;
            this.renderStep();
        }
    }

    updateState(updates) {
        Object.assign(this.state, updates);
    }

    showToast(title, text, type = 'info') {
        if (typeof window.create_toast === 'function') {
            window.create_toast(i18next.t(title), i18next.t(text), type);
        } else {
            console.log(`[Toast] ${type}: ${title} - ${text}`);
        }
    }

    show(config = {}) {
        // Каждый раз монтируем свежий DOM
        this._mount();

        if (config.projectMode !== undefined) {
            this.projectMode = config.projectMode;
            const startStep = (!this.projectMode && this.state.mode !== 'edit')
                ? 'CREATE'
                : 'SELECT';
            this.state.currentStep = startStep;
        }
        this.modal.show();
    }

    showForInterfaceConfig(agentId) {
        if (!agentId) {
            this.showToast('Error', 'No agent selected', 'error');
            return;
        }

        // Монтируем перед показом
        this._mount();

        this.projectMode = true;
        this.state = {
            currentStep: 'INTERFACES',
            selectedAgent: null,
            newAgentData: null,
            parentAgents: [],
            agentId: agentId,
            interfaces: [],
            modules: [],
            _autoCloseAfterInterfaces: true,
            _useProjectInterfacesApi: true
        };

        this.renderStep();
        this.modal.show();
    }

    showConfirmCloseModal() {
        const existing = document.getElementById('agentCancelConfirmModal');
        if (existing) existing.remove();

        const modalHTML = `
            <div class="modal fade" id="agentCancelConfirmModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${i18next.t('Cancel Agent Creation')}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p>${i18next.t('Are you sure you want to cancel? The created agent will be deleted.')}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                ${i18next.t('Go back')}
                            </button>
                            <button type="button" class="btn btn-danger" id="confirm-agent-cancel">
                                ${i18next.t('Yes, cancel')}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        const confirmModal = new bootstrap.Modal(document.getElementById('agentCancelConfirmModal'));
        confirmModal.show();

        document.getElementById('confirm-agent-cancel').addEventListener('click', async () => {
            try {
                await fetch('/api/v1/agents/delete', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify([this.state.agentId])
                });
            } catch (err) {
            }
            this.allowModalClose = true;
            this.modal.hide();
            this.allowModalClose = false;

            confirmModal.hide();
        });
    }
}

// Базовый класс шага
class AgentManagerStep {
    constructor(manager) {
        this.manager = manager;
    }

    renderContent() {
        return '<p>Step content not implemented</p>';
    }

    renderFooter() {
        const backButton = this.hasBackButton()
            ? `<button class="btn btn-secondary" onclick="agentManager.goToStep('${this.getPrevStep()}')">${i18next.t('Back')}</button>`
            : '';

        const nextButton = this.hasNextButton()
            ? `<button class="btn btn-primary" onclick="${this.getNextHandler()}">${i18next.t('Next')}</button>`
            : '';

        const finishButton = this.hasFinishButton()
            ? `<button class="btn btn-success" onclick="agentManager.modal.hide()">${i18next.t('Finish')}</button>`
            : '';

        const primaryButton = finishButton || nextButton;

        return `
            <div class="d-flex w-100">
                <div>${backButton}</div>
                <div class="ms-auto">${primaryButton}</div>
            </div>
        `;
    }

    hasBackButton() { return this.manager.state.currentStep !== 'SELECT'; }
    hasNextButton() { return !this.hasFinishButton() && this.manager.state.currentStep !== 'FINISH'; }
    hasFinishButton() { return this.manager.state.currentStep === 'FINISH'; }
    getPrevStep() {
        const steps = Object.keys(this.manager.steps);
        const idx = steps.indexOf(this.manager.state.currentStep);
        return idx > 0 ? steps[idx - 1] : 'SELECT';
    }
    getNextHandler() { return `agentManager.goToStep('${this.getNextStep()}')`; }
    getNextStep() {
        const steps = Object.keys(this.manager.steps);
        const idx = steps.indexOf(this.manager.state.currentStep);
        return idx < steps.length - 1 ? steps[idx + 1] : 'FINISH';
    }
}

// === ШАГ 1: ВЫБОР АГЕНТА ===
class SelectStep extends AgentManagerStep {
    renderContent() {
        return `
            <div class="mb-3">
                <h5>${i18next.t('Available Agents')}</h5>
                <div id="agents-list" class="list-group mt-2" style="height: 145px; overflow-y: auto">${i18next.t('Loading...')}</div>
            </div>
            <hr>
            <button class="btn btn-outline-primary w-100" onclick="agentManager.goToStep('CREATE')">
                <i class="bi bi-plus-circle me-2"></i>${i18next.t('Create New Agent')}
            </button>
        `;
    }

    async init() {
        try {
            const allAgentsResp = await fetch("/api/v1/agents/settings");
            const allAgents = await allAgentsResp.json();
            this.manager.updateState({ allAgentNames: allAgents.map(a => a.name) });

            const connectableResp = await fetch("/api/v1/agents_in_project/settings/possible_agents");
            const connectableAgents = await connectableResp.json();

            const listEl = document.getElementById('agents-list');

            if (connectableAgents.length === 0) {
                listEl.innerHTML = `
                    <div class="alert alert-warning text-center">
                        ${i18next.t('No agents available for this project.')}
                    </div>
                `;
            } else {
                listEl.innerHTML = connectableAgents.map(agent => `
                    <button class="list-group-item list-group-item-action d-flex justify-content-between align-items-center agent-select-item"
                            data-agent-id="${agent.id}">
                        <div>
                            <strong>${agent.name}</strong><br>
                            <small class="text-muted">${agent.rest_url}</small>
                        </div>
                        <span class="badge bg-primary">${i18next.t('Select')}</span>
                    </button>
                `).join('');

                document.querySelectorAll('.agent-select-item').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const agentId = e.currentTarget.dataset.agentId;
                        const selected = connectableAgents.find(a => a.id == agentId);

                        this.manager.updateState({
                            mode: 'edit',
                            selectedAgent: selected,
                            agentId
                        });

                        this.manager.goToStep('INTERFACES');
                    });
                });
            }
        } catch (err) {
            document.getElementById('agents-list').innerHTML =
                `<div class="alert alert-danger">${i18next.t('Error loading agents')}</div>`;
            create_toast('Error', 'Failed to load agents list', 'error');
        }
    }

    hasBackButton() { return false; }
    hasNextButton() { return false; }
    renderFooter() { return ''; }
}

// === ШАГ 2: СОЗДАНИЕ АГЕНТА ===
class CreateStep extends AgentManagerStep {
    generateUniqueName(existingNames) {
        const baseName = "Agent";
        let counter = 1;
        while (existingNames.includes(`${baseName} ${counter}`)) {
            counter++;
        }
        return `${baseName} ${counter}`;
    }

    renderContent() {
        const existingNames = this.manager.state.allAgentNames || [];
        let suggestedName = this.generateUniqueName(existingNames);
        let currentDesc = '';
        let currentProtocol = 'https';
        let currentHost = '';
        let currentPort = '16662';
        const isEditMode = !!this.manager.state.newAgentData;

        if (isEditMode) {
            const agent = this.manager.state.newAgentData;
            suggestedName = agent.name || suggestedName;
            currentDesc = agent.description || '';
            try {
                const url = new URL(agent.rest_url);
                currentProtocol = url.protocol.replace(':', '');
                currentHost = url.hostname;
                currentPort = url.port || (currentProtocol === 'https' ? '443' : '80');
            } catch (e) {
                console.warn('Invalid rest_url format:', agent.rest_url);
            }
        }

        return `
            <form id="create-agent-form">
                <div class="mb-3">
                    <label for="new-agent-name" class="form-label" style="text-align: left;">${i18next.t('Agent name')}</label>
                    <input type="text" class="form-control" id="new-agent-name"
                        value="${this.escapeHtml(suggestedName)}" required>
                </div>

                <div class="mb-3">
                    <label for="new-agent-desc" class="form-label" style="text-align: left;">${i18next.t('Agent description')}</label>
                    <textarea class="form-control" id="new-agent-desc" rows="2">${this.escapeHtml(currentDesc)}</textarea>
                </div>

                <div class="mb-1">
                    <label class="form-label">${i18next.t('Address')}</label>
                    <div class="d-flex flex-wrap align-items-center gap-2">
                        <select class="form-select form-select-sm" id="new-agent-protocol" style="width: auto; min-width: 90px;">
                            <option value="http"${currentProtocol === 'http' ? ' selected' : ''}>HTTP</option>
                            <option value="https"${currentProtocol === 'https' ? ' selected' : ''}>HTTPS</option>
                        </select>
                        <input type="text" class="form-control form-control-sm"
                            id="new-agent-host"
                            value="${this.escapeHtml(currentHost)}"
                            placeholder="${i18next.t('Host or IP')}"
                            title="${i18next.t('Example: 192.168.1.100')}"
                            required
                            style="flex: 1; min-width: 160px;"
                        >
                        <input type="number" class="form-control form-control-sm"
                            id="new-agent-port"
                            value="${currentPort}"
                            min="1" max="65535"
                            required
                            style="width: 90px;">
                    </div>
                </div>
            </form>
        `;
    }

    init() {
        if (!this.manager.state.allAgentNames) {
            (async () => {
                try {
                    const resp = await fetch("/api/v1/agents/settings");
                    const allAgents = await resp.json();
                    const names = allAgents.map(a => a.name);
                    this.manager.updateState({ allAgentNames: names });
                    const nameInput = document.getElementById('new-agent-name');
                    if (nameInput && nameInput.value.startsWith('Agent ')) {
                        nameInput.value = this.generateUniqueName(names);
                    }
                } catch (e) {
                    console.error('Failed to load agent names', e);
                }
            })();
        }
    }

    escapeHtml(str) {
        if (!str) return '';
        return str.toString()
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    getNextHandler() {
        return 'agentManager.steps.CREATE.handleCreate()';
    }

    async handleCreate() {
        if (this.isCreating) return;

        const name = document.getElementById('new-agent-name').value.trim();
        const desc = document.getElementById('new-agent-desc').value.trim();
        const protocol = document.getElementById('new-agent-protocol').value;
        const host = document.getElementById('new-agent-host').value.trim();
        const port = document.getElementById('new-agent-port').value.trim();
        if (!name || !host || !port) {
            create_toast('Validation Error', 'Name, host and port are required', 'error');
            return;
        }

        const portNum = parseInt(port);
        if (isNaN(portNum) || portNum < 1 || portNum > 65535) {
            create_toast('Validation Error', 'Port must be between 1 and 65535', 'error');
            return;
        }

        this.isCreating = true;
        const url = `${protocol}://${host}:${port}`;
        const { agentId, mode } = this.manager.state;
        const isUpdate = agentId && mode === 'create';

        try {
            let resp;
            if (isUpdate) {
                resp = await fetch(`/api/v1/agents/${agentId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, description: desc, rest_url: url })
                });
            } else {
                resp = await fetch('/api/v1/agents', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, description: desc, rest_url: url })
                });
            }

            if (!resp.ok) {
                const errorData = await resp.json();
                throw new Error(errorData.detail || (isUpdate ? 'Update failed' : 'Creation failed'));
            }

            const agent = await resp.json();
            this.manager.updateState({
                newAgentData: agent,
                agentId: agent.id,
                mode: 'create'
            });

            create_toast(
                'Success',
                isUpdate ? 'Agent updated successfully' : 'Agent created successfully',
                'success'
            );

            this.manager.goToStep('PARENTS');
        } catch (err) {
            create_toast(
                isUpdate ? 'Update Error' : 'Creation Error',
                err.message,
                'error'
            );
        } finally {
            this.isCreating = false;
        }
    }

    hasBackButton() {
        return this.manager.projectMode;
    }
}

// === ШАГ 3: РОДИТЕЛЬСКИЕ АГЕНТЫ ===
class ParentsStep extends AgentManagerStep {
    renderContent() {
        return `
            <div class="mb-3">
                <h5>${i18next.t('Select Parent Agents')}</h5>
                <div id="parent-agents-container">${i18next.t('Loading...')}</div>
            </div>
        `;
    }

    async init() {
        const agentId = this.manager.state.agentId;
        try {
            const resp = await fetch(`/api/v1/agents/${agentId}/parents`);
            const parents = await resp.json();
            const container = document.getElementById('parent-agents-container');

            if (parents.length === 0) {
                container.innerHTML = `<div class="alert alert-info">${i18next.t('No parents available')}</div>`;
                this.updateNextButton(false);
                this.manager.updateState({ currentParentIds: [] });
                return;
            }
            const server = parents.find(p => p.name === "Server");
            const currentParentIds = [];

            const htmlItems = parents.map(p => {
                let checked = false;
                let disabled = false;

                if (p.is_parent) {
                    checked = true;
                    disabled = true;
                    currentParentIds.push(p.id);
                }
                else if (p.id === server?.id) {
                    checked = true;
                    currentParentIds.push(p.id);
                }

                return `
                    <div class="form-check mb-2">
                        <input class="form-check-input parent-agent-checkbox"
                               type="checkbox"
                               id="parent-${p.id}"
                               value="${p.id}"
                               ${checked ? 'checked' : ''}
                               ${disabled ? 'disabled' : ''}>
                        <label class="form-check-label ${disabled ? 'text-muted' : ''}"
                               for="parent-${p.id}">
                            ${this.escapeHtml(p.name)}
                        </label>
                    </div>
                `;
            });

            container.innerHTML = htmlItems.join('');
            this.manager.updateState({ currentParentIds });
            this.checkNextButton();

            document.querySelectorAll('.parent-agent-checkbox:not(:disabled)').forEach(checkbox => {
                checkbox.addEventListener('change', () => this.checkNextButton());
            });

        } catch (err) {
            container.innerHTML = `<div class="alert alert-danger">${i18next.t('Error loading parents')}</div>`;
            create_toast('Error', 'Failed to load parents', 'error');
            this.manager.updateState({ currentParentIds: [] });
            this.updateNextButton(false);
        }
    }

    escapeHtml(str) {
        if (!str) return '';
        return str.toString()
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    checkNextButton() {
        const selectedIds = Array.from(
            document.querySelectorAll('.parent-agent-checkbox:checked')
        ).map(cb => cb.value);

        this.manager.updateState({ currentParentIds: selectedIds });
        this.updateNextButton(selectedIds.length > 0);
    }

    updateNextButton(enabled) {
        const nextBtn = this.manager.modalElement.querySelector('.step-footer .btn-primary');
        if (nextBtn) {
            nextBtn.disabled = !enabled;
            nextBtn.title = enabled ? '' : i18next.t('At least one parent agent must be selected');
        }
    }

    getNextHandler() { return 'agentManager.steps.PARENTS.handleSaveParents()'; }

    async handleSaveParents() {
        const parentIds = this.manager.state.currentParentIds || [];
        if (parentIds.length === 0) return;

        try {
            await fetch(`/api/v1/agents/${this.manager.state.agentId}/parents`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    parents: Object.fromEntries(parentIds.map(id => [id, true]))
                })
            });
            this.manager.updateState({ parentAgents: parentIds });
            this.manager.goToStep('CONNECT');
        } catch (err) {
            create_toast('Save Error', err.message, 'error');
        }
    }

    hasNextButton() { return true; }
}

// === ШАГ 4: ПОДКЛЮЧЕНИЕ ===
class ConnectStep extends AgentManagerStep {
    constructor(manager) {
        super(manager);
        this.connectionError = null;
    }

    renderContent() {
        if (this.connectionError) {
            return `
                <div class="alert alert-danger d-flex align-items-start">
                    <i class="bi bi-exclamation-triangle-fill fs-4 me-2 mt-1"></i>
                    <div>
                        <h5 class="alert-heading mb-2">${i18next.t('Connection failed')}</h5>
                        <p class="mb-0 text-muted">
                            ${i18next.t('Please check agent settings and try again, or return to previous step to adjust configuration.')}
                        </p>
                    </div>
                </div>
            `;
        }
        return `
            <div class="text-center py-4">
                <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;"></div>
                <p class="text-muted">${i18next.t('Connecting to agent...')}</p>
            </div>
        `;
    }

    renderFooter() {
        if (this.connectionError) {
            return `
                <button class="btn btn-secondary" onclick="agentManager.goToStep('PARENTS')">
                    <i class="bi bi-arrow-left me-1"></i>${i18next.t('Return to configuration')}
                </button>
                <button class="btn btn-primary" onclick="agentManager.steps.CONNECT.init()">
                    <i class="bi bi-arrow-clockwise me-1"></i>${i18next.t('Retry connection')}
                </button>
            `;
        }
        return '';
    }

    async init() {
        this.connectionError = null;

        const contentEl = this.manager.modalElement.querySelector('.step-content');
        contentEl.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;"></div>
                <p class="text-muted">${i18next.t('Connecting to agent...')}</p>
            </div>
        `;

        try {
            const resp = await fetch(`/api/v1/agents/${this.manager.state.agentId}/connect`, {
                method: 'POST'
            });

            if (!resp.ok) {
                const errorData = await resp.json();
                throw new Error(errorData.detail || 'Connection failed');
            }

            create_toast('Success', 'Agent connected successfully', 'success');
            this.manager.goToStep('INTERFACES');
        } catch (err) {
            this.connectionError = err.message || 'Unknown connection error';
            contentEl.innerHTML = this.renderContent();
            const footerEl = this.manager.modalElement.querySelector('.step-footer');
            footerEl.innerHTML = this.renderFooter();
        }
    }

    hasBackButton() { return false; }
    hasNextButton() { return false; }
}

// === ШАГ 4: НАСТРОЙКА ИНТЕРФЕЙСОВ ===
class InterfacesStep extends AgentManagerStep {
    constructor(manager) {
        super(manager);
        this.originalActiveInterfaces = [];
        this.currentInterfaces = [];
    }

    renderContent() {
        return `
            <div class="mb-0">
                <h5>${i18next.t('Agent Interfaces')}</h5>
                <div id="interfaces-list-container" class="text-center py-2">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">${i18next.t('Loading...')}</span>
                    </div>
                </div>
            </div>
        `;
    }

    async init() {
        const agentId = this.manager.state.agentId;
        const container = document.getElementById('interfaces-list-container');

        try {
            const resp = await fetch(`/api/v1/agents/${agentId}/interfaces`);
            if (!resp.ok) throw new Error('Failed to load interfaces');

            this.currentInterfaces = await resp.json();
            this.originalActiveInterfaces = this.currentInterfaces
                .filter(i => i.is_already_enabled)
                .map(i => ({ name: i.name, ip: i.ip, mac: i.mac }));

            this.renderInterfaceList(container);
        } catch (err) {
            container.innerHTML = `<div class="alert alert-danger">${i18next.t('Failed to load interfaces')}</div>`;
            create_toast('Error', 'Failed to load interfaces', 'error');
        }
    }

    renderInterfaceList(container) {
        if (!this.currentInterfaces.length) {
            container.innerHTML = `<div class="alert alert-info mb-0" data-i18n="No interfaces found"></div>`;
            return;
        }

        const selectAllHTML = `
            <label class="card bg-light mb-2 shadow-sm">
                <div class="card-body py-2">
                    <div class="form-check mb-0 d-block text-start">
                        <input class="form-check-input" type="checkbox" id="interfacesSelectAll">
                        <label class="form-check-label d-inline" for="interfacesSelectAll">${i18next.t('Select all')}</label>
                    </div>
                </div>
            </label>
        `;

        let listContent = `<div class="list-group list-group-flush">`;
        this.currentInterfaces.forEach((iface, index) => {
            const id = `iface-${index}`;
            const checked = iface.is_already_enabled ? "checked" : "";
            const disabled = iface.is_already_enabled ? "disabled" : "";
            const badge = iface.is_already_enabled ?
                `<span class="badge bg-success ms-2" data-i18n="Active"></span>` : "";

            listContent += `
                <div class="list-group-item py-2 ${!disabled ? 'cursor-pointer' : ''}"
                     style="${!disabled ? 'cursor: pointer;' : ''}">
                    <div class="form-check mb-0 d-flex align-items-center">
                        <input class="form-check-input me-2 interface-checkbox"
                               type="checkbox" id="${id}"
                               name="${iface.name}" ip="${iface.ip}" mac="${iface.mac}"
                               ${checked} ${disabled}>
                        <label class="form-check-label flex-grow-1 mb-0">
                            <div class="d-flex justify-content-between">
                                <span class="fw-medium">${iface.ip || "—"}</span>
                                <small class="text-muted">${iface.name || "—"}</small>
                            </div>
                            ${badge}
                        </label>
                    </div>
                </div>
            `;
        });
        listContent += `</div>`;

        const scrollWrapper = `
            <div style="max-height: 200px; overflow-y: auto; overscroll-behavior: contain;">
                ${listContent}
            </div>
        `;
        container.innerHTML = selectAllHTML + scrollWrapper;

        const selectAll = document.getElementById("interfacesSelectAll");
        const checkboxes = Array.from(container.querySelectorAll(".interface-checkbox:not(:disabled)"));
        selectAll.disabled = checkboxes.length === 0;

        container.querySelectorAll(".list-group-item").forEach(item => {
            item.addEventListener("click", (e) => {
                if (e.target.closest('input[type="checkbox"]')) return;
                const checkbox = item.querySelector("input[type='checkbox']:not(:disabled)");
                if (checkbox) {
                    checkbox.checked = !checkbox.checked;
                    checkbox.dispatchEvent(new Event("change"));
                }
            });
        });

        selectAll.addEventListener("change", () => {
            checkboxes.forEach(cb => cb.checked = selectAll.checked);
        });

        checkboxes.forEach(cb => {
            cb.addEventListener("change", () => {
                const allChecked = checkboxes.every(c => c.checked);
                const someChecked = checkboxes.some(c => c.checked);
                selectAll.checked = allChecked;
                selectAll.indeterminate = !allChecked && someChecked;
            });
        });
    }

    getNextHandler() {
        return 'agentManager.steps.INTERFACES.handleSaveInterfaces()';
    }

    areInterfacesEqual(arr1, arr2) {
        if (arr1.length !== arr2.length) return false;
        const normalize = arr => arr
            .map(i => `${i.name}|${i.ip}|${i.mac}`)
            .sort()
            .join('|');
        return normalize(arr1) === normalize(arr2);
    }

    async handleSaveInterfaces() {
        const checkboxes = document.querySelectorAll('.interface-checkbox:checked');
        const selectedInterfaces = Array.from(checkboxes).map(cb => ({
            name: cb.name,
            ip: cb.getAttribute('ip'),
            mac: cb.getAttribute('mac')
        }));

        if (!this.areInterfacesEqual(selectedInterfaces, this.originalActiveInterfaces)) {
            try {
                const resp = await fetch(`/api/v1/agents/${this.manager.state.agentId}/interfaces`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(selectedInterfaces)
                });
                if (!resp.ok) throw new Error("Failed to save interfaces");
                create_toast("Success", "Interfaces saved", "success");
            } catch (err) {
                create_toast("Error", err.message || "Failed to save interfaces", "error");
                return;
            }
        } else {
            create_toast("Info", "No interface changes", "info");
        }

        if (this.manager.state._autoCloseAfterInterfaces) {
            if (typeof window.getInterfaceData === 'function' && window.agentData?.default_agent) {
                window.interfaceData = await window.getInterfaceData(window.agentData.default_agent);
            }
            document.querySelectorAll('[data-interface-bar]').forEach(bar => {
                if (typeof window.fillInterfaceBar === 'function') {
                    window.fillInterfaceBar(bar.getAttribute('data-interface-bar'));
                }
            });
            this.manager.modal.hide();
            return;
        }

        this.manager.goToStep('MODULES');
    }

    hasBackButton() { return false; }

    getPrevStep() {
        const { mode } = this.manager.state;
        return mode === 'edit' ? 'SELECT' : 'CONNECT';
    }
}

// === ШАГ 5: НАСТРОЙКА МОДУЛЕЙ ===
class ModulesStep extends AgentManagerStep {
    constructor(manager) {
        super(manager);
        this.originalInstalledModules = [];
        this.currentModules = [];
    }

    renderContent() {
        return `
            <div class="mb-0">
                <h5>${i18next.t('Agent Modules')}</h5>
                <div id="modules-list-container" class="text-center py-2">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">${i18next.t('Loading...')}</span>
                    </div>
                </div>
            </div>
        `;
    }

    async init() {
        const agentId = this.manager.state.agentId;
        const container = document.getElementById('modules-list-container');

        try {
            const resp = await fetch(`/api/v1/agents/show_available_modules/${agentId}`);
            if (!resp.ok) throw new Error('Failed to load modules');

            this.currentModules = await resp.json();
            this.originalInstalledModules = this.currentModules
                .filter(m => m.is_already_installed)
                .map(m => ({ name: m.name }));

            this.renderModuleList(container);
        } catch (err) {
            container.innerHTML = `<div class="alert alert-danger">${i18next.t('Failed to load modules')}</div>`;
            create_toast('Error', 'Failed to load modules', 'error');
        }
    }

    renderModuleList(container) {
        if (!this.currentModules.length) {
            container.innerHTML = `<div class="alert alert-info mb-0" data-i18n="No modules available"></div>`;
            return;
        }

        const selectAllHTML = `
            <label class="card bg-light mb-3 shadow-sm">
                <div class="card-body py-2">
                    <div class="form-check mb-0 text-start">
                        <input class="form-check-input" type="checkbox" id="modulesSelectAll">
                        <label class="form-check-label" for="modulesSelectAll">${i18next.t('Select all')}</label>
                    </div>
                </div>
            </label>
        `;

        let listContent = `<div class="list-group list-group-flush">`;
        this.currentModules.forEach((mod, index) => {
            const id = `mod-${index}`;
            const checked = mod.module_is_installed ? "checked" : "";
            const disabled = mod.module_is_installed ? "disabled" : "";
            const badge = mod.module_is_installed ?
                `<span class="badge bg-success ms-2" data-i18n="Installed"></span>` : "";

            listContent += `
                <div class="list-group-item py-2 ${!disabled ? 'cursor-pointer' : ''}"
                     style="${!disabled ? 'cursor: pointer;' : ''}">
                    <div class="form-check mb-0 d-flex align-items-center">
                        <input class="form-check-input me-2 module-checkbox"
                               type="checkbox" id="${id}"
                               name="${mod.module_name}"
                               ${checked} ${disabled}>
                        <label class="form-check-label flex-grow-1 mb-0">
                            <div class="d-flex justify-content-between">
                                <span class="fw-medium">${this.getModuleDisplayName(mod)}</span>
                            </div>
                            ${badge}
                        </label>
                    </div>
                </div>
            `;
        });
        listContent += `</div>`;

        const scrollWrapper = `
            <div style="max-height: 163px; overflow-y: auto; overscroll-behavior: contain;">
                ${listContent}
            </div>
        `;
        container.innerHTML = selectAllHTML + scrollWrapper;

        const selectAll = document.getElementById("modulesSelectAll");
        const checkboxes = Array.from(container.querySelectorAll(".module-checkbox:not(:disabled)"));
        selectAll.disabled = checkboxes.length === 0;

        container.querySelectorAll(".list-group-item").forEach(item => {
            item.addEventListener("click", (e) => {
                if (e.target.closest('input[type="checkbox"]')) return;
                const checkbox = item.querySelector("input[type='checkbox']:not(:disabled)");
                if (checkbox) {
                    checkbox.checked = !checkbox.checked;
                    checkbox.dispatchEvent(new Event("change"));
                }
            });
        });

        selectAll.addEventListener("change", () => {
            checkboxes.forEach(cb => cb.checked = selectAll.checked);
        });

        checkboxes.forEach(cb => {
            cb.addEventListener("change", () => {
                const allChecked = checkboxes.every(c => c.checked);
                const someChecked = checkboxes.some(c => c.checked);
                selectAll.checked = allChecked;
                selectAll.indeterminate = !allChecked && someChecked;
            });
        });
    }

    getNextHandler() {
        return 'agentManager.steps.MODULES.handleSaveModules()';
    }

    getModuleDisplayName(mod) {
        if (mod.description) {
            try {
                const parsed = typeof mod.description === 'string'
                    ? JSON.parse(mod.description)
                    : mod.description;
                if (parsed?.name) return parsed.name;
            } catch (e) {}
        }
        return mod.task_name || mod.module_name || 'Unknown';
    }

    areModulesEqual(arr1, arr2) {
        if (arr1.length !== arr2.length) return false;
        const normalize = arr => arr
            .map(m => m.name)
            .sort()
            .join('|');
        return normalize(arr1) === normalize(arr2);
    }

    async handleSaveModules() {
        const checkboxes = document.querySelectorAll('.module-checkbox:checked');
        const selectedModules = Array.from(checkboxes).map(cb => ({
            name: cb.name
        }));

        if (!this.areModulesEqual(selectedModules, this.originalInstalledModules)) {
            try {
                const toInstall = selectedModules
                    .filter(sel => !this.originalInstalledModules.some(orig => orig.name === sel.name))
                    .map(m => m.name);

                if (toInstall.length > 0) {
                    await fetch('/api/v1/task/push_module', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            agent_id: this.manager.state.agentId,
                            module_names: toInstall
                        })
                    });
                }
            } catch (err) {
                create_toast("Error", err.message || "Failed to install modules", "error");
                return;
            }
        } else {
            create_toast("Info", "No module changes", "info");
        }

        const nextStep = this.manager.projectMode ? 'ASSIGN' : 'FINISH';
        this.manager.goToStep(nextStep);
    }
}

// === ШАГ 6: ДОБАВЛЕНИЕ В ПРОЕКТ ===
class AssignStep extends AgentManagerStep {
    constructor(manager) {
        super(manager);
        this.assignError = null;
    }

    renderContent() {
        if (this.assignError) {
            return `
                <div class="alert alert-danger d-flex align-items-start">
                    <i class="bi bi-exclamation-triangle-fill fs-4 me-2 mt-1"></i>
                    <div>
                        <h5 class="alert-heading mb-2">${i18next.t('Assignment failed')}</h5>
                        <p class="mb-2">${this.assignError}</p>
                        <p class="mb-0 text-muted">
                            ${i18next.t('Please try again or contact support.')}
                        </p>
                    </div>
                </div>
            `;
        }
        return `
            <div class="text-center py-4">
                <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;"></div>
                <p class="text-muted">${i18next.t('Assigning agent to project...')}</p>
            </div>
        `;
    }

    renderFooter() {
        if (this.assignError) {
            return `
                <button class="btn btn-secondary" onclick="agentManager.goToStep('${this.getPrevStep()}')">
                    <i class="bi bi-arrow-left me-1"></i>${i18next.t('Back')}
                </button>
                <button class="btn btn-primary" onclick="agentManager.steps.ASSIGN.init()">
                    <i class="bi bi-arrow-clockwise me-1"></i>${i18next.t('Retry')}
                </button>
            `;
        }
        return '';
    }

    getPrevStep() {
        return 'MODULES';
    }

    async init() {
        this.assignError = null;

        const contentEl = this.manager.modalElement.querySelector('.step-content');
        contentEl.innerHTML = this.renderContent();

        try {
            const agentsData = {
                agents: {
                    [this.manager.state.agentId]: true
                }
            };

            const resp = await fetch('/api/v1/agents_in_project/settings/possible_agents', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(agentsData)
            });

            if (!resp.ok) {
                const errorData = await resp.json();
                throw new Error(errorData.detail || 'Assignment failed');
            }

            create_toast('Success', 'Agent assigned to project successfully', 'success');
            if (this.manager.state.mode === 'edit') {
                document.dispatchEvent(new CustomEvent('agentManagerFinish', {
                    detail: { agentId: this.manager.state.agentId }
                }));
                this.manager.modal.hide();
            } else {
                this.manager.goToStep('FINISH');
            }
            return;
        } catch (err) {
            this.assignError = err.message || 'Unknown assignment error';
            contentEl.innerHTML = this.renderContent();
            const footerEl = this.manager.modalElement.querySelector('.step-footer');
            footerEl.innerHTML = this.renderFooter();
        }
    }

    hasBackButton() { return false; }
    hasNextButton() { return false; }
}

// === ШАГ 7: ЗАВЕРШЕНИЕ ===
class FinishStep extends AgentManagerStep {
    renderContent() {
        const message = this.manager.projectMode
            ? 'The agent is now active in your project'
            : 'The agent is now ready to use';
        return `
            <div class="text-center py-4">
                <div class="mb-3">
                    <i class="bi bi-check-circle-fill text-success" style="font-size: 4rem;"></i>
                </div>
                <h4>${i18next.t('Agent Successfully Configured!')}</h4>
                <p class="text-muted">${i18next.t(message)}</p>
            </div>
        `;
    }

    init() {
        document.dispatchEvent(new CustomEvent('agentManagerFinish', {
            detail: { agentId: this.manager.state.agentId }
        }));
    }

    hasBackButton() { return false; }
    hasNextButton() { return false; }
    hasFinishButton() { return true; }
}

// === ИНИЦИАЛИЗАЦИЯ ===
document.addEventListener('DOMContentLoaded', () => {
    window.agentManager = new AgentManager({ modalId: 'agentManagerModal' });

    const connectBtn = document.querySelector('[data-testid="connect-agents"]');
    if (connectBtn) {
        connectBtn.removeAttribute('onclick');
        connectBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.agentManager.show();
        });
    }

    const observer = new MutationObserver(() => {
        const btn = document.querySelector('[data-testid="connect-agents"]:not([data-agent-manager-bound])');
        if (btn) {
            btn.removeAttribute('onclick');
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                window.agentManager?.show();
            });
            btn.setAttribute('data-agent-manager-bound', 'true');
            observer.disconnect();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
});