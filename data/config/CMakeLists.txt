file(GLOB CONFIG_FILES 
  *.config
  *.xml
  *.json
  )

message("\nSearching for configuration files")
message(STATUS "Config files found: ${CONFIG_FILES}")

set(CONFIG_INSTALL_DIR "${CMAKE_INSTALL_PREFIX}/config/data")
message(STATUS "Config install dir : ${CONFIG_INSTALL_DIR}")

foreach(CONFIG_FILE ${CONFIG_FILES})
  get_filename_component(CONFIG_FILE_NAME ${CONFIG_FILE} NAME)
  message(STATUS "Config file dest: ${CONFIG_INSTALL_DIR}/${CONFIG_FILE_NAME}")
  install(
    CODE 
    "
      set(CONFIG_INSTALL_DIR \"${CONFIG_INSTALL_DIR}\")
      set(LIB_INSTALL_DIR \"${CMAKE_INSTALL_PREFIX}/lib\")
      message(STATUS \"Installing ${CONFIG_INSTALL_DIR}/${CONFIG_FILE_NAME}\")
      configure_file(
        ${CONFIG_FILE} ${CONFIG_INSTALL_DIR}/${CONFIG_FILE_NAME} @ONLY
      )
    "
    )
endforeach(CONFIG_FILE)