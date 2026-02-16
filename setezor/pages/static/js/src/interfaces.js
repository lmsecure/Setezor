
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
let interfaceLength = 0
async function getInterfaceData(id) {
    if (id == undefined){
        if (window.location.pathname != "/projects"){
            create_toast("Warning", "Create agent and interfaces on settings page", "warning")
        }
        interfaceLength = 0
        return new InterfaceData([], undefined)
    }
    const resp = await fetch(`/api/v1/agents_in_project/${id}/interfaces`);
    if (resp.ok) {
        const data = await resp.json();
        interfaceLength = data.length
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
    
    list.innerHTML = html;

    if (interfaceData.default_interface != undefined){
        const defaultInterface = interfaceData.interfaces.find(
            (iface) => iface.id === interfaceData.default_interface.id
        );

        button.setAttribute("data-bs-toggle", "dropdown");
        button.onclick = null; 

        let name = defaultInterface.name
        const limitedName = name.length > 10 ? name.slice(0, 10) + "..." : name
        button.innerHTML = `${limitedName} - ${defaultInterface.ip}`;
    } else {

        button.innerHTML = `<i class="bi bi-exclamation-diamond-fill" style="font-size: 1.2rem; color: red;"></i>`;

        button.removeAttribute("data-bs-toggle");

        button.onclick = function() {
            if (typeof agentData !== 'undefined' && agentData.default_agent) {
                currentAgent=agentData.default_agent
                getAgentInterfaces(agentData.default_agent);
            } else {
                console.warn("agentData не определен или нет default_agent");
                if (typeof getAgentInterfaces === 'function') currentAgent=agentData.default_agent; getAgentInterfaces();
            }
        };
    }
}

function createInterfaceBar(barSelector) {
    const elem = document.querySelector(`[data-interface-bar="${barSelector}"]`);
    if (!elem) return;

    const html = `
        <div class="dropdown">
            <button 
                class="btn btn-secondary dropdown-toggle btn-limit" 
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

function fillInterfacesTable(){
        let el = document.getElementById("interfaces_list_container")
        let result = ``
        for (const [index, interface] of currentAgentInterfaces.entries()){
            let checkboxId = `interface-checkbox-${index}`;
			let checkboxIsActive = interface.is_already_enabled ? "checked" : "";
            let disabled = interface.is_already_enabled ? "disabled" : "";
            result += `
                <div class="form-check" style="margin-bottom:-1rem">
                    <input id="${checkboxId}" class="form-check-input" type="checkbox" mac="${interface.mac}" ip="${interface.ip}" name="${interface.name}" ${checkboxIsActive} ${disabled}>
                    <label for="${checkboxId}"><pre style="font-size:1.05rem" class="form-check-label">${interface.ip != null ? interface.ip.padEnd(18):""}${interface.name}</pre></label>
                </div>
            `
        }
        el.innerHTML = result
    }

let currentAgentInterfaces = []
let originalActiveInterfaces = [];
let originalInstalledModules = [];

async function getAgentInterfaces(id) {
    currentAgentInterfaces = []
    resp = await fetch(`/api/v1/agents/${id}/remote_interfaces`)
    if (resp.ok) {
        data = await resp.json()
        if (data.length == 0){
            $('#editAgentInterfacesWhichDoesNotExist').modal('show');
        }else{
            currentAgentInterfaces = data
            fillInterfacesTable()
            $('#editAgentInterfaces').modal('show');
        }
    }
}

async function requestAgentInterfaces(agent_id, object_id) {
    let resp = await fetch(`/api/v1/task/interfaces_task`, { method: 'POST', body: JSON.stringify({ agent_id: agent_id }), headers: {
                'Content-Type': 'application/json',
            }, })
}


let currentAgent = 0

async function saveSynthInterface(event){
    event.preventDefault()
    let data = new FormData(event.target)
    let new_interface = new Object()
    data.forEach(function(value, key){
        new_interface[key] = value;
    });
    new_interface.mac=''
    let result = [new_interface]
    let resp = await fetch(`/api/v1/agents/${currentAgent}/interfaces`,
    { method: 'PATCH',
    headers: {"Content-Type": "application/json",},
    body: JSON.stringify(result) 
    }
    )
    $('#editAgentInterfacesWhichDoesNotExist').modal('hide');
}

async function saveInterfaces(){
    let el = document.getElementById("interfaces_list_container")
    let result = []
    for (const children of el.children){
        for (const sub_child of children.children){
            if (sub_child.tagName == "INPUT"){
                if (sub_child.checked){
                    let new_interface = new Object()
                    new_interface.mac = sub_child.attributes.mac.value
                    new_interface.ip = sub_child.attributes.ip.value
                    new_interface.name = sub_child.attributes.name.value
                    result.push(new_interface)
                }
            }
        }
    }
    let resp = await fetch(`/api/v1/agents/${currentAgent}/interfaces`,
    { method: 'PATCH',
    headers: {"Content-Type": "application/json",},
    body: JSON.stringify(result) 
    }
    )
    getAgentData().then((data) => {
        agentData = data
        fillAgentBar("agent_tools");
        fillAgentBar("agent_net_map");
        fillAgentBar("agent_nmap");
        fillAgentBar("agent_scapy");
        fillAgentBar("agent_masscan");
        fillAgentBar("agent_snmp");
        fillAgentBar("agent_recon_");
        fillAgentBar("agent_cert");
        fillAgentBar("agent_whois_");
        fillAgentBar("agent_brute_");
        fillAgentBar("agent_ip_info_");
        fillAgentBar("agent_acunetix");
        fillAgentBar("agent_screenshoter");
        fillAgentBar("agent_wappalyzer");
        fillAgentBar("agent_cpeguess");
        fillAgentBar("agent_searchvulns");
        fillAgentBar("agent_web_grabber");
        fillAgentBar("agent_lookup_");
        getInterfaceData(agentData.default_agent).then((data) => {
            interfaceData = data
            fillInterfaceBar("interface_tools");
            fillInterfaceBar("interface_net_map");
            fillInterfaceBar("interface_nmap");
            fillInterfaceBar("interface_scapy");
            fillInterfaceBar("interface_masscan");
            fillInterfaceBar("interface_snmp");
            fillInterfaceBar("interface_recon_");
            fillInterfaceBar("interface_cert");
            fillInterfaceBar("interface_whois_");
            fillInterfaceBar("interface_brute_");
            fillInterfaceBar("interface_ip_info_");
            fillInterfaceBar("interface_acunetix");
            fillInterfaceBar("interface_screenshoter");
            fillInterfaceBar("interface_wappalyzer");
            fillInterfaceBar("interface_cpeguess");
            fillInterfaceBar("interface_searchvulns");
            fillInterfaceBar("interface_lookup_");
        })
    })
    $('#editAgentInterfaces').modal('hide');
}