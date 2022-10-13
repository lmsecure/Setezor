var levels = {info: "#0d6efd", error: "#dc3545", warning: "#ffc107"};
function create_toast(title, message, level="info", time="just now") {
    var toast_holder = document.getElementById("toast_holder")
    var toast = document.createElement("div")
    toast.classList.add("toast", "fade")
    toast.innerHTML = create_html_toast(title, message, time, levels[level])
    var toast_instance = new bootstrap.Toast(toast)
    toast_holder.appendChild(toast)
    toast_instance.show()
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
function upload_binary_file(file_ext, task_type, task_title) {
    let input = document.createElement('input');
    input.type = "file";
    input.multiple = true;
    input.accept = file_ext
    input.onchange = e => { 
        for (var file of e.target.files)
        {
            var reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = readerEvent => {
                ajax_request('/api/task/', 'post', {task_type: task_type, args: {log_file: readerEvent.target.result, to_log: {task_type: task_type,  filename: file.name}}});
                create_toast('Task started', `Task ${task_title} parse started`)
            }
        }
    }
    input.click();           
};
function ajax_request(url, type, data, success_func, error_func) {
    var response = $.ajax({
                    url:   url,
                    async: false,
                    dataType: 'json',
                    data:  type.toLowerCase() == 'post'? JSON.stringify(data) : data,
                    success: function (json) {
                        if (success_func != undefined){
                            success_func()
                        } else {
                            response = json;
                        }
                        
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        if (error_func != undefined){
                            error_func()
                        } else {
                            create_toast('Request to server ERROR', `Request to server to ${url} finished with error. Details: textStatus: ${textStatus}`, 'error')
                        }
                        throw `ERROR: request to ${url}`
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
function craft_nmap_command () {
    var ip_target = document.getElementById('ip_target').value
    var nmap_options = [];
    for (var option of document.getElementById('nmap_options'))
    {
        if (option.selected) {
            nmap_options.push(option.value);
        }
    }
    document.getElementById('nmap_command').value = "nmap -oX - " + nmap_options.join(" ") + " " + ip_target
};