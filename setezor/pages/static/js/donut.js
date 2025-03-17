
function createGraphDeviceType(title, mainId, data, labels, height = null, width = null) {
    const graphHtml = `
            <div id="${mainId}" class="card w-100">
                <div class="card-header">
                    ${title}
                </div>
                <div class="card-body">
                    <div id="${mainId}_donut"></div>
                </div>
            </div>
        `;

    const container = document.getElementById('device-type-container');
    container.innerHTML = graphHtml;

    plotlyDeviceType(`${mainId}_donut`, data, labels, height);
}

function plotlyDeviceType(elementId, values, labels, height = null, textInside = '') {

    let data;

    if (values.length === 0 || labels.length === 0) {
        data = [{
            x: ['No Data'],
            y: [0],
            type: 'bar',
            textinfo: "label",
            textposition: "inside",
            marker: { colors: ['#ddd'] },
        }];
    } else {
        data = [{
            x: labels,
            y: values,
            type: 'bar',
            textinfo: "label",
            textposition: "inside",
        }];
    }

    const layout = {
        autosize: true,
        margin: { t: 0, b: 30, l: 20, r: 0 },
        showlegend: false,
    };

    if (height != null) {
        layout.height = height;
    }

    Plotly.newPlot(elementId, data, layout, { displayModeBar: false });
}

function createPortsAndProtocols(title, mainId, labels, parents, graph_values, height = null, width = null) {
    const graphHtml = `
            <div id="${mainId}" class="card">
                <div class="card-header">
                    ${title}
                </div>
                <div class="card-body">
                    <div id="${mainId}_donut"></div>
                </div>
            </div>
        `;

    const container = document.getElementById('ports-and-protocols-container');
    container.innerHTML = graphHtml;
    createSunburstChart(`${mainId}_donut`, labels, parents, graph_values, height);
}

function createProductsAndServiceName(title, mainId, labels, parents, graph_values, height = null, width = null) {
    const graphHtml = `
            <div id="${mainId}" class="card">
                <div class="card-header">
                    ${title}
                </div>
                <div class="card-body">
                    <div id="${mainId}_donut"></div>
                </div>
            </div>
        `;

    const container = document.getElementById('products-and-service-name-container');
    container.innerHTML = graphHtml;
    createSunburstChart(`${mainId}_donut`, labels, parents, graph_values, height);
}

function createSunburstChart(elementId, labels, parents, graph_values, height = null) {
    let data;
    if (labels.length === 0 || parents.length === 0 || graph_values.length === 0) {
        data = [{
            type: 'sunburst',
            labels: ['No Data'],
            parents: [''],
            values: [0],
            branchvalues: 'total',
            textinfo: "label+value",
            marker: { colors: ['#ddd'] }
        }];
    } else {
        data = [{
            type: 'sunburst',
            labels: labels,
            parents: parents,
            values: graph_values,
            branchvalues: 'total',
        }];
    }

    const layout = {
        autosize: true,
        margin: { t: 0, b: 0, l: 0, r: 0 },
        showlegend: false
    };

    if (height != null) {
        layout.height = height;
    }
    Plotly.newPlot(elementId, data, layout, { displayModeBar: false });
}