import logging
import os
import h5py

from typing import Dict

class HdfMetadataWriter():

    def __init__(self, file_path: str, file_name : str, mode : str ="a"):

        self.file_path = file_path
        self.file_name = file_name
        self.mode = mode

        self.full_path = os.path.join(file_path, file_name)

    def __enter__(self):

        os.makedirs(self.file_path, exist_ok=True)
        self.file = h5py.File(self.full_path, self.mode)
        return self
    
    def __exit__(self, exc_type, exc_value, exc_tb):

        if self.file:
            self.file.close()
    
    def write(self, group: str, metadata: Dict):

        group = self.file.require_group(group)

        for key, value in metadata.items():
            group.attrs[key] = value

        logging.debug("Wrote metadata to group %s in HDF file %s", group.name, self.full_path)
