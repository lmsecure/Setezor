/**
 * Логика страницы /info — сборка вкладок, ленивая загрузка таблиц.
 *
 * Зависимости (подключены через <script> в base.html):
 *   Tabulator, bootstrap, XLSX, jspdf, i18next, axios
 *
 */

import TabulatorTable from '/static/js/src/tabulator/TabulatorTable.js';
import ExportManager from '/static/js/src/tabulator/exportManager.js';
import ScopeManager from '/static/js/src/tabulator/scopeManager.js';
import ScreenshotViewer from '/static/js/src/tabulator/screenshotViewer.js';
import VulnsModal from '/static/js/src/tabulator/vulnsModal.js';
import LogViewer from '/static/js/src/tabulator/logViewer.js';
import CommentsManager from '/static/js/src/tabulator/commentsManager.js';

// ─── Конфигурация страницы ──────────────────────────────────────────────────

const TABS_WITH_CHECKBOX = new Set([
  'open_ports', 'ip_domain', 'web_screenshot',
  'auth_credentials', 'ip_info', 'domain_info', 'web',
]);

const LAYOUT_MAP = {
  auth_credentials: 'fitDataStretch',
  web: 'fitDataStretch',
  cve: 'fitDataStretch',
};

const TAB_TOOLS = {
  ip_info: ['nmap', 'masscan', 'whois'],
  domain_info: ['lookup', 'brute', 'web_grabber', 'whois'],
  open_ports: ['nmap', 'masscan', 'cert', 'snmp', 'whois', 'brute', 'lookup', 'web_grabber'],
  ip_domain: ['nmap', 'masscan', 'whois', 'brute', 'lookup', 'web_grabber'],
  web: ['nmap', 'masscan', 'whois', 'brute', 'lookup', 'web_grabber'],
  web_screenshot: ['nmap', 'masscan', 'whois', 'brute', 'lookup', 'web_grabber'],
  auth_credentials: ['nmap', 'masscan', 'whois', 'brute', 'lookup', 'web_grabber'],
};
// можно фильтровать по нескольким параметрам [['ipaddr', 'port'], ['domain', 'port']],
const TAB_SCOPE_KEY_FIELDS = {
  ip_info:          [['ipaddr']],
  cve:              [['ipaddr']],
  open_ports:       [['ipaddr']],
  ip_domain:        [['ipaddr'], ['domain']],
  web:              [['ipaddr'], ['domain']],
  auth_credentials: [['ipaddr'], ['domain']],
  web_screenshot:   [['ip'],['domain']],
  domain_info:      [['domain']],
};

// ─── Состояние страницы ─────────────────────────────────────────────────────

let selectedScans = [];

const registry = new Map();

// ─── Глобальные синглтоны ──────────────────────────────────────────

window.__tables = {};
window.__vulnsModal = new VulnsModal();
window.__logViewer = new LogViewer();
window.__commentsManager = new CommentsManager();
window.__screenshotViewer = new ScreenshotViewer(
  () => window.__tables['web_screenshot']?.getInstance()?.getData() || []
);

function buildTabs(tabsConfig) {
  const tabButtons = document.getElementById('tab_buttons');
  const tabContent = document.getElementById('nav-tabContent');

  tabsConfig.forEach((tab, index) => {
    const isFirst = index === 0;
    const tools = TAB_TOOLS[tab.name] || [];

    const tabLabel = tab.name.toLowerCase().replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    tabButtons.insertAdjacentHTML('beforeend', `
      <li class="nav-item" role="presentation">
        <button
          class="nav-link py-1 px-2 small ${isFirst ? 'active' : ''}"
          id="infotabs-${tab.name}"
          data-bs-toggle="tab"
          data-bs-target="#tab-content-${tab.name}"
          data-tab-anchor="${tab.name}"
          type="button" role="tab"
        >${tabLabel}</button>
      </li>`);

    tabContent.insertAdjacentHTML('beforeend', `
      <div class="tab-pane fade${isFirst ? ' show active' : ''}"
        id="tab-content-${tab.name}" role="tabpanel">

        <!-- ── Тулбар ── -->
        <div class="d-flex align-items-center gap-1 pt-1 flex-wrap mb-2">

          <!-- Фильтры (toggle) -->
          <button class="btn btn-outline-secondary btn-sm"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#filter-panel-${tab.name}"
            aria-expanded="false"
            aria-controls="filter-panel-${tab.name}"
            id="filter-toggle-btn-${tab.name}">
            <i class="bi bi-funnel"></i>
            <span data-i18n="Filters"></span>

          </button>

          <!-- Reload -->
          <button class="btn btn-outline-secondary btn-sm"
            onclick="reloadTab('${tab.name}')"
            title="Reload">
            <i class="bi bi-arrow-clockwise"></i>
          </button>

          <div class="vr mx-1"></div>

          ${tools.length ? `
          <!-- Инструмент + Start -->
          <select class="form-select form-select-sm" style="width:auto;"
            id="filter-tools-${tab.name}">
            ${tools.map(t => `<option value="${t}">${t}</option>`).join('')}
          </select>
          <button class="btn btn-success btn-sm"
            onclick="openModalTools('${tab.name}')" data-i18n="Start">Start</button>
          <div class="vr mx-1"></div>` : ''}

          <!-- Export dropdown -->
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-secondary dropdown-toggle" type="button"
              data-bs-toggle="dropdown" aria-expanded="false">
              <i class="bi bi-download"></i>
              <span data-i18n="Export">Export</span>
            </button>
            <ul class="dropdown-menu">
              <li><a class="dropdown-item" href="#" onclick="triggerExport('${tab.name}','csv')">CSV</a></li>
              <li><a class="dropdown-item" href="#" onclick="triggerExport('${tab.name}','json')">JSON</a></li>
              <li><a class="dropdown-item" href="#" onclick="triggerExport('${tab.name}','xlsx')">Excel</a></li>
              <li><a class="dropdown-item" href="#" onclick="triggerExport('${tab.name}','pdf')">PDF</a></li>
            </ul>
          </div>

          <!-- Правая часть: scope + scans -->
          <div class="ms-auto d-flex align-items-center gap-1">
            <div id="global-scope-dropdown-placeholder-${tab.name}" class="dropdown" style="width:10rem;"></div>
            <button class="btn btn-outline-primary btn-sm"
              data-bs-toggle="modal" data-bs-target="#global-scans-modal">
              <span data-i18n="Pick scans">Scans</span>
            </button>
          </div>
        </div>

        <!-- ── Панель фильтров (collapse) ── -->
        <div class="collapse mt-1" id="filter-panel-${tab.name}">
          <!-- filter-panel-container — рендерится initFilterPanelContainer -->
          <div id="filter-panel-container-${tab.name}"></div>
        </div>



        <!-- Модалка экспорта -->
        <div class="modal fade" id="${tab.name}_exportModal" tabindex="-1" aria-hidden="true">
          <div class="modal-dialog">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title" data-i18n="Export Options"></h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
              </div>
              <div class="modal-body">
                <div class="form-check">
                  <input class="form-check-input" type="radio" name="${tab.name}_exportType"
                    id="${tab.name}_exportCurrent" value="current" checked>
                  <label class="form-check-label" for="${tab.name}_exportCurrent" data-i18n="Current page"></label>
                </div>
                <div class="form-check">
                  <input class="form-check-input" type="radio" name="${tab.name}_exportType"
                    id="${tab.name}_exportAll" value="all">
                  <label class="form-check-label" for="${tab.name}_exportAll" data-i18n="The whole table"></label>
                </div>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" data-i18n="Cancel"></button>
                <button type="button" class="btn btn-primary"
                  onclick="confirmExport('${tab.name}')" data-i18n="Export"></button>
              </div>
            </div>
          </div>
        </div>

        <!-- Модалка комментариев -->
        <div class="modal fade" id="${tab.name}commentsModal" tabindex="-1"
          data-bs-backdrop="static" aria-hidden="true">
          <div class="modal-dialog modal-lg">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title" data-i18n="Comments"></h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
              </div>
              <div class="modal-body">
                <div id="${tab.name}commentsContainer">
                  <div class="d-flex justify-content-center">
                    <div class="spinner-border" role="status"></div>
                  </div>
                </div>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" data-i18n="Close"></button>
              </div>
            </div>
          </div>
        </div>

        <!-- Контейнер таблицы -->
        <div id="${tab.name}-table"></div>
      </div>`);
  });
}

const GLOBAL_SCOPE_DROPDOWN_HTML = `
  <button class="btn btn-outline-secondary btn-sm dropdown-toggle w-100 text-start"
    type="button" data-bs-toggle="dropdown"
    data-bs-auto-close="outside"
    id="scope-selector-btn-global">
    <span id="scope-selector-label-global">${i18next.t('Scopes')}</span>
  </button>
  <ul class="dropdown-menu" id="scope-selector-global"></ul>`;

async function initGlobalScopeDropdown() {
  const master = document.createElement('div');
  master.id = 'global-scope-master';
  master.className = 'dropdown';
  master.style.cssText = 'width:10rem;position:absolute;left:-9999px;';
  master.innerHTML = GLOBAL_SCOPE_DROPDOWN_HTML;
  document.body.appendChild(master);

  try {
    const resp   = await fetch('/api/v1/scope');
    const json   = await resp.json();
    const scopes = json.data ?? json;
    const container = document.getElementById('scope-selector-global');

    scopes.forEach(scope => {
      window.globalScopeIdToName = window.globalScopeIdToName || {};
      window.globalScopeIdToName[String(scope.id)] = scope.name;
      container.insertAdjacentHTML('beforeend', `
        <li>
          <label class="dropdown-item">
            <input type="checkbox" class="scope-checkbox-global" value="${scope.id}">
            ${scope.name}
          </label>
        </li>`);
    });

    container.querySelectorAll('.scope-checkbox-global').forEach(cb => {
      cb.addEventListener('change', () => {
        updateGlobalScopeButtonLabel();
        const activeTab = document.querySelector('#tab_buttons .nav-link.active');
        const tabName = activeTab?.getAttribute('data-bs-target')?.replace('#tab-content-', '');
        if (tabName) registry.get(tabName)?.scope.applyHighlight();
      });
    });
  } catch(e) {
    console.error('Failed to load global scopes:', e);
  }

  mountGlobalDropdownToActive();
}

function mountGlobalDropdownToActive() {
  const activeTab = document.querySelector('#tab_buttons .nav-link.active');
  const tabName = activeTab?.getAttribute('data-bs-target')?.replace('#tab-content-', '');
  if (tabName) mountGlobalDropdownTo(tabName);
}

function mountGlobalDropdownTo(tabName) {
  const placeholder = document.getElementById(`global-scope-dropdown-placeholder-${tabName}`);
  const master = document.getElementById('global-scope-master');
  if (!placeholder || !master) return;
  placeholder.appendChild(master);
  master.style.cssText = '';
}

function updateGlobalScopeButtonLabel() {
  const lbl = document.getElementById('scope-selector-label-global');
  if (!lbl) return;
  const names = Array.from(
    document.querySelectorAll('.scope-checkbox-global:checked')
  ).map(cb => cb.closest('label')?.textContent.trim() || '');
  lbl.textContent = names.length === 0 ? i18next.t('Scopes')
    : names.length <= 2               ? names.join(', ')
    : `${names.length} selected`;
}



function registerTabs(tabsConfig) {
  tabsConfig.forEach(tab => {
    const tableComponent = new TabulatorTable({
      height: "80vh",
      containerId: `${tab.name}-table`,
      ajaxUrl: tab.base_url,
      columns: tab.columns,
      layout: LAYOUT_MAP[tab.name],
      hasCheckbox: TABS_WITH_CHECKBOX.has(tab.name),
      getExtraParams: () => ({ scans: selectedScans }),
      onBuilt: (instance) => {
        const filterFields = tab.columns
          .filter(c => !['ID', 'Vulnerabilities', 'Comments', 'Range IP', 'Data',
            'Country', 'Created', 'Expires', 'Nameservers', 'Contacts',
            'Org-name', 'EXTRA_DATA', 'SCREENSHOT'].includes(c.title))
          .map(c => ({ field: c.field, title: c.title }));

        if (typeof initFilterPanelContainer === 'function') {
          initFilterPanelContainer({
            tableId: tab.name,
            tableVar: instance.getInstance(),
            fields: filterFields,
            containerId: `filter-panel-container-${tab.name}`,
            allowMultipleFilters: true,
          });
        }
      },
      onDataLoaded: () => {
        const entry = registry.get(tab.name);
        entry?.scope.applyHighlight();
      },
    });

    const exporter = new ExportManager(
      tableComponent,
      tab.name,
      () => ({ scans: selectedScans })
    );

    const scope = new ScopeManager({
      tabName: tab.name,
      keyFields: TAB_SCOPE_KEY_FIELDS[tab.name] || ['ipaddr'],
      getTableInstance: () => tableComponent.getInstance(),
      getSelectedRows: () => tableComponent.getSelectedRows(),
    });

    registry.set(tab.name, {
      tab,
      table: tableComponent,
      exporter,
      scope,
      loaded: false,
    });

    window.__tables[tab.name] = tableComponent;
  });
}

function loadTabIfNeeded(tabName) {
  const entry = registry.get(tabName);
  if (!entry || entry.loaded) return;

  entry.loaded = true;
  entry.table.init();
}

async function initGlobalScansModal() {
  const modal = document.createElement('div');
  modal.id = 'global-scans-modal';
  modal.className = 'modal fade';
  modal.setAttribute('tabindex', '-1');
  modal.setAttribute('aria-hidden', 'true');
  modal.innerHTML = `
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 data-i18n="Pick scans"></h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <form onsubmit="applyScansFilter(event)">
          <div class="modal-body" id="global-scans-container">
            <div class="d-flex justify-content-center">
              <div class="spinner-border spinner-border-sm" role="status"></div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" data-i18n="Close"></button>
            <button type="submit" class="btn btn-primary" data-bs-dismiss="modal" data-i18n="Show"></button>
          </div>
        </form>
      </div>
    </div>`;
  document.body.appendChild(modal);
  if (typeof updateContent === 'function') updateContent();

  try {
    const resp = await fetch('/api/v1/scan');
    const scans = await resp.json();
    const el = document.getElementById('global-scans-container');
    if (!el) return;
    el.innerHTML = scans.map(scan => `
      <div class="form-check">
        <input class="form-check-input scan-checkbox-global" type="checkbox"
          value="${scan.id}" id="global_scan_${scan.id}">
        <label class="form-check-label" style="word-break:break-all;white-space:normal"
          for="global_scan_${scan.id}">
          ${scan.name} - ${scan.created_at}
        </label>
      </div>`).join('');
    _restoreScansCheckboxes();
  } catch (e) {
    console.error('Failed to load global scans:', e);
  }
}

function _restoreScansCheckboxes() {
  document.querySelectorAll('.scan-checkbox-global').forEach(cb => {
    cb.checked = selectedScans.includes(cb.value);
  });
}

window.triggerExport = (tabName, format) => {
  registry.get(tabName)?.exporter.trigger(format);
};

window.confirmExport = (tabName) => {
  registry.get(tabName)?.exporter.confirm();
};

window.applyScansFilter = (event) => {
  event.preventDefault();
  selectedScans = Array.from(
    document.querySelectorAll('.scan-checkbox-global:checked')
  ).map(cb => cb.value);

  registry.forEach((entry) => {
    if (entry.loaded) entry.table.reload();
  });
};

window.openModalTools = (tabName) => {
  const toolEl = document.getElementById(`filter-tools-${tabName}`);
  if (!toolEl) return;
  const tool = toolEl.value;
  const entry = registry.get(tabName);
  if (!entry) return;
  
  const rows = entry.table.getAndClearSelection();
  console.log(`Selected rows for ${tabName}:`, rows);

const toolFns = {
  nmap: () => {
    openNmapModal();
    if (rows?.length) nmap_start_with_prefill(rows);
  },
  masscan: () => {
    openMasscanModal();
    if (rows?.length) masscan_start_with_prefill(rows);
  },
  lookup: () => {
    openLookupModal();
    if (rows?.length) lookup_start_with_prefill(rows);
  },
  cert: () => {
    openCertModal();
    if (rows?.length) cert_start_with_prefill(rows);
  },
  whois: () => {
    openWhoisModal();
    if (rows?.length) whois_start_with_prefill(rows);
  },
  web_grabber: () => {
    openWebGrabberModal();
    if (rows?.length) web_grabber_start_with_prefill(rows);
  },
  brute: () => {
    openBruteModal();
    if (rows?.length) brute_start_with_prefill(rows);
  },
  snmp: () => {
    openSnmpModal();
    if (rows?.length) snmp_start_with_prefill(rows);
  },
};
  toolFns[tool]?.();
};

// Reload удалить когда добавление фильтров изменится
window.reloadTab = (tabName) => {
  registry.get(tabName)?.table.reload();
};

async function initPage() {
  try {
    const resp = await fetch('/api/v1/analytics/tabs_config');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const tabsConfig = await resp.json();

    buildTabs(tabsConfig);
    if (typeof updateContent === 'function') updateContent();
    registerTabs(tabsConfig);
    await initGlobalScopeDropdown();
    await initGlobalScansModal();

    const hashTab = location.hash.replace('#', '');
    const initialTab = (hashTab && registry.has(hashTab)) ? hashTab : tabsConfig[0]?.name;

    if (initialTab) {
      if (hashTab && hashTab !== tabsConfig[0]?.name && registry.has(hashTab)) {
        document.querySelectorAll('#tab_buttons .nav-link').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('#nav-tabContent .tab-pane').forEach(p => p.classList.remove('show', 'active'));
        const btn = document.getElementById(`infotabs-${initialTab}`);
        if (btn) btn.classList.add('active');
        document.getElementById(`tab-content-${initialTab}`)?.classList.add('show', 'active');
      }
      loadTabIfNeeded(initialTab);
      mountGlobalDropdownTo(initialTab);
    }

    document.getElementById('tab_buttons').addEventListener('shown.bs.tab', e => {
      const tabName = e.target.getAttribute('data-bs-target')?.replace('#tab-content-', '');
      if (!tabName) return;
      history.replaceState(null, '', `#${tabName}`);
      loadTabIfNeeded(tabName);
      mountGlobalDropdownTo(tabName);
      updateGlobalScopeButtonLabel();
      registry.get(tabName)?.scope.applyHighlight();
    });

  } catch (e) {
    console.error('Failed to initialize page:', e);
    document.getElementById('nav-tabContent').innerHTML =
      `<div class="alert alert-danger m-3">Ошибка загрузки конфигурации: ${e.message}</div>`;
  }
}

if (window.i18nReady) {
  initPage();
} else {
  document.addEventListener('i18nReady', initPage);
}