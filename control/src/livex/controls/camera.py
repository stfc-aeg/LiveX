"""Class to control camera. Initially, IPC communication as this is how the cameras will be interacted with."""

from odin_data.ipc_channel import IpcChannel
from odin_data.ipc_message import IpcMessage
from odin.adapters.parameter_tree import ParameterTree

import logging

class Camera():

    def __init__(self, instance_count):
        
        # I want a tree that links to a button that, when pressed, will create and send an IPC message
        self.port = 9001
        self.ctrl_channels = []

        for i in range(instance_count):
            channel = IpcChannel(IpcChannel.CHANNEL_TYPE_DEALER)
            endpoint = f"tcp://192.168.0.31:{self.port + i}"  # Different port for each
            channel.connect(endpoint)
            self.ctrl_channels.append(channel)

        # tree
        self.test = None
        self.tree = ParameterTree({
            'test': (lambda: self.test, self.send_command)
        })

        self.msg_id = 0

    def next_msg_id(self):
        """Return the next message id."""
        self.msg_id += 1
        return self.msg_id

    def send_command(self, value):
        """Compose a command message to be sent."""
        self.command = {}
        self.command["command"] = value

        self.command_msg = {
            "params": self.command
        }
        self.send_config_message(self.command_msg)
    
    def send_config_message(self, config):
        """Send a configuration message."""
        all_responses_valid = True

        for channel in self.ctrl_channels:
            msg = IpcMessage('cmd', 'configure', id=self.next_msg_id())
            msg.attrs.update(config)
            # logging
            logging.debug(f"Sending configuration: {config} to {channel.identity}")

            channel.send(msg.encode())
            if not self.await_response(channel):
                # await response from channel
                all_responses_valid = False

        return all_responses_valid

    def await_response(self, channel, timeout_ms=10000):
        """Await a response on the given channel."""
        pollevents = channel.poll(timeout_ms)

        if pollevents == IpcChannel.POLLIN:
            reply = IpcMessage(from_str=channel.recv())

            logging.debug(f"Got response from {channel.identity}: {reply}")

            return reply
        else:
            logging.debug(f"No response received or error occurred from {channel.identity}.")

            return False
