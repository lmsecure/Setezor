function create_websocket(endpoint, user_id) {
    var sock = new WebSocket('wss://' + window.location.host + endpoint);
    sock.onmessage = function (message) {
        let data = JSON.parse(message.data)
        //console.log(data)
        if (data.title === "Install module") {
            const text = data.text;
            const match = text.match(/^Module\s+(\w+)\s+successfully installed$/);
            const moduleName = match ? match[1] : null;
            if (window.moduleInstaller) {
                window.moduleInstaller.onModuleInstalled(moduleName);
            }
            return;
        }
        if (window.location.pathname == '/network-map/' && data.command === "update") {
            get_nodes_and_edges([], true)
            return;
        }
        if (data.command == "notify_user" && data.user_id && data.user_id == user_id){
            create_toast(data.title, data.text, data.type)
            if (data.title === 'Import project' && window.location.pathname === '/projects') {location.reload()}
            return;
        }
        if (data.command === "notify"){
            create_toast(data.title, data.text, data.type)
            return;
        }
    };
    sock.onerror = function (error) {console.log(error)}
    sock.onopen = function (event) {console.log('connection is open')}
    sock.onclose = function (event) {console.log('connection is close')}
    return sock
}

async function getScans(){
    let resp = await fetch("/api/v1/scan")
    let scans = await resp.json()
    return scans
}

async function getCurrentScan(){
    let resp = await fetch("/api/v1/scan/current")
    if (resp.redirected){
        return null
    }
    let scan = await resp.json()
    return scan
}

function ajax_request(url, type, data, success_func, error_func, async=false) {
    var response = $.ajax({
                    url:   url,
                    async: async,
                    dataType: 'json',
                    data:  ['post', 'put'].includes(type.toLowerCase()) ? JSON.stringify(data) : data,
                    statusCode: {
                        302: function(some) {
                            console.log(some)
                        }
                    },
                    success: function (json) {
                        if (success_func != undefined){
                            success_func()
                        } else {
                            response = json;
                        }
                        
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        // if (error_func != undefined){
                        //     error_func()
                        // } else {
                        //     create_toast('Request to server ERROR', `Request to server to ${url} finished with error. Details: textStatus: ${textStatus}`, 'error')
                        // }
                        // throw `ERROR: request to ${url}`
                    },
                    type: type
                });
return response.responseJSON;
};
