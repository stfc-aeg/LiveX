"""
Graphing Adapter for Odin Control.
Implements means of monitoring a stream of data, with specified time intervals.
this is done so that GUI elements (such as using chart.js) can be easily implemented

Ashley Neaves, STFC Detector Systems Software Group"""

import logging

from odin.adapters.adapter import (ApiAdapter, ApiAdapterRequest,
                                   ApiAdapterResponse, request_types, response_types)
from odin.util import decode_request_body
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from tornado.ioloop import PeriodicCallback, IOLoop
from tornado.escape import json_decode
import time
import datetime
import json
import h5py
import numpy as np
import os


class GraphDataset():

    def __init__(self, time_interval, adapter, get_path, get_subpaths, retention, log_file, log_directory, name=None):
        self.time_interval = time_interval
        self.data = {
            'temp_a': [],
            'temp_b': [],
            'timestamps': []
        }
        self.timestamps = []
        self.adapter_name = adapter
        self.adapter = None
        self.get_path = get_path
        self.get_subpaths = get_subpaths
        self.retention = retention
        self.name = name

        self.log_file = log_file
        self.log_directory = log_directory

        self.data_loop = PeriodicCallback(self.get_data, self.time_interval * 1000)

        logging.debug("Created Dataset %s, interval of %f seconds", name, self.time_interval)

        logging_tree = ParameterTree({
            "log_directory": (lambda: self.log_directory, None),
            "log_file": (lambda: self.log_file, self.update_log_file),
            "write_data": (lambda: False, self.write_data)
        })

        self.param_tree = ParameterTree({
            "name": (self.name, None),
            "data": (lambda: self.data, None),
            "timestamps": (lambda: self.timestamps, None),
            "interval": (self.time_interval, None),
            "retention": (self.retention * self.time_interval, None),
            "loop_running": (lambda: self.data_loop.is_running(), None),
            "logging": logging_tree
        })

    def get_data(self):

        for key in self.data.keys():
            if len(self.data[key]) > self.retention:
                self.data[key].pop(0)

        cur_time = datetime.datetime.now()
        cur_time = cur_time.strftime("%H:%M:%S")
        self.data['timestamps'].append(cur_time)

        if len(self.data['timestamps']) > self.retention:
            self.data['timestamps'].pop(0)

    def get_adapter(self, adapter_list):
        self.adapter = adapter_list[self.adapter_name]

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    def update_log_file(self, filename):
        if (filename.endswith('.hdf5')):
            self.log_file = filename
        else:
            filename += '.hdf5'
            self.log_file = filename

    def write_data(self, request):
        """Write stored data to an hdf5 file.
        To-do: make this more generic / file-writing its own class."""
        logging.debug("log directory: %s", self.log_directory)

        log_filepath = os.path.join(self.log_directory, self.log_file)
        os.makedirs(self.log_directory, exist_ok=True)

        f = h5py.File(log_filepath, "w")

        temp_group = f.require_group("temperature_readings")

        # Param tree could be np arrays - this for now
        tempa_arr = np.array(self.data['temp_a'])
        tempb_arr = np.array(self.data['temp_b'])
        times_arr = np.array(self.data['timestamps'], dtype='S')

        if ("temp_a" or "temp_b" or "timestamps") in temp_group:
            temp_group['temp_a'][...] = tempa_arr
            temp_group['temp_b'][...] = tempb_arr
            temp_group['timestamps'][...] = times_arr
        else:
            tempa_dset = temp_group.create_dataset(
                "temp_a", data=tempa_arr
            )
            tempb_dset = temp_group.create_dataset(
                "temp_b", data=tempb_arr
            )
            times_dset = temp_group.create_dataset(
                "timestamps", data=times_arr
            )
        logging.debug("File written successfully.")

class AvgGraphDataset(GraphDataset):

    def __init__(self, time_interval, retention, name, source):
        super().__init__(time_interval, adapter=None, get_path=None, retention=retention, name=name)
        
        self.source = source
        self.num_points_get = int(self.time_interval / self.source.time_interval)

        logging.debug("This is an averaging dataset, averaging from %s", self.source)

    def get_data(self):
        cur_time = time.time()
        data = self.source.data[-self.num_points_get:]  # slice, get last x elements
        # data = list(zip(*data))[1]  # zip the timestamps and data of target list into separate
        data = data = sum(data) / len(data)

        self.data.append(data)
        self.timestamps.append(cur_time)
        if len(self.data) > self.retention:
            self.data.pop(0)
            self.timestamps.pop(0)

    def get_adapter(self, adapter_list):
        pass  # method empty on purpose as we don't need the adapter for this type of dataset


class GraphAdapter(ApiAdapter):

    def __init__(self, **kwargs):

        super(GraphAdapter, self).__init__(**kwargs)

        self.dataset_config = self.options.get("config_file")
        self.log_directory = self.options.get("log_directory")
        self.log_file = self.options.get("log_file")

        self.datasets = {}

        with open(self.dataset_config) as f:
            config = json.load(f)
            for name, info in config.items():
                try:
                    if info.get('average', False):
                        # dataset is an averaging of another dataset
                        dataset = AvgGraphDataset(
                            time_interval=info['interval'],
                            retention=info['retention'],
                            name=name,
                            source=self.datasets[info['source']]
                        )
                    else:
                        dataset = GraphDataset(
                            time_interval=info['interval'],
                            adapter=info['adapter'],
                            get_path=info['get_path'],
                            get_subpaths=info['get_subpaths'],
                            retention=info['retention'],
                            log_file = self.log_file,
                            log_directory = self.log_directory,
                            name=name
                        )
                    self.datasets[name] = dataset
                except KeyError as err:
                    logging.error("Error creating dataset %s: %s", name, err)

        logging.debug("dataset: %s", self.datasets)

        self.param_tree = ParameterTree({
            name: dataset.param_tree for (name, dataset) in self.datasets.items()
        })

        # self.data_loop = PeriodicCallback(self.get_data, 500)

    def initialize(self, adapters):
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)

        logging.debug("Received following dict of Adapters: %s", self.adapters)
        # logging.debug("Getting adapter %s", self.target_adapter)

        for name, dataset in self.datasets.items():
            logging.debug(name)
            dataset.get_adapter(self.adapters)
            dataset.data_loop.start()

    def get(self, path, request):
        """
        Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """

        try:
            response = self.param_tree.get(path)
            content_type = 'application/json'
            status = 200
        except ParameterTreeError as param_error:
            response = {'response': "Graphing Adapter GET Error: %s".format(param_error)}
            content_type = 'application/json'
            status = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status)

    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """

        content_type = 'application/json'

        try:
            data = json_decode(request.body)
            self.param_tree.set(path, data)
            response = self.param_tree.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {'error': str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(e))}
            status_code = 400

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)