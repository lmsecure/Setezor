/**
 * Универсальный переиспользуемый компонент таблицы на базе Tabulator.
 *
 * Использование:
 *   import TabulatorTable from './TabulatorTable.js';
 *
 *   const table = new TabulatorTable({
 *     containerId: 'my-table',        // id div-контейнера
 *     ajaxUrl: '/api/v1/data',        // URL данных (опционально, если есть ajaxRequestFunc)
 *     ajaxRequestFunc: queryRealm,    // кастомная функция запроса (опционально)
 *     columns: [...],                 // конфиг колонок (field, title, width, tooltip...)
 *     layout: 'fitColumns',           // опционально
 *     hasCheckbox: true,              // добавить колонку с чекбоксами
 *     getExtraParams: () => ({        // опционально — доп. параметры к запросу
 *       scans: selectedScans
 *     }),
 *     onBuilt: (instance) => {},      // колбэк после построения
 *     onDataLoaded: (instance) => {}, // колбэк после загрузки данных
 *   });
 *
 *   table.init();        // создать таблицу и загрузить первую страницу
 *   table.reload();      // перезагрузить с текущими параметрами
 *   table.getInstance(); // получить Tabulator instance
 */

import { getFormatterForField } from './formatters.js';

const FIELD_HOZALIGN = {
  data: 'center',
  nameservers: 'left',
  contacts: 'left',
};

const FIELD_NO_SORT = new Set(['screenshot_path', 'data', 'comments', 'vulns_btn']);

export default class TabulatorTable {
  constructor(options) {
    this.options = options;
    this._instance = null;
    this._initialized = false;
    this._tabName = options.containerId.replace('-table', '');
    this._isRestoring = false;

    this._selection = {};
  }

  init() {
    if (this._initialized) return;
    this._initialized = true;

    const {
      containerId,
      ajaxUrl,
      ajaxRequestFunc,
      columns,
      layout,
      hasCheckbox,
      getExtraParams,
      onBuilt,
      onDataLoaded,
    } = this.options;

    const tableConfig = {
      layout: layout || 'fitColumns',
      selectable: hasCheckbox ? true : false,
      selectableRangeMode: 'click',
      selectableCheck: () => true,
      selectablePersistence: false,
      sortMode: 'remote',
      filterMode: 'remote',
      pagination: true,
      paginationMode: 'remote',
      paginationSize: 50,
      paginationInitialPage: 1,
      paginationSizeSelector: [5, 10, 25, 50, 100, 250, 500],
      validationMode: 'highlight',
      rowHeight: 'auto',
      columns: this._buildColumns(columns, hasCheckbox),
      height: this.options.height || undefined,
      renderVertical: this.options.height ? "basic" : undefined,
      renderVertical: "basic",
    };

// ПРИМЕР ИСПОЛЬЗОВАНИЯ ajaxRequestFunc (Возможно его нужно доработать, может не отработать)
// function queryRealm(url, config, params) {
//   return new Promise((resolve, reject) => {
//     fetch(url, {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify(params)
//     })
//     .then(res => res.json())
//     .then(resolve)
//     .catch(reject);
//   });
// }

// const table = new TabulatorTable({
//   containerId: 'my-table',
//   ajaxRequestFunc: queryRealm,
//   columns: [...],
//   getExtraParams: () => ({ scans: selectedScans })
// });

    if (ajaxRequestFunc) {
      tableConfig.ajaxRequestFunc = (url, config, params) => {
        const extra = getExtraParams?.() || {};
        return ajaxRequestFunc(url, config, { ...params, ...extra });
      };
    } else if (ajaxUrl) {
      tableConfig.ajaxURL = ajaxUrl;
      tableConfig.ajaxURLGenerator = (url, config, params) =>
        this._buildUrl(url, params, getExtraParams?.());
    } else {
      throw new Error('Необходимо указать либо ajaxUrl, либо ajaxRequestFunc');
    }

    this._instance = new Tabulator(`#${containerId}`, tableConfig);

    this._instance.on('tableBuilt', () => {
      if (hasCheckbox) {
        this._loadFromStorage();
      }
      onBuilt?.(this);
    });

    this._instance.on('dataLoaded', () => {
      if (hasCheckbox) {
        setTimeout(() => {
          this._restoreSelection();
        }, 0);
      }
      onDataLoaded?.(this);
    });

    if (hasCheckbox) {
      this._instance.on('rowSelected', (row) => {
        if (this._isRestoring) return;
        const data = row.getData();
        if (data.id != null) {
          this._selection[data.id] = data;
          this._saveToStorage();
          this._updateHeaderButton();
        }
      });

      this._instance.on('rowDeselected', (row) => {
        if (this._isRestoring) return;
        const data = row.getData();
        if (data.id != null) {
          delete this._selection[data.id];
          this._saveToStorage();
          this._updateHeaderButton();
        }
      });
    }
  }

  reload() {
    if (!this._instance) return;
    if (this.options.ajaxRequestFunc) {
      this._instance.replaceData();
    } else {
      this._instance.setData(this._instance.getAjaxUrl(), {}, 'GET');
    }
  }

  getInstance() {
    return this._instance;
  }

  getSelectedRows() {
    if (!this.options.hasCheckbox) return [];
    return Object.values(this._selection);
  }

  getAndClearSelection() {
    const rows = this.getSelectedRows();
    this.clearAllSelections();
    return rows;
  }

  toggleSelectAll() {
    if (!this._instance || !this.options.hasCheckbox) return;

    const currentPageRows = this._instance.getRows();
    const allSelected = currentPageRows.every(r => this._selection[r.getData().id] != null);

    if (allSelected) {
      this._instance.deselectRow(currentPageRows);
    } else {
      const toSelect = currentPageRows.filter(r => this._selection[r.getData().id] == null);
      this._instance.selectRow(toSelect);
    }

    this._updateHeaderButton();
  }

  clearAllSelections() {
    if (!this._instance || !this.options.hasCheckbox) return;
    this._selection = {};
    this._saveToStorage();
    this._instance.deselectRow();
    this._updateHeaderButton();
  }

  getVisibleColumns() {
    return (this._instance?.getColumns() || []).filter(col => {
      const def = col.getDefinition();
      return col.isVisible() && def.field && def.field !== 'select';
    });
  }

  // ─── Private ───────────────────────────────────────────────────────────────

  _restoreSelection() {
    if (!this._instance) return;
    const ids = Object.keys(this._selection);
    if (ids.length === 0) return;

    this._isRestoring = true;
    this._instance.getRows().forEach(row => {
      const data = row.getData();
      if (data.id != null && this._selection[data.id] != null) {
        row.select();
      }
    });
    this._isRestoring = false;

    this._updateHeaderButton();
  }

  _saveToStorage() {
    try {
      const rows = Object.values(this._selection);
      if (rows.length > 0) {
        sessionStorage.setItem(`${this._tabName}_sel`, JSON.stringify(rows));
      } else {
        sessionStorage.removeItem(`${this._tabName}_sel`);
      }
    } catch (e) {
      console.warn('TabulatorTable: failed to save selection', e);
    }
  }

  _loadFromStorage() {
    try {
      const raw = sessionStorage.getItem(`${this._tabName}_sel`);
      if (raw) {
        const rows = JSON.parse(raw);
        this._selection = {};
        rows.forEach(row => {
          if (row.id != null) this._selection[row.id] = row;
        });
      }
    } catch (e) {
      console.warn('TabulatorTable: failed to load selection', e);
    }
  }

  _updateHeaderButton() {
    const headerEl = document.querySelector(
      `#${this.options.containerId} .tabulator-col[data-field="select"] .tabulator-col-content`
    );
    if (!headerEl) return;

    const currentPageRows = this._instance?.getRows() || [];
    if (currentPageRows.length === 0) return;

    const allSelected = currentPageRows.every(r => this._selection[r.getData().id] != null);
    const someSelected = currentPageRows.some(r => this._selection[r.getData().id] != null);

    let icon, title;
    if (allSelected) {
      icon = 'bi-check2-square'; title = 'Deselect all on page';
    } else if (someSelected) {
      icon = 'bi-dash-square';   title = 'Select all on page';
    } else {
      icon = 'bi-square';        title = 'Select all on page';
    }

    const btn = headerEl.querySelector('.select-all-btn');
    if (btn) {
      btn.innerHTML = `<i class="bi ${icon}"></i>`;
      btn.title = title;
    }
  }

  _buildUrl(url, params, extra = {}) {
    const sort = encodeURIComponent(JSON.stringify(params.sort || []));
    const filter = encodeURIComponent(JSON.stringify(params.filter || []));
    const extraParts = Object.entries(extra).flatMap(([key, val]) =>
      Array.isArray(val)
        ? val.map(v => `${encodeURIComponent(key)}=${encodeURIComponent(v)}`)
        : [`${encodeURIComponent(key)}=${encodeURIComponent(val)}`]
    ).join('&');
    return `${url}?page=${params.page}&size=${params.size}&sort=${sort}&filter=${filter}${extraParts ? `&${extraParts}` : ''}`;
  }

  _buildColumns(columnDefs, hasCheckbox) {
    const cols = [];

    if (hasCheckbox) {
      cols.push({
        title: this._renderHeaderButton(),
        field: 'select',
        formatter: 'rowSelection',
        width: 50,
        minWidth: 50,
        hozAlign: 'center',
        headerHozAlign: 'center',
        headerSort: false,
        frozen: true,
        resizable: false,
        cssClass: 'text-center',
        cellClick: (e, cell) => {           // ← добавить это
          if (!e.target.closest('input')) {
            cell.getRow().toggleSelect();
          }
        },
        headerClick: (e) => {
          if (e.target.closest('.select-all-btn')) {
            this.toggleSelectAll();
          }
        },
      });
    }

    columnDefs.forEach(col => {
      const formatter = getFormatterForField(col.field);
      const def = {
        title: col.title,
        field: col.field,
        headerMenu: this._headerMenu.bind(this),
      };
      if (col.tooltip) def.tooltip = true;
      if (col.width) def.width = col.width;
      if (formatter) def.formatter = formatter;
      if (FIELD_NO_SORT.has(col.field)) def.headerSort = false;
      if (FIELD_HOZALIGN[col.field]) def.hozAlign = FIELD_HOZALIGN[col.field];
      cols.push(def);
    });

    return cols;
  }

  _renderHeaderButton() {
    return `<div class="d-flex justify-content-center">
      <button class="btn btn-sm btn-outline-secondary select-all-btn p-0 border-0"
        style="width:30px; height:30px;"
        title="Select/Deselect all on page">
        <i class="bi bi-square"></i>
      </button>
    </div>`;
  }

  _headerMenu() {
    const menu = [];

    if (this.options.hasCheckbox) {
      menu.push({
        label: '<i class="bi bi-check-all"></i> Select All Page',
        action: (e) => { e.stopPropagation(); this.toggleSelectAll(); },
      });
      menu.push({
        label: '<i class="bi bi-x-circle"></i> Clear All Selections',
        action: (e) => { e.stopPropagation(); this.clearAllSelections(); },
      });
      menu.push({ separator: true });
    }

    (this._instance?.getColumns() || []).forEach(column => {
      const def = column.getDefinition();
      if (!def.field || def.field === 'select') return;

      const icon = document.createElement('i');
      icon.classList.add('bi', column.isVisible() ? 'bi-check-square' : 'bi-square');
      const title = document.createElement('span');
      title.textContent = ' ' + def.title;
      const label = document.createElement('span');
      label.appendChild(icon);
      label.appendChild(title);

      menu.push({
        label,
        action: (e) => {
          e.stopPropagation();
          column.toggle();
          this._instance.redraw();
        },
      });
    });

    return menu;
  }
}