/**
 * Модалка просмотра скриншотов с навигацией.
 *
 * Использование:
 *   import ScreenshotViewer from './screenshotViewer.js';
 *   const viewer = new ScreenshotViewer(() => tableInstance.getData());
 *   viewer.view('path/to/img.png', 'example.com', '1.2.3.4');
 *
 *   // Сделать доступным из форматтера:
 *   window.__screenshotViewer = viewer;
 */

export default class ScreenshotViewer {
  /**
   * @param {Function} getTableData — () => Array, возвращает данные таблицы web_screenshot
   */
  constructor(getTableData) {
    this._getTableData = getTableData;
    this._screenshots  = [];
    this._index        = 0;
    this._modal        = null;
    this._bsModal      = null;
    this._keyHandler   = null;
  }

  view(screenshotPath, domain, ip) {
    this._screenshots = this._getTableData()
      .filter(r => r.screenshot_path)
      .map(r => ({ screenshot_path: r.screenshot_path, domain: r.domain, ip: r.ip }));

    this._index = Math.max(0, this._screenshots.findIndex(s => s.screenshot_path === screenshotPath));
    this._show();
  }

  // ─── Private ───────────────────────────────────────────────────────────────

  _show() {
    if (!this._screenshots.length) return;
    const shot = this._screenshots[this._index];

    if (this._modal && document.body.contains(this._modal)) {
      this._updateContent(shot);
      return;
    }

    this._modal = document.createElement('div');
    this._modal.className = 'modal fade screenshot-modal';
    this._modal.id        = 'screenshot-carousel-modal';
    this._modal.setAttribute('tabindex', '-1');
    this._modal.innerHTML = this._buildHTML(shot);

    document.body.appendChild(this._modal);
    this._bsModal = new bootstrap.Modal(this._modal);
    this._bsModal.show();

    this._keyHandler = (e) => {
      if      (e.key === 'ArrowLeft')  { e.preventDefault(); this._navigate(-1); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); this._navigate(1);  }
      else if (e.key === 'Escape')     { this._bsModal.hide(); }
    };
    document.addEventListener('keydown', this._keyHandler);

    this._modal.addEventListener('hidden.bs.modal', () => this._destroy());
  }

  _navigate(dir) {
    if (this._screenshots.length <= 1) return;
    this._index = (this._index + dir + this._screenshots.length) % this._screenshots.length;
    this._show();
  }

  _updateContent(shot) {
    const domainEl  = document.getElementById('modal-domain-ip');
    const counterEl = document.getElementById('modal-counter');
    const img       = document.getElementById('screenshot-image');
    const spinner   = document.getElementById('loading-spinner');
    const dl        = document.getElementById('download-link');

    if (domainEl)  domainEl.textContent  = `${shot.domain} - ${shot.ip}`;
    if (counterEl) counterEl.textContent = `(${this._index + 1} / ${this._screenshots.length})`;
    if (spinner)   spinner.classList.remove('d-none');
    if (img) {
      img.style.opacity = '0';
      setTimeout(() => {
        img.classList.add('d-none');
        img.src = `/api/v1/dns_a_screenshot/screenshot/${shot.screenshot_path}`;
      }, 150);
    }
    if (dl) {
      dl.href     = `/api/v1/dns_a_screenshot/screenshot/${shot.screenshot_path}`;
      dl.download = `screenshot_${shot.domain}_${shot.ip}.png`;
    }
  }

  _buildHTML(shot) {
    const multi = this._screenshots.length > 1;
    return `
      <div class="modal-dialog modal-dialog-centered modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="bi bi-image me-2"></i>
              <span id="modal-domain-ip">${shot.domain} - ${shot.ip}</span>
              <small class="text-muted ms-2" id="modal-counter">(${this._index + 1} / ${this._screenshots.length})</small>
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body position-relative text-center p-0">
            ${multi ? `
              <button class="btn btn-primary position-absolute start-0 translate-middle-y ms-3"
                style="z-index:1000;top:10rem" onclick="window.__screenshotViewer?._navigate(-1)">
                <i class="bi bi-chevron-left"></i></button>
              <button class="btn btn-primary position-absolute end-0 translate-middle-y me-3"
                style="z-index:1000;top:10rem" onclick="window.__screenshotViewer?._navigate(1)">
                <i class="bi bi-chevron-right"></i></button>` : ''}
            <div class="d-flex justify-content-center align-items-center" style="min-height:400px" id="image-container">
              <div class="spinner-border text-primary" id="loading-spinner">
                <span class="visually-hidden">${i18next.t('Loading...')}</span>
              </div>
              <img src="/api/v1/dns_a_screenshot/screenshot/${shot.screenshot_path}"
                class="img-fluid d-none" id="screenshot-image"
                onclick="window.__screenshotViewer?._openImage(this.src)"
                onload="window.__screenshotViewer?._onLoad()"
                onerror="window.__screenshotViewer?._onError()"
                style="cursor:pointer;transition:opacity 0.15s;">
            </div>
          </div>
          <div class="modal-footer d-flex justify-content-between">
            <div>${multi ? `<small class="text-muted"><i class="bi bi-keyboard me-1"></i>${i18next.t('Use ← → to navigate')}</small>` : ''}</div>
            <div>
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                <i class="bi bi-x-lg"></i>${i18next.t('Close')}</button>
              <a href="/api/v1/dns_a_screenshot/screenshot/${shot.screenshot_path}"
                class="btn btn-primary ms-2" id="download-link"
                download="screenshot_${shot.domain}_${shot.ip}.png">
                <i class="bi bi-download"></i>${i18next.t('Download')}</a>
            </div>
          </div>
        </div>
      </div>`;
  }

  _onLoad() {
    const spinner = document.getElementById('loading-spinner');
    const img     = document.getElementById('screenshot-image');
    spinner?.classList.add('d-none');
    if (img) { img.classList.remove('d-none'); setTimeout(() => { img.style.opacity = '1'; }, 50); }
  }

  _onError() {
    const container = document.getElementById('image-container');
    if (container) container.innerHTML = `
      <div class="text-center py-5">
        <i class="bi bi-exclamation-triangle text-warning" style="font-size:3rem;"></i>
        <h5 class="mt-3">${i18next.t('Error loading image')}</h5>
        <p class="text-muted">${i18next.t('Failed to upload screenshot')}</p>
      </div>`;
  }
  _openImage(src) {
    const w = window.open('', '_blank');
    w.document.body.style.cssText = 'margin:0;background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh';
    const img = w.document.createElement('img');
    img.src = src;
    img.style.cssText = 'max-width:100%;height:auto';
    w.document.body.appendChild(img);
  }

  _destroy() {
    if (this._keyHandler) document.removeEventListener('keydown', this._keyHandler);
    this._keyHandler = null;
    this._modal?.remove();
    this._modal   = null;
    this._bsModal = null;
  }
}