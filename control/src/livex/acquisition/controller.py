import logging
from datetime import datetime

from functools import partial

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from livex.base_controller import BaseController
from livex.modbusAddresses import modAddr
from livex.util import (
    LiveXError,
    write_coil,
    write_modbus_float,
    iac_get,
    iac_set
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
        # Which 'devices' are doing this acquisition. Set in start_acquisition
        self.current_acquisition = []

        # Requires trigger adapter, so is to be built later
        self.frequency_subtree = {}
        self.frequencies = {}

        self.freerun = False

        # Furnace is a given as an adapter
        self.filepaths = {
            'furnace': {
                'filename': None,
                'filepath': None
            },
            'metadata': {
                'hdf5': {
                    'filename': None,
                    'filepath': None
                },
                'md': {
                    'filename': None,
                    'filepath': self.filepath
                }
            }
        }

        self._build_tree()

    def initialize(self, adapters):
        """Initialize the controller.

        This method initializes the controller with information about the adapters loaded into the
        running application.

        :param adapters: dictionary of adapter instances
        """
        self.adapters = adapters

        # These adapters are all necessary so warn if they are not found
        if 'munir' in self.adapters:
            self.munir = adapters["munir"].controller
            self.munir_adapter = adapters["munir"]
        else:
            logging.warning("Munir adapter not found.")

        self.furnace = adapters["furnace"].controller if 'furnace' in self.adapters else logging.warning("Furnace adapter not found.")
        self.trigger = adapters["trigger"].controller if 'trigger' in self.adapters else logging.warning("Trigger adapter not found.")
        self.orca = adapters["camera"].camera if 'camera' in self.adapters else logging.warning("Camera adapter not found")
        self.metadata = adapters["metadata"] if 'metadata' in self.adapters else logging.warning("Metadata adapter not found.")
        # Metadata adapter is likely easier with IAC

        if 'sequencer' in self.adapters:
            logging.debug("Livex controller registering context with sequencer")
            self.adapters['sequencer'].add_context('livex', self)

        # With adapters initialised, IAC can be used to get any more needed info
        self._get_timer_frequencies()

        # Write furnace timer to go for readings
        self.trigger.triggers['furnace'].set_frequency(10)
        self.trigger.triggers['furnace'].set_enable(True)

        # Add cameras to self.filepaths for acquisition handling
        for camera in self.orca.cameras:
            self.filepaths[camera.name] = {'filename': None, 'filepath': self.filepath}

        # Reconstruct tree with relevant adapter references
        self._build_tree()

    def _build_tree(self):
        """Construct the parameter tree once adapters have been initialised."""
        self.param_tree = ParameterTree({
            'acquisition': {
                'acquiring': (lambda: self.acquiring, None),
                'start': (lambda: None, self.start_acquisition),
                'stop': (lambda: None, self.stop_acquisition),
                'time': (lambda: self.acq_time, self.set_acq_time),
                'frame_target': (lambda: self.acq_frame_target, self.set_acq_frame_target),
                'freerun': (lambda: self.freerun, self.set_freerun),
                'reference_trigger': (lambda: self.ref_trigger, None),
                'frequencies': self.frequency_subtree
            }
        })

    def _generate_experiment_filenames(self):
        """Generate the file names and paths for an acquisition.
        """
        # Experiment id is campaign name plus incrementing acquisition number value
        campaign_name = iac_get(self.metadata, 'fields/campaign_name/value', param='value')
        campaign_name = campaign_name.replace(" ", "_")

        acquisition_number = iac_get(self.metadata, 'fields/acquisition_num/value', param='value')
        acquisition_number += 1

        experiment_id = campaign_name + "_" + str(acquisition_number).rjust(4, '0')

        # Most files should have the same structure and location
        for key in self.filepaths.keys():
            # Special handling for metadata
            self.filepaths[key]['filename'] = experiment_id + "_" + key + ".hdf5"
            self.filepaths[key]['filepath'] = self.filepath

        # metadata hdf5 writes to same file as furnace
        self.filepaths['metadata']['hdf5']['filename'] = self.filepaths['furnace']['filename']
        self.filepaths['metadata']['hdf5']['filepath'] = self.filepaths['furnace']['filepath']
        # metadata markdown goes to unique logs/acquisitions location
        self.filepaths['metadata']['md']['filename'] = experiment_id + "_" + "furnace.md"
        self.filepaths['metadata']['md']['filepath'] = self.filepath + "/logs/acquisitions"

        # Set values in metadata adapter
        iac_set(self.metadata, 'fields/acquisition_num', 'value', acquisition_number)
        iac_set(self.metadata, 'fields/experiment_id', 'value', experiment_id)
        iac_set(self.metadata, 'hdf', 'file', self.filepaths['metadata']['hdf5']['filename'])
        iac_set(self.metadata, 'hdf', 'path', self.filepaths['metadata']['hdf5']['filepath'])
        iac_set(self.metadata, 'markdown', 'file', self.filepaths['metadata']['md']['filename'])
        iac_set(self.metadata, 'markdown', 'path', self.filepaths['metadata']['md']['filepath'])

        for camera in self.orca.cameras:
            self.filepaths[camera.name]['filename'] = f"{experiment_id}_{camera.name}"  # no .hdf5 extension needed here

    def start_acquisition(self, acquisitions=[]):
        """Start an acquisition. Disable timers, configure all values, then start timers simultaneously.
        :param freerun: bool deciding if frame target is overridden to 0 for indefinite capture
        :param acquisitions: (dict) {name: bool} to determine which acquisitions are to be run
        """
        self.acquiring = True
        self.current_acquisition = acquisitions

        # Get self.filepaths set to
        self._generate_experiment_filenames()

        # Stop all timers while processing
        self.trigger.set_all_timers(
            {'enable': False,
             'freerun': self.freerun}
        )
        # Set targets to 0 for freerun
        if self.freerun:
            for name in self.trigger.triggers.keys():
                self.trigger.triggers[name].set_target(0)

        # Check which acquisitions are being run and call the relevant function
        if 'furnace' in self.current_acquisition:
            self.furnace._set_filepath(
                self.filepaths['furnace']['filepath']
            )
            self.furnace._set_filename(
                self.filepaths['furnace']['filename']
            )
            self.furnace._start_acquisition()

        for camera in self.orca.cameras:
            if camera.name in self.current_acquisition:
                # Move camera to connected state
                if camera.status['camera_status'] == 'disconnected':
                    camera.send_command('connect')
                elif camera.status['camera_status'] == 'capturing':
                    camera.send_command('end_capture')

                # Set cameras to trigger source 2 (external)
                camera.set_config(value=2, param='trigger_source')
                # Set orca frames to prevent HDF error
                # No. frames is equal to target set in trigger by user (or 0 if freerun)
                target = int(self.trigger.triggers[camera.name].target)
                camera.set_config(value=target, param='num_frames')

                # Munir arguments for subsystem
                munir_args = {
                    'file_path': self.filepaths[camera.name]['filepath'],
                    'file_name': self.filepaths[camera.name]['filename'],
                    'num_frames': target
                }
                iac_set(self.munir_adapter, f'subsystems/{camera.name}/', 'args', munir_args)
                iac_set(self.munir_adapter, 'execute', camera.name, True)

        # Move camera(s) to capture state
        for camera in self.orca.cameras:
            if camera.name in self.current_acquisition:
                camera.send_command('capture')

        # Set temperature profile metadata
        iac_set(self.metadata, 'fields/thermal_gradient_kmm', 'value', self.furnace.gradient.wanted)
        iac_set(self.metadata, 'fields/thermal_gradient_distance', 'value', self.furnace.gradient.distance),
        iac_set(self.metadata, 'fields/cooling_rate', 'value', self.furnace.aspc.rate)

        # Start time
        now = datetime.now()
        start_time = now.strftime("%d/%m/%Y, %H:%M:%S")
        iac_set(self.metadata, 'fields/start_time', 'value', start_time)

        # Write out markdown metadata - done first so it is available during acquisition
        iac_set(self.metadata, 'markdown', 'write', True)

        # Enable timer coils simultaneously
        self.trigger.set_all_timers(
            {'enable': True,
             'freerun': self.freerun}
        )

    def stop_acquisition(self, value=None):
        """Stop the acquisition."""
        self.acquiring = False

        # All timers explicitly disabled (even if they have and reach a target)
        self.trigger.set_all_timers(
            {'enable': False,
             'freerun': self.freerun}
        )

        # Furnace
        if 'furnace' in self.current_acquisition:
            # Turn off acquisition coil
            self.furnace._stop_acquisition()

        # Cams stop capturing, num-frames to 0, start again
        # Move camera(s) to capture state
        for camera in self.orca.cameras:
            if camera.name in self.current_acquisition:

                if camera.status['camera_status'] == 'capturing':
                    camera.send_command('end_capture')

                # Set target to 0 (endless run), stop acquisition, start capturing 
                camera.set_config(value=0, param='num_frames')
                self.munir.munir_managers[camera.name].stop_acquisition()
                camera.send_command('capture')

        # Post-acquisition, targets are 0 for monitoring
        # Previous targets are lost as updating target restarts timer
        targets = {}
        for name, trigger in self.trigger.triggers.items():
            targets[name] = trigger.target
            trigger.set_target(0)

        # Stop time
        now = datetime.now()
        stop_time = now.strftime("%d/%m/%Y, %H:%M:%S")
        iac_set(self.metadata, 'fields/stop_time', 'value', stop_time)

        # Write metadata hdf to file afterwards, only md needs doing first
        iac_set(self.metadata, 'hdf', 'write', True)

        # Reenable timers
        self.trigger.set_all_timers(
            {'enable': True,
             'freerun': self.freerun}
        )

    def _get_timer_frequencies(self):
        """Update the timer frequency variables."""
        for name, trigger in self.trigger.triggers.items():
            self.frequencies[name] = trigger.frequency

            self.frequency_subtree[name] = (
                lambda trigger=trigger: trigger.frequency,
                partial(self.set_timer_frequency, timer=name)
            )

    def set_freerun(self, value):
        """Set the freerun boolean. If True, frame targets are ignored when running an acquisition.
        :param value: bool, determines if freerun is True or False.
        """
        self.freerun = bool(value)

    def set_timer_frequency(self, value, timer=None):
        """Set a given timer's frequency to the provided value.
        :param value: integer represening the new time
        :param timer: string representing the trigger parameter tree path of the timer to edit
        """
        if timer and timer in self.trigger.triggers.keys():
            self.trigger.triggers[timer].set_frequency(int(value))
            self.frequencies[timer] = int(value)
            logging.debug(f"self.frequencies: {self.frequencies}")

            # Ensure furnace frequency is updated
            self.furnace.update_furnace_frequency(self.frequencies[self.ref_trigger])

            # We can recalculate duration and frame targets for the new frequency by calling this
            # function with the current ref target, instead of duplicating code.
            ref_target = self.trigger.triggers[self.ref_trigger].target
            self.set_acq_frame_target(ref_target)
        else:
            logging.debug("Timer not updated; not found or timer not in list of triggers.")

    def set_acq_time(self, value):
        """Set the duration of the acquisition. Used to calculate targets from frequencies."""
        self.acq_time = int(value)
        self._get_timer_frequencies()

        # Frame target = time (in s) * frequency
        for name, trigger in self.trigger.triggers.items():
            trigger.set_target(
                self.acq_time * self.frequencies[name]
            )

    def set_acq_frame_target(self, value):
        """Set the frame target(s) of the acquisition."""
        # Furnace is the 'source of truth' for frame targets. Others are derived from it
        self._get_timer_frequencies()

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
