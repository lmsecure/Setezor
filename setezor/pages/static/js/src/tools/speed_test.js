
async function speed_test_modal_window(prefillParams = null) {
    const MODAL_ID = 'SpeedTestModal';

    // Если модалка уже открыта — не создаём повторно
    if (window.modalManager.hasModal(MODAL_ID)) {
        window.modalManager.showModal(MODAL_ID);
        return;
    }

    const [agent_list_1, agent_list_2] = await Promise.all([
        axios.get('/api/v1/agents_in_project/settings').then(r => r.data),
        axios.get('/api/v1/agents_in_project/settings').then(r => r.data),
    ]);

    const agentOptions = (list) =>
        list.map((agent, index) =>
            index === 0 ? '' : `<option value="${agent.id}">${agent.name}</option>`
        ).join('');

    const bodyContent = `
        <div class="d-flex justify-content-end mb-2" id="agent_interface_bar_speed_test">
            <div id="scans_bar_speed_test" class="ms-3"></div>
        </div>
        <form id="id_formSpeedTest" name="SpeedTestModalName" onsubmit="SpeedTestTask(event)">
            <div id="modal_speed_test_body" class="container">

                <div class="row mb-3">
                    <div class="col-6"><label for="id_select_agent_from">${i18next.t('Agent from')}</label></div>
                    <div class="col-6">
                        <select class="form-select w-100" name="agent_id_from" id="id_select_agent_from"
                            onchange="updateSourceIPs(this.value)">
                            ${agentOptions(agent_list_1)}
                        </select>
                    </div>
                </div>

                <div class="row mb-3">
                    <div class="col-6"><label for="id_select_interface_from">${i18next.t('Source interface')}</label></div>
                    <div class="col-6">
                        <select class="form-select w-100" name="interface_from" id="id_select_interface_from"></select>
                    </div>
                </div>

                <div class="row mb-3">
                    <div class="col-6"><label for="id_select_agent_to">${i18next.t('Agent to')}</label></div>
                    <div class="col-6">
                        <select class="form-select w-100" name="agent_id_to" id="id_select_agent_to"
                            onchange="updateTargetIPs(this.value)">
                            ${agentOptions(agent_list_2)}
                        </select>
                    </div>
                </div>

                <div class="row mb-3">
                    <div class="col-6"><label for="id_select_interface_to">${i18next.t('Target interface')}</label></div>
                    <div class="col-6">
                        <select class="form-select w-100" name="interface_to" id="id_select_interface_to"></select>
                    </div>
                </div>

                <div class="row mb-3">
                    <div class="mb-3 d-flex justify-content-between align-items-center">
                        <label for="id_source_port" class="form-label">${i18next.t('Target Port')}</label>
                        <input type="number" class="form-control w-100" id="id_source_port" name="target_port"
                            min="1" max="65535" style="appearance: textfield;" required>
                    </div>
                </div>

                <div class="row mb-3">
                    <div class="mb-3 d-flex justify-content-between align-items-center">
                        <label>${i18next.t('Protocol')}:</label>
                        <div class="d-flex flex-row">
                            <div class="form-check" style="margin-right: 1rem;">
                                <input class="form-check-input" type="radio" name="protocol" id="id_protocol_tcp" value="0" checked>
                                <label class="form-check-label" for="id_protocol_tcp">TCP</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="protocol" id="id_protocol_udp" value="1">
                                <label class="form-check-label" for="id_protocol_udp">UDP</label>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row mb-3">
                    <div class="col-4">
                        <label>${i18next.t('Duration')}:
                            <span id="id_slider_duration_value">5</span>
                        </label>
                    </div>
                    <div class="col-8 d-flex align-items-center gap-2">
                        <span>2</span>
                        <input type="range" class="form-range w-100" id="id_slider_duration" name="duration"
                            min="2" max="100" step="1" value="5"
                            oninput="document.getElementById('id_slider_duration_value').textContent = this.value">
                        <span>100</span>
                    </div>
                </div>

                <div class="row mb-3">
                    <div class="col-4">
                        <label>${i18next.t('Packet size')}:
                            <span id="id_slider_packet_size_value">1200</span>
                        </label>
                    </div>
                    <div class="col-8 d-flex align-items-center gap-2">
                        <span>100</span>
                        <input type="range" class="form-range w-100" id="id_slider_rate" name="packet_size"
                            min="100" max="1400" step="50" value="1200"
                            oninput="document.getElementById('id_slider_packet_size_value').textContent = this.value">
                        <span>1400</span>
                    </div>
                </div>

            </div>
            <div class="d-flex justify-content-end mb-2">
                <button type="submit" class="btn btn-primary" style="margin-right: 0.8rem;"
                    id="createSpeedTestButton" data-i18n="Start scan">
                    ${i18next.t('Start scan')}
                </button>
            </div>
        </form>
    `;

    const modalData = window.modalManager.createModal({
        id: MODAL_ID,
        title: i18next.t('Speed test task'),
        helpUrl: 'https://help.setezor.net/%D0%98%D0%BD%D1%81%D1%82%D1%80%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B.html#speed-test',
        staticBackdrop: true,
        keyboard: false,
        bodyContent,
        onClose: () => window.modalManager.destroyModal(MODAL_ID),
    });

    // Инициализируем дефолтные значения select-ов
    await updateSourceIPs(agent_list_1[1].id);
    await updateTargetIPs(agent_list_2[1].id);

    // Prefill, если передан
    if (prefillParams) {
        await _speedTestPrefill(prefillParams);
    }

    window.modalManager.showModal(MODAL_ID);
}

async function _speedTestPrefill(p) {
    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el && val !== undefined) el.value = String(val);
    };

    if (p.agent_id_from) {
        const sel = document.getElementById('id_select_agent_from');
        if (sel) { sel.value = p.agent_id_from; sel.dispatchEvent(new Event('change')); }
        await new Promise(r => setTimeout(r, 100));
    }

    if (p.ip_id_from) {
        Array.from(document.getElementById('id_select_interface_from')?.options ?? []).some(opt => {
            try {
                if (JSON.parse(opt.value).ip_id_from === p.ip_id_from) {
                    document.getElementById('id_select_interface_from').value = opt.value;
                    return true;
                }
            } catch {}
            return false;
        });
    }

    if (p.agent_id) {
        const sel = document.getElementById('id_select_agent_to');
        if (sel) { sel.value = p.agent_id; sel.dispatchEvent(new Event('change')); }
        await new Promise(r => setTimeout(r, 100));
    }

    if (p.ip_id_to) {
        Array.from(document.getElementById('id_select_interface_to')?.options ?? []).some(opt => {
            try {
                if (JSON.parse(opt.value).ip_id_to === p.ip_id_to) {
                    document.getElementById('id_select_interface_to').value = opt.value;
                    return true;
                }
            } catch {}
            return false;
        });
    }

    setVal('id_source_port', p.target_port);
    setVal('id_slider_duration', p.duration ?? 5);
    setVal('id_slider_rate', p.packet_size ?? 1200);

    const durationLabel = document.getElementById('id_slider_duration_value');
    if (durationLabel) durationLabel.textContent = p.duration ?? 5;

    const packetLabel = document.getElementById('id_slider_packet_size_value');
    if (packetLabel) packetLabel.textContent = p.packet_size ?? 1200;

    if (p.protocol !== undefined) {
        const radio = document.querySelector(`input[name="protocol"][value="${Number(p.protocol)}"]`);
        if (radio) radio.checked = true;
    }
}

async function updateSourceIPs(agentId) {
    const { data: interfaces } = await axios.get(`/api/v1/agents_in_project/${agentId}/interfaces`);
    const sel = document.getElementById('id_select_interface_from');
    if (sel) sel.innerHTML = interfaces.map(
        iface => `<option value='${JSON.stringify({ ip_id_from: iface.ip_id })}'>${iface.name} - ${iface.ip}</option>`
    ).join('');
}

async function updateTargetIPs(agentId) {
    const { data: interfaces } = await axios.get(`/api/v1/agents_in_project/${agentId}/interfaces`);
    const sel = document.getElementById('id_select_interface_to');
    if (sel) sel.innerHTML = interfaces.map(
        iface => `<option value='${JSON.stringify({ ip_id_to: iface.ip_id, target_ip: iface.ip })}'>${iface.name} - ${iface.ip}</option>`
    ).join('');
}

async function SpeedTestTask(event) {
    event.preventDefault();
    const params = Object.fromEntries(new FormData(event.target));

    const data = {
        agent_id_from: params['agent_id_from'],
        agent_id:      params['agent_id_to'],
        target_port:   Number(params['target_port']),
        protocol:      Number(params['protocol']),
        duration:      Number(params['duration']),
        packet_size:   Number(params['packet_size']),
    };

    try {
        Object.assign(data, JSON.parse(params['interface_from']));
        Object.assign(data, JSON.parse(params['interface_to']));
    } catch (e) {
        console.error('Failed to parse interface data:', e);
        return;
    }

    const result = await window.executeToolTasks({
        tasks: [{ endpoint: '/api/v1/task/speed_test_task', payload: data }],
        stopOnFirstFailure: true,
    });

    if (result.success) {
        window.modalManager.destroyModal('SpeedTestModal');
    } else if (result.reason !== 'module_install_requested') {
        console.error('Speed test task failed:', result.error);
    }
}
