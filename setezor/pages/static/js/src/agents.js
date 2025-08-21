
class IP {
    constructor(id, address) {
        this.id = id
        this.address = address
    }
}

class Agent {
    constructor(id, name, parent_agent_id, description, is_server, red, green, blue) {
        this.id = id
        this.name = name
        this.parent_agent_id = parent_agent_id
        this.description = description
        this.is_server = is_server
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


async function getAgentData() {
    const resp = await fetch('/api/v1/agents_in_project/settings');
    if (resp.ok) {
        const data = await resp.json();
        const agents = data.map((element) => {
            const hex_rgb = hexToRgb(element.color);
            return new Agent(
                element.id,
                element.name,
                element.parent_agent_id,
                element.description,
                element.is_server,
                hex_rgb.r,
                hex_rgb.g,
                hex_rgb.b
            );
        });
        return new AgentData(agents, agents[agents.length - 1].id);
    }
}

function createAgentElement(id, name) {
    return `<li><a class="dropdown-item" data-agent-id="${id}" onclick="setDefaultAgent('${id}')">${name}</a></li>`;
}

/* Функция, которая заполнит панель агентов */
function fillAgentBar(barSelector) {
    const elem = document.querySelector(`[data-agent-bar="${barSelector}"]`);
    if (!elem) return;

    const button = elem.querySelector("button");
    const list = elem.querySelector("ul");

    const html = agentData.agents
        .filter((agent) => !agent.is_server)
        .map((agent) => createAgentElement(agent.id, agent.name))
        .join("\n");

    const defaultAgent = agentData.agents.find((agent) => agent.id === agentData.default_agent);
    if (defaultAgent != undefined){
        button.innerHTML = `${defaultAgent.name}`;
    }
    list.innerHTML = html;
}

/* Функция, которая создаёт панель агентов */
function createAgentBar(barSelector) {
    const elem = document.querySelector(`[data-agent-bar="${barSelector}"]`);
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

function setDefaultAgent(id) {
    agentData.default_agent = id;

    // Обновляем все панели агентов
    document.querySelectorAll("[data-agent-bar]").forEach((bar) => {
        fillAgentBar(bar.getAttribute("data-agent-bar"));
    });

    // Загружаем интерфейсы для выбранного агента
    getInterfaceData(agentData.default_agent).then((data) => {
        interfaceData = data;

        // Обновляем все панели интерфейсов
        document.querySelectorAll("[data-interface-bar]").forEach((bar) => {
            fillInterfaceBar(bar.getAttribute("data-interface-bar"));
        });
    });
}

function getAgent() {
    agent = agentData.agents.find((elem) => elem.id == agentData.default_agent)
    return agent.id
}