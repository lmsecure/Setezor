/**
 * Управляет подсветкой строк таблицы по выбранным scope'ам.
 * Dropdown со scope'ами — один общий на всю страницу (global-scope-master).
 */

export default class ScopeManager {
  /**
   * @param {Object}   options
   * @param {string}   options.tabName
   * @param {string[]} options.keyFields        — поля для построения составного ключа
   * @param {Function} options.getTableInstance — () => Tabulator instance
   */
  constructor({ tabName, keyFields, getTableInstance }) {
    this._tabName          = tabName;
    this._keyFields        = keyFields;
    this._getTableInstance = getTableInstance;
    this._colorCache       = window.scopeColorCache || (window.scopeColorCache = {});
    window.globalScopeIdToName = window.globalScopeIdToName || {};
  }

  async applyHighlight() {
    const table            = this._getTableInstance();
    const selectedScopeIds = this._getSelectedScopeIds();

    this._clearHighlight(table);

    if (!selectedScopeIds.length) return;

    const scopeIdToIndex  = Object.fromEntries(selectedScopeIds.map((sid, i) => [sid, i]));
    selectedScopeIds.forEach(sid => {
      if (!this._colorCache[sid]) this._colorCache[sid] = this._randomPastelColor();
    });

    const keyMap = await this._fetchScopeKeys(selectedScopeIds);

  table.getRows().forEach(row => {
    const keys     = this._buildKeys(row.getData());
    const el       = row.getElement();
    const matched  = new Set();

    for (const key of keys) {
      const scopeIds = keyMap.get(key);
      if (scopeIds) scopeIds.forEach(s => matched.add(String(s)));
    }

    if (matched.size > 0) {
      const sidArr = Array.from(matched);
      const idx    = scopeIdToIndex[sidArr[0]];
      if (idx !== undefined) el.classList.add(`in-scope-row-${idx}`);
      el.title = sidArr.map(s => window.globalScopeIdToName[s]).join(', ');
    } else {
      el.title = '';
    }
  });

    this._injectScopeStyles(selectedScopeIds, scopeIdToIndex);
  }

  // ─── Private ───────────────────────────────────────────────────────────────

  _getSelectedScopeIds() {
    return Array.from(
      document.querySelectorAll('.scope-checkbox-global:checked')
    ).map(cb => String(cb.value));
  }

  _clearHighlight(table) {
    table?.getRows().forEach(row => {
      const el = row.getElement();
      el.className = el.className.split(' ').filter(c => !c.startsWith('in-scope-row-')).join(' ');
      el.title = '';
    });
    document.getElementById(`scope-style-${this._tabName}`)?.remove();
  }

  async _fetchScopeKeys(scopeIds) {
    const keyMap = new Map();
    await Promise.all(scopeIds.map(async scopeId => {
      try {
        const resp = await fetch(`/api/v1/scope/${scopeId}/targets`);
        if (!resp.ok) return;
        const data = await resp.json();
        for (const t of (data.data ?? [])) {
          for (const key of this._buildKeysFromTarget(t)) {
            if (!keyMap.has(key)) keyMap.set(key, new Set());
            keyMap.get(key).add(String(scopeId));
          }
        }
      } catch(e) {
        console.error('Scope fetch error:', scopeId, e);
      }
    }));
    return keyMap;
  }

  _buildKeysFromTarget(t) {
    return this._keyFields
      .map(group => {
        const parts = [];
        if (group.includes('ipaddr')   && t.ip)            parts.push(t.ip.split('/')[0]);
        if (group.includes('ip')       && t.ip)            parts.push(t.ip.split('/')[0]);
        if (group.includes('port')     && t.port != null)  parts.push(String(t.port));
        if (group.includes('domain')   && t.domain)        parts.push(t.domain);
        if (group.includes('protocol') && t.protocol)      parts.push(t.protocol);
        return parts.length === group.length ? parts.join('|') : null;
      })
      .filter(Boolean);
  }

  _buildKeys(rowData) {
    return this._keyFields
      .map(group => {
        const parts = [];
        if (group.includes('ipaddr')   && rowData.ipaddr)       parts.push(rowData.ipaddr);
        if (group.includes('ip')       && rowData.ip)           parts.push(rowData.ip);
        if (group.includes('port')     && rowData.port != null) parts.push(String(rowData.port));
        if (group.includes('domain')   && rowData.domain)       parts.push(rowData.domain);
        if (group.includes('protocol') && rowData.protocol)     parts.push(rowData.protocol);
        return parts.length === group.length ? parts.join('|') : null;
      })
      .filter(Boolean);
  }

  _injectScopeStyles(scopeIds, scopeIdToIndex) {
    const style   = document.createElement('style');
    style.id      = `scope-style-${this._tabName}`;
    style.textContent = scopeIds.map(sid => {
      const idx   = scopeIdToIndex[String(sid)];
      const color = this._colorCache[String(sid)];
      if (idx === undefined || !color) return '';
      return `.tabulator .tabulator-row.in-scope-row-${idx},
              .tabulator .tabulator-row.in-scope-row-${idx} .tabulator-cell {
                background-color: ${color} !important; }`;
    }).join('\n');
    document.head.appendChild(style);
  }

  _randomPastelColor() {
    const hue = Math.floor(Math.random() * 360);
    return `hsl(${hue}, ${45 + Math.floor(Math.random() * 15)}%, ${80 + Math.floor(Math.random() * 8)}%)`;
  }
}