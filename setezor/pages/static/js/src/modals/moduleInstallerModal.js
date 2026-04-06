class ModuleInstaller {
  constructor() {
    this.modalId = 'moduleInstallModal';
    this.currentResolve = null;
    this.currentReject = null;
    this.pendingAgentId = null;
    this.pendingModuleName = null;
    this.pendingDisplayName = null;
  }

  async prompt(agentId, moduleName, displayName = null) {
    return new Promise((resolve, reject) => {
      this.currentResolve = resolve;
      this.currentReject = reject;
      this.pendingAgentId = agentId;
      this.pendingModuleName = moduleName;
      this.pendingDisplayName = displayName;

      const agent = window.agentData?.agents?.find(a => a.id === agentId);
      const agentName = agent?.name || agentId;
      const label = displayName || moduleName;

      const modalConfig = {
        id: this.modalId,
        title: i18next.t('Module is not installed'),
        size: '',
        staticBackdrop: true,
        keyboard: false,
        zIndex: 1100,
        bodyContent: `
          <p id="moduleInstallMessage">${i18next.t('Module not installed', {
            moduleName: label,
            agentId: agentName
          })}</p>
          <div id="moduleInstallStatus" class="d-none text-muted small mt-2" data-i18n="Installing...">
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
          </div>
        `,
        buttons: [
          {
            id: 'cancel',
            text: i18next.t('Cancel'),
            class: 'btn-secondary',
            onClick: () => this.handleCancel()
          },
          {
            id: 'install',
            text: i18next.t('Install module'),
            class: 'btn-success',
            onClick: () => this.handleInstall()
          }
        ],
        onClose: () => {
          if (this.currentReject) {
            this.reset();
          }
        }
      };

      if (!window.modalManager.hasModal(this.modalId)) {
        window.modalManager.createModal(modalConfig);
      } else {
        document.getElementById('moduleInstallMessage').textContent = 
          i18next.t('Module not installed', { moduleName: label, agentId: agentName });
        
        window.modalManager.updateButton(this.modalId, 'install', {
          disabled: false,
          text: i18next.t('Install module')
        });
        
        document.getElementById('moduleInstallStatus').classList.add('d-none');
      }

      window.modalManager.showModal(this.modalId);
    });
  }

  async handleInstall() {
    const { pendingAgentId, pendingModuleName } = this;

    document.getElementById('moduleInstallStatus').classList.remove('d-none');
    
    window.modalManager.updateButton(this.modalId, 'install', {
      disabled: true,
      text: '<span class="spinner-border spinner-border-sm"></span>'
    });

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
      window.modalManager.hideModal(this.modalId, true);
    }
  }

  handleCancel() {
    window.modalManager.hideModal(this.modalId, true);
  }

  reset() {
    this.currentResolve = null;
    this.currentReject = null;
    this.pendingAgentId = null;
    this.pendingModuleName = null;
    this.pendingDisplayName = null;
  }

  onModuleInstalled(moduleName) {
    if (this.currentResolve && this.pendingModuleName === moduleName) {
      const label = this.pendingDisplayName || moduleName;
      create_toast(
        i18next.t('Install module'),
        i18next.t('Installation finished', { moduleName: label }),
        'success'
      );
      this.currentResolve(true);
      window.modalManager.hideModal(this.modalId, true);
      this.reset();
    }
  }
}

window.moduleInstaller = new ModuleInstaller();