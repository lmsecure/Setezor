class ModuleInstaller {
  constructor() {
    this.modal = new bootstrap.Modal(document.getElementById('moduleInstallModal'));
    this.messageEl = document.getElementById('moduleInstallMessage');
    this.statusEl = document.getElementById('moduleInstallStatus');
    this.confirmBtn = document.getElementById('moduleInstallConfirmBtn');
    this.cancelBtn = document.getElementById('moduleInstallCancelBtn');

    this.currentResolve = null;
    this.currentReject = null;
    this.pendingAgentId = null;
    this.pendingModuleName = null;

    this.confirmBtn.addEventListener('click', () => this.handleInstall());
    this.cancelBtn.addEventListener('click', () => this.handleCancel());
    document.getElementById('moduleInstallModal').addEventListener('hidden.bs.modal', () => {
      if (this.currentReject) {
        //this.currentReject(new Error('Installation cancelled'));
        this.reset();
      }
    });
  }

  async prompt(agentId, moduleName) {
    return new Promise((resolve, reject) => {
      this.currentResolve = resolve;
      this.currentReject = reject;
      this.pendingAgentId = agentId;
      this.pendingModuleName = moduleName;

      this.confirmBtn.disabled = false;
      this.confirmBtn.innerHTML = i18next.t('Install module');
      this.statusEl.classList.add('d-none');

      const agent = window.agentData?.agents?.find(a => a.id === agentId);
      const agentName = agent?.name || agentId;

      this.messageEl.textContent = i18next.t('Module not installed', {
        moduleName,
        agentId: agentName
      });
      this.cancelBtn.innerHTML = i18next.t('Cancel');
      this.modal.show();
    });
  }

  async handleInstall() {
    const { pendingAgentId, pendingModuleName } = this;
    this.statusEl.classList.remove('d-none');
    this.confirmBtn.disabled = true;
    this.confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

    try {
      const resp = await fetch('/api/v1/task/push_module', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: pendingAgentId,
          module_names: [pendingModuleName]
        })
      });

      if (!resp.ok) throw new Error('Failed to start install');

    } catch (err) {
      console.error('Module install request failed:', err);
      create_toast(
        i18next.t('Install module'),
        i18next.t('Installation failed'),
        'error'
      );
      this.modal.hide();
    }
  }

  handleCancel() {
    this.modal.hide();
  }

  reset() {
    this.currentResolve = null;
    this.currentReject = null;
    this.pendingAgentId = null;
    this.pendingModuleName = null;
  }

  onModuleInstalled(moduleName) {
    if (
      this.currentResolve &&
      this.pendingModuleName === moduleName
    ) {
      create_toast(
        i18next.t('Install module'),
        i18next.t('Installation finished', { moduleName }),
        'success'
      );
      this.modal.hide();
      this.currentResolve(true);
      this.reset();
    }
  }
}

window.moduleInstaller = new ModuleInstaller();