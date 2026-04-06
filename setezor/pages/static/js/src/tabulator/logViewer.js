/**
 * Модалка просмотра лог-контента.
 *
 * Использование:
 *   import LogViewer from './logViewer.js';
 *   const logViewer = new LogViewer();
 *   logViewer.show(someJsonOrTextString);
 *
 *   window.__logViewer = logViewer; // доступ из форматтера
 */

export default class LogViewer {
  constructor() {
    this._modal    = null;
    this._instance = null;
  }

  show(logText) {
    this._ensureModal();
    this._modal.querySelector('.modal-title').textContent       = i18next.t('Log Content');
    this._modal.querySelector('.modal-footer .btn').textContent = i18next.t('Close');

    let display = logText || i18next.t('No log content');
    try { display = JSON.stringify(JSON.parse(logText), null, 2); } catch(_) {}

    this._modal.querySelector('textarea').value = display;
    this._instance.show();
  }

  // ─── Private ───────────────────────────────────────────────────────────────

  _ensureModal() {
    if (this._modal) return;

    document.body.insertAdjacentHTML('beforeend', `
      <div class="modal fade" id="logViewerModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title"></h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body p-0">
              <textarea class="form-control" readonly rows="30"
                style="font-family:monospace;font-size:0.9em;resize:none;border:none;
                       width:100%;padding:0.1rem;background:transparent;outline:none;">
              </textarea>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal"></button>
            </div>
          </div>
        </div>
      </div>`);

    this._modal    = document.getElementById('logViewerModal');
    this._instance = new bootstrap.Modal(this._modal, { backdrop: true, keyboard: true });
  }
}