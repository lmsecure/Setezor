const filterPanelConfigs = new Map();
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

    const config = { tableId, tableVar, fields, containerId, allowMultipleFilters, counter: 1 };
    filterPanelConfigs.set(tableId, config);

    const valuePlaceholder = allowMultipleFilters
        ? i18next.t('value1, value2')
        : i18next.t('value');

    const addFilterButton = allowMultipleFilters
        ? `<button class="btn btn-outline-success btn" id="add-filter-panel-${tableId}" 
              data-i18n="Add filter" style="height: 34px !important;">
              <i class="bi bi-plus-lg"></i> ${i18next.t('Add filter')}
           </button>`
        : '';

    const initialField = fields.length > 0 ? fields[0].field : '';
    container.innerHTML = `
        <div class="d-flex flex-wrap align-items-start gap-2 w-100" id="main-filter-row-${tableId}">
            <!-- Первая панель -->
            <div class="d-flex flex-wrap align-items-center gap-1" id="${tableId}-filter-panel-0">
                <select class="form-select form-select" style="width: auto; height: 34px !important;" id="filter-field-${tableId}-0">
                    ${fields.map(({ field, title }) => `<option value="${field}">${i18next.t(title)}</option>`).join('')}
                </select>
                <select class="form-select form-select" style="width: auto; height: 34px !important;" id="filter-type-${tableId}-0">
                    ${getOperatorSelectHtml(initialField)}
                </select>
                <input id="filter-value-${tableId}-0" class="form-control form-control" type="text" placeholder="${valuePlaceholder}" style="width: 15rem; height: 34px !important;"/>
            </div>

            <!-- Кнопки управления справа -->
            <div class="d-flex flex-wrap align-items-center gap-1 flex-grow-1">
                ${addFilterButton}
                <button class="btn btn-primary btn" id="apply-all-filters-${tableId}" data-i18n="Search" style="height: 34px !important;">
                    ${i18next.t('Search')}
                </button>
                <button class="btn btn-danger btn" id="clear-all-filters-${tableId}" data-i18n="Clear" style="height: 34px !important;">
                    ${i18next.t('Clear')}
                </button>
                <button class="btn btn-primary btn" id="${tableId}-reload-data" title="${i18next.t('Reload')}" style="height: 34px !important;">
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
            addExtraFilterPanel(extraWrapper, config, config.counter++);
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
}

function addExtraFilterPanel(wrapper, config, index) {
    const { tableId, fields, allowMultipleFilters } = config;
    const initialField = fields.length > 0 ? fields[0].field : '';
    
    const valuePlaceholder = allowMultipleFilters
        ? i18next.t('value1, value2')
        : i18next.t('value');

    const panelHTML = `
        <div class="d-flex flex-wrap align-items-center gap-1" id="${tableId}-filter-panel-${index}">
            <span class="and-label px-1 text-nowrap"
                style="font-size: 0.8rem; font-weight: 600; color: #6c757d; align-self: center;">
                AND
            </span>
            <select class="form-select form-select" style="width: auto;" id="filter-field-${tableId}-${index}">
                ${fields.map(({ field, title }) => `<option value="${field}">${i18next.t(title)}</option>`).join('')}
            </select>
            <select class="form-select form-select" style="width: auto;" id="filter-type-${tableId}-${index}">
                ${getOperatorSelectHtml(initialField)}
            </select>
            <input id="filter-value-${tableId}-${index}" class="form-control form-control" type="text" 
                placeholder="${valuePlaceholder}" style="width: 15rem;"/>
            <button type="button" class="btn btn btn-outline-danger" 
                data-i18n-title="Remove filter" title="${i18next.t('Remove filter')}" 
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

        const values = rawValue
            .split(',')
            .map(v => v.trim())
            .filter(v => v !== '');

        if (values.length === 0) return;
        allFilters.push({ field, type, value: values });
    });

    tableVar.setFilter(allFilters);
}

function clearAllFilters(tableId, tableVar) {
    document.querySelectorAll(`[id^="filter-value-${tableId}-"]`).forEach(input => {
        input.value = '';
    });
    tableVar.clearFilter();
}

function updateFilterPanelTranslations() {
    filterPanelConfigs.forEach(config => {
        const { tableId, fields, allowMultipleFilters } = config;
        
        document.querySelectorAll(`[data-i18n]`).forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (key) el.textContent = el.textContent.replace(i18next.t(key), i18next.t(key));
        });
        
        document.querySelectorAll(`[data-i18n-title]`).forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            if (key) el.title = i18next.t(key);
        });
        
        document.querySelectorAll(`[id^="filter-value-${tableId}-"]`).forEach((input, idx) => {
            const placeholder = allowMultipleFilters
                ? i18next.t('value1, value2')
                : i18next.t('value');
            input.placeholder = placeholder;
        });
        
        const fieldSelects = document.querySelectorAll(`[id^="filter-field-${tableId}-"]`);
        fieldSelects.forEach(select => {
            Array.from(select.options).forEach((opt, i) => {
                if (fields[i]) {
                    opt.textContent = i18next.t(fields[i].title);
                }
            });
        });
    });
}

i18next.on('languageChanged', () => {
    updateFilterPanelTranslations();
});