#----------------------------------------------------------------
# Generated CMake target import file for configuration "RelWithDebInfo".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "mir" for configuration "RelWithDebInfo"
set_property(TARGET mir APPEND PROPERTY IMPORTED_CONFIGURATIONS RELWITHDEBINFO)
set_target_properties(mir PROPERTIES
  IMPORTED_LOCATION_RELWITHDEBINFO "${_IMPORT_PREFIX}/lib64/libmir.so"
  IMPORTED_SONAME_RELWITHDEBINFO "libmir.so"
  )

list(APPEND _cmake_import_check_targets mir )
list(APPEND _cmake_import_check_files_for_mir "${_IMPORT_PREFIX}/lib64/libmir.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
