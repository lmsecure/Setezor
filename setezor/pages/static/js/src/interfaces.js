
/* Класс интерфейса */
class Interface {

    constructor(id, name, ip_id, ip_addr, mac_addr) {
        this.id = id
        this.name = name
        this.ip_id = ip_id
        this.ip = ip_addr
        this.mac = mac_addr
    }
}

/* Хранилище интерфейсов, содержит список интерфейсов и id дефолтного */
class InterfaceData {
    constructor(interfaces, default_interface) {
        this.interfaces = interfaces
        this.default_interface = default_interface
    }
}

/* Функция запроса к апи, возвращает InterfaceData*/
async function getInterfaceData(id) {
    if (id == undefined){
        if (window.location.pathname != "/projects"){
            create_toast("Warning", "Create agent and interfaces on settings page", "warning")
        }
        return new InterfaceData([], undefined)
    }
    const resp = await fetch(`/api/v1/agents_in_project/${id}/interfaces`);
    if (resp.ok) {
        const data = await resp.json();
        const ifaces = data.map(
            (element) => new Interface(element.id, element.name, element.ip_id, element.ip, element.mac)
        );
        if (ifaces.length == 0){
            create_toast("Warning", "Create interfaces on settings page", "warning")
            return new InterfaceData([], undefined);
        }
        return new InterfaceData(ifaces, ifaces[0]);
    }
}

function createInterfaceElement(id, name, ip) {
    return `
        <li>
            <a 
                class="dropdown-item" 
                data-interface-id="${id}" 
                data-interface-name="${name}" 
                onclick="setDefaultInterface('${id}')">
                ${name} - ${ip}
            </a>
        </li>`;
}

function fillInterfaceBar(barSelector) {
    const elem = document.querySelector(`[data-interface-bar="${barSelector}"]`);
    if (!elem) return;

    const button = elem.querySelector("button");
    const list = elem.querySelector("ul");

    const html = interfaceData.interfaces.map((iface) =>
        createInterfaceElement(iface.id, iface.name, iface.ip)
    ).join("\n");
    if (interfaceData.default_interface != undefined){
        const defaultInterface = interfaceData.interfaces.find(
            (iface) => iface.id === interfaceData.default_interface.id
        );
        button.innerHTML = `${defaultInterface.name} - ${defaultInterface.ip}`;
    }
    list.innerHTML = html;
}

function createInterfaceBar(barSelector) {
    const elem = document.querySelector(`[data-interface-bar="${barSelector}"]`);
    if (!elem) return;

    const html = `
        <div class="dropdown">
            <button 
                class="btn btn-secondary dropdown-toggle" 
                type="button" 
                data-bs-toggle="dropdown" 
                aria-expanded="false">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </button>
            <ul class="dropdown-menu"></ul>
        </div>`;
    elem.innerHTML = html;
    return elem;
}

async function setDefaultInterface(id) {
    const defaultInterface = interfaceData.interfaces.find((iface) => iface.id === id);
    interfaceData.default_interface = defaultInterface;

    // Обновляем все элементы с интерфейсами
    document.querySelectorAll("[data-interface-bar]").forEach((bar) => {
        fillInterfaceBar(bar.getAttribute("data-interface-bar"));
    });
}

function getIface() {
    if (interfaceData.default_interface == undefined){
        create_toast("Warning", "Create interfaces on settings page", "warning")
    }
    iface = interfaceData.interfaces.find((elem) => elem.id == interfaceData.default_interface.id)
    return iface
}
