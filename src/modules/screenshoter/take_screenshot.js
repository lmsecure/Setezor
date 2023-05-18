var page = require('webpage').create(),
    system = require('system'),
    address, output, timeout, screen_size, clip;

address = system.args[1];
output = system.args.length > 2 ? system.args[2] : new Date().toJSON() + '.png';
timeout = system.args.length > 3 ? system.args[3] : 5000;
screen_size = system.args.length > 4 ? system.args[4] : '1024*768';
clip = system.args.length > 5 ? system.args[5] : undefined;


page.viewportSize = {width: screen_size.split('*')[0], height: screen_size.split('*')[1]};
if (clip != undefined) {
    var top, left, width, height;
    top = clip.split('x')[0].split('*')[0];
    width = clip.split('x')[1].split('*')[0];
    left = clip.split('x')[0].split('*')[1];
    height = clip.split('x')[1].split('*')[1];
    page.clipRect = {top: top, left: left, width: width, height: height};
}
page.settings.resourceTimeout =  timeout;

generate_console_message = function (status, message) {
    if (message === undefined) {
        switch(status) {
            case 'success':
                var message = 'Screenshot successfuly taken';
                break;
            case 'error': 
                var message = 'Cannot take screenshot';
                break;
        };
    };
    return `${new Date().toJSON()} - ${status.toUpperCase()} - ${address} - ${message}`;
};

page.onResourceTimeout = function (e) {
    console.log(generate_console_message('error', 'Timeout error'));
    phantom.exit();
};

page.onLoadFinished = function(status) {
    switch(status) {
        case 'success':
            page.render(output);
            console.log(generate_console_message('success'));
            phantom.exit();
        case 'fail':
            console.log(generate_console_message('error'));
            phantom.exit();
    }
};

page.open(address, function (status) {
});