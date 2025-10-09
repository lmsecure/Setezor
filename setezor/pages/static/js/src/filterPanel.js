async function createFilterPanel({ tableId, tableVar, fields, containerId }) {
    const container = document.getElementById(containerId);

    if (!container) {
        console.error(`Container "${containerId}" not found`);
        return;
    }

    container.innerHTML = `
        <div class="d-flex flex-row justify-content-start py-2 " id="filter-panel-${tableId}">
            <div class="btn-group me-1" role="group">
                <button class="btn btn-primary" id="${tableId}-reload-data">
                    <i class="bi bi-arrow-clockwise" style="font-family: 'Times New Roman', Times, serif"></i>
                </button>
            </div>
            <div class="me-1">
                <select class="form-select" id="filter-field-${tableId}">
                    ${fields.map(({ field, title }) => `<option value="${field}">${i18next.t(`${title}`)}</option>`).join('')}
                </select>
            </div>
            <div class="me-1">
                <select class="form-select" id="filter-type-${tableId}">
                    <option value="=">=</option>
                    <option value="<">&lt;</option>
                    <option value="<=">&lt;=</option>
                    <option value=">">&gt;</option>
                    <option value=">=">&gt;=</option>
                    <option value="!=">!=</option>
                    <option value="like">like</option>
                </select>
            </div>
            <input id="filter-value-${tableId}" class="form-control me-1" type="text" style="width: 15rem;" />
            <button class="btn btn-primary me-1" style="width: 5rem" id="filter-search-${tableId}">${i18next.t('Search')}</button>
            <button class="btn btn-danger me-1" style="width: 7rem" id="filter-clear-${tableId}">${i18next.t('Clear')}</button>
        </div>
    `;

    document.getElementById(`${tableId}-reload-data`).onclick = () => {
        tableVar?.dataLoader?.reloadData?.();
    };

    document.getElementById(`filter-search-${tableId}`).onclick = () => {
        const field = document.getElementById(`filter-field-${tableId}`).value;
        const type = document.getElementById(`filter-type-${tableId}`).value;
        const value = document.getElementById(`filter-value-${tableId}`).value;
        if (field && value) {
            tableVar.setFilter(field, type, value);
        }
    };

    document.getElementById(`filter-clear-${tableId}`).onclick = () => {
        document.getElementById(`filter-value-${tableId}`).value = '';
        tableVar.clearFilter();
    };

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
}
