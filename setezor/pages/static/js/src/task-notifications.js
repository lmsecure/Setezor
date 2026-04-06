(function () {
    'use strict';

    const taskNotifications = new Map();

    const TASK_STATES = [
        { key: 'CREATED',              label: 'Created' },
        { key: 'REGISTERED',           label: 'Registered' },
        { key: 'PROCESSING_ON_AGENT',  label: 'Agent' },
        { key: 'FINISHED_ON_AGENT',    label: 'Agent Done' },
        { key: 'PROCESSING_ON_SERVER', label: 'Processing' },
        { key: 'FINISHED',             label: 'Finished' },
    ];

    const SIDE_STATES = {
        FAILED:    { key: 'FAILED',    label: 'Failed',    type: 'error' },
        CANCELLED: { key: 'CANCELLED', label: 'Cancelled', type: 'warning' },
    };

    const SEARCH_STATES = [...TASK_STATES, ...Object.values(SIDE_STATES)].sort((a, b) => b.key.length - a.key.length);

    function extractTaskId(text) {
        try {
            const json = typeof text === 'string' ? JSON.parse(text) : text;
            if (json?.id) return String(json.id).toLowerCase();
        } catch (_) {}
        
        const patterns = [/Task\s+([a-f0-9]{32})/i, /task_id\s*=\s*['"]?([a-f0-9]{32})['"]?/i];
        for (const p of patterns) {
            const m = text.match(p);
            if (m?.[1]) return m[1].toLowerCase();
        }
        return null;
    }

    function extractError(text, statusKey) {
        try {
            const json = typeof text === 'string' ? JSON.parse(text) : text;
            if (json?.traceback) return json.traceback.trim() || null;
        } catch (_) {}
        
        const m = text.match(new RegExp(`${statusKey}\\s+(.+)$`, 'i'));
        return m?.[1]?.trim() || null;
    }

    function getStateInfo(text) {
        try {
            const json = typeof text === 'string' ? JSON.parse(text) : text;
            if (json?.status) {
                const upperStatus = json.status.toUpperCase();
                for (const state of SEARCH_STATES) {
                    if (upperStatus === state.key) {
                        return { ...state, isSide: !!SIDE_STATES[state.key] };
                    }
                }
            }
        } catch (_) {}
        
        const upper = text.toUpperCase();
        for (const state of SEARCH_STATES) {
            if (upper.includes(state.key)) {
                return { ...state, isSide: !!SIDE_STATES[state.key] };
            }
        }
        return null;
    }

    function formatTime(date = new Date()) {
        const p = (n) => String(n).padStart(2, '0');
        return `${date.getFullYear()}-${p(date.getMonth() + 1)}-${p(date.getDate())} ${p(date.getHours())}:${p(date.getMinutes())}:${p(date.getSeconds())}`;
    }

    function getStepClasses(stateKey, idx, states, completedMain, isFinished, hasSideStatus) {
        const data = states[stateKey];
        const isDone = data?.completed && (idx < completedMain - 1 || isFinished);
        const isActive = data?.completed && !isDone;
        
        if (hasSideStatus && !data?.completed) return { step: 'failed', connector: 'failed', label: 'failed' };
        if (isDone) return { step: 'done', connector: 'done', label: 'done' };
        if (isActive) return { step: 'active', connector: 'active', label: 'active' };
        return { step: 'pending', connector: '', label: '' };
    }

    function getSideStatusHTML(sideState, states) {
        const errorMsg = states[sideState.key]?.errorMessage;
        const icon = sideState.type === 'error'
            ? '<circle cx="12" cy="12" r="10" stroke="#ef4444" stroke-width="2"/><path d="M12 8v4M12 16h.01" stroke="#ef4444" stroke-width="2" stroke-linecap="round"/>'
            : '<circle cx="12" cy="12" r="10" stroke="#f59e0b" stroke-width="2"/><path d="M12 8v4M12 16h.01" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/>';
        
        return `
            <div class="side-status ${sideState.type}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="flex-shrink:0">${icon}</svg>
                <span class="side-status-text">${sideState.label}${errorMsg ? `: ${errorMsg}` : ''}</span>
            </div>`;
    }

    function createTaskTimelineHTML(title, taskId, states) {
        const completedMain = TASK_STATES.filter((s) => states[s.key]?.completed).length;
        const isFinished = states['FINISHED']?.completed;
        const sideState = Object.values(SIDE_STATES).find(s => states[s.key]?.completed);
        const hasSideStatus = !!sideState;

        const steps = TASK_STATES.map((state, idx) => {
            const { step, connector } = getStepClasses(state.key, idx, states, completedMain, isFinished, hasSideStatus);
            const timeHint = states[state.key]?.time ? ` • ${states[state.key].time.split(' ')[1]}` : '';
            const dot = `<div class="step ${step}" title="${state.label}${timeHint}"></div>`;
            const conn = idx < TASK_STATES.length - 1 ? `<div class="step-connector ${connector}"></div>` : '';
            return `<div class="step-item">${dot}${conn}</div>`;
        }).join('');

        const labels = TASK_STATES.map((state, idx) => {
            const { label } = getStepClasses(state.key, idx, states, completedMain, isFinished, hasSideStatus);
            return `<span class="step-label ${label}">${state.label}</span>`;
        }).join('');

        return `
            <div class="toast-header">
                <div class="t-icon">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M2 7h10M7 2l5 5-5 5" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body p-0">
                <div class="task-progress">
                    <div class="task-id-row">
                        <span class="task-id-text">Task:</span>
                        <code class="task-id-value" data-copy="${taskId}" title="Click to copy full ID">${taskId}</code>
                    </div>
                    ${hasSideStatus ? getSideStatusHTML(sideState, states) : ''}
                    <div>
                        <div class="progress-steps">${steps}</div>
                        <div class="step-labels">${labels}</div>
                    </div>
                </div>
            </div>`;
    }

    function updateTaskTimeline(toastEl, states, title) {
        if (!toastEl || !document.contains(toastEl)) return;

        const titleEl = toastEl.querySelector('.toast-header strong.me-auto');
        if (title && titleEl) titleEl.textContent = title;

        const completedMain = TASK_STATES.filter((s) => states[s.key]?.completed).length;
        const isFinished = states['FINISHED']?.completed;
        const sideState = Object.values(SIDE_STATES).find(s => states[s.key]?.completed);
        const hasSideStatus = !!sideState;

        toastEl.querySelectorAll('.step-item').forEach((item, idx) => {
            const state = TASK_STATES[idx];
            const { step, connector } = getStepClasses(state.key, idx, states, completedMain, isFinished, hasSideStatus);
            
            const dot = item.querySelector('.step');
            const conn = item.querySelector('.step-connector');
            
            if (dot) {
                dot.className = `step ${step}`;
                dot.title = `${state.label}${states[state.key]?.time ? ' • ' + states[state.key].time.split(' ')[1] : ''}`;
            }
            if (conn) conn.className = `step-connector ${connector}`;
        });

        toastEl.querySelectorAll('.step-label').forEach((el, idx) => {
            const state = TASK_STATES[idx];
            const { label } = getStepClasses(state.key, idx, states, completedMain, isFinished, hasSideStatus);
            el.className = `step-label ${label}`;
        });

        const existingSide = toastEl.querySelector('.side-status');
        if (hasSideStatus) {
            if (!existingSide) {
                const idRow = toastEl.querySelector('.task-id-row');
                if (idRow) idRow.insertAdjacentHTML('afterend', getSideStatusHTML(sideState, states));
            } else {
                existingSide.className = `side-status ${sideState.type}`;
                const textEl = existingSide.querySelector('.side-status-text');
                const errorMsg = states[sideState.key]?.errorMessage;
                if (textEl) textEl.textContent = `${sideState.label}${errorMsg ? `: ${errorMsg}` : ''}`;
            }
        } else if (existingSide) {
            existingSide.remove();
        }
    }

    function bindCopyButtons(toastEl) {
        toastEl.querySelectorAll('.task-id-value[data-copy]').forEach((el) => {
            el.addEventListener('click', () => {
                navigator.clipboard?.writeText(el.dataset.copy).catch(() => {});
                el.classList.add('copied');
                setTimeout(() => el.classList.remove('copied'), 1000);
            });
        });
    }

    function initTaskRecord(taskId) {
        const states = {};
        TASK_STATES.forEach((s) => { states[s.key] = { completed: false, time: null }; });
        Object.values(SIDE_STATES).forEach((s) => { states[s.key] = { completed: false, time: null, errorMessage: null }; });
        taskNotifications.set(taskId, { states, createdAt: Date.now(), popupEl: null, notificationEl: null, hideTimeout: null });
        return taskNotifications.get(taskId);
    }

    function manageContainer(holderId, taskId, record, isNewTask, isFinished, displayTitle) {
        const holder = document.getElementById(holderId);
        if (!holder) return;

        const tryUpdate = () => {
            const existing = holder.querySelector(`[data-task-id="${taskId}"]`);
            if (existing && document.contains(existing)) {
                existing.dataset.states = JSON.stringify(record.states);
                updateTaskTimeline(existing, record.states, displayTitle);
                return true;
            }
            return false;
        };

        if (!tryUpdate() && isNewTask) {
            const notif = document.createElement('div');
            notif.classList.add('toast', 'fade', 'toast-task');
            notif.setAttribute('data-bs-autohide', isFinished ? 'true' : 'false');
            notif.setAttribute('data-task-id', taskId);
            notif.dataset.states = JSON.stringify(record.states);
            notif.innerHTML = createTaskTimelineHTML(displayTitle, taskId, record.states);
            holder.prepend(notif);
            bindCopyButtons(notif);
            new bootstrap.Toast(notif, { autohide: isFinished }).show();
            record.notificationEl = notif;
        }
    }

    window.TaskNotifier = {
        notify(title, message, level = 'info') {
            const taskId = extractTaskId(message);
            if (!taskId) {
                if (typeof create_toast === 'function') create_toast(title, message, level);
                return;
            }

            const state = getStateInfo(message);
            if (!state) return;
            let displayTitle = title;
            try {
                const json = typeof message === 'string' ? JSON.parse(message) : message;
                if (json?.name) {
                    displayTitle = `${json.name} Status`;
                }
            } catch (_) {}

            const isNewTask = !taskNotifications.has(taskId);
            const record = isNewTask ? initTaskRecord(taskId) : taskNotifications.get(taskId);
            const timeString = formatTime();

            if (state.isSide) {
                record.states[state.key] = { completed: true, time: timeString, errorMessage: extractError(message, state.key) };
            } else {
                record.states[state.key] = { completed: true, time: timeString };
                if (state.key === 'FINISHED') {
                    TASK_STATES.forEach(s => {
                        if (!record.states[s.key]?.completed) record.states[s.key] = { completed: true, time: timeString };
                    });
                }
            }

            const isFinished = state.key === 'FINISHED' && !state.isSide;
            const isSideError = state.isSide; 
            
            const shouldAutoHide = isFinished || isSideError; 
            const hideDelay = isFinished ? 4000 : 8000; 
            
            if (record.hideTimeout) {
                clearTimeout(record.hideTimeout);
                record.hideTimeout = null;
            }

            if (record.popupEl && document.contains(record.popupEl) && !record.popupEl.classList.contains('show')) {
                const inst = bootstrap.Toast.getInstance(record.popupEl);
                if (inst) inst.show();
            }

            if (!isFinished && !state.isSide) {
                record.hideTimeout = setTimeout(() => {
                    if (record.popupEl && document.contains(record.popupEl)) {
                        const inst = bootstrap.Toast.getInstance(record.popupEl);
                        if (inst) inst.hide();
                    }
                    record.hideTimeout = null;
                }, 5000);
            }

            const toastHolder = document.getElementById('toast_holder');

            if (record.popupEl && document.contains(record.popupEl)) {
                updateTaskTimeline(record.popupEl, record.states, displayTitle);
                if (shouldAutoHide) {
                    record.popupEl.setAttribute('data-bs-autohide', 'true');
                    const inst = bootstrap.Toast.getInstance(record.popupEl);
                    if (inst) { inst.show(); setTimeout(() => inst.hide(), hideDelay); }
                }
            } else if (isNewTask && toastHolder) {
                toastHolder.classList.add('position-fixed', 'bottom-0', 'end-0', 'p-3');
                const toast = document.createElement('div');
                toast.classList.add('toast', 'fade', 'toast-task');
                toast.setAttribute('data-bs-autohide', shouldAutoHide);
                toast.innerHTML = createTaskTimelineHTML(displayTitle, taskId, record.states);
                toastHolder.append(toast);
                bindCopyButtons(toast);
                
                const inst = new bootstrap.Toast(toast, { autohide: shouldAutoHide });
                inst.show();
                record.popupEl = toast;

                toast.addEventListener('hidden.bs.toast', () => {
                    const rec = taskNotifications.get(taskId);
                    if (rec && (rec.states['FINISHED']?.completed || rec.states['FAILED']?.completed || rec.states['CANCELLED']?.completed)) {
                        setTimeout(() => {
                            if (taskNotifications.get(taskId)) taskNotifications.delete(taskId);
                        }, 1000);
                    }
                });
            }

            manageContainer('notifications_body', taskId, record, isNewTask, isFinished, displayTitle);

            if (shouldAutoHide) {
                setTimeout(() => {
                    const rec = taskNotifications.get(taskId);
                    if (rec && (rec.states['FINISHED']?.completed || rec.states['FAILED']?.completed || rec.states['CANCELLED']?.completed)) {
                        try { bootstrap.Toast.getInstance(rec.popupEl)?.hide(); } catch (_) {}
                        taskNotifications.delete(taskId);
                    }
                }, hideDelay + 1000);
            }
        },

        isTaskNotification(title, text) {
            return title === 'Task status' && /Task/.test(text) && !!extractTaskId(text);
        },

        clearAll() {
            taskNotifications.forEach((rec) => {
                try { bootstrap.Toast.getInstance(rec.popupEl)?.hide(); } catch (_) {}
                try { bootstrap.Toast.getInstance(rec.notificationEl)?.hide(); } catch (_) {}
            });
            taskNotifications.clear();
        },
    };
})();