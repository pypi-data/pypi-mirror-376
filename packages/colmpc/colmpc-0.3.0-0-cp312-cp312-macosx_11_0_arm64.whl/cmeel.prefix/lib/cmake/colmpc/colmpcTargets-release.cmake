#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "colmpc::colmpc" for configuration "Release"
set_property(TARGET colmpc::colmpc APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(colmpc::colmpc PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libcolmpc.0.3.0.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libcolmpc.0.3.0.dylib"
  )

list(APPEND _cmake_import_check_targets colmpc::colmpc )
list(APPEND _cmake_import_check_files_for_colmpc::colmpc "${_IMPORT_PREFIX}/lib/libcolmpc.0.3.0.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
