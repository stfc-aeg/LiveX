"""LiveX inference controller."""

import logging

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from odin_data.control.ipc_channel import IpcChannel
from odin_data.control.ipc_message import IpcMessage

from tornado.ioloop import PeriodicCallback

class InferenceEndpoint():

    def __init__(self, endpoint, name, bg_poll_task_enable, bg_poll_task_interval):

        self.endpoint = endpoint
        self.name = name
        self.msg_id = 0

        self.bg_poll_task_enable = bg_poll_task_enable
        self.bg_poll_task_interval = bg_poll_task_interval

        self.results = {}
        self.tree = {}

        self.timeout_ms = 1000
        self.error_consecutive = 0

        self._connect()

    def _connect(self):
        """Create an IpcChannel object and build the ParameterTree."""
        # IpcChannel object
        self.inference = IpcChannel(IpcChannel.CHANNEL_TYPE_DEALER)
        self.inference.connect(self.endpoint)
        # With no return from IpcChannel.connect(), assume success until failure is reached
        self.connected = True

        # Number of acquisition to use for flatfield
        self.flatfield_num = 0

        # Tree branches
        self.tree['endpoint_name'] = self.name
        self.tree['endpoint'] = self.endpoint
        self.tree['connection'] = {
            'connected': (lambda: self.connected, None),
            'reconnect': (lambda: False, self._reconnect)
        }

        self.columnar = []
        self.equiaxed = []
        self.alpha = []
        self.beta = []
        self.hot_tear = []

        self.tree['probabilities'] = {
            'columnar': (lambda: self.columnar, None),
            'equiaxed': (lambda: self.equiaxed, None),
            'alpha': (lambda: self.alpha, None),
            'beta': (lambda: self.beta, None),
            'hot_tear': (lambda: self.hot_tear, None)
        }

        # Default results
        self.results = {
            'inference_enabled': False,
            'inference_running': False,
            'last_frame_number': -1,
            'avg_inference_time_ms': 0.0,
            'flatfield_file': '',
            'experiment_number': -1,
            'recording': False,
            'num_predictions': 0,
        }

        # Get config
        self.get_results()  # Goes to self.results
        results_tree = {}

        for key, item in self.results.items():
            results_tree[key] = (lambda key=key:
                self.results[key], None
            )

        results_tree['set_flatfield_num'] = (lambda: self.flatfield_num, self.set_flatfield_num)

        results_tree = ParameterTree(results_tree)
        self.tree['results'] = results_tree

        # Background task branch of tree
        self.tree['background_task'] = {
            "interval": (lambda: self.bg_poll_task_interval, self.set_task_interval),
            "enable": (lambda: self.bg_poll_task_enable, self.set_task_enable)
        }

        self.param_tree = ParameterTree(self.tree)

        if self.bg_poll_task_enable:
            self.start_background_tasks()

    def _reconnect(self, value=None):
        """Close the previous camera connection and recreate it."""
        self._close_connection()
        self._connect()

    def set_flatfield_num(self, num):
        """Set the acquisition file number for flatfield correction."""

        try:
            if num < 0:
                self.flatfield_num = 0
                num = None  # Special case to clear flatfield, assuming -1

            cmd_msg = IpcMessage('cmd', msg_val='set_flatfield_num', id=self._next_msg_id())
            config = { "params": {"num": num} }
            cmd_msg.attrs.update(config)
            self.inference.send(cmd_msg.encode())

            response = self.await_response(silence_reply=False)

            if response:
                logging.info(f"Set flatfield acquisition number to {num} for {self.name}:{self.inference.identity}")
            else:
                logging.debug(f"Got no or unexpected response structure from {self.name}:{self.inference.identity}")
        except Exception as e:
            logging.error(f"Error setting ff acq num: {e}")

    def _append_probabilities(self, probabilities, num_probabilities=0):
        """Append new probabilities to the lists."""
        for i in range(num_probabilities):
            res = probabilities[i]

            # Need to trim these to maximum length by removing earliest entries
            max_length = 3600  # Arbitrary maximum length for now

            self.columnar.append(res['columnar'])
            self.equiaxed.append(res['equiaxed'])
            self.alpha.append(res['alpha'])
            self.beta.append(res['beta'])
            self.hot_tear.append(res['hot_tear'])

        if len(self.columnar) > max_length:  # If one is longer, they will all be longer
            diff = len(self.columnar) - max_length
            self.columnar = self.columnar[diff:]
            self.equiaxed = self.equiaxed[diff:]
            self.alpha = self.alpha[diff:]
            self.beta = self.beta[diff:]
            self.hot_tear = self.hot_tear[diff:]

    def get_results(self, silence_reply=True):
        """Identify if the response is for setting the status or config."""
        cmd_msg = IpcMessage('cmd', msg_val='get_results', id=self._next_msg_id())
        self.inference.send(cmd_msg.encode())

        try:
            response = self.await_response(silence_reply=silence_reply)

            if response and (self.name in response.attrs['params']):
                results = response.attrs['params'][self.name]
                self.results = {
                    'inference_enabled': results.get('inference_enabled', False),
                    'inference_running': results.get('inference_running', False),
                    'last_frame_number': results.get('last_frame_number', -1),
                    'avg_inference_time_ms': results.get('avg_inference_time_ms', 0.0),
                    'flatfield_file': results.get('flatfield_file', ''),
                    'experiment_number': results.get('experiment_number', -1),
                    'recording': results.get('recording', False),
                    'num_predictions': results.get('num_predictions', 0),
                    'frames_per_second': results.get('frames_per_second', 0),
                    'active_classes': results.get('active_classes', [])
                }

                probabilities = results.get('result_buffer', [])

                if probabilities:
                    self._append_probabilities(probabilities, len(probabilities))

            else:
                logging.debug(f"Got no or unexpected response structure from {self.name}:{self.inference.identity}")
        except Exception as e:  # If there is an error, do not update the status
            logging.debug(f"Could not fetch results for endpoint {self.name}:{self.inference.identity}: {e}")

    def await_response(self, timeout_ms=100, silence_reply=True):
        """Await a response on the given camera.
        :param timeout_ms: timeout in milliseconds
        :param silence_reply: silence positive response logging if true. for frequent requests
        :return: response, or False
        """
        pollevents = self.inference.poll(timeout_ms)

        if pollevents == IpcChannel.POLLIN:
            reply = IpcMessage(from_str=self.inference.recv())

            if not silence_reply:
                logging.info(f"Got response from {self.inference.identity}: {reply}")

            self.error_consecutive = 0
            return reply
        else:
            self.error_consecutive += 1
            logging.debug(f"No response received, or error occurred, from {self.inference.identity}")
            return False

    def start_experiment(self, experiment_number):
        """Send a start_experiment command.
        :param experiment_number: number of experiment e.g. 0012
        """
        cmd_msg = IpcMessage('cmd', msg_val='start_experiment', id=self._next_msg_id())
        cmd_msg.set_param(param_name='experiment_number', param_value=experiment_number)
        self.inference.send(cmd_msg.encode())

        try:
            response = self.await_response(silence_reply=True)
            if response:
                if response.get('msg_type', 'ack') == 'nack':
                    logging.error(f"Error when starting inferencing experiment: {response.attrs['params']['error']}")
                    # No particular handling of errors but should at least inform on what they are
        except Exception as e:
            logging.error(f"Error when starting inferencing experiment: {e}")

    def stop_experiment(self):
        """Send a stop_experiment command."""
        cmd_msg = IpcMessage('cmd', msg_val='stop_experiment', id=self._next_msg_id())
        self.inference.send(cmd_msg.encode())

    def _next_msg_id(self):
        """Return the next (incremented) message id."""
        self.msg_id += 1
        return self.msg_id

    def status_ioloop_callback(self):
        """Periodic callback task to update camera status."""
        if self.error_consecutive >= 10:
            # After 10 consecutive errors, halt the background task and assume disconnected
            self.connected = False
            logging.error("Multiple consecutive errors in inference endpoint response. Halting periodic request task.")
            self.stop_background_tasks()
        self.get_results()

    def start_background_tasks(self):
        """Start the background tasks and reset the continuous error counter."""
        self.error_consecutive = 0
        self.connected = True

        logging.debug(f"Launching inference result update task for {self.name} endpoint with interval {self.bg_poll_task_interval}.")
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

    def _close_connection(self):
        """Close the IpcChannel connection."""
        logging.info(f"Closing socket for endpoint {self.name}.")
        self.inference.close()