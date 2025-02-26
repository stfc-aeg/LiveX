provides = ['set_uniform_trigger_details', 'read_metadata_values']

def set_uniform_trigger_details(frequency=50, target=10000):
    """Example script sets all timers to the same frequency."""
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