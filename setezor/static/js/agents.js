
class IP {
    constructor(id, address) {
        this.id = id
        this.address = address
    }
}

class Agent {
    constructor(id, name, description, ip, red, green, blue) {
        this.id = id
        this.name = name
        this.description = description
        this.ip = ip
        this.red = red
        this.green = green
        this.blue = blue
    }
}

/* Данные об агентах. содержит список агентов и id дефолтного */
class AgentData {
    constructor(agents, default_agent) {
        this.agents = agents
        this.default_agent = default_agent
    }
}

/* color functions */
function hexToRgb(hex) {
    result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

function componentToHex(color) {
    hex = color.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}
function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}


async function getAgentData(page = 1, ifaces = []) {
    params = { page: page, size: 100 }
    params_json = JSON.stringify(params)
    resp = await fetch('/api/agent/all?' + new URLSearchParams({ params: params_json }))

    if (resp.ok) {
        data = await resp.json()
        data.forEach(element => {
            rgb = JSON.parse(element.color)
            ifaces.push(
                new Agent(element.id, element.name, element.description, element.ip, rgb.red, rgb.green, rgb.blue)
            )
        })

        resp = await fetch('/api/agent/get_default')
        agent_id = await resp.text()
        return new AgentData(ifaces, agent_id)
    }
}

function createAgentElement(id, name) {
    return `<li><a class="dropdown-item" onclick=setDefaultAgent(${id})>${id} - ${name}</a></li>`
}

/* Функция, которая заполнит плашку из созданной agentData */
function fillAgentBar(div_id) {
    elem = document.getElementById(div_id)
    button = elem.getElementsByTagName('button')[0]
    list = elem.getElementsByTagName('ul')[0]

    html = []
    agentData.agents.forEach((agent) => {
        html.push(createAgentElement(agent.id, agent.name))
    })
    default_agent = agentData.agents.find((elem) => elem.id == agentData.default_agent)
    button.innerHTML = `${default_agent.id} - ${default_agent.name}`
    list.innerHTML = html.join('\n')
}

/* Функция, которая в диве создаст плашку с выбором агента и интерфейса */
function createAgentBar(div_id) {
    elem = document.getElementById(div_id)

    html = `
    <div class="dropdown">
        <button id='agent_button' class="btn btn-secondary dropdown-toggle" type="button" id="agentBarButton" data-bs-toggle="dropdown" aria-expanded="false">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </button>
        <ul class="dropdown-menu" aria-labelledby="agentBarButton">
        </ul>
    </div>`
    elem.innerHTML = html
    return elem
}


async function setDefaultAgent(id) {
    url = '/api/agent/set_default?' + new URLSearchParams({ agent_id: id })
    resp = await fetch(url, { method: 'put' })
    if (resp.ok) {
        agentData.default_agent = Number(id)
        fillAgentBar('agent_bar')
    }
    else {
        create_toast('Error on edit default agent', 'Can not edit default agent', 'error')
    }
}