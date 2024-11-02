var levels = {info: "#0d6efd", error: "#dc3545", warning: "#ffc107",success:"#198754"};
function create_websocket(endpoint) {
    var sock = new WebSocket('wss://' + window.location.host + endpoint);
    
    sock.onmessage = function (message) {
        data = JSON.parse(message.data)
        if (window.location.pathname == '/network-map/' && data.command === "update") {
            get_nodes_and_edges(true)
            return;
        }
        if (data.command === undefined){
            create_toast(data.title, data.text, data.type)
        }
        if (window.location.pathname == '/tools/' && data.command === "update") {
            get_all_ips_with_open_port_snmp();
            return;
        }
    };
    sock.onerror = function (error) {console.log(error)}
    sock.onopen = function (event) {console.log('connection is open')}
    sock.onclose = function (event) {console.log('connection is close')}
    return sock
}
var message_sock = create_websocket('/api/websocket/message')

function redirect_fetch(url, method, body) {
    fetch(url, {method: method, redirect: 'follow', body: body == undefined ? null: body})
    .then(response => {
        if (response.redirected) {window.location.href = response.url }
    })
    .catch(function(err) {
        console.log(err)
    })
}
function create_toast(title, message, level="info", time="just now") {
    var toast_holder = document.getElementById("toast_holder")
    var toast = document.createElement("div")
    toast.classList.add("toast", "fade")
    toast.innerHTML = create_html_toast(title, message, time, levels[level])
    var toast_instance = new bootstrap.Toast(toast)
    toast_holder.prepend(toast)
    toast_instance.show()

    var notification_holder = document.getElementById("notifications_body")
    var notification_toast = document.createElement("div")
    notification_toast.classList.add("toast", "fade")
    notification_toast.innerHTML = create_html_toast(title, message, time, levels[level])
    notification_toast.setAttribute("data-bs-autohide",false)
    var notification_toast_instance = new bootstrap.Toast(notification_toast)
    notification_holder.prepend(notification_toast)
    notification_toast_instance.show()
};
function create_html_toast(title, message, time, level) {
    return `
            <div class="toast-header">
                <svg width="25" height="25">
                    <rect fill=${level} y="3" width="20" height="20" rx="3" />
                </svg>
                <strong class="me-auto">${title}</strong>
                <small class="text-muted">${time}</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>`
};
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
function ajax_and_toast(url, type, data, title, level, message) {
    try {
        var res = ajax_request(url, type, data);
        create_toast(title, message == undefined ? res.message : message, level)
    } catch (error) {
        console.log(error);
    }
};
function create_modal(element_id, title, content, ok_text, ok_func) {
    var modal_elem = document.getElementById(element_id)
    modal_elem.innerHTML = `<div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="exampleModalLabel">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-primary">${ok_text}</button>
                </div>
            </div>
        </div>
    </div>`
    var modal = new bootstrap.Modal(modal_elem.children[0])
    var ok_button_elem = modal_elem.getElementsByClassName('btn btn-primary')[0]
    ok_button_elem.onclick = function() {ok_func(); modal.hide()}
    return modal
};