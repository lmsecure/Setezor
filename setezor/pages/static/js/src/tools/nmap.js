const NmapDescriptions = {
  scanTechniques: {
    '-sS': 'TCP SYN scan',
    '-sT': 'TCP Connect() scan',
    '-sA': 'TCP ACK scan',
    '-sW': 'TCP Window scan',
    '-sM': 'TCP Maimon scan',
    '-sU': 'UDP Scan',
    '-sP': 'Ping Scan'
  },
  
  discovery: {
    '-PA': 'TCP ACK discovery to given ports',
    '-PS': 'TCP SYN discovery to given ports',
    '-PU': 'UDP discovery to given ports',
    '-PY': 'SCTP discovery to given ports'
  },
  
  icmp: {
    '-PE': 'ICMP echo request discovery probes',
    '-PP': 'ICMP timestamp request discovery probes',
    '-PM': 'ICMP netmask request discovery probes'
  }
};

const NmapTimingTemplates = {
  'T0': { name: i18next.t('Paranoid'), values: { minRtt: '100ms', maxRtt: '300s', initialRtt: '300s', maxRetries: '10', scanDelay: '300s', maxTcpDelay: '300s', maxUdpDelay: '300s', hostTimeout: '0', minRate: '', maxRate: ''}},
  'T1': { name: i18next.t('Sneaky'), values: { minRtt: '100ms', maxRtt: '15s', initialRtt: '15s', maxRetries: '10', scanDelay: '15s', maxTcpDelay: '15s', maxUdpDelay: '15s', hostTimeout: '0', minRate: '', maxRate: ''}},
  'T2': { name: i18next.t('Polite'), values: { minRtt: '100ms', maxRtt: '10s', initialRtt: '1s', maxRetries: '10', scanDelay: '400ms', maxTcpDelay: '1s', maxUdpDelay: '1s', hostTimeout: '0', minRate: '', maxRate: ''}},
  'T3': { name: i18next.t('Normal'), values: { minRtt: '100ms', maxRtt: '10s', initialRtt: '1s', maxRetries: '10', scanDelay: '0', maxTcpDelay: '1s', maxUdpDelay: '1s', hostTimeout: '0', minRate: '', maxRate: ''}},
  'T4': { name: i18next.t('Aggressive'), values: { minRtt: '100ms', maxRtt: '1250ms', initialRtt: '500ms', maxRetries: '6', scanDelay: '0', maxTcpDelay: '10ms', maxUdpDelay: '1s', hostTimeout: '0', minRate: ''}},
  'T5': { name: i18next.t('Insane'), values: { minRtt: '50ms', maxRtt: '300ms', initialRtt: '250ms', maxRetries: '2', scanDelay: '0', maxTcpDelay: '5ms', maxUdpDelay: '1s', hostTimeout: '900s', minRate: ''}}
};

const NmapUI = {

  getStyles() {
    return `
      <style>
        .nmap-tool-section {
          background: #f8f9fa;
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 15px;
          border: 1px solid #e9ecef;
        }
        .nmap-tool-section h6 {
          font-size: 0.85rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: #6c757d;
          margin-bottom: 10px;
          font-weight: bold;
          display: flex;
          align-items: center;
        }
        .nmap-tool-section h6 i { 
          margin-right: 8px; 
        }
        .tooltip-inner {
          max-width: 300px !important;
          padding: 8px 10px;
          background-color: #212529 !important;
          color: #fff !important;
          text-align: left;
        }
        .tooltip .tooltip-inner strong {
          color: #fff !important;
        }
        .timing-overridden {
          border-color: #ffc107 !important;
          background-color: #fff3cd !important;
        }
        .timing-overridden::placeholder {
          color: #856404 !important;
        }
      </style>
    `;
  },

  createRadioGroup(prefix, name, values, descriptions) {
    return values.map(v => `
      <input type="radio" class="btn-check" 
             name="${prefix}${name}" 
             value="${v}" 
             id="${prefix}${v.replace('-','')}" 
             autocomplete="off">
      <label class="btn btn-outline-primary" 
             for="${prefix}${v.replace('-','')}" 
             title="${descriptions[v]}" 
             data-bs-toggle="tooltip">
        ${v.replace('-','')}
      </label>
    `).join('');
  },

  buildParams(prefix) {
    return `
      ${this.getStyles()}
      ${this.buildGeneralOptions(prefix)}
      ${this.buildTimingOptions(prefix)}
      ${this.buildScanTechniques(prefix)}
      ${this.buildDiscoveryOptions(prefix)}
      ${this.buildParseButton(prefix)}
    `;
  },

  buildGeneralOptions(prefix) {
    return `
      <div class="nmap-tool-section">
        <h6><i class="bi bi-gear-fill"></i> ${i18next.t("General Options & Ports")}</h6>
        
        <div class="row g-3 align-items-center">
          <div class="col-6">
            <div class="form-check form-switch">
              <input class="form-check-input" type="checkbox" id="${prefix}portsScan">
              <label class="form-check-label" for="${prefix}portsScan">
                ${i18next.t("Ports")}
              </label>
            </div>
          </div>
          <div class="col-6">
            <input type="text" 
                   list="${prefix}portsSelectorList" 
                   id="${prefix}portsSelector" 
                   class="form-control" 
                   placeholder="${i18next.t("Ports")}" 
                   disabled>
            <datalist id="${prefix}portsSelectorList">
              <option value="--top-ports 1000">${i18next.t("top-1000")}</option>
              <option value="--top-ports 100">${i18next.t("top-100")}</option>
              <option value="-p 80,443,8080,8443">${i18next.t("web ports")}</option>
              <option value="-p-">${i18next.t("All")}</option>
            </datalist>
          </div>
        </div>

        <div class="row mt-2">
          <div class="col-6">
            <div class="form-check form-switch" 
                 title="${i18next.t("Trace hop path to each host")}" 
                 data-bs-toggle="tooltip">
              <input class="form-check-input" type="checkbox" id="${prefix}trace" checked>
              <label class="form-check-label" for="${prefix}trace">
                ${i18next.t("TraceRoute")}
              </label>
            </div>
          </div>
          <div class="col-6">
            <div class="form-check form-switch" 
                 title="${i18next.t("Attempts to determine the version of the service running on port")}" 
                 data-bs-toggle="tooltip">
              <input class="form-check-input" type="checkbox" id="${prefix}service">
              <label class="form-check-label" for="${prefix}service">
                ${i18next.t("Service Version")}
              </label>
            </div>
          </div>
          <div class="col-6">
            <div class="form-check form-switch" 
                 title="${i18next.t("OS detection")}" 
                 data-bs-toggle="tooltip">
              <input class="form-check-input" type="checkbox" id="${prefix}stealth">
              <label class="form-check-label" for="${prefix}stealth">
                ${i18next.t("OS detection")}
              </label>
            </div>
          </div>
          <div class="col-6">
            <div class="form-check form-switch" 
                 title="${i18next.t("Disable host discovery. Port scan only.")}" 
                 data-bs-toggle="tooltip">
              <input class="form-check-input" type="checkbox" id="${prefix}pn">
              <label class="form-check-label" for="${prefix}pn">
                ${i18next.t("Skip discovery")}
              </label>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  buildScanTechniques(prefix) {
    const techniques = ['-sS','-sT','-sA','-sW','-sM','-sU','-sP'];
    return `
      <div class="nmap-tool-section">
        <h6><i class="bi bi-search"></i> ${i18next.t("Scan Techniques")}</h6>
        <div class="btn-group w-100" role="group">
          ${this.createRadioGroup(prefix, 'scanTechniques', techniques, NmapDescriptions.scanTechniques)}
        </div>
      </div>
    `;
  },

  getTimingTooltipContent() {
    return `
      <div style="font-size:0.7rem;line-height:1.3;color:#fff;min-width:260px">
        <div style="margin-bottom:6px;font-weight:600;border-bottom:1px solid #555;padding-bottom:4px">
          ${i18next.t("Timing templates")}
        </div>
        <div style="display:grid;gap:4px">
          <div><strong style="color:#fff">T0</strong> <span style="color:#aaa">Paranoid</span> — ${i18next.t("max stealth, very slow")}</div>
          <div><strong style="color:#fff">T1</strong> <span style="color:#aaa">Sneaky</span> — ${i18next.t("stealthy, slow scan")}</div>
          <div><strong style="color:#fff">T2</strong> <span style="color:#aaa">Polite</span> — ${i18next.t("polite, low load")}</div>
          <div><strong style="color:#fff">T3</strong> <span style="color:#aaa">Normal</span> — ${i18next.t("default balance")}</div>
          <div><strong style="color:#fff">T4</strong> <span style="color:#aaa">Aggressive</span> — ${i18next.t("fast, reliable nets")}</div>
          <div><strong style="color:#fff">T5</strong> <span style="color:#aaa">Insane</span> — ${i18next.t("max speed, risk losses")}</div>
        </div>
        <div style="margin-top:8px;font-size:0.65rem;color:#aaa;border-top:1px solid #444;padding-top:4px">
          • ${i18next.t("Select template or customize below")}<br>
          • ${i18next.t("Recommended: T4 for reliable networks")}<br>
          • ${i18next.t("T0/T1: very slow, for IDS evasion")}<br>
        </div>
      </div>
    `;
  },

  buildTimingOptions(prefix) {
    const fields = [
      {id:'minRtt', label:'min-rtt-timeout', placeholder:'100ms'},
      {id:'maxRtt', label:'max-rtt-timeout', placeholder:'10s'},
      {id:'initialRtt', label:'initial-rtt-timeout', placeholder:'1s'},
      {id:'maxRetries', label:'max-retries', placeholder:'10', type:'number'},
      {id:'scanDelay', label:'scan-delay', placeholder:'0'},
      {id:'maxTcpDelay', label:'max-tcp-scan-delay', placeholder:'1s'},
      {id:'maxUdpDelay', label:'max-udp-scan-delay', placeholder:'1s'},
      {id:'hostTimeout', label:'host-timeout', placeholder:'0'},
      {id:'minRate', label:'min-rate', placeholder:''},
      {id:'maxRate', label:'max-rate', placeholder:''},
    ];

    const tooltipContent = this.getTimingTooltipContent().replace(/"/g, '&quot;');
    return `
      <div class="nmap-tool-section">
        <h6>
          <i class="bi bi-speedometer2"></i> ${i18next.t("Performance")}
          <span class="ms-2" 
                id="${prefix}timingTooltipTrigger"
                data-bs-toggle="tooltip" 
                data-bs-html="true"
                data-bs-title="${tooltipContent}"
                style="cursor:help;color:#6c757d">
            <i class="bi bi-question-circle-fill small"></i>
          </span>
        </h6>
        
        <div class="row g-2 align-items-center">
          <div class="col-auto">
            <select class="form-select form-select-sm" id="${prefix}timingTemplate" style="min-width:140px">
              ${Object.entries(NmapTimingTemplates).map(([k,v]) => 
                `<option value="${k}" ${k==='T4'?'selected':''}>${k} — ${v.name}</option>`
              ).join('')}
            </select>
          </div>
          <div class="col">
            <button class="btn btn-sm btn-outline-secondary" type="button" 
                    data-bs-toggle="collapse" data-bs-target="#${prefix}timingAdvanced"
                    aria-expanded="false" aria-controls="${prefix}timingAdvanced">
              <i class="bi bi-sliders"></i> ${i18next.t("Advanced")}
            </button>
          </div>
        </div>
        
        <div class="collapse mt-3" id="${prefix}timingAdvanced">
          <div class="row g-2">
            ${fields.map(f => `
              <div class="col-6 col-md-4 col-lg-3">
                <label class="form-label small mb-1" for="${prefix}${f.id}">${f.label}</label>
                <input type="${f.type||'text'}" class="form-control form-control-sm timing-field" 
                      id="${prefix}${f.id}" data-field="${f.id}" 
                      placeholder="${f.placeholder}" value="">
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  },

  buildDiscoveryOptions(prefix) {
    const tcpUdp = ['-PA','-PS','-PU','-PY'];
    const icmp = ['-PE','-PP','-PM'];
    
    return `
      <div class="row g-2">
        <div class="col-md-7">
          <div class="nmap-tool-section h-100">
            <h6><i class="bi bi-broadcast"></i> ${i18next.t("TCP/UDP discovery")}</h6>
            <div class="btn-group w-100" role="group">
              ${this.createRadioGroup(prefix, 'portsDiscovery', tcpUdp, NmapDescriptions.discovery)}
            </div>
          </div>
        </div>
        <div class="col-md-5">
          <div class="nmap-tool-section h-100">
            <h6><i class="bi bi-shield-check"></i> ${i18next.t("ICMP request discovery")}</h6>
            <div class="btn-group w-100" role="group">
              ${this.createRadioGroup(prefix, 'requestDiscovery', icmp, NmapDescriptions.icmp)}
            </div>
          </div>
        </div>
      </div>
    `;
  },

  buildParseButton(prefix) {
    return `
      <button class="btn btn-primary w-100 mt-3 shadow-sm" id="${prefix}parseXmlBtn">
        <i class="bi bi-file-earmark-code me-2"></i>${i18next.t("Parse xml logs")}
      </button>
    `;
  }
};

const NmapHandlers = {

  setupPortSwitch(prefix) {
    const portSwitch = document.getElementById(`${prefix}portsScan`);
    const portInput = document.getElementById(`${prefix}portsSelector`);
    
    if (portSwitch && portInput) {
      FormHelpers.linkSwitchToInput(portSwitch, portInput);
    }
  },
  
  setupTimingTemplate(prefix) {
    const select = document.getElementById(`${prefix}timingTemplate`);
    const fields = document.querySelectorAll(`#${prefix}timingAdvanced .timing-field`);
    
    const applyTemplate = (templateKey) => {
      const values = NmapTimingTemplates[templateKey]?.values;
      if (!values) return;
      
      fields.forEach(field => {
        const key = field.dataset.field;
        const val = values[key] ?? '';
        field.value = val;
        field.placeholder = val || '';
        field.classList.remove('timing-overridden');
      });
    };

    applyTemplate('T4');
    
    select?.addEventListener('change', (e) => {
      applyTemplate(e.target.value);
    });
    
    fields.forEach(f => f.addEventListener('input', (e) => {
      const key = e.target.dataset.field;
      const templateKey = select.value;
      const templateVal = NmapTimingTemplates[templateKey]?.values?.[key] || '';
      const currentVal = e.target.value.trim();
      
      if (currentVal && currentVal !== templateVal) {
        e.target.classList.add('timing-overridden');
      } else {
        e.target.classList.remove('timing-overridden');
      }
      
    }));
  },

  setupToggleableRadios(prefix) {
    const radios = document.querySelectorAll(`input[type="radio"][id^="${prefix}"]`);
    FormHelpers.makeRadiosToggleable(radios);
  },

  async handleXmlParsing(instance) {
    const agentId = window.agentData?.default_agent;
    const iface = window.interfaceData?.default_interface;

    if (!agentId || !iface) {
      return;
    }

    try {
      const files = await FormHelpers.selectAndReadFiles('.xml', true);
      
      for (const { content, filename } of files) {
        const payload = {
          file: content,
          filename: filename,
          agent_id: String(agentId),
          interface_ip_id: String(iface.ip_id || iface.id),
          ip: String(iface.ip || ""),
          mac: String(iface.mac || "")
        };

        await fetch('/api/v1/task/nmap_parse_task', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }
      
      window[`close_${instance.modalId}`]();
    } catch (error) {
      console.error('Failed to parse XML files:', error);
    }
  },

  async handleNodeModal(instance, node) {
    const prefix = instance.prefix;
    
    instance.reset();
    
    const ipInput = document.getElementById(`${prefix}inputIP`);
    if (ipInput) {
      ipInput.value = node.label || '';
    }

    try {
      const response = await fetch(`/api/v1/vis/node_info/${node.id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      const portInput = document.getElementById(`${prefix}inputPort`);
      
      if (data.ports && portInput) {
        const ports = [...new Set(data.ports.map(p => p.port))].join(',');
        portInput.value = ports;
      }
    } catch (error) {
      console.error('Failed to load node ports:', error);
    }
    
    window[`show_${instance.modalId}`]();
  },

  handlePrefill(instance, rows = [], params = {}) {
    const prefix = instance.prefix;
    
    if (params?.agent_id) {
      instance.state.overrides.agent_id = params.agent_id;
    }
    if (params?.interface_ip_id && params?.agent_id) {
      window.getInterfaceData(params.agent_id).then(ifaceData => {
        if (ifaceData?.interfaces) {
          const ifaceObj = ifaceData.interfaces.find(
            i => i.ip_id == params.interface_ip_id
          );
          
          if (ifaceObj) {
            instance.state.overrides.interface_obj = ifaceObj;
            instance.state.overrides.interface_id = ifaceObj.id;
          }
        }
      });
    }

    instance.reset();
    
    const targetTab = document.getElementById(`${prefix}target-tab`);
    if (targetTab) {
      const tab = new bootstrap.Tab(targetTab);
      tab.show();
    }

    [['traceroute', 'trace'], ['serviceVersion', 'service'], 
    ['stealthScan', 'stealth'], ['skipDiscovery', 'pn']].forEach(([key, id]) => {
      if (typeof params[key] === 'boolean') {
        const el = document.getElementById(`${prefix}${id}`);
        if (el) el.checked = params[key];
      }
    });

    [['scanTechniques'], ['portsDiscovery'], ['requestDiscovery']].forEach(([key]) => {
      if (params[key]) {
        const radio = document.getElementById(`${prefix}${params[key].replace('-','')}`);
        if (radio) radio.checked = true;
      }
    });

    const timingFields = [
      'minRtt', 'maxRtt', 'initialRtt', 'maxRetries', 
      'scanDelay', 'maxTcpDelay', 'maxUdpDelay', 'hostTimeout',
      'minRate', 'maxRate'
    ];

    const select = document.getElementById(`${prefix}timingTemplate`);

    if (params.timingTemplate && NmapTimingTemplates[params.timingTemplate]) {
      select.value = params.timingTemplate;
      
      const templateValues = NmapTimingTemplates[params.timingTemplate].values;
      timingFields.forEach(field => {
        const input = document.getElementById(`${prefix}${field}`);
        const templateVal = templateValues[field] || '';
        if (input) {
          input.value = templateVal;
          input.placeholder = templateVal || '';
          input.classList.remove('timing-overridden');
        }
      });
      
      timingFields.forEach(field => {
        const paramVal = params[field];
        const templateVal = templateValues[field] || '';
        
        if (paramVal && paramVal !== templateVal) {
          const input = document.getElementById(`${prefix}${field}`);
          if (input) {
            input.value = paramVal;
            input.classList.add('timing-overridden');
          }
        }
      });
      
    } else {
      select.value = '';
      timingFields.forEach(field => {
        const input = document.getElementById(`${prefix}${field}`);
        const value = params[field];
        if (input && value) {
          input.value = value;
          input.placeholder = value;
        }
      });
    }

    if (params.targetPorts && params.targetPorts.trim() !== '-sn') {
      const portSwitch = document.getElementById(`${prefix}portsScan`);
      const portInput = document.getElementById(`${prefix}portsSelector`);
      
      if (portSwitch && portInput) {
        portSwitch.checked = true;
        portInput.disabled = false;
        
        let cleanValue = params.targetPorts.trim();
        if (cleanValue.startsWith('-p ')) cleanValue = cleanValue.slice(3);
        else if (cleanValue.startsWith('-p')) cleanValue = cleanValue.slice(2);
        
        portInput.value = cleanValue;
      }
    }

    const ipMap = new Map();
    rows.forEach(row => {
      const ip = (row.ipaddr || '').trim();
      const port = String(row.port || '').trim();
      
      if (!ip) return;
      
      const existing = ipMap.get(ip) || '';
      const combined = existing ? `${existing},${port}` : port;
      const uniquePorts = [...new Set(combined.split(',').filter(Boolean))].join(',');
      
      ipMap.set(ip, uniquePorts);
    });

    Array.from(ipMap.entries()).forEach(([ip, ports], index) => {
      if (index === 0) {
        const ipInput = document.getElementById(`${prefix}inputIP`);
        const portInput = document.getElementById(`${prefix}inputPort`);
        
        if (ipInput) ipInput.value = ip;
        if (portInput) portInput.value = ports;
      } else {
        instance.addInputField('ip_port', true);
        
        const container = document.getElementById(`${prefix}InputContainer`);
        const lastGroup = container?.lastElementChild;
        
        if (lastGroup) {
          const ipInput = lastGroup.querySelector('.ip');
          const portInput = lastGroup.querySelector('.port');
          
          if (ipInput) ipInput.value = ip;
          if (portInput) portInput.value = ports;
        }
      }
    });
    
    window[`show_${instance.modalId}`]();
  }
};

class NmapScanner {
  constructor(prefix) {
    this.prefix = prefix;
  }

  validateParams(targets = []) {
    const errors = [];
    const scanTech = this.getRadioValue('scanTechniques');
    const portsDiscovery = this.getRadioValue('portsDiscovery');
    const requestDiscovery = this.getRadioValue('requestDiscovery');
    const globalPorts = this.getGlobalPorts();
    const skipDiscovery = document.getElementById(`${this.prefix}pn`)?.checked;
    const serviceVer = document.getElementById(`${this.prefix}service`)?.checked;
    const stealth = document.getElementById(`${this.prefix}stealth`)?.checked;

    const isScopeMode = !Array.isArray(targets);
    const hasAnyPorts = isScopeMode 
    ? (globalPorts !== '-sn') 
    : (globalPorts !== '-sn') || targets.some(t => {
        const p = String(t.port || '').trim();
        return p && p !== 'null' && p !== 'undefined';
      });

    // 1. Если нет портов НИГДЕ — разрешена только -sP
    if (!isScopeMode && !hasAnyPorts && scanTech && scanTech !== '-sP') {
      errors.push('Port scan techniques require at least one target with ports specified');
    }

    // 2. Если выбрана -sP — нельзя указывать порты (ни глобально, ни в таргетах)
    if (!isScopeMode && scanTech === '-sP' && hasAnyPorts) {
      errors.push('Ping scan (-sP) cannot be combined with port specifications');
    }

    // 3. -sV / -O без портов = ошибка
    if (!isScopeMode && !hasAnyPorts && (serviceVer || stealth)) {
      errors.push('Service Version (-sV) and OS detection (-O) require ports on at least one target');
    }

    // 4. OS detection требует TCP-скана
    const tcpScans = ['-sS', '-sT', '-sA', '-sW', '-sM'];
    if (stealth && scanTech && !tcpScans.includes(scanTech)) {
      errors.push('OS detection (-O) requires TCP scan technique (-sS/-sT/etc.)');
    }

    // 5. -Pn + discovery probes = конфликт
    if (skipDiscovery && (portsDiscovery || requestDiscovery)) {
      errors.push('Discovery probes conflict with -Pn (skip host discovery)');
    }

    // 6. Тайминги: min ≤ initial ≤ max
    const timing = this.getTimingParams();
    const toMs = (v) => {
      if (!v) return null;
      const m = v.match(/^(\d+)(ms|s|m)?$/);
      if (!m) return null;
      const [, num, unit] = m;
      return parseInt(num) * ({ ms: 1, s: 1000, m: 60000 }[unit] || 1000);
    };
    const min = toMs(timing.minRtt), init = toMs(timing.initialRtt), max = toMs(timing.maxRtt);
    if (min != null && max != null && min > max) 
      errors.push('min-rtt-timeout cannot exceed max-rtt-timeout');
    if (init != null && min != null && init < min) 
      errors.push('initial-rtt-timeout cannot be less than min-rtt-timeout');

    return { valid: errors.length === 0, errors };
  }

  getRadioValue(name) {
    const radio = document.querySelector(`input[name="${this.prefix}${name}"]:checked`);
    return radio?.value || "";
  }

  getGlobalPorts() {
    const portSwitch = document.getElementById(`${this.prefix}portsScan`);
    if (!portSwitch?.checked) return "-sn";
    
    const portValue = document.getElementById(`${this.prefix}portsSelector`)?.value;
    if (!portValue) return "-sn";
    
    return portValue.startsWith('-') ? portValue : `-p ${portValue}`;
  }

  getTimingParams() {
    const prefix = this.prefix;
    const templateSelect = document.getElementById(`${prefix}timingTemplate`);
    const selectedTemplate = templateSelect?.value;
    
    const timingFields = [
      { id: 'minRtt', flag: '--min-rtt-timeout' },
      { id: 'maxRtt', flag: '--max-rtt-timeout' },
      { id: 'initialRtt', flag: '--initial-rtt-timeout' },
      { id: 'maxRetries', flag: '--max-retries' },
      { id: 'scanDelay', flag: '--scan-delay' },
      { id: 'maxTcpDelay', flag: '--max-tcp-scan-delay' },
      { id: 'maxUdpDelay', flag: '--max-udp-scan-delay' },
      { id: 'hostTimeout', flag: '--host-timeout' },
      { id: 'minRate', flag: '--min-rate' },
      { id: 'maxRate', flag: '--max-rate' },
    ];
    
    const params = {};
    
    if (selectedTemplate && NmapTimingTemplates[selectedTemplate]) {
      params.timingTemplate = selectedTemplate;
      const templateValues = NmapTimingTemplates[selectedTemplate].values;
      
      for (const field of timingFields) {
        const input = document.getElementById(`${prefix}${field.id}`);
        const manualValue = input?.value?.trim();
        const templateValue = templateValues[field.id] || '';
        
        if (manualValue && manualValue !== templateValue) {
          params[field.id] = manualValue;
        }
      }
    } else {
      for (const field of timingFields) {
        const input = document.getElementById(`${prefix}${field.id}`);
        const value = input?.value?.trim();
        if (value) params[field.id] = value;
      }
    }
    
    return params;
  }

  getBaseParams() {
    const agentId = window.agentData?.default_agent;
    const overrideAgent = this.instance?.state?.overrides?.agent_id;

    const agent_id = overrideAgent || agentId;

    const ifaceObj = this.instance?.state?.overrides?.interface_obj || window.interfaceData?.default_interface;
    if (!agent_id) {
      throw new Error("Please select an Agent");
    }
    if (!ifaceObj) {
      throw new Error("Please select an Interface");
    }

    return {
      agent_id: String(agent_id),
      interface: String(ifaceObj.name),
      interface_ip_id: String(ifaceObj.ip_id || ifaceObj.id),
      traceroute: !!document.getElementById(`${this.prefix}trace`)?.checked,
      serviceVersion: !!document.getElementById(`${this.prefix}service`)?.checked,
      stealthScan: !!document.getElementById(`${this.prefix}stealth`)?.checked,
      skipDiscovery: !!document.getElementById(`${this.prefix}pn`)?.checked,
      scanTechniques: this.getRadioValue('scanTechniques'),
      portsDiscovery: this.getRadioValue('portsDiscovery'),
      requestDiscovery: this.getRadioValue('requestDiscovery'),
      targetPorts: "",
      targetIP: null,
      scope_id: "",
      ...this.getTimingParams(),
    };
  }

  async scanScope(scopeId) {
    const baseParams = this.getBaseParams();
    const globalPorts = this.getGlobalPorts();
    
    const payload = { 
      ...baseParams, 
      scope_id: String(scopeId),
      targetPorts: globalPorts
    };

    const result = await window.executeToolTasks({
      tasks: [{ endpoint: '/api/v1/task/nmap_scan_task', payload }],
      stopOnFirstFailure: true
    });

    if (!result.success) {
      if (result.reason === 'module_install_requested') {
        return null;
      }
      throw new Error(result.error?.message || 'Scan failed');
    }
    return result.responses[0];
  }

  async scanTargets(targets) {
    const baseParams = this.getBaseParams();
    const globalPorts = this.getGlobalPorts();
    const tasks = [];
    const seen = new Set();

    for (const target of targets) {
      const targetIP = String(target.ip || target.domain || target.url || target.target || target).trim();
      if (!targetIP) continue;
      
      const targetPort = target.port ? String(target.port).trim() : '';
      const hasValidPort = targetPort && targetPort !== 'null' && targetPort !== 'undefined' && targetPort !== '';
      
      let finalPorts;
      if (hasValidPort) {
        const portsArray = targetPort.split(',')
          .map(p => p.trim())
          .filter(p => p && p !== 'null' && p !== 'undefined' && p !== '');
        
        if (portsArray.length > 0) {
          finalPorts = `-p ${portsArray.sort().join(',')}`; 
        } else {
          finalPorts = globalPorts;
        }
      } else {
        finalPorts = globalPorts;
      }
      
      const key = `${targetIP}:${finalPorts}`;
      if (seen.has(key)) continue;
      seen.add(key);
      
      const payload = { 
        ...baseParams,
        targetIP: targetIP,
        targetPorts: finalPorts
      };

      tasks.push({ endpoint: '/api/v1/task/nmap_scan_task', payload });
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
      throw new Error(result.error?.message || 'Scan failed');
    }

    return result.responses;
  }
}

const nmapModalConfig = {
  prefix: 'nmap_',
  
  tabs: [
    { id: 'target', label: i18next.t('Target'), targetType: 'ip_port' },
    { id: 'scope', label: i18next.t('Scope') },
    { id: 'database', label: i18next.t('Database') },
    { id: 'textarea', label: i18next.t('Textarea'), placeholder: '192.168.1.1:80\n192.168.1.10/24', textareaValidTypes: ['ip', 'ip_ports', 'network', 'network_ports'] },
  ],
  
  toolParams: (prefix) => NmapUI.buildParams(prefix),

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
          title: "Port", 
          field: "port", 
          headerFilter: "input", 
          headerFilterPlaceholder: "Search port..." 
        }
      ],
      filter: [
        { field: "ipaddr", type: "!=", value: "" }
      ]
    };
  },

  onInit(instance) {
    const prefix = instance.prefix;
    NmapHandlers.setupPortSwitch(prefix);
    NmapHandlers.setupToggleableRadios(prefix);
    NmapHandlers.setupTimingTemplate(prefix);

    setTimeout(() => {
      const tooltipTrigger = document.getElementById(`${prefix}timingTooltipTrigger`);
      if (tooltipTrigger && typeof bootstrap !== 'undefined') {
        new bootstrap.Tooltip(tooltipTrigger, { 
          html: true, 
          sanitize: false,
          trigger: 'hover focus',
          placement: 'auto'
        });
      }
    }, 200);
    
    const parseBtn = document.getElementById(`${prefix}parseXmlBtn`);
    if (parseBtn) {
      parseBtn.addEventListener('click', () => {
        NmapHandlers.handleXmlParsing(instance);
      });
    }

    const dbTabTrigger = document.getElementById(`${prefix}database-tab`);
    if (dbTabTrigger) {
      let tableInitialized = false;
      
      dbTabTrigger.addEventListener('shown.bs.tab', () => {
        if (!tableInitialized) {
          instance.initDatabaseTable();
          tableInitialized = true;
          
          setTimeout(() => {
            if (instance.databaseTable) {
              const originalRowSelectionChanged = instance.databaseTable.options.rowSelectionChanged;
              
              instance.databaseTable.options.rowSelectionChanged = function(data, rows) {
                const ipMap = new Map();
                
                rows.forEach((row) => {
                  const rowData = row.getData();
                  const ip = rowData.ipaddr;
                  const port = rowData.port;
                  const domain = rowData.domain;
                  
                  if (!ip) return;
                  
                  if (ipMap.has(ip)) {
                    const existing = ipMap.get(ip);
                    if (port && port !== 'null' && port !== 'undefined' && port !== '') {
                      existing.ports.add(port.toString());
                    }
                  } else {
                    const portsSet = new Set();
                    if (port && port !== 'null' && port !== 'undefined' && port !== '') {
                      portsSet.add(port.toString());
                    }
                    ipMap.set(ip, {
                      ip: ip,
                      domain: domain || '',
                      ports: portsSet
                    });
                  }
                });
                
                instance.state.selectedDatabaseTargets = {};
                ipMap.forEach((value, key) => {
                  instance.state.selectedDatabaseTargets[key] = value;
                });
              };
            }
          }, 100);
        }
      });
    }
    
    window.nmap_script_modal_to_node = (node) => NmapHandlers.handleNodeModal(instance, node);
    window.nmap_start_with_prefill = (rows, params = {}) => NmapHandlers.handlePrefill(instance, rows, params);
  },

  onReset(instance) {
    const prefix = instance.prefix;
    const trace = document.getElementById(`${prefix}trace`);
    if (trace) trace.checked = true;
    const stealth = document.getElementById(`${prefix}stealth`);
    if (stealth) stealth.checked = false;
    const portInput = document.getElementById(`${prefix}portsSelector`);
    if (portInput) portInput.disabled = true;
    instance.state.selectedDatabaseTargets = {};
    const timingSelect = document.getElementById(`${prefix}timingTemplate`);
    if (timingSelect) timingSelect.value = 'T4';
    NmapHandlers.setupTimingTemplate(prefix);
  },

  getTargets() {
    const tabId = this.getActiveTab();
    if (!tabId) return [];

    if (tabId === 'scope') {
      return { scope_id: this.state.selectedScopeId };
    }

    if (tabId === 'database') {
      const targets = [];
      
      Object.values(this.state.selectedDatabaseTargets).forEach(item => {
        const portsArray = Array.from(item.ports || [])
          .filter(p => p && p !== 'null' && p !== 'undefined' && p !== '');
        
        targets.push({
          ip: item.ip,
          domain: item.domain || '',
          port: portsArray.join(','),
          target: item.ip
        });
      });
      
      return targets;
    }

    if (tabId === 'target') {
      return this.getTargetsFromInputs();
    }

    if (tabId === 'textarea') {
      return this.getTargetsFromTextarea();
    }

    return [];
  },

  async onStart(instance) {
    const scanner = new NmapScanner(instance.prefix);
    const targets = instance.getTargets();
    const validation = scanner.validateParams(targets);
    if (!validation.valid) {
      create_toast("Warning", validation.errors.join('\n'), 'warning');
      return;
    }
    try {
      const tabId = instance.getActiveTab();
      let result;

      if (tabId === 'scope') {
        if (!instance.state.selectedScopeId) {
          throw new Error('Please select a scope');
        }
        result = await scanner.scanScope(instance.state.selectedScopeId);
      } else {
        if (!targets || targets.length === 0) {
          throw new Error('Please enter at least one target');
        }
        result = await scanner.scanTargets(targets);
      }

      if (result !== null) {
        window[`close_${instance.modalId}`]();
      }
    } catch (error) {
      console.error('Nmap scan error:', error);
      throw error;
    }
  }
};

window.openNmapModal = function () {
  if (document.getElementById('nmapModalWindow')) {
    show_nmapModalWindow();
    return;
  }
  createModal('nmapModalWindow', 'Nmap Tool', 'https://help.setezor.net/nmap');
  ToolModalBuilder.register('nmapModalWindow', nmapModalConfig);
  show_nmapModalWindow();
};