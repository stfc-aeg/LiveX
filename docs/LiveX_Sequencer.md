# LiveX Sequencing

This document aims to cover all of the functions available to users of the sequencer for LiveX.
A function prefixed with ‘_’ is generally not one you will need to access, so not all of these are listed.

To use the sequencer, there are code examples and a README in the [odin-sequencer GitHub repository](https://github.com/stfc-aeg/odin-sequencer). Alternatively, there are some examples [in the LiveX repository](https://github.com/stfc-aeg/LiveX) too (see `/control/test/config/sequences`).

In short, you define functions in sequences files ( `control/test/config/sequences`). You then provide these functions in a list (`provides=['<name_of_function>']`) and these become visible in the user interface, with function arguments interpreted. Sequences can rely on other sequences; if those sequences are in another file, they can be used following `requires=['<name_of_file>']` (accessing all sequences in that file).


# Furnace

The `furnace adapter` controls the furnace hardware, tcp acquisition stream and has its own internal h5 logging. It manages the Modbus and TCP clients needed, thermocouple readings, and regularly polls updates from the firmware.  
Most of the control functions are delegated to its child classes: PID, ASPC, Gradient, and ThermocoupleManager.access.

Attributes:

- **pid_upper / pid_lower**: `PID` controller objects for the two heaters; see below.
- **gradient**: Gradient control object, see below.
- **aspc**: Auto SetPoint Control object, see below.
- **ip / port**: connection details for the PLC (Modbus/TCP).
- **mocking**: if True, uses mock Modbus/TCP clients instead of real hardware for testing.
- **bg_read_task_enable / bg_stream_task_enable**: booleans that control the two background tasks (PLC polling and TCP streaming).
- **bg_read_task_interval / bg_stream_task_interval**: polling intervals for the background read task and stream task. `bg_stream_task_interval` is derived from `pid_frequency`.
- **pid_frequency**: frequency (Hz) at which the PID runs; used to size buffers and determine when to flush fast data to disk. This is usually set by the `livex` adapter but is given a default on startup.
- **buffer_size**: derived from `pid_frequency`; number of fast readings written per second.
- **packet_decoder / tcp_reading / stream_buffer / data_groupname / event_buffer**: TCP packet decoding and buffers used to collect and batch acquisition data for HDF5 writes.
- **file_writer / log_directory / log_filename / file_open_flag**: file writing utility and current file state.
- **tc_manager / thermocouples**: thermocouple manager and list of thermocouple entries read from the PLC.
- **mod_client / tcp_client**: Modbus and TCP clients (real or mock) used for communications.
- **acquiring**: True while an acquisition is active.

Controller operations (important methods):

- **set_max_setpoint(value)**: update the maximum allowed setpoint (affects both PIDs) and writes the value to the PLC holding registers, toggling the setpoint update coil.

- **set_max_setpoint_increase(value)**: writes the maximum allowed setpoint increase (step) to the PLC.

- **_set_filename(value) / _set_filepath(value)**: update `FileWriter` filename/path (ensures `.h5` extension) and recompute full path; caller should avoid changing these during an active acquisition.
- **stop_all_pid(value=None)**: disables both PID controllers (acts as an emergency stop).

- **solo_acquisition(value)**: when `allow_solo_acquisition` is enabled, asks the `livex` adapter to start or stop a furnace-only acquisition via `livex.start_acquisition(acquisitions={'furnace': True})` or `livex.stop_acquisition()`.

- **_start_acquisition()**: low-level start used by the adapter; writes the acquisition coil on the PLC, opens the HDF5 file and marks `acquiring=True`. If the gradient is active, records that for metadata.

- **_stop_acquisition()**: low-level stop; clears the acquisition coil, writes any buffered stream data to HDF5, clears buffers, writes event batches and closes the file.

- **update_furnace_frequency(freq)**: updates `pid_frequency`, recalculates `buffer_size` and `bg_stream_task_interval`, and writes the new frequency to the PLC (also asserts an update coil). Passing non-positive values defaults to 1 Hz.



# Furnace Controls (PID, ASPC, Gradient, ThermocoupleManager)

The furnace control classes live under `control/src/livex/furnace/controls` and are exposed via the `FurnaceController` as `pid_upper`, `pid_lower`, `aspc`, `gradient` and `tc_manager`. e.g.: `furnace = get_context('furnace')` // `furnace.pid_upper`



### PID_upper/lower

`PID` instances manage one heater each and provide the live PID parameters and write helpers for the PLC.
Accessed in the sequencer through `.pid_upper` or `.pid_lower` on the furnace controller object.

| attr name      | description |
|----------------|-------------|
| enable         | (bool) is heater enabled (reads/writes a coil)
| setpoint       | (float) target temperature (written to holding register, update coil asserted)
| kp/ ki/ kd | (float) PID term values (written to holding registers)
| temperature    | (float) current measured temperature (read from input register)
| output         | (float) PID output (read from input register)
| outputsum      | (float) PID integral sum (read from input register)
| override_percent | (int) manual override percent (written to holding register)
| override_enable | (bool) enable manual override (writes coil)
| output_scalar  | (float) scaling applied to PID output (written to holding register)

Methods:
- `set_setpoint(value: float)`: write the new setpoint to the PLC. Enforces `max_setpoint` and `max_setpoint_increase` limits from the `FurnaceController`
- `set_proportional/integral/derivative(value: float)`: write the respective PID term to the PLC.
- `set_enable(value: bool)`: toggle the PID enable coil and subsequently enable/disable the heater
- `set_override_percent(value: float)` and `set_override_enable(value: bool)`: control the manual override output if `allow_pid_override` is enabled in options.
- `set_power_scalar(value: float (0-1))`: write the PID output scalar to the PLC.


### Auto SetPoint Control (ASPC)

Controls automatic, continuous adjustment of the setpoint.
Accessed in the sequencer through `.aspc` on the furnace controller object.

| attr name     | description |
|---------------|-------------|
| enable        | (bool) ASPC enabled (coil)
| heating       | (str) 'heating' or 'cooling' (writes coil)
| rate          | (float) average rate (C/s) — limited by a configured maximum and written to a holding register
| midpt_temp    | (float) midpoint temperature calculated/read from PLC

Key methods:
- `set_enable(value)`: write enable coil and assert update; emits `autosp_enable` event.
- `set_heating(value)`: set direction ('heating'/'cooling') by writing the heating coil and emits `autosp_heating` event.
- `set_rate(value)`: writes the rate to the PLC and asserts the update coil; emits `autosp_rate` event.

The `rate` parameter is interpreted by the PLC per-tick; the controller writes a float value and the hardware applies it across PID ticks.

### Gradient

Handles the thermal gradient behaviour between the two heaters.
Accessed in the sequencer through `.gradient` on the furnace controller object.

| attr name    | description |
|--------------|-------------|
| enable       | (bool) gradient enabled (coil)
| wanted       | (float) desired temperature change per mm (holding register)
| distance     | (float) distance in mm between heaters (holding register)
| actual       | (float) actual measured difference (input register)
| theoretical  | (float) theoretical difference (input register)
| high_heater  | ('Upper'|'Lower') which heater is defined as the high side (coil / read as index)

Key methods:
- `set_enable(value)`: toggles enable coil, activating the gradient logic in the PLC. If the gradient is enabled while acquiring, `was_gradient_active` is set for metadata.
- `set_distance(value)` / `set_wanted(value)`: set the respective gradient values. Emit `gradient_distance` / `gradient_wanted` events.
- `set_high(value)`: set which heater is 'high' - the other/'low' heater's setpoint will be *reduced* by the *theoretical* gradient value.

### ThermocoupleManager

`ThermocoupleManager` manages thermocouple configuration and readings. It maps logical thermocouple labels to physical PLC indices.
Accessed in the sequencer through `.tc_manager` on the furnace controller object.

Attributes:
- `num_mcp`: number of thermocouple inputs reported by the PLC (read from `modAddr.number_mcp_inp`), which should be 6.
- `thermocouples`: list of `Thermocouple` dataclass entries. Each entry contains `label`, `connection` (enum `CONNECTIONS` with values a..f), `addr` (holding register address used to write the selected index), `val_addr` (input register address for the thermocouple value), `index` (the index written into the PLC) and `value` (last-read temperature).

This means that to access a given thermocouple's value you need to check the labels by iterating over the list. The upper and lower heaters will always be labelled `upper_heater` and `lower_heater` respectively. Other names for 'extra' thermocouples will depend on your configuration file. If you need the temperatures of the heaters, it is better to access them through the `pid` objects' `temperature` attribute.

Key methods:
- There are no publically available methods in this class


# LiveX Adapter

The `LiveXController` is exposed as the `livex` context in the sequencer. It manages acquisition start/stop, freerun mode, trigger frequency control, and camera exposure settings.

| attr name               | description |
|-------------------------|-------------|
| ref_trigger             | (str) reference trigger name from config, usually `furnace` |
| frame_target            | (int) current acquisition frame target for the reference trigger |
| acquiring               | (bool) whether an acquisition is currently active |
| current_acquisition     | (list) names of subsystems currently being acquired |
| freerun                 | (bool) whether target values are overridden to 0 for continuous capture |
| filepaths               | (dict) current filenames and paths for `furnace`, `metadata`, and cameras |
| frequencies             | (subtree) per-trigger frequency controls under `livex.acquisition.frequencies` |
| cameras                 | (subtree) camera exposure controls and lookup toggle |
| trigger_manager         | (object) has methods to manage trigger frequencies, targets, and camera exposures. See below

### Methods
- `start_acquisition(acquisition: list)`: Start an acquisition. Pass a list of names ('furnace', 'widefov', 'narrowfov') to select which acquisition subsystems should run. The adapter then configures filenames, starts requested acquisitions, prepares cameras, and starts the trigger timers simultaneously.
- `stop_acquisition()`: Stop the acquisition. Disables timers, stops acquisitions, ends camera capture, writes metadata and sequence file, and then restarts in preview mod

### Trigger Manager (class)

The `TriggerManager` is the internal class used by `LiveXController` to manage trigger frequencies, frame targets, linked triggers, and camera exposure behavior.

It is exposed through `.trigger_manager` in the livex context in the sequencer.

| attr name | description |
|-----------| ----------- |
| linked_triggers | (list: str[]) connected triggers by name. when the frequency or exposure time on one is set, the other will be set to match it |
| use_exposure_lookup | (bool) use the exposure lookup table |
| frequencies | (dict) {trigger_name: frequency} |
| acq_frame_target | (int) acquisition frame target |
| acq_frame_frequency | (int) frequency of all triggers, used through set_acq_frame_frequency |
| freerun | (bool) is acquisition running endlessly (no frame target) |
| targets | (dict) {trigger_name: frame_target} used to set target of each trigger |

| method | description |
|--------|-------------|
| `set_freerun(value)` |  enable or disable freerun mode |
| `set_acq_frame_target(value)` | set the reference trigger frame target |
| `set_acq_frame_frequency(value)` | set one frequency for all triggers |
| `set_frequency(value, trigger=...)` |  set frequency for a named trigger |
| `link_triggers([t1, t2])` |  link two triggers together based on trigger names. linked|
| `unlink_triggers([t1, t2])` |  unlink two triggers based on trigger names|
| `set_use_exposure_lookup(value)` |  toggle exposure lookup for camera triggers |
| `set_camera_exposure(value, cam_name=...)` |  set exposure for a named camera |

# Trigger (adapter)

The trigger adapter creates a trigger for each value provided to it in the ‘triggers’ option in its config file. The triggers have their own callable functions, accessed via `trigger.triggers[trigger_name]`.

| attr name                | description |
|--------------------------|-------------|
| ip                      | (str) ip address for modbus server |
| status_bg_task_enable   | (int) is background task enabled |
| status_bg_task_interval | (int) background task interval in seconds |
| triggers                | (dict) {name: trigger} dictionary of Trigger objects based on names in config |

### Methods:
- `set_all_timers(values: dict)`: {'enable': bool, 'freerun': bool}. This function enables (enable: True) or disables (enable: False) all timers, with the additional 'freerun' key overwriting trigger targets to 0 if true. With a target of 0, timers run until stopped manually.


### Trigger (Class)

These are instantiated by the trigger adapter above, accessible via `trigger.triggers[trigger_name]`.

| attr name  | description |
|-----------|-------------|
| name      | (str) name of trigger |
| addr      | (dict) modbus addresses (see `modbusAddresses.py`) |
| frequency | (int) frequency of trigger |
| target    | (int) frame target |
| running   | (bool) is trigger currently running (read from hardware). Enable is a single-fire flag on trigger hardware, this is a status report |
| client    | (ModbusTCPClient) modbus client object from trigger adapter |

### Methods
- `set_enable(value: bool)`: turn the trigger on (True) or off (False)
- `set_frequency(value: int)`: set the frequency of the trigger to the given value
- `set_target(target: int)`: set the frame target of the trigger to the given value

# Live_Data

The live_data image previewer is also available through the sequencer. It is important to remember that the variables here apply only to the preview images seen, and not the saved data, which is always the full region and resolution. You could use this to define a specific zoom, increase the resolution, or automatically change the colour map; for example, if you know that during a sequence a certain area will become of interest, or you want to save some processing power with lower resolution images before a certain temperature.
When changing any detail with the live_data adapter, it requires an argument for which processor (which accepts the output from one camera) is being referred to. The processors aren’t named but are defined in order from the config – you can access these with `self.processors[x]` where x is (indexed from 0) the number in the list of processors.

| Attr Name | Description | 
| --------- | ----------- |
| processors | (list) processor objects that contain the information for image previewing. Aside from the parameter tree, this is the only class attribute |

### Processor Attributes

Processors store the actual information, but they are run in a Process. This means that they should be edited only through functions in the live_data class, though you can still access the previously-updated version of this information.

| attr name           | description |
|---------------------|-------------|
| endpoint           | (str) endpoint of image data source (config) |
| max_size_x         | (int) max image width in pixels |
| max_size_y         | (int) max image height in pixels |
| size_x             | (int) desired output image width in pixels |
| size_y             | (int) desired output image height in pixels |
| out_dimensions     | (list) list of size_x and size_y to represent dimensions in controller parameter tree |
| colour            | (str) representation of opencv colour map for output image |
| resolution_percent | (int) resolution of image expressed as a percentage |
| image             | Processed image pulled from queue |
| histogram         | Processed histogram image pulled from queue |
| cam_pixel_min     | (int) minimum pixel value of camera |
| cam_pixel_max     | (int) maximum pixel value of camera |
| zoom              | (dict) zoom specifications in px and % |
| clipping          | (dict) pixel clipping values in px and % |
| image_queue       | (Queue) queue object for sending images through process |
| hist_queue        | (Queue) queue object for sending histogram images through process |
| pipe_parent, pipe_child | Pipe object outputs |
| process           | (Process) process object that runs image processing logic |

### Methods (live_data adapter)
When a method has a Processor as the argument, get the processor you want to use from the processors attribute in the class. Processors are created in the order listed in the `livex.cfg` file (typically widefov, then narrowfov)

- `set_img_x/y(value: int, processor: Processor)`: Set the width/height of the image in pixels within an existing zoom. If you define more than the maximum width, it should just include the entire image.
- `set_img_dims(value: int[], processor: Processor)`: Sets both image dimensions, width and height (x and y). Value should take the shape `[x, y]`. This selection occurs within any existing defined zoom.
- `set_img_colour(value: str, processor: Processor)`: Set the colourmap based on the string provided. See the [opencv ‘COLORMAP’ pages for information](https://docs.opencv.org/4.x/d3/d50/group__imgproc__colormap.html) on the string – only the name is needed, not the `COLORMAP_` prefix.
- `set_img_clip_value(value: int[], processor: Processor)`: Set the image clipping range absolutely – limiting the range of output values on the graph, pulling any beyond the limit to that limit. Value should be an array like `[min, max]` as integers.
- `set_img_clip_percent(value: int[], processor: Processor)`: This sets the clipping range proportionally – if you have a range defined, this defines it within that range. So the value `[min,max]` represent percentages instead. Normally, this information is provided by the ClickableImage histogram underneath the previews.
- `set_resolution(value: int, processor: Processor)`: Sets the resolution of the image, as a percentage. So value should be within 0-100.
- `set_zoom_boundaries(value: [int[], int[]], processor: Processor)`: Set zoom boundaries for the image, zooming in on the specified area (as it will fill the full image space on the interface). This will work if you have one set already, allowing the ClickableImage UI to repeatedly click-and-drag to zoom on one area.
Value should look like this: `[[x_low, x_high], [y_low, y_high]]`. If you provide 0 as both lows and 100 as both highs the zoom is set to full image size, as an override to allow resetting within one function.

# Motors (Kinesis)

The motors are also available in the sequencer through the 'kinesis' name.
From there you're able to access each of the motor controllers and their stages, which have a range of functions relating to positions and speed.
The kinesis controller has a `controllers` attribute which contains a dictionary of motor controllers (key=name (as per `devices.json`): value=motor controller), each of which has a `stages` attribute with the same structure which manages the stages.
At present, the controllers and stages are one-to-one, which does simplify the structure, but referencing by name is easier. Naming your controllers and stages sensibly can help a lot with making writing a sequence feel natural.

Generally, whenever you need to adjust a position you will do it for a particular stage, which should be done through the stage objects (the children of the motor controllers).  

**Controllers manage the connection, stages manage the movement.**

If you want to look at the codebase for the motor controllers, look here: https://github.com/stfc-aeg/odin-kinesis

### adapter attributes

| attr name           | description |
|---------------------|-------------|
| controllers        | (dict) store of controller objects referenced by name |
| bg_tasks_enable    | (bool) handles wether background tasks (sending messages, getting positions) are running |
| bg_await_reply_interval | (float) period of task that checks/sends via serial message queues |
| bg_check_position_interval | (float) period of task that requests motor positions


### Motor controller attributes and functions

Motor controllers are built on a `SerialController` class. The functions within it are available but are used exclusively by other functions in the actual controller classes for communication, they should not need to be used at all and so are not listed here.

Controllers have stages as objects within them which contain the stage details, such as jog settings, current position, etc..  
For the KDC101 controllers, which are the only controllers used in AIXI, there is only one stage so this does not need to be considered except when reading values back. For setting values, use the given functions.

## Motor Stage Attributes

Stage attributes for the KDC101 controller are accessed like so from the kinesis context:
- `.controllers[controller_name].stages[stage_name][attribute]`
- It may be preferable to assign these to their own variable e.g. `stage_upperheater = kinesis.controllers['furnace_upper'].stages['upper_heater']` then `stage_upperheater['current_position']

| attr name             | description |
| --------------------- | ----------- |
| name              | (str) name of stage |
| chan_ident  | (int) number used to identify stages for commands |
| stage_type | (str) type of stage as listed in `devices.json` |
| upper/lower_limit | (float) software positional limit of stage |
| destination | (int) communications protocol value for sent messages |
| current_position | (float) reading of current position |
| target_position | (float) postition to move to (when set via set_target) |
| moving | (bool) is motor moving |
| homing | (bool) is motor homing |
| current_command | (str) current non-instant command (e.g. move_jog) |
| expected_response | (str) response expected from current command |
| jog_mode | (int) 0x01 continuous or 0x02 step |
| jog_step_size | (float) size of each step in mm |
| jog_min_vel | (float) minimum velocity of stage in mm/s. must be 0 |
| jog_accel | (float) acceleration speed of stage in mm/s^2. cannot be 0 |
| jog_max_vel | (float) maximum velocity of stage in mm/s. cannot be 0 |
| reverse_jog | (bool) is jog direction reversed. set through config |
| await_queue | (Queue) queue of non-instant commands |
| instant_queue | (PriorityQueue) queue of instant commands with special priority for 'stop' |

### Controller Methods
Methods available to the KDC101 Controller class.
- `move_home(val: any)`: val is unused. Homes the stage
- `move_stop(val: any)`: val is unused. Sends a stop command to the stage
- `move(position: float)`: move to the target position.
- `move_jog(direction: bool)`: True is forward, False is backward. This is called by `jog()`, which also handles the reverse logic, so use `jog()` for this movement.
- `get_current_position()`: Requests the position of this stage from the controller. Done by a background task in the adapter for all stages periodically
- `get_jogparams()`: sets the jog params to the queue to be updated in the response
- `set_jogparams()`: sets the jog params based on the current stage attributes
- `set_target_position(pos: float)`: sets the target position to the given value, and moves the motor if that position is different to current and within the limits
- `stop()`: calls move_stop()
- `jog(direction: bool)`: jogs forward (True) or backward (False). Handles reverse direction and respects stage limits
- `set_jog_mode(value: int)`: set the jog mode to continuous (0x01) or step (0x02), defaulting to 2 if value is out of that range. Then calls `set_jogparams()`
- `set_jog_step_size(value: float)`: sets the jog step size and calls `set_jogparams()`
- `set_jog_min_vel(value: float)`: sets the jog minimum velocity and calls `set_jogparams()`
- `set_jog_accel(value: float)`: sets the jog acceleration and calls `set_jogparams()`
- `set_jog_max_vel(value: float)`: sets the jog maximum velocity and calls `set_jogparams()`
- `set_jog_stop_mode(value: int)`: sets the stop mode to immediate (0x01) or continuous/profiled (0x02) and calls `set_jogparams()`. Is value is not 0x01 or 0x02, it is set to 0x02.


# Metadata

The metadata adapter stores all of the metadata that is written in hdf5 to the furnace file, and to the markdown file as well.
It is available as a sequencer context, but by itself does not have any especially useful functions aside from the usual get/set functions available with the ParameterTree ODIN controls. However, its availability here does give you easy access to the metadata variables via `metadata.metadata[key][‘value’]`, which could be useful.
You can see and edit the metadata structure, independently of the sequencer, in `test/config/metadata.json`. As the values are stored, you can edit these here prior to a session to override them in advance.
