import logging
import time
from concurrent import futures

from tornado.ioloop import PeriodicCallback
from tornado.concurrent import run_on_executor

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

        # These can be configured but a sensible default should be determined
        self.filepath = "/tmp"
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
                'frequency': (lambda: self.acq_frequency, self.set_acq_frequency)
            }
        })

    def start_acquisition(self, value):
        """Start an acquisition. Disable timers, configure all values, then start timers simultaneously."""
        # End any current timers
        logging.debug("disable all timers")
        self.iac_set(self.trigger, '', 'all_timers_enable', False)

        logging.debug("disable preview")
        # Disable trigger 'preview' mode
        self.iac_set(self.trigger, '', 'preview', False)

        logging.debug("cams to connected")
        # Move camera(s) to 'connected' state
        for i in range(len(self.orca.camera.cameras)):
            if self.iac_get(self.orca, f'cameras/{i}/status/camera_status', param='camera_status') == 'disconnected':
                self.iac_set(self.orca, f'cameras/{i}', 'command', 'connect')
            elif self.iac_get(self.orca, f'cameras/{i}/status/camera_status', param='camera_status') == 'capturing':
                self.iac_set(self.orca, f'cameras/{i}', 'command', 'end_capture')

        # Enable furnace acquisition coil
        self.iac_set(self.furnace, 'tcp', 'acquire', True)

        logging.debug("munir setting")
        # Set odin-data config (frame count, filepath, filename, dataset name)
        self.iac_set(self.munir, 'args', 'file_path', self.filepath)
        self.iac_set(self.munir, 'args', 'file_name', self.filename)
        self.iac_set(self.munir, 'args', 'num_frames', self.acq_frame_target)

        self.iac_set(self.munir, '', 'execute', True)

        # Set timers with *one* frequency and frame target
        #    # (in future, multiple frequencies means that frame count is scaled to other timers. based on camera freq?)
        logging.debug("trigger setting")
        self.iac_set(self.trigger, 'furnace', 'frequency', self.acq_frequency)
        self.iac_set(self.trigger, 'widefov', 'frequency', self.acq_frequency)
        self.iac_set(self.trigger, 'narrowfov', 'frequency', self.acq_frequency)

        self.iac_set(self.trigger, 'furnace', 'target', self.acq_frame_target)
        self.iac_set(self.trigger, 'widefov', 'target', self.acq_frame_target)
        self.iac_set(self.trigger, 'narrowfov', 'target', self.acq_frame_target)

        # Move camera(s) to capture state
        for i in range(len(self.orca.camera.cameras)):
            self.iac_set(self.orca, f'cameras/{i}', 'command', 'capture')

        logging.debug("enable all timer")
        # Enable timer coils simultaneously
        self.iac_set(self.trigger, '', 'all_timers_enable', True)

        # Await capture finish

    def stop_acquisition(self, value):
        """Stop the acquisition."""
        # All timers can be explicitly disabled (even though they should turn themselves off).
        self.iac_set(self.trigger, '', 'all_timers_enable', False)
        
        self.iac_set(self.munir, '', 'stop_execute', True)
        # # Set camera(s) to connected
        # for i in range(len(self.orca.camera.cameras)):
        #     if self.iac_get(self.orca, f'cameras/{i}/status/camera_status', param='camera_status') == 'disconnected':
        #         self.iac_set(self.orca, f'cameras/{i}', 'command', 'connect')
        #     elif self.iac_get(self.orca, f'cameras/{i}/status/camera_status', param='camera_status') == 'capturing':
        #         self.iac_set(self.orca, f'cameras/{i}', 'command', 'end_capture')

        # Edit camera properties (frametarget 0, explicitly set filewriting to false)
        # set frame num back to 0
        self.iac_set(self.trigger, 'furnace', 'target', 0)
        self.iac_set(self.trigger, 'widefov', 'target', 0)
        self.iac_set(self.trigger, 'narrowfov', 'target', 0)

        # Set trigger mode back to 'preview'
        self.iac_set(self.trigger, '', 'preview', True)

        # Turn off acquisition coil
        self.iac_set(self.furnace, 'tcp', 'acquire', False)

        # # Move camera(s) to capture state
        # for i in range(len(self.orca.camera.cameras)):
        #     self.iac_set(self.orca, f'cameras/{i}', 'command', 'capture')

        # Reenable timers
        self.iac_set(self.trigger, '', 'all_timers_enable', True)

    def set_acq_frequency(self, value):
        """Set the acquisition frequency."""
        self.acq_frequency = value

    def initialise_adapters(self, adapters):
        """Get access to all of the other adapters.
        :param adapters: dict of adapters from adapter.py.
        """
        self.adapters = adapters
        self.munir = adapters["munir"]
        self.furnace = adapters["furnace"]
        self.trigger = adapters["trigger"]
        self.orca = adapters["camera"]

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
