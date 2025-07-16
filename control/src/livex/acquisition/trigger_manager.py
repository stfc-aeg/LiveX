"""Class to handle trigger management for the acquisition adapter."""
import logging
from functools import partial

class TriggerManager:

    def __init__(self, trigger_adapter, furnace_adapter, ref_trigger='furnace'):

        self.triggers = trigger_adapter.triggers
        self.ref_trigger = ref_trigger

        self.furnace = furnace_adapter

        self.linked_triggers = set()  # List to hold connected triggers

        # Initialize frequencies and frequency subtree
        self.frequencies = {}
        self.frequency_subtree = {}
        self.acq_frame_target = 100
        self.acq_frame_frequency = 10  # Frequency used for frame target acquisitions (future)
        self.freerun = True
        self.targets = {name: 0 for name in self.triggers.keys()}  # Store targets for freerun use
        self.get_frequencies()

    def get_frequencies(self):
        """Get all triggers and set up the tree."""
        for name, trigger in self.triggers.items():
            self.frequencies[name] = float(trigger.frequency)
            logging.debug(f"self.frequencies[{name}] = {self.frequencies[name]}")

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

    def link_triggers(self, trigger1, trigger2):
        """Link two triggers to each other."""
        self.linked_triggers.add(trigger1)
        self.linked_triggers.add(trigger2)

    def unlink_triggers(self, trigger1, trigger2):
        """Unlink two triggers from each other."""
        if trigger1 in self.linked_triggers:
            self.linked_triggers.remove(trigger1)
        if trigger2 in self.linked_triggers:
            self.linked_triggers.remove(trigger2)

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
