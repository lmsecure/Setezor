const LookupDescriptions = {
  recordTypes: {
    'A': 'IPv4 address record',
    'AAAA': 'IPv6 address record',
    'CNAME': 'Canonical name record',
    'MX': 'Mail exchange record',
    'NS': 'Name server record',
    'SOA': 'Start of authority record',
    'TXT': 'Text record',
    'SRV': 'Service locator'
  }
};

const LookupUI = {
  getStyles() {
    return `
      <style>
        .lookup-tool-section {
          background: #f8f9fa;
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 15px;
          border: 1px solid #e9ecef;
        }
        .lookup-tool-section h6 {
          font-size: 0.85rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: #6c757d;
          margin-bottom: 10px;
          font-weight: bold;
          display: flex;
          align-items: center;
        }
        .lookup-tool-section h6 i { 
          margin-right: 8px; 
        }
        .record-type-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 8px;
        }
        .record-type-item {
          display: flex;
          align-items: center;
        }
      </style>
    `;
  },

  buildParams(prefix) {
    return `
      ${this.getStyles()}
      ${this.buildNameServers(prefix)}
      ${this.buildRecordTypes(prefix)}
    `;
  },

  buildNameServers(prefix) {
    return `
      <div class="lookup-tool-section">
        <h6><i class="bi bi-server"></i> ${i18next.t("NS Servers")}</h6>
        <div class="form-text text-muted mb-2">
          ${i18next.t("Optional: Specify custom nameservers for DNS queries (comma separated)")}
        </div>
        <input type="text" 
               class="form-control" 
               id="${prefix}nsServer" 
               name="ns_servers" 
               placeholder="8.8.8.8, 1.1.1.1"
               data-bs-toggle="tooltip"
               data-bs-placement="top"
               title="${i18next.t("Optional: Specify nameservers (comma separated)")}">
      </div>
    `;
  },

  buildRecordTypes(prefix) {
    const records = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'SOA', 'TXT', 'SRV'];
    
    return `
      <div class="lookup-tool-section">
        <h6><i class="bi bi-diagram-3"></i> ${i18next.t("Record Types")}</h6>
        <div class="record-type-grid">
          ${records.map(record => `
            <div class="record-type-item">
              <input class="form-check-input me-1" 
                     type="checkbox" 
                     id="${prefix}record${record}" 
                     value="${record}"
                     checked>
              <label class="form-check-label" 
                     for="${prefix}record${record}"
                     title="${LookupDescriptions.recordTypes[record]}"
                     data-bs-toggle="tooltip">
                ${record}
              </label>
            </div>
          `).join('')}
        </div>
        <div class="form-text text-muted mt-2">
          ${i18next.t("Select DNS record types to query")}
        </div>
      </div>
    `;
  }
};

const LookupHandlers = {
  async handleNodeModal(instance, node) {
    const prefix = instance.prefix;
    
    instance.reset();
    
    const domainInput = document.getElementById(`${prefix}inputDomain`);
    if (domainInput) {
        const target = node.domains?.[0] || node.domain || node.label || '';
        domainInput.value = target;
    }
    
    if (node.domains?.length > 1) {
        node.domains.slice(1).forEach((domain, idx) => {
            setTimeout(() => {
                instance.addInputField('domain_only', true);
                const container = document.getElementById(`${prefix}InputContainer`);
                const lastGroup = container?.lastElementChild;
                if (lastGroup) {
                    const input = lastGroup.querySelector('.domain');
                    if (input) input.value = domain;
                }
            }, idx * 50);
        });
    }
    
    window[`show_${instance.modalId}`]();
  },

  handlePrefill(instance, rows = [], prefillParams = {}) {
    const prefix = instance.prefix;
    
    if (prefillParams?.agent_id) {
      instance.state.overrides.agent_id = prefillParams.agent_id;
    }
    
    instance.reset();

    const targetTab = document.getElementById(`${prefix}target-tab`);
    if (targetTab) {
      const tab = new bootstrap.Tab(targetTab);
      tab.show();
    }

    const domains = new Set();

    if (prefillParams.domain) {
      domains.add(String(prefillParams.domain).trim());
    }

    rows.forEach(row => {
      const d = (row.domain).trim();
      if (d) domains.add(d);
    });

    const uniqueDomains = Array.from(domains);

    uniqueDomains.forEach((domain, index) => {
      if (index === 0) {
        const domainInput = document.getElementById(`${prefix}inputDomain`);
        if (domainInput) domainInput.value = domain;
      } else {
        instance.addInputField('domain_only', true);
        const container = document.getElementById(`${prefix}InputContainer`);
        const lastGroup = container?.lastElementChild;
        if (lastGroup) {
          const domainInput = lastGroup.querySelector('.domain');
          if (domainInput) domainInput.value = domain;
        }
      }
    });

    if (prefillParams.ns_servers && Array.isArray(prefillParams.ns_servers)) {
      const nsInput = document.getElementById(`${prefix}nsServer`);
      if (nsInput) {
        nsInput.value = prefillParams.ns_servers.join(', ');
      }
    } else if (typeof prefillParams.ns_servers === 'string') {
      const nsInput = document.getElementById(`${prefix}nsServer`);
      if (nsInput) nsInput.value = prefillParams.ns_servers;
    }

    if (prefillParams.records && Array.isArray(prefillParams.records)) {
      document.querySelectorAll(`[id^="${prefix}record"]`).forEach(el => {
        el.checked = false;
      });
      prefillParams.records.forEach(rt => {
        const cb = document.getElementById(`${prefix}record${rt}`);
        if (cb) cb.checked = true;
      });
    }

    window[`show_${instance.modalId}`]();
  },

  getDatabaseTableConfig() {
    return {
      columns: [
        { 
          title: "Select", 
          field: "selected", 
          formatter: "rowSelection", 
          titleFormatter: "rowSelection", 
          hozAlign: "center", 
          headerHozAlign: "center", 
          headerSort: false,
          width: 50
        },
        { 
          title: "Domain", 
          field: "domain", 
          headerFilter: "input", 
          headerFilterPlaceholder: "Search domain..." 
        }
      ],
      filter: [
        { field: "domain", type: "!=", value: "" }
      ]
    };
  }
};

class LookupScanner {
  constructor(prefix) {
    this.prefix = prefix;
  }

  getSelectedRecordTypes() {
    const recordTypes = [];
    const checkboxes = document.querySelectorAll(`[id^="${this.prefix}record"]:checked`);
    checkboxes.forEach(cb => recordTypes.push(cb.value));
    return recordTypes;
  }

  getBaseParams() {
    const agentId = 
      this.instance?.state?.overrides?.agent_id || 
      window.agentData?.default_agent;

    if (!agentId) {
      throw new Error("Please select an Agent");
    }

    const params = {
      agent_id: String(agentId),
      records: this.getSelectedRecordTypes()
    };

    const nsInput = document.getElementById(`${this.prefix}nsServer`);
    if (nsInput?.value.trim()) {
      params.ns_servers = nsInput.value
        .split(',')
        .map(item => item.trim())
        .filter(Boolean);
    }

    return params;
  }

  async lookupTargets(targets) {
    const baseParams = this.getBaseParams();
    const tasks = [];
    const seen = new Set();

    for (const target of targets) {
      let domain = '';
      
      if (typeof target === 'string') {
        domain = target;
      } else {
        domain = target.domain || target.ip || target.target || target.url || '';
      }
      
      if (!domain) continue;
      
      const d = String(domain).trim();
      
      if (seen.has(d)) continue;
      seen.add(d);
      
      const payload = {
        ...baseParams,
        domain: d
      };

      tasks.push({
        endpoint: '/api/v1/task/dns_task',
        payload
      });
    }

    if (tasks.length === 0) return [];

    const result = await window.executeToolTasks({
      tasks,
      stopOnFirstFailure: true
    });

    if (!result.success) {
      if (result.reason === 'module_install_requested') {
        return null;
      }
      throw new Error(result.error?.message || 'DNS lookup targets failed');
    }

    return result.responses;
  }

  async lookupScope(scopeId) {
    const baseParams = this.getBaseParams();
    const payload = {
      ...baseParams,
      scope_id: String(scopeId)
    };

    const result = await window.executeToolTasks({
      tasks: [{
        endpoint: '/api/v1/task/dns_task',
        payload
      }],
      stopOnFirstFailure: true
    });

    if (!result.success) {
      if (result.reason === 'module_install_requested') {
        return null;
      }
      throw new Error(result.error?.message || 'DNS lookup scope failed');
    }

    return result.responses[0];
  }
}

const lookupModalConfig = {
  prefix: 'lookup_',
  hideInterfaceBar: true,
  tabs: [
    { id: 'target', label: i18next.t('Target'), targetType: 'domain_only' },
    { id: 'scope', label: i18next.t('Scope') },
    { id: 'database', label: i18next.t('Database') },
    { id: 'textarea', label: i18next.t('Textarea'), placeholder: 'example.com\nexample1.com', textareaValidTypes: ['domain'] },
  ],
  
  toolParams: (prefix) => LookupUI.buildParams(prefix),

  databaseProcessor: 'domainOnly',
  databaseOutputFormat: 'array',


  getDatabaseTableConfig() {
    return LookupHandlers.getDatabaseTableConfig();
  },

  onInit(instance) {
    const prefix = instance.prefix;

    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
      const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
      tooltips.forEach(el => new bootstrap.Tooltip(el));
    }

    window.lookup_script_modal_to_node = (node) => {
      LookupHandlers.handleNodeModal(instance, node);
    };

    window.lookup_start_with_prefill = (rows, prefillParams) => {
      LookupHandlers.handlePrefill(instance, rows, prefillParams);
    };

    window.lookup_script_modal_to_info_tabs = async (rows) => {
      LookupHandlers.handlePrefill(instance, rows);
    };

    window.lookup_script_modal_to_database = async (rows) => {
      const prefix = instance.prefix;
      
      instance.reset();
      
      const databaseTab = document.getElementById(`${prefix}database-tab`);
      if (databaseTab) {
        databaseTab.click();
        
        setTimeout(() => {
          if (instance.databaseTable) {
            instance.databaseTable.setData().then(() => {
              setTimeout(() => {
                const rowsToSelect = [];
                const tableData = instance.databaseTable.getData();
                
                rows.forEach(row => {
                  const match = tableData.find(tableRow => 
                    tableRow.domain === (row.domain || row.ipaddr)
                  );
                  if (match) rowsToSelect.push(match);
                });
                
                if (rowsToSelect.length > 0) {
                  instance.databaseTable.selectRow(rowsToSelect);
                  instance.syncDatabaseTargetsFromTable();
                }
              }, 200);
            });
          }
        }, 300);
      }
      
      window[`show_${instance.modalId}`]();
    };
  },

  onReset(instance) {
    const prefix = instance.prefix;

    const nsInput = document.getElementById(`${prefix}nsServer`);
    if (nsInput) {
      nsInput.value = '';
    }

    document.querySelectorAll(`[id^="${prefix}record"]`).forEach(el => {
      el.checked = true;
    });

    const container = document.getElementById(`${prefix}InputContainer`);
    if (container) {
      container.innerHTML = '';
    }
    
    const domainInput = document.getElementById(`${prefix}inputDomain`);
    if (domainInput) {
      domainInput.value = '';
    }

    instance.state.selectedDatabaseTargets = {};
    instance.state.selectedRowsState = {};
    
    if (instance.databaseTable && typeof instance.databaseTable.deselectRow === 'function') {
        instance.databaseTable.deselectRow();
    }
  },

  async onStart(instance) {
    const scanner = new LookupScanner(instance.prefix);
    
    try {
      const tabId = instance.getActiveTab();
      let result;

      if (tabId === 'scope') {
        if (!instance.state.selectedScopeId) {
          create_toast('Warning', i18next.t('Please select a scope'), 'warning');
          return;
        }
        result = await scanner.lookupScope(instance.state.selectedScopeId);
      } else if (tabId === 'database') {
        const targets = Object.values(instance.state.selectedDatabaseTargets || {}).map(item => item.domain);
          if (!targets.length) {
              create_toast('Warning', i18next.t('No domains selected from database'), 'warning');
              return;
          }
          result = await scanner.lookupTargets(targets);
      } else {
        const targets = instance.getTargets();
        
        if (!targets.length) {
          create_toast('Warning', i18next.t('No targets found'), 'warning');
          return;
        }
        result = await scanner.lookupTargets(targets);
      }

      if (result !== null) {
        window[`close_${instance.modalId}`]();
      }
    } catch (error) {
      console.error('Failed to start lookup:', error);
      create_toast('Error', error.message || i18next.t('Failed to start lookup'), 'error');
    }
  }
};

window.openLookupModal = function () {
  if (document.getElementById('lookupModalWindow')) {
    show_lookupModalWindow();
    return;
  }
  createModal('lookupModalWindow', 'Lookup Tool', 'https://help.setezor.net/%D0%98%D0%BD%D1%81%D1%82%D1%80%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B.html#lookup');
  ToolModalBuilder.register('lookupModalWindow', lookupModalConfig);
  show_lookupModalWindow();
};