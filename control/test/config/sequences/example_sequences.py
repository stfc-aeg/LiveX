provides = ['set_uniform_trigger_details', 'read_metadata_values', 'stabilise_at_temperature_a', 'change_img_settings']

import time

def set_uniform_trigger_details(frequency=50, target=10000):
    """Example script to set all timers to the same frequency."""
    # Noted in the docs, livex context is best for this, but we still want access to the timers
    livex = get_context('livex')
    trigger = get_context('trigger')

    # Accessing the trigger class objects via the `triggers` value of the context controller class
    for name, trig in trigger.triggers.items():
        print(f"Setting timer {name} frequency")
        livex.set_timer_frequency(frequency, timer=name)
    livex.set_acq_frame_target(target)

def read_metadata_values(parameters=''):
    """Example script gives you the values of a given metadata option."""
    metadata = get_context('metadata')

    if parameters:
        params = [param.strip() for param in parameters.split(",")]
        for param in params:
            # Values are accessed from the 'metadata' dictionary of the metadata context above
            # The objects in there are MetadataFields (see `types.py` in the metadata folder)
            # so the values within are accessed by .value
            print(f"{param}: {metadata.metadata[param].value}")

def stabilise_at_temperature_a(setpoint=300, stability_threshold=0.25, do_gradient=False, gradient_temp_per_mm=2, distance=5, grad_high_towards_a=True):
    """Example sequence to set PID A to reach and maintain a target temperature."""
    furnace = get_context('furnace')
    trigger = get_context('trigger')

    furnace.pid_a.set_setpoint(setpoint)
    interval = furnace.bg_read_task_interval

    freq = trigger.triggers['furnace'].frequency
    duration = 10*freq

    if do_gradient:
        furnace.gradient.set_distance(distance)
        furnace.gradient.set_wanted(gradient_temp_per_mm)
        furnace.gradient.set_high(grad_high_towards_a)
        furnace.gradient.set_enable(do_gradient)

    furnace.pid_a.set_enable(True)

    def mean(errors):
        if len(errors) == 0:
            return -1
        return (sum(abs(err) for err in errors) / len(errors))
    # Need to determine that temperature is stable
    # Seeing that magnitude error of last 50 readings is below a certain amount should suffice
    # When testing, this is 10 seconds. Should be based off of frequency
    errors = []
    # Checking
    while (len(errors)<duration) or (mean(errors) >= stability_threshold):
        errors.append((furnace.pid_a.temperature - furnace.pid_a.setpoint))
        if len(errors) > duration:
            errors.pop(0)
        time.sleep(interval)

    print(f"temperature stabilised at {furnace.pid_a.temperature} for setpoint {furnace.pid_a.setpoint}")


def change_img_settings(camera_name="widefov", x_boundaries=[0,100], y_boundaries=[0,100], clip_percent_range=[0, 100], colour='AUTUMN'):
    """Example sequence to demonstrate interaction with the live_data adapter."""
    livedata = get_context('livedata')

    proc = None
    # Normally, livedata is accessed only via ParameterTree where processor is part of the argument
    # Can't do that here, so instead you need to identify which processor to target
    for processor in livedata.processors:
        if processor.name == camera_name:
            proc = processor

    livedata.set_roi_boundaries([x_boundaries, y_boundaries], processor=proc)
    livedata.set_img_colour(colour, processor=proc)
    livedata.set_img_clip_percent(clip_percent_range, processor=proc)
