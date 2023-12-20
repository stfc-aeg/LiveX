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
import time
import json


class GraphDataset():

    def __init__(self, time_interval, adapter, get_path, get_subpaths, retention, name=None):
        self.time_interval = time_interval
        self.data = {
            'temp_a': [],
            'temp_b': []
        }
        self.timestamps = []
        self.adapter_name = adapter
        self.adapter = None
        self.get_path = get_path
        self.get_subpaths = get_subpaths
        self.retention = retention
        self.name = name

        self.data_loop = PeriodicCallback(self.get_data, self.time_interval * 1000)

        logging.debug("Created Dataset %s, interval of %f seconds", name, self.time_interval)

        self.param_tree = ParameterTree({
            "name": (self.name, None),
            "data": (lambda: self.data, None),
            "timestamps": (lambda: self.timestamps, None),
            "interval": (self.time_interval, None),
            "retention": (self.retention * self.time_interval, None),
            "loop_running": (lambda: self.data_loop.is_running(), None)
        })

    def get_data(self):
        pop_timestamp = False  # Flag, only want to do this once but have multiple lists
        cur_time = time.time()
        self.timestamps.append(cur_time)

        for key in self.data.keys():
            if len(self.data[key]) > self.retention:
                self.data[key].pop(0)

        if len(self.timestamps) > self.retention:
            self.timestamps.pop(0)

        # response = self.adapter.get(self.get_path, ApiAdapterRequest(None))

        # # For each subpath, look through response and add to same-named list
        # for subpath, key in zip(self.get_subpaths, self.data.keys()):
        #     data = response.data[self.get_path][subpath]
        #     self.data[key].append(data)

    def get_adapter(self, adapter_list):
        self.adapter = adapter_list[self.adapter_name]

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)


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

        # logging.debug(data)

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