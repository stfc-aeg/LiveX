import logging
from datetime import datetime

from functools import partial

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from livex.base_controller import BaseController
from livex.util import (
    LiveXError,
    iac_get,
    iac_set
)
from livex.acquisition.trigger_manager import TriggerManager

class LiveXController(BaseController):
    """LiveXController - class that manages the other adapters for LiveX."""

    def __init__(self,  options):
        """Initialise the LiveXController object.

        This constructor initialises the LiveXController, building the parameter tree and getting
        system info.
        """
        self.options = options
        # Parse options
        self.ref_trigger = options.get('reference_trigger', 'furnace')
        # Filepaths can vary by system - i.e. cameras may have multiple storage locations
        self.furnace_filepath = options.get('furnace_filepath', '/tmp')
        self.widefov_filepath = options.get('widefov_filepath', '/tmp')
        self.narrowfov_filepath = options.get('narrowfov_filepath', '/tmp')

        self.acquiring = False
        # Which 'devices' are doing this acquisition. Set in start_acquisition
        self.current_acquisition = []

        self.exposure_lookup_path = options.get('exposure_lookup_filepath', 'test/config/cam_exposure_lookup.json')

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
                    'filepath': self.furnace_filepath
                }
            }
        }

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

        if 'trigger' in self.adapters:
            self.trigger = adapters["trigger"].controller
        else:
            logging.warning("Trigger adapter not found.")

        self.orca = adapters["camera"].camera if 'camera' in self.adapters else logging.warning("Camera adapter not found")
        self.metadata = adapters["metadata"] if 'metadata' in self.adapters else logging.warning("Metadata adapter not found.")
        # Metadata adapter is likely easier with IAC

        if 'sequencer' in self.adapters:
            logging.debug("Livex controller registering context with sequencer")
            self.adapters['sequencer'].add_context('livex', self)

        # With adapters initialised, IAC can be used to get any more needed info

        # Write furnace timer to go for readings
        self.trigger.triggers['furnace'].set_frequency(10)
        self.trigger.triggers['furnace'].set_enable(True)
        self.furnace.update_furnace_frequency(10)  # Inform furnace of frequency change, as this is done outside of usual channel

        self.trigger_manager = TriggerManager(
            self.trigger, self.furnace, self.orca,
            exposure_lookup_path=self.exposure_lookup_path, ref_trigger=self.ref_trigger
        )
        self.trigger_manager.get_frequencies()
        self.trigger_manager.set_target(self.trigger_manager.acq_frame_target)

        # Add cameras to self.filepaths for acquisition handling with default
        for camera in self.orca.cameras:
            self.filepaths[camera.name] = {'filename': None, 'filepath': self.furnace_filepath}

        # Reconstruct tree with relevant adapter references
        self._build_tree()

    def _build_tree(self):
        """Construct the parameter tree once adapters have been initialised."""

        self.param_tree = ParameterTree({
            'acquisition': {
                'acquiring': (lambda: self.acquiring, None),
                'start': (lambda: None, self.start_acquisition),
                'stop': (lambda: None, self.stop_acquisition),
                'freerun': (lambda: self.trigger_manager.freerun, self.trigger_manager.set_freerun),
                'frame_target': (lambda: self.trigger_manager.acq_frame_target, self.trigger_manager.set_acq_frame_target),
                'reference_trigger': (lambda: self.ref_trigger, None),
                'frequencies': self.trigger_manager.frequency_subtree,
                'link_triggers': {
                    'current': (lambda: self.trigger_manager.linked_triggers, None),
                    'link_cameras': (lambda: None, self.trigger_manager.link_triggers),
                    'unlink_cameras': (lambda: None, self.trigger_manager.unlink_triggers)
                }
            },
            'cameras': self.trigger_manager.cam_subtree
        })

    def _generate_experiment_filenames(self):
        """Generate the file names and paths for an acquisition.
        """
        # Experiment id is campaign name plus incrementing acquisition number value
        campaign_name = iac_get(self.metadata, 'fields/campaign_name/value', param='value')
        acquisition_number = iac_get(self.metadata, 'fields/acquisition_num/value', param='value')
        campaign_name = campaign_name.replace(" ", "_")
        experiment_id = campaign_name + "_" + str(acquisition_number).rjust(4, '0')

        # Add other path sorting logic here. Consider how the names might need to be in config file for real use
        # e.g. system_names=furnace, wide... then widefov_dir, narrowfov_dir, etc.. Should furnace be assumed?

        def build_filename(system, ext):
            return f"{experiment_id}_{system}.{ext}"

        # Furnace
        filename = build_filename('furnace', 'h5')
        self.filepaths['furnace']['filename'] = filename
        self.filepaths['furnace']['filepath'] = self.furnace_filepath

        # Metadata
        filename = build_filename('metadata', 'h5')
        self.filepaths['metadata']['hdf5']['filename'] = filename
        self.filepaths['metadata']['hdf5']['filepath'] = self.furnace_filepath
        # Metadata markdown

        filename = build_filename('metadata', 'md')
        self.filepaths['metadata']['md']['filename'] = filename
        self.filepaths['metadata']['md']['filepath'] = f"{self.furnace_filepath}/logs/acquisitions"

        # Cameras
        for camera in self.orca.cameras:
            name = camera.name
            self.filepaths[name]["filename"] = f"{experiment_id}_{name}"
            self.filepaths[name]["filepath"] = self.options.get(f"{name}_filepath", self.furnace_filepath)
        # Set values in metadata adapter
        iac_set(self.metadata, 'fields/experiment_id', 'value', experiment_id)
        iac_set(self.metadata, 'hdf', 'file', self.filepaths['metadata']['hdf5']['filename'])
        iac_set(self.metadata, 'hdf', 'path', self.filepaths['metadata']['hdf5']['filepath'])
        iac_set(self.metadata, 'markdown', 'file', self.filepaths['metadata']['md']['filename'])
        iac_set(self.metadata, 'markdown', 'path', self.filepaths['metadata']['md']['filepath'])

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
             'freerun': self.trigger_manager.freerun}
        )
        # Set targets to 0 for freerun
        if self.trigger_manager.freerun:
            for name in self.trigger_manager.triggers.keys():
                self.trigger_manager.set_target(0)  # Setting for one sets for all

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
                target = int(self.trigger_manager.triggers[camera.name].target)
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

        # Start time
        now = datetime.now()
        start_time = now.strftime("%d/%m/%Y, %H:%M:%S")
        iac_set(self.metadata, 'fields/start_time', 'value', start_time)

        # Enable timer coils simultaneously
        self.trigger.set_all_timers(
            {'enable': True,
             'freerun': self.trigger_manager.freerun}
        )

    def stop_acquisition(self, value=None):
        """Stop the acquisition."""
        self.acquiring = False

        # All timers explicitly disabled (even if they have and reach a target)
        self.trigger.set_all_timers(
            {'enable': False,
             'freerun': self.trigger_manager.freerun}
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
        for name, trigger in self.trigger_manager.triggers.items():
            targets[name] = trigger.target
            self.trigger_manager.set_target(0)

        # Write other metadata information
        iac_set(self.metadata, 'fields/thermal_gradient_kmm', 'value', self.furnace.gradient.wanted)
        iac_set(self.metadata, 'fields/thermal_gradient_distance', 'value', self.furnace.gradient.distance),
        iac_set(self.metadata, 'fields/cooling_rate', 'value', self.furnace.aspc.rate)

        # Stop time
        now = datetime.now()
        stop_time = now.strftime("%d/%m/%Y, %H:%M:%S")
        iac_set(self.metadata, 'fields/stop_time', 'value', stop_time)

        # Write out markdown metadata - data matches h5 at this point
        iac_set(self.metadata, 'markdown', 'write', True)

        # Write metadata hdf to file afterwards, only md needs doing first
        iac_set(self.metadata, 'hdf', 'write', True)

        # Reenable timers
        self.trigger.set_all_timers(
            {'enable': True,
             'freerun': True}
        )

        # Increase acquisition number after acquisition so UI indicates next acq instead of previous
        acquisition_number = iac_get(self.metadata, 'fields/acquisition_num/value', param='value')
        acquisition_number += 1
        iac_set(self.metadata, 'fields/acquisition_num', 'value', acquisition_number)

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
