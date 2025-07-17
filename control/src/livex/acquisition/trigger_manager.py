"""Class to handle trigger management for the acquisition adapter."""
import logging
from functools import partial
import json

class TriggerManager:

    def __init__(self, trigger_adapter, furnace_adapter, camera_adapter, exposure_lookup_path, ref_trigger='furnace'):

        self.triggers = trigger_adapter.triggers
        self.ref_trigger = ref_trigger

        self.furnace = furnace_adapter
        self.orca = camera_adapter
        self.cam_names = [cam.name for cam in self.orca.cameras]

        try:
            with open(exposure_lookup_path, 'r') as f:
                self.exp_lookup = {int(k): v for k,v in json.load(f).items()}
        except Exception as e:
            logging.warning(f"Error loading cam exposure lookup table: {e}. Setting to empty.")
            self.exp_lookup = {}

        self.linked_triggers = []  # List to hold connected triggers
        self.use_exposure_lookup = False

        # Initialize frequencies and frequency subtree
        self.frequencies = {}
        self.frequency_subtree = {}
        self.acq_frame_target = 100
        self.acq_frame_frequency = 10  # Frequency used for frame target acquisitions (future)
        self.freerun = True
        self.targets = {name: 0 for name in self.triggers.keys()}  # Store targets for freerun use
        self.get_frequencies()

        self.cam_subtree = {
            f'{camera.name}_exposure': (lambda camera=camera: camera.config['exposure_time'], partial(
                self.set_camera_exposure, cam_name=camera.name)
            ) for camera in self.orca.cameras
        }
        self.cam_subtree['use_exposure_lookup'] = (lambda: self.use_exposure_lookup, self.set_use_exposure_lookup)

    def get_frequencies(self):
        """Get all triggers and set up the tree."""
        for name, trigger in self.triggers.items():
            self.frequencies[name] = float(trigger.frequency)

            self.frequency_subtree[name] = (
                lambda trigger=trigger: float(trigger.frequency), partial(self.set_frequency, trigger=name)
            )

    def set_frequency(self, value, trigger=None):
        """Set a given timer's frequency to the provided value."""
        if trigger not in self.triggers.keys():
            logging.warning(f"Trigger {trigger} not found when setting frequency.")
            return

        value = float(value)

        self.triggers[trigger].set_frequency(value)
        self.frequencies[trigger] = value

        # Logic for linked triggers goes here
        if trigger in self.linked_triggers:
            for linked in self.linked_triggers:
                if linked != trigger:
                    self.triggers[linked].set_frequency(value)
                    self.frequencies[linked] = value

        # Handle exposure if needed
        if self.use_exposure_lookup and trigger in self.cam_names:
            cam = self.orca.get_camera_by_name(trigger)
            exp_time = self.exp_lookup.get(value, cam.config['exposure_time'])
            self.set_camera_exposure(exp_time, trigger)

        self.furnace.update_furnace_frequency(self.frequencies[self.ref_trigger])

        # Targets will change based on frequency if they aren't the reference trigger, update them
        self.set_target(self.triggers[self.ref_trigger].target)

    def set_target(self, value):
        """Set a frame target for the acquisition - based on the reference trigger.
        Each other trigger has its target scaled by its frequency against the reference trigger."""
        target = int(value)
        self.triggers[self.ref_trigger].set_target(target)

        for trigger in self.triggers.values():
            scaled_target = target * (trigger.frequency / self.frequencies[self.ref_trigger])
            trigger.set_target(scaled_target)

        # Logic for linked triggers goes here

    def link_triggers(self, triggers):
        """Link two triggers to each other."""
        trigger1, trigger2 = triggers
        self.linked_triggers.append(trigger1) if trigger1 not in self.linked_triggers else None
        self.linked_triggers.append(trigger2) if trigger2 not in self.linked_triggers else None

    def unlink_triggers(self, triggers):
        """Unlink two triggers from each other."""
        trigger1, trigger2 = triggers
        if trigger1 in self.linked_triggers:
            self.linked_triggers.remove(trigger1)
        if trigger2 in self.linked_triggers:
            self.linked_triggers.remove(trigger2)

    def set_use_exposure_lookup(self, value):
        """Enable or disable exposure lookup table for cameras."""
        self.use_exposure_lookup = bool(value)

    def set_camera_exposure(self, exposure_time, cam_name=None):
        """Interface for the orca-quest adapter to set camera exposure with linked trigger logic.
        """
        if cam_name is None or cam_name not in self.cam_names:
            logging.error("Camera name not provided or not found for exposure setting.")
            return

        camera = None
        camera = self.orca.get_camera_by_name(cam_name)
        camera.set_config(value=exposure_time, param='exposure_time')

        # Handle linked cameras
        if cam_name in self.linked_triggers:
            for linked in self.linked_triggers:
                if linked != cam_name:
                    cam = self.orca.get_camera_by_name(linked)
                    cam.set_config(value=exposure_time, param='exposure_time')

    def set_acq_frame_target(self, value):
        """Set the frame target(s) of the acquisition."""
        # Furnace works as 'source of truth' for frame targets. Others are scaled against it
        self.get_frequencies()

        self.acq_frame_target = int(value)

        self.set_target(self.acq_frame_target)

    # Function currently unused pending discussion of how target-based acquisition should work
    def set_acq_frame_frequency(self, value):
        """Set the frequency of the frame target acquisition."""
        value = float(value)
        self.acq_frame_frequency = value
        for trigger in self.trigger.triggers.values():
            trigger.set_frequency(value)

    def set_freerun(self, freerun):
        """Enable or disable freerun mode for the targets."""

        self.freerun = bool(freerun)

        if freerun:
            logging.debug("Freerun mode enabled for all triggers.")
            for trigger in self.triggers.values():
                self.targets[trigger.name] = trigger.target
                trigger.set_target(0)
        else:  # Freerun disabled, restore previous targets
            logging.debug("Freerun mode disabled, restoring targets.")
            for trigger in self.triggers.values():
                trigger.set_target(self.targets[trigger.name])
