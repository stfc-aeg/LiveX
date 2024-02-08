# How does this class work
"""
It needs functions to:
- Check if file exists, if not create it with <name>
- Receive data structure
- Write data into file with given structure

Temp logs, camera data, metadata (config) are the obvious structures. User notes could also be handled by this, creating a markdown or text file.

Camera data will eventually need more consideration
"""

import h5py
import os
import time
import datetime
import numpy as np
import logging

def write_hdf5(filepath, filename, data, groupname, dtypes=None):
    """Create or access a specified file, create a group in it and add data to that group.
    :param filepath: path to file/file directory
    :param filename: name of file
    :param data: dict of data, with each dataset as key and its data as value
    :param groupname: name of group for file
    :param dtypes: optional specified data-typing for specific datasets, e.g.: 'S'
    """
    # Handle filename
    if (filename.endswith('.hdf5')):
        filename = filename
    else:
        filename += '.hdf5'
        filename = filename
    # File path, make directory
    full_path = os.path.join(
        filepath, filename
    )
    os.makedirs(filepath, exist_ok=True),
    file = h5py.File(full_path, "w")

    # Add group to file
    group = file.require_group(groupname)

    for entry in data.keys():
        # Create np array
        if entry in dtypes.keys():  # Sort special dtypes
            arr_entry = np.array(data[entry], dtype=dtypes[entry])
        else:
            arr_entry = np.array(data[entry])

        # Replace/create dataset
        if entry in group:
            group[entry][...] = arr_entry
        else:
            dset = group.create_dataset(
                entry, data=arr_entry
            )
    logging.debug("file written")

def create_notes_file(filepath, filename, filetype='md'):
    """Create a notes file in the specified location, with specified name and filetype.
    :param filepath (str): folder location from control/
    :param filename (str): name of file
    :param filetype: type of file. 'txt' or 'md'
    """
    logging.debug("filetype: %s", filetype)
    # force filetype by passed argument for config mismatches
    if filetype not in ['md', 'txt']:
        logging.debug("Filetype should be 'md' or 'txt'.")
        return

    name, ext = filename.split(".")
    logging.debug("name: %s", name)
    logging.debug("ext: %s", ext)
    if ext in ['md', 'txt']:
        filename = name  # remove existing extension
    logging.debug("filename: %s", filename)
    filename += '.' + filetype
    logging.debug("filename: %s", filename)

    # want to add option for .txt or .md?
    full_path = os.path.join(
        filepath, filename
    )
    os.makedirs(filepath, exist_ok=True),

    try:
        with open(full_path, 'x') as file:
            logging.debug("Notes file created as %s", filetype)
    except:
        logging.debug("Notes file already exists")
