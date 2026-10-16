"""Python class to manage the inferencing endpoints (results, image)."""

import logging

import zmq
from zmq import ZMQError
from tornado.escape import json_decode
from odin_control.adapters.parameter_tree import ParameterTree
from odin_data.control.ipc_channel import IpcChannel
from odin_data.control.ipc_message import IpcMessage

from livex.util import LiveXError

class EndpointManager():

    def __init__(self, endpoint, name, data_retention):
        """Initialise the endpoint manager class.
        Create a range of variables for managing the connections and results,
        and create the ParameterTree after attempting to connect to a results endpoint.
        """
        self.endpoint_addr = endpoint
        self.results_endpoint = self.endpoint_addr + ":9002"
        self.image_endpoint = self.endpoint_addr + ":9003"
        self.image_channel = None
        self.image_header = None
        self.image = None
        self.name = name
        self.data_retention = data_retention

        self.msg_id = 0
        self.results = {}
        self.stats = {}
        self.model_status = {'app_state': 'no_model'}
        self.selected_model = None
        self.available_models = []
        self.result_modes = None
        self.bitmap_images = {}
        self.results_connected = False
        self.image_connected = False
        self.timeout_ms = 1000
        self.error_consecutive = 0

        self._connect_results()
        self.tree = {
            'endpoint_name': self.name,
            'endpoint': self.endpoint_addr,
            'connection': {'connected': {
                'results': (lambda: self.results_connected, None),
                'image': (lambda: self.image_connected, None)
            }},
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
        """Connect to the results endpoint.
        If it's available, fetch results.
        If there is a model loaded, populate the results part of the tree.
        """
        self.results_channel = IpcChannel(IpcChannel.CHANNEL_TYPE_DEALER)
        try:
            self.results_channel.connect(self.results_endpoint)
            self.results_connected = True
        except ZMQError as e:
            raise LiveXError(f"Error connecting to {self.name} results endpoint: {e}")

        # Get state once connection is established
        self.get_stats()
        self.list_models()

        if not self.stats:
            raise LiveXError(f"Failed to get stats from {self.name} results endpoint, please check the connection.")

        # There may be a model loaded already
        if self.model_status['app_state'] != 'no_model':
            self.get_model_status()
            self._clear_results()

    def _connect_image(self):
        """Connect and subscribe to the image endpoint."""
        self.image_channel = IpcChannel(IpcChannel.CHANNEL_TYPE_SUB)
        try:
            self.image_channel.connect(self.image_endpoint)
            self.image_channel.subscribe()
        except ZMQError as e:
            self.image_channel.close()
            logging.warning("Error connecting to %s image endpoint: %s", self.name, e)
            return

        self.image_connected = True

    def _update_image_connection(self, image_stream):
        """Handle the image connection process."""
        endpoint = image_stream.get('endpoint') if image_stream.get('available') else None
        if endpoint == self.image_endpoint and (endpoint is None or self.image_connected):
            return

        self._close_image_connection()
        if endpoint:
            self._connect_image()

    def _close_image_connection(self):
        """Close the image connection and reset the local references."""
        if self.image_channel is not None:
            self.image_channel.close()
        self.image_connected = False
        self.image_header = None
        self.image = None
        self.bitmap_images.clear()

    def _call(self, cmd, params=None, timeout=1000):
        """Send an IPC command and return its response body."""
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
        response = self._call(cmd='get_stats')
        self.stats = response.get('stats', {})  # Just the frame counters needed
        self.model_status['app_state'] = response.get(
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
        result_modes = self.result_modes
        self.results = {'first_frame': 0, 'most_recent_frame': 0}
        self.bitmap_images.clear()
        if result_modes is None:
            return

        # Result modes describe each graph and the series available to plot.
        for graph_name, graph in result_modes.items():
            self.results[graph_name] = {
                'type': graph['type'],
                'axis_limit': graph.get('axis_limit'),
                'x_label': graph.get('x_label'),
                'y_label': graph.get('y_label'),
                'graph_label': graph.get('graph_label'),
                'results': {}
            }

            if graph['type'] != 'bitmap':
                for result in graph.get('results', []):
                    self.results[graph_name]['results'][result['name']] = {
                        'label': result.get('label', result['name']),
                        'data': [],
                    }

    def get_model_status(self):
        """Send a command to get the latest model status information."""
        response = self._call(cmd='get_model_status')
        self.model_status = {
            'app_state': response.get('app_state', self.model_status.get('app_state', 'no_model')),
            'display_name': response.get('display_name', self.model_status.get('display_name', None)),
            'preprocessing': response.get('preprocessing', self.model_status.get('preprocessing', None)),
            'image_stream': response.get('image_stream', {'available': False})
        }
        self.selected_model = response.get('selected', self.selected_model)
        self.result_modes = response.get('result_modes', self.result_modes)

        self._update_image_connection(self.model_status['image_stream'])

    def get_results(self):
        """Drain and store results currently buffered by the endpoint."""
        response = self._call(cmd='get_results')

        results = response.get('results', [])
        frame_number = None
        for inferred_frame in results:  # Results is an array of objects
            frame_number = inferred_frame['frame_number']
            for graph_name, results in inferred_frame['values'].items():
                for result, value in results.items():
                    if len(self.results[graph_name]['results'][result]['data']) >= self.data_retention:
                        self.results[graph_name]['results'][result]['data'].pop(0)
                    self.results[graph_name]['results'][result]['data'].append(
                        value
                    )

        self.results['most_recent_frame'] = frame_number

    def get_image(self):
        """Receive available image messages and retain the newest encoded image."""
        if not self.image_connected:
            return self.image

        latest_parts = None
        while True:
            try:
                parts = self.image_channel.socket.recv_multipart(flags=zmq.NOBLOCK)
            except zmq.Again:
                break
            if len(parts) == 2:
                latest_parts = parts

        if latest_parts is not None:
            header = json_decode(latest_parts[0])

            self.image = latest_parts[1]
            content_type = {'jpeg': 'image/jpeg', 'png': 'image/png'}.get(
                header.get('dtype')
            )
            if content_type is None:
                logging.warning(f"Unsupported image format from {self.name}: {self.header}")
                return self.image

            for graph in self.results.values():
                if isinstance(graph, dict) and graph.get('type') == 'bitmap':
                    graph['results']['frame_number'] = header.get('frame_num')

            bitmap_graphs = [
                graph_name for graph_name, graph in self.results.items()
                if isinstance(graph, dict) and graph.get('type') == 'bitmap'
            ]
            if len(bitmap_graphs) == 1:
                self.bitmap_images[bitmap_graphs[0]] = (self.image, content_type)
            elif bitmap_graphs:
                logging.warning(
                    "Cannot associate image from %s with multiple bitmap graphs: %s",
                    self.name, bitmap_graphs
                )

        return self.image

    def get_bitmap_image(self, graph_name):
        """Return the latest encoded image and content type for a bitmap graph."""
        graph = self.results.get(graph_name)
        if not isinstance(graph, dict) or graph.get('type') != 'bitmap':
            return None
        return self.bitmap_images.get(graph_name)

    def _close_connection(self):
        """Close the control and image channels."""
        self._close_image_connection()
        if self.results_connected:
            self.results_channel.close()
            self.results_connected = False

    def _periodic_results_task(self):
        """Periodic task called by the controller to get model results if ready."""
        self.get_model_status()
        if self.model_status['app_state'] in ['ready', 'capturing_flat', 'inferencing']:
            self.get_results()
        if self.image_connected:
            self.get_image()