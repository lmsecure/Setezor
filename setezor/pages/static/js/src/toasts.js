var levels = {info: "#0d6efd", error: "#dc3545", warning: "#ffc107",success:"#198754"};
function create_toast(title, message, level = "info", position = "bottom-0 end-0") {
    var now = new Date();
    var year = now.getFullYear();
    var month = now.getMonth() + 1;
    var day = now.getDate();
    var hours = now.getHours();
    var minutes = now.getMinutes();
    var seconds = now.getSeconds();

    var dateString = `${year}-${month < 10 ? '0' + month : month}-${day < 10 ? '0' + day : day}`;
    var timeString = `${hours}:${minutes < 10 ? '0' + minutes : minutes}:${seconds < 10 ? '0' + seconds : seconds}`;
    var dateTimeString = `${dateString} ${timeString}`;

    var toast_holder = document.getElementById("toast_holder");

    toast_holder.className = "position-fixed " + position + " p-3";

    const max_toasts = 5;
    if (toast_holder.children.length >= max_toasts) {
        toast_holder.removeChild(toast_holder.firstChild);
    }

    var toast = document.createElement("div");
    toast.classList.add("toast", "fade");
    toast.innerHTML = create_html_toast(title, message, dateTimeString, levels[level]);
    var toast_instance = new bootstrap.Toast(toast);
    toast_holder.append(toast);
    toast_instance.show();

    var notification_holder = document.getElementById("notifications_body");
    var notification_toast = document.createElement("div");
    notification_toast.classList.add("toast", "fade");
    notification_toast.innerHTML = create_html_toast(title, message, dateTimeString, levels[level]);
    notification_toast.setAttribute("data-bs-autohide", false);
    var notification_toast_instance = new bootstrap.Toast(notification_toast);
    notification_holder.append(notification_toast); 
    notification_toast_instance.show();
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