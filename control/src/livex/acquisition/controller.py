import logging
import time

from functools import partial

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin.adapters.adapter import ApiAdapterRequest, ApiAdapterResponse
from odin._version import get_versions

from livex.util import LiveXError

class LiveXController():
    """LiveXController - class that manages the other adapters for LiveX."""

    def __init__(self):
        """Initialise the LiveXController object.

        This constructor initialises the LiveXController, building the parameter tree and getting
        system info.
        """
        self.acq_frequency = 50
        self.acq_frame_target = 1000
        self.acq_time = 1  # Time in seconds

        # To be configured in
        self.furnace_freq = None
        self.widefov_freq = None
        self.narrowfov_freq = None

        # These can be configured but a sensible default should be determined
        self.filepath = "/data"
        self.filename = "tmpy"
        self.dataset_name = "tmp"

        # Store initialisation time
        self.init_time = time.time()

        # Get package version information
        version_info = get_versions()

        self.param_tree = ParameterTree({
            'odin_version': version_info['version'],
            'server_uptime': (lambda: self.get_server_uptime(), None),
            'acquisition': {
                'start': (lambda: None, self.start_acquisition),
                'stop': (lambda: None, self.stop_acquisition),
                'time': (lambda: self.acq_time, self.set_acq_time),
                'frame_target': (lambda: self.acq_time, self.set_acq_frame_target),
                'frequencies': {
                    'furnace': (lambda: self.furnace_freq, partial(self.set_timer_frequency, timer='furnace')),
                    'widefov': (lambda: self.widefov_freq, partial(self.set_timer_frequency, timer='widefov')),
                    'narrowfov': (lambda: self.widefov_freq, partial(self.set_timer_frequency, timer='narrowfov'))
                },
            }
        })

    def start_acquisition(self, value):
        """Start an acquisition. Disable timers, configure all values, then start timers simultaneously."""
        # End any current timers
        self.iac_set(self.trigger, '', 'all_timers_enable', False)

        # Disable trigger 'preview' mode
        self.iac_set(self.trigger, '', 'preview', False)

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
            target = self.iac_get(self.trigger, f'{camera}/target', param='target')
            self.iac_set(self.orca, f'cameras/{camera}/config/', 'num_frames', target)

        # Set odin-data config (frame count, filepath, filename, dataset name)
        self.iac_set(self.munir, 'args', 'file_path', self.filepath)
        self.iac_set(self.munir, 'args', 'file_name', self.filename)
        self.iac_set(self.munir, 'args', 'num_frames', self.acq_frame_target)

        self.iac_set(self.munir, '', 'execute', True)

        # TODO: Munir will reference the camera in its path so this will need adjusting

        # Move camera(s) to capture state
        for i in range(len(self.orca.camera.cameras)):
            camera = self.orca.camera.cameras[i].name
            self.iac_set(self.orca, f'cameras/{camera}', 'command', 'capture')

         # Enable furnace acquisition coil
        self.iac_set(self.furnace, 'tcp', 'acquire', True)

        # Enable timer coils simultaneously
        self.iac_set(self.trigger, '', 'all_timers_enable', True)

        # Await capture finish

    def stop_acquisition(self, value):
        """Stop the acquisition."""
        # All timers can be explicitly disabled (even though they should turn themselves off).
        self.iac_set(self.trigger, '', 'all_timers_enable', False)

        # Explicitly stop acquisition
        self.iac_set(self.munir, '', 'stop_execute', True)

        # cams stop capturing, num-frames to 0, start again
        # Move camera(s) to capture state
        for i in range(len(self.orca.camera.cameras)):
            camera = self.orca.camera.cameras[i].name
            if self.iac_get(self.orca, f'cameras/{camera}/status/camera_status', param='camera_status') == 'capturing':
                self.iac_set(self.orca, f'cameras/{camera}', 'command', 'end_capture')

            self.iac_set(self.orca, f'cameras/{camera}/config', 'num_frames', 0)

            self.iac_set(self.orca, f'cameras/{camera}', 'command', 'capture')

        # set frame num back to 0
        self.iac_set(self.trigger, 'furnace', 'target', 0)
        self.iac_set(self.trigger, 'widefov', 'target', 0)
        self.iac_set(self.trigger, 'narrowfov', 'target', 0)

        # Set trigger mode back to 'preview'
        self.iac_set(self.trigger, '', 'preview', True)

        # Turn off acquisition coil
        self.iac_set(self.furnace, 'tcp', 'acquire', False)

        # Reenable timers
        self.iac_set(self.trigger, '', 'all_timers_enable', True)

    def set_acq_frequency(self, value):
        """Set the acquisition frequency(ies)."""
        self.acq_frequency = value

    def get_timer_frequencies(self):
        """Update the timer frequency variables."""
        self.furnace_freq = int(self.iac_get(self.trigger, 'furnace/frequency', param='frequency'))
        self.widefov_freq = int(self.iac_get(self.trigger, 'widefov/frequency', param='frequency'))
        self.narrowfov_freq = int(self.iac_get(self.trigger, 'narrowfov/frequency', param='frequency'))

    def set_timer_frequency(self, value, timer=None):
        """Set a given timer's frequency to the provided value.
        :param value: integer represening the new time
        :param timer: string representing the trigger parameter tree path of the timer to edit
        """
        if timer:
            self.iac_set(self.trigger, timer, 'frequency', int(value))
            # We can recalculate duration and frame targets for the new frequency by calling this
            # function with the current furnace target, instead of duplicating code.
            furnace_target = self.iac_get(self.trigger, 'furnace/target', param='target')
            self.set_acq_frame_target(furnace_target)

    def set_acq_time(self, value):
        """Set the duration of the acquisition. Used to calculate targets from frequencies."""
        self.acq_time = int(value)
        self.get_timer_frequencies()

        # Frame target = time (in s) * frequency
        self.iac_set(self.trigger, 'furnace', 'target', (self.acq_time * self.furnace_freq))
        self.iac_set(self.trigger, 'widefov', 'target', (self.acq_time * self.widefov_freq))
        self.iac_set(self.trigger, 'narrowfov', 'target', (self.acq_time * self.narrowfov_freq))

    def set_acq_frame_target(self, value):
        """Set the frame target(s) of the acquisition."""
        # Furnace is the 'source of truth' for frame targets. Others are derived from it
        self.get_timer_frequencies()

        # New furnace target as provided
        furnace_target = int(value)
        self.iac_set(self.trigger, 'furnace', 'target', furnace_target)

        # Get new 'real' acquisition time for calculations
        self.acq_time = furnace_target / self.furnace_freq
        logging.debug(f"acq time = target//freq: {furnace_target} / {self.furnace_freq} = {self.acq_time}")

        # Calculate other targets based on that time
        self.iac_set(self.trigger, 'widefov', 'target', (self.acq_time * self.widefov_freq))
        self.iac_set(self.trigger, 'narrowfov', 'target', (self.acq_time * self.narrowfov_freq))

        self.acq_time = furnace_target // self.furnace_freq  # Avoid showing long floats to users

    def initialise_adapters(self, adapters):
        """Get access to all of the other adapters.
        :param adapters: dict of adapters from adapter.py.
        """
        self.adapters = adapters
        self.munir = adapters["munir"]
        self.furnace = adapters["furnace"]
        self.trigger = adapters["trigger"]
        self.orca = adapters["camera"]

        # With adapters initialised, IAC can be used to get any more needed info
        self.get_timer_frequencies()
        self.timer_frequencies = {
            "furnace": self.furnace_freq,
            "widefov": self.widefov_freq,
            "narrowfov": self.narrowfov_freq
        }

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
