const SnmpUI = {
  getStyles() {
    return `
      <style>
        .snmp-target-dropdown { margin: 0.5rem 0 1rem; }
        .snmp-file-section { 
          background: #f8f9fa; 
          border-radius: 8px; 
          padding: 12px; 
          margin-bottom: 1rem;
          border: 1px solid #e9ecef;
        }
        .snmp-file-section h6 {
          font-size: 0.85rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: #6c757d;
          margin-bottom: 10px;
          font-weight: bold;
        }
      </style>
    `;
  },
  buildParams(prefix) {
    return `
      ${this.getStyles()}
      <div class="snmp-target-dropdown">
        <div class="dropdown w-100">
          <button class="btn btn-outline-secondary dropdown-toggle w-100" 
                  type="button" 
                  id="${prefix}targetDropdown" 
                  data-bs-toggle="dropdown"
                  data-i18n="Select target">
            Select target
          </button>
          <ul class="dropdown-menu w-100" id="${prefix}targetDropdownMenu" style="max-height: 200px; overflow-y: auto;">
          </ul>
        </div>
      </div>
      <div class="snmp-file-section">
        <h6 data-i18n="Community strings dictionary (default if empty):">Community strings dictionary</h6>
        <input class="form-control" 
               type="file" 
               id="${prefix}communityFile" 
               accept=".txt"
               data-max-size="10485760">
        <small class="form-text text-muted mt-1">
          Upload a .txt file with community strings (max 10MB)
        </small>
      </div>
    `;
  }
};

const SnmpHandlers = {
  uploadedFile: null,
  availableTargets: [],
  isLoading: false,

  setupFileUpload(prefix) {
    const fileInput = document.getElementById(`${prefix}communityFile`);
    if (!fileInput) return;

    fileInput.addEventListener('change', (event) => {
      const file = event.target.files[0];
      const maxSize = parseInt(fileInput.dataset.maxSize || 10485760);
      
      if (file) {
        if (file.size > maxSize) {
          create_toast('Error', 'File size too large. Maximum 10MB allowed.', 'error');
          fileInput.value = '';
          this.uploadedFile = null;
          return;
        }
        this.uploadedFile = file;
      } else {
        this.uploadedFile = null;
      }
    });
  },

  async readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = (e) => reject(e);
      reader.readAsDataURL(file);
    });
  },

  async loadTargets(prefix) {
    if (this.isLoading) return;
    this.isLoading = true;
    
    const dropdownBtn = document.getElementById(`${prefix}targetDropdown`);
    const dropdownMenu = document.getElementById(`${prefix}targetDropdownMenu`);
    
    if (!dropdownMenu) {
      this.isLoading = false;
      return;
    }
    
    try {
      const currentTarget = this.getSelectedTarget(prefix);
      const resp = await axios.get('/api/v1/l4/get_resources_for_snmp');
      this.availableTargets = resp.data || [];
      
      dropdownMenu.innerHTML = '';
      
      if (this.availableTargets.length === 0) {
        const li = document.createElement('li');
        li.innerHTML = '<span class="dropdown-item text-muted">No SNMP targets found</span>';
        dropdownMenu.appendChild(li);
        if (dropdownBtn) dropdownBtn.textContent = 'No targets available';
        return;
      }
      
      this.availableTargets.forEach((item, idx) => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.classList.add('dropdown-item');
        a.href = '#';
        a.textContent = `${item.ip}:${item.port}`;
        a.dataset.ip = item.ip;
        a.dataset.port = item.port;
        
        a.addEventListener('click', (e) => {
          e.preventDefault();
          dropdownMenu.querySelectorAll('.dropdown-item').forEach(el => 
            el.classList.remove('active', 'fw-medium')
          );
          a.classList.add('active', 'fw-medium');
          if (dropdownBtn) dropdownBtn.textContent = `${item.ip}:${item.port}`;
        });
        
        li.appendChild(a);
        dropdownMenu.appendChild(li);
        
        if (currentTarget && currentTarget.ip === item.ip && currentTarget.port === item.port) {
          a.classList.add('active', 'fw-medium');
          if (dropdownBtn) dropdownBtn.textContent = `${item.ip}:${item.port}`;
        }
        
        if (idx === 0 && !currentTarget) {
          a.classList.add('active', 'fw-medium');
          if (dropdownBtn) dropdownBtn.textContent = `${item.ip}:${item.port}`;
        }
      });
      
    } catch (err) {
      console.error('Failed to load SNMP targets:', err);
      dropdownMenu.innerHTML = '<li><span class="dropdown-item text-danger">Error loading targets</span></li>';
    } finally {
      this.isLoading = false;
    }
  },

  getSelectedTarget(prefix) {
    const dropdownMenu = document.getElementById(`${prefix}targetDropdownMenu`);
    const activeItem = dropdownMenu?.querySelector('.dropdown-item.active');
    
    if (activeItem) {
      return { ip: activeItem.dataset.ip, port: activeItem.dataset.port };
    }
    return null;
  },

  filterSnmpTargets(rows) {
    return (rows || [])
      .map(row => {
        const protocol = (row.protocol || '').toLowerCase();
        const port = Number(row.port);
        const service = (row.service_name || row.service || '').toLowerCase();
        const ip = row.ipaddr || row.ip;
        if (!ip) return null;
        const isSnmp = (protocol === 'udp' && port === 161) || service.includes('snmp');
        return isSnmp ? { ip, port: String(port) } : null;
      })
      .filter(Boolean);
  }
};

class SnmpScanner {
  constructor(prefix) { this.prefix = prefix; }

  getBaseParams() {
    const agentId = this.instance?.state?.overrides?.agent_id || window.agentData?.default_agent;
    if (!agentId) throw new Error('Please select an Agent');
    return { agent_id: String(agentId) };
  }

  async scan(targetIp, targetPort, communityFile) {
    const baseParams = this.getBaseParams();
    let community_strings_file = '';
    if (communityFile) {
      try {
        community_strings_file = await SnmpHandlers.readFileAsBase64(communityFile);
      } catch (error) {
        console.error('Error reading community file:', error);
        create_toast('Error', 'Error reading file. Please try again.', 'error');
        throw error;
      }
    }

    const payload = {
      ...baseParams,
      target_ip: targetIp,
      target_port: targetPort,
      community_strings_file: community_strings_file
    };

    const result = await window.executeToolTasks({
      tasks: [{ endpoint: '/api/v1/task/snmp_brute_communitystring_task', payload }],
      stopOnFirstFailure: true
    });

    if (!result.success) {
      if (result.reason === 'module_install_requested') return null;
      throw new Error(result.error?.message || 'SNMP scan failed');
    }

    return result;
  }
}

const snmpModalConfig = {
  prefix: 'snmp_',
  tabs: [],
  hideActionButtons: false,
  hideInterfaceBar: true,
  toolParams: (prefix) => SnmpUI.buildParams(prefix),

  onInit(instance) {
    const prefix = instance.prefix;

    SnmpHandlers.loadTargets(prefix);
    SnmpHandlers.setupFileUpload(prefix);

    const modalEl = document.getElementById('snmpModalWindow');
    if (modalEl) {
      modalEl.addEventListener('shown.bs.modal', () => {
        SnmpHandlers.loadTargets(prefix);
      });
    }

    instance.getTargets = function() {
      const target = SnmpHandlers.getSelectedTarget(this.prefix);
      return target ? [target] : [];
    };

    window.snmp_full_modal_window = () => {
      instance.reset();
      window[`show_${instance.modalId}`]();
    };

    window.snmp_start_with_prefill = (rows, prefillParams = {}) => {
      if (prefillParams?.agent_id) {
        instance.state.overrides.agent_id = prefillParams.agent_id;
      }
      
      if (prefillParams?.interface_name) {
        const iface = interfaceData?.interfaces?.find(i => i.name === prefillParams.interface_name);
        if (iface) {
          instance.state.overrides.interface_obj = iface;
          instance.state.overrides.interface_id = String(iface.id);
        } else {
          window.getInterfaceData(prefillParams.agent_id).then(ifaceData => {
            if (ifaceData?.interfaces) {
              const found = ifaceData.interfaces.find(i => i.name === prefillParams.interface_name);
              if (found) {
                instance.state.overrides.interface_obj = found;
                instance.state.overrides.interface_id = String(found.id);
              }
            }
          });
        }
      }
      
      instance.reset();
      const selectTarget = () => {
        const { target_ip, target_port } = prefillParams || {};
        const dropdownMenu = document.getElementById(`${prefix}targetDropdownMenu`);
        
        if (target_ip && target_port && dropdownMenu) {
          const items = dropdownMenu.querySelectorAll('.dropdown-item');
          for (const item of items) {
            if (item.dataset.ip === target_ip && item.dataset.port === String(target_port)) {
              item.click();
              return true;
            }
          }
        }
        return false;
      };

      if (!selectTarget()) {
        const dropdownMenu = document.getElementById(`${prefix}targetDropdownMenu`);
        const observer = new MutationObserver(() => {
          if (selectTarget()) observer.disconnect();
        });
        if (dropdownMenu) observer.observe(dropdownMenu, { childList: true });
        setTimeout(() => {
          selectTarget();
          observer.disconnect();
          window[`show_${instance.modalId}`]();
        }, 500);
      } else {
        window[`show_${instance.modalId}`]();
      }
    };
  },

  onReset(instance) {
    const prefix = instance.prefix;
    const fileInput = document.getElementById(`${prefix}communityFile`);
    if (fileInput) fileInput.value = '';
    SnmpHandlers.uploadedFile = null;
    
    const dropdownBtn = document.getElementById(`${prefix}targetDropdown`);
    const dropdownMenu = document.getElementById(`${prefix}targetDropdownMenu`);
    if (dropdownBtn) dropdownBtn.textContent = 'Select target';
    if (dropdownMenu) {
      dropdownMenu.querySelectorAll('.dropdown-item').forEach(el => el.classList.remove('active', 'fw-medium'));
    }
  },

  async onStart(instance) {
    const prefix = instance.prefix;
    try {
      const target = SnmpHandlers.getSelectedTarget(prefix);
      if (!target?.ip || !target?.port) {
        create_toast('Warning', 'Please select a target', 'warning');
        return;
      }
      const scanner = new SnmpScanner(prefix);
      scanner.instance = instance;
      const result = await scanner.scan(target.ip, target.port, SnmpHandlers.uploadedFile);
      if (result !== null) {
        window[`close_${instance.modalId}`]();
      }
    } catch (error) {
      console.error('SNMP scan error:', error);
      create_toast('Error', error.message || 'Failed to start scan', 'error');
    }
  }
};

window.openSnmpModal = function () {
  if (document.getElementById('snmpModalWindow')) {
    show_snmpModalWindow();
    return;
  }
  createModal('snmpModalWindow', 'Snmp Tool', 'https://help.setezor.net/%D0%98%D0%BD%D1%81%D1%82%D1%80%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B.html#snmp');
  ToolModalBuilder.register('snmpModalWindow', snmpModalConfig);
  show_snmpModalWindow();
};