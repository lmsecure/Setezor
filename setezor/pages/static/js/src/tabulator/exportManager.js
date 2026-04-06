/**
 * Управляет экспортом данных таблицы в CSV, JSON, XLSX, PDF.
 *
 * Использование:
 *   import ExportManager from './exportManager.js';
 *   const exporter = new ExportManager(tabulatorTableInstance, tabName);
 *   exporter.trigger('csv');   // открыть модалку выбора scope экспорта
 */

export default class ExportManager {
  constructor(tableComponent, tabName, getExtraParams) {
    this._table          = tableComponent;
    this._tabName        = tabName;
    this._getExtraParams = getExtraParams || (() => ({}));
    this._pendingFormat  = null;
  }

  /** Открыть модалку выбора режима (текущая страница / всё) */
  trigger(format) {
    this._pendingFormat = format;
    bootstrap.Modal.getOrCreateInstance(
      document.getElementById(`${this._tabName}_exportModal`)
    ).show();
  }

  confirm() {
    const radio = document.querySelector(`input[name="${this._tabName}_exportType"]:checked`);
    if (!radio) return;
    bootstrap.Modal.getInstance(
      document.getElementById(`${this._tabName}_exportModal`)
    )?.hide();

    if (radio.value === 'current') {
      this._export(this._pendingFormat, this._table.getInstance().getData());
    } else {
      this._fetchAllAndExport(this._pendingFormat);
    }
  }

  // ─── Private ───────────────────────────────────────────────────────────────

  async _fetchAllAndExport(fmt) {
    try {
      const instance = this._table.getInstance();
      const filters  = instance.getFilters().map(f => ({ field: f.field, type: f.type, value: f.value }));
      const sort     = instance.getSorters().map(s => ({ column: s.field, dir: s.dir }));
      const extra    = this._getExtraParams();

      const params = new URLSearchParams({
        page:   1,
        size:   1_000_000,
        sort:   JSON.stringify(sort),
        filter: JSON.stringify(filters),
        export: true,
      });
      Object.entries(extra).forEach(([key, val]) => {
        if (Array.isArray(val)) val.forEach(v => params.append(key, v));
        else params.append(key, val);
      });

      const resp = await fetch(`${instance.getAjaxUrl()}?${params}`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      this._export(fmt, data.data);
    } catch(e) {
      console.error('Export error:', e);
      alert(`Ошибка при экспорте: ${e.message}`);
    }
  }

  _export(fmt, data) {
    const cols = this._table.getVisibleColumns();
    switch (fmt) {
      case 'csv':  this._exportCSV(data, cols);   break;
      case 'json': this._exportJSON(data, cols);   break;
      case 'xlsx': this._exportXLSX(data, cols);  break;
      case 'pdf':  this._exportPDF(data, cols);   break;
    }
  }

  _exportCSV(data, cols) {
    let csv = cols.map(c => `"${c.getDefinition().title}"`).join(',') + '\n';
    data.forEach(row => {
      csv += cols.map(c => {
        let v = row[c.getField()] ?? '';
        if (typeof v === 'string') v = v.replace(/"/g, '""');
        return `"${v}"`;
      }).join(',') + '\n';
    });
    this._download(
      new Blob([csv], { type: 'text/csv;charset=utf-8;' }),
      `${this._tabName}_data.csv`
    );
  }

  _exportJSON(data, cols) {
    const out = data.map(row =>
      Object.fromEntries(cols.map(c => [c.getField(), row[c.getField()]]))
    );
    this._download(
      new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' }),
      `${this._tabName}_data.json`
    );
  }

  _exportXLSX(data, cols) {
    const ws = XLSX.utils.json_to_sheet(data.map(row =>
      Object.fromEntries(cols.map(c => [c.getDefinition().title, row[c.getField()]]))
    ));
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, this._tabName);
    XLSX.writeFile(wb, `${this._tabName}_data.xlsx`);
  }

  _exportPDF(data, cols) {
    const doc     = new window.jspdf.jsPDF();
    const headers = cols.map(c => c.getDefinition().title);
    const rows    = data.map(row => cols.map(c => {
      let v = String(row[c.getField()] || '');
      return v.length > 100 ? v.substring(0, 100) + '...' : v;
    }));
    doc.autoTable({
      head: [headers], body: rows, theme: 'grid',
      styles:     { fontSize: 7, cellPadding: 1, overflow: 'linebreak' },
      headStyles: { fillColor: [66, 139, 202], fontSize: 8, cellPadding: 2 },
      margin:     { top: 10, right: 5, bottom: 5, left: 5 },
      pageBreak: 'auto', tableWidth: 'wrap', showHead: 'everyPage', horizontalPageBreak: true,
    });
    doc.save(`${this._tabName}_data.pdf`);
  }

  _download(blob, filename) {
    const a    = document.createElement('a');
    a.href     = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
  }
}