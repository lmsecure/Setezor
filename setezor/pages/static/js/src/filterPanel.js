let filterPanelCounter = 0;

const NUMERIC_FIELDS = new Set(['port']);

function getOperatorSelectHtml(field) {
    const options = [];
    options.push('<option value="=">=</option>');
    options.push('<option value="!=">!=</option>');

    if (NUMERIC_FIELDS.has(field)) {
        options.push('<option value="<"><</option>');
        options.push('<option value="<="><=</option>');
        options.push('<option value=">">></option>');
        options.push('<option value=">=">>=</option>');
    } else {
        options.push('<option value="like">like</option>');
    }

    return options.join('');
}

function updateOperatorSelect(tableId, index, field) {
    const operatorSelect = document.getElementById(`filter-type-${tableId}-${index}`);
    if (operatorSelect) {
        operatorSelect.innerHTML = getOperatorSelectHtml(field);
    }
}

function initFilterPanelContainer({ tableId, tableVar, fields, containerId, allowMultipleFilters = false }) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container "${containerId}" not found`);
        return;
    }

    const valuePlaceholder = allowMultipleFilters
        ? i18next.t('value1, value2')
        : i18next.t('value');

    const addFilterButton = allowMultipleFilters
        ? `<button class="btn btn-outline-success btn" id="add-filter-panel-${tableId}">
              <i class="bi bi-plus-lg"></i> ${i18next.t('Add filter')}
           </button>`
        : '';

    const initialField = fields.length > 0 ? fields[0].field : '';
    container.innerHTML = `
        <div class="d-flex flex-wrap align-items-start gap-2 mt-2 w-100" id="main-filter-row-${tableId}">
            <!-- Первая панель -->
            <div class="d-flex flex-wrap align-items-center gap-1" id="${tableId}-filter-panel-0">
                <select class="form-select form-select" style="width: auto;" id="filter-field-${tableId}-0">
                    ${fields.map(({ field, title }) => `<option value="${field}">${i18next.t(title)}</option>`).join('')}
                </select>
                <select class="form-select form-select" style="width: auto;" id="filter-type-${tableId}-0">
                    ${getOperatorSelectHtml(initialField)}
                </select>
                <input id="filter-value-${tableId}-0" class="form-control form-control" type="text" placeholder="${valuePlaceholder}" style="width: 15rem;"/>
            </div>

            <!-- Кнопки управления справа -->
            <div class="d-flex flex-wrap align-items-center gap-1 flex-grow-1">
                ${addFilterButton}
                <button class="btn btn-primary btn" id="apply-all-filters-${tableId}">
                    ${i18next.t('Search')}
                </button>
                <button class="btn btn-danger btn" id="clear-all-filters-${tableId}">
                    ${i18next.t('Clear')}
                </button>
                <button class="btn btn-primary btn" id="${tableId}-reload-data">
                    <i class="bi bi-arrow-clockwise"></i>
                </button>
            </div>
        </div>

        <!-- Обёртка со скроллом для дополнительных панелей -->
        <div class="mt-1 mb-2" style="max-height: 150px; overflow-y: auto;">
            <div class="d-flex flex-column gap-1" id="extra-filter-panels-${tableId}"></div>
        </div>
    `;

    const firstFieldSelect = document.getElementById(`filter-field-${tableId}-0`);
    if (firstFieldSelect) {
        firstFieldSelect.addEventListener('change', function () {
            updateOperatorSelect(tableId, 0, this.value);
        });
    }

    const extraWrapper = document.getElementById(`extra-filter-panels-${tableId}`);

    if (allowMultipleFilters) {
        document.getElementById(`add-filter-panel-${tableId}`)?.addEventListener('click', () => {
            addExtraFilterPanel(extraWrapper, tableId, fields, filterPanelCounter++);
        });
    }

    document.getElementById(`apply-all-filters-${tableId}`).addEventListener('click', () => {
        applyAllFilters(tableId, tableVar);
    });

    document.getElementById(`clear-all-filters-${tableId}`).addEventListener('click', () => {
        clearAllFilters(tableId, tableVar);
    });

    document.getElementById(`${tableId}-reload-data`).addEventListener('click', () => {
        tableVar?.dataLoader?.reloadData?.();
    });

    filterPanelCounter = 1;
}

function addExtraFilterPanel(wrapper, tableId, fields, index) {
    const initialField = fields.length > 0 ? fields[0].field : '';
    const panelHTML = `
        <div class="d-flex flex-wrap align-items-center gap-1" id="${tableId}-filter-panel-${index}">
            <select class="form-select form-select" style="width: auto;" id="filter-field-${tableId}-${index}">
                ${fields.map(({ field, title }) => `<option value="${field}">${i18next.t(title)}</option>`).join('')}
            </select>
            <select class="form-select form-select" style="width: auto;" id="filter-type-${tableId}-${index}">
                ${getOperatorSelectHtml(initialField)}
            </select>
            <input id="filter-value-${tableId}-${index}" class="form-control form-control" type="text" placeholder="${i18next.t('value1, value2')}" style="width: 15rem;"/>
            <button type="button" class="btn btn btn-outline-danger" title="${i18next.t('Remove filter')}" 
                    onclick="removeFilterPanel('${tableId}', ${index})">
                <i class="bi bi-x-lg"></i>
            </button>
        </div>
    `;
    wrapper.insertAdjacentHTML('beforeend', panelHTML);
    const newFieldSelect = document.getElementById(`filter-field-${tableId}-${index}`);
    if (newFieldSelect) {
        newFieldSelect.addEventListener('change', function () {
            updateOperatorSelect(tableId, index, this.value);
        });
    }
}

function removeFilterPanel(tableId, index) {
    const panel = document.getElementById(`${tableId}-filter-panel-${index}`);
    if (panel) {
        panel.remove();
    }
}

function applyAllFilters(tableId, tableVar) {
    const allPanels = [
        document.getElementById(`${tableId}-filter-panel-0`),
        ...Array.from(document.querySelectorAll(`[id^="${tableId}-filter-panel-"]:not([id="${tableId}-filter-panel-0"])`))
    ].filter(Boolean);

    const allFilters = [];

    allPanels.forEach(panel => {
        const idParts = panel.id.split('-');
        const index = idParts[idParts.length - 1];
        const field = document.getElementById(`filter-field-${tableId}-${index}`)?.value;
        const type = document.getElementById(`filter-type-${tableId}-${index}`)?.value;
        const rawValue = document.getElementById(`filter-value-${tableId}-${index}`)?.value;

        if (!field || !rawValue) return;

        allFilters.push({ field, type, value: rawValue });
    });

    tableVar.setFilter(allFilters);
}

function removeFilterPanel(tableId, index) {
    const panel = document.getElementById(`${tableId}-filter-panel-${index}`);
    if (panel) {
        panel.remove();
    }
}

function clearAllFilters(tableId, tableVar) {
    document.querySelectorAll(`[id^="filter-value-${tableId}-"]`).forEach(input => {
        input.value = '';
    });
    tableVar.clearFilter();
}

/*fetch('/api/v1/scan')
    .then(res => res.json())
    .then(scans => {
        const el = document.getElementById(`${tableId}_scansContainer`);
        if (!el) return;

        el.innerHTML = scans.map(scan => `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" value="${scan.id}" id="${tableId}_scan_${scan.id}">
                <label class="form-check-label" for="${tableId}_scan_${scan.id}">
                    ${scan.name} - ${scan.created_at}
                </label>
            </div>
        `).join('');
    });

document.querySelector(`form[name="showInformationForScansForm_${tableId}"]`)?.addEventListener("submit", function (e) {
    e.preventDefault();
    const selectedScans = Array.from(this.querySelectorAll('input[type="checkbox"]:checked'))
        .map(checkbox => checkbox.value);

    console.log(`[${tableId}] Selected scans:`, selectedScans);

    tableVar.setData(tableVar.getAjaxUrl(), {}, "GET");
});*/