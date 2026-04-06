class ModalManager {
  constructor() {
    this.modals = new Map(); // Храним ссылки на созданные модалки
  }

  /**
   * Создание модального окна
   * @param {Object} config - Конфигурация модального окна
   * @param {string} config.id - ID модального окна
   * @param {string} config.title - Заголовок
   * @param {string} config.size - Размер (sm, lg, xl, по умолчанию пусто)
   * @param {string} config.helpUrl - URL для справки (опционально)
   * @param {boolean} config.staticBackdrop - Запрет закрытия по клику вне модалки
   * @param {boolean} config.keyboard - Разрешить закрытие по Escape
   * @param {string} config.bodyContent - HTML контент тела модалки
   * @param {Array} config.buttons - Массив кнопок для footer
   * @param {Function} config.onClose - Колбэк при закрытии
   */
  createModal(config) {
    const { 
      id, 
      title, 
      size = '', 
      helpUrl = '', 
      staticBackdrop = true,
      keyboard = false,
      bodyContent = '',
      buttons = [],
      onClose = null,
      zIndex = null
    } = config;

    if (document.getElementById(id)) {
      return this.modals.get(id);
    }

    const modal = document.createElement('div');
    modal.id = id;
    modal.className = 'modal fade';
    modal.tabIndex = -1;
    modal.setAttribute('aria-hidden', 'true');
    
    if (staticBackdrop) {
      modal.setAttribute('data-bs-backdrop', 'static');
    }
    if (!keyboard) {
      modal.setAttribute('data-bs-keyboard', 'false');
    }

    const sizeClass = size ? `modal-${size}` : '';

    const footerButtons = buttons.map(btn => {
      const btnHtml = `
        <button type="button" 
          class="btn ${btn.class || 'btn-secondary'}" 
          id="${id}_${btn.id || btn.text.toLowerCase().replace(/\s+/g, '_')}Btn"
          ${btn.disabled ? 'disabled' : ''}>
          ${btn.text}
        </button>
      `;
      return btnHtml;
    }).join('');

    modal.innerHTML = `
      <div class="modal-dialog modal-dialog-centered ${sizeClass}">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${title}</h5>
            ${helpUrl ? `
              <a href="${helpUrl}" target="_blank" style="margin-left: 0.2rem">
                <i class="bi bi-question-circle fs-4"></i>
              </a>` : ''}
            <button type="button" class="btn-close" id="${id}_closeBtn"></button>
          </div>
          <div class="modal-body" id="${id}_body">
            ${bodyContent}
          </div>
          ${buttons.length ? `
            <div class="modal-footer" id="${id}_footer">
              ${footerButtons}
            </div>
          ` : ''}
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    if (zIndex !== null) {
      modal.style.zIndex = zIndex;
    }

    const modalData = {
      element: modal,
      config,
      buttons: {},
      onClose
    };

    const bsModal = new bootstrap.Modal(modal);
    modalData.instance = bsModal;

    modal.addEventListener('hidden.bs.modal', () => {
      if (modalData.onClose) {
        modalData.onClose();
      }
    });

    document.getElementById(`${id}_closeBtn`).addEventListener('click', () => {
      this.destroyModal(id);
    });

    buttons.forEach(btn => {
      const btnId = `${id}_${btn.id || btn.text.toLowerCase().replace(/\s+/g, '_')}Btn`;
      const btnElement = document.getElementById(btnId);
      if (btnElement && btn.onClick) {
        btnElement.addEventListener('click', () => btn.onClick(modalData));
      }
      modalData.buttons[btn.id || btn.text] = btnElement;
    });

    this.modals.set(id, modalData);
    return modalData;
  }

  showModal(id) {
    const modalData = this.modals.get(id);
    if (modalData) {
      modalData.instance.show();
    } else {
      console.error(`Modal with id "${id}" not found`);
    }
  }

  hideModal(id, destroy = true) {
    const modalData = this.modals.get(id);
    if (!modalData) return;

    const { element, instance } = modalData;

    if (destroy) {
      element.addEventListener('hidden.bs.modal', () => {
        this.destroyModal(id);
      }, { once: true });
    }
    
    instance.hide();
  }

  destroyModal(id) {
    const modalData = this.modals.get(id);
    if (!modalData) return;

    const { element } = modalData;

    const bsModal = bootstrap.Modal.getInstance(element);
    if (bsModal) {
      element.addEventListener('hidden.bs.modal', () => {
        element.remove();
        this.modals.delete(id);
      }, { once: true });
      bsModal.hide();
    } else {
      element.remove();
      this.modals.delete(id);
    }
  }

  updateBody(id, content) {
    const modalData = this.modals.get(id);
    if (modalData) {
      const bodyEl = document.getElementById(`${id}_body`);
      if (bodyEl) {
        bodyEl.innerHTML = content;
      }
    }
  }

  updateButton(modalId, buttonId, state) {
    const modalData = this.modals.get(modalId);
    if (modalData && modalData.buttons[buttonId]) {
      const btn = modalData.buttons[buttonId];
      if (state.disabled !== undefined) btn.disabled = state.disabled;
      if (state.text !== undefined) btn.innerHTML = state.text;
      if (state.class !== undefined) {
        btn.className = `btn ${state.class}`;
      }
    }
  }

  hasModal(id) {
    return this.modals.has(id);
  }
}

window.modalManager = new ModalManager();