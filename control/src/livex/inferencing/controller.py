"""LiveX inferencing controller."""

import logging

from livex.util import LiveXError
from livex.inferencing.endpoint_manager import EndpointManager
from odin_control.adapters.base_controller import BaseController
from odin_control.adapters.parameter_tree import ParameterTree, ParameterTreeError

from tornado.ioloop import PeriodicCallback

class InferencingController(BaseController):
    """Inferencing controller - creates an endpoint manager for each inferencing endpoint."""

    def __init__(self, options):

        self.managers = []

        endpoint_addresses = options.get('endpoint_addresses') or ''
        endpoint_names = options.get('endpoint_names', options.get('names', '')) or ''
        self.endpoint_addresses = [item.strip() for item in endpoint_addresses.split(',') if item.strip()]
        self.names = [item.strip() for item in endpoint_names.split(',') if item.strip()]

        if len(self.names) != len(self.endpoint_addresses):
            raise LiveXError('endpoint_names must contain one name for each endpoint address')

        # Endpoints will share a background task interval
        self.bg_poll_task_enable = bool(options.get('endpoint_poll_enable', 1))
        self.bg_poll_task_interval = bool(options.get('endpoint_poll_interval', 1))

        self._create_managers()


    def _create_managers(self):
        """Build the parameter tree and the endpoint managers."""
        if len(self.managers) > 0:
            for manager in self.managers:
                manager._close_connection()
        self.managers = []
        managerTrees = {}
        tree = {}

        for i in range(len(self.endpoint_addresses)):
            manager = EndpointManager(self.endpoint_addresses[i], self.names[i])
            self.managers.append(manager)
            managerTrees[self.names[i]] = manager.param_tree

        tree['background_task'] = {
            'interval': (lambda: self.bg_poll_task_interval, self.set_task_interval),
            'enable': (lambda: self.bg_poll_task_enable, self.set_task_enable)
        }
        tree['endpoint'] = managerTrees
        self.param_tree = ParameterTree(tree)

        if self.bg_poll_task_enable:
            self.start_background_tasks()

    def get(self, path, metadata=False):
        """Get the parameter tree.
        This method returns the parameter tree for use by clients via the FurnaceController adapter.
        :param path: path to retrieve from tree
        """
        return self.param_tree.get(path, metadata)

    def get_manager_by_name(self, name):
        """Get an endpoint object by referencing its name."""
        for manager in self.managers:
            if name == manager.name:
                return manager
        return None

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

    def initialize(self, adapters):
        pass

    def status_ioloop_callback(self):
        """Periodic callback task to update inference model status."""
        for manager in self.managers:
            manager._periodic_results_task()

    def start_background_tasks(self):
        """Start the background tasks and reset the continuous error counter."""
        self.error_consecutive = 0
        self.connected = True

        logging.debug(f"Launching inference result update task with interval {self.bg_poll_task_interval}.")
        self.status_ioloop_task = PeriodicCallback(
            self.status_ioloop_callback, (self.bg_poll_task_interval * 1000)
        )
        self.status_ioloop_task.start()

    def stop_background_tasks(self):
        """Stop the background tasks."""
        self.bg_poll_task_enable = False
        self.status_ioloop_task.stop()

    def set_task_enable(self, enable):
        """Set the background task enable - accordingly enable or disable the task."""
        enable = bool(enable)

        if enable != self.bg_poll_task_enable:
            if enable:
                self.start_background_tasks()
            else:
                self.stop_background_tasks()

    def set_task_interval(self, interval):
        """Set the background task interval."""
        logging.debug("Setting background task interval to %f", interval)
        self.bg_poll_task_interval = float(interval)

    def cleanup(self):
        for manager in self.managers:
            manager._close_connection()