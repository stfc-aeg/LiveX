"""LiveX inference controller."""

import logging
from livex.base_controller import BaseController
from livex.util import LiveXError
from livex.inference.inference_endpoint import InferenceEndpoint
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

class InferenceController(BaseController):
    """"""

    def __init__(self, options):
        #  endpoints, names, bg_poll_task_enable, bg_poll_task_interval):
        """This constructor initialises the object and builds parameter trees."""

        # Internal variables
        self.endpoints = []

        self.endpoint_addresses = [
            item.strip() for item in options.get('endpoint_addresses', None).split(",") if item.strip()
        ]
        self.names = [
            item.strip() for item in options.get('names', None).split(",") if item.strip()
        ]

        self.bg_poll_task_enable = bool(options.get('bg_poll_task_enable', 1))
        self.bg_poll_task_interval = int(options.get('bg_poll_task_interval', 1))

        # Also builds the tree
        self._connect_endpoints()

    def _connect_endpoints(self, value=None):
        """Build the parameter tree and attempt to connect the cameras to it."""
        if len(self.endpoints) > 0:
            for endpoint in self.endpoints:
                endpoint._close_connection()
        self.endpoints= []
        endpointTrees = {}
        tree = {}

        for i in range(len(self.endpoint_addresses)):
            endpoint = InferenceEndpoint(self.endpoint_addresses[i], self.names[i], self.bg_poll_task_enable, self.bg_poll_task_interval)
            self.endpoints.append(endpoint)
            endpointTrees[self.names[i]] = endpoint.param_tree

        # Array of camera trees becomes a real Parameter Tree
        tree['endpoints'] = endpointTrees
        self.param_tree = ParameterTree(tree['endpoints'])

    def get(self, path, metadata=False):
        """Get the parameter tree.
        This method returns the parameter tree for use by clients via the FurnaceController adapter.
        :param path: path to retrieve from tree
        """
        return self.param_tree.get(path, metadata)

    def get_endpoint_by_name(self, name):
        """Get an endpoint object by referencing its name."""
        for endpoint in self.endpoints:
            if name == endpoint.name:
                return endpoint
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

    def cleanup(self):
        for endpoint in self.endpoints:
            endpoint._close_connection()