/**
 * Кастомные форматтеры ячеек для Tabulator.
 * Каждый форматтер — чистая функция, не зависит от глобального состояния страницы.
 */

export function screenshotsFormatter(cell) {
  const row = cell.getRow().getData();
  return `<button class="btn btn-sm btn-outline-primary"
    onclick="window.__screenshotViewer?.view('${row.screenshot_path}','${row.domain}','${row.ip}')"
    title="${i18next.t('View screenshot')}"><i class="bi bi-image"></i></button>`;
}

export function modalLinkFormatter(cell, formatterParams, onRendered) {
  const value = cell.getValue();
  if (!value) return '';

  let links = Array.isArray(value)
    ? value
    : typeof value === 'string' && value.includes(',')
      ? value.split(',').map(l => l.trim()).filter(Boolean)
      : [value];

  if (!links.length) return '';

  if (links.length === 1) {
    const url     = links[0];
    const display = url.length > 20 ? url.substring(0, 20) + '...' : url;
    return `<a href="${url}" target="_blank" class="text-primary text-decoration-none" title="${url}">${display}</a>`;
  }

  const modalId   = `modal_${Math.random().toString(36).substr(2, 9)}`;
  const linksList = links.map(link =>
    `<li class="list-group-item"><a href="${link}" target="_blank" class="text-primary text-decoration-none">${link}</a></li>`
  ).join('');

  onRendered(() => {
    if (!document.getElementById(modalId)) {
      document.body.insertAdjacentHTML('beforeend', `
        <div class="modal fade" id="${modalId}" tabindex="-1">
          <div class="modal-dialog modal-lg">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">Vulnerability Links</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
              </div>
              <div class="modal-body">
                <ul class="list-group list-group-flush">${linksList}</ul>
              </div>
            </div>
          </div>
        </div>`);
    }
  });

  return `<button class="btn btn-sm btn-outline-primary"
    data-bs-toggle="modal" data-bs-target="#${modalId}">
    View ${links.length} links</button>`;
}

export function vulnsBtnFormatter(cell) {
  const row    = cell.getRow().getData();
  const portId = row.port_id || '';
  const count  = parseInt(row.vulns_count, 10) || 0;
  const label  = typeof i18next !== 'undefined' ? i18next.t('Vulerabilities') : 'Vulnerabilities';
  return `<button class="btn btn-sm btn-outline-danger vulns-btn" ${count === 0 ? 'disabled' : ''}
    onclick="${count > 0 ? `window.__vulnsModal?.show('${portId}')` : ''}">
    ${label} (${count})</button>`;
}

export function viewLogButtonFormatter(cell) {
  const value = cell.getValue();
  if (!value) return '';
  const label  = typeof i18next !== 'undefined' ? i18next.t('View Log') : 'View Log';
  const btn    = document.createElement('button');
  btn.className = 'btn btn-sm btn-outline-secondary';
  btn.innerHTML = `<i class="bi bi-file-earmark-text"></i> ${label}`;
  btn.addEventListener('click', () => window.__logViewer?.show(value));
  return btn;
}

export function commentsFormatter(cell) {
  const row     = cell.getRow().getData();
  const tabName = cell.getTable().element.id.replace('-table', '');
  const label   = typeof i18next !== 'undefined' ? i18next.t('Comments') : 'Comments';
  return `<button class="btn btn-sm btn-outline-primary"
    onclick="window.__commentsManager?.open('${row.ip_id}','${tabName}')">
    ${label} (${row.comments_count || 0})</button>`;
}

export function nameserversFormatter(cell) {
  const v = cell.getValue();
  return v ? v.replace(/,\s*/g, ',<br>') : '';
}

export function contactsFormatter(cell) {
  const v = cell.getValue();
  return v ? v.replace(/;\s*/g, ';<br>') : '';
}

/**
 * Возвращает нужный форматтер по имени поля.
 * Используется в TabulatorTable при построении колонок.
 */
export function getFormatterForField(field) {
  const map = {
    screenshot_path: screenshotsFormatter,
    data:            viewLogButtonFormatter,
    link:            modalLinkFormatter,
    comments:        commentsFormatter,
    vulns_btn:       vulnsBtnFormatter,
    nameservers:     nameserversFormatter,
    contacts:        contactsFormatter,
  };
  return map[field] || null;
}