api_version = '0.1';
var input_text = document.getElementById("setPtInput");
var set_button = document.getElementById("set-button");
set_button.addEventListener("click", () => set_temp());

var kp_input = document.getElementById("KpInput");
var kp_button = document.getElementById("KpButton");
kp_button.addEventListener("click", () => set_kp());

var ki_input = document.getElementById("KiInput");
var ki_button = document.getElementById("KiButton");
ki_button.addEventListener("click", () => set_ki());

var kd_input = document.getElementById("KdInput");
var kd_button = document.getElementById("KdButton");
kd_button.addEventListener("click", () => set_kd());

$( document ).ready(function() {

    update_api_version();
    update_api_adapters();
    poll_update();
});

function poll_update() {
    update_background_task();
    setTimeout(poll_update, 1000);
}

function update_api_version() {

    $.getJSON('/api', function(response) {
        $('#api-version').html(response.api);
        api_version = response.api;
    });
}

function update_api_adapters() {

    $.getJSON('/api/' + api_version + '/adapters/', function(response) {
        adapter_list = response.adapters.join(", ");
        $('#api-adapters').html(adapter_list);
    });
}

function update_background_task() {

    $.getJSON('/api/' + api_version + '/livex/pid_loop', function(response) {
        var pid_output = response.pid_loop.pid_output;
        var resistor_temp  = response.pid_loop.resistor_temp;
        var ambient_temp  = response.pid_loop.ambient_temp;
        $('#pid-output').html(pid_output);
        $('#resistor-temp').html(resistor_temp);
        $('#ambient-temp').html(ambient_temp);
    });
}
function pid_enable() { 
    var enabled = $('#pid-enable').prop('checked');
    console.log("PID-enable changes to " + (enabled ? "true" : "false"));
    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/livex/pid_loop',
        contentType: "application/json",
        data: JSON.stringify({'pid_enable': enabled})
    });
}

function set_temp() {
    console.log("Setting new temperature setpoint");
    var value = parseFloat(input_text.value);

    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/livex/pid_loop',
        contentType: "application/json",
        data: JSON.stringify({'setpoint': value})
    })
}

function set_term_PUT(term, value) {
    var obj = {};
    obj[term] = value;
    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/livex/pid_loop',
        contentType: "application/json",
        data: JSON.stringify(obj)
    })
}

function set_kp() {
    console.log("Setting new proportional term");
    var value = parseFloat(kp_input.value);
    set_term_PUT("proportional", value);
}

function set_ki() {
    console.log("Setting new integral term");
    var value = parseFloat(ki_input.value);
    set_term_PUT("integral", value);
}

function set_kd() {
    console.log("Setting new derivative term");
    var value = parseFloat(kd_input.value);
    set_term_PUT("derivative", value);
}