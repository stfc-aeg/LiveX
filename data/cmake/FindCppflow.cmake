#
# FindCppflow.cmake
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
# Finds the Cppflow library. This module defines:
#   - CPPFLOW_INCLUDE_DIR, directory containing headers
#   - CPPFLOW_FOUND, whether CPPFLOW has been found
# Define CPPFLOW_ROOT_DIR if Cppflow is installed in a non-standard location.

message ("\nLooking for Cppflow Headers")

if (CPPFLOW_ROOT_DIR)
    message (STATUS "Searching Cppflow Root Dir: ${CPPFLOW_ROOT_DIR}")
endif()

# Find header files
if(CPPFLOW_ROOT_DIR)
    find_path(
        CPPFLOW_INCLUDE_DIR cppflow.h
        PATHS ${CPPFLOW_ROOT_DIR}/include/cppflow
        NO_DEFAULT_PATH
    )
else()
    find_path(CPPFLOW_INCLUDE_DIR cppflow.h)
endif()

if(CPPFLOW_INCLUDE_DIR)
    message(STATUS "Found Cppflow: ${CPPFLOW_INCLUDE_DIR}")
    set(CPPFLOW_FOUND TRUE)
else()
    set(CPPFLOW_FOUND FALSE)
endif()

if(NOT CPPFLOW_FOUND)
    message(STATUS "Could not find the Cppflow Library.")
endif()
