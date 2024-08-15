import logging
import time
import datetime

from functools import partial

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin.adapters.adapter import ApiAdapterRequest, ApiAdapterResponse
from odin._version import get_versions

from livex.util import LiveXError

class LiveXController():
    """LiveXController - class that manages the other adapters for LiveX."""

    def __init__(self, ref_trigger):
        """Initialise the LiveXController object.

        This constructor initialises the LiveXController, building the parameter tree and getting
        system info.
        """
        self.acq_frame_target = 1000
        self.acq_time = 1  # Time in seconds

        # Requires trigger adapter, so is to be built later
        self.frequency_subtree = {}
        self.frequencies = {}
        self.ref_trigger = ref_trigger

        self.furnace_freq = None
        self.widefov_freq = None
        self.narrowfov_freq = None

        # These can be configured but a sensible default should be determined
        self.filepath = "/tmp"
        self.filename = "tmpy"
        self.dataset_name = "tmp"

        # Store initialisation time
        self.init_time = time.time()

        # Get package version information
        self.version_info = get_versions()

        self._build_tree()

    def _build_tree(self):
        """Construct the parameter tree once adapters have been initialised."""
        self.param_tree = ParameterTree({
            'odin_version': self.version_info['version'],
            'server_uptime': (lambda: self.get_server_uptime(), None),
            'acquisition': {
                'start': (lambda: None, self.start_acquisition),
                'stop': (lambda: None, self.stop_acquisition),
                'time': (lambda: self.acq_time, self.set_acq_time),
                'frame_target': (lambda: self.acq_frame_target, self.set_acq_frame_target),
                'frequencies': self.frequency_subtree
            }
        })

    def toggle_previews(self, value):
        """Starts or stops all timers and puts them in previewing mode."""
        previewing = self.iac_get(self.trigger, 'preview', param='preview')
        previewing = not previewing

        self.iac_set(self.trigger, '', 'all_timers_enable', previewing)
        self.iac_set(self.trigger, '', 'preview', previewing)

    def start_acquisition(self, value):
        """Start an acquisition. Disable timers, configure all values, then start timers simultaneously."""
        # experiment id is the campaign name plus an incrementing suffix (the acquisition_number)
        campaign_name = self.iac_get(self.metadata, 'fields/campaign_name/value', param='value')
        # Spaces in filenames do not play nice with Linux
        campaign_name = campaign_name.replace(" ", "_")

        acquisition_number = self.iac_get(self.metadata, 'fields/acquisition_num/value', param='value')
        acquisition_number += 1
        experiment_id = campaign_name + "_" + str(acquisition_number).rjust(4, '0')

        self.iac_set(self.metadata, 'fields/acquisition_num', 'value', acquisition_number)
        self.iac_set(self.metadata, 'fields/experiment_id', 'value', experiment_id)
        self.iac_set(self.metadata, 'hdf', 'file', str(experiment_id +"_metadata.hdf5"))

        # End any current timers
        self.iac_set(self.trigger, '', 'all_timers_enable', False)
        # Disable trigger 'preview' mode
        self.iac_set(self.trigger, '', 'preview', False)

        # Set filename for furnace
        self.iac_set(self.furnace, 'filewriter', 'filename', str(experiment_id+"_furnace.hdf5"))

        # Move camera(s) to 'connected' state
        for i in range(len(self.orca.camera.cameras)):
            camera = self.orca.camera.cameras[i].name

            if self.iac_get(self.orca, f'cameras/{camera}/status/camera_status', param='camera_status') == 'disconnected':
                self.iac_set(self.orca, f'cameras/{camera}', 'command', 'connect')
            elif self.iac_get(self.orca, f'cameras/{camera}/status/camera_status', param='camera_status') == 'capturing':
                self.iac_set(self.orca, f'cameras/{camera}', 'command', 'end_capture')

            # Set cameras explicitly to trigger source 2 (external)
            self.iac_set(self.orca, f'cameras/{camera}/config/', 'trigger_source', 2)
            # Set orca frames to prevent HDF error
            # No. frames is equal to the target set in the trigger by the user
            target = int(self.iac_get(self.trigger, f'triggers/{camera}/target', param='target'))
            self.iac_set(self.orca, f'triggers/cameras/{camera}/config/', 'num_frames', target)

            # Format the same filename as metadata, but with the system name instead of 'metadata'
            filename = experiment_id + "_" + camera

            # Provide arguments to munir
            self.iac_set(self.munir, f'subsystems/{camera}/args', 'file_path', self.filepath)
            self.iac_set(self.munir, f'subsystems/{camera}/args', 'file_name', filename)
            self.iac_set(self.munir, f'subsystems/{camera}/args', 'num_frames', target)

            # Presently, '/' is required for execute
            self.iac_set(self.munir, 'execute', f'{camera}', True)

        # Move camera(s) to capture state
        for i in range(len(self.orca.camera.cameras)):
            camera = self.orca.camera.cameras[i].name
            self.iac_set(self.orca, f'cameras/{camera}', 'command', 'capture')

         # Enable furnace acquisition coil
        self.iac_set(self.furnace, 'tcp', 'acquire', True)

        # Enable timer coils simultaneously
        self.iac_set(self.trigger, '', 'all_timers_enable', True)

    def stop_acquisition(self, value):
        """Stop the acquisition."""
        # All timers can be explicitly disabled (even though they should turn themselves off).
        self.iac_set(self.trigger, '', 'all_timers_enable', False)

        # cams stop capturing, num-frames to 0, start again
        # Move camera(s) to capture state
        for i in range(len(self.orca.camera.cameras)):
            camera = self.orca.camera.cameras[i].name
            if self.iac_get(self.orca, f'cameras/{camera}/status/camera_status', param='camera_status') == 'capturing':
                self.iac_set(self.orca, f'cameras/{camera}', 'command', 'end_capture')

            self.iac_set(self.orca, f'cameras/{camera}/config', 'num_frames', 0)

            self.iac_set(self.orca, f'cameras/{camera}', 'command', 'capture')

            # Explicitly stop acquisition
            self.iac_set(self.munir, f'subsystems/{camera}', 'stop_execute', True)

        # set frame num back to 0
        self.iac_set(self.trigger, 'triggers/furnace', 'target', 0)
        self.iac_set(self.trigger, 'triggers/widefov', 'target', 0)
        self.iac_set(self.trigger, 'triggers/narrowfov', 'target', 0)

        # Set trigger mode back to 'preview'
        self.iac_set(self.trigger, '', 'preview', True)

        # Turn off acquisition coil
        self.iac_set(self.furnace, 'tcp', 'acquire', False)

        # Write out metadata
        self.iac_set(self.metadata, 'hdf', 'write', True)
        self.iac_set(self.metadata, 'markdown', 'write', True)

        # Reenable timers
        self.iac_set(self.trigger, '', 'all_timers_enable', True)

    def get_timer_frequencies(self):
        """Update the timer frequency variables."""
        for name, trigger in self.trigger.triggers.items():
            self.frequencies[name] = trigger.frequency

            self.frequency_subtree[name] = (
                lambda: trigger.frequency,
                partial(self.set_timer_frequency, timer=name)
            )

    def set_timer_frequency(self, value, timer=None):
        """Set a given timer's frequency to the provided value.
        :param value: integer represening the new time
        :param timer: string representing the trigger parameter tree path of the timer to edit
        """
        if timer:
            self.trigger.triggers[timer].set_frequency(int(value))
            self.frequencies[timer] = int(value)
            logging.debug(f"self.frequencies: {self.frequencies}")

            # We can recalculate duration and frame targets for the new frequency by calling this
            # function with the current ref target, instead of duplicating code.
            ref_target = self.trigger.triggers[self.ref_trigger].target
            self.set_acq_frame_target(ref_target)

    def set_acq_time(self, value):
        """Set the duration of the acquisition. Used to calculate targets from frequencies."""
        self.acq_time = int(value)
        self.get_timer_frequencies()

        # Frame target = time (in s) * frequency
        for name, trigger in self.trigger.triggers.items():
            trigger.set_target(
                self.acq_time * self.frequencies[name]
            )

    def set_acq_frame_target(self, value):
        """Set the frame target(s) of the acquisition."""
        # Furnace is the 'source of truth' for frame targets. Others are derived from it
        self.get_timer_frequencies()

        # New furnace target as provided
        ref_target = int(value)

        self.trigger.triggers[self.ref_trigger].set_target(ref_target)

        # Get new 'real' acquisition time for calculations
        self.acq_time = ref_target / self.frequencies[self.ref_trigger]
        logging.debug(f"acq time = target//freq: {ref_target} / {self.frequencies[self.ref_trigger]} = {self.acq_time}")

        # Calculate targets based on that time
        for name, trigger in self.trigger.triggers.items():
            trigger.set_target(
                (self.acq_time * trigger.frequency)
            )

        self.acq_time = ref_target // self.frequencies[self.ref_trigger]  # Avoid showing long floats to users

    def initialise_adapters(self, adapters):
        """Get access to all of the other adapters.
        :param adapters: dict of adapters from adapter.py.
        """
        self.adapters = adapters
        self.munir = adapters["munir"]
        self.furnace = adapters["furnace"]
        self.trigger = adapters["trigger"].controller
        self.orca = adapters["camera"]
        self.metadata = adapters["metadata"]

        # With adapters initialised, IAC can be used to get any more needed info
        self.get_timer_frequencies()

        # Reconstruct tree with relevant adapter references
        self._build_tree()

    def get_server_uptime(self):
        """Get the uptime for the ODIN server.

        This method returns the current uptime for the ODIN server.
        """
        return time.time() - self.init_time

    def get(self, path):
        """Get the parameter tree.
        This method returns the parameter tree for use by clients via the FurnaceController adapter.
        :param path: path to retrieve from tree
        """
        return self.param_tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree.
        This method simply wraps underlying ParameterTree method so that an exceptions can be
        re-raised with an appropriate LiveXError.
        :param path: path of parameter tree to set values for
        :param data: dictionary of new data values to set in the parameter tree
        """
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise LiveXError(e)

    def iac_get(self, adapter, path, **kwargs):
        """Generic IAC get method for synchronous adapters."""
        request = ApiAdapterRequest(None, accept="application/json")
        response = adapter.get(path, request)
        if response.status_code != 200:
            logging.debug(f"IAC GET failed for adapter {adapter}, path {path}: {response.data}")
        return response.data.get(kwargs['param']) if 'param' in kwargs else response.data

    def iac_set(self, adapter, path, param, data):
        """Generic IAC set method for synchronous adapters."""
        request = ApiAdapterRequest({param: data}, content_type="application/vnd.odin-native")
        response = adapter.put(path, request)
        if response.status_code != 200:
            logging.debug(f"IAC SET failed for adapter {adapter}, path {path}: {response.data}")
