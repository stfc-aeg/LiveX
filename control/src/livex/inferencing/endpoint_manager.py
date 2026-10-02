"""Python class to manage the inferencing endpoints (results, image)."""

import logging

from odin_control.adapters.parameter_tree import ParameterTree
from odin_data.control.ipc_channel import IpcChannel
from odin_data.control.ipc_message import IpcMessage
from livex.util import LiveXError
from zmq import ZMQError

class EndpointManager():

    def __init__(self, endpoint, name):

        self.endpoint_addr = endpoint
        self.results_endpoint = self.endpoint_addr + ":9002"
        self.name = name

        self.msg_id = 0
        self.results = {}
        self.stats = {}
        self.model_status = {'app_state': 'no_model'}
        self.selected_model = None
        self.available_models = []
        self.result_modes = None
        self.connected = False
        self.timeout_ms = 1000
        self.error_consecutive = 0

        self._connect_results()
        self.tree = {
            'endpoint_name': self.name,
            'endpoint': self.results_endpoint,
            'connection': {'connected': (lambda: self.connected, None)},
            'stats': (lambda: self.stats, None),
            'model': {
                'selected': (lambda: self.selected_model, None),
                'select': (lambda: self.selected_model, self.select_model),
                'status': (lambda: self.model_status, None),
                'available': (lambda: self.available_models, None)
            },
            'results': (lambda: self.results, None),
        }
        self.param_tree = ParameterTree(self.tree)

    def _connect_results(self):
        self.results_channel = IpcChannel(IpcChannel.CHANNEL_TYPE_DEALER)
        try:
            self.results_channel.connect(self.results_endpoint)
            self.connected = True
        except ZMQError as e:
            raise LiveXError(f"Error connecting to {self.name} results endpoint: {e}")

        # Get state once connection is established
        self.get_stats()
        self.list_models()

        if not self.stats:
            raise LiveXError(f"Failed to get stats from {self.name} results endpoint, please check the connection.")

        # There may be a model loaded already
        
        if self.stats['app_state'] != 'no_model':
            self.get_model_status()
            self._clear_results()

    def _call(self, cmd, params=None, timeout=1000):
        """Send an ipc command message and return the response.
        :param cmd: command as a string
        :param params: any required parameters for the object
        :param timeout: timeout in ms as an integer
        :return: IpcMessage
        """
        self.msg_id += 1
        req = IpcMessage("cmd", cmd, id=self.msg_id)
        if params:
            req.set_params(params)
        self.results_channel.send(req.encode())
        if not (self.results_channel.poll(timeout) & IpcChannel.POLLIN):
            raise LiveXError(f"Timeout on inference command: {cmd}")
        response = IpcMessage(from_str=self.results_channel.recv())
        response_attrs = response.attrs

        if response_attrs.get('msg_type') == 'nack':
            body = next(iter(response_attrs.get('params', {}).values()), {})
            raise LiveXError(body.get('error', f"Inference command failed: {cmd}"))

        response_params = response_attrs.get('params', {})
        if self.name in response_params:
            return response_params[self.name]
        if len(response_params) == 1:
            return next(iter(response_params.values()))
        raise LiveXError(f"Unexpected response from inference command: {cmd}")

    def get_stats(self):
        """Get the endpoint stats and update the app state"""
        self.stats = self._call(cmd='get_stats')
        self.model_status['app_state'] = self.stats.get(
            'app_state', self.model_status.get('app_state', 'no_model')
        )
        return self.stats

    def list_models(self):
        response = self._call('list_models')
        self.models = response['models']
        for model in self.models:
            self.available_models.append(model['display_name'])

    def select_model(self, name):
        """Request an asynchronous model selection by model folder name."""
        if not isinstance(name, str) or not name.strip():
            raise LiveXError('A model name is required')

        # Fetch the actual model name
        selected_model = ""
        for model in self.models:
            if model['display_name'] == name:
                selected_model = model['name']
                logging.warning(f"selected_model: {model['name']}")
        if not selected_model:
            raise LiveXError(f"Model name {name} not found.")

        response = self._call(cmd='select_model', params={'name': selected_model})
        self.selected_model = response.get('name', name.strip())
        self.model_status = response

        self.get_model_status()
        self._clear_results()

    def _clear_results(self):
        """Create an empty results tree based on the current model's result_modes."""
        result_modes = self.model_status.get('result_modes')
        if result_modes is not None and result_modes != self.result_modes:
            self.result_modes = result_modes
            self.results = { 'first_frame': 0, 'most_recent_frame': 0}

            # Result modes is a dictionary of graph-names, which have some data and the results to plot on them
            # These results contain the name of the result and an optional label for the graph legend
            logging.warning(f"result_modes: {result_modes}")
            for graph_name in result_modes.keys():
                graph = result_modes[graph_name]
                self.results[graph_name] = {
                    'type': graph['type'],
                    'axis_limit': graph.get('axis_limit', None),
                    'x_label': graph.get('x_label', None),
                    'y_label': graph.get('y_label', None),
                    'graph_label': graph.get('graph_label', None),
                    'results': {}
                }

                if graph['type'] != 'bitmap':
                    for result in graph['results']:
                        self.results[graph_name]['results'][result['name']] = {
                            'label': result.get('label', result['name']),
                            'data': [],
                        }

    def get_model_status(self):
        """Send a command to get the latest model status information."""
        self.model_status = self._call(cmd='get_model_status')
        self.selected_model = self.model_status.get('selected', self.selected_model)

    def get_results(self):
        """Drain and store results currently buffered by the endpoint."""
        response = self._call(cmd='get_results')

        results = response.get('results', [])
        frame_number = None
        for inferred_frame in results:  # Results is an array of objects
            frame_number = inferred_frame['frame_number']
            for graph_name, results in inferred_frame['values'].items():
                for result, value in results.items():
                    self.results[graph_name]['results'][result]['data'].append(
                        value
                    )

        self.results['most_recent_frame'] = frame_number

    def _close_connection(self):
        """Close the control channel."""
        if self.connected:
            self.results_channel.close()
            self.connected = False

    def _periodic_results_task(self):
        """Periodic task called by the controller to get model results if ready."""
        self.get_model_status()
        if self.model_status['app_state'] in ['ready', 'capturing_flat', 'inferencing']:
            self.get_results()