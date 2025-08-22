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

        # Tree branches
        self.tree['endpoint_name'] = self.name
        self.tree['endpoint'] = self.endpoint
        self.tree['connection'] = {
            'connected': (lambda: self.connected, None),
            'reconnect': (lambda: False, self._reconnect)
        }

        # Get config
        self.get_results()  # Goes to self.results
        if self.results:
            results_tree = {}

            for key, item in self.results.items():
                results_tree[key] = (lambda key=key:
                    self.results[key], None
                )  # Function uses key (the parameter) as argument via partial

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

    def get_results(self, silence_reply=True):
        """Identify if the response is for setting the status or config."""
        cmd_msg = IpcMessage('cmd', msg_val='get_results', id=self._next_msg_id())
        self.inference.send(cmd_msg.encode())

        try:
            response = self.await_response(silence_reply=silence_reply)

            if response and (self.name in response.attrs['params']):
                self.results = response.attrs['params'][self.name]
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