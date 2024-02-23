# Project name
project(LiveX)

# Require CMake version >=2.8
cmake_minimum_required(VERSION 2.8)

# Set output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_CONFIG_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/test_config)

# Set the common directory
set(COMMON_DIR ${LiveX_SOURCE_DIR}/common)

# Set the frameReceiver directory
set(FRAMERECEIVER_DIR ${LiveX_SOURCE_DIR}/frameReceiver)

# Set the frameProcessor directory
set(FRAMEPROCESSOR_DIR ${LiveX_SOURCE_DIR}/frameProcessor)

# Set the frameSimulator directory
set(FRAMESIMULATOR_DIR ${LiveX_SOURCE_DIR}/frameSimulator)

# set the integrationTest directory
set(TEST_DIR ${LiveX_SOURCE_DIR}/test)

# C++17 requires for cppflow
set(CMAKE_CXX_STANDARD 17)

# Avoid linker warnings for tensorflow
set(GCC_LINKER_FLAGS "-fuse-ld=gold")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${GCC_LINKER_FLAGS}")
set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} ${GCC_LINKER_FLAGS}")

# Appends the cmake/modules path inside the MAKE_MODULE_PATH variable which stores the
# directories of additional CMake modules (ie. MacroOutOfSourceBuild.cmake):
set(CMAKE_MODULE_PATH ${LiveX_SOURCE_DIR}/cmake ${CMAKE_MODULE_PATH})

# Allow macOS shared (dynamic) libraries to link with undefined symbols
if (APPLE)
	message("Allowing undefined symbols in macOS shared library linking")
    set (CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -undefined dynamic_lookup")
endif(APPLE)

# Find and add external packages required for application and test
find_package( Boost 1.41.0
	      REQUIRED
	      COMPONENTS program_options system filesystem unit_test_framework date_time thread)
find_package(Log4CXX 0.10.0 REQUIRED)
find_package(ZeroMQ 3.2.4 REQUIRED)
find_package(OdinData REQUIRED)
# find_package(Torch REQUIRED)

message("\nDetermining LiveX-detector version")
include(GetGitRevisionDescription)
git_describe(GIT_DESC_STR)

string(REGEX REPLACE "^([0-9]+)[\\.-].*" "\\1" VERSION_MAJOR "${GIT_DESC_STR}")
string(REGEX REPLACE "^[0-9]+[\\.-]([0-9]+).*" "\\1" VERSION_MINOR "${GIT_DESC_STR}")
string(REGEX REPLACE "^[0-9]+[\\.-][0-9]+[\\.-]([0-9]+).*" "\\1" VERSION_PATCH "${GIT_DESC_STR}")
string(REGEX REPLACE "^[0-9]+[\\.-][0-9]+[\\.-][0-9]+-[0-9]+-(.*)" "\\1" VERSION_SHA1 "${GIT_DESC_STR}")

set(VERSION_SHORT "${VERSION_MAJOR}.${VERSION_MINOR}.${VERSION_PATCH}")
set(VERSION_STR ${GIT_DESC_STR})
message("-- Git describe version: ${GIT_DESC_STR}")
message("-- major:${VERSION_MAJOR} minor:${VERSION_MINOR} patch:${VERSION_PATCH} sha1:${VERSION_SHA1}")
message("-- short version: ${VERSION_SHORT}")

configure_file(${COMMON_DIR}/include/version.h.in "${CMAKE_BINARY_DIR}/include/version.h")
include_directories(${CMAKE_BINARY_DIR}/include)

# Add common/include directory to include path
include_directories(${COMMON_DIR}/include)

# Add the frameReceiver subdirectory
add_subdirectory(${FRAMERECEIVER_DIR})

# Add the frameReceiver subdirectory
add_subdirectory(${FRAMEPROCESSOR_DIR})

# Add the frameSimulator subdirectory
add_subdirectory(${FRAMESIMULATOR_DIR})

# Add the integrationTest subdirectory
add_subdirectory(${TEST_DIR})

# Add the doc subdirectory
#add_subdirectory(doc)

# Add the config subdirectory (config files used for integration testing)
add_subdirectory(config)

# target_link_libraries(LiveX ${TORCH_LIBRARIES})