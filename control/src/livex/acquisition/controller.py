import logging
import time
from concurrent import futures

from tornado.ioloop import PeriodicCallback
from tornado.concurrent import run_on_executor

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin._version import get_versions

from livex.util import LiveXError

class LiveXController():
    """LiveXController - class that manages the other adapters for LiveX."""

    def __init__(self):
        """Initialise the LiveXController object.

        This constructor initialises the LiveXController, building the parameter tree and getting
        system info.
        """

        # Store initialisation time
        self.init_time = time.time()

        # Get package version information
        version_info = get_versions()

        self.param_tree = ParameterTree({
            'odin_version': version_info['version'],
            'server_uptime': (self.get_server_uptime, None)
        })

    def initialise_adapters(self, adapters):
        """Get access to all of the other adapters.
        :param adapters: dict of adapters from adapter.py.
        """
        self.adapters = adapters

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