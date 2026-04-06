const WebGrabberUI = {

  getStyles() {
    return `
      <style>
        .webgrabber-tool-section {
          background: #f8f9fa;
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 15px;
          border: 1px solid #e9ecef;
        }
        .webgrabber-tool-section h6 {
          font-size: 0.85rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: #6c757d;
          margin-bottom: 10px;
          font-weight: bold;
          display: flex;
          align-items: center;
        }
        .webgrabber-tool-section h6 i { 
          margin-right: 8px; 
        }
        .timeout-slider-container {
          padding: 10px;
          background: white;
          border-radius: 6px;
          border: 1px solid #e9ecef;
        }
        .options-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-top: 10px;
        }
        .option-item {
          background: white;
          border-radius: 6px;
          padding: 12px;
          border: 1px solid #e9ecef;
        }
      </style>
    `;
  },

  buildParams(prefix) {
    return `
      ${this.getStyles()}
      ${this.buildOptionsSection(prefix)}
      ${this.buildTimeoutSlider(prefix)}
    `;
  },

  buildOptionsSection(prefix) {
    return `
      <div class="webgrabber-tool-section">
        <h6><i class="bi bi-gear-fill"></i> ${i18next.t("Options")}</h6>
        <div class="options-grid">
          <div class="option-item">
            <div class="form-check form-switch">
              <input class="form-check-input" type="checkbox" id="${prefix}takeScreenshot" checked>
              <label class="form-check-label" for="${prefix}takeScreenshot">
                <i class="bi bi-camera-fill me-1"></i> ${i18next.t('Take screenshot')}
              </label>
            </div>
          </div>
          <div class="option-item">
            <div class="form-check form-switch">
              <input class="form-check-input" type="checkbox" id="${prefix}withWappalyzer" checked>
              <label class="form-check-label" for="${prefix}withWappalyzer">
                <i class="bi bi-binoculars-fill me-1"></i> ${i18next.t('Take wappalyzer')}
              </label>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  buildTimeoutSlider(prefix) {
    return `
      <div class="webgrabber-tool-section timeout-slider-container">
        <h6><i class="bi bi-clock"></i> ${i18next.t('Timeout')}</h6>
        <div class="d-flex justify-content-between mb-1">
          <small class="text-muted">30s</small>
          <small class="text-muted">65s</small>
          <small class="text-muted">100s</small>
        </div>
        <input type="range" class="form-range" id="${prefix}timeoutSlider" 
               min="30" max="100" step="5" value="30">
        <div class="text-center mt-2">
          <span class="badge bg-secondary" id="${prefix}timeoutValue">30</span>
          <small class="text-muted ms-2">seconds</small>
        </div>
      </div>
    `;
  }
};

const WebGrabberHandlers = {

  setupTimeoutSlider(prefix) {
    const slider = document.getElementById(`${prefix}timeoutSlider`);
    const value = document.getElementById(`${prefix}timeoutValue`);
    
    if (slider && value) {
      slider.addEventListener('input', (e) => {
        value.textContent = e.target.value;
      });
    }
  },

  async handleNodeModal(instance, node) {
    const prefix = instance.prefix;
    
    instance.reset();
    
    const urlInput = document.getElementById(`${prefix}inputURL`);
    if (urlInput) {
        const target = node.domains?.[0] || node.domain || node.label || node.name || node.ip || '';
        if (target) {
            urlInput.value = target.startsWith('http') ? target : `https://${target}`;
        }
    }
    
    if (node.domains?.length > 1) {
        node.domains.slice(1).forEach((domain, idx) => {
            setTimeout(() => {
                instance.addInputField('url', true);
                const container = document.getElementById(`${prefix}InputContainer`);
                const lastGroup = container?.lastElementChild;
                if (lastGroup) {
                    const input = lastGroup.querySelector('.url');
                    if (input) {
                        const fullUrl = domain.startsWith('http') ? domain : `https://${domain}`;
                        input.value = fullUrl;
                    }
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

    if (rows.length > 0) {
      const uniqueDomains = new Set();
      
      rows.forEach(row => {
        const domain = row.domain?.trim();
        if (domain) uniqueDomains.add(domain);
      });

      Array.from(uniqueDomains).forEach((domain, index) => {
        const fullUrl = domain.startsWith('http') ? domain : `https://${domain}`;
        
        if (index === 0) {
          const urlInput = document.getElementById(`${prefix}inputURL`);
          if (urlInput) {
            urlInput.value = fullUrl;
          }
        } else {
          instance.addInputField('url', true);
          
          const container = document.getElementById(`${prefix}InputContainer`);
          const lastGroup = container?.lastElementChild;
          
          if (lastGroup) {
            const urlInput = lastGroup.querySelector('.url');
            if (urlInput) {
              urlInput.value = fullUrl;
            }
          }
        }
      });
    }

    if (Object.keys(prefillParams).length > 0) {
      this.applyPrefillParams(prefix, prefillParams);
    }

    window[`show_${instance.modalId}`]();
  },

  applyPrefillParams(prefix, params) {
    if (params.url) {
      const urlInput = document.getElementById(`${prefix}inputURL`);
      if (urlInput) {
        let url = params.url.trim();
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
          url = 'https://' + url;
        }
        urlInput.value = url;
      }
    }

    if (params.timeout !== undefined) {
      const slider = document.getElementById(`${prefix}timeoutSlider`);
      const value = document.getElementById(`${prefix}timeoutValue`);
      
      if (slider && value) {
        const timeoutVal = Math.max(30, Math.min(100, parseInt(params.timeout, 10) || 30));
        const steppedVal = Math.round(timeoutVal / 5) * 5;
        slider.value = steppedVal;
        value.textContent = steppedVal;
      }
    }

    if (params.with_screenshot !== undefined) {
      const screenshotCheckbox = document.getElementById(`${prefix}takeScreenshot`);
      if (screenshotCheckbox) {
        screenshotCheckbox.checked = params.with_screenshot === true || params.with_screenshot === 'true';
      }
    }

    if (params.with_wappalyzer !== undefined) {
      const wappalyzerCheckbox = document.getElementById(`${prefix}withWappalyzer`);
      if (wappalyzerCheckbox) {
        wappalyzerCheckbox.checked = params.with_wappalyzer === true || params.with_wappalyzer === 'true';
      }
    }

    if (params.agent_id) {
      if (typeof window.setAgent === 'function') {
        window.setAgent(params.agent_id);
      }
    }
  }
};

class WebGrabberScanner {
  constructor(prefix) {
    this.prefix = prefix;
  }

  getBaseParams() {
    const agentId = 
      this.instance?.state?.overrides?.agent_id || 
      window.agentData?.default_agent;

    if (!agentId) {
      throw new Error("Please select an Agent");
    }

    return {
      agent_id: String(agentId),
      with_screenshot: !!document.getElementById(`${this.prefix}takeScreenshot`)?.checked,
      with_wappalyzer: !!document.getElementById(`${this.prefix}withWappalyzer`)?.checked,
      timeout: parseInt(document.getElementById(`${this.prefix}timeoutValue`)?.textContent || '30', 10)
    };
  }

  async scanScope(scopeId) {
    const baseParams = this.getBaseParams();
    const payload = { ...baseParams, scope_id: String(scopeId) };

    const result = await window.executeToolTasks({
      tasks: [{
        endpoint: '/api/v1/task/parse_site',
        payload
      }],
      stopOnFirstFailure: true
    });

    if (!result.success) {
      if (result.reason === 'module_install_requested') {
        return null;
      }
      throw new Error(result.error?.message || 'WebGrabber scope scan failed');
    }

    return result.responses[0];
  }

  async scanTargets(targets) {
    const baseParams = this.getBaseParams();
    const tasks = [];

    for (const target of targets) {
      if (!target.url) continue;

      const payload = {
        ...baseParams,
        url: target.url.trim()
      };

      tasks.push({
        endpoint: '/api/v1/task/parse_site',
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
      throw new Error(result.error?.message || 'WebGrabber targets scan failed');
    }

    return result.responses;
  }
}

const webGrabberModalConfig = {
  prefix: 'webgrabber_',
  hideInterfaceBar: true,
  tabs: [
    { id: 'target', label: i18next.t('Target'), targetType: 'url' },
    { id: 'scope', label: i18next.t('Scope') },
    { id: 'database', label: i18next.t('Database') },
    { id: 'textarea', label: i18next.t('Textarea'), placeholder: 'https://example1.com\nhttp://192.168.1.1', textareaValidTypes: ['url', 'ip', 'ip_ports', 'domain', 'domain_ports'] }
  ],
  
  toolParams: (prefix) => WebGrabberUI.buildParams(prefix),

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
          title: "IP Address", 
          field: "ipaddr",
          headerFilter: "input",
          headerFilterPlaceholder: "Search IP..."
        },
        { 
          title: "Domain", 
          field: "domain",
          headerFilter: "input",
          headerFilterPlaceholder: "Search domain..."
        },
        { 
          title: "Port", 
          field: "port",
          headerFilter: "input",
          headerFilterPlaceholder: "Search port..."
        },
        { 
          title: "Service", 
          field: "service_name",
          formatter: (cell) => {
            const service = cell.getValue();
            if (service === 'http') {
              return '<span class="badge bg-info">HTTP</span>';
            } else if (service === 'https') {
              return '<span class="badge bg-success">HTTPS</span>';
            }
            return service || '';
          },
          headerFilter: "input",
          headerFilterPlaceholder: "Search service..."
        },
        { 
          title: "SSL", 
          field: "is_ssl",
          visible: false,
          headerSort: false
        }
      ],
      filter: [
        { field: "service_name", type: "like", value: "http" }
      ]
    };
  },

  onInit(instance) {
    const prefix = instance.prefix;
    
    if (instance.config.getTargets) {
      instance.getTargets = instance.config.getTargets.bind(instance);
    }

    WebGrabberHandlers.setupTimeoutSlider(prefix);

    const dbTabTrigger = document.getElementById(`${prefix}database-tab`);

    window.web_grabber_script_modal_to_node = (node) => {
      WebGrabberHandlers.handleNodeModal(instance, node);
    };

    window.web_grabber_start_with_prefill = (rows = [], prefillParams = {}) => {
      WebGrabberHandlers.handlePrefill(instance, rows, prefillParams);
    };
  },

  onReset(instance) {
    const prefix = instance.prefix;

    const slider = document.getElementById(`${prefix}timeoutSlider`);
    const value = document.getElementById(`${prefix}timeoutValue`);
    if (slider && value) {
      slider.value = '30';
      value.textContent = '30';
    }

    const screenshotCheckbox = document.getElementById(`${prefix}takeScreenshot`);
    if (screenshotCheckbox) {
      screenshotCheckbox.checked = true;
    }

    const wappalyzerCheckbox = document.getElementById(`${prefix}withWappalyzer`);
    if (wappalyzerCheckbox) {
      wappalyzerCheckbox.checked = true;
    }

    instance.state.selectedDatabaseTargets = {};
  },

  getTargets() {
    const tabId = this.getActiveTab();
    
    if (!tabId) {
      return [];
    }

    const normalizeUrl = (url) => {
      if (!url) return '';
      let u = url.trim().toLowerCase();
      if (!u.startsWith('http://') && !u.startsWith('https://')) {
        u = 'https://' + u;
      }
      try {
        const parsed = new URL(u);
        return parsed.origin + parsed.pathname.replace(/\/+$/, '');
      } catch {
        return u;
      }
    };

    const seen = new Set();
    const addUnique = (url, extra = {}) => {
      const key = normalizeUrl(url);
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return { url: key, target: key, ...extra };
    };

    const targets = [];

    if (tabId === 'database') {
      if (!this.databaseTable) return [];
      
      Object.values(this.state.selectedDatabaseTargets).forEach((item) => {
          const host = item.domain || item.ip;
          if (!host) return;

          const ports = item.ports || [];
          const protocols = ports.length > 0 
              ? ports.map(p => p === '443' ? 'https' : p === '80' ? 'http' : 'http')
              : ['http', 'https'];

          protocols.forEach(proto => {
              let url = `${proto}://${host}`;
              if (ports.length > 0 && ports[0] !== '80' && ports[0] !== '443') {
                  url += `:${ports[0]}`;
              }
              const t = addUnique(url, { ip: item.ip, domain: item.domain, port: ports[0] || '', service: proto });
              if (t) targets.push(t);
          });
      });
      
      return targets;
    }

    if (tabId === 'scope') {
      return { scope_id: this.state.selectedScopeId };
    }

    const collectFromInput = (url) => {
      if (!url?.trim()) return;
      let fullUrl = url.trim();
      if (!fullUrl.startsWith('http://') && !fullUrl.startsWith('https://')) {
        fullUrl = 'https://' + fullUrl;
      }
      const t = addUnique(fullUrl);
      if (t) targets.push(t);
    };

    if (tabId === 'target') {
      const urlInput = document.getElementById(`${this.prefix}inputURL`);
      if (urlInput) collectFromInput(urlInput.value);

      document.querySelectorAll(`#${this.prefix}InputContainer .input-group`).forEach(group => {
        const urlEl = group.querySelector(".url");
        if (urlEl) collectFromInput(urlEl.value);
      });
    } 
    else if (tabId === 'textarea') {
      const textarea = document.getElementById(`${this.prefix}textareaInput`);
      if (textarea?.value) {
        textarea.value.split("\n").forEach(line => collectFromInput(line.trim()));
      }
    }
    
    return targets;
  },

  async onStart(instance) {
    const scanner = new WebGrabberScanner(instance.prefix);
    
    try {
      const tabId = instance.getActiveTab();

      let result;
      if (tabId === 'scope') {
        if (!instance.state.selectedScopeId) {
          create_toast('Warning', i18next.t('Please select a scope'), 'warning');
          return;
        }
        result = await scanner.scanScope(instance.state.selectedScopeId);
      } else {
        const targets = instance.getTargets();
        if (!targets?.length) {
          create_toast('Warning', i18next.t('Please enter at least one target'), 'warning');
          return;
        }
        result = await scanner.scanTargets(targets);
      }

      if (result !== null) {
        window[`close_${instance.modalId}`]();
      }
    } catch (error) {
      console.error('WebGrabber scan error:', error);
      create_toast('Error', error.message || i18next.t('Failed to start scan'), 'error');
    }
  }
};

window.openWebGrabberModal = function () {
  if (document.getElementById('webGrabberModalWindow')) {
    show_webGrabberModalWindow();
    return;
  }
  createModal('webGrabberModalWindow', 'Web Grabber Tool', 'https://help.setezor.net/Инструменты.html#web-grabber');
  ToolModalBuilder.register('webGrabberModalWindow', webGrabberModalConfig);
  show_webGrabberModalWindow();
};