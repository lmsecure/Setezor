const ScapyUI = {
  getStyles() {
    return `
      <style>
        .scapy-action-btn { margin-bottom: 1rem; }
        .scapy-divider { margin: 1.5rem 0; border-top: 1px solid #e9ecef; }
      </style>
    `;
  },
  buildParams(prefix) {
    return `
      ${this.getStyles()}
      <div class="scapy-action-btn">
        <button type="button" id="${prefix}startSniff" class="btn btn-primary w-100" data-i18n="Start sniffing">
          Start sniffing
        </button>
      </div>
      <div class="scapy-divider"></div>
      <div>
        <button type="button" id="${prefix}parsePcap" class="btn btn-outline-primary w-100" data-i18n="Parse pcap logs">
          Parse pcap logs
        </button>
      </div>
    `;
  }
};

const ScapyHandlers = {
  async parsePcapFiles(files, agentId) {
    for (const file of files) {
      try {
        const content = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = e => resolve(e.target.result);
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });
        
        await fetch('/api/v1/task/scapy_parse_task', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file: content, agent_id: agentId, filename: file.name })
        });
      } catch (err) {
        console.error('Parse error:', err);
        create_toast('Error', 'Not enough permissions. Check file owner', 'error');
      }
    }
  }
};

class ScapyScanner {
  constructor(prefix) { this.prefix = prefix; }

  getBaseParams() {
    const agentId = 
        this.instance?.state?.overrides?.agent_id || 
        window.agentData?.default_agent;
    
    const iface = 
        this.instance?.state?.overrides?.interface_obj || 
        window.interfaceData?.default_interface || 
        window.getIface?.();
    
    if (!agentId) throw new Error('Please select an Agent');
    if (!iface?.name) throw new Error('Please select an Interface');
    
    return { agent_id: String(agentId), iface: iface.name };
  }

  async startSniff() {
    const payload = this.getBaseParams();
    const result = await window.executeToolTasks({
      tasks: [{ endpoint: '/api/v1/task/scapy_sniff_task', payload }],
      stopOnFirstFailure: true
    });
    if (!result.success && result.reason !== 'module_install_requested') {
      throw new Error(result.error?.message || 'Scapy sniff failed');
    }
    return result;
  }
}

const scapyModalConfig = {
  prefix: 'scapy_',
  tabs: [],
  hideActionButtons: true,
  toolParams: (prefix) => ScapyUI.buildParams(prefix),

  getTargets() { return []; },

  onInit(instance) {
    const prefix = instance.prefix;

    document.getElementById(`${prefix}startSniff`)?.addEventListener('click', async () => {
      try {
        const scanner = new ScapyScanner(prefix);
        scanner.instance = instance;
        const result = await scanner.startSniff();
        if (result !== null) window[`close_${instance.modalId}`]();
      } catch (err) {
        console.error('Sniff error:', err);
        create_toast('Error', err.message || 'Failed to start sniffing', 'error');
      }
    });

    document.getElementById(`${prefix}parsePcap`)?.addEventListener('click', async () => {
      const agentId = instance.state.overrides?.agent_id || window.agentData?.default_agent;
      if (!agentId) {
        create_toast('Warning', 'Please select an Agent first', 'warning');
        return;
      }

      const input = document.createElement('input');
      input.type = 'file';
      input.multiple = true;
      input.accept = '.pcap';
      
      input.onchange = async (e) => {
        await ScapyHandlers.parsePcapFiles(Array.from(e.target.files), agentId);
        window[`close_${instance.modalId}`]();
      };
      input.click();
    });

    window.scapy_full_modal_window = () => {
      instance.reset();
      window[`show_${instance.modalId}`]();
    };

    window.startScapyWithPrefill = (agentId, ifaceName) => {
        instance.state.overrides.agent_id = agentId;
        
        const iface = interfaceData?.interfaces?.find(i => i.name === ifaceName);
        if (iface) {
            instance.state.overrides.interface_obj = iface;
            instance.state.overrides.interface_id = String(iface.id);
            instance.reset();
            window[`show_${instance.modalId}`]();
            return;
        }
        
        window.getInterfaceData(agentId).then(ifaceData => {
            if (ifaceData?.interfaces) {
            const found = ifaceData.interfaces.find(i => i.name === ifaceName);
            if (found) {
                instance.state.overrides.interface_obj = found;
                instance.state.overrides.interface_id = String(found.id);
            }
            }
            instance.reset();
            window[`show_${instance.modalId}`]();
        });
    };
  },

  onReset(instance) {
    // Нечего сбрасывать, таргетов нет
  },

  async onStart(instance) {
    create_toast('Info', 'Use the action buttons below to start sniffing or parse pcap', 'info');
  }
};

window.openScapyModal = function () {
  if (document.getElementById('scapyModalWindow')) {
    show_scapyModalWindow();
    return;
  }
  createModal('scapyModalWindow', 'Scapy Tool', 'https://help.setezor.net/%D0%98%D0%BD%D1%81%D1%82%D1%80%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B.html#scapy');
  ToolModalBuilder.register('scapyModalWindow', scapyModalConfig);
  show_scapyModalWindow();
};