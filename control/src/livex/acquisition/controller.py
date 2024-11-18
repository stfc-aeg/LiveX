import logging
from datetime import datetime

from functools import partial

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin.adapters.adapter import ApiAdapterRequest, ApiAdapterResponse
from odin._version import get_versions

from livex.base_controller import BaseController
from livex.modbusAddresses import modAddr
from livex.util import (
    LiveXError,
    write_coil,
    write_modbus_float
)

class LiveXController(BaseController):
    """LiveXController - class that manages the other adapters for LiveX."""

    def __init__(self,  options):
        """Initialise the LiveXController object.

        This constructor initialises the LiveXController, building the parameter tree and getting
        system info.
        """

        # Parse options
        self.ref_trigger = options.get('reference_trigger', 'furnace')
        self.filepath = options.get('filepath', '/tmp')

        self.acq_frame_target = 1000
        self.acq_time = 1  # Time in seconds

        self.acquiring = False

        # Requires trigger adapter, so is to be built later
        self.frequency_subtree = {}
        self.frequencies = {}

        self.furnace_freq = None
        self.widefov_freq = None
        self.narrowfov_freq = None

        # These can be configured but a sensible default should be determined
        self.filename = "tmpy"
        self.dataset_name = "tmp"

        self._build_tree()

    def initialize(self, adapters):
        """Initialize the controller.

        This method initializes the controller with information about the adapters loaded into the
        running application.

        :param adapters: dictionary of adapter instances
        """
        self.adapters = adapters

        self.munir = adapters["munir"]
        self.furnace = adapters["furnace"].controller
        self.trigger = adapters["trigger"].controller
        self.orca = adapters["camera"].camera
        self.metadata = adapters["metadata"]  # This is likely easier with IAC

        self.munir = adapters["munir"].controller

        if 'sequencer' in self.adapters:
            logging.debug("Livex controller registering context with sequencer")
            self.adapters['sequencer'].add_context('livex', self)

        # With adapters initialised, IAC can be used to get any more needed info
        self.get_timer_frequencies()

        # Write furnace timer to go for readings
        self.trigger.triggers['furnace'].set_frequency(10)
        self.trigger.triggers['furnace'].set_enable(True)

        # Reconstruct tree with relevant adapter references
        self._build_tree()

    def cleanup(self):
        """Clean up the controller.

        This method cleans up the state of the controller at shutdown, closing the persistent
        metadata store if open.
        """
        pass

    def get(self, path, with_metadata=False):
        """Get parameter data from controller.

        This method gets data from the controller parameter tree.

        :param path: path to retrieve from the tree
        :param with_metadata: flag indicating if parameter metadata should be included
        :return: dictionary of parameters (and optional metadata) for specified path
        """
        try:
            return self.param_tree.get(path, with_metadata)
        except ParameterTreeError as error:
            logging.error(error)
            raise LiveXError(error)

    def set(self, path, data):
        """Set parameters in the controller.

        This method sets parameters in the controller parameter tree. If the parameters to write
        metadata to HDF and/or markdown have been set during the call, the appropriate write
        action is executed.

        :param path: path to set parameters at
        :param data: dictionary of parameters to set
        """
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as error:
            logging.error(error)
            raise LiveXError(error)
        
    def _build_tree(self):
        """Construct the parameter tree once adapters have been initialised."""
        self.param_tree = ParameterTree({
            'acquisition': {
                'acquiring': (lambda: self.acquiring, None),
                'start': (lambda: None, self.start_acquisition),
                'stop': (lambda: None, self.stop_acquisition),
                'time': (lambda: self.acq_time, self.set_acq_time),
                'frame_target': (lambda: self.acq_frame_target, self.set_acq_frame_target),
                'reference_trigger': (lambda: self.ref_trigger, None),
                'frequencies': self.frequency_subtree
            }
        })

    def start_acquisition(self, freerun=False):
        """Start an acquisition. Disable timers, configure all values, then start timers simultaneously.
        :param freerun: bool deciding if frame target is overridden to 0 for indefinite capture
        """
        self.acquiring = True

        # experiment id is the campaign name plus an incrementing suffix (the acquisition_number)
        campaign_name = self.iac_get(self.metadata, 'fields/campaign_name/value', param='value')
        # Spaces in filenames do not play nice with Linux
        campaign_name = campaign_name.replace(" ", "_")

        acquisition_number = self.iac_get(self.metadata, 'fields/acquisition_num/value', param='value')
        acquisition_number += 1
        experiment_id = campaign_name + "_" + str(acquisition_number).rjust(4, '0')

        furnace_file = experiment_id + "_furnace.hdf5"
        markdown_file = experiment_id + "_furnace.md"
        markdown_filepath = self.filepath + "/logs/acquisitions"

        self.iac_set(self.metadata, 'fields/acquisition_num', 'value', acquisition_number)
        self.iac_set(self.metadata, 'fields/experiment_id', 'value', experiment_id)
        self.iac_set(self.metadata, 'hdf', 'file', furnace_file)
        self.iac_set(self.metadata, 'hdf', 'path', self.filepath)
        self.iac_set(self.metadata, 'markdown', 'file', markdown_file)
        self.iac_set(self.metadata, 'markdown', 'path', markdown_filepath)

        # Set file name and path for furnace
        self.furnace.set_filepath(self.filepath)
        self.furnace.set_filename(self.filename)

        # End any current timers
        self.trigger.set_all_timers(False)

        # Set targets to 0 for freerun
        if freerun:
            for name in self.trigger.triggers.keys():
                self.trigger.triggers[name].set_target(0)

        # Move camera(s) to 'connected' state
        for name, camera in self.orca.cameras.items():
            # Move camera(s) to connected state
            if camera.status['camera_status'] == 'disconnected':
                camera.send_command('connect')
            elif camera.status['camera_status'] == 'capturing':
                camera.send_command('end_capture')

            # Set cameras to trigger source 2 (external)
            camera.set_config(value=2, param='trigger_source')
            # Set orca frames to prevent HDF error
            # No. frames is equal to target set in trigger by user (or 0 if freerun)
            target = int(self.trigger.triggers[camera].target)
            camera.set_config(value=target, param='num_frames')

            # Format same filename as metadata, but with camera name instead of 'metadata'
            filename = experiment_id + "_" + camera

            # Munir arguments for subsystem
            self.munir.munir_managers[name].set_arg(arg='file_path', value=self.filepath)
            self.munir.munir_managers[name].set_arg(arg='file_name', value=filename)
            self.munir.munir_managers[name].set_arg(arg='num_frames', value=target)

            # Presently, '/' is required for execute
            self.munir.set_execute(subsystem_name=name, value=True)

        # Move camera(s) to capture state
        for name, camera in self.orca.cameras.items():
            camera.send_command('capture')

        # Enable furnace acquisition coil
        self.furnace.set_acquisition(True)

        # Set temperature profile metadata
        self.iac_set(self.metadata, 'fields/thermal_gradient_kmm', 'value', self.furnace.controller.gradient.wanted)
        self.iac_set(self.metadata, 'fields/thermal_gradient_distance', 'value', self.furnace.controller.gradient.distance),
        self.iac_set(self.metadata, 'fields/cooling_rate', 'value', self.furnace.controller.aspc.rate)

        # Start time
        now = datetime.now()
        start_time = now.strftime("%d/%m/%Y, %H:%M:%S")
        self.iac_set(self.metadata, 'fields/start_time', 'value', start_time)

        # Write out markdown metadata - done first so it is available during acquisition
        self.iac_set(self.metadata, 'markdown', 'write', True)

        # Enable timer coils simultaneously
        self.trigger.set_all_timers(True)

    def stop_acquisition(self, value):
        """Stop the acquisition."""
        self.acquiring = False

        # All timers can be explicitly disabled (even though they should turn themselves off).
        self.trigger.set_all_timers(False)

        # cams stop capturing, num-frames to 0, start again
        # Move camera(s) to capture state
        for name, camera in self.orca.cameras.items():
            if camera.status['camera_status'] == 'capturing':
                camera.send_command('end_capture')

            # Set target to 0 (endless run), stop acquisition, start capturing 
            camera.set_config(value=0, param='num_frames')
            self.munir.munir_managers[name].stop_acquisition()
            camera.send_command('capture')

        # Set targets to 0 so timers keep running after acquisition, for monitoring
        targets = {}
        for name, trigger in self.trigger.triggers.items():
            targets[name] = trigger.target
            trigger.set_target(0)

        # Turn off acquisition coil
        self.furnace.set_acquisition(False)

        # Stop time
        now = datetime.now()
        stop_time = now.strftime("%d/%m/%Y, %H:%M:%S")
        self.iac_set(self.metadata, 'fields/stop_time', 'value', stop_time)

        # Write metadata hdf to file afterwards, only md needs doing first
        self.iac_set(self.metadata, 'hdf', 'write', True)

        # Reenable timers
        self.trigger.set_all_timers(True)

        # Put targets back to how they were to preserve previous settings and their display
        for name, trigger in self.trigger.triggers.items():
            trigger.set_target(targets[name])

    def get_timer_frequencies(self):
        """Update the timer frequency variables."""
        for name, trigger in self.trigger.triggers.items():
            self.frequencies[name] = trigger.frequency

            self.frequency_subtree[name] = (
                lambda trigger=trigger: trigger.frequency,
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

            # Ensure furnace frequency is updated
            self.update_furnace_frequency(self.frequencies[self.ref_trigger])

            # We can recalculate duration and frame targets for the new frequency by calling this
            # function with the current ref target, instead of duplicating code.
            ref_target = self.trigger.triggers[self.ref_trigger].target
            self.set_acq_frame_target(ref_target)

    def update_furnace_frequency(self, frequency):
        """Useful function to inform the furnace PLC of its trigger frequency.
        This helps with SampleTime and the Auto Set Point Control.
        """
        logging.debug(f"Writing freq {frequency} to register {modAddr.furnace_freq_hold}")
        write_modbus_float(self.furnace.mod_client, frequency, modAddr.furnace_freq_hold)
        logging.debug(f"Writing {True} to coil {modAddr.freq_aspc_update_coil}")
        write_coil(self.furnace.mod_client, modAddr.freq_aspc_update_coil, True)  

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
