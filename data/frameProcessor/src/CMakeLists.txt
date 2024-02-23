set(CMAKE_INCLUDE_CURRENT_DIR on)

# no idea if this is a valid way of doing things anymore but lets see if it works
list(APPEND CMAKE_PREFIX_PATH ${TORCH_ROOT_DIR})
find_package(Torch REQUIRED)
if(Torch_FOUND)
  MESSAGE("FOUND TORCH")
  MESSAGE("Torch Version: ${Torch_VERSION}")
  MESSAGE("Torch Libs: ${TORCH_LIBRARIES}")
  MESSAGE("Torch Include DIR: ${TORCH_INCLUDE_DIR}")
  MESSAGE("Torch Lib Dir: ${TORCH_LIBRARY_DIR}")
  MESSAGE("Torch CXX Flags: ${TORCH_CXX_FLAGS}")
ENDIF(Torch_FOUND)

include_directories(${FRAMEPROCESSOR_DIR}/include ${ODINDATA_INCLUDE_DIRS}
	${Boost_INCLUDE_DIRS} ${LOG4CXX_INCLUDE_DIRS}/.. ${ZEROMQ_INCLUDE_DIRS}
	${TORCH_INCLUDE_DIR})

# Add Library for each LiveX Plugin
add_library(LiveXTorchPlugin SHARED LiveXTorchPlugin.cpp)

target_compile_options(LiveXTorchPlugin PRIVATE ${TORCH_CXX_FLAGS})
# target_link_directories(LiveXTorchPlugin PUBLIC ${TORCH_LIBRARY_DIR})
target_link_libraries(LiveXTorchPlugin ${TORCH_LIBRARIES})
target_include_directories(LiveXTorchPlugin PRIVATE ../../include ${TORCH_INCLUDE_DIR})

get_target_property(PLUGIN_INSTALL_RPATH LiveXTorchPlugin INSTALL_RPATH)
set_target_properties(LiveXTorchPlugin PROPERTIES
INSTALL_RPATH "${PLUGIN_INSTALL_RPATH}:${TORCH_ROOT_DIR}/lib")

install (TARGETS LiveXTorchPlugin LIBRARY DESTINATION lib)