# LiveX Sequencing

This document aims to cover all of the functions available to users of the sequencer for LiveX.
A function prefixed with ‘_’ is generally not one you will need to access, so not all of these are listed.

To use the sequencer, there are code examples and a README in the [odin-sequencer GitHub repository](https://github.com/stfc-aeg/odin-sequencer). Alternatively, there are some examples [in the LiveX repository](https://github.com/stfc-aeg/LiveX) too (see `/control/test/config/sequences`).

In short, you define functions in sequences files ( `control/test/config/sequences`). You then provide these functions in a list (`provides=['<name_of_function>']`) and these become visible in the user interface, with function arguments interpreted. Sequences can rely on other sequences; if those sequences are in another file, they can be used following `requires=['<name_of_file>']` (accessing all sequences in that file).

# Furnace

The furnace adapter mostly just controls the other furnace-related components (see Furnace Components below), but has a few essential functions of its own, mostly related to starting and stopping acquisitions.

| attr name                 | description |
|---------------------------|-------------|
| pid_a / pid_b            | PID class objects representing heater controls |
| gradient                 | Thermal gradient controls |
| aspc                     | Auto setpoint controls |
| log_directory            | Location of output file (edit through function) |
| log_filename             | Name of output file (edit through function) |
| ip                       | (str) ip address for modbus server |
| bg_read_task_enable      | (bool) is background reading task (getting PLC parameters) enabled |
| bg_read_task_interval    | (int) background task interval in seconds |
| bg_stream_task_enable    | (bool) is background streaming task (receive acquisition TCP data) enabled |
| pid_frequency           | (int) frequency PID is running at, used to derive the following: |
| buffer_size             | (int) size of data buffer, derived from frequency so that data is written once per second |
| bg_stream_task_interval | (int) interval for stream task so it never waits longer than the PID interval and stays up-to-date (set to half of pid_frequency) |
| file_writer             | (FileWriter) FileWriter class object |
| file_open_flag          | (bool) is file currently open/being written to |
| tcp_reading             | Data object representing last stream data received |
| packet_decoder          | (PacketDecoder) PacketDecoder object to process TCP data |
| stream_buffer           | (dict) object of decoded packets to be written to file |
| data_groupname          | (str) name of groupname in hdf5 file |
| acquiring              | (bool) is acquisition currently occurring |
| thermocouple_c         | (float) reading of third ‘central’ thermocouple |
| lifetime_counter       | (float) value of counter from PLC |
| mocking                | (bool) config, is mock client being used |
| mod_client             | ModbusClient which manages connection to PLC |
| mockClient             | Mock modbus client used if mocking is true. Used in background read task |

### solo_acquisition(bool: value)
Given a Boolean value (which is converted to bool immediately on calling the function), this starts (True) or stops (False) a ‘solo’ acquisition with the furnace. This means that only the furnace will record and save any data. 

### stop_all_pid(value=None)
This function has an unused argument. It sets both PIDs to false, disabling them. Usually used as an ‘emergency stop’.

### set_task_enable(bool: enable)
This function starts and stops the background tasks based on the truthiness of the argument you give it. Enable is converted to a bool immediately when the function is run. The background tasks handle the regular polling of information from the PLC, and the reception of streaming data during an acquisition. You generally want these enabled.

### set_task_interval(float: interval)
This function sets the interval of the polling task. The streaming tasks runs at the frequency defined by `pid_frequency` in the adapter.

### update_furnace_frequency(int: frequency)
Inform the furnace PLC of its trigger frequency, helping with accuracy of its PID logic and ensuring the auto setpoint control keeps to the correct rate. This also updates the size of the stream buffer and stream interval, to ensure 

### _start_acquisition()
This function signals the PLC to start the acquisition process, which sends data to the background task. Normally this is called by the livexadapter and not used otherwise, but you could use this with _set_filename/_set_filepath to work around the automatic filename generation.

### _stop_acquisition()
This function stops the acquisition, and also finishes writing any data in the buffer to the file. Normally this would be called by the livexadapter, so if you call _start_acquisition it would be consistent to call this instead of a different process. 

### _set_filename(str: value) / _set_filepath(str: value)
Given a String value, this function sets the filename/filepath for the furnace. In an acquisition (full or solo), this is set automatically and shouldn’t need to be called – running an acquisition will overwrite it, calling it during an acquisition could cause issues with the file writing.


# Furnace Components (PIDA/B, ASPC, Gradient, Motors)

There are four components, but as of February 2025 the motors are not used, pending future development. The components are accessed as part of the furnace sequencer context.
All of these functions contain a ‘register_modbus_client’ and ‘_get_parameters’ function, which are used in initialisation and are not useful for any sequencer activities.

### PID

These handle the PID behaviour for the adapters. You can access these via `furnace.pid_a` or `furnace.pid_b`, as there are two heaters. I recommend heater A being the physically-uppermost heater as this is how it’s labelled in the UI. 

| attr name   | description |
|------------|-------------|
| enable     | (bool) is heater enabled |
| setpoint   | (float) target temperature of heater |
| kp/ki/kd   | (float) value of proportional/integral/derivative terms |
| output     | (float) PID output value |
| outputSum  | (float) PID cumulative integral value |
| temperature | (float) actual temperature |


### set_setpoint/_proportional/_integral/_derivative(float: value)
All four of these functions set the relevant value in the PLC and keep that value internally.

### set_enable(bool: value)
Turn the PID on or off. Pass a Boolean value to turn off that particular heater.
 
### Auto SetPoint Control (ASPC)

This class handles the auto setpoint control behaviour. You can access it via `furnace.aspc` in the sequencer.

| attr name          | description |
|--------------------|-------------|
| enable            | (bool) is ASPC enabled |
| heating           | (bool) is ASPC heating (True) or cooling (False) |
| heating_options   | (list) reference to what heating options are for parameterTree |
| rate             | (float) rate of setpoint change (average per second) |
| midpt            | (float) midpoint temperature of heaters A and B (calculated from PLC) |

### set_enable(bool: value)
Turn the ASPC on (True) or off (False) via a boolean argument.

### set_heating(bool: value)
This determines if you are heating (True) or cooling (False). With heating, the ASPC increases the setpoint, otherwise it decreases it.

### set_rate(float: value)
Set the rate at which the ASPC will adjust the setpoint. The value you enter here is an average per second, the rate is calculated per-tick in the hardware, so with a frequency of 50Hz, a 1C/s ASPC will change by 0.02 per tick.

### Gradient

This class handles the thermal gradient behaviour. You can access it as `furnace.gradient` in the sequencer.

| attr name   | description |
|------------|-------------|
| enable     | (bool) is gradient enabled |
| wanted     | (float) desired temperature change per mm |
| distance   | (float) distance between heaters in mm |
| actual     | (float) actual temperature difference between heaters |
| theoretical | (float) theoretical temperature difference (wanted*distance) |
| high       | (bool) which heater does gradient increase towards (1: B, 0: A) |
| high_options | (list) textual representation of the high options |

### set_enable(bool: value)
Turn the gradient on (True) or off (False) via a Boolean argument.

### set_distance(float: value)
Set the ‘distance’ value, that being the distance in mm between the heaters.

### set_wanted(float: value)
Set the ‘wanted’ value, that being the desired temperature change per mm. A distance of 5 and wanted of 2 gives a 10C gradient.

### set_high(bool: value)
Set the direction of the gradient, or set the ‘high heater’, which determines which heater has its setpoint rise from the gradient. If True, the gradient is high towards heater B. If False, the gradient is high towards heater A.


# LiveX Adapter

This adapter is mostly responsible for handling the acquisition process, and other user-side-only details such as the estimated acquisition duration in seconds.

| attr name            | description |
|----------------------|-------------|
| ref_trigger         | (str) from config, name of reference trigger |
| filepath           | (str) from config, where are files saved |
| acq_frame_target   | (int) frame target for acquisition |
| acq_time           | (int) estimated duration of acquisition (calculated when target is set) |
| acquiring         | (bool) is an acquisition currently happening |
| current_acquisition | (dict) details of what is running in current acquisition e.g.: {‘furnace’: True} |
| freerun           | (bool) is frame target respected or overridden to zero (for endless acquisition) |
| filepaths         | (dict) store of filepaths and names for furnace, metadata, and cameras |
| munir/furnace/trigger/orca/metadata | References to other adapters |

### start_acquisition(dict: acquisitions)
This function starts an acquisition. It checks for values in the acquisition dictionary argument to determine which parts of the acquisition are to be run. The key is a string, the value is a Bool. Generally, this is going to be ‘furnace’ and ‘widefov’+’narrowfov’ (the camera names). This allows for files to be saved with consistent name formats and for acquisitions to include a variety of things.
Related, this function calls an internal function, `_generate_experiment_filenames`. This function uses the metadata adapter to create a filename, so be wary about overwriting files if you reset this information (particularly the acquisition_number).

### stop_acquisition(None: value)
This function has an unused optional argument. It stops the acquisitions based on the ones called in start_acquisition. It should only be called after start_acquisition to avoid unexpected results.

### set_freerun(bool: value)
Set the freerun attribute of the acquisition. If True, frame targets are ignored when running an acquisition, instead relying on a manual stop command.

### set_timer_frequency(int: value, str: timer) 
The timer values can also be set in the trigger adapter, but this function includes some additional logic about updating the frequency for the furnace (which is the ‘reference trigger’ as defined in the config) and recalculating frame targets and duration based on the frequency. When you update a timer, you pass the new frequency as value, and then specify which timer via a string, which should match one of the timers in the config for trigger.

### set_acq_frame_target(int: value)
This sets the frame target for the acquisition. This is the target for the ‘reference trigger’ as described in set_timer_frequency, which is the furnace for livex. Other targets will be based on this so that the durations match. i.e.: if the camera Hz is twice as high as the furnace, the frame target for that camera will be twice as high as the frame target given for the furnace.

# Trigger

The trigger adapter creates a trigger for each value provided to it in the ‘triggers’ option in its config file. The triggers have their own callable functions, accessed via `trigger.triggers[trigger_name]`.

| attr name                | description |
|--------------------------|-------------|
| ip                      | (str) ip address for modbus server |
| status_bg_task_enable   | (int) is background task enabled |
| status_bg_task_interval | (int) background task interval in seconds |
| triggers                | (dict) dictionary of Trigger objects based on names in config |


### set_ip(str: value)
Sets the ip attribute to the given string value. (e.g.: ‘127.0.0.1’). This would then be used in the `initialise_client` function if the reconnect parameter tree value is called.

### set_all_timers(dict: values)
Values is a dictionary in the structure: `{‘enable’: bool, ‘freerun’: bool}`.
This function enables (enable: True) or disables (enable: False) all timers, with the additional ‘freerun’ argument overwriting the trigger targets to 0 if set to true. With a target of 0, triggers run until stopped manually, otherwise going until the target is reached.

### Trigger (Class)

These are instantiated by the trigger adapter above, accessible via `trigger.triggers[trigger_name]`.

| attr name  | description |
|-----------|-------------|
| name      | (str) name of trigger |
| addr      | (dict) modbus addresses (see `modbusAddresses.py`) |
| enable    | (bool) set trigger enable |
| frequency | (int) frequency of trigger |
| target    | (int) frame target |
| running   | (bool) is trigger currently running (read from hardware). Enable is a single-fire flag on trigger hardware, this is a status report |
| client    | (ModbusTCPClient) modbus client object from trigger adapter |

### set_enable(bool: value)
Turn the trigger on (True) or off (False).

### set_frequency(int: value)
Sets the frequency of the trigger to the given value.

### set_target(int: target)
Sets the frame target of the trigger to the given value.

# Live_Data

The live_data image previewer is also available through the sequencer. It is important to remember that the variables here apply only to the preview images seen, and not the saved data, which is always the full region and resolution. You could use this to define a specific region of interest, increase the resolution, or automatically change the colour map; for example, if you know that during a sequence a certain area will become of interest, or you want to save some processing power with lower resolution images before a certain temperature.
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
| roi               | (dict) region of interest specifications in px and % |
| clipping          | (dict) pixel clipping values in px and % |
| image_queue       | (Queue) queue object for sending images through process |
| hist_queue        | (Queue) queue object for sending histogram images through process |
| pipe_parent, pipe_child | Pipe object outputs |
| process           | (Process) process object that runs image processing logic |

###  set_img_x/y(int: value, Processor: processor)
Set the width/height of the image in pixels within an existing region of interest (this can be the full image). If you define more than the maximum width, it should just include the entire image without causing further issue.

### set_img_dims(array, int: value, Processor: processor)
Sets both image dimensions, width and height (x and y). Value should look like `[x, y]`. This selection occurs within any existing defined region of interest.

### set_img_colour(str: value, Processor: processor)
 Set the colourmap based on the string provided. See the [opencv ‘COLORMAP’ pages for information](https://docs.opencv.org/4.x/d3/d50/group__imgproc__colormap.html) on the string – only the name is needed, not the `COLORMAP_` prefix.

### set_img_clip_value(array, int: value, Processor: processor)
Set the image clipping range absolutely – limiting the range of output values on the graph, pulling any beyond the limit to that limit. Value should be an array like `[min, max]` as integers.

### set_img_clip_percent(array, int: value, Processor: processor)
This sets the clipping range proportionally – if you have a range defined, this defines it within that range. So the value `[min,max]` represent percentages instead. Normally, this information is provided by the ClickableImage histogram underneath the previews.

### set_resolution(int: value, Processor: processor)
Sets the resolution of the image, as a percentage. So value should be within 0-100.

### set_roi_boundaries(array, array, int: value, Processor: processor)
Set region of interest boundaries for the image, effectively ‘zooming in’ on the specified area (as it will fill the full image space on the interface). This will work if you have one set already, allowing the ClickableImage UI to repeatedly click-and-drag to zoom on one area.
Value should look like this: `[[x_low, x_high], [y_low, y_high]]`. If you provide 0 as both lows and 100 as both highs the region of interest is set to full image size, as an override to allow resetting within one function.

# Metadata

The metadata adapter stores all of the metadata that is written in hdf5 to the furnace file, and to the markdown file as well.
It is available as a sequencer context, but by itself does not have any especially useful functions aside from the usual get/set functions available with the ParameterTree ODIN controls. However, its availability here does give you easy access to the metadata variables via `metadata.metadata[key][‘value’]`, which could be useful.
You can see and edit the metadata structure, independently of the sequencer, in `test/config/metadata.json`. As the values are stored, you can edit these here prior to a session to override them in advance.
