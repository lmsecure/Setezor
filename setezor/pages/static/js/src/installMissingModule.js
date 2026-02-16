function ensureSystemToastContainer() {
    let container = document.getElementById('system-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'system-toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1100'; 
        document.body.appendChild(container);
    }
    return container;
}

const activeModuleToasts = new Set();

async function handleMissingModule(agentId, moduleName) {
    const toastKey = `${agentId}-${moduleName}`;

    if (activeModuleToasts.has(toastKey)) {
        return;
    }

    activeModuleToasts.add(toastKey);

    const btnId = `install-module-btn-${Date.now()}`;

    const toastEl = document.createElement('div');
    toastEl.className = 'toast align-items-center text-bg-warning border-0';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    const message = i18next.t('Module not installed', { moduleName, agentId });
    const installBtnText = i18next.t('Install');
    toastEl.innerHTML = `
        <div class="toast-body position-relative">
            ${message}<br>
            <button type="button" class="btn btn-sm btn-success mt-2" id="${btnId}">
                ${installBtnText}
            </button>
            <button type="button" 
                    class="btn-close position-absolute top-0 end-0 mt-1 me-1" 
                    data-bs-dismiss="toast" 
                    aria-label="Close"
                    style="opacity: 0.7; z-index: 1;">
            </button>
        </div>
    `;

    const container = ensureSystemToastContainer();
    container.appendChild(toastEl);

    const toastInstance = new bootstrap.Toast(toastEl, { autohide: false });
    toastInstance.show();

    const installBtn = toastEl.querySelector(`#${btnId}`);

    const cleanup = () => {
        activeModuleToasts.delete(toastKey);
        toastEl.removeEventListener('hidden.bs.toast', cleanup);
    };

    if (installBtn) {
        installBtn.onclick = async () => {
            try {
                const resp = await fetch('/api/v1/task/push_module', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        agent_id: agentId,
                        module_names: [moduleName]
                    })
                });

                if (!resp.ok) throw new Error(i18next.t('HTTP error', { status: resp.status }));

                create_toast(
                    i18next.t('Module install'),
                    i18next.t('Installation started', { moduleName }),
                    'success'
                );
                toastInstance.hide();

            } catch (err) {
                console.error('Module installation error:', err);
                create_toast(
                    i18next.t('Module install'),
                    i18next.t('Installation failed generic', { moduleName }),
                    'error'
                );
                toastInstance.hide();
            }
        };
    }

    toastEl.addEventListener('hidden.bs.toast', cleanup);
}