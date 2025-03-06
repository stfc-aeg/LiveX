let detect_module_modifications;
let last_message_timestamp = '';
let sequence_modules = {};
let is_executing;
let sequencer_endpoint;
let detect_changes_switch  = document.getElementById('detect-module-changes-toggle');
let execution_spinner = document.getElementById("execution-status-spinner");
let execution_text = document.getElementById("execution-status-text");
let execution_progress = document.getElementById("execution-progress");
let execution_progress_bar = document.getElementById("execution-progress-bar");
let execution_status_progress = document.getElementById("execution-status-progress");

const ALERT_ID = {
    'sequencer_error': '#command-sequencer-error-alert',
    'sequencer_info': '#command-sequencer-info-alert',
};

const BUTTON_ID = {
    'all_execute': '.execute-btn',
    'reload': '#reload-btn',
    'abort': '#abort-btn'
};

/**
 * This function is called when the DOM content of the page is loaded, and initialises
 * various elements of the sequencer page. The sequence module layout and log messages
 * are initialised from the current state of the adapter and the current execution state
 * is retrieved and managed appropriately.
 */
document.addEventListener("DOMContentLoaded", function () {

    // Initialise the sequencer adapter endpoint
    sequencer_endpoint = new AdapterEndpoint("sequencer");

    build_sequence_modules_layout();
    display_log_messages();

    sequencer_endpoint.get('')
    .then(result => {
        is_executing = result.is_executing;
        detect_module_modifications = result.detect_module_modifications;

        if (is_executing) {
            disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, true);
            disable_buttons(`${BUTTON_ID['abort']}`, false);
            display_execution(result.execute);
            await_execution_complete();
            await_process_execution_complete();
        }
        else
        {
            disable_buttons(`${BUTTON_ID['abort']}`, true);
            hide_execution();
        }

        set_detect_module_changes_toggle(detect_module_modifications);
        if (detect_module_modifications) {
            await_module_changes();
        }
    })
    .catch(error => {
        display_alert(ALERT_ID['sequencer_error'], error.message);
    });
});

/**
 * This is called when a change in the Detect Changes toggle is detected. Depending on
 * whether the toggle was enabled or disabled, it calls the mechanism on the backend to
 * either enable or disable the detect module changes process. If the toggle is enabled,
 * it calls the await_module_changes function to listen for module changes. It also
 * displays an alert message if an error occurs.
 */
detect_changes_switch.addEventListener("change", function() {
    enabled = detect_changes_switch.checked;
    sequencer_endpoint.put({ 'detect_module_modifications': enabled })
    .then(() => {
        detect_module_modifications = enabled;
        if (enabled) {
            await_module_changes();
        }
    })
    .catch(error => {
        if (enabled) {
            set_detect_module_changes_toggle(false);
        }
        display_alert(ALERT_ID['sequencer_error'], error.message);
    });
});

/**
 * This function listens for module changes by calling itself every second. It displays
 * an alert message when it detects that the backend has reported of module changes. 
 */
function await_module_changes() {
    sequencer_endpoint.get('module_modifications_detected')
    .then(result => {
        if (result.module_modifications_detected) {
            info_message = 'Code changes were detected, click the Reload button to load them';
            display_alert(ALERT_ID['sequencer_info'], info_message);
        }

        if (detect_module_modifications) {
            setTimeout(await_module_changes, 1000);
        }
    })
    .catch(error => {
        display_alert(ALERT_ID['sequencer_error'], error.message);
    });
}

/**
 * This function enables or disables the Detect Changes toggle.
 */
function set_detect_module_changes_toggle(detect_module_modifications) {
    detect_changes_switch.checked = detect_module_modifications;
}

/**
 * This function calls the reloading mechanism implemented on the backend which decides
 * which modules need to be reloaded. It disables the execute and reload buttons before
 * making a call to the backend and enables them when the process completes or fails.
 * It also calls the build_sequence_modules_layout to rebuild the layout and displays
 * the relevant messages in the alerts depending on the process outcome.
 */
function reload_modules() {
    hide_alerts(`${ALERT_ID['sequencer_info']},${ALERT_ID['sequencer_error']}`);
    disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, true);

    alert_id = '';
    alert_message = '';
    sequencer_endpoint.put({ 'reload': true })
    .then(() => {
        alert_id = ALERT_ID['sequencer_info'];
        alert_message = 'The sequence modules were successfully reloaded';
    })
    .catch(error => {
        alert_id = ALERT_ID['sequencer_error'];
        alert_message = error.message
        if (!alert_message.startsWith('Cannot start the reloading')) {
            alert_message += '.<br><br>To load the missing sequences, first resolve the errors and then click the Reload button.';
        }
    })
    .then(() => {
        display_alert(alert_id, alert_message);
        build_sequence_modules_layout();
        disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, false);
    });
}

function abort_sequence() {
    hide_alerts(`${ALERT_ID['sequencer_info']},${ALERT_ID['sequencer_error']}`);

    alert_id = '';
    alert_message = '';
    sequencer_endpoint.put({ 'abort': true })
    .then(() => {
        alert_id = ALERT_ID['sequencer_info'];
        alert_message = "Abort sent to currently executing sequence";
    })
    .catch(error => {
        alert_id = ALERT_ID['sequencer_error'];
        alert_message = error.message;
    })
    .then(() => {
        display_alert(alert_id, alert_message);
    });
}
/**
 * This function replicates the equivalent jQuery isEmptyObject, returning true if the
 * object passed as an parameter is empty.
 */
function is_empty_object(obj) {
    return Object.keys(obj).length === 0;
}

/**
 * This function executes a sequence. Each sequence in the UI has an Execute button
 * whose id contains the name of the sequence, and it decides which sequence to execute
 * based on the id. If the sequence has parameter(s) then it will get input values and
 * send them to the back end before executing it. Because the execute call to the
 * backend is asynchronous, it calls the await_execution_complete function with a
 * slight delay. It also disables the execute and reload buttons, and displays
 * messages in the alerts about any errors that may occur during the processes.
 */
function execute_sequence(button) {
    clicked_button_id = button.id;
    arr = clicked_button_id.split('-');
    seq_module_name = arr[0];
    seq_name = arr[1];
    params = sequence_modules[seq_module_name][seq_name];

    if (!is_empty_object(params)) {
        
        data = get_input_parameter_values(params);
        
        sequencer_endpoint.put(data, `sequence_modules/${seq_module_name}/${seq_name}`)
        .then(() => {
            hide_alerts(`${ALERT_ID['sequencer_info']},${ALERT_ID['sequencer_error']},.sequence-alert`);
            disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, true);
            disable_buttons(`${BUTTON_ID['abort']}`, false);
            display_execution(`${seq_module_name}/${seq_name}`);

            sequencer_endpoint.put({ 'execute': seq_name })
            .catch(error => {
                alert_message = error.message;
                if (alert_message.startsWith('Invalid list')) {
                    alert_message = alert_message.substring(alert_message.lastIndexOf(':') + 2);
                }

                display_alert(`#${seq_name}-alert`, alert_message);
            });

            setTimeout(await_execution_complete, 250);
            setTimeout(await_process_execution_complete, 500);
        })
        .catch(error => {
            alert_message = error.message;
            if (alert_message.startsWith('Type mismatch updating')) {
                last_slash = alert_message.lastIndexOf('/');
                second_to_last_slash = alert_message.lastIndexOf('/', last_slash - 1);
                param_name = alert_message.substring(second_to_last_slash + 1, last_slash);
                alert_message = `${param_name} - ${alert_message.substring(alert_message.lastIndexOf(':') + 2)}`;
            }

            display_alert(`#${seq_name}-alert`, alert_message);
        });

    } else {
        disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, true);
        disable_buttons(`${BUTTON_ID['abort']}`, false);
        display_execution(`${seq_module_name}/${seq_name}`);
        sequencer_endpoint.put({ 'execute': seq_name })
        .catch(error => {
            alert_message = error.message;
            display_alert(`#${seq_name}-alert`, alert_message);
        });

        setTimeout(await_execution_complete, 250);
        setTimeout(await_process_execution_complete, 500);
        
    }
}

/**
 * This function gets the input parameter values. The id of each parameter
 * input box contains the name of the parameter. It calls the parse_parameter_value
 * function if the parameter type is not of type string.
 */
function get_input_parameter_values(params) {
    data = {};
    for (param in params) {
        param_val = document.querySelector(`#${seq_name}-${param}-input`).value;
        param_type = params[param]['type'];

        if (param_type != 'str') {
            param_val = parse_parameter_value(param_val, param_type);
        }

        data[param] = { 'value': param_val };
    }

    return data;
}

/**
 * This function parses the parameter value from string to the correct type.
 * Parsing is required because input boxes hold values in form of strings.
 * If the parameter is of type list, then the string is split by comma to
 * form an array of strings.
 */
function parse_parameter_value(param_val, param_type) {
    if (param_type.startsWith('list')) {
        param_type = 'list';
    }

    switch (param_type) {
        case 'int':
            param_val = parseInt(param_val);
            break;
        case 'float':
            param_val = parseFloat(param_val);
            break;
        case 'bool':
            param_val = param_val == 'True';
            break;
        case 'list':
            param_val = param_val.split(',');
            break;
    }

    return param_val;
}

/**
 * This function waits for the execution to complete by calling itself if the process
 * is not finished. It calls the display_log_messages to display any log messages.
 * It enables the execute and reload buttons when it detects that the execution
 * process has completed.
 */
function await_execution_complete() {
    sequencer_endpoint.get('is_executing')
    .then(result => {
        display_log_messages();
        is_executing = result.is_executing
        if (is_executing) {
            update_execution_progress();
            setTimeout(await_execution_complete, 500);
        } else {
            disable_buttons(`${BUTTON_ID['all_execute']},${BUTTON_ID['reload']}`, false);
            disable_buttons(`${BUTTON_ID['abort']}`, true);
            hide_execution();
        }
    });
}

/**
 * This function waits for the execution of a process task to complete by calling
 * itself if the process is not finished. It calls the display_log_messages to 
 * display any log messages.
 */
function await_process_execution_complete() {
    sequencer_endpoint.get('process_tasks')
    .then(result => {
        display_log_messages();
        process_tasks = result.process_tasks
        if (process_tasks.length != 0) {
            setTimeout(await_process_execution_complete, 500);
        }
    });
}

/**
 * This function displays the alert and the given alert message by removing
 * the d-none class from the div(s).
 */
function display_alert(alert_id, alert_message) {
    let alert_elem = document.querySelector(alert_id);
    alert_elem.innerHTML = alert_message;
    alert_elem.classList.remove('d-none');
}

/**
 * This function hides the alert(s) and the alert message(s) by adding the d-none
 * class to the div(s).
 */
function hide_alerts(alert_id_or_ids) {
    alert_elems = document.querySelectorAll(alert_id_or_ids);
    alert_elems.forEach(element => {
        element.innerHTML = '';
        element.classList.add('d-none');
    });
    //$(alert_id_or_ids).addClass('d-none').html('');
}

/*
 * This function displays the excution progress elements on the UI
 */
function display_execution(sequence_name)
{
    execution_spinner.classList.remove('d-none');
    execution_text.innerHTML = "<b>Executing:&nbsp;" + sequence_name + "</b>";
    execution_progress_bar.style.width = "0%";
    execution_progress_bar.setAttribute('aria-valuenow', 0);
    execution_status_progress.innerHTML = ""

    execution_progress.classList.remove('d-none');
}

/*
 * This function hides the eexcution progress elements on the UI
 */
function hide_execution()
{
    execution_progress.classList.add('d-none');
    execution_spinner.classList.add('d-none');
    execution_text.innerHTML = "";
    execution_status_progress.innerHTML = "";
}

/*
 * This function updates the execution progress bar
 */

function update_execution_progress()
{
    sequencer_endpoint.get('execution_progress')
    .then(result => {
        var current = result.execution_progress.current;
        var total = result.execution_progress.total;
        if (total != -1)
        {
            var percent_complete = Math.floor((100.0 * current) / total);
            execution_progress_bar.style.width = percent_complete + "%";
            execution_progress_bar.setAttribute('aria-valuenow', percent_complete);
            execution_status_progress.innerHTML = "<b>(" + current + "/" + total + ")</b>";
        }
        else
        {
            execution_progress_bar.style.width = "100%";
            execution_status_progress.innerHTML = "";
        }
    });
}

/**
 * This function disables the button(s) if disabled is True, otherwise it enables them.
 */
function disable_buttons(button_id_or_ids, disabled) {
    button_elems = document.querySelectorAll(button_id_or_ids)
    button_elems.forEach(element => {
        element.disabled = disabled;
    });
    //$(button_id_or_ids).prop('disabled', disabled);
}

/**
 * This function extracts the message from the error response. 
 */
function extract_error_message(jqXHR) {
    response_text = JSON.parse(jqXHR["responseText"]);
    return response_text['error'];
}

/**
 * This function displays the log messages that are returned by the backend in the
 * pre-scrollable element and scrolls down to the bottom of it. It stores the
 * timestamp of the last message so that it can tell the backend which messages it
 * needs to get next. All log messages are returned if the last_message_timestamp is
 * empty and this normally happens when the page is reloaded.
 */
function display_log_messages() {
    get_log_messages()
    .then(result => {
        log_messages = result.log_messages;
        if (!is_empty_object(log_messages)) {
            last_message_timestamp = log_messages[log_messages.length - 1][0];

            pre_scrollable = document.querySelector('#log-messages');
            for (log_message in log_messages) {
                timestamp = log_messages[log_message][0];
                timestamp = timestamp.substr(0, timestamp.length - 3);
                pre_scrollable.innerHTML += 
                    `<span style="color:#007bff">${timestamp}</span> ${log_messages[log_message][1]}<br>`;
                pre_scrollable.scrollTop = pre_scrollable.scrollHeight;
            }
        }
    })
    .catch(error => {
        alert_message = 'A problem occurred while trying to get log messages: ' + error.message;
        display_alert(ALERT_ID['sequencer_info'], alert_message);
    });
}

/**
 * This function gets the log messages from the backend.
 */
function get_log_messages() {
    return sequencer_endpoint.put({ 'last_message_timestamp': last_message_timestamp })
        .then(sequencer_endpoint.get('log_messages')
    );
}

/**
 * This function gets information about the loaded sequence modules from the backend and based
 * on that, it dynamically builds and injects the HTML code for the sequence modules layout.
 */
function build_sequence_modules_layout() {
    sequencer_endpoint.get('sequence_modules')
    .then(result => {
        
        sequence_modules = result.sequence_modules;
        if (!is_empty_object(sequence_modules)) {
            // Sort the modules in alphabetical order
            sequence_modules = Object.fromEntries(Object.entries(sequence_modules).sort());
            let html_text = `<div id="accordion" role="tablist">`;
            for (seq_module in sequence_modules) {
                sequences = sequence_modules[seq_module];

                html_text += `
                <div class="row border">
                    <div class="col-md-12">
                        <div class="row">
                            <div class="col-md-12 text-center">
                                <h4><b>${seq_module}</b></h4>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-md-12">
                                ${build_sequences_layout(seq_module, sequences)}
                            </div>
                        </div>
                    </div>
                </div>`;
            }

            html_text += '</div>';
            document.querySelector('#sequence-modules-layout').innerHTML = html_text;
        } else {
            error_message = 'There are no sequence modules loaded';
            display_alert(ALERT_ID['sequencer_info'], error_message);
        }
    });
}

/**
 * This function builds the sequences layout for each module. It creates a collapsable
 * element if the sequence has parameters. 
 */
function build_sequences_layout(seq_module, sequences) {
    html_text = '';
    for (seq in sequences) {
        params = sequences[seq];

        html_text += `
        <div class="card">
            <div class="card-header" role="tab" id="${seq}-heading">
                <div class="row">
                    <div class="col-md-5">
                        <h5>`;

        sequence_params_layout = '';
        if (is_empty_object(params)) {
            html_text += `${seq}`;
        } else {
            html_text += `
            <a data-bs-toggle="collapse" href="#${seq}-collapse" aria-expanded="false"
               aria-controls="${seq}-collapse" class="collapsed">
                ${seq}
            </a>`;
            sequence_params_layout = build_sequence_parameters_layout(seq, params);
        }

        html_text += `
                        </h5>
                    </div>
                    <div class="col-md-5">
                        <div class="sequence-alert alert alert-danger mb-0 d-none" role="alert" id="${seq}-alert"></div>
                    </div>
                    <div class="col-md-2">
                        <button type="submit" class="btn btn-primary execute-btn mb-3" onclick="execute_sequence(this)" id="${seq_module}-${seq}-execute-btn">Execute</button>
                    </div>
                </div>
            </div>
            ${sequence_params_layout}
        </div>`;
    }

    return html_text;
}

/**
 * This function builds the input boxes for all the parameters of the sequence. A
 * tooltip is added next to the parameter name label for all list parameters which
 * provides information to users about how they need to input the list elements.
 */
function build_sequence_parameters_layout(seq, params) {
    let html_text = `
    <div id="${seq}-collapse" class="collapse" role="tabpanel" aria-labelledby="${seq}-heading" data-parent="#accordion">
        <div class="card-body">`;
    for (param in params) {
        attributes = params[param];
        param_type = attributes['type'];
        param_default_value = attributes['default'];

        html_text += `
        <div class="row">
            <div class="col-md-2">
                <label for="${seq}-${param}-input">${param} (${param_type})</label>`;

        if (param_type.startsWith('list')) {
            html_text += '<i class="far fa-question-circle fa-fw my-tooltip" title="Enter elements as a comma separate string and do not include quotes or square brackets"></i>';
        }

        html_text += `
        </div>
        <div class="col-md-10">`;

        if (param_type == 'bool') {
            html_text += `
            <select class="form-control mb-3" id="${seq}-${param}-input">
                <option>False</option>
                <option>True</option>
            </select>`;
        } else {
            input_type = (param_type == 'int' || param_type == 'float') ? 'number' : 'text';
            html_text += `<input type="${input_type}" value="${param_default_value}" class="form-control mb-3" id="${seq}-${param}-input" />`;
        }

        html_text += `
            </div>
        </div>`;
    }

    html_text += `
        </div>
    </div>`;

    return html_text;
}
