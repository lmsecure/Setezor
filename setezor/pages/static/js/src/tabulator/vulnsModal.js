/**
 * Модалка уязвимостей порта.
 *
 * Использование:
 *   import VulnsModal from './vulnsModal.js';
 *   const vulnsModal = new VulnsModal();
 *   vulnsModal.show('port-uuid-here');
 *
 *   window.__vulnsModal = vulnsModal; // доступ из форматтера
 */

export default class VulnsModal {
  show(portId) {
    const modalEl = document.getElementById('vulnsModal');
    const modal   = bootstrap.Modal.getOrCreateInstance(modalEl);
    const content = document.getElementById('vulnsModalContent');

    content.innerHTML = `
      <div class="d-flex justify-content-center">
        <div class="spinner-border" role="status"></div>
      </div>`;
    modal.show();

    fetch(`/api/v1/l4/${encodeURIComponent(portId)}/vulnerabilities`)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json(); })
      .then(data => this._render(content, data))
      .catch(err => {
        content.innerHTML = `<div class="alert alert-danger">Failed to load: ${err.message}</div>`;
      });
  }

  // ─── Private ───────────────────────────────────────────────────────────────

  _render(content, data) {
    const vulns = Array.isArray(data) ? data : (data?.vulnerabilities || data?.results || []);

    if (!vulns.length) {
      content.innerHTML = `<div class="alert alert-info">No vulnerabilities found</div>`;
      return;
    }

    const counts = { critical: 0, high: 0, medium: 0, low: 0, informational: 0 };
    vulns.forEach(v => {
      const score = parseFloat(v.cvss3_score || v.cvss2_score || v.cvss_score || 0) || 0;
      if      (score >= 9) counts.critical++;
      else if (score >= 7) counts.high++;
      else if (score >= 4) counts.medium++;
      else if (score > 0)  counts.low++;
      else                 counts.informational++;
    });

    const badge = (label, value, color) =>
      `<div class="text-center">
        <span class="fs-3" style="color:${color}">${value}</span>
        <div class="text-muted mt-1">${label}</div>
      </div>`;

    content.innerHTML = `
      <div class="d-flex justify-content-around mb-3">
        ${badge('Critical',      counts.critical,      '#b12825')}
        ${badge('High',          counts.high,          '#b93c16')}
        ${badge('Medium',        counts.medium,        '#9f5620')}
        ${badge('Low',           counts.low,           '#966406')}
        ${badge('Informational', counts.informational, '#0d6efd')}
      </div>`;
  }
}