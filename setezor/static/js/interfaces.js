
/* Класс интерфейса */
class Interface {

    constructor(id, name, ip_addr, mac_addr) {

        console.assert(typeof (id) == 'number')
        console.assert(typeof (name) == 'string')
        console.assert(typeof (ip_addr) == 'string')
        console.assert(typeof (mac_addr) == 'string')

        this.id = id
        this.name = name
        this.ip_addr = ip_addr
        this.mac_addr = mac_addr
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
async function getInterfaceData() {
    resp = await fetch('/api/interface/interfaces')
    if (resp.ok) {
        data = await resp.json()
        ifaces = []
        data.interfaces.forEach((element) => {
            ifaces.push(new Interface(element.id, element.name, element.ip_address, element.mac_address))
        })
        iface_data = new InterfaceData(ifaces, data.default_interface)
        return iface_data
    }
}

function createInterfaceElement(id, name) {
    return `<li><a class="dropdown-item" interface_id=${id} interface_name=${name} onclick=setDefaultInterface(${id})>${id} - ${name}</a></li>`
}

function fillInterfaceBar(div_id) {
    elem = document.getElementById(div_id)
    button = elem.getElementsByTagName('button')[0]
    list = elem.getElementsByTagName('ul')[0]

    html = []
    interfaceData.interfaces.forEach((interface) => {
        html.push(createInterfaceElement(interface.id, interface.name))
    })
    default_interface = interfaceData.interfaces.find((elem) => elem.id == interfaceData.default_interface)
    button.innerHTML = `${default_interface.id} - ${default_interface.name}`
    list.innerHTML = html.join('\n')
}


/* Функция, которая в диве создаст плашку с выбором интерфейса */
function createInterfaceBar(div_id) {
    elem = document.getElementById(div_id)

    html = `
    <div class="dropdown">
        <button id='interface_button' class="btn btn-secondary dropdown-toggle" type="button" id="interfaceBarButton" data-bs-toggle="dropdown" aria-expanded="false">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </button>
        <ul class="dropdown-menu" aria-labelledby="interfaceBarButton">
        </ul>
    </div>`
    elem.innerHTML = html
    return elem
}


async function setDefaultInterface(id) {
    url = '/api/interface/set_default?' + new URLSearchParams({ interface_id: id })
    resp = await fetch(url, { method: 'put' })
    if (resp.ok) {
        interfaceData.default_interface = Number(id)
        fillInterfaceBar('interface_bar')
    }
    else {
        create_toast('Error on edit default interface', 'Can not edit default interface', 'error')
    }
}