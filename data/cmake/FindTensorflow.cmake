#
# FindTensorflow.cmake
#
#
# The MIT License
#
# Copyright (c) 2016 MIT and Intel Corporation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Finds the Tensorflow library. This module defines:
#   - TENSORFLOW_INCLUDE_DIR, directory containing headers
#   - TENSORFLOW_FOUND, whether TENSORFLOW has been found
# Define TENSORFLOW_ROOT_DIR if Tensorflow is installed in a non-standard location.

message ("\nLooking for Tensorflow headers and libraries")

if (TENSORFLOW_ROOT_DIR)
    message (STATUS "Searching Tensorflow Root Dir: ${TENSORFLOW_ROOT_DIR}")
endif()

if(TENSORFLOW_ROOT_DIR)

    # Find header files
    find_path(
            TENSORFLOW_INCLUDE_DIR tensorflow/c/c_api.h
            PATHS ${TENSORFLOW_ROOT_DIR}/include
            NO_DEFAULT_PATH
    )

    # Find libraries
    find_library(TENSORFLOW_LIBRARY
        NAMES
            tensorflow
        PATHS
            ${TENSORFLOW_ROOT_DIR}/lib
    )
    find_library(TENSORFLOW_FRAMEWORK_LIBRARY
        NAMES
            tensorflow_framework
        PATHS
            ${TENSORFLOW_ROOT_DIR}/lib
    )

    endif()

include(FindPackageHandleStandardArgs)

find_package_handle_standard_args(TENSORFLOW
    DEFAULT_MSG
    TENSORFLOW_INCLUDE_DIR
    TENSORFLOW_LIBRARY
    TENSORFLOW_FRAMEWORK_LIBRARY
)

if (TENSORFLOW_FOUND)
    set(TENSORFLOW_LIBRARIES ${TENSORFLOW_LIBRARY} ${TENSORFLOW_FRAMEWORK_LIBRARY})
    message(STATUS "Include directory: ${TENSORFLOW_INCLUDE_DIR}")
    message(STATUS "Libararies: ${TENSORFLOW_LIBRARIES}")
endif()
